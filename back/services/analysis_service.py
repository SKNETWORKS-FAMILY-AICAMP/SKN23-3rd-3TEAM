"""
analysis_service.py
─────────────────────────────────────────────────────────────
목적  : 피부 분석 결과 관련 비즈니스 로직 담당
역할  :
    1. 피부 분석 결과 저장
    2. 분석 결과 단건 조회
    3. 사용자의 분석 히스토리 전체 조회
    4. 가장 최근 분석 결과 조회
    5. 분석 결과 삭제 (soft delete)
    6. 위시리스트 추가 / 조회 / 삭제

흐름:
    FastAPI 라우터 → analysis_service 함수 호출
                    → db_manager 헬퍼로 DB 접근
                    → models.SkinAnalysisResult / Wishlist 로 변환 후 반환
─────────────────────────────────────────────────────────────
"""

import json
from datetime import datetime
from typing import Optional

from db.db_manager import execute_one, execute_write, execute_query
from db.models import SkinAnalysisResult, Wishlist
from db.schemas import AnalysisCreate, WishlistAdd


# ─────────────────────────────────────────────
# 1. 피부 분석 결과 저장
# ─────────────────────────────────────────────

def save_analysis(data: AnalysisCreate) -> SkinAnalysisResult:
    """
    피부 분석 결과 저장.
    - image_url (list) → JSON 문자열 변환 후 저장
    - analysis_data (dict) → JSON 문자열 변환 후 저장

    사용 예시:
        result = save_analysis(AnalysisCreate(
            user_id       = 1,
            image_url     = ["https://s3.../face1.jpg"],
            model_type    = "simple",
            analysis_data = {"moisture": 72, "oil": 45, "pore": 30}
        ))
    """
    image_url_json    = json.dumps(data.image_url,     ensure_ascii=False)
    analysis_data_json = json.dumps(data.analysis_data, ensure_ascii=False)

    analysis_id = execute_write(
        """
        INSERT INTO skin_analysis_results (user_id, image_url, model_type, analysis_data)
        VALUES (%s, %s, %s, %s)
        """,
        (data.user_id, image_url_json, data.model_type, analysis_data_json)
    )
    return get_analysis_by_id(analysis_id)


# ─────────────────────────────────────────────
# 2. 피부 분석 결과 조회
# ─────────────────────────────────────────────

def get_analysis_by_id(analysis_id: int) -> Optional[SkinAnalysisResult]:
    """
    analysis_id로 분석 결과 단건 조회.
    삭제된 결과는 반환하지 않음 (soft delete 고려).

    사용 예시:
        result = get_analysis_by_id(1)
    """
    row = execute_one(
        """
        SELECT * FROM skin_analysis_results
        WHERE analysis_id = %s AND deleted_at IS NULL
        """,
        (analysis_id,)
    )
    return SkinAnalysisResult.from_dict(row) if row else None


def get_analysis_history(user_id: int) -> list[SkinAnalysisResult]:
    """
    사용자의 전체 피부 분석 히스토리 조회.
    최신 순(created_at DESC)으로 반환.

    사용 예시:
        history = get_analysis_history(1)
    """
    rows = execute_query(
        """
        SELECT * FROM skin_analysis_results
        WHERE user_id = %s AND deleted_at IS NULL
        ORDER BY created_at DESC
        """,
        (user_id,)
    )
    return [SkinAnalysisResult.from_dict(row) for row in rows]


