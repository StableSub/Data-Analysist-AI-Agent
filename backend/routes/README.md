# backend/routes

FastAPI 라우터 모음입니다. 각 파일이 하나의 라우터를 정의하고 `api.py`에서 마운트됩니다.

## 라우터 목록
- `upload.py`
  - `POST /upload`
    - 요청: `multipart/form-data` (file, sample_rows)
    - 동작: 파일 임시 저장 → 영구 저장 → 스니핑/샘플/메타 저장 → dtype/null 통계 → Retriever 생성 → 상태 업데이트
    - 응답: `FileUploadResponse`(success, message, dataset_id, meta, preview_df, dtype_df)
    - 사용: `core.data.sniff`, `core.data.load`, `core.data.meta`, `core.rag.builder`
- `chat.py`
  - `POST /chat`
    - 요청: `{message: string}`
    - 동작: 최근 업로드 복원 시도 → 파일명 치환(enhance) → 대화 저장 → 에이전트 실행(ReAct+MCP+Retriever) → 응답 저장
    - 응답: `{response: string, messages: ChatMessage[]}`
  - `GET /messages`
    - 동작: 최근 100개 대화 반환
  - 사용: `services/agent.run_agent`, `state.conversation_memory`
- `system.py`
  - `GET /file-info`
    - 동작: `global_state`의 파일 메타/프리뷰/타입 통계 반환(없으면 404)
  - `DELETE /clear-data`
    - 동작: `data/meta`, `data/uploads` 삭제 후 재생성 → 상태 리셋 → 대화 삭제
- `profile.py`
  - `POST /profile`
    - 요청: `{category, key, value}` (현재 value 중심 누적 저장)
  - `GET /profile`
    - 응답: 누적된 정보 리스트를 포함한 단순 구조
  - 사용: `state.user_profile`
