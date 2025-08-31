# 📊 Data Analysis AI Agent

현대적인 React 프론트엔드와 FastAPI 백엔드를 사용한 데이터 분석 AI Agent입니다. CSV, TSV, TXT 파일을 업로드하고 AI와 대화하며 데이터를 분석할 수 있습니다.

## ✨ 주요 기능

- **파일 업로드**: CSV, TSV, TXT 파일 드래그 앤 드롭 업로드
- **데이터 미리보기**: 업로드된 파일의 구조와 내용 미리보기
- **AI 채팅**: 데이터에 대한 질문과 AI의 답변
- **현대적 UI**: Material-UI 기반의 반응형 디자인
- **다크 모드**: 라이트/다크 테마 전환 지원
- **실시간 처리**: 파일 업로드 및 AI 응답 실시간 처리

## 🚀 기술 스택

### Frontend
- **React 18** - 사용자 인터페이스
- **TypeScript** - 타입 안전성
- **Material-UI (MUI)** - 현대적인 UI 컴포넌트
- **Axios** - HTTP 클라이언트
- **React Dropzone** - 파일 업로드

### Backend
- **FastAPI** - 고성능 Python 웹 프레임워크
- **Uvicorn** - ASGI 서버
- **LangChain** - AI 모델 통합
- **Google Gemini** - AI 언어 모델
- **FAISS** - 벡터 검색
- **Pandas** - 데이터 처리

## 📦 설치 및 실행

### 1. 가상환경 활성화
```bash
workon ai_agent
```

### 2. 백엔드 의존성 설치
```bash
pip install fastapi uvicorn python-multipart
```

### 3. 프론트엔드 의존성 설치
```bash
cd frontend
npm install
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 Google API 키를 설정하세요:
```
GOOGLE_API_KEY=your_google_api_key_here
```

### 5. 서버 실행

#### 백엔드 서버 (포트 8000)
```bash
python api.py
```

#### 프론트엔드 개발 서버 (포트 3000)
```bash
cd frontend
npm start
```

### 6. 브라우저에서 접속
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000
- API 문서: http://localhost:8000/docs

## 🎯 사용법

1. **파일 업로드**: 왼쪽 패널에서 CSV, TSV, TXT 파일을 드래그 앤 드롭하거나 클릭하여 업로드
2. **데이터 확인**: 업로드된 파일의 구조, 컬럼 정보, 미리보기를 확인
3. **AI와 대화**: 오른쪽 채팅 패널에서 데이터에 대한 질문을 입력
4. **분석 결과**: AI가 데이터를 분석하고 답변을 제공

## 📁 프로젝트 구조

```
streamlit-chatlab/
├── api.py                 # FastAPI 백엔드
├── main.py               # 기존 Streamlit 앱 (참고용)
├── llm_model.py          # AI 모델 설정
├── data_processing.py    # 데이터 처리 로직
├── rag_processsing.py    # RAG 처리 로직
├── MCP/                  # MCP 서버
├── data/                 # 업로드된 파일 저장소
│   ├── uploads/         # 원본 파일
│   └── meta/           # 메타데이터
├── frontend/            # React 프론트엔드
│   ├── src/
│   │   ├── components/  # React 컴포넌트
│   │   ├── types/       # TypeScript 타입 정의
│   │   └── App.tsx      # 메인 앱 컴포넌트
│   └── package.json
└── README.md
```

## 🔧 API 엔드포인트

- `POST /upload` - 파일 업로드
- `POST /chat` - 채팅 메시지 전송
- `GET /messages` - 채팅 히스토리 조회
- `GET /file-info` - 업로드된 파일 정보 조회

## 🎨 UI 특징

- **반응형 디자인**: 모바일과 데스크톱 모두 지원
- **다크 모드**: 라이트/다크 테마 전환
- **드래그 앤 드롭**: 직관적인 파일 업로드
- **실시간 피드백**: 로딩 상태와 진행률 표시
- **코드 하이라이팅**: AI 응답의 코드 블록 자동 포맷팅

## 🔒 보안 고려사항

- 파일 업로드 크기 제한
- 지원 파일 형식 검증
- CORS 설정으로 프론트엔드 접근 제한
- 환경 변수를 통한 API 키 관리

## 🚧 개발 중인 기능

- [ ] 파일 다운로드 기능
- [ ] 데이터 시각화 차트
- [ ] 사용자 인증
- [ ] 대화 히스토리 저장
- [ ] 다중 파일 업로드

## 📝 라이선스

MIT License

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해 주세요.

