from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from insurance_excel_agents.llm.client import LLMClient


def _compact_json(data: Any, max_chars: int = 12000) -> str:
    text = json.dumps(data, indent=2, default=str)
    return text[:max_chars]


@dataclass
class ForecastInterpretationAgent:
    use_llm: bool = True

    def __post_init__(self) -> None:
        self.llm = None
        if self.use_llm:
            try:
                self.llm = LLMClient()
            except Exception:
                self.llm = None

    def run(
        self,
        execution_trace: dict[str, Any],
        api_contract: dict[str, Any],
        output_dir: str | Path,
    ) -> dict[str, Any]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if self.llm is None:
            interpretation = self._fallback(execution_trace, api_contract)
        else:
            interpretation = self._with_llm(execution_trace, api_contract)

        json_file = output_path / "forecast_interpretation.json"
        md_file = output_path / "forecast_interpretation.md"

        json_file.write_text(json.dumps(interpretation, indent=2), encoding="utf-8")
        md_file.write_text(self._to_markdown(interpretation), encoding="utf-8")
        return interpretation

    def _with_llm(self, execution_trace: dict[str, Any], api_contract: dict[str, Any]) -> dict[str, Any]:
        prompt = f"""
Create a stakeholder-friendly executive interpretation.

Execution Trace:
{_compact_json(execution_trace)}

API Contract:
{_compact_json(api_contract)}

Return strict JSON with:
{{
  "executive_summary": "string",
  "business_interpretation": {{
    "workflow_type": "string",
    "forecast_horizon": "string",
    "likely_output_destinations": ["string"],
    "api_candidates": ["string"]
  }},
  "controls_and_risks": ["string"],
  "recommendations": ["string"]
}}
"""
        text = self.llm.complete(
            system_prompt="You are a senior consulting architect. Return valid JSON only.",
            user_prompt=prompt,
        )

        try:
            return json.loads(text)
        except Exception:
            return {
                "executive_summary": text,
                "business_interpretation": {
                    "workflow_type": "excel_model_modernization",
                    "forecast_horizon": "not_explicitly_detected",
                    "likely_output_destinations": [],
                    "api_candidates": [],
                },
                "controls_and_risks": [],
                "recommendations": [],
            }

    def _fallback(self, execution_trace: dict[str, Any], api_contract: dict[str, Any]) -> dict[str, Any]:
        summary = execution_trace.get("summary", {})
        endpoints = api_contract.get("endpoints", []) if isinstance(api_contract, dict) else []
        return {
            "executive_summary": (
                f"The workbook appears to implement an analytical workflow. "
                f"The analysis identified {summary.get('input_count', 0)} candidate inputs, "
                f"{summary.get('formula_step_count', 0)} formula-driven steps, "
                f"{summary.get('macro_step_count', 0)} macro procedures, and {len(endpoints)} synthesized API candidates."
            ),
            "business_interpretation": {
                "workflow_type": "excel_model_modernization",
                "forecast_horizon": "not_explicitly_detected",
                "likely_output_destinations": [],
                "api_candidates": [
                    ep.get("path", str(ep)) if isinstance(ep, dict) else str(ep)
                    for ep in endpoints
                ],
            },
            "controls_and_risks": [],
            "recommendations": [
                "Add LLM reasoning for richer stakeholder summaries.",
                "Convert workbook logic into deployable services.",
            ],
        }

    def _to_markdown(self, interpretation: dict[str, Any]) -> str:
        lines = [
            "# Forecast Interpretation Report",
            "",
            "## Executive Summary",
            interpretation.get("executive_summary", ""),
            "",
            "## Business Interpretation",
        ]
        for key, value in interpretation.get("business_interpretation", {}).items():
            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        lines += ["", "## Controls and Risks"]
        for risk in interpretation.get("controls_and_risks", []):
            lines.append(f"- {risk}")
        lines += ["", "## Recommendations"]
        for rec in interpretation.get("recommendations", []):
            lines.append(f"- {rec}")
        return "\n".join(lines)