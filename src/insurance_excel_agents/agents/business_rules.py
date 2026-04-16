from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from insurance_excel_agents.llm.client import LLMClient


def _compact_json(data: Any, max_chars: int = 12000) -> str:
    text = json.dumps(data, indent=2, default=str)
    return text[:max_chars]


@dataclass
class BusinessRuleExtractionAgent:
    use_llm: bool = True

    def __post_init__(self) -> None:
        self.llm = None
        if self.use_llm:
            try:
                self.llm = LLMClient()
            except Exception:
                self.llm = None

    def run(self, schema_inventory: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
        if self.llm is None:
            return self._fallback(schema_inventory, lineage)

        prompt = f"""
Analyze this Excel workbook-derived schema and lineage.

Schema Inventory:
{_compact_json(schema_inventory)}

Lineage:
{_compact_json(lineage)}

Return strict JSON with this shape:
{{
  "rules": [
    {{
      "rule_name": "string",
      "business_meaning": "string",
      "inputs": ["string"],
      "outputs": ["string"],
      "confidence": 0.0
    }}
  ],
  "summary": "string"
}}
"""
        text = self.llm.complete(
            system_prompt="You extract business rules from spreadsheet logic and return valid JSON only.",
            user_prompt=prompt,
        )

        try:
            parsed = json.loads(text)
            return parsed
        except Exception:
            return {
                "rules_text": text,
                "summary": "LLM returned non-JSON output; captured raw text instead."
            }

    def _fallback(self, schema_inventory: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
        rules = []
        inventory = schema_inventory.get("inventory", []) if isinstance(schema_inventory, dict) else []
        for wb in inventory[:5]:
            workbook_name = wb.get("workbook_name", "unknown_workbook")
            rules.append(
                {
                    "rule_name": f"{workbook_name}_summary_logic",
                    "business_meaning": "Workbook appears to contain formula-driven business logic.",
                    "inputs": ["workbook sheets", "cell formulas"],
                    "outputs": ["summary metrics", "derived calculations"],
                    "confidence": 0.6,
                }
            )

        return {
            "rules": rules,
            "summary": "Fallback rules extracted without an LLM."
        }