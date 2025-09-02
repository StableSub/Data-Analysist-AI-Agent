"""데이터 파이프라인 전반에서 사용하는 타입 모델 정의.

이 모듈은 서비스 간에 자주 오가는 구조를 표준화하여 경계(입출력)에서의
검증을 돕습니다. 메타데이터 JSON 직렬화/역직렬화 및 내부 전달 시 일관된
형태를 보장합니다. Pydantic을 사용하면 다음과 같은 이점이 있습니다.

- 코드 자체가 문서가 되는 명확한 타입 정의
- 객체 생성 시 유효성 검증(필수/옵션 필드 등)
- `.model_dump()` / `.model_dump_json()`을 통한 간편한 직렬화
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel


class SniffInfo(BaseModel):
    """텍스트 구분자 파일에서 자동 감지된 기본 정보.

    Attributes:
        filetype: 논리적 파일 타입(예: "csv")로 정규화된 값.
        encoding: 감지된 문자 인코딩(상위 계층에서 기본값 적용 가능).
        delimiter: 필드 구분자(예: ",", "\t" 등).
        ext: 원래 파일 확장자(예: "csv", "tsv").
    """

    filetype: str
    encoding: Optional[str] = None
    delimiter: Optional[str] = None
    ext: Optional[str] = None


class FileMeta(BaseModel):
    """업로드된 데이터셋에 대해 디스크에 저장되는 메타데이터.

    Attributes:
        sniff: 원본 파일에서 감지된 포맷 정보.
        shape_sample: 메모리에 로드한 샘플의 형태(행, 열).
        shape_total: 전체 파일에 대한 추정 형태(행, 열).
        columns: 샘플에서 확인된 컬럼명 목록.
        ext: 정규화된 파일 확장자.
        raw_path: 디스크에 저장된 원본 파일의 절대 경로.
    """

    sniff: SniffInfo
    shape_sample: Tuple[int, int]
    shape_total: Optional[Tuple[int, int]] = None
    columns: List[str]
    ext: str
    raw_path: str
