# core/data 모듈

데이터 입수/전처리의 공통 유틸리티를 제공합니다. 파일을 안전하고 일관되게 처리하여, 상위 계층(라우터/서비스)이 도메인 로직에 집중할 수 있게 합니다.

## 파일 구성과 상세
- `ids.py`
  - 함수: `gen_dataset_id(filename) -> str`
  - 입력/출력: 파일명 → 16자리 해시 ID
  - 사용처: 업로드 세션 식별, 디렉토리 및 메타 파일명 생성
  - 오류/주의: 없음(순수 계산)

- `sniff.py`
  - 함수: `detect_encoding(path)`, `detect_delimiter(text)`, `sniff_file(path, ext)`
  - 입력/출력: 파일 경로/확장자 → `{filetype, encoding, delimiter, ext}` dict
  - 동작: 파일 앞부분 샘플링 → 인코딩 추정 → 구분자 추정(tsv는 강제 탭)
  - 성능: 최대 바이트 샘플만 읽음(기본 200KB)
  - 폴백: 모호 시 UTF-8/콤마로 폴백
  - 오류: 미지원 확장자 → `ValueError('UNSUPPORTED_FILE_TYPE')`

- `load.py`
  - 함수: `sample_load(path, sniff_info, sample_rows)`, `count_rows_csv(path, enc, sep)`
  - 입력/출력: 경로+스니핑 정보 → `(df_sample, {shape_total: (rows, cols)})`
  - 동작: 지정 행수(nrows)만 읽고, 전체 행수는 청크 단위로 계산
  - 성능: `chunksize`로 메모리 보호, 불량 라인은 `on_bad_lines='skip'`
  - 오류: 미지원 filetype → `ValueError`

- `meta.py`
  - 함수: `write_meta(dsid, meta)`, `read_meta(dsid)`, `get_latest_uploaded_file()`
  - 입력/출력: dsid/메타 dict ↔ JSON 파일
  - 동작: `data/meta/{dsid}.json` 저장/조회, mtime 기준 최신 파일 검색
  - 주의: 스키마 유연(dict) 유지. 엄격 검증이 필요하면 `core/models.py` 도입 권장

## 연결 지점(콜 체인)
- 업로드 라우트(`backend/routes/upload.py`)
  1) `sniff.sniff_file` → 2) `load.sample_load` → 3) `meta.write_meta`
- 상태 복원(`backend/state.py`)
  - `meta.get_latest_uploaded_file`로 최신 업로드 복원
- MCP 플롯(`MCP/server.py`)
  - `meta.read_meta`, `meta.get_latest_uploaded_file`로 원본 경로/스니핑 정보 확보

## 확장/운영 팁
- 파일 형식 추가: `SUPPORTED`에 확장자 추가 후, `sniff_file` 분기 및 전용 로더 구현
- 인코딩 이슈: 외국어/혼합 인코딩 데이터는 `encoding` 폴백 전략 점검 필요
- 스트리밍 처리: 초대형 파일은 `load.py`에 제너레이터 기반 로딩 로직을 추가 고려
