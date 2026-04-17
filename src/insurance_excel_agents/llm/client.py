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

    def safe_chat(
        self,
        messages,
        retries: int = 3,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ):
        for i in range(retries):
            try:
                return self.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception:
                if i == retries - 1:
                    raise
                time.sleep(2)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.safe_chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def complete(
        self,
        prompt: str | None = None,
        system_prompt: str | None = None,
        user_prompt: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ):
        """
        Backward-compatible wrapper that supports both:

        1) llm.complete(prompt="...")
        2) llm.complete(system_prompt="...", user_prompt="...")
        """

        if system_prompt is not None or user_prompt is not None:
            messages = []
            if system_prompt is not None:
                messages.append({"role": "system", "content": system_prompt})
            if user_prompt is not None:
                messages.append({"role": "user", "content": user_prompt})

            return self.safe_chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if prompt is not None:
            messages = [{"role": "user", "content": prompt}]
            return self.safe_chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        raise ValueError("Either prompt or system_prompt/user_prompt must be provided.")