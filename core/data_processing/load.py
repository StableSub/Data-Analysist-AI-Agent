"""샘플 로딩과 행수 집계를 위한 데이터 로딩 헬퍼.

인터랙티브 세션에서 응답성과 메모리 사용을 고려해 제한된 범위만 읽습니다.
"""

from pathlib import Path
from typing import Tuple

import pandas as pd


def count_rows_csv(path: Path, enc: str, sep: str | None) -> int:
    """전체 파일을 로드하지 않고 CSV 계열 파일의 총 행 수를 셉니다.

    청크 단위로 읽어 각 청크의 길이를 누적합니다. 파싱 실패 라인은 건너뛰어
    불완전한 데이터에서도 중단 없이 동작합니다.
    """
    total = 0
    for chunk in pd.read_csv(
        path,
        sep=sep,
        engine="python",
        encoding=enc,
        chunksize=100_100,
        dtype=object,
        on_bad_lines="skip",
    ):
        total += len(chunk)
    return total


def sample_load(raw_path: Path, sniff_info: dict, sample_rows: int = 5000):
    """일부 행만 샘플링 로드하고 기본 통계를 계산합니다.

    반환값은 DataFrame 샘플과 추정 전체 형태(shape_total)를 담은 dict 입니다.
    현재는 CSV 계열만 지원합니다.
    """
    ftype = sniff_info["filetype"]
    if ftype == "csv":
        enc = sniff_info["encoding"] or "utf-8"
        sep = sniff_info["delimiter"] or None
        df = pd.read_csv(
            raw_path,
            sep=sep,
            engine="python",
            encoding=enc,
            nrows=sample_rows,
            on_bad_lines="skip",
        )
        try:
            total_rows = count_rows_csv(raw_path, enc, sep)
        except Exception:
            total_rows = len(df)
        shape_total: Tuple[int, int] = (int(total_rows), int(len(df.columns)))
        return df, {"shape_total": shape_total}
    else:
        raise ValueError(f"UNSUPPORTED_FILE_TYPE: {ftype}")
