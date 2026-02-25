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

[중요 가드레일]
- vision_result가 없거나, vision_result.findings가 비어있거나, vision_result.qc.status가 'fail'이면:
  1) 피부 상태를 추정/단정/서술하지 말 것
  2) chat_answer에는 '얼굴 정면이 선명한 사진' 재업로드 안내만 할 것
  3) observations/recommendations는 최소화하고 warnings에 '이미지 분석 불가'를 포함할 것
"""

def _safe_json_loads(text: str) -> dict:
    if not text:
        raise ValueError("Empty LLM response")

    text2 = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text2 = re.sub(r"\s*```$", "", text2.strip())

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
    history = (evidence.get("chat_history", []) or [])[-8:]

    schema_hint = {
        "chat_answer": "string (3~6 sentences, no repetition, no internal ids)",
        "summary": "string (1~2 sentences)",
        "observations": [{"title": "string", "detail": "string", "confidence": "0~1 float"}],
        "recommendations": [{"category": "AM|PM|Lifestyle|Ingredients", "items": ["string"]}],
        "warnings": ["string"],
        "red_flags": ["string"],
        "citations": [{"source_id": "string", "snippet": "string"}]
    }

    requirements = [
        "chat_answer는 3~6문장으로 짧게 작성",
        "중복 문장 금지, 동일 내용 반복 금지",
        "chat_answer에는 문서ID/소스ID/source_id/doc_id 등 내부 식별자 노출 금지",
        "특정 제품명/브랜드 직접 추천은 피하고 성분/제형/선택 기준으로만 안내",
        "근거(rag_passages, vision_result)가 부족하면 단정하지 말고 warnings에 '근거 부족'을 포함",
        "citations는 rag_passages에서 제공된 source_id/snippet만 사용(새로 만들어내지 말 것)",

        # ✅ 여기 추가 (핵심)
        "vision_result가 없거나 findings가 비어있거나 qc.status가 fail이면 피부 상태를 추정하지 말 것",
        "위 조건이면 chat_answer는 '얼굴 정면이 선명한 사진 재업로드' 안내로만 구성하고 warnings에 '이미지 분석 불가' 포함",
    ]

    # ✅ 비전 유효성 플래그를 prompt에 명시(LLM이 판단 쉽게)
    vision_ok = False
    if isinstance(vision, dict):
        qc_ok = (vision.get("qc", {}) or {}).get("status") != "fail"
        findings_ok = bool(vision.get("findings"))
        vision_ok = qc_ok and findings_ok

    prompt = {
        "task": "Generate a skincare response JSON for a chat UI.",
        "chat_history": history,
        "user_text": user_text,
        "vision_result": vision,
        "vision_ok": vision_ok,  # ✅ LLM이 헷갈리지 않게
        "rag_passages": passages,
        "requirements": requirements,
        "output_schema_hint": schema_hint,
    }

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
        ],
        temperature=0.3,
    )

    text = resp.choices[0].message.content
    return _safe_json_loads(text)   