import streamlit as st
import os
from dotenv import load_dotenv

# Import Agents
from src.agent_logic import CodeReviewAgent
from src.test_agent_logic import TestGenAgent
from src.sql_agent_logic import BigQueryAgent
from src.mongo_agent_logic import MongoAgent  # <--- NEW

load_dotenv()

st.set_page_config(page_title="AI Coder", page_icon="☕", layout="wide")
st.title("☕ AI Coder")

with st.sidebar:
    st.header("⚙️ Configuration")

    # Provider Selection
    provider = st.selectbox(
        "AI Model",
        [
            "ollama (qwen2.5-coder:14b) - Local Workhorse",
            "google (gemini-3-flash-preview) - Cloud SOTA"
        ],
        index=0
    )

    st.divider()

    # --- AGENT SELECTOR ---
    agent_type = st.radio(
        "Select Agent Role",
        [
            "🕵️‍♂️ Code Reviewer",
            "🧪 Unit Test Generator",
            "💾 Text-to-BigQuery",
            "🍃 Text-to-MongoDB"  # <--- NEW
        ],
    )

    # --- DYNAMIC INPUTS ---
    repo_path = None
    schema_path = None

    # JAVA AGENTS
    if agent_type in ["🕵️‍♂️ Code Reviewer", "🧪 Unit Test Generator"]:
        repo_path = st.text_input("Repo Path", value="/Users/user/projects/my-app")

    # BIGQUERY AGENT
    elif agent_type == "💾 Text-to-BigQuery":
        st.info("SQL Schema Required")
        schema_path = st.text_input("Schema File (.sql)", value="/Users/user/projects/my-app/schema.sql")

    # MONGODB AGENT
    elif agent_type == "🍃 Text-to-MongoDB":
        st.info("JSON Schema Required")
        schema_path = st.text_input(
            "Schema File (.json)",
            value="/Users/user/projects/my-app/mongo_schema.json",
            help="A JSON file containing sample documents for your collections."
        )

    # INITIALIZE BUTTON
    if st.button("🚀 Initialize Agent", type="primary"):
        st.session_state.messages = []

        try:
            if agent_type == "🕵️‍♂️ Code Reviewer":
                if os.path.exists(repo_path):
                    st.session_state.agent = CodeReviewAgent(repo_path, provider)
                    st.success("✅ Architect Loaded")

            elif agent_type == "🧪 Unit Test Generator":
                if os.path.exists(repo_path):
                    st.session_state.agent = TestGenAgent(repo_path, provider)
                    st.success("✅ QA Engineer Loaded")

            elif agent_type == "💾 Text-to-BigQuery":
                if os.path.exists(schema_path):
                    st.session_state.agent = BigQueryAgent(schema_path, provider)
                    st.success("✅ SQL Agent Loaded")

            # NEW INITIALIZATION
            elif agent_type == "🍃 Text-to-MongoDB":
                if os.path.exists(schema_path):
                    st.session_state.agent = MongoAgent(schema_path, provider)
                    st.success("✅ Mongo Agent Loaded")
                else:
                    st.error("❌ Schema file not found.")

        except Exception as e:
            st.error(f"Error: {e}")

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Detect code blocks for nice formatting
        if "db." in msg["content"] or "SELECT" in msg["content"]:
            st.code(msg["content"], language="javascript" if "db." in msg["content"] else "sql")
        else:
            st.markdown(msg["content"])

if prompt := st.chat_input("Ask your agent..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if "agent" in st.session_state:
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                response = st.session_state.agent.ask(prompt)

                # Format Output
                if response.startswith("db."):
                    st.code(response, language="javascript")
                else:
                    st.markdown(response)

                st.session_state.messages.append({"role": "assistant", "content": response})
