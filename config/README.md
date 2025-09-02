# config 디렉터리

경로 등 애플리케이션 전역 설정을 정의합니다.

## 파일 구성
- `paths.py`: 프로젝트 루트 기준으로 `data/`, `uploads/`, `meta/`, `plots/` 경로를 정의하고, 폴더를 보장 생성합니다.

## 연결 지점
- `backend/services/ingest.py`: 업로드 파일 저장 경로(`UPLOAD_DIR`)
- `core/data/meta.py`: 메타데이터 저장/조회 경로(`META_DIR`)

## 동작/주의
- 실행 시 경로를 즉시 생성하여, 라우트/서비스에서 디렉터리 존재 여부를 신경 쓰지 않도록 합니다.
- OS 독립적(`pathlib.Path`)으로 동작합니다.
