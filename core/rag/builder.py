"""CSV 파일을 임베딩해 검색용 Retriever로 변환하는 빌더.

단순화를 위해 전체 행을 문서로 변환하여 FAISS에 색인합니다. 대용량 CSV의 경우
메모리 사용량이 커질 수 있으니, 실제 운영에서는 청크/샘플링 도입을 고려하세요.
"""

import pandas as pd
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


def build_retriever_from_csv(uploaded_file, k: int = 3):
    """CSV 경로를 받아 Retriever 객체를 생성합니다.

    Args:
        uploaded_file: CSV 파일 경로(str 또는 Path)
        k: 검색 시 반환할 문서 개수
    """
    df = pd.read_csv(uploaded_file)

    docs = []
    for i, row in df.iterrows():
        content = row.to_json(force_ascii=False)
        docs.append(Document(page_content=content, metadata={"row": i}))

    embed = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vs = FAISS.from_documents(docs, embed)
    return vs.as_retriever(search_kwargs={"k": k})
