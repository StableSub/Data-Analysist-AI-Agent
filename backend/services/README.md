# backend/services

라우터에서 호출하는 비즈니스 로직을 담습니다.

## 파일 구성
- `agent.py`: ReAct 에이전트 실행
  - 흐름: LLM 로딩 → MCP 서버 세션 연결 → MCP 도구 로드 → (있다면) RAG retriever 도구 추가 → ReAct 에이전트 구성 → 메시지 어셈블 → 실행
  - 메시지 구성: system(프로필 요약), system(파일 정보/도구 사용 지침), 최근 대화(n개), user 입력
  - 반환: LLM 최종 메시지의 content
  - 사용: `core.llm.factory.get_llm`, `langgraph.prebuilt.create_react_agent`, `langchain_mcp_adapters.tools`, `langchain.tools.retriever`
- `ingest.py`: 업로드 파일 영구 저장
  - 동작: 업로드 임시 파일을 `data/uploads/{dsid}/raw.ext`로 복사
  - 반환: `(dataset_id, raw_path, ext)`
  - 사용: `config.paths.UPLOAD_DIR`, `core.data.ids.gen_dataset_id`
