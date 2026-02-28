from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Citation(BaseModel):
    source_id: str
    snippet: str

class Observation(BaseModel):
    title: str
    detail: str
    confidence: float = Field(ge=0.0, le=1.0)

# ✅ Products 추가
RecCategory = Literal["AM", "PM", "Lifestyle", "Ingredients", "Products"]

class Recommendation(BaseModel):
    category: RecCategory
    items: List[str]

# ✅ (권장) 제품 추천을 구조화해서 담을 필드 추가
class ProductItem(BaseModel):
    brand: str
    name: str
    why: str
    url: Optional[str] = None          # ✅ 추가
    how_to_use: Optional[str] = None
    evidence_source_id: str  # rag_passages의 source_id와 매칭(프롬프트에서 강제)

class FinalReport(BaseModel):
    summary: str
    observations: List[Observation]
    recommendations: List[Recommendation]

    # ✅ (권장) 제품 리스트. 없으면 빈 리스트로.
    products: List[ProductItem] = []

    warnings: List[str] = []
    red_flags: List[str] = []
    citations: List[Citation] = []
    chat_answer: str = ""