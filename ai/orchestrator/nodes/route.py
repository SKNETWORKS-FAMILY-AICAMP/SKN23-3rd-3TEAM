"""
nodes/route.py
사용자 입력을 분석해서 intent와 처리 플래그를 결정합니다.
기존 pipeline.py의 Step 1 + Step 2(즉시응답 준비)에 해당합니다.
"""
import time
from ai.orchestrator.state import GraphState
from ai.orchestrator.router import decide

# 즉시 반환 응답 텍스트 (pipeline.py에서 이동)
_INSTANT_RESPONSES = {
    "out_of_domain": (
        "저는 피부/스킨케어 전문 챗봇이에요 😊\n\n"
        "피부 고민, 화장품 성분, 스킨케어 루틴에 관한 질문을 해주세요!"
    ),
    "greeting": (
        "안녕하세요! 피부/스킨케어 전문 AI 챗봇이에요 😊\n\n"
        "피부 고민이나 화장품 관련 질문을 편하게 해주세요.\n"
        "- 피부 타입별 루틴 추천\n"
        "- 화장품 성분 분석\n"
        "- 피부 사진 정량 분석 (회원 전용)\n\n"
        "어떤 도움이 필요하신가요?"
    ),
    "login_required": (
        "**이 기능은 회원 전용이에요** 🔒\n\n"
        "피부 사진 분석 및 전성분 분석 기능은 로그인 후 이용할 수 있어요.\n\n"
        "로그인하시면:\n"
        "- 📸 **빠른 분석**: 얼굴 사진 1장으로 피부 상태 정량 분석\n"
        "- 🔬 **정밀 분석**: 좌·정면·우측 3장으로 정밀 분석\n"
        "- 🧪 **성분 분석**: 화장품 전성분 이미지로 피부 적합성 분석\n\n"
        "로그인 후 다시 시도해주세요!"
    ),
    "ask_for_context": (
        "어떤 피부 타입이나 고민에 맞는 제품을 찾고 계신가요? 😊\n\n"
        "예를 들어:\n"
        "- **건성 피부**에 맞는 수분크림 추천해줘\n"
        "- **여드름** 고민인데 세럼 추천해줘\n"
        "- **지성 피부**에 맞는 선크림 알려줘\n\n"
        "피부 타입이나 고민을 알려주시면 딱 맞는 제품을 찾아드릴게요!"
    ),
    "ask_for_category": (
        "어떤 종류의 제품을 찾고 계신가요? 😊\n\n"
        "예를 들어:\n"
        "- 수분크림\n"
        "- 세럼\n"
        "- 폼클렌징\n"
        "- 토너/스킨\n"
        "- 선크림\n"
        "- 로션\n\n"
        "원하시는 제품 종류를 알려주시면 올리브영에서 딱 맞는 제품을 찾아드릴게요!"
    ),
}

# 즉시 응답 intent 목록
_INSTANT_INTENTS = {"out_of_domain", "greeting", "login_required", "ask_for_context", "ask_for_category"}


def _make_instant_response(intent: str, user_text: str, is_first_message: bool) -> dict:
    """즉시 반환용 응답 dict 생성"""
    result = {
        "chat_answer": _INSTANT_RESPONSES.get(intent, "잠시 후 다시 시도해주세요."),
        "summary": "", "observations": [], "recommendations": [],
        "products": [], "warnings": [], "citations": [],
        "intent": intent, "room_title": None,
    }
    if is_first_message:
        text = (user_text or "").strip()
        result["room_title"] = text[:18] + "…" if len(text) > 20 else text
    return result


def route_node(state: GraphState) -> GraphState:
    """
    [route_node]
    입력: user_text, analysis_type, images, user_id, chat_history
    출력: route, instant_response(즉시 응답이면)
    """
    t0 = time.perf_counter()

    route = decide(
        user_text=state["user_text"],
        analysis_type=state.get("analysis_type"),
        has_images=len(state.get("images", [])) > 0,
        user_id=state.get("user_id"),
        user_profile=None,          # context_node 전이라 None
        chat_history=state.get("chat_history", []),
    )

    print(
        f"[ROUTE] intent={route.intent} | needs_rag={route.needs_rag} "
        f"| needs_product={route.needs_product} "
        f"| needs_context_check={route.needs_context_check}",
        flush=True
    )
    print(f"[TIMER] route_node: {time.perf_counter()-t0:.3f}s", flush=True)

    updates: GraphState = {"route": route}

    # 즉시 응답이면 미리 준비 (context_node 스킵됨)
    if route.intent in _INSTANT_INTENTS:
        updates["instant_response"] = _make_instant_response(
            intent=route.intent,
            user_text=state["user_text"],
            is_first_message=state.get("is_first_message", False),
        )

    return updates
