from typing import Dict, Any, List

def build(user_text, vision_result, rag_passages, chat_history=None):
    return {
        "user_text": user_text,
        "vision_result": vision_result,
        "rag_passages": rag_passages or [],
        "chat_history": chat_history or [],
    }