# app.py

import streamlit as st
import os
from dotenv import load_dotenv
from src.agent_logic import CodeReviewAgent

load_dotenv()

st.set_page_config(page_title="Java Agent", page_icon="☕", layout="wide")
st.title("☕ Java 17+ Code Reviewer")

with st.sidebar:
    st.header("⚙️ Controls")
    repo_path = st.text_input("Repo Path", value="/Users/yourname/ideaProjects/my-app")
    provider = st.selectbox("Model", ["ollama (qwen-code 2.5)", "google (gemini 3)"])

    # Initialize Button
    if st.button("🚀 Initialize Agent"):
        if os.path.exists(repo_path):
            st.session_state.agent = CodeReviewAgent(repo_path, provider)
            st.session_state.messages = []
            st.success("Context Loaded!")
        else:
            st.error("Invalid Path")

    # --- NEW: AUTO-FIX BUTTON ---
    if "agent" in st.session_state:
        st.divider()
        st.subheader("🛠️ Actions")
        if st.button("✨ Auto-Fix Issues"):
            with st.spinner("Writing clean code..."):
                fix_code = st.session_state.agent.fix_issues()
                st.session_state.messages.append({"role": "assistant", "content": fix_code})
                # Force refresh to show the message immediately
                st.rerun()

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about your code..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if "agent" in st.session_state:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.agent.ask(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
