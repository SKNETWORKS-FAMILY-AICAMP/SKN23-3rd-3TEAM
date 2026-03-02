"""
validators.py
LLM 응답을 FinalReport 스키마에 맞게 검증/보정합니다.
raise 없이 항상 유효한 FinalReport를 반환합니다.
"""
from typing import Any, Dict

from ai.schemas.report_schema import FinalReport, Recommendation


def _s(x: Any) -> str:
    return str(x).strip() if x is not None else ""


def _as_list(x: Any) -> list:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _clamp01(x: Any) -> float:
    try:
        v = float(x)
        return max(0.0, min(1.0, v))
    except Exception:
        return 0.5


_ALLOWED_CATEGORIES = {"AM", "PM", "Lifestyle", "Ingredients", "Products"}

_FALLBACK_ANSWER = (
    "현재 피부/스킨케어 관련 질문에 답변드릴 수 있어요. "
    "피부 고민(예: 홍조, 여드름, 건조, 루틴 추천)을 알려주세요. "
    "증상이 심하다면 피부과 상담을 권장해요."
)


def _normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}

    # 상위 필드 기본값
    raw["chat_answer"] = _s(raw.get("chat_answer")) or _FALLBACK_ANSWER
    raw["summary"] = _s(raw.get("summary")) or "요청을 바탕으로 안내드립니다."
    raw["intent"] = _s(raw.get("intent"))
    raw["room_title"] = raw.get("room_title")

    # warnings / citations
    raw["warnings"] = [_s(x) for x in _as_list(raw.get("warnings")) if _s(x)]
    raw["citations"] = [
        c for c in _as_list(raw.get("citations"))
        if isinstance(c, dict) and c.get("source_id") and c.get("snippet")
    ]

    # observations
    obs = []
    for o in _as_list(raw.get("observations")):
        if not isinstance(o, dict):
            continue
        t, d = _s(o.get("title")), _s(o.get("detail"))
        if t and d:
            obs.append({"title": t, "detail": d, "confidence": _clamp01(o.get("confidence"))})
    raw["observations"] = obs

    # recommendations
    recs = []
    for r in _as_list(raw.get("recommendations")):
        if not isinstance(r, dict):
            continue
        cat = _s(r.get("category"))
        if cat not in _ALLOWED_CATEGORIES:
            cat = "Lifestyle"
        items = [_s(i) for i in _as_list(r.get("items")) if _s(i)]
        if items:
            recs.append({"category": cat, "items": items})
    raw["recommendations"] = recs

    # products: name만 있으면 유효 (brand, why는 선택값)
    prods = []
    for p in _as_list(raw.get("products")):
        if not isinstance(p, dict):
            continue
        if p.get("name"):  # name만 필수
            prods.append(p)
    raw["products"] = prods

    return raw


def validate_report(report_dict: Dict[str, Any]) -> FinalReport:
    """
    LLM 응답을 FinalReport로 변환합니다.
    항상 유효한 FinalReport를 반환합니다 (raise 없음).
    """
    normalized = _normalize(report_dict)

    # recommendations가 비면 기본값
    if not normalized["recommendations"]:
        normalized["recommendations"] = [
            {"category": "Lifestyle", "items": ["피부 고민을 구체적으로 알려주세요."]}
        ]

    try:
        return FinalReport.model_validate(normalized)
    except Exception as e:
        # 최후 fallback
        return FinalReport(
            chat_answer=_FALLBACK_ANSWER,
            summary="응답 생성 중 오류가 발생했습니다.",
            recommendations=[
                Recommendation(category="Lifestyle", items=["피부 고민을 알려주세요."])
            ],
            warnings=[f"schema_error: {repr(e)}"],
        )
