# backend 디렉터리

FastAPI 기반 백엔드 애플리케이션입니다. 라우터(입출력) → 서비스(로직) → core(비즈니스 무관 유틸) → 상태/스토리지 흐름으로 구성됩니다.

## 구조
- `state.py`: 전역 상태 관리
- `routes/`: API 라우터 모음
- `services/`: 라우터에서 호출되는 도메인 로직
- `schemas/`: 요청/응답 Pydantic 스키마

## 상태(state.py)
- 책임: 최근 업로드 파일 복원, 프리뷰/타입 통계/메타/Retriever 캐시, 대화/프로필 인스턴스 제공
- 시동: 임포트 시 `ensure_initial_message()`와 `restore_uploaded_files()` 수행
- 필드: `global_state = {retriever, file_hash, dsid, meta, preview_df, dtype_df}`

## API 수명주기(예시)
1) `POST /upload`(routes/upload.py)
   - 파일 저장(services/ingest.py) → 스니핑/샘플/메타 저장(core.data.*) → dtype/null 통계 생성 → Retriever 생성(core.rag)
   - `global_state` 업데이트 후 응답 반환
2) `POST /chat`(routes/chat.py)
   - 최근 업로드 복원 시도(state) → 대화 저장(memory) → 에이전트 실행(services/agent.py)
   - 프로필/파일 정보를 system 메시지에 주입, retriever 도구(doc_search) 포함 → 응답 저장/반환
3) `DELETE /clear-data`(routes/system.py)
   - `data/meta`, `data/uploads` 삭제 및 재생성 → 상태 초기화 → 대화 초기화

## core와의 연결
- `core.memory`, `core.profile`: 대화/프로필 인스턴스
- `core.data.sniff/load/meta`: 파일 스니핑/로딩/메타 저장
- `core.data.ids`: 업로드 ID 생성
- `core.rag.builder`: Retriever 생성
- `core.llm.factory`: LLM 생성

## 진입점
- 루트의 `api.py`에서 FastAPI 앱을 생성하고 본 디렉터리의 라우트들을 마운트합니다. CORS, 버전, 기본 라우트는 `api.py`에서 설정합니다.
