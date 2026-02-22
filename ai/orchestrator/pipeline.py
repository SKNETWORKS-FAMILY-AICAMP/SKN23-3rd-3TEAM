import json, os, time
from typing import List, Optional, Dict, Any

from ai.config.settings import settings
from ai.orchestrator.router import decide
from ai.orchestrator.evidence import build

from ai.tools import rag_retriever_local, vision_client_mock
from ai.llm.generator import generate_report
from ai.llm.validators import validate_report

def build_rag_query(user_text: str, vision_result: dict | None) -> str:
    if not vision_result:
        return user_text

    findings = vision_result.get("findings", [])
    # 점수 상위 2개만 섞기(데모용)
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

def run(user_text: str, images: List[bytes], chat_history: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    if chat_history is None:
        chat_history = []
    route = decide(user_text=user_text, has_images=len(images) > 0)

    vision_result = None
    rag_passages = None
    query = None

    if route.needs_vision:
        vision_result = vision_client_mock.infer(images)

    if route.needs_rag:
        # 실제로는 user_text + vision 요약으로 query를 만들지만 데모는 간단히
        query = build_rag_query(user_text, vision_result)
        rag_passages = rag_retriever_local.search(query=query, top_k=3)

    evidence = build(user_text=user_text,
                    vision_result=vision_result, 
                    rag_passages=rag_passages, 
                    chat_history=chat_history)
    
    report_dict = generate_report(evidence)

    # Validator (스키마 강제)
    report = validate_report(report_dict).model_dump()

    run_dir = _save_run({
        "request": {"user_text": user_text, "n_images": len(images)},
        "route": {"needs_vision": route.needs_vision, "needs_rag": route.needs_rag},
        "tool_outputs": {"vision_result": vision_result, "rag_passages": rag_passages},
        "report": report,
    })

    report["_meta"] = {"run_dir": run_dir}
   
    return report