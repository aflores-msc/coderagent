import os
import re
from src.shared.llm_clients import GoogleClient, OllamaClient


class ClassDiagramAgent:
    def __init__(self, repo_path: str, provider: str):
        self.repo_path = repo_path
        self.provider = provider.lower()

        print(f"📊 diagram-agent: Scanning {repo_path}...")
        self.java_context = self._read_java_files()

        # --- STRATEGY: FEW-SHOT PROMPTING ---
        # We give the AI an example so it blindly copies the format.
        self.system_prompt = f"""
You are a strict syntax converter. 
Convert Java Source Code into a Mermaid.js Class Diagram.

**EXAMPLE INPUT:**
class User {{
    private List<String> roles;
    public void login() {{ ... }}
}}
class Admin extends User {{ ... }}

**EXAMPLE OUTPUT:**
classDiagram
    class User {{
        -List~String~ roles
        +login()
    }}
    class Admin
    User <|-- Admin

**YOUR TASK:**
Convert the following Java code following the EXACT format above.
1. Use `~` for generics (e.g., `List~String~`). NEVER use `< >`.
2. Do not write method bodies.
3. Do not use keywords like `public`, `private`, `final` in the diagram.
4. Output ONLY the mermaid code.

**SOURCE CODE:**
{self.java_context}
"""

        if "google" in self.provider:
            self.client = GoogleClient(model_name="gemini-3-flash-preview")
        else:
            self.client = OllamaClient(model_name="qwen2.5-coder:14b")

        self.client.start_session(self.system_prompt)

    def _read_java_files(self) -> str:
        java_code = ""
        if not os.path.exists(self.repo_path):
            return "Error: Path not found."

        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".java"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r") as f:
                            content = f.read()
                            # Optimization: remove imports to save context tokens
                            lines = [line for line in content.splitlines() if
                                     not line.strip().startswith("import") and not line.strip().startswith("package")]
                            java_code += f"\n// File: {file}\n" + "\n".join(lines) + "\n"
                    except Exception:
                        pass
        return java_code[:100000]

    def generate_diagram(self) -> str:
        prompt = "Output the mermaid code now."
        raw_response = self.client.ask(prompt)
        return self._final_sanitizer(raw_response)

    def _final_sanitizer(self, text: str) -> str:
        """
        Brute-force cleanup for any remaining Java artifacts.
        """
        # 1. Strip Markdown
        text = text.replace("```mermaid", "").replace("```", "").strip()

        # 2. Force Header
        if "classDiagram" not in text:
            text = "classDiagram\n" + text

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # 3. Remove Lines that look like Java imports or packages (common hallucination)
            if line.strip().startswith("import ") or line.strip().startswith("package "):
                continue

            # 4. BRUTE FORCE: Replace all < and > with ~
            # This is safer than regex. If it's in the diagram, it's a generic.
            # Mermaid doesn't use < or > for anything except relationships ( handled below )

            # Temporarily hide relationships to protect them
            line = line.replace("--|>", "##INHERIT##").replace("..|>", "##IMPL##")

            # Nuke the brackets
            line = line.replace("<", "~").replace(">", "~")

            # Restore relationships
            line = line.replace("##INHERIT##", "--|>").replace("##IMPL##", "..|>")

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)
