"""
report_schema.py
LLM 응답 구조를 정의합니다.
프론트에는 chat_answer 필드가 주로 사용됩니다.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Citation(BaseModel):
    source_id: str
    snippet: str


class Observation(BaseModel):
    title: str
    detail: str
    confidence: float = Field(ge=0.0, le=1.0)


RecCategory = Literal["AM", "PM", "Lifestyle", "Ingredients", "Products"]


class Recommendation(BaseModel):
    category: RecCategory
    items: List[str]


class ProductItem(BaseModel):
    brand: str = ""                         # 선택값 (Tavily에서 추출 어려움)
    name: str
    why: str = ""
    oliveyoung_url: Optional[str] = None   # 올리브영 상세 링크
    evidence_source_id: str = ""            # 선택값


class FinalReport(BaseModel):
    # ── 프론트 메인 표시 ──────────────────────────
    chat_answer: str = ""               # 사용자에게 보여주는 최종 답변 (Markdown)

    # ── 구조화 데이터 (추후 프론트 활용 가능) ─────
    summary: str = ""
    observations: List[Observation] = []
    recommendations: List[Recommendation] = []
    products: List[ProductItem] = []

    # ── 메타 ──────────────────────────────────────
    intent: str = ""                    # 분류된 intent
    warnings: List[str] = []
    citations: List[Citation] = []

    # ── 채팅방 제목 (첫 메시지일 때만 채워짐) ────
    room_title: Optional[str] = None
