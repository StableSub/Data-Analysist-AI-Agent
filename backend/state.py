"""애플리케이션 전역 상태 관리.

- 최근 업로드 파일 복원 및 미리보기/스키마 캐시
- 대화 메모리/사용자 프로필 인스턴스 제공
- 업로드된 CSV로부터 검색용 Retriever 생성
"""

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from core.memory import get_memory
from core.profile import get_user_profile
from core.data_processing.meta import get_latest_uploaded_file
from core.rag.builder import build_retriever_from_csv


# In-memory state (file-related only)
global_state: Dict[str, Any] = {
    "retriever": None,
    "file_hash": None,
    "dsid": None,
    "meta": None,
    "preview_df": None,
    "dtype_df": None,
}

# Instances
conversation_memory = get_memory()
user_profile = get_user_profile()


def ensure_initial_message():
    """대화가 비어 있으면 초기 인사 메시지를 추가합니다."""
    recent_messages = conversation_memory.get_recent_messages(limit=1)
    if not recent_messages:
        conversation_memory.add_message(
            "assistant",
            "안녕하세요! 데이터 분석을 도와드리는 AI 어시스턴트입니다. 파일을 업로드하고 질문해 보세요!",
        )


def restore_uploaded_files():
    """최근 업로드 파일이 있으면 global_state에 복원합니다."""
    try:
        dataset_id, meta = get_latest_uploaded_file()
        if dataset_id and meta:
            raw_path = Path(meta["raw_path"]) if meta.get("raw_path") else None
            if raw_path and raw_path.exists():
                with open(raw_path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()

                df = pd.read_csv(raw_path, nrows=20)
                dtype_df = pd.DataFrame(
                    {
                        "column": df.columns,
                        "null_count": df.isnull().sum().values,
                        "null_ratio": (df.isnull().mean() * 100).round(2).values,
                        "dtype": df.dtypes.astype(str).values,
                    }
                )

                retriever = build_retriever_from_csv(raw_path)

                global_state.update(
                    {
                        "file_hash": file_hash,
                        "dsid": dataset_id,
                        "meta": meta,
                        "preview_df": df.to_dict("records"),
                        "dtype_df": dtype_df.to_dict("records"),
                        "retriever": retriever,
                    }
                )
                logging.info(f"업로드된 파일 복원 완료: {dataset_id}")
            else:
                logging.warning(f"파일이 존재하지 않음: {raw_path}")
    except Exception as e:
        logging.error(f"파일 복원 중 오류: {str(e)}")


# Initialize on import
ensure_initial_message()
restore_uploaded_files()
