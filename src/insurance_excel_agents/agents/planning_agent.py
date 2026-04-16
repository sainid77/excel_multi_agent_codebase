from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from insurance_excel_agents.llm.client import LLMClient


@dataclass
class PlanningAgent:
    use_llm: bool = True

    def __post_init__(self) -> None:
        self.llm = None
        if self.use_llm:
            try:
                self.llm = LLMClient()
            except Exception:
                self.llm = None

    def run(self, intake_result: dict[str, Any]) -> dict[str, Any]:
        if self.llm is None:
            return {
                "execution_order": [
                    "intake",
                    "schema",
                    "lineage",
                    "macros",
                    "dependencies",
                    "business_rules",
                    "api_synthesis",
                ],
                "optional_agents": ["execution_trace", "forecast_interpretation", "code_generation"],
                "reasons": ["Fallback planner without LLM."],
            }

        prompt = f"""
Given this intake result, decide which agents should run and in what order.

Intake Result:
{json.dumps(intake_result, indent=2, default=str)[:12000]}

Return strict JSON:
{{
  "execution_order": ["string"],
  "optional_agents": ["string"],
  "reasons": ["string"]
}}
"""
        text = self.llm.complete(
            system_prompt="You are a planning agent for a multi-agent Excel modernization system. Return valid JSON only.",
            user_prompt=prompt,
        )

        try:
            return json.loads(text)
        except Exception:
            return {
                "execution_order": [
                    "intake",
                    "schema",
                    "lineage",
                    "macros",
                    "dependencies",
                    "business_rules",
                    "api_synthesis",
                ],
                "optional_agents": ["execution_trace", "forecast_interpretation", "code_generation"],
                "reasons": ["LLM planner returned invalid JSON; fallback applied."],
            }