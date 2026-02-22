import streamlit as st

def read_user_input(placeholder: str = "피부 고민을 입력해줘 (예: 건조함/홍조/트러블 등)"):
    return st.chat_input(placeholder)