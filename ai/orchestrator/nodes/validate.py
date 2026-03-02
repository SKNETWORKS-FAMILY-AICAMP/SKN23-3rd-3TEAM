"""
nodes/validate.py
LLM 출력을 검증하고 올리브영 링크를 반영해서 최종 응답을 만듭니다.
기존 pipeline.py의 Step 7 + Step 8 + Step 9 + Step 10에 해당합니다.
"""
import json
import os
import time
from ai.orchestrator.state import GraphState
from ai.llm.validators import validate_report


def _append_oliveyoung_links(chat_answer: str, products: list[dict]) -> str:
    """chat_answer 끝에 올리브영 구매 링크 섹션 추가
    형식: - [제품명](URL) | URL: https://...
    """
    links = []
    for p in products:
        url     = p.get("oliveyoung_url", "")
        display = p.get("display_name") or p.get("name", "")
        if not url or not display:
            continue
        # 제품명에 하이퍼링크 + URL 텍스트 병기
        links.append(f"- [{display}]({url})  \n  🔗 {url}")
    if not links:
        return chat_answer
    return (
        (chat_answer or "").rstrip() +
        "\n\n---\n**🛒 올리브영 구매 링크**\n" + "\n".join(links)
    )


def _save_run(state: GraphState, report: dict):
    """실행 결과를 파일로 저장 (디버그용)"""
    try:
        from ai.config.settings import RUNS_DIR
        ts = time.strftime("%Y%m%d-%H%M%S")
        run_dir = os.path.join(RUNS_DIR, ts)
        os.makedirs(run_dir, exist_ok=True)
        route = state.get("route")
        payloads = {
            "request": {
                "user_text": state.get("user_text"),
                "analysis_type": state.get("analysis_type"),
                "user_id": state.get("user_id"),
                "n_images": len(state.get("images", [])),
            },
            "route": {
                "intent": route.intent if route else None,
                "needs_rag": route.needs_rag if route else None,
                "needs_product": route.needs_product if route else None,
                "reason": route.reason if route else None,
            },
            "tool_outputs": {
                "vision_result": state.get("vision_result"),
                "rag_passages": state.get("rag_passages", []),
                "oliveyoung_products": state.get("oliveyoung_products", []),
            },
            "report": report,
        }
        for name, obj in payloads.items():
            with open(os.path.join(run_dir, f"{name}.json"), "w", encoding="utf-8") as f:
                json.dump(obj, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SAVE_RUN ERROR] {repr(e)}", flush=True)


# ── 피부 수치 → 0~100 정규화 ──────────────────────────────────

def _score_label(score: int) -> str:
    """0~100 점수 → 5단계 label"""
    if score >= 81: return "매우 양호"
    if score >= 61: return "양호"
    if score >= 41: return "보통"
    if score >= 21: return "주의 필요"
    return "개선 필요"


def _normalize_fast(skin_metrics: dict) -> dict:
    """
    fast 결과 skin_metrics → metrics (0~100 score)

    fast value 범위: 0~1
      moisture, elasticity : 높을수록 좋음 → × 100
      wrinkle, pore, pigmentation : 낮을수록 좋음 → (1 - value) × 100
    """
    direction = {
        "moisture"    : "high",
        "elasticity"  : "high",
        "wrinkle"     : "low",
        "pore"        : "low",
        "pigmentation": "low",
    }
    metrics = {}
    for key, d in direction.items():
        item = skin_metrics.get(key)
        if item is None:
            continue
        value = item.get("value", 0.0)
        if d == "high":
            score = round(value * 100)
        else:
            score = round((1.0 - value) * 100)
        score = max(0, min(100, score))
        metrics[key] = {"score": score, "label": _score_label(score)}
    return metrics


def _normalize_deep(measurements: dict) -> dict:
    """
    deep 결과 measurements → metrics (0~100 score)

    measurements 단위:
      moisture      : 0~100  (높을수록 좋음)
      elasticity_R2 : 0~1    (높을수록 좋음 → × 100)
      wrinkle_Ra    : 0~50   (낮을수록 좋음 → (1 - v/50) × 100)
      pore          : 0~2600 (낮을수록 좋음 → (1 - v/2600) × 100)
      pigmentation  : 0~350  (낮을수록 좋음 → (1 - v/350) × 100)
    """
    # moisture: 여러 부위 평균
    moisture_keys = [k for k in measurements if "moisture" in k]
    elasticity_keys = [k for k in measurements if k.endswith("_R2")]
    wrinkle_keys = [k for k in measurements if k.endswith("_Ra")]
    pore_keys = [k for k in measurements if "pore" in k]
    pigment_keys = [k for k in measurements if "pigmentation" in k or "count" in k]

    def avg(keys):
        vals = [measurements[k] for k in keys if measurements.get(k) is not None]
        return sum(vals) / len(vals) if vals else None

    def to_score(value, min_val, max_val, invert=False):
        if value is None:
            return None
        normalized = (value - min_val) / (max_val - min_val) * 100
        score = 100 - normalized if invert else normalized
        return max(0, min(100, round(score)))

    results = {
        "moisture"    : avg(moisture_keys),
        "elasticity"  : avg(elasticity_keys),
        "wrinkle"     : avg(wrinkle_keys),
        "pore"        : avg(pore_keys),
        "pigmentation": avg(pigment_keys),
    }

    conversions = {
        "moisture"    : (0,   100,  False),
        "elasticity"  : (0,   1,    False),
        "wrinkle"     : (0,   50,   True),
        "pore"        : (0,   2600, True),
        "pigmentation": (0,   350,  True),
    }

    metrics = {}
    for key, raw in results.items():
        if raw is None:
            continue
        mn, mx, inv = conversions[key]
        score = to_score(raw, mn, mx, inv)
        if score is not None:
            metrics[key] = {"score": score, "label": _score_label(score)}
    return metrics



