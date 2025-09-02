# core/llm 모듈

LLM 인스턴스 및 간단 체인 구성을 제공합니다. 환경변수(.env)를 로드하여 API 키를 주입합니다.

## 파일 구성
- `factory.py`
  - `get_llm(model="gemini-2.5-flash", temperature=0.4)`
    - Google Generative AI(Gemini)용 LangChain LLM 생성
    - 내부에서 `.env` 로드, `LANGCHAIN_PROJECT` 기본값 설정
  - `get_chain(llm)`
    - LLM → 문자열 파서 체인 구성(StrOutputParser)

## 환경변수
- 필수: `GOOGLE_API_KEY`
- 선택: `LANGCHAIN_PROJECT` (없으면 `langchain_streamlit`로 설정)

## 오류/안전
- 키 미설정 시 LLM 생성 실패 → 백엔드 에이전트 초기화에서 예외 메시지 확인 권장
- 요금/쿼터: 모델 호출량 제한 고려 필요(백오프/재시도는 상위 계층에서 결정)

## 연결 지점
- `backend/services/agent.py`: 에이전트 초기화 시 `get_llm()` 사용
