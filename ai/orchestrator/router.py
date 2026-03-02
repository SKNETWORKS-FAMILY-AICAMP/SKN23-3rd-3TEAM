"""
router.py - 사용자 입력을 intent로 분류합니다.

[핵심 변경사항]
1. RouteDecision에 needs_product 플래그 추가
   - needs_rag: 벡터DB(가이드/성분/질환) 검색 여부
   - needs_product: Tavily 올리브영 직접 검색 여부 (기존 needs_oliveyoung 대체)
   - 두 플래그가 동시에 True → 병렬 처리 가능

2. 복합 intent 추가
   - routine_and_product: 루틴 + 제품 동시 요청 ("홍조에 좋은 루틴이랑 제품 추천")

3. 맥락 부족 감지
   - needs_context_check: 제품 추천인데 피부타입/고민 정보가 부족하면 True
   - pipeline에서 이 플래그를 보고 역질문 반환 결정
"""
from dataclasses import dataclass
from typing import Literal

Intent = Literal[
    # 즉시 처리 (LLM 불필요 or 최소)
    "out_of_domain",          # 피부 무관 질문
    "greeting",               # 인사/잡담
    "login_required",         # 비회원 + 분석 요청
    "ask_for_context",        # 맥락 부족 → 역질문 (LLM 없이 즉시 반환)

    # 일반 피부 상담 (RAG only)
    "general_advice",         # 피부 관리법/정보
    "routine_advice",         # 루틴 추천 (RAG only)
    "medical_advice",         # 피부과 상담 필요 수준

    # 제품 관련
    "product_recommend",      # 제품 추천 (Tavily only)
    "routine_and_product",    # 루틴 + 제품 동시 (RAG + Tavily)
    "ingredient_question",    # 성분 질문 (RAG only)

    # 분석 (Vision + RAG)
    "skin_analysis_fast",     # 빠른 분석 (이미지 1장)
    "skin_analysis_deep",     # 정밀 분석 (이미지 3장)

    # OCR
    "ingredient_analysis",    # 화장품 전성분 이미지 분석

    # 이력 기반
    "history_compare",        # 이전 분석 대비 변화
]


@dataclass(frozen=True)
class RouteDecision:
    intent: Intent
    needs_vision: bool
    needs_rag: bool          # 벡터DB(가이드/성분/질환) 검색
    needs_product: bool      # Tavily 올리브영 직접 검색 (기존 needs_oliveyoung 대체)
    needs_context_check: bool  # 제품 추천인데 피부 맥락 부족 가능성
    reason: str


# ── 키워드 사전 ───────────────────────────────────────────────

_SKIN_DOMAIN_KW = [
    "피부", "여드름", "홍조", "모공", "각질", "트러블", "색소", "기미", "잡티",
    "주름", "탄력", "노화", "건조", "지성", "민감", "복합", "건성", "중성",
    "루틴", "스킨케어", "세안", "클렌징", "토너", "에센스", "세럼", "크림",
    "선크림", "자외선", "화장품", "성분", "레티놀", "나이아신", "비타민c",
    "bha", "aha", "판테놀", "세라마이드", "히알루론산", "보습", "수분",
    "촉촉", "번들", "피지", "블랙헤드", "화이트헤드", "필링", "각질제거",
    "미백", "브라이트닝", "올리브영", "닥터지", "라로슈포제", "이니스프리",
    "아로마티카", "코스알엑스", "스킨1004", "셀퓨전씨",
    # 자연어 표현 추가
    "붉은기", "붉어", "붉음", "빨개", "빨갛", "빨간",
    "칙칙", "어두운 피부", "다크서클", "눈가",
    "트러블", "뾰루지", "뭐가 남", "자국", "흉터",
    "민감해", "따끔", "가렵", "건조해", "당김", "당겨",
    "번들거려", "번들번들", "기름지", "피지",
    "탄력없", "처져", "늘어져",
]

_OUT_OF_DOMAIN_KW = [
    "맛집", "음식", "레시피", "요리", "여행", "관광", "숙박", "호텔",
    "주식", "코인", "투자", "환율", "부동산",
    "영화", "드라마", "음악", "노래", "게임",
    "정치", "선거", "법률", "소송",
    "수학", "물리", "화학", "역사", "지리",
    "취업", "이력서", "자소서", "면접",
    "날씨", "스포츠", "축구", "야구",
]

_GREETING_KW = [
    "안녕", "반가워", "처음", "hi", "hello", "ㅎㅇ", "안녕하세요",
    "뭐해", "뭐할수있어", "뭘 도와", "어떤 도움", "무엇을 도와",
]

