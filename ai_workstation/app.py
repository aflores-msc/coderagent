import streamlit as st
import streamlit.components.v1 as components
import os
import pandas as pd
import base64
import json
from dotenv import load_dotenv

# --- IMPORT AGENT CLASSES ---
from src.agent_logic import CodeReviewAgent
from src.test_agent_logic import TestGenAgent
from src.sql_agent_logic import BigQueryAgent
from src.mongo_agent_logic import MongoAgent
from src.diagram_agent_logic import ClassDiagramAgent
from src.dependency_agent_logic import DependencyInspectorAgent

load_dotenv()
st.set_page_config(page_title="Smart Developer Assistant", layout="wide")
st.title("☕ Smart Developer Assistant")


# --- HELPER: Mermaid Live Link Generator ---
def get_mermaid_link(graph_code):
    """Generates a direct link to open the diagram in Mermaid.live"""
    state = {
        "code": graph_code,
        "mermaid": {"theme": "default"}
    }
    json_str = json.dumps(state)
    base64_str = base64.urlsafe_b64encode(json_str.encode("utf-8")).decode("utf-8")
    return f"https://mermaid.live/edit#base64:{base64_str}"


# --- HELPER: Inline Mermaid Renderer ---
def render_mermaid(code: str, height=600):
    """
    Custom HTML component to render Mermaid diagrams reliably.
    """
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        </script>
        <style>
            body {{ font-family: sans-serif; }}
            .mermaid {{ display: flex; justify-content: center; }}
        </style>
    </head>
    <body>
        <div class="mermaid">
            {code}
        </div>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=True)


# --- HELPER: Code Cleaner ---
def clean_code_output(text: str) -> str:
    """Defensively removes markdown code fences from LLM output."""
    if not text: return ""
    return text.replace("```java", "").replace("```sql", "").replace("```json", "").replace("```", "").strip()


# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("⚙️ Configuration")
    provider = st.selectbox("AI Model", ["ollama (qwen2.5-coder:14b)", "google (gemini-3-flash)"], index=0)

    agent_type = st.radio("Select Agent Role", [
        "🕵️‍♂️ Code Reviewer",
        "🧪 Unit Test Generator",
        "📊 Class Diagram Generator",
        "📦 Dependency Inspector",
        "💾 Text-to-BigQuery",
        "🍃 Text-to-MongoDB"
    ])

    # --- DYNAMIC INPUT TOGGLING ---
    repo_path = None
    schema_path = None

    # Group 1: Data Agents (Need Schema, NOT Project Root)
    if agent_type in ["💾 Text-to-BigQuery", "🍃 Text-to-MongoDB"]:
        default_schema = "/Users/user/IdeaProjects/my-app/schema.sql" if "BigQuery" in agent_type else "/Users/user/IdeaProjects/my-app/schema.json"
        schema_path = st.text_input("Schema File Path", value=default_schema)

    # Group 2: Code Agents (Need Project Root, NOT Schema)
    else:
        repo_path = st.text_input("Project Root Path", value="/Users/user/IdeaProjects/my-app")

    if st.button("🚀 Initialize Agent", type="primary"):
        try:
            # --- INITIALIZATION LOGIC ---

            # CASE 1: Data Agents (Validate Schema Path)
            if agent_type in ["💾 Text-to-BigQuery", "🍃 Text-to-MongoDB"]:
                if schema_path and os.path.exists(schema_path):
                    if agent_type == "💾 Text-to-BigQuery":
                        st.session_state.agent = BigQueryAgent(schema_path=schema_path, provider=provider)
                        st.success(f"✅ BigQuery Agent Initialized")
                    elif agent_type == "🍃 Text-to-MongoDB":
                        st.session_state.agent = MongoAgent(schema_path=schema_path, provider=provider)
                        st.success(f"✅ Text-to-MongoDB Initialized")
                else:
                    st.error(f"❌ Schema file not found: {schema_path}")

            # CASE 2: Code Agents (Validate Repo Path)
            else:
                if repo_path and os.path.exists(repo_path):
                    # Save repo path for later use by these agents
                    st.session_state.repo_path = repo_path

                    if agent_type == "📦 Dependency Inspector":
                        st.session_state.agent = DependencyInspectorAgent(provider=provider)
                        st.success("✅ Dependency Inspector Initialized")

                    elif agent_type == "🕵️‍♂️ Code Reviewer":
                        st.session_state.agent = CodeReviewAgent(repo_path=repo_path, provider=provider)
                        st.success("✅ Code Reviewer Initialized")

                    elif agent_type == "🧪 Unit Test Generator":
                        st.session_state.agent = TestGenAgent(repo_path=repo_path, provider=provider)
                        st.success("✅ Unit Test Generator Initialized")

                    elif agent_type == "📊 Class Diagram Generator":
                        st.session_state.agent = ClassDiagramAgent(repo_path=repo_path, provider=provider)
                        st.success("✅ Class Diagram Generator Initialized")
                else:
                    st.error(f"❌ Project path not found: {repo_path}")

        except Exception as e:
            st.error(f"Failed to initialize: {str(e)}")

