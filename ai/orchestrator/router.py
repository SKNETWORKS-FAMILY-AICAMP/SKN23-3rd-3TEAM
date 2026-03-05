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

4. LLM 라우팅
   - 비로그인(user_id=None): GPT로 intent 판단, 분석 기능은 login_required로 차단
   - 로그인(user_id 있음): GPT로 intent 판단, DB 프로필 + 이미지 유무 + 분석 이력 활용
   - 공통: LLM 실패 시 기존 키워드 방식으로 자동 폴백
"""
import json
import re
import time
from dataclasses import dataclass
from typing import Literal

from openai import OpenAI

from ai.config.settings import OPENAI_API_KEY, OPENAI_MODEL

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



# OpenAI 클라이언트 (LLM 라우팅 전용)

_LLM_CLIENT: OpenAI | None = None

def _get_llm_client() -> OpenAI:
    """OpenAI 클라이언트 싱글턴 (router 전용, 지연 초기화)"""
    global _LLM_CLIENT
    if _LLM_CLIENT is None:
        _LLM_CLIENT = OpenAI(api_key=OPENAI_API_KEY)
    return _LLM_CLIENT


# intent → RouteDecision 플래그 매핑 (공통)

_INTENT_FLAGS = {
    # 즉시 응답 (파이프라인 스킵)
    "out_of_domain":       {"needs_vision": False, "needs_rag": False, "needs_product": False, "needs_context_check": False},
    "greeting":            {"needs_vision": False, "needs_rag": False, "needs_product": False, "needs_context_check": False},
    "login_required":      {"needs_vision": False, "needs_rag": False, "needs_product": False, "needs_context_check": False},
    "ask_for_context":     {"needs_vision": False, "needs_rag": False, "needs_product": False, "needs_context_check": False},
    "ask_for_category":    {"needs_vision": False, "needs_rag": False, "needs_product": False, "needs_context_check": False},
    "ask_for_skin_info":   {"needs_vision": False, "needs_rag": False, "needs_product": False, "needs_context_check": False},
    # 일반 상담 (RAG)
    "general_advice":      {"needs_vision": False, "needs_rag": True,  "needs_product": False, "needs_context_check": False},
    "routine_advice":      {"needs_vision": False, "needs_rag": True,  "needs_product": False, "needs_context_check": False},
    "medical_advice":      {"needs_vision": False, "needs_rag": True,  "needs_product": False, "needs_context_check": False},
    "ingredient_question": {"needs_vision": False, "needs_rag": True,  "needs_product": False, "needs_context_check": False},
    # 제품 추천 (Tavily)
    "product_recommend":   {"needs_vision": False, "needs_rag": False, "needs_product": True,  "needs_context_check": True},
    "routine_and_product": {"needs_vision": False, "needs_rag": True,  "needs_product": True,  "needs_context_check": True},
    # 분석 (Vision + RAG) - 회원 전용
    "skin_analysis_fast":  {"needs_vision": True,  "needs_rag": True,  "needs_product": False, "needs_context_check": False},
    "skin_analysis_deep":  {"needs_vision": True,  "needs_rag": True,  "needs_product": False, "needs_context_check": False},
    "ingredient_analysis": {"needs_vision": True, "needs_rag": True,  "needs_product": False, "needs_context_check": False},
    "history_compare":     {"needs_vision": False, "needs_rag": True,  "needs_product": False, "needs_context_check": False},
}


# 비로그인 전용 LLM 라우팅

_GUEST_ALLOWED_INTENTS = [
    "out_of_domain",
    "greeting",
    "login_required",
    "ask_for_context",
    "ask_for_category",
    "general_advice",
    "routine_advice",
    "medical_advice",
    "product_recommend",
    "routine_and_product",
    "ingredient_question",
]

_LLM_ROUTER_GUEST_PROMPT = """\
너는 피부/스킨케어 전문 AI 챗봇의 intent 분류기이다.
사용자의 메시지를 읽고, 아래 intent 중 가장 적합한 것을 정확히 하나 선택해라.

## intent 목록 및 판단 기준

1. "out_of_domain" — 피부/스킨케어와 전혀 관련 없는 질문 (맛집, 여행, 주식, 코딩 등)
2. "greeting" — 인사, 잡담, 챗봇 소개 요청 ("안녕", "뭐 도와줄 수 있어?")
3. "login_required" — 피부 사진 분석, 정밀 분석, 전성분 분석, 이전 분석 비교 등 로그인이 필요한 기능 요청
4. "ask_for_context" — 제품 추천을 원하는데 피부타입/고민 정보가 전혀 없는 경우 ("추천해줘"만 있고 피부 정보 없음)
5. "ask_for_category" — 제품 추천을 원하지만 제품 종류(크림, 세럼, 토너 등)가 특정되지 않은 경우
6. "general_advice" — 피부 관리법, 생활 습관, 음식, 피부 관련 일반 지식 질문
7. "routine_advice" — 스킨케어 루틴 추천/순서/사용법 질문 (제품 추천 없이 루틴만)
8. "medical_advice" — 피부과 진료, 처방약, 치료가 필요한 수준의 질문
9. "product_recommend" — 특정 제품 카테고리 추천 요청 ("건성 피부에 수분크림 추천해줘")
10. "routine_and_product" — 루틴 추천과 제품 추천을 동시에 요청 ("아침 루틴이랑 세럼 추천해줘")
11. "ingredient_question" — 화장품 성분에 대한 질문 ("레티놀이 뭐야?", "나이아신아마이드 효과")

## 핵심 판단 규칙 (위에서부터 순서대로 적용 — 먼저 매칭되면 아래 규칙은 무시)

