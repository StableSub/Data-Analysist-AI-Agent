import time, json, csv, hashlib, chardet
import pandas as pd
from pathlib import Path
from typing import Tuple

# __file__ : 현재 실행 중인 경로. reslove() : 경로를 절대 경로로 변환. parent 그 파일이 있는 디렉토리 경로. 
BASE_DIR = Path(__file__).resolve().parent 

# 이 파일의 경로에 data 폴더, data 폴더 안에 uploads, meta 폴더를 지정.
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
META_DIR = DATA_DIR / "meta"

# 실제 디렉토리를 생성. parents=True : parents가 t없으면(여기선 data 폴더가 없으면) 자동으로 생성. exist_ok : 이미 존재해도 넘어감.
for d in (UPLOAD_DIR, META_DIR):
    d.mkdir(parents=True, exist_ok=True)

# 지원하는 확장자 선언.
SUPPORTED = {"csv", "tsv", "txt"}

### 사용자가 올린 파일을 고유 ID로 분류해서 디렉토리에 저장하는 부분. ###

# 업로드 세션을 식별할 고유 ID 생성.
def gen_dataset_id(filename: str) -> str:
    raw = f"{filename}-{time.time_ns()}".encode("utf-8") # 파일명-현재 시간 형태의 문자열을 만들고 UTF-8 바이트로 인코딩. 시간까지 포함해 충돌 가능성 낮춤.
    return hashlib.sha1(raw).hexdigest()[:16] # raw 바이트를 SHA-1 해시 -> 40자리 hex 문자열 중 앞 16자리만 사용해 짧은 ID 생성.

# 업로드 객체를 받아 디스크에 저장하고 dataset_id, 저장 경로, 확장자를 반환.
def save_upload_to_disk(uploaded_file) -> tuple[str, Path, str]:
    filename = uploaded_file.name 
    ext = Path(filename).suffix.lower().lstrip(".") # 확장자를 소문자 + 앞의 점 제거 형태로 정규화(.CSV -> csv)
    dsid = gen_dataset_id(filename) # 해당 파일을 식별할 데이터셋 ID 생성.
    target_dir = UPLOAD_DIR / dsid # data/uploads/{dataset_id} 형태의 데이터셋 전용 디렉토리 경로 구성.
    target_dir.mkdir(parents=True, exist_ok=True) # 디렉토리가 없으면 상위 경로까지 생성, 이미 존재 시 통과.
    raw_path = target_dir / f"raw.{ext if ext else 'bin'}" # 실제 저장 파일명은 항상 raw.{ext}로 고정.
    with open(raw_path, "wb") as f: # 원본 그대로 저장하기 위해 바이너리 쓰기 모드로 파일 오픈.
        f.write(uploaded_file.getbuffer()) # 업로드 버퍼 전체를 한 번에 기록.
    return dsid, raw_path, ext

### 저장된 원본 파일이 어떤 형식인지, 어떻게 일겅야 하는지 자동 감지하는 부분. ###

# 텍스트 파일의 문자 인코딩을 빠르게 추정. 파일 앞부분만 샘플링해 성능을 올림.
def detect_encoding(path: Path, max_bytes: int = 200_000) -> str:
    with open(path, "rb") as f: # 바이너리 모드로 파일을 열고 앞 max_bytes 바이트만 읽어 샘플 확보.
        raw = f.read(max_bytes)
    res = chardet.detect(raw) # chardet.detect로 인코딩을 추정하고 실패 시 빈 dict 반환.
    enc = (res.get("encoding") or "utf-8").lower() # encoding 방식을 불러오고 실패 시 utf-8을 반환.
    return enc

