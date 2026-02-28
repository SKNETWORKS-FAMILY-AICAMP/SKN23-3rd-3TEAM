import json, os, time
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from ai.config.settings import settings
from ai.orchestrator.router import decide
from ai.orchestrator.evidence import build

from ai.tools.web.web_retriever import search_web
from ai.tools import rag_retriever_local
import ai.tools.vision_client as vision_client
from ai.llm.generator import generate_report
from ai.llm.validators import validate_report


def need_external(user_text: str, rag_passages: list, min_score: float = 0.6) -> bool:
    t = (user_text or "").lower()

    # ✅ web은 "명시적" 요청이 있을 때만
    web_triggers = ["올리브영", "구매", "가격", "링크", "url", "검색", "최저가", "공식", "사이트"]
    if not any(k in t for k in web_triggers):
        return False

    if not rag_passages:
        return True

    best = max((p.get("score", 0.0) for p in rag_passages), default=0.0)
    # ✅ 문턱을 올려서 웬만하면 로컬 RAG로 끝내기
    return best < 0.85


def build_rag_query(user_text: str, vision_result: Optional[dict]) -> str:
    if not vision_result:
        return user_text
    if vision_result.get("qc", {}).get("status") == "fail":
        return user_text

    findings = vision_result.get("findings", [])
    top = sorted(findings, key=lambda x: x.get("score", 0), reverse=True)[:2]
    tags = [f"{x.get('region','')}-{x.get('name','')}" for x in top]
    tags = " ".join([t for t in tags if t])
    return f"{user_text}\n[vision_tags] {tags}"


def _save_run(payloads: Dict[str, Any]) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join(settings.RUNS_DIR, ts)
    os.makedirs(run_dir, exist_ok=True)
    for name, obj in payloads.items():
        with open(os.path.join(run_dir, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    return run_dir


def is_skin_domain(text: str) -> bool:
    t = (text or "").lower()
    keywords = [
        "피부","여드름","홍조","모공","각질","트러블","색소","잡티","주름","건조","지성","민감",
        "루틴","스킨케어","세안","클렌징","토너","에센스","세럼","크림","선크림","자외선",
        "화장품","성분","레티놀","나이아신아마이드","비타민c","bha","aha","판테놀","세라마이드",
    ]
    return any(k in t for k in keywords)


@contextmanager
def timer(name: str):
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt = time.perf_counter() - t0
        # ✅ streamlit 콘솔에서 바로 보이게 flush
        print(f"[TIMER] {name}: {dt:.3f}s", flush=True)


def run(user_text: str, images: List[bytes], chat_history: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    if chat_history is None:
        chat_history = []

    if not is_skin_domain(user_text):
        return {
            "chat_answer": "현재 피부/스킨케어 질문에만 답할 수 있어요. 피부 고민(예: 홍조, 여드름, 건조, 루틴 추천)으로 질문해 주세요.",
            "summary": "도메인 밖 질문으로 판단되어 스킨케어 안내만 제공했습니다.",
            "observations": [],
            "recommendations": [
                {"category": "Lifestyle", "items": ["피부 고민/증상/루틴/제품 성분 관련 질문으로 다시 입력해 주세요."]}
            ],
            "products": [],
            "warnings": ["도메인 밖 요청에는 응답하지 않음"],
            "red_flags": [],
            "citations": [],
        }

    with timer("decide"):
        route = decide(user_text=user_text, has_images=len(images) > 0)

    vision_result: Optional[dict] = None
    rag_passages: list = []
    query: Optional[str] = None
    web_passages: list = []
    web_error: Optional[str] = None
    rag_error: Optional[str] = None
    vision_error: Optional[str] = None
    llm_error: Optional[str] = None

    # ✅ Vision
    if route.needs_vision:
        try:
            with timer("vision_infer"):
                vision_result = vision_client.infer(images)
        except Exception as e:
            vision_error = repr(e)
            vision_result = None

    # ✅ RAG
    if route.needs_rag:
        with timer("build_rag_query"):
            query = build_rag_query(user_text, vision_result)

        try:
            # ✅ top_k 줄여서 LLM 컨텍스트 폭발 방지
            with timer("rag_search"):
                rag_passages = rag_retriever_local.search(query=query, top_k=5)
        except Exception as e:
            rag_error = repr(e)
            rag_passages = []

        # ✅ Web (명시 요청 + rag 부족일 때만)
        if need_external(user_text, rag_passages, min_score=0.6):
            web_query = query or user_text
            if "올리브영" in (user_text or ""):
                web_query = f"{web_query} site:oliveyoung.co.kr"

            try:
                with timer("web_search"):
                    web_passages = search_web(web_query, top_k=3)
            except Exception as e:
                web_error = repr(e)
                web_passages = []

    with timer("evidence_build"):
        evidence = build(
            user_text=user_text,
            vision_result=vision_result,
            rag_passages=rag_passages,
            web_passages=web_passages,
            chat_history=chat_history,
        )

    # ✅ LLM
    report_dict: Dict[str, Any]
    try:
        with timer("llm_generate"):
            report_dict = generate_report(evidence)
    except Exception as e:
        llm_error = repr(e)
        report_dict = {
            "chat_answer": "LLM 호출 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            "summary": "LLM error",
            "observations": [],
            "recommendations": [],
            "products": [],
            "warnings": [llm_error],
            "red_flags": [],
            "citations": [],
        }

    # ✅ Validate
    try:
        with timer("validate"):
            report = validate_report(report_dict, evidence).model_dump()
    except Exception as e:
        # validator가 실패해도 최소 응답은 보장
        report = report_dict
        report.setdefault("warnings", [])
        report["warnings"].append(f"validator_error: {repr(e)}")

    with timer("save_run"):
        run_dir = _save_run({
            "request": {"user_text": user_text, "n_images": len(images)},
            "route": {"needs_vision": route.needs_vision, "needs_rag": route.needs_rag},
            "tool_outputs": {
                "route": {"needs_vision": route.needs_vision, "needs_rag": route.needs_rag},
                "vision_result": vision_result,
                "vision_error": vision_error,
                "rag_passages": rag_passages,
                "rag_error": rag_error,
                "web_passages": web_passages,
                "web_error": web_error,
                "query": query,
                },
            "report": report,
        })

    report["_meta"] = {"run_dir": run_dir}
    return report