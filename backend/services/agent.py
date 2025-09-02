"""ReAct 에이전트 실행 서비스.

MCP 도구와(대화 기록/시각화) RAG 검색 도구를 조합해 사용자 질문에 답변합니다.
사용자 프로필과 파일 정보를 system 메시지로 주입해 개인화/문맥화를 강화합니다.
"""

import os
import sys
from typing import Any, Dict, List

from core.llm.factory import get_llm
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain.tools.retriever import create_retriever_tool


# Load LLM once
LLM = get_llm()

# MCP server parameters
SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["-u", os.path.abspath("MCP/server.py")],
)


async def run_agent(
    user_input: str,
    conversation_history: List[Dict[str, Any]] | None,
    global_state: Dict[str, Any],
    user_profile,
) -> str:
    """가용 도구와 컨텍스트를 사용해 ReAct 에이전트를 실행합니다."""
    try:
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                try:
                    mcp_tools = await load_mcp_tools(session)
                    tools = list(mcp_tools)
                except Exception as e:
                    print(f"Warning: Failed to load MCP tools: {e}")
                    tools = []

                # Attach retriever tool if present
                if global_state.get("retriever"):
                    try:
                        retriever_tool = create_retriever_tool(
                            global_state["retriever"],
                            name="doc_search",
                            description=(
                                "업로드된 문서에서 질문과 관련된 내용을 찾습니다. "
                                "요약/개요/핵심 정리 등도 이 도구로 필요한 근거를 수집한 후 작성하세요."
                            ),
                        )
                        tools.append(retriever_tool)
                    except Exception as e:
                        print(f"Warning: Failed to add retriever tool: {e}")

                agent = create_react_agent(LLM, tools)

                messages: List[Dict[str, str]] = []

                # Inject user profile
                try:
                    profile_summary = user_profile.get_profile_summary()
                    if profile_summary != "사용자 프로필 정보가 없습니다.":
                        messages.append(
                            {
                                "role": "system",
                                "content": (
                                    f"사용자 프로필 정보:\n{profile_summary}\n\n"
                                    f"위 정보를 바탕으로 개인화된 답변을 제공해주세요."
                                ),
                            }
                        )
                except Exception as e:
                    print(f"Warning: Failed to get profile summary: {e}")

                # Inject file-aware context
                if global_state.get("meta"):
                    file_info = global_state["meta"]
                    messages.append(
                        {
                            "role": "system",
                            "content": (
                                "현재 업로드된 파일 정보:\n"
                                f"- 파일명: {file_info.get('raw_path', '').split('/')[-1] if file_info.get('raw_path') else '알 수 없음'}\n"
                                f"- 형식: {file_info.get('ext', '알 수 없음')}\n"
                                f"- 컬럼: {', '.join(file_info.get('columns', []))}\n"
                                f"- 전체 데이터 크기: {file_info.get('shape_total', '알 수 없음')}\n\n"
                                "사용자가 파일에 대해 질문하면 doc_search 도구를 사용하여 파일 내용을 검색하고 분석해주세요."
                            ),
                        }
                    )

                if conversation_history:
                    messages.append(
                        {
                            "role": "system",
                            "content": "이전 대화 내용을 참고하여 맥락을 이해하고 답변해주세요.",
                        }
                    )
                    for msg in conversation_history[-5:]:
                        messages.append({"role": msg["role"], "content": msg["content"]})

                messages.append({"role": "user", "content": user_input})

                response = await agent.ainvoke({"messages": messages})
                answer = response["messages"][-1].content
                return answer
    except Exception as e:
        print(f"Error in run_agent: {e}")
        return f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"
