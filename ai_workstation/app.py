import streamlit as st
import os
import pandas as pd
import streamlit.components.v1 as components
from dotenv import load_dotenv

from src.agent_logic import CodeReviewAgent
from src.test_agent_logic import TestGenAgent
from src.sql_agent_logic import BigQueryAgent
from src.mongo_agent_logic import MongoAgent
from src.diagram_agent_logic import ClassDiagramAgent
from src.dependency_agent_logic import DependencyInspectorAgent

load_dotenv()
st.set_page_config(page_title="Smart Developer Assistant", layout="wide")
st.title("☕ Smart Developer Assistant")

with st.sidebar:
    st.header("⚙️ Configuration")
    provider = st.selectbox("AI Model", ["ollama (qwen2.5-coder:14b)", "google (gemini-3-flash)"], index=0)
    agent_type = st.radio("Select Agent Role", [
        "🕵️‍♂️ Code Reviewer", "🧪 Unit Test Generator", "📊 Class Diagram Generator",
        "📦 Dependency Inspector", "💾 Text-to-BigQuery"
    ])
    repo_path = st.text_input("Project Root Path", value="/Users/user/IdeaProjects/my-app")

    if st.button("🚀 Initialize Agent", type="primary"):
        if agent_type == "📦 Dependency Inspector":
            if os.path.exists(repo_path):
                st.session_state.agent = DependencyInspectorAgent(provider)
                st.session_state.repo_path = repo_path
                st.success("✅ Dependency Inspector Initialized")
            else:
                st.error("Invalid Path")

# --- MAIN CONTENT ---
if "agent" in st.session_state and isinstance(st.session_state.agent, DependencyInspectorAgent):
    st.header("📦 Dependency Inspector")

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("🔍 Check for Latest Versions", type="primary"):
            with st.spinner("Querying Maven Central..."):
                df = st.session_state.agent.check_project_dependencies(st.session_state.repo_path)
                if not df.empty:
                    report_path = "dependency_report.parquet"
                    df.to_parquet(report_path, engine='pyarrow')  # Preserve strict schema
                    st.session_state.last_report = report_path

    if "last_report" in st.session_state:
        st.divider()
        report_df = pd.read_parquet(st.session_state.last_report)
        details = pd.json_normalize(report_df['Current'])
        final_df = pd.concat([report_df['Package'], details], axis=1)

        st.subheader("📊 Version Drift Analysis")

        # Search filter
        search = st.text_input("🔍 Filter packages:", "")
        if search:
            final_df = final_df[final_df['Package'].str.contains(search, case=False)]


        # Clean Styling: Colors only the text in the Status column
        def style_status(val):
            if val == 'outdated': return 'color: #d9534f; font-weight: bold;'
            if val == 'up-to-date': return 'color: #5cb85c;'
            return ''


        st.dataframe(
            final_df.style.map(style_status, subset=['status']),
            use_container_width=True,
            hide_index=True
        )

        st.info(st.session_state.agent.interpret_report(st.session_state.last_report))

        with open(st.session_state.last_report, "rb") as f:
            st.download_button("💾 Download Parquet Report", f, "dependency_report.parquet")
else:
    st.info("Initialize the Dependency Inspector in the sidebar to begin.")
