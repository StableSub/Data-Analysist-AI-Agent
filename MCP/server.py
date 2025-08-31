import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# 대화 메모리 관리를 위한 import 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from conversation_memory import get_memory

mcp = FastMCP("DataAnalysis")

# 전역 변수
global_df = None
data_dir = Path("data")

@mcp.prompt()
def default_prompt(message) -> list[base.Message]:
    return [
        base.AssistantMessage(
            "You are a helpful data analysis assistant. \n"
            "Please clearly organize and return the results of the tool calling and the data analysis. \n"
            "Use the available tools to analyze data, create visualizations, and provide insights."
        ),
        base.UserMessage(message),
    ]

# 대화 메모리 관리 도구들
@mcp.tool()
async def get_conversation_history(limit: int = 20, user_id: str = "default") -> str:
    """사용자의 이전 대화 기록을 조회합니다."""
    try:
        memory = get_memory(user_id)
        if memory is None:
            return "대화 메모리 시스템을 사용할 수 없습니다."
        
        messages = memory.get_recent_messages(limit=limit)
        
        if not messages:
            return "저장된 대화 기록이 없습니다."
        
        history = f"최근 {len(messages)}개의 대화 기록:\n" + "="*50 + "\n"
        
        for i, msg in enumerate(messages, 1):
            role_name = "사용자" if msg["role"] == "user" else "어시스턴트"
            timestamp = msg.get("timestamp", "시간 정보 없음")
            history += f"\n[{i}] {role_name} ({timestamp}):\n{msg['content']}\n" + "-"*30 + "\n"
        return history
        
    except Exception as e:
        return f"대화 기록 조회 중 오류 발생: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")