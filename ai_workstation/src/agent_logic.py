from src.shared.git_utils import get_staged_files, read_file
from src.shared.linter import run_static_analysis
from src.shared.llm_clients import GoogleClient, OllamaClient


class CodeReviewAgent:
    def __init__(self, repo_path: str, provider: str):
        self.repo_path = repo_path

        # 1. PRE-COMPUTE CONTEXT (Speed + Accuracy)
        print("⚡ agent: Running Modern Java + Dead Code Scan...")
        context_data = self._gather_repo_context()

        # 2. THE "MODERN ARCHITECT" PROMPT
        system_prompt = f"""
You are an Expert Java Developer specializing in Java 17 (and newer) Migration and Code Cleanup.
Your goal is to enforce modern standards and delete dead code.

**CONTEXT:**
The user has staged files. I have already run a regex scan for global issues.
Review the code below.

**DATA:**
{context_data}

**YOUR CHECKLIST (ENFORCE STRICTLY):**
🗂️ Staged Files
List all staged files before analysis.
🧹 Dead Code
Remove unused imports, fields, methods, parameters, locals.
Flag unreachable code, duplicate logic, magic numbers.
🚀 Modern Java
Suggest records for data carriers.
Use var for obvious local types.
Enforce switch → syntax.
Suggest text blocks for multi‑line strings.
Use pattern matching for instanceof and switch.
Suggest sealed classes when hierarchies are closed.
Prefer “x %s”.formatted(v).
🛡️ Best Practices
Prefer Optional.map().orElse().
Use Objects.requireNonNull.
Replace println/printStackTrace with SLF4J.
Enforce constructor injection.
Use try‑with‑resources.
Mark non‑reassigned fields final.
Validate Lombok usage.
Enforce consistent formatting.
Flag deprecated or insecure APIs.
Flag inefficient patterns (string concat in loops, unnecessary streams).
Flag concurrency risks (shared mutable state, incorrect volatile usage).
Flag missing tests for public methods.
Flag missing Javadoc on public APIs.
Flag long methods, high complexity, SOLID violations.
Flag hardcoded credentials, unsafe exec, insecure file handling.
Flag maintainability or scalability issues.
Suggest design patterns when complexity warrants it.
🔐 Security
Flag SQL built via concatenation.
Flag XML parsers without secure config.
Flag file operations using unvalidated input.
Require SecureRandom for sensitive operations.
Flag unsafe deserialization.
Flag exposure of internal mutable state.
⚙️ Performance
Flag unnecessary boxing/unboxing.
Flag inefficient collection choices.
Flag overly complex stream pipelines.
Flag unbuffered I/O.
Flag excessive object creation in hot paths.
🧵 Concurrency
Flag manual thread creation; suggest executors or CompletableFuture.
Flag non‑final shared fields.
Flag misuse of synchronized collections.
Flag incorrect double‑checked locking.
Flag blocking calls inside async/reactive code.
🧪 Testing
Flag weak or missing assertions.
Flag insufficient coverage of logic branches.
Suggest parameterized tests for repeated scenarios.
Flag unnecessary mocks.
🧰 Dependencies
Flag unused or outdated dependencies.
Flag dependencies with known vulnerabilities.
Flag excessive transitive dependency usage.
🧩 API & Design
Flag interfaces with too many methods.
Suggest Builder for constructors with many parameters.
Flag overuse of static utilities.
Flag public mutable fields.
Flag mixed responsibilities.
📝 Documentation
Flag outdated TODO/FIXME.
Flag comments that restate code.
Require @since for public APIs when applicable.
Output Format
Status: APPROVED / REJECTED / CLEANUP REQUIRED
Critical Issues: Injection, security risks, concurrency bugs, logic errors
Dead Code Report: Unused imports, fields, methods, parameters, locals
Modernization Tips: Records, pattern matching, sealed classes, text blocks

**OUTPUT:**
- **Status:** [APPROVED / REJECTED / CLEANUP REQUIRED]
- **Critical Issues:** (Injection, Bugs)
- **Dead Code Report:** (List unused items)
- **Modernization Tips:** (Records, Pattern Matching, etc.)
"""

        # 3. CLIENT SETUP
        if "google" in provider.lower():
            self.client = GoogleClient(model_name="gemini-3-flash-preview")
        else:
            # Qwen 2.5 Coder 14B is perfect for this prompt
            self.client = OllamaClient(model_name="qwen2.5-coder:14b")

        self.client.start_session(system_prompt)

    def _gather_repo_context(self) -> str:
        files = get_staged_files(self.repo_path)
        if not files:
            return "No staged files found."

        report = []
        for f in files:
            content = read_file(self.repo_path, f)
            issues = run_static_analysis(content, f)  # Run the upgraded linter

            chunk = f"\n=== FILE: {f} ===\n"
            if issues:
                chunk += "🚨 DETECTED ISSUES (MUST FIX):\n" + "\n".join(issues) + "\n"
            else:
                chunk += "✅ Regex Scan: Clean\n"

            chunk += f"--- CODE START ---\n{content}\n--- CODE END ---\n"
            report.append(chunk)

        return "\n".join(report)

    def ask(self, prompt: str):
        return self.client.ask(prompt)

    def fix_issues(self):
        """
        Auto-Fix Prompt updated for Modern Java + Cleanup.
        """
        fix_prompt = """
        ACT AS: Senior Java Architect.
        TASK: Rewrite the code to fix ALL detected issues.

        INSTRUCTIONS:
        1. ❌ REMOVE all Unused Imports and Unused Fields flagged in the report.
        2. ❌ REMOVE Unused Local Variables inside methods.
        3. ✅ CONVERT simple data classes to `record`.
        4. ✅ UPGRADE to Java 17 syntax (Text Blocks, Switch Expressions, Pattern Matching).
        5. ✅ REPLACE Field Injection with Constructor Injection.

        OUTPUT: Only the full, clean Java Class.
        """
        return self.client.ask(fix_prompt)