def _select_factorial(metrics: dict, skin_type: str | None, mode: str) -> list[str] | None:
    """
    정밀 분석(deep)일 때만 DB keywords 테이블 기반으로 factorial label 2~5개 선택.
    하드코딩 제거 → analysis_service.select_factorial() 위임.
    """
    if mode != "deep":
        return None

    try:
        import sys, os as _os
        _root = _os.path.abspath(
            _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "back")
        )
        if _root not in sys.path:
            sys.path.insert(0, _root)
        from services.analysis_service import select_factorial
        return select_factorial(metrics, min_count=2, max_count=5)
    except Exception as e:
        print(f"[FACTORIAL] DB 조회 실패, 빈 리스트 반환: {repr(e)}", flush=True)
        return []


def _build_analysis_data(
    vision_result: dict,
    llm_output: dict,
) -> dict:
    """
    vision_result(모델 원시값) + llm_output(skin_type 등)
    → DB 저장용 analysis_data JSON 생성

    최종 구조:
    {
        "skin_type": "복합성",
        "skin_type_detail": "T존 피지...",
        "overall_score": 71,
        "metrics": {
            "moisture":     { "score": 65, "label": "보통" },
            ...
        }
    }
    """
    mode = vision_result.get("mode", "")

    # 1. 수치 정규화
    if mode == "fast":
        skin_metrics = vision_result.get("skin_metrics", {})
        metrics = _normalize_fast(skin_metrics)
    elif mode == "deep":
        measurements = vision_result.get("measurements", {})
        metrics = _normalize_deep(measurements)
    else:
        metrics = {}

    # 2. overall_score: metrics score 평균
    if metrics:
        overall_score = round(sum(v["score"] for v in metrics.values()) / len(metrics))
    else:
        overall_score = None

    # 3. skin_type, skin_type_detail: LLM 응답에서 추출
    skin_type        = llm_output.get("skin_type")
    skin_type_detail = llm_output.get("skin_type_detail")

    # 4. factorial: 정밀 분석일 때만 수치 기반 관리 키워드
    factorial = _select_factorial(metrics, skin_type, mode)

    result = {
        "skin_type"       : skin_type,
        "skin_type_detail": skin_type_detail,
        "overall_score"   : overall_score,
        "metrics"         : metrics,
    }
    if factorial is not None:
        result["factorial"] = factorial

    return result


def _save_to_db(state: GraphState, vision_result: dict, llm_output: dict):
    """
    피부 분석 결과를 정규화해서 DB에 저장합니다.

    저장되는 analysis_data 구조:
    {
        "skin_type": "복합성",
        "skin_type_detail": "...",
        "overall_score": 71,
        "metrics": {
            "moisture":     { "score": 65, "label": "보통" },
            "elasticity":   { "score": 62, "label": "보통" },
            "wrinkle":      { "score": 76, "label": "양호" },
            "pore":         { "score": 79, "label": "양호" },
            "pigmentation": { "score": 73, "label": "양호" }
        }
    }
    """
    user_id       = state.get("user_id")
    analysis_type = state.get("analysis_type")

    if not user_id or not analysis_type:
        return
    if not vision_result or vision_result.get("mode") == "error":
        return

    # model_type 매핑: "quick" → "simple", "detailed" → "detailed"
    model_type = "simple" if analysis_type == "quick" else "detailed"

    # vision_result + llm_output → 정규화된 analysis_data
    analysis_data = _build_analysis_data(vision_result, llm_output)

    try:
        import sys, os as _os
        _root = _os.path.abspath(
            _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "back")
        )
        if _root not in sys.path:
            sys.path.insert(0, _root)

        from db.schemas import AnalysisCreate
        from services.analysis_service import save_analysis

        data = AnalysisCreate(
            user_id       = user_id,
            image_url     = state.get("image_urls", []),
            model_type    = model_type,
            analysis_data = analysis_data,
        )
        result = save_analysis(data)
        if result:
            print(
                f"[DB SAVE] 완료: analysis_id={result.analysis_id} "
                f"skin_type={analysis_data.get('skin_type')} "
                f"overall_score={analysis_data.get('overall_score')}",
                flush=True,
            )
    except Exception as e:
        print(f"[DB SAVE ERROR] {repr(e)}", flush=True)


