from dataclasses import dataclass

@dataclass(frozen=True)
class RouteDecision:
    needs_vision: bool
    needs_rag: bool

def decide(user_text: str, has_images: bool) -> RouteDecision:
    text = (user_text or "").lower()

    # 아주 단순한 룰 기반 라우팅(데모용)
    wants_diagnosis = any(k in text for k in ["진단", "피부", "트러블", "홍조", "여드름", "건조"])
    wants_reco = any(k in text for k in ["추천", "루틴", "화장품", "성분"])

    needs_vision = has_images and wants_diagnosis
    needs_rag = wants_reco or wants_diagnosis  # 진단/추천이면 근거가 있으면 좋음

    return RouteDecision(needs_vision=needs_vision, needs_rag=needs_rag)