"""메타데이터 영속화 유틸리티.

`data/meta` 경로에 JSON으로 데이터셋 메타데이터를 저장/조회합니다.
백엔드의 디스크 상태와 인메모리 상태를 연결하는 다리 역할을 합니다.
"""

import json
from pathlib import Path
from typing import Tuple

from config.paths import META_DIR


def write_meta(dataset_id: str, meta: dict):
    """주어진 데이터셋 ID에 대한 메타데이터를 JSON 파일로 저장합니다."""
    p = META_DIR / f"{dataset_id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def read_meta(dataset_id: str) -> dict | None:
    """데이터셋 ID에 대한 메타데이터 JSON을 읽어 dict 또는 None을 반환합니다."""
    p = META_DIR / f"{dataset_id}.json"
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def get_latest_uploaded_file() -> Tuple[str | None, dict | None]:
    """가장 최근에 수정된 메타 파일을 찾아 dataset_id와 메타를 반환합니다.

    서버 재시작 후에도 마지막 업로드 파일을 복원하기 위해 mtime 기준으로 검색합니다.
    """
    if not META_DIR.exists():
        return None, None
    meta_files = list(META_DIR.glob("*.json"))
    if not meta_files:
        return None, None
    latest_file = max(meta_files, key=lambda f: f.stat().st_mtime)
    dataset_id = latest_file.stem
    meta = read_meta(dataset_id)
    return dataset_id, meta