def validate_node(state: GraphState) -> GraphState:
    """
    [validate_node]
    입력: llm_output, route, oliveyoung_products, user_text, is_first_message
    출력: report (최종 응답)
    """
    t0 = time.perf_counter()

    route               = state["route"]
    report_dict         = dict(state.get("llm_output", {}))
    oliveyoung_products = state.get("oliveyoung_products", [])

    # ── 올리브영 링크 반영 ──────────────────────────────────
    # 전략: oliveyoung_products(Tavily에서 실제 확인된 제품)를 신뢰의 근거로 삼음
    # LLM products 매칭은 oliveyoung_url 보완용. 링크는 항상 oliveyoung_products 기준.
    if route.needs_product and oliveyoung_products:
        # oliveyoung_products → url이 있는 것만 유효 제품으로 간주
        valid_oy = [p for p in oliveyoung_products if p.get("oliveyoung_url") and p.get("name")]

        # LLM products에 oliveyoung_url 보완 (fuzzy 매칭)
        def _fuzzy_match(llm_name: str) -> dict | None:
            if not llm_name:
                return None
            llm_clean = llm_name.replace(" ", "").lower()
            for oy in valid_oy:
                oy_clean = oy["name"].replace(" ", "").lower()
                if llm_clean == oy_clean:
                    return oy
                if llm_clean in oy_clean or oy_clean in llm_clean:
                    return oy
            return None

        llm_products = [
            p for p in (report_dict.get("products") or [])
            if p and isinstance(p, dict) and p.get("name")
        ]
        for p in llm_products:
            matched = _fuzzy_match(p.get("name", ""))
            if matched:
                p["oliveyoung_url"] = matched["oliveyoung_url"]
                p["display_name"]   = matched.get("display_name") or matched["name"]
                print(f"[PRODUCTS] ✅ {p['name']} → {p['display_name']}", flush=True)
            else:
                print(f"[PRODUCTS] ❌ 매칭 실패: '{p.get('name')}'", flush=True)

        # report_dict products: LLM 답변 유지하되 url 보완
        report_dict["products"] = llm_products if llm_products else valid_oy

        # 링크 섹션은 항상 valid_oy 기준으로 붙임 (LLM 매칭 실패와 무관하게 링크 보장)
        report_dict["chat_answer"] = _append_oliveyoung_links(
            report_dict.get("chat_answer", ""), valid_oy
        )

    elif route.needs_product and not oliveyoung_products:
        report_dict["chat_answer"] = (
            "**현재 올리브영에서 관련 제품을 찾지 못했어요** 😥\n\n"
            f"'{state['user_text']}'에 맞는 제품을 찾기 어려웠어요. "
            "조건을 조금 더 구체적으로 말씀해 주시면 다시 찾아볼게요!\n\n"
            + (report_dict.get("chat_answer") or "")
        )

    # ── 스키마 검증 ──────────────────────────────────────────
    try:
        report = validate_report(report_dict).model_dump()
    except Exception as e:
        report = report_dict
        report.setdefault("warnings", []).append(f"validator_error: {repr(e)}")

    report["intent"] = route.intent

    # ── 비로그인 회원가입 유도 문구 추가 ────────────────────
    if state.get("guest_upsell"):
        upsell_text = (
            "\n\n---\n"
            "💡 **더 정확한 피부 분석을 원하신다면?**\n"
            "회원가입 후 얼굴 사진 한 장으로 수분, 탄력, 모공 등\n"
            "5가지 지표를 정량 분석해드려요!\n"
            "[회원가입 / 로그인하기]"
        )
        report["chat_answer"] = (report.get("chat_answer") or "") + upsell_text

    # ── 채팅방 제목 ──────────────────────────────────────────
    if state.get("is_first_message"):
        text = (state.get("user_text") or "").strip()
        report["room_title"] = text[:18] + "…" if len(text) > 20 else text
    else:
        report["room_title"] = None

    print(f"[TIMER] validate_node: {time.perf_counter()-t0:.3f}s", flush=True)

    _save_run(state, report)

    # ── DB 저장: 분석 intent이고 vision_result 있을 때만 ──────
    vision_result = state.get("vision_result")
    if vision_result and state.get("analysis_type"):
        _save_to_db(state, vision_result, state.get("llm_output", {}))

    return {"report": report}
