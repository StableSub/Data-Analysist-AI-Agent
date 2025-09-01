import os
import sys
import time
from pathlib import Path

import pandas as pd
import numpy as np

# Headless 환경에서 시각화 저장을 위해 Agg 백엔드 사용
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# 대화 메모리 관리를 위한 import 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from conversation_memory import get_memory
from data_processing import read_meta, get_latest_uploaded_file

mcp = FastMCP("DataAnalysis")

# 전역 변수
global_df = None
data_dir = Path("data")
plots_dir = data_dir / "plots"
plots_dir.mkdir(parents=True, exist_ok=True)

@mcp.prompt()
def default_prompt(message) -> list[base.Message]:
    return [
        base.AssistantMessage(
            "You are a helpful data analysis assistant. \n"
            "Please clearly organize and return the results of the tool calling and the data analysis. \n"
            "Use the available tools to analyze data, create visualizations, and provide insights."
        ),
        base.UserMessage(message),
    ]

# 대화 메모리 관리 도구들
@mcp.tool()
async def get_conversation_history(limit: int = 20, user_id: str = "default") -> str:
    """사용자의 이전 대화 기록을 조회합니다."""
    try:
        memory = get_memory(user_id)
        if memory is None:
            return "대화 메모리 시스템을 사용할 수 없습니다."
        
        messages = memory.get_recent_messages(limit=limit)
        
        if not messages:
            return "저장된 대화 기록이 없습니다."
        
        history = f"최근 {len(messages)}개의 대화 기록:\n" + "="*50 + "\n"
        
        for i, msg in enumerate(messages, 1):
            role_name = "사용자" if msg["role"] == "user" else "어시스턴트"
            timestamp = msg.get("timestamp", "시간 정보 없음")
            history += f"\n[{i}] {role_name} ({timestamp}):\n{msg['content']}\n" + "-"*30 + "\n"
        return history
        
    except Exception as e:
        return f"대화 기록 조회 중 오류 발생: {str(e)}"

# -------------------- 추가 도구: 데이터 시각화 --------------------

