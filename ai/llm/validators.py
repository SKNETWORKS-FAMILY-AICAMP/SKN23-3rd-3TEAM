# -----------------------------------------------------------------------------
# Change Log
# - 2026-02-27: (bugfix) 도메인 밖 입력/근거 부족 시 LLM 출력이 정책을 깨며
#   ValueError로 Streamlit 앱이 중단되는 문제 해결.
#   - 기존: 정책 위반(문장수, citation 형식, recommendations empty) -> raise
#   - 변경: raise 대신 보정/필터링으로 "유효한 FinalReport"를 항상 반환
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict, List

from ai.schemas.report_schema import FinalReport, Recommendation, RecCategory

ALLOWED: set[str] = {"AM", "PM", "Lifestyle", "Ingredients", "Products"}


def _as_list(x) -> list:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _s(x: Any) -> str:
    return str(x).strip() if x is not None else ""


def _clamp01(x: Any, default: float = 0.5) -> float:
    try:
        v = float(x)
    except Exception:
        v = default
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


def _normalize_observations(report_dict: Dict[str, Any]) -> None:
    obs = _as_list(report_dict.get("observations"))
    cleaned = []
    for o in obs:
        if not isinstance(o, dict):
            continue
        title = _s(o.get("title"))
        detail = _s(o.get("detail"))
        if not title or not detail:
            continue
        cleaned.append(
            {"title": title, "detail": detail, "confidence": _clamp01(o.get("confidence"), 0.5)}
        )
    report_dict["observations"] = cleaned


def _normalize_recommendations(report_dict: Dict[str, Any]) -> None:
    recs = _as_list(report_dict.get("recommendations"))
    cleaned = []
    for r in recs:
        if not isinstance(r, dict):
            continue
        cat = _s(r.get("category"))
        if cat not in ALLOWED:
            cat = "Lifestyle"
        items = _as_list(r.get("items"))
        items = [_s(it) for it in items if _s(it)]
        if not items:
            continue
        cleaned.append({"category": cat, "items": items})
    report_dict["recommendations"] = cleaned


def _normalize_products(report_dict: Dict[str, Any]) -> None:
    prods = _as_list(report_dict.get("products"))
    cleaned = []
    for p in prods:
        if not isinstance(p, dict):
            continue
        brand = _s(p.get("brand"))
        name = _s(p.get("name"))
        why = _s(p.get("why"))
        ev = _s(p.get("evidence_source_id"))
        if not (brand and name and why and ev):
            continue
        item = {
            "brand": brand,
            "name": name,
            "why": why,
            "evidence_source_id": ev,
        }
        how = _s(p.get("how_to_use"))
        if how:
            item["how_to_use"] = how
        cleaned.append(item)
    report_dict["products"] = cleaned


def _normalize_citations(report_dict: Dict[str, Any]) -> None:
    cits = _as_list(report_dict.get("citations"))
    cleaned = []
    for c in cits:
        if not isinstance(c, dict):
            continue
        sid = _s(c.get("source_id"))
        snip = _s(c.get("snippet"))
        if sid and snip:
            cleaned.append({"source_id": sid, "snippet": snip})
    report_dict["citations"] = cleaned


def _normalize_top_level(report_dict: Any) -> Dict[str, Any]:
    if not isinstance(report_dict, dict):
        report_dict = {}

    report_dict["summary"] = _s(report_dict.get("summary"))
    report_dict["chat_answer"] = _s(report_dict.get("chat_answer"))

    # 리스트형 default 필드들
    report_dict["warnings"] = [_s(x) for x in _as_list(report_dict.get("warnings")) if _s(x)]
    report_dict["red_flags"] = [_s(x) for x in _as_list(report_dict.get("red_flags")) if _s(x)]

    # 핵심 필드 정규화
    _normalize_observations(report_dict)
    _normalize_recommendations(report_dict)
    _normalize_products(report_dict)
    _normalize_citations(report_dict)

    return report_dict


