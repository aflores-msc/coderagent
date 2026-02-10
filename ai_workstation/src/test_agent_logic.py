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
🧪 JUnit 5
Use @Test, @DisplayName, @Nested, @ParameterizedTest, @MethodSource, and Assertions.
Use assertThrows for exception testing.
Never use JUnit 4 annotations.
🎯 Test Structure (AAA)
Arrange: create inputs, mocks, and test data.
Act: call the method under test.
Assert: verify results and interactions.
Use @BeforeEach for shared setup.
🌱 Spring Boot Test
Use @SpringBootTest for integration tests.
Use @WebMvcTest for controller‑only tests.
Use @MockBean for Spring‑managed dependencies.
Use @Autowired for real beans under test.
Use MockMvc for HTTP‑level tests.
Use @TestConfiguration for test‑only beans.
🎭 Mockito
Use @ExtendWith(MockitoExtension.class) for pure unit tests.
Use @Mock, @Spy, and @InjectMocks appropriately.
Use when(...).thenReturn(...) and verify(...).
Avoid mocking value objects or simple data carriers.
Use argument captors when needed.
🛡️ Edge Cases
Test null inputs, empty collections, boundary values, and invalid states.
Test exceptions using assertThrows.
Test alternative branches, not just the happy path.
❌ Strictness
Never use System.out.println in tests.
Never assert on side effects without verifying behavior.
Never rely on test execution order.
📏 Coverage Expectations
Cover all public methods.
Cover all branches when feasible.
Include at least one negative test per method.
🧩 Output Format
Only output the Java test class code.
No explanations, comments, or additional text outside the class.
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
