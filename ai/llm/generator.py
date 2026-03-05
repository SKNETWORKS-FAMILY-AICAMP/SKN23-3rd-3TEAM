"""
generator.py
intent에 맞는 프롬프트를 선택하고 OpenAI를 호출합니다.
"""
import json
import re
from openai import OpenAI

from ai.config.settings import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
from ai.llm.prompts.skin_analysis import FAST_ANALYSIS_PROMPT, DEEP_ANALYSIS_PROMPT
from ai.llm.prompts import (
    BASE_SYSTEM,
    GENERAL_CHAT_PROMPT,
    PRODUCT_RECOMMEND_PROMPT,
    INGREDIENT_CHAT_PROMPT,
    ROUTINE_AND_PRODUCT_PROMPT,
)

client = OpenAI(api_key=OPENAI_API_KEY)

# 피부 분석 intent - LLM 프롬프트에서 skin_type/concern 제거 대상
_ANALYSIS_INTENTS = {"skin_analysis_fast", "skin_analysis_deep"}

# ── intent → 프롬프트 매핑 ────────────────────────────────────
_PROMPT_MAP = {
    "general_advice":        GENERAL_CHAT_PROMPT,
    "routine_advice":        GENERAL_CHAT_PROMPT,
    "medical_advice":        GENERAL_CHAT_PROMPT,
    "ingredient_question":   GENERAL_CHAT_PROMPT,
    "skin_analysis_fast":    FAST_ANALYSIS_PROMPT,
    "skin_analysis_deep":    DEEP_ANALYSIS_PROMPT,
    "product_recommend":     PRODUCT_RECOMMEND_PROMPT,
    "routine_and_product":   ROUTINE_AND_PRODUCT_PROMPT,
    "ingredient_analysis":   INGREDIENT_CHAT_PROMPT,
    "history_compare":       DEEP_ANALYSIS_PROMPT,
}


def _safe_json_loads(text: str) -> dict:
    """LLM 응답에서 JSON만 안전하게 파싱합니다."""
    if not text:
        raise ValueError("Empty LLM response")

    # 코드펜스 제거
    text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text.strip())

    # { } 범위만 추출
    if not text.lstrip().startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

    return json.loads(text)


def _build_user_profile_text(user_profile: dict | None) -> str:
    """user_profile dict → 프롬프트용 텍스트 변환"""
    if not user_profile:
        return "비회원 (프로필 없음) — 대화에서 수집된 임시 정보만 활용"

    parts = []
    if user_profile.get("skin_type_label"):
        parts.append(f"피부타입: {user_profile['skin_type_label']}")
    if user_profile.get("skin_concern"):
        parts.append(f"피부고민: {user_profile['skin_concern']}")
    if user_profile.get("age"):
        parts.append(f"나이: {user_profile['age']}세")
    if user_profile.get("gender"):
        g = "여성" if user_profile["gender"] == "female" else "남성"
        parts.append(f"성별: {g}")
    if user_profile.get("recent_analysis_summary"):
        parts.append(f"최근 분석 요약: {user_profile['recent_analysis_summary']}")

    return "\n".join(parts) if parts else "프로필 정보 없음"




def _build_analysis_profile_text(user_profile: dict | None) -> str:
    """
    분석 intent용 프로필 텍스트 - skin_type/skin_concern 제외.
    모델 수치가 유일한 판단 근거가 되도록 피부 타입 정보를 차단합니다.
    """
    if not user_profile:
        return "프로필 없음"

    parts = []
    if user_profile.get("age"):
        parts.append(f"나이: {user_profile['age']}세")
    if user_profile.get("gender"):
        g = "여성" if user_profile["gender"] == "female" else "남성"
        parts.append(f"성별: {g}")

    return "\n".join(parts) if parts else "나이/성별 정보 없음"

def _build_history_summary(user_profile: dict | None) -> str:
    """이전 분석 이력 요약 텍스트"""
    if not user_profile:
        return "이전 분석 없음"
    return user_profile.get("recent_analysis_summary") or "이전 분석 없음"


def _trim_passages(passages: list, max_len: int = 300) -> list:
    """RAG passage snippet을 max_len자로 잘라 토큰 절약"""
    result = []
    for p in passages:
        tp = dict(p)
        if tp.get("snippet") and len(tp["snippet"]) > max_len:
            tp["snippet"] = tp["snippet"][:max_len] + "…"
        result.append(tp)
    return result


