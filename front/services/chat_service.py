import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 .env에 없습니다.")
    return OpenAI(api_key=api_key)

def _model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def ask_gpt(messages: list[dict]) -> str:
    """
    messages = [{"role":"system|user|assistant","content":"..."}]
    """
    resp = _client().chat.completions.create(
        model=_model(),
        messages=messages,
        temperature=0.6,
    )
    return resp.choices[0].message.content