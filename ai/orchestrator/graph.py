"""
graph.py
LangGraph 그래프를 정의하고 컴파일합니다.
기존 pipeline.py의 run() 함수를 완전히 대체합니다.

그래프 흐름:
  START
    │
  [route_node]
    │
  조건 분기 (route_condition)
    ├─ "instant" → END              (greeting, out_of_domain 등 즉시 반환)
    └─ "continue" → [context_node]
                        │
                    조건 분기 (context_condition)
                        ├─ "instant" → END          (맥락 부족 → 역질문)
                        └─ "continue" → [vision_node]
                                            │
                                        [search_node]    ← RAG + Tavily 병렬
                                            │
                                        [llm_node]
                                            │
                                        [validate_node]
                                            │
                                           END
"""
from langgraph.graph import StateGraph, END

from ai.orchestrator.state import GraphState
from ai.orchestrator.nodes import (
    route_node,
    context_node,
    vision_node,
    search_node,
    llm_node,
    validate_node,
)

# 즉시 반환 intent 목록 (context_node 이전에 종료)
_INSTANT_INTENTS = {"out_of_domain", "greeting", "login_required", "ask_for_context"}


# ── 조건부 엣지 함수 ──────────────────────────────────────────

def route_condition(state: GraphState) -> str:
    """
    route_node 다음 분기:
    - 즉시 응답 intent → "instant" (END로)
    - 나머지 → "continue" (context_node로)
    """
    intent = state["route"].intent
    if intent in _INSTANT_INTENTS:
        return "instant"
    return "continue"


def context_condition(state: GraphState) -> str:
    """
    context_node 다음 분기:
    - 맥락 부족 역질문 → "instant" (END로)
    - 나머지 → "continue" (vision_node로)
    """
    if state.get("instant_response") is not None:
        return "instant"
    return "continue"


# ── 그래프 빌드 ───────────────────────────────────────────────

def _build_graph() -> StateGraph:
    graph = StateGraph(GraphState)

    # 노드 등록
    graph.add_node("route_node",    route_node)
    graph.add_node("context_node",  context_node)
    graph.add_node("vision_node",   vision_node)
    graph.add_node("search_node",   search_node)
    graph.add_node("llm_node",      llm_node)
    graph.add_node("validate_node", validate_node)

    # 시작점
    graph.set_entry_point("route_node")

    # route_node 다음 분기
    graph.add_conditional_edges(
        "route_node",
        route_condition,
        {
            "instant":  END,            # greeting/out_of_domain → 즉시 종료
            "continue": "context_node", # 일반 처리 → context로
        }
    )

    # context_node 다음 분기
    graph.add_conditional_edges(
        "context_node",
        context_condition,
        {
            "instant":  END,            # 맥락 부족 역질문 → 즉시 종료
            "continue": "vision_node",  # 일반 처리 → vision으로
        }
    )

    # 이후 선형 실행
    graph.add_edge("vision_node",   "search_node")
    graph.add_edge("search_node",   "llm_node")
    graph.add_edge("llm_node",      "validate_node")
    graph.add_edge("validate_node", END)

    return graph


# ── 컴파일 (모듈 import 시 1회만 실행) ───────────────────────
_graph = _build_graph()
app = _graph.compile()


# ── 외부에서 호출하는 메인 함수 ──────────────────────────────

def run(
    user_text: str,
    images: list,
    analysis_type: str | None = None,
    user_id: int | None = None,
    chat_history: list | None = None,
    is_first_message: bool = False,
    image_urls: list[str] | None = None,
) -> dict:
    """
    LangGraph 기반 챗봇 파이프라인 실행.
    기존 pipeline.py의 run()과 동일한 인터페이스를 유지합니다.
    → app.py의 import 경로만 변경하면 됩니다.

    Args:
        image_urls: S3에 업로드된 이미지 URL 리스트.
                    validate_node에서 DB 저장 시 사용합니다.

    Returns:
        dict: chat_answer, products, intent 등을 포함한 최종 응답
    """
    initial_state: GraphState = {
        "user_text":        user_text,
        "images":           images or [],
        "analysis_type":    analysis_type,
        "user_id":          user_id,
        "chat_history":     chat_history or [],
        "is_first_message": is_first_message,
        "image_urls":       image_urls or [],   # S3 URL → DB 저장용
        # 중간 상태 초기값
        "route":            None,
        "instant_response": None,
        "user_profile":     None,
        "vision_result":    None,
        "rag_passages":     [],
        "oliveyoung_products": [],
        "llm_output":       {},
        "report":           {},
    }

    final_state = app.invoke(initial_state)

    # 즉시 응답(greeting 등)은 instant_response에 있음
    if final_state.get("instant_response"):
        return final_state["instant_response"]

    # 일반 응답은 report에 있음
    return final_state.get("report", {
        "chat_answer": "응답 생성에 실패했어요. 다시 시도해주세요.",
        "intent": "error",
    })
