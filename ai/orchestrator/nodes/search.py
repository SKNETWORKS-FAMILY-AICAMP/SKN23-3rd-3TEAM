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

        # ── 모델 출력 범위: 0.4~0.6 중심 (Sigmoid 특성)
        # 상대적 순위 기반으로 판단하여 5가지 타입 골고루 분류

        # 1. 종합 점수 계산 (각 지표의 상대적 위치)
        #    moisture, elasticity: 높을수록 좋음 → 그대로 사용
        #    wrinkle, pore, pigmentation: 낮을수록 좋음 → 1에서 빼기
        wrinkle = metrics.get("wrinkle", {}).get("value", 0.5)

        good_score = (moisture + elasticity + (1 - wrinkle) + (1 - pore) + (1 - pigmentation)) / 5
        oily_score = pore * 0.5 + pigmentation * 0.3 + (1 - moisture) * 0.2
        dry_score = (1 - moisture) * 0.5 + (1 - elasticity) * 0.3 + (1 - pore) * 0.2

        # 2. 민감성: 탄력 낮고 + 색소침착 높고 + 주름도 높음 (장벽 약화 시그널)
        if elasticity <= 0.46 and pigmentation >= 0.50 and wrinkle >= 0.50:
            return "민감성"

        # 3. 건성: 수분이 상대적으로 가장 부족한 경우
        if moisture <= 0.46 and pore <= 0.48:
            return "건성"

        # 4. 지성: 모공+색소침착이 높은 경우 (수분과 무관)
        if pore >= 0.48 and pigmentation >= 0.50:
            # 단, 수분도 낮으면 복합성
            if moisture <= 0.46:
                return "복합성"
            return "지성"

        # 5. 복합성: 수분 부족 + 모공 큼 (부위별 불균형 시그널)
        if moisture <= 0.48 and pore >= 0.46:
            return "복합성"

        # 6. 중성: 전반적으로 양호하거나 어디에도 치우치지 않음
        if good_score >= 0.50:
            return "중성"

        # 7. 기본값: 점수 기반 판단
        scores = {
            "건성": dry_score,
            "지성": oily_score,
            "중성": good_score,
            "복합성": 0.5,  # 기본 경쟁력
        }
        return max(scores, key=scores.get)

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
        wrinkle_keys = [k for k in measurements if k.endswith("_Ra")]
        wrinkle_vals = [measurements[k] for k in wrinkle_keys if measurements[k] is not None]
        avg_wrinkle = sum(wrinkle_vals) / len(wrinkle_vals) if wrinkle_vals else 20

        # 1. 민감성: 탄력 전반적 낮음 + 주름 or 색소 문제
        if avg_elasticity <= 0.48 and (avg_wrinkle >= 22 or pigmentation >= 120):
            return "민감성"

        # 2. 건성: 수분 중심 판단 (모공과 무관하게)
        #    이마/턱/볼 중 2곳 이상 수분 부족하면 건성
        dry_zones = 0
        if measurements.get("forehead_moisture", 60) <= 55:
            dry_zones += 1
        if measurements.get("chin_moisture", 60) <= 50:
            dry_zones += 1
        if min_moisture <= 55:
            dry_zones += 1
        if avg_moisture <= 55:
            dry_zones += 1

        if dry_zones >= 3 and avg_elasticity <= 0.50:
            return "건성"
        if avg_moisture <= 53:
            return "건성"

        # 3. 지성: 모공 매우 크고 + 수분 충분 (건조하지 않은 상태에서 모공만 큼)
        if avg_pore >= 900 and avg_moisture >= 62:
            return "지성"

        # 4. 복합성: 부위별 불균형이 명확한 경우
        if cheek_diff >= 12:
            return "복합성"
        if max_pore >= 900 and min_moisture <= 52:
            return "복합성"

        # 5. 중성: 수분 양호 + 탄력 양호 + 극단적 항목 없음
        if avg_moisture >= 60 and avg_elasticity >= 0.50 and avg_pore <= 800:
            return "중성"

        # 6. 점수 기반 폴백 (모공 비중 축소, 수분/탄력 비중 확대)
        scores = {
            "건성": (65 - avg_moisture) / 50 * 0.5 + (0.55 - avg_elasticity) * 0.3 + dry_zones * 0.1,
            "지성": avg_pore / 2000 * 0.4 + pigmentation / 300 * 0.3 + (avg_moisture - 50) / 50 * 0.3,
            "복합성": cheek_diff / 30 * 0.4 + abs(avg_pore - 700) / 2000 * 0.3 + (65 - avg_moisture) / 50 * 0.3,
            "중성": avg_moisture / 80 * 0.3 + avg_elasticity * 0.4 + (1200 - avg_pore) / 2000 * 0.3,
        }
        return max(scores, key=scores.get)

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

        # 규칙 기반 피부타입을 vision_result에 확정값으로 주입
        determined_type = _infer_skin_type_from_metrics(vision_result)
        if determined_type:
            vision_result["determined_skin_type"] = determined_type
            print(f"[SEARCH] 확정 피부타입: {determined_type}", flush=True)

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
