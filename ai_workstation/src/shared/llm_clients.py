import os
import ollama
from google import genai
from google.genai import types


# --- GOOGLE CLIENT (Simple) ---
class GoogleClient:
    def __init__(self, model_name="gemini-3-flash-preview", tools=None):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = model_name
        self.chat = None

    def start_session(self, system_instruction: str):
        # Gemini handles context natively
        self.chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )

    def ask(self, prompt: str) -> str:
        return self.chat.send_message(prompt).text


# --- OLLAMA CLIENT (The "Dumb Pipe" Fix) ---
class OllamaClient:
    def __init__(self, model_name="qwen2.5-coder:14b", tools=None):
        # We accept 'tools' arg for compatibility, but we IGNORE it.
        # This prevents errors if agent_logic.py passes it.
        self.model_name = model_name
        self.messages = []

    def start_session(self, system_instruction: str):
        # The 'system_instruction' now contains the huge context string
        self.messages = [{"role": "system", "content": system_instruction}]
        print(f"🔹 Session started with {self.model_name}")

    def ask(self, prompt: str) -> str:
        print(f"🔹 Sending prompt to Ollama...")
        self.messages.append({"role": "user", "content": prompt})

        # SINGLE CALL - NO LOOPS
        # This might take 2-5 seconds to process the context
        response = ollama.chat(
            model=self.model_name,
            messages=self.messages
        )

        print("✅ Response received from Ollama!")
        content = response.message.content
        self.messages.append(response.message)

        return content
