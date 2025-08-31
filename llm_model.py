import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

class load_model:
    def load_llm():
        load_dotenv()
        os.environ["LANGCHAIN_PROJECT"] = "langchain_streamlit"
        llm = ChatGoogleGenerativeAI(
            model = "gemini-2.5-flash",
            temperature=0.4,
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        return llm

    def load_chain(llm):
        chain = llm | StrOutputParser()
        return chain