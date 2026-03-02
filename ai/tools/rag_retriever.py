"""
rag_retriever.py
intent별로 ChromaDB 검색 전략을 다르게 적용합니다.

[속도 문제 해결]
Streamlit은 스크립트를 재실행할 때 전역변수를 초기화합니다.
따라서 _collection을 전역변수로 두면 매번 재로드됩니다.
→ st.cache_resource 대신 모듈 레벨에서 즉시 로드합니다.
"""
import os
import sys
import time
from functools import lru_cache

import chromadb
from chromadb.utils import embedding_functions

from ai.config.settings import (
    CHROMA_DB_PATH, CHROMA_COLLECTION, EMBED_MODEL_NAME,
    RAG_TOP_K_DEFAULT, RAG_TOP_K_PRODUCT,
)

# tagging 유틸 경로 연결
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(_ROOT, "back", "vector", "utils"))
try:
    from tagging import match_tags, SKIN_TYPE_RULES, CONCERN_TAG_RULES, INGREDIENT_TAG_RULES
except ImportError:
    # tagging 모듈 없을 때 fallback
    def match_tags(text, rules): return []
    SKIN_TYPE_RULES = CONCERN_TAG_RULES = INGREDIENT_TAG_RULES = {}


# ── 임베딩 함수 싱글톤 (모듈 import 시 1회만 생성) ─────────────
print("[RAG] 임베딩 모델 초기화 중...", flush=True)
_t0 = time.perf_counter()
_embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL_NAME
)
_chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
_collection = _chroma_client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    embedding_function=_embed_fn,
    metadata={"hnsw:space": "cosine"},
)
print(f"[RAG] 임베딩 모델 초기화 완료! ({time.perf_counter()-_t0:.2f}s)", flush=True)


def warmup():
    """이미 모듈 로드 시 초기화됨. 하위호환용으로만 존재."""
    print("[RAG] warmup 호출됨 (이미 초기화 완료)", flush=True)


@lru_cache(maxsize=512)
def _embed_cached(text: str):
    """쿼리 임베딩 캐싱 - 동일 쿼리는 재계산 없이 즉시 반환"""
    return _embed_fn([text])[0]


# ── where 필터 생성 ───────────────────────────────────────────
def _build_where(intent: str, query: str, user_profile: dict | None) -> dict | None:
    """
    intent + 프로필 기반 ChromaDB where 필터 생성.

    [변경사항]
    - product_recommend: 이제 Tavily 직접 검색으로 대체됨 → RAG 호출 안 함
    - routine_and_product: 루틴/가이드 정보 검색 (가이드+질환)
    - routine_advice에 routine_and_product 추가
    """
    doc_type_map = {
        "general_advice":        ["guide", "disease"],
        "routine_advice":        ["guide"],
        "routine_and_product":   ["guide", "disease"],  # 루틴 파트 담당 (제품은 Tavily)
        "medical_advice":        ["guide", "disease"],
        "ingredient_question":   ["ingredient", "cosmetic_product"],
        "ingredient_analysis":   ["ingredient", "cosmetic_product"],
        "skin_analysis_fast":    ["guide"],
        "skin_analysis_deep":    ["guide"],
        "history_compare":       ["guide"],
    }
    allowed_types = doc_type_map.get(intent)
    if not allowed_types:
        return None

    if len(allowed_types) == 1:
        return {"doc_type": {"$eq": allowed_types[0]}}
    return {"$or": [{"doc_type": {"$eq": t}} for t in allowed_types]}


def _enrich_query(query: str, intent: str, user_profile: dict | None) -> str:
    """
    벡터 검색 정확도를 높이기 위해 쿼리에 프로필 정보를 추가합니다.
    where 필터 대신 쿼리 자체를 풍부하게 만드는 전략입니다.

    예) "수분크림 추천해줘" + 건성 + 수분부족
     → "수분크림 추천 건성 피부 보습 수분 moisturizing dry skin cream"
    """
    enriched = query

    if user_profile:
        skin_type = user_profile.get("skin_type_label") or ""
        concern = user_profile.get("skin_concern") or ""
        if skin_type:
            enriched += f" {skin_type} 피부"
        if concern:
            enriched += f" {concern}"

    # intent별 키워드 보강
    if intent == "product_recommend":
        enriched += " 화장품 추천 제품"
    elif intent in ("general_advice", "routine_advice", "routine_and_product"):
        enriched += " 피부 관리 루틴"
    elif intent in ("ingredient_question", "ingredient_analysis"):
        enriched += " 성분 효능"

    return enriched.strip()


def _query_with_fallback(query: str, where: dict | None, top_k: int) -> dict:
    """
    where 필터로 검색 → 결과 부족 시 필터 없이 재검색 (fallback)
    """
    def _do_query(w):
        try:
            qvec = _embed_cached(query)
            return _collection.query(
                query_embeddings=[qvec],
                n_results=top_k,
                where=w,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            print(f"[RAG] 임베딩 검색 실패, query_texts 방식으로 재시도: {e}", flush=True)
            return _collection.query(
                query_texts=[query],
                n_results=top_k,
                where=w,
                include=["documents", "metadatas", "distances"],
            )

    res = _do_query(where)
    docs = (res.get("documents") or [[]])[0]

    if len(docs) < 2 and where is not None:
        print(f"[RAG] 필터 결과 부족({len(docs)}개) → 필터 제거 후 재검색", flush=True)
        res = _do_query(None)

    return res


def _to_passages(res: dict) -> list:
    """ChromaDB 결과 → passage 리스트 변환"""
    documents = (res.get("documents") or [[]])[0]
    metadatas = (res.get("metadatas") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]

    passages = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        meta = meta or {}
        score = round(1.0 - min(max(float(dist) / 2.0, 0.0), 1.0), 4)
        passages.append({
            "source_id": (
                meta.get("source_id") or meta.get("doc_id")
                or meta.get("id") or "unknown"
            ),
            "snippet": doc,
            "score": score,
            "meta": meta,
        })
    return passages


# ── 메인 검색 함수 ────────────────────────────────────────────
def search(
    query: str,
    intent: str,
    user_profile: dict | None = None,
    top_k: int | None = None,
) -> list:
    """
    intent와 user_profile 기반으로 ChromaDB를 검색합니다.

    전략:
    1. doc_type 필터만 적용 (skin_type/concern_tag 필터 제거 - 데이터 불완전)
    2. 쿼리에 프로필 정보 추가 (벡터 유사도로 관련 문서 탐색)
    3. 결과 부족 시 필터 없이 재검색
    """
    if top_k is None:
        # routine_and_product는 루틴 정보를 더 많이 가져옴
        top_k = RAG_TOP_K_DEFAULT

    where = _build_where(intent, query, user_profile)
    enriched_query = _enrich_query(query, intent, user_profile)

    print(f"[RAG] 검색 쿼리: '{enriched_query[:80]}'", flush=True)
    print(f"[RAG] where 필터: {where}", flush=True)

    res = _query_with_fallback(enriched_query, where, top_k)
    return _to_passages(res)
