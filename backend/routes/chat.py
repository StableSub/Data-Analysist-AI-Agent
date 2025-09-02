from typing import Dict, Any, List

from fastapi import APIRouter

from backend.schemas.chat import ChatMessage, ChatRequest, ChatResponse
from backend.services.agent import run_agent
from backend.state import conversation_memory, global_state, restore_uploaded_files, user_profile


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:

        if not global_state.get("meta"):
            restore_uploaded_files()

        current_file_info = None
        if global_state.get("meta"):
            current_file_info = {
                "filename": global_state["meta"].get("raw_path", "").split("/")[-1]
                if global_state["meta"].get("raw_path")
                else "알 수 없음",
                "columns": global_state["meta"].get("columns", []),
                "shape_total": global_state["meta"].get("shape_total"),
                "ext": global_state["meta"].get("ext", ""),
            }
        
        # 사용자가 업로드 된 파일을 원하면, 파일 이름을 추출.
        enhanced_message = conversation_memory.enhance_message_with_file_context(
            request.message, current_file_info
        )

        # 유저의 질문을 데이터 베이스에 저장.
        conversation_memory.add_message(
            role="user", content=enhanced_message, file_context=current_file_info
        )

        recent_messages = conversation_memory.get_recent_messages(limit=10)
        response = await run_agent(enhanced_message, recent_messages, global_state, user_profile)

        conversation_memory.add_message(
            role="assistant", content=response, file_context=current_file_info
        )

        recent_messages = conversation_memory.get_recent_messages(limit=50)
        api_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in recent_messages]

        return ChatResponse(response=response, messages=api_messages)

    except Exception as e:
        error_response = f"에러가 발생했습니다: {str(e)}"
        conversation_memory.add_message(role="assistant", content=error_response)
        recent_messages = conversation_memory.get_recent_messages(limit=50)
        api_messages = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in recent_messages]
        return ChatResponse(response=error_response, messages=api_messages)


@router.get("/messages")
async def get_messages():
    recent_messages = conversation_memory.get_recent_messages(limit=100)
    api_messages = [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]
    return {"messages": api_messages}

