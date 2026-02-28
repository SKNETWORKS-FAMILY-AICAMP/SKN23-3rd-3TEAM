import json
from typing import Dict, Any, List
from pydantic import ValidationError

from ai.schemas.report_schema import FinalReport


# -------------------------
# 1️⃣ 최소 유효 리포트 (Fallback)
# -------------------------
def minimal_valid_report() -> Dict[str, Any]:
    return FinalReport(
        summary="현재 제공된 정보로는 구체적인 분석이 어렵습니다.",
        chat_answer="현재 제공된 정보가 제한적이라 정확한 판단은 어렵습니다. 추가 이미지나 상세 설명이 있다면 더 구체적인 안내가 가능합니다. 일반적인 피부 관리 원칙을 우선 참고해 주세요.",
        observations=[],
        recommendations=[
            {
                "category": "Lifestyle",
                "items": ["충분한 수분 섭취", "자극적인 제품 사용 최소화"]
            }
        ],
        warnings=["근거 부족"],
        red_flags=[],
        citations=[]
    ).model_dump()


# -------------------------
# 2️⃣ 1회 자동 수정 로직
# -------------------------
def _auto_fix(report_dict: Dict[str, Any]) -> Dict[str, Any]:
    fixed = dict(report_dict)

    # 1️⃣ 누락 필드 기본값 보정
    fixed.setdefault("summary", "")
    fixed.setdefault("chat_answer", "")
    fixed.setdefault("observations", [])
    fixed.setdefault("recommendations", [])
    fixed.setdefault("warnings", [])
    fixed.setdefault("red_flags", [])
    fixed.setdefault("citations", [])

    # 2️⃣ confidence 0~1 클램핑
    for obs in fixed.get("observations", []):
        if "confidence" in obs:
            try:
                val = float(obs["confidence"])
                obs["confidence"] = max(0.0, min(1.0, val))
            except Exception:
                obs["confidence"] = 0.5

    # 3️⃣ 타입 교정 (recommendations.items가 문자열이면 리스트로)
    for rec in fixed.get("recommendations", []):
        if isinstance(rec.get("items"), str):
            rec["items"] = [rec["items"]]

    # 4️⃣ 근거 없는 citation 제거 (형식 불량 제거)
    cleaned_citations = []
    for c in fixed.get("citations", []):
        if isinstance(c, dict) and c.get("source_id") and c.get("snippet"):
            cleaned_citations.append(c)
    fixed["citations"] = cleaned_citations

    return fixed


# -------------------------
# 3️⃣ Repair 메인 함수
# -------------------------
def repair_report(original_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validator 실패 시 1회 자동 수정.
    그래도 실패하면 minimal fallback 반환.
    """

    # 1️⃣ 1회 자동 수정 시도
    try:
        fixed = _auto_fix(original_report)
        validated = FinalReport.model_validate(fixed)
        return validated.model_dump()

    except ValidationError:
        # 2️⃣ 그래도 실패 → fallback
        return minimal_valid_report()