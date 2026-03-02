"""
nodes/llm.py
RAG/Tavily 결과를 바탕으로 LLM 답변을 생성합니다.
기존 pipeline.py의 Step 6에 해당합니다.
"""
import time
from ai.orchestrator.state import GraphState
from ai.llm.generator import generate_report


def llm_node(state: GraphState) -> GraphState:
    """
    [llm_node]
    입력: route, user_text, user_profile, vision_result,
          rag_passages, oliveyoung_products, chat_history, analysis_type
    출력: llm_output
    """
    route = state["route"]
    analysis_type = state.get("analysis_type")

    analysis_mode = (
        "fast" if analysis_type == "quick"
        else "deep" if analysis_type == "detailed"
        else ""
    )

    t0 = time.perf_counter()
    llm_output: dict

    try:
        llm_output = generate_report(
            intent=route.intent,
            user_text=state["user_text"],
            user_profile=state.get("user_profile"),
            vision_result=state.get("vision_result"),
            rag_passages=state.get("rag_passages", []),
            web_passages=[],
            chat_history=state.get("chat_history", []),
            ingredients=None,
            analysis_mode=analysis_mode,
            verified_products=(
                state.get("oliveyoung_products")
                if route.needs_product else None
            ),
        )
    except Exception as e:
        error_msg = repr(e)
        print(f"[LLM ERROR] {error_msg}", flush=True)
        llm_output = {
            "chat_answer": "잠시 오류가 발생했어요. 다시 시도해주세요.",
            "summary": "LLM 오류", "observations": [], "recommendations": [],
            "products": [], "warnings": [error_msg], "citations": [],
        }

    print(f"[TIMER] llm_node: {time.perf_counter()-t0:.3f}s", flush=True)
    return {"llm_output": llm_output}
