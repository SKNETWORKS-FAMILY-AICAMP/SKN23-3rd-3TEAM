"""
keyword_router.py
─────────────────────────────────────────────────────────────
엔드포인트 목록:
    GET /keywords     키워드 목록 조회 (type 파라미터로 필터링)
─────────────────────────────────────────────────────────────
"""

from db import db_manager
from typing import Optional
from fastapi import APIRouter
from db.schemas import KeywordResponse

router = APIRouter(prefix="/keywords", tags=["Keywords"])


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
        rows = db_manager.execute_query(
            "SELECT * FROM keywords WHERE type = %s ORDER BY keyword_id",
            (type,),
        )
    else:
        rows = db_manager.execute_query(
            "SELECT * FROM keywords ORDER BY keyword_id",
        )
    return rows
