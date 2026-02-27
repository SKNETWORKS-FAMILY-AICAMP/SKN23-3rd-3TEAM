from typing import Dict, Any, List

def build(user_text, vision_result, rag_passages, web_passages=None, chat_history=None):
    return {
        "user_text": user_text,
        "vision_result": vision_result,
        "rag_passages": rag_passages or [],
        "web_passages":web_passages or [], # ✅ 추가260227
        "chat_history": chat_history or [],
    }