def _fallback_report(reason: str) -> Dict[str, Any]:
    return {
        "summary": "출력 형식이 깨져 기본 응답으로 복구했습니다.",
        "observations": [],
        "recommendations": [
            {
                "category": "Lifestyle",
                "items": ["피부 고민(예: 홍조/여드름/건조/모공)과 현재 루틴을 알려주면 더 정확히 안내할 수 있어요."],
            }
        ],
        "products": [],
        "warnings": [f"LLM 출력 스키마 오류로 fallback 적용: {reason}"],
        "red_flags": [],
        "citations": [],
        "chat_answer": "현재 데모는 피부/스킨케어 질문에 맞춰 답변해요. 피부 고민과 루틴을 알려주면 더 정확히 안내할 수 있어요. 증상이 심하면 피부과 상담을 권장해요.",
    }


def _fix_chat_answer(chat_answer: str) -> str:
    s = (chat_answer or "").strip()
    if not s:
        s = "현재 데모는 피부/스킨케어 질문에 맞춰 답변해요. 피부 고민과 루틴을 알려주면 더 정확히 안내할 수 있어요. 증상이 심하면 피부과 상담을 권장해요."
    # 너무 짧으면 문장 보강
    if len(s) < 80:
        s += " 피부 고민(예: 홍조/여드름/건조/모공)과 현재 루틴을 알려주면 더 정확히 안내할 수 있어요."
        s += " 증상이 심하거나 통증/진물/급격한 악화가 있으면 피부과 상담을 권장해요."
    # 너무 길면 잘라냄
    if len(s) > 700:
        s = s[:700].rstrip() + "…"
    return s

def _drop_ungrounded_products(report_dict: Dict[str, Any], evidence: Dict[str, Any] | None) -> None:
    if not evidence:
        return
    passages = (evidence.get("rag_passages") or []) + (evidence.get("web_passages") or [])
    text_blob = "\n".join([(p.get("snippet") or "") for p in passages])

    prods = _as_list(report_dict.get("products"))
    kept = []
    for p in prods:
        if not isinstance(p, dict):
            continue
        name = _s(p.get("name"))
        ev = _s(p.get("evidence_source_id"))
        # 1) evidence_source_id가 실제 passage source_id 중 하나인지
        if ev and ev not in {pp.get("source_id") for pp in passages}:
            continue
        # 2) 제품명이 근거 텍스트에 실제 등장하는지(최소 포함 검사)
        if name and name in text_blob:
            kept.append(p)
    report_dict["products"] = kept
def validate_report(report_dict, evidence=None) -> FinalReport:
    normalized = _normalize_top_level(report_dict)

    # ✅ 환각 제품 제거(근거 기반) — model_validate 전에!
    _drop_ungrounded_products(normalized, evidence)

    # 필수 3종(summary/observations/recommendations) 보장
    if not normalized["summary"]:
        normalized["summary"] = "요청을 바탕으로 피부/스킨케어 관점에서 안내합니다."
    if not normalized["recommendations"]:
        normalized["recommendations"] = [
            {"category": "Lifestyle", "items": ["피부 고민을 조금 더 구체적으로 알려주세요."]}
        ]
    if "observations" not in normalized or normalized["observations"] is None:
        normalized["observations"] = []

    try:
        report = FinalReport.model_validate(normalized)
    except Exception as e:
        report = FinalReport.model_validate(_fallback_report(str(e)))

    # 추가 정책은 raise 금지: 보정만
    report.chat_answer = _fix_chat_answer(report.chat_answer)

    # recommendations가 혹시라도 비면 보정
    if not report.recommendations:
        report.recommendations = [
            Recommendation(category="Lifestyle", items=["피부 고민을 구체적으로 알려주세요."])
        ]
        report.warnings = list(report.warnings or [])
        report.warnings.append("recommendations가 비어 기본값으로 보정함")

    return report