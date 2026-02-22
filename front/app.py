import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from ai.orchestrator.pipeline import run

    
# 반드시 최상단 Streamlit 호출
st.set_page_config(page_title="Skin Demo", layout="wide")

# session init
if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "last_images_bytes" not in st.session_state:
    st.session_state["last_images_bytes"] = []

st.title("피부 리포트 챗봇 (로컬 데모)")

with st.sidebar:
    st.caption(f"CHROMA_DB_PATH = {os.environ.get('CHROMA_DB_PATH', './vector_store')}")
    st.caption(f"CHROMA_COLLECTION = {os.environ.get('CHROMA_COLLECTION')}")
    st.caption(f"EMBED_MODEL_NAME = {os.environ.get('EMBED_MODEL_NAME')}")
    st.divider()

uploaded = st.file_uploader(
    "피부 사진 업로드(선택)",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)
if uploaded:
    st.session_state["last_images_bytes"] = [f.read() for f in uploaded]

images_bytes = st.session_state["last_images_bytes"]

# chat history render
for m in st.session_state["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# chat input
user_input = st.chat_input("질문을 입력하세요 (예: 홍조가 심한데 루틴 추천해줘)")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})

    # 파이프라인에는 '복사본 + 최소 필드'만 전달 (세션 오염 방지)
    safe_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

    with st.spinner("분석 중..."):
        report = run(
            user_text=user_input,
            images=images_bytes,
            chat_history=safe_history,
        )

    answer = report.get("chat_answer") or report.get("summary") or "답변을 생성했습니다."
    st.session_state["messages"].append({"role": "assistant", "content": answer, "report": report})

    st.rerun()