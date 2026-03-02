"""
keyword_service.py
─────────────────────────────────────────────────────────────
목적  : keywords 테이블 관련 비즈니스 로직 담당
역할  :
    1. 피부 케어 루틴 키워드 목록 조회 (skin_care_routine)
    2. 정밀 분석 metrics 기반 factorial label 선택
─────────────────────────────────────────────────────────────
"""

from db.db_manager import execute_query


# ─────────────────────────────────────────────
# 1. 피부 케어 루틴 키워드 조회
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
          {"keyword_id": 1, "type": "skin_care_routine", "keyword": "moisturizing_boost", "label": "보습 강화", "description": "..."},
          {"keyword_id": 2, "type": "skin_care_routine", "keyword": "oil_cleansing",      "label": "오일 클렌징", "description": "..."},
          ...
        ]
    """
    rows = execute_query(
        """
        SELECT keyword_id, type, keyword, label, description
        FROM keywords
        WHERE type = 'skin_care_routine'
        ORDER BY keyword_id ASC
        """,
        ()
    )
    return [dict(row) for row in rows] if rows else []


# ─────────────────────────────────────────────
# 2. 정밀 분석 Factorial 선택 (DB 기반)
# ─────────────────────────────────────────────

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
            kw    = routine.get("keyword") or ""
            label = routine.get("label") or ""
            desc  = routine.get("description") or ""   # NULL → 빈 문자열
            if not kw or not label:
                continue
            if kw in seen_keywords:
                continue
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
            kw    = routine.get("keyword") or ""
            label = routine.get("label") or ""
            if not kw or not label:
                continue
            if kw not in seen_keywords:
                selected_labels.append(label)
                seen_keywords.add(kw)
            if len(selected_labels) >= min_count:
                break

    return selected_labels