_MEDICAL_KW = [
    "진단", "치료", "처방", "약", "병원", "의사", "피부과",
    "항생제", "스테로이드", "의약품", "처방전",
]

# 제품 추천 키워드
_PRODUCT_KW = [
    "추천", "어떤 제품", "뭐 써", "뭐 바르", "뭐 쓰면",
    "올리브영", "구매", "살까", "살만한", "살 수 있",
    "브랜드", "제품", "써볼만한",
    # 자연어 표현 추가
    "잡아주", "완화해주", "도움되는", "좋은거",
    "뭐가 좋아", "뭐가 좋을", "어떤거", "어떤 거",
    "써봤어", "효과있는", "효과 있는",
]

# 루틴 키워드
_ROUTINE_KW = [
    "루틴", "아침", "저녁", "순서", "사용법", "몇 번", "빈도",
    "단계", "레이어링", "겹쳐", "같이 써", "함께 쓰",
]

# ── 제품 카테고리 키워드 (구체적인 품목) ──────────────────────────
_PRODUCT_CATEGORY_KW = [
    "크림", "세럼", "로션", "토너", "스킨", "에센스", "선크림",
    "폼클렌징", "폼 클렌징", "클렌저", "클렌징", "세안",
    "마스크팩", "마스크", "앰플", "아이크림", "미스트",
    "필링", "패드", "오일", "수분크림", "보습크림",
    "비비크림", "bb크림", "쿠션", "젤크림",
]

# ── 약어/오타/줄임말 → 정규 카테고리 매핑 ──────────────────────────
# 사용자가 짧게 치거나 오타를 내도 의도 파악
_CATEGORY_NORMALIZE = {
    # 폼클렌징 계열
    "폼클": "폼클렌징",
    "폼클린저": "폼클렌징",
    "폼클렌져": "폼클렌징",
    "폼클린징": "폼클렌징",
    "폼크렌징": "폼클렌징",
    "폼클랜징": "폼클렌징",
    "세안제": "폼클렌징",
    "클렌져": "클렌징",
    "클랜징": "클렌징",
    # 수분크림 계열
    "수분": "수분크림",
    "수크림": "수분크림",
    "모이스처": "수분크림",
    "보습": "보습크림",
    # 세럼 계열
    "써럼": "세럼",
    "세럼크림": "세럼",
    # 토너 계열
    "토닉": "토너",
    "스킨토너": "토너",
    # 선크림 계열
    "선스크린": "선크림",
    "썬크림": "선크림",
    "선블록": "선크림",
    "선케어": "선크림",
    "자외선차단": "선크림",
    # 아이크림 계열
    "아이": "아이크림",
    "눈가크림": "아이크림",
    # BB/쿠션 계열
    "비비": "bb크림",
    "비비크림": "bb크림",
    # 마스크 계열
    "마스크팩": "마스크팩",
    "팩": "마스크팩",
    "시트마스크": "마스크팩",
    # 앰플 계열
    "앰플": "앰플",
    "엠플": "앰플",
    # 에센스 계열
    "에센스": "에센스",
    "에쎈스": "에센스",
    # 로션 계열
    "로숀": "로션",
    "밀크로션": "로션",
    # 오일 계열
    "클렌징오일": "오일",
    "클랜징오일": "오일",
    # 패드 계열
    "패드": "패드",
    "필링패드": "패드",
    "토닝패드": "패드",
}


def _normalize_category(text: str) -> str:
    """
    사용자 입력에서 약어/오타를 정규 카테고리로 치환합니다.
    예) "폼클 추천해줘" → "폼클렌징 추천해줘"
    """
    for abbr, full in _CATEGORY_NORMALIZE.items():
        if abbr in text:
            text = text.replace(abbr, full)
    return text


def _extract_category_from_history(chat_history: list | None) -> str:
    """
    직전 대화에서 마지막으로 언급된 제품 카테고리를 추출합니다.
    "폼클은?" → "폼클렌징"
    "제품도 알려줘" 같은 팔로우업 발화 시 이전 맥락 이어받기용.
    """
    if not chat_history:
        return ""
    # 최근 메시지부터 역순으로 탐색 (최대 4개 메시지)
    recent = chat_history[-4:]
    for msg in reversed(recent):
        role = msg.get("role", "")
        msg_text = (msg.get("content") or "").lower()
        # 정규화 후 카테고리 탐색
        normalized = _normalize_category(msg_text)
        for kw in _PRODUCT_CATEGORY_KW:
            if kw in normalized:
                print(f"[ROUTER] 이전 대화에서 카테고리 감지: '{kw}' (role={role})", flush=True)
                return kw
    return ""

