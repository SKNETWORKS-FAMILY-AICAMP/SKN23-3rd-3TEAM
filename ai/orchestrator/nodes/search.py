"""
nodes/search.py
needs_rag / needs_product 플래그에 따라 RAG와 Tavily를 실행합니다.
두 플래그가 모두 True면 ThreadPoolExecutor로 병렬 실행합니다.
기존 pipeline.py의 Step 5에 해당합니다.

[변경] 분석 intent일 때 vision_result 수치로 피부타입을 계산해서
       RAG 쿼리에 반영합니다. (user_profile skin_type 영향 차단)
"""
import time
from concurrent.futures import ThreadPoolExecutor

from ai.orchestrator.state import GraphState
from ai.tools import rag_retriever
from ai.tools.oliveyoung import search_products_for_context

# 피부 분석 intent - RAG 쿼리에서 skin_type/concern 제거 대상
_ANALYSIS_INTENTS = {"skin_analysis_fast", "skin_analysis_deep"}


def _infer_skin_type_from_metrics(vision_result: dict | None) -> str | None:
    """
    fast_model skin_metrics 수치로 피부타입을 추론합니다.
    LLM 없이 규칙 기반으로 빠르게 계산합니다.

    수치 범위: 0~1
    - moisture  : 높을수록 수분 충분
    - pore      : 높을수록 모공 큼 (지성 지표)
    - pigmentation: 높을수록 색소침착 많음 (지성 지표)
    - elasticity: 높을수록 탄력 좋음
    """
    if not vision_result:
        return None

    mode = vision_result.get("mode")

    if mode == "fast":
        metrics = vision_result.get("skin_metrics", {})
        if not metrics:
            return None

        moisture = metrics.get("moisture", {}).get("value", 0.5)
        pore = metrics.get("pore", {}).get("value", 0.3)
        pigmentation = metrics.get("pigmentation", {}).get("value", 0.3)
        elasticity = metrics.get("elasticity", {}).get("value", 0.5)

        # 모델 출력값이 0.4~0.6 사이에 집중되므로 중앙값(0.5) 기준으로 판단
        # 지성: 모공 높음(0.5↑) + 색소침착 높음(0.5↑)
        if pore >= 0.5 and pigmentation >= 0.5:
            return "지성"
        # 건성: 수분 낮음(0.45↓) - 모공과 무관하게 건성 우선
        if moisture <= 0.45:
            return "건성"
        # 복합성: 수분 보통(0.48↓) + 모공 다소 높음(0.45↑)
        if moisture <= 0.48 and pore >= 0.45:
            return "복합성"
        # 중성: 수분 양호(0.5↑) + 모공 낮음(0.45↓)
        if moisture >= 0.5 and pore <= 0.45:
            return "중성"
        # 기본값
        return "복합성"

    elif mode == "deep":
        measurements = vision_result.get("measurements", {})
        if not measurements:
            return None

        # ── 수분 관련 수치 수집 ──────────────────────────────
        moisture_keys = [k for k in measurements if "moisture" in k]
        moisture_vals = [measurements[k] for k in moisture_keys if measurements[k] is not None]
        avg_moisture  = sum(moisture_vals) / len(moisture_vals) if moisture_vals else 50
        min_moisture  = min(moisture_vals) if moisture_vals else 50

        l_cheek_m = measurements.get("l_cheek_moisture")
        r_cheek_m = measurements.get("r_cheek_moisture")
        cheek_diff = abs(l_cheek_m - r_cheek_m) if (l_cheek_m and r_cheek_m) else 0

        chin_moisture = measurements.get("chin_moisture", 50)

        # ── 모공 수치 수집 ────────────────────────────────────
        l_pore = measurements.get("l_cheek_pore", 0) or 0
        r_pore = measurements.get("r_cheek_pore", 0) or 0
        avg_pore = (l_pore + r_pore) / 2 if (l_pore or r_pore) else 0
        max_pore = max(l_pore, r_pore)

        # ── 탄력 수치 수집 ────────────────────────────────────
        elasticity_keys = [k for k in measurements if k.endswith("_R2")]
        elasticity_vals = [measurements[k] for k in elasticity_keys if measurements[k] is not None]
        avg_elasticity  = sum(elasticity_vals) / len(elasticity_vals) if elasticity_vals else 0.5
        min_elasticity  = min(elasticity_vals) if elasticity_vals else 0.5

        # ── 기타 ─────────────────────────────────────────────
        pigmentation = measurements.get("pigmentation_count", 100) or 100

        # ── 피부타입 판단 (우선순위 순) ───────────────────────
        # 민감성: 탄력 전체 낮음 + 색소침착 있음 (피부 장벽 약화 신호)
        if avg_elasticity <= 0.47 and min_elasticity <= 0.42 and pigmentation >= 130:
            return "민감성"

        # 건성: 어느 한 부위라도 수분이 매우 낮거나, 전체 평균 낮음
        if min_moisture <= 45 or avg_moisture <= 52:
            # 단, 모공이 매우 크면 복합성으로 판단
            if max_pore < 700:
                return "건성"

        # 지성: 모공이 크고 색소침착도 있음
        if avg_pore >= 900 and pigmentation >= 130:
            return "지성"

        # 복합성: 좌우 수분 차이가 크거나, 모공 크고 수분 낮은 부위 공존
        if cheek_diff >= 15:
            return "복합성"
        if max_pore >= 700 and min_moisture <= 55:
            return "복합성"

        # 중성: 위 조건 어디도 안 걸림
        return "중성"

    return None


