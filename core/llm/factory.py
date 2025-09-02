"""LLM 생성 팩토리.

환경변수(.env)를 로드하고, 지정된 모델/온도로 LangChain LLM 인스턴스를 생성합니다.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser


def get_llm(model: str = "gemini-2.5-flash", temperature: float = 0.4):
    """LLM 인스턴스를 반환합니다.

    Args:
        model: 모델 이름(Google Generative AI)
        temperature: 생성 온도
    """
    load_dotenv()
    os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGCHAIN_PROJECT", "langchain_streamlit")
    return ChatGoogleGenerativeAI(model=model, temperature=temperature, api_key=os.getenv("GOOGLE_API_KEY"))


def get_chain(llm):
    """간단한 체인(LLM → 문자열 파서)을 구성해 반환합니다."""
    return llm | StrOutputParser()
