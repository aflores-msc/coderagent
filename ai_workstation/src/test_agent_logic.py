# src/test_agent_logic.py

from src.shared.git_utils import get_staged_files, read_file
from src.shared.llm_clients import GoogleClient, OllamaClient


class TestGenAgent:
    def __init__(self, repo_path: str, provider: str):
        self.repo_path = repo_path

        # 1. GATHER CONTEXT (Just the code, no linter needed)
        print("🧪 test-agent: Reading files for test generation...")
        context_data = self._gather_code_context()

        # 2. DEFINE PERSONA (QA Engineer)
        system_prompt = f"""
You are a Senior QA Automation Engineer.
Your goal is to write robust JUnit 5 Unit Tests for the staged code.

**CONTEXT:**
The user has written the following Java code:

{context_data}

**YOUR INSTRUCTIONS:**
1. 🧪 **Generate JUnit 5 Tests:** Use `@Test`, `@DisplayName`, `@ParameterizedTest`, and `Assertions`.
2. 🧩 **Test Structure:** Follow AAA (Arrange-Act-Assert) pattern. Use `@BeforeEach` for setup if needed.
3. **Spring:** Use Spring Boot Test annotations if the code is a Spring component (e.g., `@SpringBootTest`, `@MockBean`, `@MockMvc`).
3. 🎭 **Mock Dependencies:** Use `Mockito` (`@ExtendWith(MockitoExtension.class)`, `@Mock`, `@InjectMocks`, @Spy).
4. 🛡️ **Cover Edge Cases:** Don't just test the happy path. Test nulls, empty lists, and exceptions.
5. ❌ **Strictness:** Do NOT use `System.out.println` in tests. Use Assertions.
6. **Output:** Only the Java Test Class code.
"""

        # 3. INITIALIZE CLIENT
        if "google" in provider.lower():
            self.client = GoogleClient(model_name="gemini-3-flash-preview")
        else:
            # Qwen 2.5 Coder is EXCELLENT at writing tests
            self.client = OllamaClient(model_name="qwen2.5-coder:14b")

        self.client.start_session(system_prompt)

    def _gather_code_context(self) -> str:
        """Reads files without running the linter."""
        files = get_staged_files(self.repo_path)
        if not files:
            return "No staged files found."

        report = []
        for f in files:
            content = read_file(self.repo_path, f)
            report.append(f"=== FILE: {f} ===\n{content}\n")

        return "\n".join(report)

    def ask(self, prompt: str):
        return self.client.ask(prompt)

    def generate_tests(self):
        """Shortcut command to just generate the test file."""
        return self.client.ask("Generate the complete JUnit 5 test class for this code.")
