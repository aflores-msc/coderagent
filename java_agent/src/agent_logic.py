from src.shared.git_utils import get_staged_files, read_file
from src.shared.linter import run_static_analysis
from src.shared.llm_clients import GoogleClient, OllamaClient


class CodeReviewAgent:
    def __init__(self, repo_path: str, provider: str):
        self.repo_path = repo_path

        # 1. PYTHON DOES THE WORK (Instant)
        print("⚡ agent: Pre-scanning files...")
        context_data = self._gather_repo_context()

        # 2. INJECT INTO SYSTEM PROMPT
        system_prompt = f"""
You are a Lead Java Engineer using Qwen 2.5 Coder.
Your goal is High-Speed, High-Impact code review.

**CONTEXT:**
The user has staged the following files. 
I have already run a Static Analyzer.

**FILE DATA:**
{context_data}

**INSTRUCTIONS:**
1. Review the code above.
2. If "STATIC ANALYSIS REPORT" shows CRITICAL errors, you MUST reject the code.
3. Be concise.
"""

        # 3. SETUP CLIENT
        if provider == "google":
            self.client = GoogleClient(model_name="gemini-3-flash-preview")
        else:
            self.client = OllamaClient(model_name="qwen2.5-coder:14b")

        self.client.start_session(system_prompt)

    def _gather_repo_context(self) -> str:
        """Runs git and linter logic BEFORE calling the LLM."""
        files = get_staged_files(self.repo_path)
        if not files:
            return "No staged files found."

        report = []
        for f in files:
            content = read_file(self.repo_path, f)
            issues = run_static_analysis(content, f)  # Regex Linter

            chunk = f"\n=== FILE: {f} ===\n"
            if issues:
                chunk += "🚨 STATIC ANALYSIS REPORT (CRITICAL):\n" + "\n".join(issues) + "\n"
            else:
                chunk += "✅ Static Analysis: Passed\n"

            chunk += f"--- CODE START ---\n{content}\n--- CODE END ---\n"
            report.append(chunk)

        return "\n".join(report)

    def ask(self, prompt: str):
        return self.client.ask(prompt)

    def fix_issues(self):
        """
        Asks the LLM to rewrite the code to fix the specific Linter errors.
        """
        fix_prompt = """
        ACT AS: Senior Java Architect.
        TASK: Rewrite the staged files to FIX the Static Analysis errors reported above.

        SPECIFIC INSTRUCTIONS:
        1. ✅ REPLACE Field Injection (@Autowired private) with Constructor Injection (@RequiredArgsConstructor or manual constructor).
        2. ✅ REPLACE System.out.println with a valid SLF4J Logger.
        3. ✅ OUTPUT: The full, valid Java Class.
        4. ❌ NO conversational filler. Just the code blocks.
        """

        return self.client.ask(fix_prompt)
