import os
import time
from openai import OpenAI


class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=api_key)

    def chat(self, messages, temperature: float = 0.2, max_tokens: int = 1500):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    def safe_chat(self, messages, retries=3):
        for i in range(retries):
            try:
                return self.chat(messages)
            except Exception as e:
                if i == retries - 1:
                    raise e
                time.sleep(2)

    def generate(self, system_prompt: str, user_prompt: str):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.safe_chat(messages)