def get_latest_analysis(user_id: int) -> Optional[SkinAnalysisResult]:
    """
    사용자의 가장 최근 피부 분석 결과 조회.
    - LLM에 최근 피부 상태 컨텍스트 전달 시 사용
    - 분석 결과가 없으면 None 반환

    사용 예시:
        latest = get_latest_analysis(1)
        if latest:
            skin_context = latest.analysis_data
    """
    row = execute_one(
        """
        SELECT * FROM skin_analysis_results
        WHERE user_id = %s AND deleted_at IS NULL
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id,)
    )
    return SkinAnalysisResult.from_dict(row) if row else None


def get_analysis_by_model_type(
    user_id: int,
    model_type: str
) -> list[SkinAnalysisResult]:
    """
    모델 타입별 분석 히스토리 조회.
    - model_type: simple / detailed

    사용 예시:
        detailed_results = get_analysis_by_model_type(1, "detailed")
    """
    rows = execute_query(
        """
        SELECT * FROM skin_analysis_results
        WHERE user_id = %s AND model_type = %s AND deleted_at IS NULL
        ORDER BY created_at DESC
        """,
        (user_id, model_type)
    )
    return [SkinAnalysisResult.from_dict(row) for row in rows]


# ─────────────────────────────────────────────
# 3. 피부 분석 결과 삭제
# ─────────────────────────────────────────────

def delete_analysis(analysis_id: int) -> bool:
    """
    피부 분석 결과 삭제 (soft delete).
    - deleted_at에 현재 시각 기록

    사용 예시:
        success = delete_analysis(1)
    """
    affected = execute_write(
        """
        UPDATE skin_analysis_results
        SET deleted_at = %s
        WHERE analysis_id = %s AND deleted_at IS NULL
        """,
        (datetime.now(), analysis_id)
    )
    return affected > 0


# ─────────────────────────────────────────────
# 4. 위시리스트
# ─────────────────────────────────────────────

def add_to_wishlist(data: WishlistAdd) -> Wishlist:
    """
    위시리스트에 제품 추가.
    - 이미 추가된 제품(동일 user_id + product_vector_id)이면 예외 발생

    사용 예시:
        wish = add_to_wishlist(WishlistAdd(
            user_id           = 1,
            product_vector_id = "vec_abc123",
            product_name      = "라로슈포제 시카플라스트 밤 B5",
            message_id        = 10,
            product_description = "민감한 피부 진정 및 장벽 강화 크림"
        ))
    """
    # 중복 추가 방지
    existing = execute_one(
        """
        SELECT wish_id FROM wishlist
        WHERE user_id = %s AND product_vector_id = %s
        """,
        (data.user_id, data.product_vector_id)
    )
    if existing:
        raise ValueError("이미 위시리스트에 추가된 제품입니다.")

    wish_id = execute_write(
        """
        INSERT INTO wishlist
            (user_id, message_id, product_vector_id, product_name, product_description)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            data.user_id,
            data.message_id,
            data.product_vector_id,
            data.product_name,
            data.product_description,
        )
    )
    return get_wishlist_item_by_id(wish_id)


def get_wishlist_item_by_id(wish_id: int) -> Optional[Wishlist]:
    """
    wish_id로 위시리스트 단건 조회.

    사용 예시:
        item = get_wishlist_item_by_id(1)
    """
    row = execute_one(
        "SELECT * FROM wishlist WHERE wish_id = %s",
        (wish_id,)
    )
    return Wishlist.from_dict(row) if row else None


def get_wishlist_by_user(user_id: int) -> list[Wishlist]:
    """
    사용자의 전체 위시리스트 조회.
    최신 순(added_at DESC)으로 반환.

    사용 예시:
        items = get_wishlist_by_user(1)
    """
    rows = execute_query(
        """
        SELECT * FROM wishlist
        WHERE user_id = %s
        ORDER BY added_at DESC
        """,
        (user_id,)
    )
    return [Wishlist.from_dict(row) for row in rows]


def remove_from_wishlist(wish_id: int, user_id: int) -> bool:
    """
    위시리스트에서 제품 삭제 (hard delete).
    - user_id 검증으로 본인 항목만 삭제 가능

    사용 예시:
        success = remove_from_wishlist(wish_id=1, user_id=1)
    """
    affected = execute_write(
        """
        DELETE FROM wishlist
        WHERE wish_id = %s AND user_id = %s
        """,
        (wish_id, user_id)
    )
    return affected > 0


def remove_all_wishlist(user_id: int) -> bool:
    """
    사용자의 위시리스트 전체 삭제.
    - 회원 탈퇴 전 정리 또는 초기화 시 사용

    사용 예시:
        success = remove_all_wishlist(user_id=1)
    """
    affected = execute_write(
        "DELETE FROM wishlist WHERE user_id = %s",
        (user_id,)
    )
    return affected > 0

# ─────────────────────────────────────────────
# 5. 정밀 분석 Factorial 선택 (DB 기반)
# ─────────────────────────────────────────────