def generate_report(
    intent: str,
    user_text: str,
    user_profile: dict | None,
    vision_result: dict | None,
    rag_passages: list,
    web_passages: list,
    chat_history: list,
    ingredients: list | None = None,
    analysis_mode: str = "",
    verified_products: list | None = None,  # 올리브영 검증 완료 제품 (pipeline에서 전달)
) -> dict:
    """
    intent에 맞는 프롬프트를 선택하고 OpenAI를 호출합니다.

    verified_products: 올리브영 게이트를 통과한 제품 목록.
                       None이면 LLM이 RAG 기반으로 자유롭게 추천.
                       리스트면 이 제품들만 추천하도록 프롬프트에 주입.
    Returns:
        dict: LLM이 반환한 JSON (FinalReport 구조)
    """
    # 프롬프트 선택
    task_prompt_template = _PROMPT_MAP.get(intent, GENERAL_CHAT_PROMPT)

    # 프로필 텍스트 변환 (분석 intent일 때 skin_type/concern 제거)
    if intent in _ANALYSIS_INTENTS:
        user_profile_text = _build_analysis_profile_text(user_profile)
    else:
        user_profile_text = _build_user_profile_text(user_profile)
    history_summary = _build_history_summary(user_profile)
    analysis_mode_text = (
        "빠른 분석 (이미지 1장)" if analysis_mode == "fast"
        else "정밀 분석 (이미지 최대 3장)" if analysis_mode == "deep"
        else ""
    )

    # 프롬프트 변수 치환
    import json as _json
    task_prompt = task_prompt_template.format(
        user_profile_text=user_profile_text,
        analysis_mode=analysis_mode_text,
        history_summary=history_summary,
        ingredients_text=", ".join(ingredients) if ingredients else "없음",
        vision_result=_json.dumps(vision_result, ensure_ascii=False) if vision_result else "없음",
    )

    # 히스토리 최근 N턴만
    # 분석 intent는 수치 기반 판단 → chat_history 불필요 → 토큰 절약
    from ai.config.settings import CHAT_HISTORY_TURNS
    _ANALYSIS_INTENTS_NO_HISTORY = {"skin_analysis_fast", "skin_analysis_deep", "ingredient_analysis"}
    if intent in _ANALYSIS_INTENTS_NO_HISTORY:
        recent_history = []
    else:
        recent_history = (chat_history or [])[-CHAT_HISTORY_TURNS * 2:]

    # RAG/웹 passage snippet 트리밍 (토큰 절약)
    rag_passages = _trim_passages(rag_passages, max_len=300)
    web_passages = _trim_passages(web_passages, max_len=200)

    # LLM에 넘길 user payload
    payload = {
        "task_instruction": task_prompt,
        "chat_history": recent_history,
        "user_text": user_text,
        "vision_result": vision_result,
        "rag_passages": rag_passages,
        "web_passages": web_passages,
        "intent": intent,
    }

    # 올리브영 검증 완료 제품이 있으면 명시적으로 전달
    # LLM은 이 제품들 중에서만 추천해야 함
    if verified_products is not None:
        if verified_products:
            payload["verified_oliveyoung_products"] = verified_products
            payload["task_instruction"] += (
                "\n\n[중요] 아래 verified_oliveyoung_products 목록에 있는 제품만 추천할 것. "
                "목록에 없는 제품은 절대 추천하지 않는다. "
                f"검증된 제품 {len(verified_products)}개: "
                + ", ".join(p.get("name","") for p in verified_products)
            )
        else:
            payload["verified_oliveyoung_products"] = []
            payload["task_instruction"] += (
                "\n\n[중요] 올리브영에서 재고가 확인된 제품이 없다. "
                "제품 추천 대신 피부타입/고민에 맞는 성분 키워드와 루틴 조언만 제공할 것. "
                "products 필드는 반드시 빈 리스트로 반환할 것."
            )

    # 제품 추천 intent일 때 LLM이 링크를 직접 생성하지 않도록 금지
    # pipeline이 올리브영 링크 섹션을 단독으로 추가하므로 중복 방지
    if verified_products is not None:
        payload["task_instruction"] += (
            "\n\n[중요] chat_answer에 URL, 링크, 구매 링크 텍스트를 절대 포함하지 말 것. "
            "구매 링크는 시스템이 자동으로 추가한다."
        )

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": BASE_SYSTEM},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=OPENAI_TEMPERATURE,
        response_format={"type": "json_object"},
    )

    text = resp.choices[0].message.content
    return _safe_json_loads(text)
