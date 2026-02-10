import os
import json
from src.shared.llm_clients import GoogleClient, OllamaClient


class MongoAgent:
    def __init__(self, schema_path: str, provider: str):
        self.schema_path = schema_path
        self.provider = provider.lower()

        print(f"🍃 mongo-agent: Loading schema from {schema_path}...")
        schema_context = self._read_schema_file()

        # --- SYSTEM PROMPT ---
        # Specialized for Document Stores (No Joins, specific aggregation syntax)
        self.system_prompt = f"""
You are a Principal NoSQL Engineer specialized in MongoDB.
Your goal is to translate natural language questions into valid MongoDB Shell queries.

**DATABASE STRUCTURE (Sample Documents):**
{schema_context}

**RULES:**
🎯 Grounding
Use only the collections and fields defined in the provided schema. Reject or reinterpret any request involving nonexistent collections or fields. Never invent structure or relationships.
🍃 Syntax
Generate valid MongoDB Shell syntax only.
Use db.collection.find({...}) for simple filters.
Use db.collection.aggregate([...]) for grouping, counting, sorting, projections, or array operations.
Use correct operators ($match, $group, $project, $unwind, $sort, $limit, $lookup, $addFields, $expr).
🔎 Logic
Use find() when the request is a simple lookup, filter, or direct field comparison.
Use aggregate() when the request involves grouping, counting, summing, averaging, joining, array unwinding, or multi‑stage logic.
Use $count or $group for “how many”, “number of”, “unique”, or “distinct” queries.
Use $sort and $limit for “top”, “highest”, “latest”, or “most recent”.
📅 Dates
Use ISODate("YYYY-MM-DD") for date comparisons.
Use $gte, $lte, $gt, $lt, or $between-equivalent logic via $and.
Never compare dates as strings.
🧪 Edge Handling
If the user’s request is ambiguous, choose the safest valid interpretation using only available fields.
If the user references missing fields, reinterpret using valid ones.
If the request is impossible with the schema, return the closest valid query.
❌ Strictness
No write operations (insert, update, delete, replace, bulkWrite).
No schema creation or modification.
No comments in output.
No explanations, no markdown, no prose.
Output only the raw MongoDB Shell code.
📄 Output
Return only the MongoDB query.
"""

        # --- CLIENT INITIALIZATION ---
        if "google" in self.provider:
            self.client = GoogleClient(model_name="gemini-3-flash-preview")
        else:
            # Qwen 2.5 Coder 14B is excellent at MongoDB syntax
            self.client = OllamaClient(model_name="qwen2.5-coder:14b")

        self.client.start_session(self.system_prompt)

    def _read_schema_file(self) -> str:
        if not os.path.exists(self.schema_path):
            return "ERROR: Schema file not found."

        try:
            with open(self.schema_path, "r") as f:
                # We validate that it's real JSON before feeding it to the AI
                data = json.load(f)
                return json.dumps(data, indent=2)
        except Exception as e:
            return f"ERROR: Could not parse schema JSON. {e}"

    def ask(self, user_question: str) -> str:
        # 1. GENERATE
        raw_response = self.client.ask(user_question)

        # 2. FORMATTING (Simple cleanup)
        # We don't use sqlglot here because it doesn't support Mongo.
        # We rely on the LLM's high accuracy for JS/JSON syntax.
        clean_code = raw_response.replace("```javascript", "").replace("```json", "").replace("```", "").strip()

        return clean_code
