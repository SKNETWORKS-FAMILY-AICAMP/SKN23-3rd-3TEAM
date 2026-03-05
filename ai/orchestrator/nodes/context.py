"""
nodes/context.py
유저 프로필을 로드하고 맥락 부족 여부를 확인합니다.
기존 pipeline.py의 Step 3 + Step 3-1에 해당합니다.

[비로그인 사용자 추가 처리]
1. 일반 질의에서도 피부타입 미수집 시 역질문
2. 답변 말미에 회원가입 유도 문구 삽입 (state에 플래그 저장)
"""
import time
from ai.orchestrator.state import GraphState
from ai.orchestrator.context_builder import build_context
from ai.orchestrator.router import _has_context, _CONTEXT_KW, _PRODUCT_CATEGORY_KW, _normalize_category, _has_any

# 역질문 없이 바로 답변해도 되는 intent
_NO_ASK_INTENTS = {
    "greeting", "out_of_domain", "login_required",
    "ask_for_context", "medical_advice",
    "skin_analysis_fast", "skin_analysis_deep", "ingredient_analysis",
}

# 답변 말미에 회원가입 유도 문구를 붙일 intent
_UPSELL_INTENTS = {
    "general_advice", "routine_advice", "ingredient_question",
    "product_recommend", "routine_and_product",
}


# 피부타입 없어도 답할 수 있는 일반 지식성 질문 키워드
_GENERAL_KNOWLEDGE_KW = [
    # 이유/원리 질문
    "왜", "이유", "원인", "어떻게", "무엇", "뭐야", "뭔지", "설명",
    # 음식/생활습관
    "음식", "먹으면", "먹어야", "식단", "생활", "습관",
    "운동", "수면", "스트레스", "호르몬",
    # 환경/계절
    "계절", "겨울", "여름", "환절기", "날씨", "온도", "습도",
    "실내", "자외선", "환경", "컴퓨터", "핸드폰",
    # 성분/효능 설명
    "효능", "효과", "성분이", "작용", "차이", "비교",
    # 일반 지식 요청
    "알려줘", "궁금해", "뭐가 좋아", "좋다는데",
]


def _needs_skin_type_for_answer(user_text: str, intent: str) -> bool:
    text = (user_text or "").lower()

    # 제품 추천/루틴은 항상 개인화 필요
    if intent in ("product_recommend", "routine_and_product", "routine_advice"):
        return True

    # general_advice지만 개인화가 필요한 키워드가 있는 경우
    _PERSONALIZED_ADVICE_KW = [
        "관리법", "관리", "케어", "루틴", "어떻게 해야",
        "뭐 바르", "뭐 써", "어떤 게 좋", "맞는",
    ]
    if intent == "general_advice" and any(kw in text for kw in _PERSONALIZED_ADVICE_KW):
        # 단, 일반 지식 질문("왜", "이유", "음식" 등)과 겹치면 역질문 불필요
        _PURE_KNOWLEDGE_KW = [
            "왜", "이유", "원인", "무엇", "뭐야", "뭔지", "설명",
            "음식", "먹으면", "식단", "운동", "수면", "스트레스",
            "효능", "효과", "성분이", "작용", "차이", "비교",
        ]
        if not any(kw in text for kw in _PURE_KNOWLEDGE_KW):
            return True

    # 일반 지식성 질문이면 역질문 불필요
    if _has_any(text, _GENERAL_KNOWLEDGE_KW):
        return False

    # 카테고리 키워드 있으면 개인화 필요 (세럼 등 제품 언급)
    normalized = _normalize_category(text)
    if any(kw in normalized for kw in _PRODUCT_CATEGORY_KW):
        return True

    # general_advice는 기본적으로 역질문 불필요
    return False


def _has_temp_skin_context(user_profile: dict | None, user_text: str = "") -> bool:
    """
    임시 프로필 또는 현재 입력 텍스트에 피부타입/고민 정보가 있는지 확인.

    chat_history가 비어있어도 현재 입력("지성이야", "지성 피부요" 등)에서
    피부타입을 감지하면 바로 답변으로 진행합니다.
    """
    # 임시 프로필에서 확인
    if user_profile and (
        user_profile.get("skin_type_label") or
        user_profile.get("skin_concern")
    ):
        return True

    # 현재 입력 텍스트에서도 확인 (chat_history 미전달 케이스 대응)
    if user_text and any(kw in user_text for kw in _CONTEXT_KW):
        return True

    return False


