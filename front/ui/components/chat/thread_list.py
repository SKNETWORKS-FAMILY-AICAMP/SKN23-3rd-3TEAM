import streamlit as st
from state import session_store as store


def render_thread_list():
    st.subheader("채팅 내역")

    if st.button("새 대화", use_container_width=True, type="primary"):
        store.create_thread("새 대화")
        st.rerun()

    threads = store.list_threads()
    active = store.get_active_thread_id()

    if not threads:
        st.caption("아직 대화가 없어요. 새 대화를 시작해봐!")
        return

    for t in threads:
        label = t["title"]
        is_active = (t["id"] == active)
        if st.button(("💬 "if is_active else "💬 ") + label, use_container_width=True):
            store.set_active_thread(t["id"])
            st.rerun()