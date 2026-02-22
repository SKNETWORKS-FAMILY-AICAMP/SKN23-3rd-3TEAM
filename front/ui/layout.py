import streamlit as st
from ui.components.chat.thread_list import render_thread_list

def inject_global_css():
    try:
        with open("ui/theme/styles.css", "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def render_sidebar():
    with st.sidebar:
        render_thread_list()
        st.divider()
        st.caption("로그인/DB 저장은 추후 Auth/DB 모듈로 연결")