import os
import sqlglot
from src.shared.llm_clients import GoogleClient, OllamaClient


class BigQueryAgent:
    def __init__(self, schema_path: str, provider: str):
        self.schema_path = schema_path

        # 1. READ SCHEMA
        print(f"📄 sql-agent: Loading schema from {schema_path}...")
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Schema file not found at {self.schema_path}")

        with open(self.schema_path, "r") as f:
            schema_context = f.read()

        # 2. UNIFIED SYSTEM PROMPT (Works for Qwen & Gemini)
        self.system_prompt = f"""
You are a Principal Data Engineer.
Your goal is to translate natural language questions into valid BigQuery SQL.

**DATABASE SCHEMA:**
{schema_context}

**RULES:**
1. 🎯 **Grounding:** ONLY use the tables and columns defined above.
2. ⚡ **Dialect:** Use Standard SQL (GoogleSQL).
3. 🛑 **Safety:** Read-only queries (`SELECT`) only.
4. 🧠 **Reasoning:** If the user asks for "revenue", look for `price * quantity`.
5. **Output:** Return ONLY the raw SQL query.
"""

        # 3. CLIENT SELECTION
        if "google" in provider.lower():
            self.client = GoogleClient(model_name="gemini-3-flash-preview")
        else:
            # Qwen 2.5 Coder 14B is the best local SQL engine for your M4 Pro
            self.client = OllamaClient(model_name="qwen2.5-coder:14b")

        self.client.start_session(self.system_prompt)

    def ask(self, user_question: str) -> str:
        # 1. GENERATE
        raw_response = self.client.ask(user_question)

        # 2. VALIDATE & FORMAT (The safety net)
        return self._validate_and_format(raw_response)

    def _validate_and_format(self, raw_text: str) -> str:
        try:
            # Clean markdown formatting
            clean_sql = raw_text.replace("```sql", "").replace("```", "").strip()

            # Use SQLGlot to Validate and Format
            formatted_sql = sqlglot.transpile(
                clean_sql,
                read="bigquery",
                write="bigquery",
                pretty=True
            )[0]
            return formatted_sql

        except Exception as e:
            return f"⚠️ **Syntax Warning:**\n{e}\n\n```sql\n{raw_text}\n```"
