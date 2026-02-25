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
if "last_images_meta" not in st.session_state:
    st.session_state["last_images_meta"] = []  # 파일명/크기 등 디버그용

st.title("피부 리포트 챗봇 (로컬 데모)")

with st.sidebar:
    st.caption(f"CHROMA_DB_PATH = {os.environ.get('CHROMA_DB_PATH', './vector_store')}")
    st.caption(f"CHROMA_COLLECTION = {os.environ.get('CHROMA_COLLECTION')}")
    st.caption(f"EMBED_MODEL_NAME = {os.environ.get('EMBED_MODEL_NAME')}")
    st.divider()

    # ✅ 업로드 상태 디버그 표시
    n_imgs = len(st.session_state["last_images_bytes"])
    total_bytes = sum(len(b) for b in st.session_state["last_images_bytes"]) if n_imgs else 0
    st.caption(f"현재 저장된 이미지: {n_imgs}장 / 총 {total_bytes/1024:.1f} KB")

    if st.button("업로드 이미지 초기화"):
        st.session_state["last_images_bytes"] = []
        st.session_state["last_images_meta"] = []
        st.rerun()

uploaded = st.file_uploader(
    "피부 사진 업로드(선택)",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

# ✅ 업로드되면 즉시 bytes로 저장 + 메타도 저장
if uploaded:
    st.session_state["last_images_bytes"] = [f.getvalue() for f in uploaded]  # ✅ read() 대신 getvalue() 권장
    st.session_state["last_images_meta"] = [
        {"name": f.name, "size": f.size, "type": f.type} for f in uploaded
    ]

# ✅ 미리보기(정말로 업로드가 된 건지 눈으로 확인)
if st.session_state["last_images_bytes"]:
    st.subheader("업로드 이미지 미리보기")
    cols = st.columns(min(3, len(st.session_state["last_images_bytes"])))
    for i, b in enumerate(st.session_state["last_images_bytes"][:3]):
        with cols[i]:
            st.image(b, caption=st.session_state["last_images_meta"][i]["name"], use_container_width=True)

images_bytes = st.session_state["last_images_bytes"]

# chat history render
for m in st.session_state["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# chat input
user_input = st.chat_input("질문을 입력하세요 (예: 홍조가 심한데 루틴 추천해줘)")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})

    safe_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

    # ✅ run 호출 직전 디버그: 지금 몇 장 전달되는지 확인
    st.sidebar.caption(f"이번 요청 images 전달: {len(images_bytes)}장")

    with st.spinner("분석 중..."):
        report = run(
            user_text=user_input,
            images=images_bytes,
            chat_history=safe_history,
        )

    # ✅ assistant 답변 표시
    answer = report.get("chat_answer") or report.get("summary") or "답변을 생성했습니다."
    st.session_state["messages"].append({"role": "assistant", "content": answer, "report": report})

    # ✅ 디버그: meta/run_dir, qc 상태, face_box를 sidebar에 표시
    try:
        tool_vision = report.get("vision_result") or report.get("_debug", {}).get("vision_result")
    except Exception:
        tool_vision = None

    st.rerun()