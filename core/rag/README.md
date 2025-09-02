# core/rag 모듈

업로드된 CSV를 문서 집합으로 변환하고 임베딩하여, FAISS 벡터스토어를 통해 질의용 Retriever를 제공합니다.

## 파이프라인
1) CSV 로딩 → 각 행(row)을 JSON 문자열 문서로 변환
2) 문서 임베딩(`all-MiniLM-L6-v2`)
3) FAISS 색인 생성
4) Retriever(`as_retriever(k)`) 반환 → LangChain 도구(`doc_search`)로 연결

## 파일 구성
- `builder.py`
  - `build_retriever_from_csv(path, k=3)`
  - 입력/출력: CSV 경로 → Retriever 객체
  - 설정: `k`는 검색 시 반환할 문서 개수

## 성능/제약
- 모든 행을 문서화하므로, 행 수가 매우 많으면 메모리 사용량 증가
- 필요 시: 샘플링(상위 N행), 컬럼 선택(핵심 컬럼만), 배치 임베딩 전략 도입 권장
- 영속 저장: 현재 인메모리. 디스크 저장 필요 시 `vector_db/`로 확장 설계

## 연결 지점
- `backend/routes/upload.py`: 업로드 직후 Retriever를 생성해 `global_state`에 보관
- `backend/state.py`: 서버 재기동 시 최근 업로드로 Retriever를 재생성
