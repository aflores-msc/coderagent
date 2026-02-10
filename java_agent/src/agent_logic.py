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
1. - Show the list of staged files.

2. 🧹 **Clean Up Dead Code:**
   - **Global:** The Linter has flagged Unused Imports/Fields. Confirm and remove them.
   - **Local:** Look inside methods. If a variable is declared but never read, flag it as "Unused Local Variable".

3. 🚀 **Modernize (Java 17+):**
   - **Records:** If you see a class with only private fields, getters, setters, and `toString`, suggest converting it to a `record`.
   - **Var:** Use `var` for local variables where the type is obvious (e.g., `var list = new ArrayList<String>();`).
   - **Switch:** Enforce `case ->` syntax.
   - **Text Blocks:** If you see multi-line string concatenation, suggest using Text Blocks 

4. 🛡️ **Best Practices:**
   - **Optional:** Use `Optional.map().orElse()` instead of `if (x != null)`.
   - **Validation:** Use `Objects.requireNonNull()` instead of `if (x == null) throw...`.
   - **Logging:** Use SLF4J Logger instead of `System.out.println` or `e.printStackTrace()`.
   - **Dependency Injection:** Use Constructor Injection instead of Field Injection.
   - **Error Handling:** Use `try-with-resources` for AutoCloseable resources.
   - **Immutability:** Use `final` for fields that are not reassigned.
   - **Lombok:** If Lombok is used, ensure that it is used correctly (e.g., `@Data` for data classes).
   - **Code Style:** Enforce consistent code style (e.g., spacing, braces, etc.).
   - **Security:** Flag any use of deprecated or insecure APIs (e.g., `MD5`, `DES`, etc.).
   - **Performance:** Flag any inefficient code patterns (e.g., using `String` concatenation in loops).
   - **Concurrency:** Flag any potential concurrency issues (e.g., shared mutable state without synchronization).
   - **Testing:** Flag any public methods that lack corresponding unit tests (if test files are available).
   - **Documentation:** Flag any public classes or methods that lack Javadoc comments.
   - **Code Smells:** Flag any code that is overly complex, has long methods, or violates SOLID principles.
   - **Security:** Flag any hardcoded credentials, use of `Runtime.exec()`, or other potential security vulnerabilities.
   - **Maintainability:** Flag any code that is difficult to read, understand, or maintain.
   - **Scalability:** Flag any code that may not scale well with increased load or data size.
   - **SOLID Principles:** Flag any violations of SOLID principles (e.g., Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion).
   - **Design Patterns:** Suggest appropriate design patterns for complex code (e.g., Factory, Singleton, Observer, etc.).

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