1. 피부 사진 분석/정밀 분석/전성분 분석/이전 분석 비교 → 무조건 "login_required"
2. "루틴", "관리법", "케어법", "관리 방법" 키워드가 포함되면:
   - 루틴/관리법 + 구체적 제품(세럼, 크림 등) 둘 다 요청 → "routine_and_product"
   - 루틴/관리법만 요청 → "routine_advice" (⚠️ ask_for_category가 아님!)
3. 사용자가 피부타입/고민만 알려주는 짧은 메시지("지성이야", "복합성", "여드름이 고민이야" 등):
   - 이전 대화 맥락에서 어떤 주제를 논의 중이었는지 파악하여 해당 intent로 이어받기
   - 이전 맥락이 불명확하면 → "general_advice"
4. "추천해줘" + 구체적 제품 카테고리(세럼, 크림, 토너 등) 있음 → "product_recommend"
5. "추천해줘" + 피부 정보 있음 + 카테고리 없음 → "ask_for_category"
6. "추천해줘" + 피부 정보 없음 + 카테고리 없음 → "ask_for_context"
7. 성분 이름 언급 + 질문 → "ingredient_question"
8. 피부 관리/습관/음식/일반 지식 → "general_advice"
9. 피부와 전혀 무관 → "out_of_domain"
10. 판단이 애매하면 "general_advice"로 분류 (보수적 처리)

⚠️ 주의사항:
- "루틴 추천", "관리법 추천", "케어법 알려줘"는 제품 추천이 아니다. 반드시 routine_advice로 분류한다.
- "알려줘", "궁금해" 같은 표현만으로 ask_for_category로 분류하지 않는다.
- ask_for_category는 오직 "제품 추천을 원하는데 제품 종류만 빠진 경우"에만 사용한다.

## 대화 맥락 활용
- 이전 대화가 제공되면, 현재 메시지가 짧은 팔로우업("그것도 알려줘", "세럼도")이어도 맥락을 이어받아 판단
- 이전 대화에서 피부타입/고민이 언급되었으면 맥락 있는 것으로 간주

## 응답 형식
반드시 아래 JSON 형식으로만 응답. 다른 텍스트 없이 JSON만 출력:
{{"intent": "<intent>", "reason": "<한국어 판단 근거 1줄>", "has_skin_context": <true/false>, "has_category": <true/false>}}

- has_skin_context: 사용자 메시지 또는 대화 이력에서 피부타입/고민 정보가 파악되는지
- has_category: 제품 카테고리(크림, 세럼, 토너 등)가 특정되는지
"""


# 로그인 회원 전용 LLM 라우팅

_MEMBER_ALLOWED_INTENTS = [
    "out_of_domain",
    "greeting",
    "ask_for_context",
    "ask_for_category",
    "general_advice",
    "routine_advice",
    "medical_advice",
    "product_recommend",
    "routine_and_product",
    "ingredient_question",
    "skin_analysis_fast",
    "skin_analysis_deep",
    "ingredient_analysis",
    "history_compare",
]

_LLM_ROUTER_MEMBER_PROMPT = """\
너는 피부/스킨케어 전문 AI 챗봇의 intent 분류기이다.
로그인된 회원의 메시지를 분석하여 가장 적합한 intent를 정확히 하나 선택해라.

## 회원 프로필 정보
{profile_block}

## 이미지 첨부 여부
{image_block}

## intent 목록 및 판단 기준

### 즉시 처리
1. "out_of_domain" — 피부/스킨케어와 전혀 관련 없는 질문 (맛집, 여행, 주식, 코딩 등)
2. "greeting" — 인사, 잡담, 챗봇 소개 요청

### 피부 분석 (회원 전용)
3. "skin_analysis_fast" — 빠른 피부 분석 요청 (얼굴 사진 1장). "빠른 분석", "간단히 분석", "사진 하나로 분석" 등
4. "skin_analysis_deep" — 정밀 피부 분석 요청 (좌·정면·우측 사진 3장). "정밀 분석", "자세히 분석", "정량 분석" 등
5. "ingredient_analysis" — 화장품 전성분 이미지 분석. "성분 분석해줘", "이 성분표 분석", "전성분 분석" 등
6. "history_compare" — 이전 분석 결과와 현재 상태 비교. "저번 분석이랑 비교", "피부 좋아졌어?", "변화 있어?" 등

### 일반 상담
7. "general_advice" — 피부 관리법, 생활 습관, 음식, 피부 관련 일반 지식
8. "routine_advice" — 스킨케어 루틴 추천/순서/사용법 (제품 추천 없이 루틴만)
9. "medical_advice" — 피부과 진료, 처방약, 치료가 필요한 수준의 질문
10. "ingredient_question" — 화장품 성분에 대한 질문 ("레티놀이 뭐야?", "나이아신아마이드 효과")

### 제품 추천
11. "product_recommend" — 특정 제품 카테고리 추천 ("건성에 수분크림 추천해줘")
12. "routine_and_product" — 루틴 + 제품 동시 요청 ("아침 루틴이랑 세럼 추천")

### 역질문
13. "ask_for_context" — 제품 추천인데 피부 정보도 없고 카테고리도 없음 (프로필에도 없는 경우만)
14. "ask_for_category" — 피부 정보는 있지만 제품 종류가 특정 안 됨

## 핵심 판단 규칙 (위에서부터 순서대로 적용 — 먼저 매칭되면 아래 규칙은 무시)

