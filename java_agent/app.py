import streamlit as st
import os
from dotenv import load_dotenv

# Import Agents
from src.agent_logic import CodeReviewAgent
from src.test_agent_logic import TestGenAgent
from src.sql_agent_logic import BigQueryAgent

load_dotenv()

st.set_page_config(page_title="Java + SQL Workstation", page_icon="☕", layout="wide")
st.title("☕ Java & BigQuery AI Workstation (M4 Pro)")

with st.sidebar:
    st.header("⚙️ Configuration")

    # --- MODEL SELECTION (UPDATED) ---
    provider = st.selectbox(
        "AI Model",
        [
            "ollama (qwen2.5-coder:14b) - Generalist",
            "google (gemini-3-flash-preview) - Cloud SOTA"
        ],
        index=0
    )

    st.divider()

    # --- AGENT SELECTOR ---
    agent_type = st.radio(
        "Select Agent Role",
        ["🕵️‍♂️ Code Reviewer", "🧪 Unit Test Generator", "💾 Text-to-BigQuery"],
    )

    # --- DYNAMIC INPUTS ---
    repo_path = None
    schema_path = None

    if agent_type in ["🕵️‍♂️ Code Reviewer", "🧪 Unit Test Generator"]:
        repo_path = st.text_input("Repo Path", value="/Users/yourname/IdeaProjects/my-app")

    elif agent_type == "💾 Text-to-BigQuery":
        st.info("Schema Required")
        schema_path = st.text_input(
            "Schema File Path (.sql/.txt)",
            value="/Users/yourname/IdeaProjects/my-app/schema.sql",
            help="Path to a file containing CREATE TABLE statements."
        )

    # --- INITIALIZE BUTTON ---
    if st.button("🚀 Initialize Agent", type="primary"):
        st.session_state.messages = []  # Clear history

        try:
            # 1. CODE REVIEWER
            if agent_type == "🕵️‍♂️ Code Reviewer":
                if os.path.exists(repo_path):
                    st.session_state.agent = CodeReviewAgent(repo_path, provider)
                    st.success("✅ Architect Loaded")
                else:
                    st.error("Invalid Repo Path")

            # 2. TEST GENERATOR
            elif agent_type == "🧪 Unit Test Generator":
                if os.path.exists(repo_path):
                    st.session_state.agent = TestGenAgent(repo_path, provider)
                    st.success("✅ QA Engineer Loaded")
                else:
                    st.error("Invalid Repo Path")

            # 3. BIGQUERY AGENT
            elif agent_type == "💾 Text-to-BigQuery":
                if os.path.exists(schema_path):
                    with st.spinner("Ingesting Schema..."):
                        st.session_state.agent = BigQueryAgent(schema_path, provider)
                    st.success(f"✅ Schema Loaded!")
                else:
                    st.error("❌ Schema file not found.")

        except Exception as e:
            st.error(f"Initialization Failed: {e}")

# --- DYNAMIC ACTION BUTTONS ---
if "agent" in st.session_state:
    if isinstance(st.session_state.agent, CodeReviewAgent):
        st.sidebar.divider()
        if st.sidebar.button("✨ Auto-Fix Issues"):
            with st.spinner("Refactoring..."):
                res = st.session_state.agent.fix_issues()
                st.session_state.messages.append({"role": "assistant", "content": res})
                st.rerun()

    elif isinstance(st.session_state.agent, TestGenAgent):
        st.sidebar.divider()
        if st.sidebar.button("🧬 Generate JUnit Tests"):
            with st.spinner("Writing tests..."):
                res = st.session_state.agent.generate_tests()
                st.session_state.messages.append({"role": "assistant", "content": res})
                st.rerun()

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Special formatting for SQL code blocks
        if "```sql" in msg["content"] or "SELECT" in msg["content"]:
            st.markdown(msg["content"])
        else:
            st.markdown(msg["content"])

if prompt := st.chat_input("Ask your agent..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if "agent" in st.session_state:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.agent.ask(prompt)

                # If response looks like pure SQL, format it nicely
                if response.strip().upper().startswith("SELECT") or response.strip().upper().startswith("WITH"):
                    st.code(response, language="sql")
                else:
                    st.markdown(response)

                st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.warning("⚠️ Please initialize an agent from the sidebar first.")
