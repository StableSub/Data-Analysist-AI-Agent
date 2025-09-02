"""텍스트 구분자 파일의 인코딩/구분자를 추정하는 스니핑 유틸리티.

목표는 큰 파일에서도 안정적으로 샘플을 읽을 수 있는 최소한의 힌트를 얻는 것입니다.
보수적으로 동작하며 합리적인 폴백을 적용합니다.
"""

from pathlib import Path
import csv
import chardet

SUPPORTED = {"csv", "tsv", "txt"}


def detect_encoding(path: Path, max_bytes: int = 200_000) -> str:
    """파일 앞부분을 샘플링하여 텍스트 인코딩을 추정합니다.

    대용량 파일에서도 성능을 위해 최대 `max_bytes`까지만 읽습니다.
    추정이 모호하면 UTF-8로 폴백합니다.
    """
    with open(path, "rb") as f:
        raw = f.read(max_bytes)
    res = chardet.detect(raw)
    enc = (res.get("encoding") or "utf-8").lower()
    return enc


def detect_delimiter(text_sample: str) -> str:
    """짧은 텍스트 샘플에서 가장 그럴듯한 필드 구분자를 추정합니다.

    csv.Sniffer를 사용해 흔한 구분자 후보를 검사하며, 실패할 경우 콤마로 폴백합니다.
    """
    try:
        dialect = csv.Sniffer().sniff(text_sample, delimiters=[",", "\t", ";", "|", "^"])
        return dialect.delimiter
    except Exception:
        return ","


def sniff_file(raw_path: Path, ext: str):
    """파일 확장자와 내용 일부를 바탕으로 로더 힌트를 생성합니다.

    반환값은 하위 로더들이 사용하는 형태(dict)로, filetype/encoding/delimiter/ext를 포함합니다.
    """
    ext = (ext or "").lower()
    if ext not in SUPPORTED:
        raise ValueError(f"UNSUPPORTED_FILE_TYPE: .{ext}")

    info = {"filetype": None, "encoding": None, "delimiter": None, "ext": ext}
    if ext in ("csv", "tsv", "txt"):
        info["filetype"] = "csv"
        enc = detect_encoding(raw_path)
        info["encoding"] = enc
        # Only a small chunk is required for delimiter detection
        with open(raw_path, "rb") as f:
            head = f.read(50_000)
        try:
            sample = head.decode(enc, errors="ignore")
        except Exception:
            sample = head.decode("utf-8", errors="ignore")
        delim = detect_delimiter(sample)
        if ext == "tsv":
            delim = "\t"
        info["delimiter"] = delim
    return info
