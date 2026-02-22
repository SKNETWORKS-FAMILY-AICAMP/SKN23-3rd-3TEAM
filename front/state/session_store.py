import uuid
from typing import Dict, List
import streamlit as st
from state import session_keys as K


def _ensure_defaults():
    if K.THREADS not in st.session_state:
        st.session_state[K.THREADS] = []

    if K.THREAD_MESSAGES not in st.session_state:
        st.session_state[K.THREAD_MESSAGES] = {}

    if K.ACTIVE_THREAD_ID not in st.session_state:
        st.session_state[K.ACTIVE_THREAD_ID] = None

    if K.IS_LOGGED_IN not in st.session_state:
        st.session_state[K.IS_LOGGED_IN] = False

    if K.CURRENT_USER not in st.session_state:
        st.session_state[K.CURRENT_USER] = None


def create_thread(title: str = "새 대화") -> str:
    _ensure_defaults()
    thread_id = str(uuid.uuid4())[:8]
    # 일단 데모만 넣어둠 - 추후 수정 예정
    st.session_state[K.THREADS].insert(0, {"id": thread_id, "title": title})
    st.session_state[K.THREAD_MESSAGES][thread_id] = [
        {"role": "system", "content": "너는 피부 분석을 도와주는 친절한 상담 챗봇이야. 질문에 명확하고 실용적으로 답해."}
    ]
    st.session_state[K.ACTIVE_THREAD_ID] = thread_id
    return thread_id


def list_threads():
    _ensure_defaults()
    return st.session_state[K.THREADS]


def get_active_thread_id() -> str | None:
    _ensure_defaults()
    return st.session_state[K.ACTIVE_THREAD_ID]


def set_active_thread(thread_id: str):
    _ensure_defaults()
    st.session_state[K.ACTIVE_THREAD_ID] = thread_id


def get_messages(thread_id: str) -> List[Dict]:
    _ensure_defaults()
    return st.session_state[K.THREAD_MESSAGES].get(thread_id, [])


def append_message(thread_id: str, role: str, content: str):
    _ensure_defaults()
    st.session_state[K.THREAD_MESSAGES].setdefault(thread_id, [])
    st.session_state[K.THREAD_MESSAGES][thread_id].append({"role": role, "content": content})


def rename_thread_if_default(thread_id: str, user_first_text: str):
    """
    첫 질문이 들어오면 제목을 자동으로 '첫 질문 일부'로 바꿈
    """
    _ensure_defaults()
    threads = st.session_state[K.THREADS]
    for t in threads:
        if t["id"] == thread_id and (t["title"] == "새 대화" or t["title"].startswith("새 대화")):
            t["title"] = (user_first_text.strip()[:20] + ("…" if len(user_first_text.strip()) > 20 else ""))
            break