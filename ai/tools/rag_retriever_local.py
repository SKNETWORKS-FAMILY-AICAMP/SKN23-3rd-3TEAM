# ai/tools/rag_retriever_local.py
import os
import chromadb
from chromadb.utils import embedding_functions
from functools import lru_cache

DB_PATH = os.environ.get("CHROMA_DB_PATH", "./vector_store")
COLLECTION_NAME = os.environ.get("CHROMA_COLLECTION", "skin_knowledge_base")
EMBED_MODEL_NAME = os.environ.get("EMBED_MODEL_NAME", "jhgan/ko-sroberta-multitask")

@lru_cache(maxsize=1)
def get_local_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL_NAME)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

@lru_cache(maxsize=512)
def _embed_query_cached(qtext: str):
    col = get_local_collection()
    ef = getattr(col, "_embedding_function", None) or getattr(col, "embedding_function", None)
    if ef is None:
        raise AttributeError("No embedding function found on collection")
    return ef([qtext])[0]

def retrieve(query: str, k: int = 5, where: dict | None = None):
    col = get_local_collection()

    # query_embeddings 우선, 실패하면 query_texts fallback
    try:
        qvec = _embed_query_cached(query)
        res = col.query(
            query_embeddings=[qvec],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        res = col.query(
            query_texts=[query],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

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
        dist = float(d.get("distance", 2.0))

        # ✅ cosine distance가 0~2일 수도 있으니 정규화
        score = 1.0 - min(max(dist / 2.0, 0.0), 1.0)

        passages.append({
            "source_id": meta.get("source_id") or meta.get("doc_id") or meta.get("id") or "unknown",
            "snippet": d.get("text", ""),
            "distance": dist,
            "score": score,
            "meta": meta,
        })
    return passages