_INGREDIENT_QUESTION_KW = [
    "성분", "전성분", "레티놀", "나이아신아마이드", "비타민c",
    "bha", "aha", "판테놀", "세라마이드", "히알루론산",
    "어떤 성분", "성분이 뭐", "성분 좋",
]

_HISTORY_KW = [
    "저번", "이전", "지난", "예전", "비교", "변화", "달라졌",
    "좋아졌", "나빠졌", "변했",
]

# 텍스트로 분석 요청하는 키워드 (analysis_type 없이 채팅으로 요청하는 경우)
_ANALYSIS_REQUEST_KW = [
    "빠른 분석", "빠른분석", "피부 분석", "피부분석",
    "정밀 분석", "정밀분석", "정량 분석", "정량분석",
    "분석해줘", "분석해 줘", "분석 해줘", "분석해주세요",
    "사진 분석", "사진분석", "얼굴 분석", "얼굴분석",
    "내 피부 분석", "피부 좀 분석", "피부상태 분석",
]

# 피부타입/고민 맥락 키워드 (제품 추천 시 맥락 충분 여부 판단용)
_CONTEXT_KW = [
    "건성", "지성", "복합", "복합성", "민감", "민감성", "중성",
    "여드름", "홍조", "모공", "각질", "잡티", "기미", "주름",
    "트러블", "색소침착", "미백", "탄력", "보습", "수분부족",
    "번들", "피지", "건조",
]


def _has_any(text: str, keywords: list) -> bool:
    return any(kw in text for kw in keywords)


def _has_context(text: str, user_profile: dict | None) -> bool:
    """
    제품 추천에 필요한 최소 피부 맥락이 있는지 확인합니다.

    맥락 있다고 판단하는 경우:
    1. 로그인 유저 프로필에 피부타입이 있음
    2. 질문 자체에 피부타입/고민 키워드 있음
    """
    # 로그인 유저 프로필 확인
    if user_profile and user_profile.get("skin_type_label"):
        return True
    if user_profile and user_profile.get("skin_concern"):
        return True

    # 질문 자체에 맥락 키워드 있는지
    if _has_any(text, _CONTEXT_KW):
        return True

    return False