# metrics 지표명 → keywords.description 내 매핑 키워드
# 예: description = "수분 부족 개선, 잔주름 완화 (수분 / 탄력 / 주름)"
_METRIC_TO_DESC_KW = {
    "moisture":     ["수분"],
    "pore":         ["모공"],
    "wrinkle":      ["주름"],
    "elasticity":   ["탄력"],
    "pigmentation": ["색소"],
}

# 각 지표별 임계값 (0~100 정규화 score 기준)
# 이 값 이하면 해당 지표 '개선 필요' 판정 → 관련 루틴 선택
_METRIC_THRESHOLD = {
    "moisture":     65,
    "pore":         65,
    "wrinkle":      65,
    "elasticity":   60,
    "pigmentation": 70,
}


def get_skin_care_routines() -> list[dict]:
    """
    keywords 테이블에서 skin_care_routine 타입 전체 조회.

    반환 예시:
        [
          {"keyword_id": 1, "keyword": "moisturizing_boost", "label": "보습 강화", "description": "..."},
          {"keyword_id": 2, "keyword": "oil_cleansing",      "label": "오일 클렌징", "description": "..."},
          ...
        ]
    """
    rows = execute_query(
        """
        SELECT keyword_id, keyword, label, description
        FROM keywords
        WHERE type = 'skin_care_routine'
        ORDER BY keyword_id ASC
        """,
        ()
    )
    return [dict(row) for row in rows] if rows else []


def select_factorial(metrics: dict, min_count: int = 2, max_count: int = 5) -> list[str]:
    """
    정밀 분석(deep) metrics 점수 기반으로 적합한 케어 루틴 label 선택.

    동작 방식:
    1. DB에서 skin_care_routine 키워드 전체 조회
    2. metrics 중 임계값 이하인 지표 파악 (점수 낮을수록 우선)
    3. 낮은 지표와 description이 매칭되는 keyword의 label 선택
    4. min_count 미달 시 미매칭 루틴으로 fallback 보완
    5. 최종 min_count ~ max_count 개수로 반환

    Args:
        metrics: validate_node의 _normalize_deep() 결과
                 예) {"moisture": {"score": 55}, "pore": {"score": 62}, ...}
        min_count: 최소 반환 개수 (기본 2)
        max_count: 최대 반환 개수 (기본 5)

    Returns:
        label 문자열 리스트
        예) ["보습 강화", "모공 타이트닝", "탄력 강화"]

    사용 예시:
        labels = select_factorial(
            metrics={"moisture": {"score": 55}, "pore": {"score": 60}, ...}
        )
    """
    routines = get_skin_care_routines()
    if not routines:
        return []

    # 임계값 이하인 지표만 추출 → 점수 오름차순 (가장 나쁜 지표 우선)
    weak_metrics = sorted(
        [
            (key, metrics[key]["score"])
            for key in _METRIC_THRESHOLD
            if key in metrics and metrics[key]["score"] <= _METRIC_THRESHOLD[key]
        ],
        key=lambda x: x[1]
    )

    selected_labels = []
    seen_keywords   = set()

    # 낮은 지표 순서대로 description과 매칭되는 루틴 선택
    for metric_key, _score in weak_metrics:
        for routine in routines:
            kw    = routine.get("keyword", "")
            label = routine.get("label", "")
            desc  = routine.get("description", "")
            if kw in seen_keywords:
                continue
            # description에 해당 지표 키워드가 포함되면 선택
            desc_kws = _METRIC_TO_DESC_KW.get(metric_key, [])
            if any(dk in desc for dk in desc_kws):
                selected_labels.append(label)
                seen_keywords.add(kw)
        if len(selected_labels) >= max_count:
            break

    selected_labels = selected_labels[:max_count]

    # min_count 미달 시 아직 선택 안 된 루틴으로 보완 (fallback)
    if len(selected_labels) < min_count:
        for routine in routines:
            kw    = routine.get("keyword", "")
            label = routine.get("label", "")
            if kw not in seen_keywords:
                selected_labels.append(label)
                seen_keywords.add(kw)
            if len(selected_labels) >= min_count:
                break

    return selected_labels
