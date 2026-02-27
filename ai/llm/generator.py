from dotenv import load_dotenv
import os, json, re
from openai import OpenAI

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("openai_key", "")
assert os.environ["OPENAI_API_KEY"], "OPENAI_API_KEY가 비어있음 (.env의 openai_key 확인)"

client = OpenAI()

SYSTEM = """너는 피부 리포트 챗봇이다.
- 확정 진단/치료 처방 금지. 가능성과 권고로 말한다.
- 내부 식별자(source_id, doc_id 등)는 사용자에게 노출하지 않는다.
- 출력은 반드시 JSON만 반환한다. (추가 텍스트/마크다운/코드블록 금지)
- 제품/브랜드 추천 규칙:
  - rag_passages 또는 web_passages 또는 제품DB 근거에 제품명 있을 때만
  - 근거에 제품명이 없으면 제품명을 임의로 생성/추측하지 말고, '근거 부족'을 warnings에 포함하고 성분/선택 기준 중심으로 안내한다.
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
        "chat_answer": "string (3~6 sentences, no repetition, no internal ids)",
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
        "chat_answer는 3~6문장으로 짧게 작성",
        "중복 문장 금지, 동일 내용 반복 금지",
        "chat_answer에는 문서ID/소스ID/source_id/doc_id 등 내부 식별자 노출 금지",

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