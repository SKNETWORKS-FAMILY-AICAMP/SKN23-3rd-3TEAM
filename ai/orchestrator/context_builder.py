"""
context_builder.py
user_id가 있으면 DB에서 프로필과 최근 분석 이력을 로드합니다.
없으면 chat_history에서 임시 프로필을 추출합니다.
"""
import re
from typing import Optional


# ── DB 연동 (back/services 활용) ─────────────────────────────
def _load_from_db(user_id: int) -> dict | None:
    """
    DB에서 사용자 프로필과 최근 분석 이력을 로드합니다.
    back/services의 함수를 활용합니다.
    """
    try:
        import sys, os
        # 프로젝트 루트에서 실행 시 back 패키지 접근
        from back.services.user_service import get_user_by_id
        from back.services.analysis_service import get_latest_analysis
        from back.db.db_manager import execute_one

        user = get_user_by_id(user_id)
        if not user:
            return None

        # keywords 테이블에서 skin_type label 조회
        skin_type_label = None
        if user.skin_type:
            row = execute_one(
                "SELECT label, keyword FROM keywords WHERE keyword_id = %s",
                (user.skin_type,)
            )
            if row:
                skin_type_label = row.get("label") or row.get("keyword")

        # 최근 분석 이력
        recent = get_latest_analysis(user_id)
        recent_summary = None
        if recent and recent.analysis_data:
            data = recent.analysis_data
            if isinstance(data, str):
                import json
                data = json.loads(data)
            # 분석 데이터에서 주요 지표 요약 (vision 모델 결과 구조에 맞게)
            findings = data.get("findings", [])
            if findings:
                top = sorted(findings, key=lambda x: x.get("score", 0), reverse=True)[:2]
                tags = [f"{f.get('region','')}-{f.get('name','')}" for f in top if f.get("name")]
                recent_summary = f"최근 분석: {', '.join(tags)}" if tags else None

        return {
            "user_id": user_id,
            "skin_type_label": skin_type_label,
            "skin_concern": user.skin_concern,
            "age": user.age,
            "gender": user.gender,
            "recent_analysis_summary": recent_summary,
        }

    except Exception as e:
        print(f"[context_builder] DB 로드 실패: {e}", flush=True)
        return None


# ── 비회원: chat_history에서 임시 프로필 추출 ─────────────────
_SKIN_TYPE_PATTERNS = {
    "건성": ["건성", "건조"],
    "지성": ["지성", "피지"],
    "복합성": ["복합성", "복합"],
    "민감성": ["민감성", "민감"],
    "중성": ["중성"],
}

_CONCERN_PATTERNS = {
    "여드름": ["여드름", "뾰루지", "트러블"],
    "홍조": ["홍조", "붉"],
    "모공": ["모공"],
    "각질": ["각질"],
    "주름": ["주름", "탄력"],
    "색소침착": ["색소", "기미", "잡티"],
    "수분부족": ["건조", "수분", "촉촉"],
}


def _extract_temp_profile(chat_history: list) -> dict:
    """
    chat_history에서 피부타입/고민 키워드를 추출하여 임시 프로필을 만듭니다.
    """
    full_text = " ".join([
        m.get("content", "") for m in chat_history
        if m.get("role") == "user"
    ])

    skin_type_label = None
    for label, keywords in _SKIN_TYPE_PATTERNS.items():
        if any(kw in full_text for kw in keywords):
            skin_type_label = label
            break

    concerns = []
    for concern, keywords in _CONCERN_PATTERNS.items():
        if any(kw in full_text for kw in keywords):
            concerns.append(concern)

    return {
        "user_id": None,
        "skin_type_label": skin_type_label,
        "skin_concern": ", ".join(concerns) if concerns else None,
        "age": None,
        "gender": None,
        "recent_analysis_summary": None,
        "is_temp": True,  # 임시 프로필 표시
    }


# ── 메인 함수 ─────────────────────────────────────────────────
def build_context(
    user_id: int | None,
    chat_history: list,
) -> dict | None:
    """
    user_id가 있으면 DB에서, 없으면 chat_history에서 프로필을 빌드합니다.

    Returns:
        dict: user_profile (없으면 None 대신 빈 임시 프로필 반환)
    """
    if user_id:
        profile = _load_from_db(user_id)
        if profile:
            return profile

    # 비회원이거나 DB 로드 실패 → chat_history 기반 임시 프로필
    return _extract_temp_profile(chat_history)
