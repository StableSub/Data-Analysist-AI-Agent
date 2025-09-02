# core 패키지 개요

프레임워크 비의존(core) 로직을 모아 둔 계층입니다. FastAPI/React와 분리된 순수 기능(데이터 스니핑/로딩, 메타 저장, 대화/프로필 저장, LLM/RAG 등)을 제공해 테스트/재사용/유지보수를 쉽게 합니다.

## 설계 원칙
- 순수 로직: FastAPI, React, 세션/요청 객체 등에 의존하지 않음
- 경계 명확화: 입력/출력을 명확히(타입/Dict, Pydantic 모델 등), 부작용 최소화
- 재사용 용이: 백엔드, MCP 등 다양한 호출자에서 동일 API 사용
- 성능 고려: 샘플링/청크 처리, 대용량 파일 폴백 전략 적용

## 하위 모듈과 역할
- `data/`: 업로드 ID 생성(ids), 인코딩/구분자 스니핑(sniff), 샘플 로딩(load), 메타(JSON) 저장/조회(meta)
- `memory.py`: 대화 로그를 SQLite로 저장/조회, 파일 맥락 보조 기능
- `profile.py`: 사용자 프로필 텍스트를 SQLite로 저장/조회/요약
- `rag/`: CSV → 문서 → 임베딩 → FAISS → Retriever 생성
- `llm/`: LLM 인스턴스 생성 및 간단 체인 구성
- `models.py`: SniffInfo, FileMeta 등 데이터 모델(선택 적용, 점진 도입 권장)

## 데이터 흐름(업로드 → 분석)
1) 업로드 파일을 `backend/services/ingest.py`가 영구 저장소(`data/uploads/{dsid}/raw.ext`)로 이동
2) `core.data.sniff.sniff_file`로 인코딩/구분자 감지 → 로딩 힌트 생성
3) `core.data.load.sample_load`로 샘플 로드 및 전체 행 수 추정
4) `core.data.meta.write_meta`로 메타(JSON) 저장, `backend/state.global_state`에 프리뷰/타입 통계 캐시
5) `core.rag.builder.build_retriever_from_csv`로 Retriever 생성 후 상태에 보관 → 에이전트가 `doc_search`로 사용

## 연결 지점(어디서 사용되나)
- 백엔드
  - `backend/routes/upload.py`: `core.data.sniff/load/meta`, `core.rag.builder`
  - `backend/services/ingest.py`: `core.data.ids`
  - `backend/services/agent.py`: `core.llm.factory.get_llm`
  - `backend/state.py`: `core.memory`, `core.profile`, `core.data.meta.get_latest_uploaded_file`, `core.rag.builder`
- MCP 서버
  - `MCP/server.py`: `core.memory`, `core.data.meta`

## 초기화/생명주기
- 서버 시작 시 `backend/state.py`가 `core.data.meta.get_latest_uploaded_file`로 최근 업로드를 찾아 상태 복원
- 대화/프로필은 각 SQLite 파일이 존재하지 않으면 자동 생성

## 확장 포인트
- 대형 CSV 처리: `core/rag/builder.py`에 청크/샘플링 옵션 추가
- 파일 형식 확대: `core/data/sniff.py`에 XLSX/JSON 등 분기 추가 및 대응 로더 구현
- 메타 모델: `core/models.py`를 API 응답/저장 포맷으로 점진 도입

---
이 디렉터리는 외부 프레임워크에 의존하지 않도록 유지하는 것이 원칙입니다.
