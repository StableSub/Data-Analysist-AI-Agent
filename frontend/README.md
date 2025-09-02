# frontend 디렉터리

React + TypeScript + MUI 기반의 SPA입니다. 백엔드 FastAPI와 통신하며 파일 업로드/미리보기/채팅/프로필 설정 UI를 제공합니다.

## 구조 개요
- `src/components/`
  - `FileUpload.tsx`: 업로드 드롭존, 샘플 행수 선택 → `POST /upload`
  - `DataPreview.tsx`: 프리뷰 20행, dtype/null 통계 표시 → 업로드 응답 사용
  - `ChatInterface.tsx`: 메시지 로드/전송 → `GET /messages`, `POST /chat`
  - `ProfileSettings.tsx`: 프로필 조회/추가 다이얼로그 → `GET/POST /profile`
- `src/App.tsx`: 전체 레이아웃/테마 토글/데이터 초기화 버튼(`DELETE /clear-data`)
- `public/`: 정적 리소스, `index.html` 등

## 상태/데이터 흐름
1) 사용자가 파일 업로드 → `FileUpload`가 `/upload` 호출 → 성공 시 `FileInfo`를 상위(App)로 전달 → `DataPreview`와 `ChatInterface`가 표시
2) 채팅 입력 → `ChatInterface`가 `/chat` 호출 → 응답 메시지를 대화 목록에 추가
3) 프로필 설정 → `ProfileSettings`가 `/profile` 호출 → 저장 후 스낵 메시지/리스트 갱신
4) 데이터 초기화 → App의 버튼이 `/clear-data` 호출 → 상태 초기화 후 페이지 새로고침

## API 의존성(백엔드 매핑)
- `POST /upload` → backend/routes/upload.py
- `POST /chat`, `GET /messages` → backend/routes/chat.py
- `GET /profile`, `POST /profile` → backend/routes/profile.py
- `DELETE /clear-data` → backend/routes/system.py

## 개발/실행
- 개발 서버: `npm start` (포트 3000) — CORS: `http://localhost:3000`만 허용(백엔드 CORS 설정 참고)
- 타입 정의: `src/types/` 참고 (예: `ChatMessage`, `FileInfo`)

## UX/에러 처리
- 업로드/채팅 중 로딩 스피너 표시
- 코드 블록( ``` ) 자동 렌더링
- 네트워크 에러: 알림/에러 Alert 표시, 서버 다운 시 적절한 메시지 출력

## 확장 포인트
- 시각화 결과 표시: MCP `plot` 경로 반환 이미지를 별도 뷰로 노출 가능
- 메시지 스트리밍: 백엔드가 스트리밍을 지원하면 SSE/WebSocket으로 확장 가능
- 국제화: 한글/영문 전환(i18n) 추가 가능
