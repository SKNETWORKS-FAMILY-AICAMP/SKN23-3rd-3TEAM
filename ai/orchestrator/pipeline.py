import json, os, time
from typing import List, Optional, Dict, Any

from ai.config.settings import settings
from ai.orchestrator.router import decide
from ai.orchestrator.evidence import build

from ai.tools import rag_retriever_local
import ai.tools.vision_client as vision_client
from ai.llm.generator import generate_report
from ai.llm.validators import validate_report

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

"""
[수정 이력]
2026-02-27 | 정석원 | 예외 처리 로직 추가(스킨관련 질문 아닐경우)
"""
def is_skin_domain(text: str) -> bool:
    t = (text or "").lower()
    keywords = [
        "피부","여드름","홍조","모공","각질","트러블","색소","잡티","주름","건조","지성","민감",
        "루틴","스킨케어","세안","클렌징","토너","에센스","세럼","크림","선크림","자외선",
        "화장품","성분","레티놀","나이아신아마이드","비타민c","bha","aha","판테놀","세라마이드",
    ]
    return any(k in t for k in keywords)

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
            "warnings": ["도메인 밖 요청(예: 노래 추천)에는 응답하지 않음"],
            "red_flags": [],
            "citations": [],
        }
    """ ----------------------------------"""

    route = decide(user_text=user_text, has_images=len(images) > 0)

    vision_result = None
    rag_passages = None
    query = None

    if route.needs_vision:
        vision_result = vision_client.infer(images)

        # # ✅ 얼굴 아니거나 QC fail이면 vision_result를 evidence에 반영하지 않게
        # if vision_result and vision_result.get("qc", {}).get("status") == "fail":
        #     vision_result = None

    if route.needs_rag:
        # 실제로는 user_text + vision 요약으로 query를 만들지만 데모는 간단히
        query = build_rag_query(user_text, vision_result)
        rag_passages = rag_retriever_local.search(query=query, top_k=10)

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