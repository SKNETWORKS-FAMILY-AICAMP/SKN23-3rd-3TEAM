from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Citation(BaseModel):
    source_id: str
    snippet: str

class Observation(BaseModel):
    title: str
    detail: str
    confidence: float = Field(ge=0.0, le=1.0)

class Recommendation(BaseModel):
    category: Literal["AM", "PM", "Lifestyle", "Ingredients"]
    items: List[str]

class FinalReport(BaseModel):
    summary: str
    observations: List[Observation]
    recommendations: List[Recommendation]
    warnings: List[str] = []
    red_flags: List[str] = []
    citations: List[Citation] = []
    chat_answer: str = ""