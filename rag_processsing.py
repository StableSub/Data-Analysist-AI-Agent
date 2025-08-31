import pandas as pd
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# CSV → Retriever 생성 (진행률 표시 없이 단순화)
def build_retriever_from_csv(uploaded_file, k: int = 3):
    df = pd.read_csv(uploaded_file)

    docs = []
    total = len(df)

    for i, row in df.iterrows():
        content = row.to_json(force_ascii=False)
        docs.append(Document(page_content=content, metadata={"row": i}))

    # 벡터스토어 & retriever 생성
    embed = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vs = FAISS.from_documents(docs, embed)

    return vs.as_retriever(search_kwargs={"k": k})