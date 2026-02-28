from dotenv import load_dotenv
import os, json, re
from openai import OpenAI

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("openai_key", "")
assert os.environ["OPENAI_API_KEY"], "OPENAI_API_KEY가 비어있음 (.env의 openai_key 확인)"

client = OpenAI()

SYSTEM = """
너는 멀티모달 기반 피부 분석 및 추천 챗봇 엔진이다.

────────────────────
[권한 분기 규칙]

1. 비회원:
- 정량분석(이미지 기반 분석) 기능 사용 불가.
- 질문 시 피부타입/피부고민을 역질문으로 수집한다.
- 임시 프로필 기반으로 RAG 답변 생성.
- 이미지 분석 요청 시 회원 전용 기능임을 안내.

2. 회원:
- 저장된 프로필(피부타입, 피부고민)을 개인화 기본 키로 사용.
- 정량분석 결과가 있으면 반드시 반영.
- 이전 분석 이력이 있으면 변화 코멘트 포함.

────────────────────
[엔진 동작 원칙]

- Intent를 먼저 분류한다:
  (관리/주의사항, 제품추천, 제품분석, 정량분석해석, 기타)

- 모든 답변은 기본적으로 Vector DB 근거 기반(RAG 우선).
- 근거 부족 시에만 불확실성 명시.
- 내부 식별자(source_id, doc_id 등) 절대 노출 금지.
- 확정 진단/치료 처방 금지. 가능성/권고 수준으로 작성.
- 특정 제품 추천은 올리브영 존재 여부 게이트 통과 제품만 노출.

────────────────────
[정량분석 처리 규칙]

- vision 모델 결과(JSON 지표/관찰/qc 등)를 요약한다.
- 프로필(타입/고민)과 결합하여 해석한다.
- 액션 플랜(루틴/성분 키워드/주의사항)을 제안한다.
- 빠른검사(1장) / 정밀검사(최대3장) 구분 명시.

────────────────────
[제품 추천 규칙]

1. Vector DB에서 후보 + 근거 확보
2. 올리브영 존재 여부 확인
3. 존재하는 제품만 최종 노출
4. 추천 이유 + 성분 포인트 + 주의사항 포함

────────────────────
[출력 형식]

- 모든 답변은 Intent별 템플릿을 따른다.
- 구조화된 섹션 헤더 + 번호/불릿 사용.
- 개인화 정보(피부타입/고민)를 헤더에 명시.
- 조건부로 주의/레드플래그 섹션 포함.
- 반드시 JSON 객체만 반환.
- 마크다운, 코드블록, 설명 문장 추가 금지.
"""

def _safe_json_loads(text: str) -> dict:
    """
    LLM이 가끔 ```json ...``` 또는 앞뒤 설명을 섞는 경우가 있어 방어적으로 파싱.
    """
    if not text:
        raise ValueError("Empty LLM response")

    # 1) 코드펜스 제거
    text2 = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text2 = re.sub(r"\s*```$", "", text2.strip())

    # 2) 그래도 JSON이 아니면 첫 { ~ 마지막 } 범위만 추출 시도
    if not text2.lstrip().startswith("{"):
        start = text2.find("{")
        end = text2.rfind("}")
        if start != -1 and end != -1 and end > start:
            text2 = text2[start:end+1]

    return json.loads(text2)

def generate_report(evidence: dict) -> dict:
    user_text = evidence.get("user_text", "")
    vision = evidence.get("vision_result")
    passages = evidence.get("rag_passages", [])
    web_passages = evidence.get("web_passages", [])   # ✅ 추가260227 정석원
    history = (evidence.get("chat_history", []) or [])[-8:]

    # ✅ 스키마 힌트(LLM이 "모양"을 깨지 않게 가이드)
    schema_hint = {
        # "chat_answer": "string (3~6 sentences, no repetition, no internal ids)",
        "chat_answer": "string (Markdown formatted, includes bold summary line, section headers using ###, bullet points, no internal ids)",
        "summary": "string (1~2 sentences)",
        "observations": [{"title": "string", "detail": "string", "confidence": "0~1 float"}],
        "recommendations": [{"category": "AM|PM|Lifestyle|Ingredients|Products", "items": ["string"]}],
        "products": [
            {
                "brand": "string",
                "name": "string",
                "why": "string (1~2 sentences, grounded)",
                "url":"string (optional, must be web_passages.meta.url if source is web)",  # 260227 정석원
                "how_to_use": "string (optional)",
                "evidence_source_id": "string (must match rag_passages.source_id)"
            }
        ],
        "warnings": ["string"],
        "red_flags": ["string"],
        "citations": [{"source_id": "string", "snippet": "string"}]
    }

    # ✅ 요구사항(짧은 챗봇 답변 / 중복 금지 / 내부ID 노출 금지)
    requirements = [
        "중복 문장 금지, 동일 내용 반복 금지",
        "chat_answer에는 문서ID/소스ID/source_id/doc_id 등 내부 식별자 노출 금지",

        "chat_answer는 Markdown 형식으로 작성한다.",
        "첫 줄은 굵은 한 줄 요약으로 시작한다.",
        "섹션 제목은 ### 사용",
        "리스트는 - 또는 1. 사용",
        "문단 사이에는 한 줄 공백 포함"

        # ✅ 제품 추천 정책(핵심) 260227 정석원
        "사용자가 특정 브랜드/제품 추천을 요청한 경우, rag_passages 또는 web_passages에 '제품명' 근거가 있을 때만 products에 최대 1~5개 추천을 포함",
        "rag_passages와 web_passages 모두에 제품명이 없으면 products는 빈 리스트로 두고, warnings에 '근거 부족으로 제품명 특정 불가'를 포함",
        "제품명을 새로 만들어내거나(환각) 추측하여 기입 금지",

        # ✅ 안전/표현
        "확정 진단/치료 처방 금지. '도움이 될 수 있음/개인차'로 표현",
        "근거(rag_passages, vision_result)가 부족하면 단정하지 말고 warnings에 '근거 부족'을 포함",

        # ✅ 인용 규칙 수정 260227 정석원
        "citations는 rag_passages 또는 web_passages의 source_id/snippet만 사용",
        "web_passages를 인용할 경우 meta.url/meta.title을 활용해 사용자에게 출처를 명확히 제시",
        "products의 evidence_source_id는 반드시 citations에 존재하는 source_id 중 하나와 일치해야 함",
        "recommendations.category는 반드시 AM, PM, Lifestyle, Ingredients, Products 중 하나만 사용",
        "How to Use 같은 새 카테고리를 만들지 말고 items 안에 넣기",
        "사용자가 '구글/검색/링크'를 요청하면 web_passages만 근거로 답하고, rag_passages는 사용하지 말 것",
        "제품을 추천할 때는 products에 반드시 url을 포함(가능할 때), url은 web_passages.meta.url에서만 가져올 것",
    ]

    prompt = {
        "task": "Generate a skincare response JSON for a chat UI.",
        "chat_history": history,
        "user_text": user_text,
        "vision_result": vision,
        "rag_passages": passages,
        "web_passages": web_passages,   # ✅ 추가
        "requirements": requirements,
        "output_schema_hint": schema_hint
    }

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
        ],
        temperature=0.3,
        response_format={"type": "json_object"},    # 추가
    )

    text = resp.choices[0].message.content
    return _safe_json_loads(text)