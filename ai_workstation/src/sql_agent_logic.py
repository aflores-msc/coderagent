import sqlglot
from src.shared.llm_clients import GoogleClient, OllamaClient


class BigQueryAgent:
    def __init__(self, schema_content: str, provider: str):
        # 1. READ SCHEMA
        print(f"📄 sql-agent: Loading schema from content...")
        schema_context = schema_content

        # 2. UNIFIED SYSTEM PROMPT (Works for Qwen & Gemini)
        self.system_prompt = f"""
You are a Principal Data Engineer.
Your goal is to translate natural language questions into valid BigQuery SQL.

**DATABASE SCHEMA:**
{schema_context}

**RULES:**
🎯 Grounding
Use only the tables and columns explicitly provided in the schema.
Reject or reinterpret any request involving nonexistent fields.
Never invent tables, columns, or relationships.
⚡ Dialect
Use GoogleSQL (Standard SQL).
Always include fully qualified column references when ambiguity exists.
Use SAFE_CAST when type conversion is implied.
Use UNNEST correctly for array fields.
🛑 Safety
Generate only SELECT queries.
Never produce INSERT, UPDATE, DELETE, MERGE, DROP, or DDL.
Never use scripting (DECLARE, BEGIN, END).
Never call external functions or remote services.
🧠 Semantic Reasoning
Interpret “revenue” as price * quantity when both columns exist.
Interpret “count of X” as COUNT(X) or COUNT(*) depending on context.
Interpret “unique” as COUNT(DISTINCT ...).
Interpret “latest” as ordering by a timestamp column descending.
Interpret “top”, “highest”, “largest” as ORDER BY ... DESC LIMIT n.
Interpret “filter by date range” using BETWEEN or explicit comparisons.
Interpret “group by” concepts (per user, per day, per product) using GROUP BY.
Infer joins only when a valid foreign‑key‑like relationship exists in the schema.
📏 Query Quality
Use readable formatting: SELECT → FROM → JOIN → WHERE → GROUP BY → HAVING → ORDER BY → LIMIT.
Use aliases for long table names.
Avoid unnecessary subqueries.
Avoid SELECT *.
Prefer explicit column lists.
🧪 Edge Cases
If the user asks for impossible or ambiguous logic, choose the safest valid interpretation.
If the user references missing fields, reinterpret using available ones.
If the user asks for metrics requiring unavailable data, return the closest valid query.
❌ Strictness
No comments in SQL.
No explanations.
No prose.
Output only the raw SQL query.
🧾 Output Format
Return only the SQL query, nothing else.
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
