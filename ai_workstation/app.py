import streamlit as st
import os
import base64
import streamlit.components.v1 as components
from dotenv import load_dotenv

# Import Agents
from src.agent_logic import CodeReviewAgent
from src.test_agent_logic import TestGenAgent
from src.sql_agent_logic import BigQueryAgent
from src.mongo_agent_logic import MongoAgent
from src.diagram_agent_logic import ClassDiagramAgent

load_dotenv()

st.set_page_config(page_title="Smart Developer Assistant", page_icon="☕", layout="wide")
st.title("☕ Smart Developer Assistant")


# --- UTILITY: MERMAID LIVE LINK GENERATOR ---
def get_mermaid_link(code: str) -> str:
    """Generates a direct link to view the code in Mermaid.live"""
    # Mermaid.live expects base64 encoded JSON state
    # But for simplicity, we can use the 'edit' endpoint if we format it right.
    # Actually, a raw base64 of the code is often enough for the /view endpoint
    code_bytes = code.encode('utf-8')
    base64_bytes = base64.b64encode(code_bytes)
    base64_string = base64_bytes.decode('ascii')
    return f"https://mermaid.live/edit#base64:{base64_string}"


# --- CUSTOM MERMAID RENDERER ---
def render_mermaid(code: str):
    """
    Renders Mermaid code with a fallback link.
    """
    # 1. Generate Link
    # We use a simple JSON wrapper for the state compatible with Mermaid Live
    import json
    state = {"code": code, "mermaid": {"theme": "dark"}}
    json_str = json.dumps(state)
    b64_str = base64.urlsafe_b64encode(json_str.encode('utf-8')).decode('utf-8')
    link = f"https://mermaid.live/edit#{b64_str}"

    st.markdown(f"### [🔎 Click here to open in Mermaid.live]({link})")

    # 2. Try Inline Render (Best Effort)
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <body>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11.2/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
        </script>
        <div class="mermaid">
            {code}
        </div>
    </body>
    </html>
    """
    # Increased height to prevent cutoff
    components.html(html_code, height=800, scrolling=True)


with st.sidebar:
    st.header("⚙️ Configuration")

    provider = st.selectbox(
        "AI Model",
        [
            "ollama (qwen2.5-coder:14b) - Local Workhorse",
            "google (gemini-3-flash-preview) - Cloud SOTA"
        ],
        index=0
    )

    st.divider()

    agent_type = st.radio(
        "Select Agent Role",
        [
            "🕵️‍♂️ Code Reviewer",
            "🧪 Unit Test Generator",
            "📊 Class Diagram Generator",
            "💾 Text-to-BigQuery",
            "🍃 Text-to-MongoDB"
        ],
    )

    repo_path = None
    schema_path = None

    if agent_type in ["🕵️‍♂️ Code Reviewer", "🧪 Unit Test Generator", "📊 Class Diagram Generator"]:
        repo_path = st.text_input("Repo Path (src/main/java)", value="/Users/user/IdeaProjects/my-app/src/main/java")

    elif agent_type == "💾 Text-to-BigQuery":
        schema_path = st.text_input("Schema File (.sql)", value="/Users/user/projects/schema.sql")
    elif agent_type == "🍃 Text-to-MongoDB":
        schema_path = st.text_input("Schema File (.json)", value="/Users/user/projects/mongo_schema.json")

    if st.button("🚀 Initialize Agent", type="primary"):
        st.session_state.messages = []
        st.session_state.agent = None

        try:
            if agent_type == "🕵️‍♂️ Code Reviewer":
                if os.path.exists(repo_path):
                    st.session_state.agent = CodeReviewAgent(repo_path, provider)
                    st.success("✅ Architect Loaded")

            elif agent_type == "🧪 Unit Test Generator":
                if os.path.exists(repo_path):
                    st.session_state.agent = TestGenAgent(repo_path, provider)
                    st.success("✅ QA Engineer Loaded")

            elif agent_type == "📊 Class Diagram Generator":
                if os.path.exists(repo_path):
                    st.session_state.agent = ClassDiagramAgent(repo_path, provider)
                    st.success("✅ Diagram Generator Loaded")
                else:
                    st.error("❌ Path not found.")

            elif agent_type == "💾 Text-to-BigQuery":
                st.session_state.agent = BigQueryAgent(schema_path, provider)
                st.success("✅ SQL Agent Loaded")
            elif agent_type == "🍃 Text-to-MongoDB":
                st.session_state.agent = MongoAgent(schema_path, provider)
                st.success("✅ Mongo Agent Loaded")

        except Exception as e:
            st.error(f"Error: {e}")

# --- SPECIAL VIEW FOR DIAGRAM AGENT ---
if "agent" in st.session_state and isinstance(st.session_state.agent, ClassDiagramAgent):
    st.info("👇 Click below to generate the diagram.")
    if st.button("🎨 Generate Diagram"):
        with st.spinner("Analyzing Java classes..."):
            mermaid_code = st.session_state.agent.generate_diagram()

            # Show the raw code
            with st.expander("View Mermaid Source"):
                st.code(mermaid_code, language="mermaid")

            # Render with link
            render_mermaid(mermaid_code)

            st.session_state.messages.append({"role": "assistant", "content": "Diagram Generated!"})

# --- STANDARD CHAT INTERFACE ---
else:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if "```" in msg["content"]:
                st.markdown(msg["content"])
            else:
                st.write(msg["content"])

    if prompt := st.chat_input("Ask your agent..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        if "agent" in st.session_state:
            with st.chat_message("assistant"):
                with st.spinner("Processing..."):
                    response = st.session_state.agent.ask(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
