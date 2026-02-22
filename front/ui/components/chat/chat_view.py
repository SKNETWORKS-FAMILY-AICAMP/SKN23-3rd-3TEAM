import streamlit as st

def render_messages(messages: list[dict]):
    for m in messages:
        if m["role"] == "system":
            continue
        with st.chat_message(m["role"]):
            st.markdown(m["content"])