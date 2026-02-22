"""
전역 태깅 규칙 및 매칭 유틸리티
"""

# ─────────────────────────────────────────────────────────────
# 규칙 형식:
#   (매칭 키워드 리스트, 태그값)
#   → 텍스트에 키워드 중 하나라도 포함되면 해당 태그 부여
# ─────────────────────────────────────────────────────────────

CATEGORY_RULES: list[tuple[list[str], str]] = [
    (["여드름", "acne", "면포"],                                    "acne"),
    (["습진", "아토피", "피부염", "eczema", "dermatitis"],          "eczema"),
    (["건선", "psoriasis"],                                         "psoriasis"),
    (["색소", "기미", "잡티", "백반", "melasma", "vitiligo"],       "pigmentation"),
    (["주름", "탄력", "노화", "aging"],                             "anti-aging"),
    (["장벽", "보습", "건조", "barrier", "moistur"],               "barrier"),
    (["종양", "암", "암종", "육종", "carcinoma", "melanoma"],       "tumor"),
    (["감염", "바이러스", "세균", "진균", "fungal", "viral"],       "infection"),
    (["혈관", "혈관염", "vasculitis"],                              "vascular"),
    (["모발", "탈모", "alopecia"],                                  "hair"),
    (["두드러기", "urticaria", "가려움"],                           "urticaria"),
    (["사마귀", "wart"],                                            "wart"),
    (["흉터", "켈로이드", "scar", "keloid"],                        "scar"),
]

SKIN_TYPE_RULES: list[tuple[list[str], str]] = [
    (["건성", "건조", "dry", "보습", "수분"],               "dry"),
    (["지성", "oily", "sebum", "피지", "모공"],             "oily"),
    (["민감", "sensitive", "자극", "진정", "예민"],         "sensitive"),
    (["복합", "combination"],                               "combination"),
    (["아토피", "atopic"],                                  "atopic"),
]

CONCERN_TAG_RULES: list[tuple[list[str], str]] = [
    (["주름", "탄력", "노화", "aging", "wrinkle"],              "anti-aging"),
    (["미백", "톤", "색소", "기미", "brightening", "pigment"],  "brightening"),
    (["보습", "수분", "moistur", "hydrat", "건조"],             "moisturizing"),
    (["트러블", "여드름", "acne", "blemish"],                   "acne"),
    (["민감", "진정", "soothing", "calming"],                   "sensitive"),
    (["장벽", "barrier", "세라마이드"],                         "barrier"),
    (["모공", "pore", "sebum", "피지"],                         "pore"),
    (["탈모", "모발", "alopecia", "hair"],                      "hair-loss"),
    (["감염", "바이러스", "세균", "진균"],                      "infection"),
    (["가려움", "소양", "pruritus"],                            "itch"),
    (["홍반", "발진", "rash", "erythema"],                      "rash"),
]

INGREDIENT_TAG_RULES: list[tuple[list[str], str]] = [
    (["스테로이드", "steroid", "코르티코스테로이드"],        "steroid"),
    (["레티노이드", "레티놀", "retinoid", "retinol"],        "retinoid"),
    (["항생제", "antibiotic", "테트라사이클린"],             "antibiotic"),
    (["세라마이드", "ceramide"],                             "ceramide"),
    (["히알루론산", "hyaluronic"],                           "hyaluronic-acid"),
    (["나이아신아마이드", "niacinamide"],                    "niacinamide"),
    (["살리실산", "salicylic"],                              "salicylic-acid"),
    (["자외선차단제", "sunscreen", "spf"],                   "sunscreen"),
    (["향료", "fragrance", "parfum", "linalool", "limonene"], "fragrance"),
    (["방부제", "preservative", "paraben", "페녹시에탄올", "phenoxyethanol"], "preservative"),
    (["계면활성제", "surfactant", "lauryl", "laureth"],      "surfactant"),
    (["토코페롤", "tocopherol", "산화방지"],                 "antioxidant"),
    (["색소", "colorant", "pigment", "dye"],                 "colorant"),
]

# 모든 규칙 목록 — 전체 태깅이 필요할 때 순회용
ALL_RULES: dict[str, list[tuple[list[str], str]]] = {
    "category":       CATEGORY_RULES,
    "skin_type":      SKIN_TYPE_RULES,
    "concern_tag":    CONCERN_TAG_RULES,
    "ingredient_tag": INGREDIENT_TAG_RULES,
}

# [유틸 함수]

def match_tags(text: str, rules: list[tuple[list[str], str]]) -> list[str]:
    """
    텍스트와 규칙 목록을 받아 매칭된 태그 리스트를 반환.
    - 대소문자 무시
    - 중복 제거 (첫 등장 순서 유지)

    Args:
        text:  태깅 기준이 되는 텍스트 (성분명, 본문 등)
        rules: CATEGORY_RULES 등 규칙 상수

    Returns:
        매칭된 태그 문자열 리스트. 매칭 없으면 빈 리스트.

    Example:
        >>> match_tags("건조한 피부 장벽 관리", CONCERN_TAG_RULES)
        ['moisturizing', 'barrier']
    """
    text_lower = text.lower()

    return list(dict.fromkeys(
        tag
        for keywords, tag in rules
        if any(kw.lower() in text_lower for kw in keywords)
    ))

def match_all_tags(text: str) -> dict[str, list[str]]:
    """
    모든 규칙을 한 번에 적용해 카테고리별 태그를 반환.

    Returns:
        {
            "category":       [...],
            "skin_type":      [...],
            "concern_tag":    [...],
            "ingredient_tag": [...],
        }

    Example:
        >>> match_all_tags("건조한 민감 피부 세라마이드 장벽 강화")
        {
            "category":       ["barrier"],
            "skin_type":      ["dry", "sensitive"],
            "concern_tag":    ["moisturizing", "sensitive", "barrier"],
            "ingredient_tag": ["ceramide"],
        }
    """

    return {
        field: match_tags(text, rules)
        for field, rules in ALL_RULES.items()
    }