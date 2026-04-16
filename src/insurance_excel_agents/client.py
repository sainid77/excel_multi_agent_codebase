from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class LLMClient:
    model: str = "gpt-5.4-thinking"

    def __post_init__(self) -> None:
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.output_text