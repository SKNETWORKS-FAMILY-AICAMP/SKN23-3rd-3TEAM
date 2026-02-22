import os
import chromadb
from chromadb.utils import embedding_functions

DB_PATH = os.environ.get("CHROMA_DB_PATH", "./vector_store")
COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "skin_knowledge_base")
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL_NAME", "jhgan/ko-sroberta-multitask")

_collection = None  # ✅ 캐시

def get_local_collection():
    global _collection
    if _collection is not None:
        return _collection

    client = chromadb.PersistentClient(path=DB_PATH)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL_NAME
    )

    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection

def retrieve(query: str, k: int = 5, where: dict | None = None):
    col = get_local_collection()
    res = col.query(
        query_texts=[query],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # ✅ 안전 처리
    documents = (res.get("documents") or [[]])[0]
    metadatas = (res.get("metadatas") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]

    docs = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        docs.append({"text": doc, "meta": meta or {}, "distance": float(dist)})
    return docs

def search(query: str, top_k: int = 3, where: dict | None = None):
    docs = retrieve(query=query, k=top_k, where=where)

    passages = []
    for d in docs:
        meta = d.get("meta") or {}
        dist = float(d.get("distance", 1.0))
        passages.append({
            "source_id": meta.get("source_id") or meta.get("doc_id") or meta.get("id") or "unknown",
            "snippet": d.get("text", ""),
            "distance": dist,
            "score": 1.0 - min(max(dist, 0.0), 1.0),  # 참고용
            "meta": meta,
        })
    return passages