### 분석 관련
- 이미지가 첨부되어 있고 분석 관련 표현 → "skin_analysis_fast" 또는 "skin_analysis_deep"
- "전성분", "성분표", "성분 분석" + 이미지 → "ingredient_analysis"
- "저번 분석", "이전 결과", "변화", "비교" → "history_compare"
- 이미지 없이 "분석해줘"라고만 하면 → "general_advice" (이미지 업로드 안내 필요)

### 루틴/관리법 관련 (제품 추천보다 우선 판단)
- "루틴", "관리법", "케어법", "관리 방법" 키워드 + 제품(세럼, 크림 등) 둘 다 요청 → "routine_and_product"
- "루틴", "관리법", "케어법", "관리 방법" 키워드만 → "routine_advice" (⚠️ ask_for_category 아님!)

### 피부타입/고민 선언 (팔로우업)
- 사용자가 피부타입이나 고민만 알려주는 짧은 메시지 → 이전 대화 맥락의 intent를 이어받기

### 제품 추천 관련
- 회원 프로필에 피부타입/고민이 있으면 has_skin_context=true로 판단
- "추천해줘" + 구체적 제품 카테고리(세럼, 크림, 토너 등) 있음 → "product_recommend"
- "추천해줘" + 피부 정보 있음 + 카테고리 없음 → "ask_for_category"
- "추천해줘" + 피부 정보 없음 + 카테고리 없음 → "ask_for_context"

### 일반 상담
- 성분 이름 + 질문 → "ingredient_question"
- 피부 관리/습관/음식/원인/이유 → "general_advice"
- 피부과/치료/처방 → "medical_advice"
- 피부와 전혀 무관 → "out_of_domain"
- 판단이 애매하면 "general_advice" (보수적 처리)

⚠️ 주의사항:
- "루틴 추천", "관리법 추천", "케어법 알려줘"는 제품 추천이 아니다. 반드시 routine_advice로 분류한다.
- ask_for_category는 오직 "제품 추천을 원하는데 제품 종류만 빠진 경우"에만 사용한다.

### 팔로우업 처리
- 이전 대화 맥락이 있으면 짧은 발화("그것도", "세럼도", "알려줘")도 맥락 이어받기
- 이전에 제품 추천 대화였으면 "다른 거도 추천해줘" → "product_recommend"

## 응답 형식
반드시 아래 JSON만 출력:
{{"intent": "<intent>", "reason": "<한국어 판단 근거 1줄>", "has_skin_context": <true/false>, "has_category": <true/false>}}

