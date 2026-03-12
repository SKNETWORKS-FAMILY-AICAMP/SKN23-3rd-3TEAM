from db import db_manager
from typing import Optional
from fastapi import APIRouter
from services import keyword_service
from db.schemas import KeywordResponse

"""
keyword_router.py
─────────────────────────────────────────────────────────────
엔드포인트 목록:
    GET /keywords              키워드 목록 조회 (type 파라미터로 필터링)
    GET /keywords/factorials   피부 케어 루틴 키워드 목록 조회
─────────────────────────────────────────────────────────────
"""

router = APIRouter(prefix="/keywords", tags=["Keywords"])

# ─────────────────────────────────────────────
# 키워드 목록 조회
# ─────────────────────────────────────────────

@router.get("", response_model=list[KeywordResponse])
def get_keywords(type: Optional[str] = None):
    """
    키워드 목록 조회 (인증 불필요).
    - type 파라미터로 필터링 (예: skin_type, gender)
    - type 생략 시 전체 반환

    프론트 요청 예시:
        GET /keywords?type=skin_type
    응답:
        [
            { "keyword_id": 1, "type": "skin_type", "keyword": "dry",   "label": "건성",  "description": null },
            { "keyword_id": 2, "type": "skin_type", "keyword": "oily",  "label": "지성",  "description": null },
            ...
        ]
    """
    if type:
        rows = db_manager.execute_query("SELECT * FROM keywords WHERE type = %s ORDER BY keyword_id", (type))
    else:
        rows = db_manager.execute_query("SELECT * FROM keywords ORDER BY keyword_id")

    return rows

# ─────────────────────────────────────────────
# 피부 케어 루틴 키워드 (Factorial) 목록 조회
# ─────────────────────────────────────────────

@router.get("/factorials", response_model=list[KeywordResponse])
def get_factorials():
    """
    skin_care_routine 타입 키워드 전체 조회.
    - 프론트 분석 페이지의 factorial 선택지 표시용
    - AI 파이프라인 select_factorial() 내부 호출용

    인증 불필요 (공개 엔드포인트).

    프론트 요청 예시:
        GET /keywords/factorials
    응답:
        [
            {"keyword_id": 1, "type": "skin_care_routine", "keyword": "moisturizing_boost", "label": "보습 강화", ...},
            {"keyword_id": 2, "type": "skin_care_routine", "keyword": "oil_cleansing",      "label": "오일 클렌징", ...},
            ...
        ]
    """

    return keyword_service.get_skin_care_routines()
