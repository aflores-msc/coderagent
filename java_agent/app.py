import streamlit as st
import os
from dotenv import load_dotenv

# Import our two Agent Personas
from src.agent_logic import CodeReviewAgent
from src.test_agent_logic import TestGenAgent

# Load environment variables (API keys)
load_dotenv()

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Java AI Workstation",
    page_icon="☕",
    layout="wide"
)

st.title("☕ Java AI Workstation (M4 Pro Edition)")
st.markdown("---")

# --- 2. SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("⚙️ Configuration")

    # Repo Input
    repo_path = st.text_input(
        "Repository Path",
        value="/Users/yourname/IdeaProjects/my-app",
        help="Absolute path to your local git repository."
    )

    # Model Selection
    provider = st.selectbox(
        "AI Model",
        ["ollama (qwen 2.5)", "google (gemini)"],
        index=0
    )

    st.divider()

    # Agent Selector
    st.subheader("🤖 Select Agent Role")
    agent_type = st.radio(
        "Choose your teammate:",
        ["🕵️‍♂️ Code Reviewer", "🧪 Unit Test Generator"],
        help="Reviewer enforces strict standards. Tester writes JUnit 5 tests."
    )

    # INITIALIZE BUTTON
    if st.button("🚀 Initialize Agent", type="primary"):
        if os.path.exists(repo_path):
            # Clear history when switching contexts
            st.session_state.messages = []

            # Instantiate the correct class based on selection
            if agent_type == "🕵️‍♂️ Code Reviewer":
                st.session_state.agent = CodeReviewAgent(repo_path, provider)
                st.success("✅ Review Architect Loaded!")
            else:
                st.session_state.agent = TestGenAgent(repo_path, provider)
                st.success("✅ QA Engineer Loaded!")
        else:
            st.error("❌ Invalid Path: Folder not found.")

    # --- 3. DYNAMIC ACTION BUTTONS ---
    # These buttons only appear if an agent is active
    if "agent" in st.session_state:
        st.divider()
        st.subheader("⚡ Quick Actions")

        # SCENARIO A: The Reviewer is active
        if isinstance(st.session_state.agent, CodeReviewAgent):
            if st.button("✨ Auto-Fix Issues"):
                with st.spinner("Refactoring code to Java 17+ standards..."):
                    # Call the specific method for fixing code
                    response = st.session_state.agent.fix_issues()
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

        # SCENARIO B: The Tester is active
        elif isinstance(st.session_state.agent, TestGenAgent):
            if st.button("🧬 Generate JUnit Tests"):
                with st.spinner("Writing robust JUnit 5 tests with Mockito..."):
                    # Call the specific method for generating tests
                    response = st.session_state.agent.generate_tests()
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

# --- 4. CHAT INTERFACE ---

# Initialize chat history if not exists
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle User Input
if prompt := st.chat_input("Ask your agent something..."):
    # 1. Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Agent Response
    if "agent" in st.session_state:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.agent.ask(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.warning("⚠️ Please initialize an agent from the sidebar first.")
