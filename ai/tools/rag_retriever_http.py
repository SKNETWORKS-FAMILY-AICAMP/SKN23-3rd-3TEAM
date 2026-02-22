import os
import chromadb
from chromadb.utils import embedding_functions

NGROK_HOST = os.environ.get("CHROMA_HOST", "<NGROK_HOST>")
COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "skin_knowledge_base")
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL_NAME", "jhgan/ko-sroberta-multitask")

def get_remote_collection():
    client = chromadb.HttpClient(
        host=NGROK_HOST,
        port=443,
        ssl=True,
        headers={"ngrok-skip-browser-warning": "true"},
    )

    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL_NAME
    )

    # get_collection에 embedding_function을 넣어두면 query_texts로 바로 질의 가능
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )
    return collection

def retrieve(query: str, k: int = 5, where: dict | None = None):
    col = get_remote_collection()
    res = col.query(
        query_texts=[query],
        n_results=k,
        # where=where,
        include=["documents", "metadatas", "distances"],
    )
    # RAG에 넣기 좋은 형태로 정리
    docs = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        docs.append({"text": doc, "meta": meta, "score": float(dist)})
    return docs