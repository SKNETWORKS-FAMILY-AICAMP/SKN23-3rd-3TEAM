from dataclasses import dataclass
from typing import Optional
import re

@dataclass(frozen=True)
class RouteDecision:
    needs_vision: bool
    needs_rag: bool
    intent: str  # "general" | "routine" | "ingredient" | "product" | "reaction" | "image_analysis" | "medical"
    reason: str

# ---- helpers

def _has_any(text: str, keywords: list[str]) -> bool:
    return any(k in text for k in keywords)

def _looks_like_image_request(text: str) -> bool:
    # 사용자가 이미지 기반 해석을 원한다는 표현
    kws = ["이 사진", "사진", "이미지", "분석", "봐줘", "보여", "얼굴", "피부 상태", "점수", "측정", "결과", "qc"]
    return _has_any(text, kws)

def _is_product_or_ingredient_question(text: str) -> bool:
    kws = ["성분", "전성분", "레티놀", "나이아신", "비타민c", "bha", "aha", "판테놀", "세라마이드",
           "화장품", "제품", "추천", "올리브영", "구매", "가격", "링크", "브랜드", "선크림", "클렌저", "토너", "세럼", "크림"]
    return _has_any(text, kws)

def _is_routine_question(text: str) -> bool:
    kws = ["루틴", "아침", "저녁", "순서", "사용법", "몇 번", "빈도", "단계", "레이어링"]
    return _has_any(text, kws)

def _is_reaction_question(text: str) -> bool:
    kws = ["따가", "가렵", "붉", "홍반", "열감", "부어", "자극", "트러블", "뒤집", "알레르기", "두드러기", "물집"]
    return _has_any(text, kws)

def _is_medical_tone_request(text: str) -> bool:
    # "진단/치료/처방" 직접 요구는 medical intent로 분리(의료 조언 금지 템플릿 적용용)
    kws = ["진단", "치료", "처방", "약", "병원", "의사", "피부과", "항생제", "스테로이드"]
    return _has_any(text, kws)

# ---- main

def decide(user_text: str, has_images: bool) -> RouteDecision:
    text = (user_text or "").lower().strip()

    if not text:
        return RouteDecision(False, False, intent="general", reason="empty_input")

    medical = _is_medical_tone_request(text)
    reaction = _is_reaction_question(text)
    product_ing = _is_product_or_ingredient_question(text)
    routine = _is_routine_question(text)
    image_req = _looks_like_image_request(text)

    # intent 결정
    if has_images and image_req:
        intent = "image_analysis"
    elif product_ing:
        intent = "product"
    elif reaction:
        intent = "reaction"
    elif routine:
        intent = "routine"
    elif medical:
        intent = "medical"
    else:
        intent = "general"

    # needs_vision: 이미지 + 이미지 해석 요구일 때만
    needs_vision = bool(has_images and intent == "image_analysis")

    # needs_rag:
    # - 제품/성분/사용법/주의사항/반응(자극) 관련은 근거가 있으면 좋으니 ON
    # - general은 OFF(속도)로 두고, 필요하면 generator에서 상식 답변 + “근거 부족” 표기
    if intent in {"product", "ingredient", "routine", "reaction"}:
        needs_rag = True
    elif intent == "image_analysis":
        # 이미지 분석만 요청해도, 해석/관리팁을 근거로 보강하려면 ON
        needs_rag = True
    else:
        needs_rag = False

    # medical intent는 RAG를 켜더라도 “의료 조언 금지/상담 권장” 템플릿이 우선
    # (generator에서 안전 문구 강제)
    reason = f"intent={intent}, has_images={has_images}"
    return RouteDecision(needs_vision=needs_vision, needs_rag=needs_rag, intent=intent, reason=reason)