def context_node(state: GraphState) -> GraphState:
    """
    [context_node]
    입력: user_id, chat_history, route
    출력: user_profile, instant_response(맥락 부족이면), guest_upsell(비로그인 유도 플래그)
    """
    t0 = time.perf_counter()

    user_id = state.get("user_id")
    chat_history = state.get("chat_history", [])
    route = state["route"]
    is_guest = not user_id

    user_profile = build_context(
        user_id=user_id,
        chat_history=chat_history,
    )

    print(f"[TIMER] context_node: {time.perf_counter()-t0:.3f}s", flush=True)

    updates: GraphState = {
        "user_profile": user_profile,
        "guest_upsell": False,  # 기본값
    }

    # ── 1. 기존: 제품 추천 맥락 부족 역질문 ──────────────────
    if route.needs_context_check:
        if not _has_context(state["user_text"], user_profile, chat_history):
            print("[CONTEXT] 피부 맥락 부족 → 역질문 반환", flush=True)
            result = {
                "chat_answer": (
                    "어떤 피부 타입이나 고민에 맞는 제품을 찾고 계신가요? 😊\n\n"
                    "예를 들어:\n"
                    "- **건성 피부**에 맞는 수분크림 추천해줘\n"
                    "- **여드름** 고민인데 세럼 추천해줘\n"
                    "- **지성 피부**에 맞는 선크림 알려줘\n\n"
                    "피부 타입이나 고민을 알려주시면 딱 맞는 제품을 찾아드릴게요!"
                ),
                "summary": "", "observations": [], "recommendations": [],
                "products": [], "warnings": [], "citations": [],
                "intent": "ask_for_context", "room_title": None,
            }
            if state.get("is_first_message"):
                text = (state["user_text"] or "").strip()
                result["room_title"] = text[:18] + "…" if len(text) > 20 else text
            updates["instant_response"] = result
            return updates

    # ── 2. 비로그인 전용 처리 ─────────────────────────────────
    if is_guest and route.intent not in _NO_ASK_INTENTS:

        # 2-1. 피부타입 미수집 시 역질문
        # 단, 음식/원리/이유 같은 일반 지식 질문은 피부타입 없어도 바로 답변
        needs_type = _needs_skin_type_for_answer(state.get('user_text', ''), route.intent)
        if needs_type and not _has_temp_skin_context(user_profile, state.get('user_text', '')):
            print("[CONTEXT] 비로그인 피부 맥락 없음 → 피부타입 역질문", flush=True)

            # 첫 메시지면 질문 내용도 기억해서 답변에 포함
            user_text = (state["user_text"] or "").strip()
            topic_hint = f'"{user_text}"에 대해 ' if user_text else ""

            result = {
                "chat_answer": (
                    f"{topic_hint}답변드리기 전에 먼저 피부 타입을 알려주시면 "
                    f"더 정확한 정보를 드릴 수 있어요 😊\n\n"
                    "**피부 타입이 어떻게 되시나요?**\n"
                    "- 건성 (당기고 건조한 편)\n"
                    "- 지성 (번들거리고 피지가 많은 편)\n"
                    "- 복합성 (T존은 지성, 볼은 건성)\n"
                    "- 중성 (크게 건조하거나 번들거리지 않음)\n"
                    "- 민감성 (자극에 쉽게 반응하는 편)\n\n"
                    "추가로 주요 피부 고민(여드름/홍조/모공/주름 등)도 알려주시면 더욱 도움이 돼요!"
                ),
                "summary": "", "observations": [], "recommendations": [],
                "products": [], "warnings": [], "citations": [],
                "intent": "ask_for_context", "room_title": None,
            }
            if state.get("is_first_message"):
                result["room_title"] = user_text[:18] + "…" if len(user_text) > 20 else user_text
            updates["instant_response"] = result
            return updates

        # 2-2. 피부타입 수집됨 → 답변 후 회원가입 유도 플래그 설정
        if route.intent in _UPSELL_INTENTS:
            print("[CONTEXT] 비로그인 답변 → 회원가입 유도 플래그 설정", flush=True)
            updates["guest_upsell"] = True

    return updates