# --- MAIN CONTENT ROUTING ---
if "agent" in st.session_state:
    agent = st.session_state.agent

    # 1. DEPENDENCY INSPECTOR
    if isinstance(agent, DependencyInspectorAgent):
        st.header("📦 Dependency Inspector")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("🔍 Check for Latest Versions", type="primary"):
                with st.spinner("Querying Maven Central..."):
                    # Use the saved repo_path from session state
                    df = agent.check_project_dependencies(st.session_state.repo_path)
                    if not df.empty:
                        report_path = "dependency_report.parquet"
                        df.to_parquet(report_path, engine='pyarrow')
                        st.session_state.last_report = report_path
                    else:
                        st.warning("No dependencies found.")

        if "last_report" in st.session_state:
            st.divider()
            report_df = pd.read_parquet(st.session_state.last_report)
            details = pd.json_normalize(report_df['Current'])
            final_df = pd.concat([report_df['Package'], details], axis=1)

            st.subheader("📊 Version Drift Analysis")


            def style_status(val):
                return 'color: #d9534f; font-weight: bold;' if val == 'outdated' else 'color: #5cb85c;'


            st.dataframe(
                final_df.style.map(style_status, subset=['status']),
                width="stretch",
                hide_index=True
            )
            st.info(agent.interpret_report(st.session_state.last_report))

    # 2. CODE REVIEWER
    elif isinstance(agent, CodeReviewAgent):
        st.header("🕵️‍♂️ Code Reviewer")
        st.info(f"Scanning: `{st.session_state.repo_path}`")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("⚡ Run Static Analysis"):
                with st.spinner("Analyzing code..."):
                    review = agent.ask("Review the staged code.")
                    st.session_state.review_result = review
        with col2:
            if st.button("🛠️ Auto-Fix Issues"):
                with st.spinner("Applying fixes..."):
                    fix = agent.fix_issues()
                    st.session_state.fix_result = clean_code_output(fix)

        if "review_result" in st.session_state:
            st.subheader("📝 Review Report")
            st.markdown(st.session_state.review_result)
        if "fix_result" in st.session_state:
            st.subheader("🔧 Suggested Fixes")
            st.code(st.session_state.fix_result, language='java')

    # 3. UNIT TEST GENERATOR
    elif isinstance(agent, TestGenAgent):
        st.header("🧪 Unit Test Generator")
        st.info(f"Target: `{st.session_state.repo_path}`")
        if st.button("Generate JUnit 5 Tests"):
            with st.spinner("Writing tests..."):
                tests = agent.generate_tests()
                st.code(clean_code_output(tests), language='java')

    # 4. CLASS DIAGRAM GENERATOR
    elif isinstance(agent, ClassDiagramAgent):
        st.header("📊 Class Diagram Generator")

        if "diagram_code" not in st.session_state:
            st.session_state.diagram_code = None

        if st.button("Generate Mermaid Diagram", type="primary"):
            with st.spinner("Parsing Java classes..."):
                code = agent.generate_diagram()
                st.session_state.diagram_code = code

        if st.session_state.diagram_code:
            st.divider()

            col_link, col_copy = st.columns([1, 4])
            with col_link:
                url = get_mermaid_link(st.session_state.diagram_code)
                st.link_button("🌐 Open in Mermaid.live", url)

            tab1, tab2 = st.tabs(["🖼️ Visual Diagram", "📜 Mermaid Code"])

            with tab1:
                render_mermaid(st.session_state.diagram_code)

            with tab2:
                st.code(st.session_state.diagram_code, language='mermaid')

    # 5. BIGQUERY AGENT
    elif isinstance(agent, BigQueryAgent):
        st.header("💾 Text-to-BigQuery")
        question = st.text_area("Ask a question about your BigQuery data:")
        if st.button("Generate SQL"):
            if question:
                with st.spinner("Generating SQL..."):
                    sql = agent.ask(question)
                    st.code(clean_code_output(sql), language='sql')
            else:
                st.warning("Please enter a question.")

    # 6. Text-to-MongoDB
    elif isinstance(agent, MongoAgent):
        st.header("🍃 Text-to-MongoDB")
        question = st.text_area("Ask a question about your MongoDB collections:")
        if st.button("Generate Query"):
            if question:
                with st.spinner("Generating Mongo Shell query..."):
                    query = agent.ask(question)
                    st.code(clean_code_output(query), language='javascript')
            else:
                st.warning("Please enter a question.")

else:
    st.info("👈 Select an Agent Role in the sidebar and click **Initialize Agent** to begin.")