# CSV류 텍스트에서 필드 구분자를 샘플 텍스트만으로 추정하고, 실패 시 콤마(합리적인 기본값)으로 풀백.
def detect_delimiter(text_sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(text_sample, delimiters=[",", "\t", ";", "|", "^"]) # 주어진 후보 구분자 중 가장 적합한 것을 탐지.
        return dialect.delimiter
    except Exception: # 탐지 실패 시 콤바를 기본값으로 반환.
        return ","
    
# 저장된 파일의 경로, 확장자, 사용자 힌트를 종합해, 로더가 필요로 하는 최소 힌트(filetype, encoding, delimiter, ext)를 만듬.
# CSV, 엑셀, 파케 등 파일 탙입마다 다른 결정 포인트를 표준화해 반환.
def sniff_file(raw_path: Path, ext: str):
    ext = (ext or "").lower() # ext를 소문자 문자열로 정규화.
    if ext not in SUPPORTED: # 만약 지원하지 않는 타입일 시 에러 반환.
        raise ValueError(f"UNSUPPORTED_FILE_TYPE: .{ext}")
    
    info = {"filetype": None, "encoding": None, "delimiter": None, "ext": ext} # 스키마를 미리 초기화.
    if ext in ("csv", "tsv", "txt"): # 텍스트 계열은 filetype을 csv로 통일.
        info["filetype"] = "csv"
        enc = detect_encoding(raw_path) # 텍스트를 읽기 위해 먼저 인코딩을 추정해 기록.
        info["encoding"] = enc
        #앞 50k정도만 읽어 구분자 추정용 샘플을 만듬.
        with open(raw_path, "rb") as f:
            head = f.read(50_000)
        try: # 먼저 추정한 인코딩으로 디코드 하고, 실패 시 utf-8로 재시도.
            sample = head.decode(enc, errors="ignore")
        except Exception:
            sample = head.decode("utf-8", errors="ignore")
        delim = detect_delimiter(sample)
        if ext == "tsv": # 확장자가 tsv면 무조건 탭으로 보정.
            delim = "\t"
        info["delimiter"] = delim # 최종 구분자를 info에 기록.
    return info

# CSV 파일의 총 행 수 세기(메모리 절약을 위해 청크 단위로).
def count_rows_csv(path: Path, enc: str, sep: str | None) -> int:
    total = 0 
     # CSV를 100,000행 단위로 끊어서 읽고, 읽을 때마다 행 개수를 누적.
     # dftype=object: 행 변환 문제를 피하기 위해 문자열로 읽음.
     # on_bad_line="skip": 깨진 줄은 무시.
    for chunk in pd.read_csv(path, sep=sep, engine="python", encoding=enc, chunksize=100_100, dtype=object, on_bad_lines="skip"):
        total += len(chunk)
    return total

# 파일 형식에 맞춰 일부 샘플 데이터를 읽고, 파일 전체 구조 정보를 반환.
def sample_load(raw_path: Path, sniff_info: dict, sample_rows: int = 5000):
    ftype = sniff_info["filetype"] # 파일 형식을 sniff_info에서 가져옴.
    if ftype == "csv": # 인코딩과 구분자 정보를 가져옴.
        enc = sniff_info["encoding"] or "utf-8"
        sep = sniff_info["delimiter"] or None
        df = pd.read_csv(raw_path, sep=sep, engine="python", encoding=enc, nrows=sample_rows, on_bad_lines="skip") # CSV에서 앞부분 n행만 읽어서 샘플 DataFrame 생성.
        try: # 총 행수를 count_rows_csv로 계산. 실패 시 fallback으로 샘플 크기 사용.
            total_rows = count_rows_csv(raw_path, enc, sep)
        except Exception:
            total_rows = len(df)
        shape_total = (total_rows, len(df.columns)) # 전체 (행, 얄) shape와 함께 DataFrame 샘플 반환.
        return df, {"shape_total": shape_total}
    else:
        raise ValueError(f"UNSUPPORTED_FILE_TYPE: {ftype}")
    
# 데이터셋의 메타 정보를 JSON 파일로 저장.
def write_meta(dataset_id: str, meta: dict):
    p = META_DIR / f"{dataset_id}.json" # 저장 경로를 data/meta/{dataset_id}.json으로 설정.
    p.parent.mkdir(parents=True, exist_ok=True)  # 상위 디렉토리(META_DIR)만 생성
    with open(p, "w", encoding="utf-8") as f: # JSON으로 기록. 한글 및 비ASCII 깨지지 않게 ensure_ascii=False로 설정.
        json.dump(meta, f, ensure_ascii=False, indent=2)

def read_meta(dataset_id: str) -> dict:
    """메타데이터 파일을 읽어와 딕셔너리로 반환"""
    p = META_DIR / f"{dataset_id}.json"
    if not p.exists():
        return None
    
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def get_latest_uploaded_file() -> tuple[str, dict]:
    """가장 최근에 업로드된 파일의 dataset_id와 meta 정보를 반환"""
    if not META_DIR.exists():
        return None, None
    
    meta_files = list(META_DIR.glob("*.json"))
    if not meta_files:
        return None, None
    
    # 가장 최근 파일 찾기 (수정 시간 기준)
    latest_file = max(meta_files, key=lambda f: f.stat().st_mtime)
    dataset_id = latest_file.stem
    
    meta = read_meta(dataset_id)
    return dataset_id, meta