def _build_rag_query(
    user_text: str,
    intent: str,
    vision_result: dict | None,
) -> str:
    """
    intent별 RAG 쿼리 생성.
    분석 intent일 때 vision 수치로 피부타입을 계산해서 쿼리에 추가합니다.
    """
    query = user_text

    if intent in _ANALYSIS_INTENTS:
        # 수치 기반 피부타입으로 RAG 쿼리 생성
        skin_type = _infer_skin_type_from_metrics(vision_result)
        if skin_type:
            query = f"{skin_type} 피부 관리 루틴 스킨케어"
            print(f"[SEARCH] 수치 기반 피부타입: {skin_type} → RAG 쿼리: '{query}'", flush=True)
        else:
            query = "피부 관리 루틴 스킨케어"
        return query

    if vision_result and vision_result.get("qc", {}).get("status") != "fail":
        findings = vision_result.get("findings", [])
        top = sorted(findings, key=lambda x: x.get("score", 0), reverse=True)[:2]
        tags = [
            f"{f.get('region','')}-{f.get('name','')}"
            for f in top if f.get("name")
        ]
        if tags:
            query += " " + " ".join(tags)

    if intent == "routine_and_product":
        query += " 루틴 관리법 스킨케어"

    return query


def _get_rag_profile(intent: str, user_profile: dict | None) -> dict | None:
    """
    분석 intent일 때는 RAG에 넘기는 user_profile에서 skin_type/concern 제거.
    """
    if intent not in _ANALYSIS_INTENTS:
        return user_profile

    if not user_profile:
        return None

    return {
        "user_id": user_profile.get("user_id"),
        "skin_type_label": None,
        "skin_concern": None,
        "age": user_profile.get("age"),
        "gender": user_profile.get("gender"),
        "recent_analysis_summary": None,
    }


def search_node(state: GraphState) -> GraphState:
    """
    [search_node]
    입력: route, user_text, user_profile, vision_result
    출력: rag_passages, oliveyoung_products
    """
    route = state["route"]
    user_text = state["user_text"]
    user_profile = state.get("user_profile")
    vision_result = state.get("vision_result")

    # 수치 로그 (분석 intent일 때)
    if route.intent in _ANALYSIS_INTENTS and vision_result:
        mode = vision_result.get("mode")
        if mode == "fast":
            print(f"[VISION METRICS] {vision_result.get('skin_metrics')}", flush=True)
        elif mode == "deep":
            print(f"[VISION METRICS] {vision_result.get('measurements')}", flush=True)

    rag_passages: list = []
    oliveyoung_products: list = []

    def _run_rag():
        query = _build_rag_query(user_text, route.intent, vision_result)
        rag_profile = _get_rag_profile(route.intent, user_profile)
        # 분석 intent는 RAG를 관리법 참고용으로만 사용 → 3개로 줄여 토큰 절약
        _ANALYSIS_INTENTS = {"skin_analysis_fast", "skin_analysis_deep", "ingredient_analysis"}
        top_k = 3 if route.intent in _ANALYSIS_INTENTS else None
        return rag_retriever.search(
            query=query,
            intent=route.intent,
            user_profile=rag_profile,
            top_k=top_k,
        )

    def _run_tavily():
        return search_products_for_context(
            user_text=user_text,
            user_profile=user_profile,
            max_products=3,
        )

    t0 = time.perf_counter()

    if route.needs_rag and route.needs_product:
        print("[SEARCH] RAG + Tavily 병렬 실행", flush=True)
        with ThreadPoolExecutor(max_workers=2) as executor:
            rag_future = executor.submit(_run_rag)
            tavily_future = executor.submit(_run_tavily)

        try:
            rag_passages = rag_future.result()
            print(f"[RAG] {len(rag_passages)}개 passage", flush=True)
            for i, p in enumerate(rag_passages[:5]):
                meta = p.get("meta", {})
                print(
                    f"  [RAG {i}] score={round(p.get('score',0),3)}"
                    f" | doc_type={meta.get('doc_type','?')}"
                    f" | snippet={p.get('snippet','')[:50]}",
                    flush=True
                )
        except Exception as e:
            print(f"[RAG ERROR] {repr(e)}", flush=True)

        try:
            oliveyoung_products = tavily_future.result()
        except Exception as e:
            print(f"[TAVILY ERROR] {repr(e)}", flush=True)

    elif route.needs_rag:
        try:
            rag_passages = _run_rag()
            print(f"[RAG] {len(rag_passages)}개 passage", flush=True)
            for i, p in enumerate(rag_passages[:5]):
                meta = p.get("meta", {})
                print(
                    f"  [RAG {i}] score={round(p.get('score',0),3)}"
                    f" | doc_type={meta.get('doc_type','?')}"
                    f" | snippet={p.get('snippet','')[:50]}",
                    flush=True
                )
        except Exception as e:
            print(f"[RAG ERROR] {repr(e)}", flush=True)

    elif route.needs_product:
        try:
            oliveyoung_products = _run_tavily()
        except Exception as e:
            print(f"[TAVILY ERROR] {repr(e)}", flush=True)

    print(f"[TIMER] search_node: {time.perf_counter()-t0:.3f}s", flush=True)

    return {
        "rag_passages": rag_passages,
        "oliveyoung_products": oliveyoung_products,
    }
