# backend/schemas

FastAPI 요청/응답에 사용되는 Pydantic 모델을 정의합니다.

## 파일 구성
- `file.py`: 업로드 응답 스키마(`FileUploadResponse`)
- `chat.py`: 채팅 요청/응답 스키마(`ChatRequest`, `ChatResponse`, `ChatMessage`)
- `profile.py`: 프로필 요청/응답 스키마

## 필드 요약
- `FileUploadResponse`
  - `success: bool`, `message: str`, `dataset_id?: str`, `meta?: dict`, `preview_df?: list[dict]`, `dtype_df?: list[dict]`
- `ChatRequest`
  - `message: str`
- `ChatResponse`
  - `response: str`, `messages: list[ChatMessage]`
- `ChatMessage`
  - `role: str`, `content: str`
- `ProfileRequest`
  - `category: str`, `key: str`, `value: Any`
- `ProfileResponse`
  - `success: bool`, `message: str`, `profile?: dict`