- has_skin_context: 메시지/대화이력/회원프로필에서 피부타입 또는 고민 정보가 있는지
- has_category: 제품 카테고리(크림, 세럼, 토너 등)가 특정되는지
"""


# LLM 라우팅 공통 헬퍼

def _build_history_summary(chat_history: list | None, max_turns: int = 3) -> str:
    """최근 N턴의 대화를 요약 문자열로 변환 (LLM 라우팅 컨텍스트용)"""
    if not chat_history:
        return ""
    recent = chat_history[-(max_turns * 2):]
    lines = []
    for msg in recent:
        role = msg.get("role", "unknown")
        content = (msg.get("content") or "")[:150]  # 메시지당 150자 제한
        if content:
            prefix = "사용자" if role == "user" else "챗봇"
            lines.append(f"{prefix}: {content}")
    return "\n".join(lines)


def _build_profile_block(user_profile: dict | None) -> str:
    """회원 프로필을 LLM 프롬프트용 텍스트로 변환"""
    if not user_profile:
        return "프로필 없음"

    parts = []
    if user_profile.get("skin_type_label"):
        parts.append(f"- 피부타입: {user_profile['skin_type_label']}")
    if user_profile.get("skin_concern"):
        parts.append(f"- 피부고민: {user_profile['skin_concern']}")
    if user_profile.get("age"):
        parts.append(f"- 나이: {user_profile['age']}세")
    if user_profile.get("gender"):
        g = "여성" if user_profile["gender"] == "female" else "남성"
        parts.append(f"- 성별: {g}")
    if user_profile.get("recent_analysis_summary"):
        parts.append(f"- {user_profile['recent_analysis_summary']}")

    return "\n".join(parts) if parts else "프로필에 피부 정보 없음"


def _build_image_block(has_images: bool) -> str:
    """이미지 첨부 여부 텍스트"""
    if has_images:
        return "이미지가 첨부되어 있음 (피부 사진 또는 성분표일 수 있음)"
    return "이미지 첨부 없음"


def _parse_llm_response(raw: str) -> dict | None:
    """LLM JSON 응답 파싱. 실패 시 None 반환."""
    try:
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw.strip())
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None


def _call_llm_router(system_prompt: str, user_payload: str) -> dict | None:
    """
    LLM 라우팅 공통 호출.
    Returns parsed JSON dict or None on failure.
    """
    try:
        client = _get_llm_client()
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_payload},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            max_tokens=200,
        )
        raw = resp.choices[0].message.content or ""
        print(f"[LLM_ROUTER] raw: {raw}", flush=True)
        return _parse_llm_response(raw)
    except Exception as e:
        print(f"[LLM_ROUTER] API 호출 실패: {repr(e)}", flush=True)
        return None


# 비로그인 LLM 라우팅

def _llm_decide_guest(
    user_text: str,
    chat_history: list | None = None,
) -> RouteDecision | None:
    """
    비로그인 전용 LLM intent 분류.
    실패 시 None → 키워드 폴백.
    """
    t0 = time.perf_counter()

    # 사용자 메시지 구성
    history_text = _build_history_summary(chat_history, max_turns=3)
    user_payload = f"사용자 메시지: {user_text}"
    if history_text:
        user_payload = f"[이전 대화]\n{history_text}\n\n[현재 메시지]\n{user_text}"

    result = _call_llm_router(_LLM_ROUTER_GUEST_PROMPT, user_payload)
    if not result:
        print(f"[LLM_ROUTER] 비로그인 파싱 실패 → 폴백 ({time.perf_counter()-t0:.3f}s)", flush=True)
        return None

    intent = result.get("intent", "").strip()
    reason = result.get("reason", "LLM 분류")
    has_skin_context = result.get("has_skin_context", False)
    has_category = result.get("has_category", False)

    # 유효성 검증
    if intent not in _GUEST_ALLOWED_INTENTS:
        print(f"[LLM_ROUTER] 비로그인 허용되지 않은 intent '{intent}' → 폴백", flush=True)
        return None

    # ── 피부타입/고민만 알려주는 메시지 감지 ──────────────────
    # "나는 복합성이야", "지성이야", "여드름이 고민이야" 등
    # 이전 대화에서 역질문(피부타입 물어봄) 후 사용자가 답하는 패턴
    _SKIN_TYPE_DECLARE_KW = [
        "건성", "지성", "복합성", "민감성", "중성",
        "건조", "지성이야", "민감해", "복합이야",
    ]
    _CONCERN_DECLARE_KW = [
        "여드름", "홍조", "모공", "각질", "주름", "탄력",
        "색소", "기미", "잡티", "트러블", "뾰루지",
    ]
    text_lower = (user_text or "").strip().lower()
    is_type_declaration = (
        len(text_lower) < 20
        and has_skin_context
        and (_has_any(text_lower, _SKIN_TYPE_DECLARE_KW) or _has_any(text_lower, _CONCERN_DECLARE_KW))
    )

    if is_type_declaration and intent in ("product_recommend", "ask_for_category", "ask_for_context"):
        # 이전 대화 맥락을 확인해서 적절한 intent로 리다이렉트
        prev_intent = None
        if chat_history:
            for msg in reversed(chat_history[-6:]):
                content = (msg.get("content") or "").lower()
                if "루틴" in content:
                    prev_intent = "routine_advice"
                    break
                if any(kw in content for kw in ["추천", "제품", "크림", "세럼", "토너"]):
                    prev_intent = "product_recommend"
                    break
                if any(kw in content for kw in ["관리", "케어", "방법", "어떻게"]):
                    prev_intent = "general_advice"
                    break

        intent = prev_intent or "general_advice"
        reason = f"피부타입 선언 → 이전 맥락 기반 '{intent}'으로 전환"
        print(f"[LLM_ROUTER] 피부타입 선언 감지 → {intent}", flush=True)

    # 제품 추천 맥락 부족 → 역질문 보정
    elif intent == "product_recommend":
        if not has_skin_context and not has_category:
            intent = "ask_for_context"
            reason = "LLM: 제품 추천이지만 피부 맥락+카테고리 모두 부족"
        elif has_skin_context and not has_category:
            intent = "ask_for_category"
            reason = "LLM: 제품 추천이지만 카테고리 미특정"

    if intent == "routine_and_product" and not has_skin_context:
        intent = "ask_for_context"
        reason = "LLM: 루틴+제품이지만 피부 맥락 부족"

    # 플래그 매핑
    flags = _INTENT_FLAGS.get(intent, _INTENT_FLAGS["general_advice"])
    needs_ctx = flags["needs_context_check"] and not has_skin_context

    elapsed = time.perf_counter() - t0
    print(
        f"[LLM_ROUTER] GUEST intent={intent} | ctx={has_skin_context} "
        f"| cat={has_category} | {elapsed:.3f}s",
        flush=True,
    )

    return RouteDecision(
        intent=intent,
        needs_vision=flags["needs_vision"],
        needs_rag=flags["needs_rag"],
        needs_product=flags["needs_product"],
        needs_context_check=needs_ctx,
        reason=f"[LLM] {reason}",
    )



# 로그인 회원 LLM 라우팅

def _llm_decide_member(
    user_text: str,
    has_images: bool,
    user_profile: dict | None,
    chat_history: list | None = None,
) -> RouteDecision | None:
    """
    로그인 회원 전용 LLM intent 분류.

    비로그인 대비 추가 정보:
    - user_profile (피부타입, 고민, 나이, 성별, 최근 분석)
    - has_images (이미지 첨부 여부)
    - 분석 intent 허용 (fast/deep/ingredient/history)

    실패 시 None → 키워드 폴백.
    """
    t0 = time.perf_counter()

    # 프로필/이미지 정보를 프롬프트에 주입
    profile_block = _build_profile_block(user_profile)
    image_block = _build_image_block(has_images)
    system_prompt = _LLM_ROUTER_MEMBER_PROMPT.format(
        profile_block=profile_block,
        image_block=image_block,
    )

    # 사용자 메시지 구성
    history_text = _build_history_summary(chat_history, max_turns=4)  # 회원은 4턴
    user_payload = f"사용자 메시지: {user_text}"
    if history_text:
        user_payload = f"[이전 대화]\n{history_text}\n\n[현재 메시지]\n{user_text}"

    result = _call_llm_router(system_prompt, user_payload)
    if not result:
        print(f"[LLM_ROUTER] 회원 파싱 실패 → 폴백 ({time.perf_counter()-t0:.3f}s)", flush=True)
        return None

    intent = result.get("intent", "").strip()
    reason = result.get("reason", "LLM 분류")
    has_skin_context = result.get("has_skin_context", False)
    has_category = result.get("has_category", False)

    # 유효성 검증
    if intent not in _GUEST_ALLOWED_INTENTS:
        print(f"[LLM_ROUTER] 비로그인 허용되지 않은 intent '{intent}' → 폴백", flush=True)
        return None

    # ── 피부타입/고민만 알려주는 메시지 감지 ──────────────────
    # "나는 복합성이야", "지성이야", "여드름이 고민이야" 등
    # 이전 대화에서 역질문(피부타입 물어봄) 후 사용자가 답하는 패턴
    _SKIN_TYPE_DECLARE_KW = [
        "건성", "지성", "복합성", "민감성", "중성",
        "건조", "지성이야", "민감해", "복합이야",
    ]
    _CONCERN_DECLARE_KW = [
        "여드름", "홍조", "모공", "각질", "주름", "탄력",
        "색소", "기미", "잡티", "트러블", "뾰루지",
    ]
    text_lower = (user_text or "").strip().lower()
    is_type_declaration = (
        len(text_lower) < 20
        and has_skin_context
        and (_has_any(text_lower, _SKIN_TYPE_DECLARE_KW) or _has_any(text_lower, _CONCERN_DECLARE_KW))
    )

    if is_type_declaration and intent in ("product_recommend", "ask_for_category", "ask_for_context"):
        # 이전 대화 맥락을 확인해서 적절한 intent로 리다이렉트
        prev_intent = None
        if chat_history:
            for msg in reversed(chat_history[-6:]):
                content = (msg.get("content") or "").lower()
                if "루틴" in content:
                    prev_intent = "routine_advice"
                    break
                if any(kw in content for kw in ["추천", "제품", "크림", "세럼", "토너"]):
                    prev_intent = "product_recommend"
                    break
                if any(kw in content for kw in ["관리", "케어", "방법", "어떻게"]):
                    prev_intent = "general_advice"
                    break

        intent = prev_intent or "general_advice"
        reason = f"피부타입 선언 → 이전 맥락 기반 '{intent}'으로 전환"
        print(f"[LLM_ROUTER] 피부타입 선언 감지 → {intent}", flush=True)


    # 유효성 검증
    if intent not in _MEMBER_ALLOWED_INTENTS:
        print(f"[LLM_ROUTER] 회원 허용되지 않은 intent '{intent}' → 폴백", flush=True)
        return None

    # ── 분석 intent 후처리 ──────────────────────────────────
    # LLM이 분석 intent를 골랐지만 이미지가 없는 경우 → general_advice로 보정
    # (context_node 또는 llm_node에서 이미지 업로드 안내)
    _ANALYSIS_INTENTS = {"skin_analysis_fast", "skin_analysis_deep", "ingredient_analysis"}
    if intent in _ANALYSIS_INTENTS and not has_images:
        intent = "general_advice"
        reason = f"LLM: 분석 요청이지만 이미지 없음 → 이미지 업로드 안내"

    # history_compare인데 최근 분석 이력이 없으면 → general_advice
    if intent == "history_compare":
        has_history = bool(user_profile and user_profile.get("recent_analysis_summary"))
        if not has_history:
            intent = "general_advice"
            reason = "LLM: 분석 비교 요청이지만 이전 분석 이력 없음"

    # ── 제품 추천 맥락 보정 ──────────────────────────────────
    # DB 프로필에 피부 정보가 있으면 LLM 판단과 별개로 맥락 있음으로 처리
    profile_has_skin = bool(
        user_profile
        and (user_profile.get("skin_type_label") or user_profile.get("skin_concern"))
    )
    effective_skin_context = has_skin_context or profile_has_skin

    if intent == "product_recommend":
        if not effective_skin_context and not has_category:
            intent = "ask_for_context"
            reason = "LLM: 제품 추천이지만 프로필+메시지 모두 피부 맥락 없음"
        elif effective_skin_context and not has_category:
            intent = "ask_for_category"
            reason = "LLM: 제품 추천이지만 카테고리 미특정"

    if intent == "routine_and_product" and not effective_skin_context:
        intent = "ask_for_context"
        reason = "LLM: 루틴+제품이지만 피부 맥락 부족"

    # 플래그 매핑
    flags = _INTENT_FLAGS.get(intent, _INTENT_FLAGS["general_advice"])
    needs_ctx = flags["needs_context_check"] and not effective_skin_context

    elapsed = time.perf_counter() - t0
    print(
        f"[LLM_ROUTER] MEMBER intent={intent} | ctx={effective_skin_context} "
        f"| cat={has_category} | img={has_images} | {elapsed:.3f}s",
        flush=True,
    )

    return RouteDecision(
        intent=intent,
        needs_vision=flags["needs_vision"],
        needs_rag=flags["needs_rag"],
        needs_product=flags["needs_product"],
        needs_context_check=needs_ctx,
        reason=f"[LLM] {reason}",
    )


# 키워드 사전 (폴백용 기존 로직)

_SKIN_DOMAIN_KW = [
    "피부", "여드름", "홍조", "모공", "각질", "트러블", "색소", "기미", "잡티",
    "주름", "탄력", "노화", "건조", "지성", "민감", "복합", "건성", "중성",
    "루틴", "스킨케어", "세안", "클렌징", "토너", "에센스", "세럼", "크림",
    "선크림", "자외선", "화장품", "성분", "레티놀", "나이아신", "비타민c",
    "bha", "aha", "판테놀", "세라마이드", "히알루론산", "보습", "수분",
    "촉촉", "번들", "피지", "블랙헤드", "화이트헤드", "필링", "각질제거",
    "미백", "브라이트닝", "올리브영", "닥터지", "라로슈포제", "이니스프리",
    "아로마티카", "코스알엑스", "스킨1004", "셀퓨전씨",
    "붉은기", "붉어", "붉음", "빨개", "빨갛", "빨간",
    "칙칙", "어두운 피부", "다크서클", "눈가",
    "트러블", "뾰루지", "뭐가 남", "자국", "흉터",
    "민감해", "따끔", "가렵", "건조해", "당김", "당겨",
    "번들거려", "번들번들", "기름지", "피지",
    "탄력없", "처져", "늘어져",
    "피부야", "피부인데", "피부라서", "피부가",
    "올영", "올리영", "헬스앤뷰티",
    "뭐써야", "뭐발라", "뭐바르",
    "화장품", "스킨케어제품", "자외선차단제",
    "유분", "유수분", "피지", "유분기", "유분감",
    "각질", "모공", "블랙헤드", "화이트헤드",
    "속건조", "겉번들", "민감", "자극", "트러블",
    "건조함", "촉촉함", "탄력", "탄탄", "처짐",
    "칙칙", "어두운", "밝아지", "환해지", "미백",
    "자외선", "spf", "pa", "선케어", "자차",
    "스팟", "잡티", "기미", "주근깨", "색소",
    "붓기", "부어", "예민해", "따가워", "가려워",
    "올라와", "올라오", "뭐가 났", "뭐가 올라",
    "화장이 안", "화장이 뜨", "화장 들뜸",
    "메이크업", "파운데이션", "쿠션", "비비",
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

_PRODUCT_KW = [
    "추천", "어떤 제품", "뭐 써", "뭐 바르", "뭐 쓰면",
    "올리브영", "구매", "살까", "살만한", "살 수 있",
    "브랜드", "제품", "써볼만한",
    "잡아주", "완화해주", "도움되는", "좋은거",
    "뭐가 좋아", "뭐가 좋을", "어떤거", "어떤 거",
    "써봤어", "효과있는", "효과 있는",
    "받고싶어", "받고 싶어", "받고싶은데", "받고 싶은데",
    "알고싶어", "알고 싶어", "알려줘",
    "사고싶어", "사고 싶어", "골라줘", "골라 줘",
    "뭐가 괜찮아", "뭐가 괜찮", "뭐 괜찮", "뭐써", "뭐쓰",
    "뭐 좋아", "뭐 좋을", "뭐 발라", "뭐 바를",
    "어떤 거 써", "어떤 거 발라", "어디꺼", "어디 거",
    "하나만 추천", "몇 가지 추천", "좀 알려줘", "좀 추천",
    "뭐 살까", "뭐 구매", "살 게", "살게", "살 거",
    "써보고 싶", "사보고 싶", "사볼까", "써볼까",
    "좋다고 하던데", "유명한 거", "인기있는", "인기 있는",
    "많이 쓰는", "많이 써", "핫한", "요즘 핫",
    "잘 팔리는", "후기 좋은", "리뷰 좋은",
    "올영 추천", "올리영 추천", "올영에서",
    "도 추천해줘", "도 알려줘", "도 골라줘",
]

_ROUTINE_KW = [
    "루틴", "아침", "저녁", "순서", "사용법", "몇 번", "빈도",
    "단계", "레이어링", "겹쳐", "같이 써", "함께 쓰",
]

_PRODUCT_CATEGORY_KW = [
    "크림", "세럼", "로션", "토너", "스킨", "에센스", "선크림",
    "폼클렌징", "폼 클렌징", "클렌저", "클렌징", "세안",
    "마스크팩", "마스크", "앰플", "아이크림", "미스트",
    "필링", "패드", "오일", "수분크림", "보습크림",
    "비비크림", "bb크림", "쿠션", "젤크림",
]

_CATEGORY_NORMALIZE = {
    "폼클": "폼클렌징", "폼클린저": "폼클렌징", "폼클렌져": "폼클렌징",
    "폼클린징": "폼클렌징", "폼크렌징": "폼클렌징", "폼클랜징": "폼클렌징",
    "세안제": "폼클렌징", "클렌져": "클렌징", "클랜징": "클렌징",
    "수분": "수분크림", "수크림": "수분크림", "모이스처": "수분크림", "보습": "보습크림",
    "써럼": "세럼", "세럼크림": "세럼",
    "토닉": "토너", "스킨토너": "토너",
    "선스크린": "선크림", "썬크림": "선크림", "선블록": "선크림",
    "선케어": "선크림", "자외선차단": "선크림",
    "아이": "아이크림", "눈가크림": "아이크림",
    "비비": "bb크림", "비비크림": "bb크림",
    "마스크팩": "마스크팩", "팩": "마스크팩", "시트마스크": "마스크팩",
    "앰플": "앰플", "엠플": "앰플",
    "에센스": "에센스", "에쎈스": "에센스",
    "로숀": "로션", "밀크로션": "로션",
    "클렌징오일": "오일", "클랜징오일": "오일",
    "패드": "패드", "필링패드": "패드", "토닝패드": "패드",
    "선": "선크림", "bb": "bb크림", "미스트": "미스트", "스프레이": "미스트",
    "클랜저": "클렌저", "클렌져": "클렌저",
    "아이크림": "아이크림", "눈크림": "아이크림",
    "모이스처라이저": "수분크림", "나이트크림": "크림", "데이크림": "크림",
}


def _normalize_category(text: str) -> str:
    for abbr, full in _CATEGORY_NORMALIZE.items():
        if abbr in text:
            text = text.replace(abbr, full)
    return text


def _extract_category_from_history(chat_history: list | None) -> str:
    if not chat_history:
        return ""
    recent = chat_history[-4:]
    for msg in reversed(recent):
        role = msg.get("role", "")
        msg_text = (msg.get("content") or "").lower()
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

_ANALYSIS_REQUEST_KW = [
    "빠른 분석", "빠른분석", "피부 분석", "피부분석",
    "정밀 분석", "정밀분석", "정량 분석", "정량분석",
    "분석해줘", "분석해 줘", "분석 해줘", "분석해주세요",
    "사진 분석", "사진분석", "얼굴 분석", "얼굴분석",
    "내 피부 분석", "피부 좀 분석", "피부상태 분석",
]

_CONTEXT_KW = [
    "건성", "지성", "복합", "복합성", "민감", "민감성", "중성",
    "여드름", "홍조", "모공", "각질", "잡티", "기미", "주름",
    "트러블", "색소침착", "미백", "탄력", "보습", "수분부족",
    "번들", "피지", "건조",
    "건조한 편", "건조해요", "건조한데", "건조함",
    "기름진 편", "기름져요", "번들거려", "번들거리는",
    "예민한", "예민해요", "예민한 편", "자극에 약",
    "피지가 많", "피지 많", "유분이 많", "유분 많",
    "수분이 부족", "수분 부족", "촉촉하지 않",
    "당김", "당기는", "타이트한",
    "지성이야", "건성이야", "복합성이야", "민감성이야",
    "지성인데", "건성인데", "복합성인데", "민감성인데",
    "지성 피부", "건성 피부", "복합성 피부", "민감성 피부",
    "지성피부", "건성피부", "복합성피부", "민감성피부",
    "뾰루지", "피부 트러블", "얼굴에 뭐가", "뭐가 올라와",
    "블랙헤드", "화이트헤드", "모공이 크", "모공 넓",
    "기미가", "잡티가", "색소가", "피부톤이",
    "주름이", "탄력이 없", "탄력없어", "처져",
    "붉은기", "홍조가", "얼굴이 빨개",
]


def _has_any(text: str, keywords: list) -> bool:
    return any(kw in text for kw in keywords)


def _has_context(text: str, user_profile: dict | None, chat_history: list | None = None) -> bool:
    if user_profile and user_profile.get("skin_type_label"):
        return True
    if user_profile and user_profile.get("skin_concern"):
        return True
    if _has_any(text, _CONTEXT_KW):
        return True
    if chat_history:
        for msg in chat_history[-6:]:
            msg_text = (msg.get("content") or "").lower()
            if _has_any(msg_text, _CONTEXT_KW):
                return True
    return False



# 메인 분류 함수

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

    처리 순서:
    0. 프론트 분석 모드(analysis_type) → 무조건 우선
    1. LLM 라우팅 시도
       - 비로그인: _llm_decide_guest()
       - 로그인:   _llm_decide_member() (프로필+이미지 정보 포함)
    2. LLM 실패 시 → 기존 키워드 폴백
    """

    # ── 0. 프론트 분석 모드 명시 (최우선) ────────────────────
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
        return RouteDecision("ingredient_analysis", True, True, False, False, "성분 분석 모드")

    # ── 1. LLM 라우팅 시도 ──────────────────────────────────
    if user_id is None:
        # 비로그인
        llm_result = _llm_decide_guest(user_text, chat_history)
    else:
        # 로그인 회원
        llm_result = _llm_decide_member(
            user_text=user_text,
            has_images=has_images,
            user_profile=user_profile,
            chat_history=chat_history,
        )

    if llm_result is not None:
        return llm_result

    # ── 2. LLM 실패 → 키워드 폴백 ──────────────────────────
    print(f"[ROUTER] LLM 실패 → 키워드 폴백 (user_id={'guest' if user_id is None else user_id})", flush=True)


    # 키워드 기반 분류 (폴백)

    text = _normalize_category((user_text or "").lower().strip())
    has_history = bool(chat_history and len(chat_history) >= 2)

    # ── 인사/잡담 ────────────────────────────────────────────
    if _has_any(text, _GREETING_KW) and not _has_any(text, _SKIN_DOMAIN_KW):
        return RouteDecision("greeting", False, False, False, False, "인사/잡담")

    # ── 도메인 밖 차단 ───────────────────────────────────────
    _STRONG_OOD_KW = [
        "맛집", "레시피", "요리", "여행", "관광", "숙박", "호텔",
        "주식", "코인", "투자", "환율", "부동산",
        "영화", "드라마", "음악", "노래", "게임",
        "정치", "선거", "법률", "소송",
        "수학", "물리", "화학", "역사", "지리",
        "취업", "이력서", "자소서", "면접",
        "스포츠", "축구", "야구", "날씨",
    ]
    if _has_any(text, _STRONG_OOD_KW) and not _has_any(text, _SKIN_DOMAIN_KW):
        return RouteDecision("out_of_domain", False, False, False, False, "도메인 외 질문")

    # ── 피부 도메인 확인 ─────────────────────────────────────
    _PRODUCT_INTENT_KW = [
        "추천", "제품", "알려줘", "골라줘", "받고싶어", "사고싶어",
        "써보고 싶", "사보고 싶", "뭐써", "뭐쓰", "뭐 써", "뭐 발라",
        "좋은거", "인기있는", "핫한", "후기 좋은", "잘 팔리는",
        "올영", "올리영", "올리브영",
    ]
    has_product_domain = (
        _has_any(text, _PRODUCT_CATEGORY_KW) or
        _has_any(text, _PRODUCT_INTENT_KW)
    ) and not _has_any(text, _OUT_OF_DOMAIN_KW)

    is_skin = (
        _has_any(text, _SKIN_DOMAIN_KW) or
        len(text) < 15 or
        has_product_domain or
        not _has_any(text, _STRONG_OOD_KW)
    )

    _FOLLOWUP_KW = [
        "원해", "알려줘", "궁금해", "더 알려줘", "그럼", "그리고",
        "도 알려줘", "도 원해", "도 추천", "도 해줘",
        "이건", "저건", "그건", "이거", "저거", "그거",
        "어때", "어떤게", "뭐가", "좋을까", "될까",
        "어떻게 해", "어떻게 쓰",
        "그 제품", "그 크림", "그 세럼", "같은 거", "비슷한 거",
        "그리고 또", "그리고 혹시", "추가로", "하나 더",
        "아 그럼", "오 그럼", "그러면",
        "도 알고싶어", "도 궁금해", "도 받고싶어",
        "추천도", "선크림도", "세럼도", "크림도", "로션도",
        "폼클도", "토너도", "에센스도", "앰플도",
    ]
    if not is_skin and has_history and _has_any(text, _FOLLOWUP_KW):
        is_skin = True
        print("[ROUTER] 팔로우업 발화 감지 → 맥락 이어받기", flush=True)

    if not is_skin:
        return RouteDecision("out_of_domain", False, False, False, False, "피부 도메인 키워드 없음")

    if _has_any(text, _STRONG_OOD_KW) and not _has_any(text, _SKIN_DOMAIN_KW) and not has_product_domain:
        return RouteDecision("out_of_domain", False, False, False, False, "비피부 도메인 확인")

    # ── 텍스트 분석 요청 ─────────────────────────────────────
    if _has_any(text, _ANALYSIS_REQUEST_KW):
        if not user_id:
            return RouteDecision("login_required", False, False, False, False, "비회원 분석 요청(텍스트)")
        return RouteDecision("general_advice", False, True, False, False, "분석 요청 → 이미지 업로드 안내")

    # ── 의료 질문 ────────────────────────────────────────────
    if _has_any(text, _MEDICAL_KW):
        return RouteDecision("medical_advice", False, True, False, False, "의료 관련 질문")

    # ── 이전 분석 비교 ───────────────────────────────────────
    if _has_any(text, _HISTORY_KW) and user_id:
        return RouteDecision("history_compare", False, True, False, False, "분석 이력 비교")

    # ── 루틴 + 제품 ──────────────────────────────────────────
    _NON_PRODUCT_RECOMMEND_KW = [
        "음식", "식품", "영양", "먹", "식단", "채소", "과일", "비타민",
        "생활", "습관", "운동", "수면", "물", "수분섭취",
        "이유", "원인", "왜", "어떻게", "설명",
    ]
    if _has_any(text, _NON_PRODUCT_RECOMMEND_KW):
        return RouteDecision("general_advice", False, True, False, False, "음식/생활 관련 일반 상담")

    has_routine        = _has_any(text, _ROUTINE_KW)
    has_category       = _has_any(text, _PRODUCT_CATEGORY_KW)
    has_explicit       = _has_any(text, [
        "올리브영", "구매", "살까", "살만한", "어떤 제품",
        "뭐 써", "뭐 바르", "뭐 쓰면", "써볼만한",
        "올영", "올리영", "살게", "살 게", "사볼게",
        "인기있는", "인기 있는", "잘 팔리는", "후기 좋은",
    ])
    has_vague          = _has_any(text, [
        "제품", "추천", "좋은거", "뭐가 좋아", "뭐가 좋을",
        "어떤거", "어떤 거", "잡아주", "완화해주", "효과있는", "효과 있는",
        "알려줘", "도 알려줘", "도 추천", "뭐써", "뭐쓰",
        "받고싶어", "받고 싶어", "받고싶은데", "알고싶어", "골라줘",
        "뭐가 괜찮", "뭐 괜찮", "뭐 좋아", "뭐 좋을",
        "뭐 발라", "뭐 바를", "어디꺼", "하나만 추천",
        "좀 알려줘", "좀 추천", "유명한 거", "인기있는",
        "많이 쓰는", "핫한", "잘 팔리는", "후기 좋은",
        "도 받고싶어", "도 알고싶어",
        "도 추천해줘", "도 알려줘", "도 골라줘",
        "추천도", "선크림도", "세럼도", "크림도", "로션도",
        "폼클도", "토너도", "에센스도", "앰플도",
        "사보고 싶", "써보고 싶", "사볼까", "써볼까",
    ])
    has_product_intent = has_category or has_explicit

    if has_routine:
        if has_product_intent:
            ctx_ok = _has_context(text, user_profile, chat_history) or has_history
            return RouteDecision(
                "routine_and_product", False, True, True,
                not ctx_ok, "루틴 + 제품 복합 요청"
            )
        return RouteDecision("routine_advice", False, True, False, False, "루틴 관련 질문")

    if has_product_intent:
        ctx_ok = _has_context(text, user_profile, chat_history) or has_history
        return RouteDecision(
            "product_recommend", False, False, True,
            not ctx_ok, "제품 추천 요청"
        )

    if has_vague:
        history_category = _extract_category_from_history(chat_history)
        if history_category:
            print(f"[ROUTER] 이전 카테고리 이어받기: '{history_category}'", flush=True)
            ctx_ok = _has_context(text, user_profile, chat_history) or has_history
            return RouteDecision(
                "product_recommend", False, False, True,
                not ctx_ok, f"맥락 이어받기 → {history_category} 제품 추천"
            )
        return RouteDecision(
            "ask_for_category", False, False, False, False, "카테고리 미특정 → 역질문"
        )

    # ── 성분 질문 ────────────────────────────────────────────
    if _has_any(text, _INGREDIENT_QUESTION_KW):
        return RouteDecision("ingredient_question", False, True, False, False, "성분 관련 질문")

    # ── 기본: 일반 상담 ──────────────────────────────────────
    return RouteDecision("general_advice", False, True, False, False, "일반 피부 상담")