@mcp.tool()
async def plot(
    kind: str,
    x: str | None = None,
    y: str | None = None,
    hue: str | None = None,
    title: str | None = None,
    dataset_id: str | None = None,
    limit: int = 5000,
    bins: int | None = None,
) -> dict:
    """업로드된 데이터셋으로 차트를 생성하고 이미지 경로를 반환합니다.

    Args:
        kind: 차트 유형. hist|bar|line|scatter|box|heatmap 지원.
        x: x축 컬럼명(필요한 경우).
        y: y축 컬럼명(필요한 경우).
        hue: 카테고리 분할 컬럼명(선택).
        title: 차트 제목(선택).
        dataset_id: 대상 데이터셋 ID(미지정 시 최신 업로드 사용).
        limit: 로딩할 최대 행 수(기본 5000, 메모리 보호용).
        bins: 히스토그램 bin 개수(선택).

    Returns:
        {"path": 이미지 파일 경로, "title": 제목, "kind": 종류, "columns_used": [..], "rows_used": N}
    """
    # 1) 대상 데이터셋 식별 및 메타 로드
    if not dataset_id:
        dsid, meta = get_latest_uploaded_file()
    else:
        dsid = dataset_id
        meta = read_meta(dsid)

    if not dsid or not meta:
        return {
            "error": "NO_DATASET",
            "message": "사용 가능한 업로드 데이터셋이 없습니다.",
        }

    raw_path = Path(meta.get("raw_path", ""))
    sniff = meta.get("sniff", {}) or {}
    encoding = sniff.get("encoding") or "utf-8"
    sep = sniff.get("delimiter") or None

    if not raw_path.exists():
        return {
            "error": "MISSING_FILE",
            "message": f"원본 파일을 찾을 수 없습니다: {raw_path}",
        }

    # 2) 데이터 로드(상한선)
    try:
        df = pd.read_csv(
            raw_path,
            sep=sep,
            encoding=encoding,
            engine="python",
            nrows=max(100, int(limit)),
            on_bad_lines="skip",
        )
    except Exception as e:
        return {"error": "LOAD_FAILED", "message": f"데이터 로드 실패: {e}"}

    if df.empty:
        return {"error": "EMPTY_DF", "message": "데이터가 비어 있습니다."}

    used_cols: list[str] = []
    if x: used_cols.append(x)
    if y and y not in used_cols: used_cols.append(y)
    if hue and hue not in used_cols: used_cols.append(hue)

    # 3) 차트 생성
    plt.figure(figsize=(8, 5))
    try:
        k = (kind or "").lower()

        if k in ("hist", "histogram"):
            if not x:
                return {"error": "ARGS", "message": "hist/histogram에는 x 컬럼이 필요합니다."}
            series = pd.to_numeric(df[x], errors="coerce").dropna()
            bins_ = bins or 30
            plt.hist(series.values, bins=bins_, color="#4e79a7")
            plt.xlabel(x)
            plt.ylabel("count")

        elif k == "bar":
            if not (x and y):
                return {"error": "ARGS", "message": "bar에는 x(범주)와 y(값) 컬럼이 필요합니다."}
            tmp = (
                df[[x, y]]
                .dropna()
                .groupby(x)[y]
                .mean()
                .sort_values(ascending=False)
                .head(20)
            )
            tmp.plot(kind="bar", color="#4e79a7")
            plt.ylabel(f"mean({y})")
            plt.xticks(rotation=45, ha="right")

        elif k == "line":
            if not (x and y):
                return {"error": "ARGS", "message": "line에는 x와 y 컬럼이 필요합니다."}
            d2 = df[[x, y]].dropna().sort_values(by=x)
            plt.plot(d2[x], d2[y], color="#4e79a7")
            plt.xlabel(x)
            plt.ylabel(y)

        elif k == "scatter":
            if not (x and y):
                return {"error": "ARGS", "message": "scatter에는 x와 y 컬럼이 필요합니다."}
            d2 = df[[x, y]].dropna()
            plt.scatter(d2[x], d2[y], alpha=0.6, color="#4e79a7")
            plt.xlabel(x)
            plt.ylabel(y)

        elif k == "box":
            if not y:
                return {"error": "ARGS", "message": "box에는 y(수치) 컬럼이 필요합니다."}
            d2 = df[[c for c in [x, y] if c]].dropna()
            if x:
                # 그룹별 박스플롯
                d2.boxplot(column=y, by=x, grid=False, rot=45)
                plt.suptitle("")  # pandas가 추가하는 기본 제목 제거
            else:
                d2.boxplot(column=y, grid=False)

        elif k == "heatmap":
            num = df.select_dtypes(include=[np.number])
            if num.shape[1] < 2:
                return {"error": "ARGS", "message": "heatmap은 수치형 컬럼이 2개 이상 필요합니다."}
            corr = num.corr(numeric_only=True)
            im = plt.imshow(corr, cmap="viridis", aspect="auto")
            plt.colorbar(im, fraction=0.046, pad=0.04)
            plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right", fontsize=8)
            plt.yticks(range(len(corr.index)), corr.index, fontsize=8)

        else:
            return {"error": "ARGS", "message": f"지원하지 않는 kind: {kind}"}

        if title:
            plt.title(title)
        else:
            default_title = f"{k} plot"
            if x: default_title += f" | x={x}"
            if y: default_title += f" | y={y}"
            plt.title(default_title)

        plt.tight_layout()
    except Exception as e:
        plt.close()
        return {"error": "PLOT_FAILED", "message": f"차트 생성 실패: {e}"}

    # 4) 저장 및 경로 반환
    filename = f"{dsid}_{k}_{int(time.time())}.png"
    out_path = plots_dir / filename
    try:
        plt.savefig(out_path, dpi=150)
    finally:
        plt.close()

    return {
        "path": str(out_path),
        "title": title or "",
        "kind": kind,
        "columns_used": used_cols,
        "rows_used": int(len(df)),
        "dataset_id": dsid,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")