def decide(
    user_text: str,
    analysis_type: str | None,
    has_images: bool,
    user_id: int | None,
    user_profile: dict | None = None,
    chat_history: list | None = None,
) -> RouteDecision:
    """
    사용자 입력을 분석하여 RouteDecision을 반환합니다.

    짧은 팔로우업 발화 처리:
    - chat_history 있고 "원해", "알려줘" 같은 표현이면 도메인 차단 완화
    - 이전 대화가 피부 주제였으면 맥락 이어받기
    """
    # 약어/오타 정규화 먼저 적용 ("폼클" → "폼클렌징" 등)
    text = _normalize_category((user_text or "").lower().strip())
    has_history = bool(chat_history and len(chat_history) >= 2)

    # ── 1. 프론트 분석 모드 명시 ─────────────────────────────
    if analysis_type == "quick":
        if not user_id:
            return RouteDecision("login_required", False, False, False, False, "비회원 분석 요청")
        return RouteDecision("skin_analysis_fast", True, True, False, False, "빠른 분석 모드")

    if analysis_type == "detailed":
        if not user_id:
            return RouteDecision("login_required", False, False, False, False, "비회원 분석 요청")
        return RouteDecision("skin_analysis_deep", True, True, False, False, "정밀 분석 모드")

    if analysis_type == "ingredient":
        if not user_id:
            return RouteDecision("login_required", False, False, False, False, "비회원 성분분석 요청")
        return RouteDecision("ingredient_analysis", False, True, False, False, "성분 분석 모드")

    # ── 2. 인사/잡담 ─────────────────────────────────────────
    if _has_any(text, _GREETING_KW) and not _has_any(text, _SKIN_DOMAIN_KW):
        return RouteDecision("greeting", False, False, False, False, "인사/잡담")

    # ── 3. 도메인 밖 차단 ────────────────────────────────────
    if _has_any(text, _OUT_OF_DOMAIN_KW) and not _has_any(text, _SKIN_DOMAIN_KW):
        return RouteDecision("out_of_domain", False, False, False, False, "도메인 외 질문")

    # ── 4. 피부 도메인 확인 ──────────────────────────────────
    is_skin = _has_any(text, _SKIN_DOMAIN_KW) or len(text) < 10

    # 핵심: 짧은 팔로우업 발화 + 이전 대화 있으면 도메인 차단 완화
    _FOLLOWUP_KW = [
        "원해", "알려줘", "궁금해", "더 알려줘", "그럼", "그리고",
        "도 알려줘", "도 원해", "도 추천", "도 해줘",
        "이건", "저건", "그건", "이거", "저거", "그거",
        "어때", "어떤게", "뭐가", "좋을까", "될까",
        "어떻게 해", "어떻게 쓰",
    ]
    if not is_skin and has_history and _has_any(text, _FOLLOWUP_KW):
        is_skin = True
        print("[ROUTER] 팔로우업 발화 감지 → 맥락 이어받기", flush=True)

    if not is_skin:
        return RouteDecision("out_of_domain", False, False, False, False, "피부 도메인 키워드 없음")

    # ── 4-1. 텍스트로 분석 요청 (비로그인 차단) ────────────────
    if _has_any(text, _ANALYSIS_REQUEST_KW):
        if not user_id:
            return RouteDecision("login_required", False, False, False, False, "비회원 분석 요청(텍스트)")
        # 로그인 유저면 빠른 분석으로 처리 (이미지는 별도 업로드 필요 안내)
        return RouteDecision("general_advice", False, True, False, False, "분석 요청 → 이미지 업로드 안내")

    # ── 5. 의료 수준 질문 ────────────────────────────────────
    if _has_any(text, _MEDICAL_KW):
        return RouteDecision("medical_advice", False, True, False, False, "의료 관련 질문")

    # ── 6. 이전 분석 비교 ────────────────────────────────────
    if _has_any(text, _HISTORY_KW) and user_id:
        return RouteDecision("history_compare", False, True, False, False, "분석 이력 비교")

    # ── 7. 루틴 + 제품 판단 ────────────────────────────────────
    has_routine        = _has_any(text, _ROUTINE_KW)
    has_category       = _has_any(text, _PRODUCT_CATEGORY_KW)
    has_explicit       = _has_any(text, [
        "올리브영", "구매", "살까", "살만한", "어떤 제품",
        "뭐 써", "뭐 바르", "뭐 쓰면", "써볼만한",
    ])
    has_vague          = _has_any(text, [
        "제품", "추천", "좋은거", "뭐가 좋아", "뭐가 좋을",
        "어떤거", "어떤 거", "잡아주", "완화해주", "효과있는", "효과 있는",
        "알려줘", "도 알려줘", "도 추천", "뭐써", "뭐쓰",
    ])
    has_product_intent = has_category or has_explicit

    # ── 7-1. 루틴 판단 (제품 카테고리 없으면 루틴만) ──────────
    if has_routine:
        if has_product_intent:
            ctx_ok = _has_context(text, user_profile) or has_history
            return RouteDecision(
                "routine_and_product", False, True, True,
                not ctx_ok, "루틴 + 제품 복합 요청"
            )
        return RouteDecision("routine_advice", False, True, False, False, "루틴 관련 질문")

    # ── 7-2. 제품 카테고리 명시된 경우 → 바로 검색 ────────────
    if has_product_intent:
        ctx_ok = _has_context(text, user_profile) or has_history
        return RouteDecision(
            "product_recommend", False, False, True,
            not ctx_ok, "제품 추천 요청"
        )

    # ── 7-3. 모호한 제품 요청 ("제품도 알려줘", "추천해줘" 등) ──
    # chat_history에서 직전에 언급된 카테고리 이어받기
    if has_vague:
        history_category = _extract_category_from_history(chat_history)
        if history_category:
            # 이전 대화 카테고리를 현재 text에 합쳐서 재판단
            print(f"[ROUTER] 이전 카테고리 이어받기: '{history_category}'", flush=True)
            ctx_ok = _has_context(text, user_profile) or has_history
            return RouteDecision(
                "product_recommend", False, False, True,
                not ctx_ok, f"맥락 이어받기 → {history_category} 제품 추천"
            )
        # 이전 대화에도 카테고리 없음 → 역질문
        return RouteDecision(
            "ask_for_category", False, False, False, False, "카테고리 미특정 → 역질문"
        )

    # ── 8. 성분 질문 ────────────────────────────────────────
    if _has_any(text, _INGREDIENT_QUESTION_KW):
        return RouteDecision("ingredient_question", False, True, False, False, "성분 관련 질문")

    # ── 9. 기본: 일반 피부 상담 ─────────────────────────────
    return RouteDecision("general_advice", False, True, False, False, "일반 피부 상담")
