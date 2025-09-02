"""업로드 데이터셋을 위한 ID 생성 유틸리티.

원본 파일명과 단조 증가 시간 값을 조합해 짧고 충돌 가능성이 낮은 ID를
만듭니다. 동일 파일명을 빠르게 여러 번 업로드해도 충돌하지 않도록 설계했습니다.
"""

import hashlib
import time


def gen_dataset_id(filename: str) -> str:
    """업로드 세션을 식별하는 16자리 16진수 ID를 생성합니다.

    디스크 경로/메타데이터에서 참조하기에 충분히 안정적이며, UI에 표시하기에도
    부담 없는 길이입니다.
    """
    raw = f"{filename}-{time.time_ns()}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]
