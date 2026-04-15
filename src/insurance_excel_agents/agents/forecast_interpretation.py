from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class ForecastInterpretationAgent:
    """
    Converts execution trace + API contract into a business-readable report.
    """

    def run(
        self,
        execution_trace: dict[str, Any],
        api_contract: dict[str, Any],
        output_dir: str | Path,
    ) -> dict[str, Any]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        workbook_name = execution_trace.get("workbook_name", "unknown_workbook")
        summary = execution_trace.get("summary", {})
        risks = execution_trace.get("risks", [])
        outputs = execution_trace.get("outputs", [])
        macro_steps = execution_trace.get("macro_steps", [])
        formula_steps = execution_trace.get("formula_steps", [])

        endpoints = (
            api_contract.get("endpoints")
            or api_contract.get("apis")
            or api_contract.get("routes")
            or []
        )

        interpretation = {
            "workbook_name": workbook_name,
            "executive_summary": self._executive_summary(
                workbook_name=workbook_name,
                summary=summary,
                endpoint_count=len(endpoints),
            ),
            "business_interpretation": {
                "workflow_type": self._infer_workflow_type(outputs, macro_steps),
                "forecast_horizon": self._infer_forecast_horizon(outputs, formula_steps),
                "likely_output_destinations": [o.get("target") for o in outputs[:25] if isinstance(o, dict)],
                "api_candidates": [self._endpoint_name(e) for e in endpoints],
            },
            "controls_and_risks": risks,
            "recommendations": self._recommendations(risks, endpoints, macro_steps),
        }

        json_file = output_path / "forecast_interpretation.json"
        md_file = output_path / "forecast_interpretation.md"

        json_file.write_text(json.dumps(interpretation, indent=2), encoding="utf-8")
        md_file.write_text(self._to_markdown(interpretation), encoding="utf-8")

        return interpretation

    def _endpoint_name(self, endpoint: Any) -> str:
        if isinstance(endpoint, dict):
            return str(endpoint.get("path") or endpoint.get("name") or endpoint.get("endpoint") or endpoint)
        return str(endpoint)

    def _executive_summary(self, workbook_name: str, summary: dict[str, Any], endpoint_count: int) -> str:
        return (
            f"The workbook '{workbook_name}' appears to implement a forecast or analytical workflow. "
            f"The analysis identified {summary.get('input_count', 0)} candidate inputs, "
            f"{summary.get('formula_step_count', 0)} formula-driven computation steps, "
            f"{summary.get('macro_step_count', 0)} macro procedures, and {endpoint_count} synthesized API candidates. "
            f"This indicates the workbook can be documented, monitored, and incrementally migrated into cloud services."
        )

    def _infer_workflow_type(self, outputs: list[dict[str, Any]], macro_steps: list[dict[str, Any]]) -> str:
        targets = " ".join(str(o.get("target", "")).lower() for o in outputs if isinstance(o, dict))
        if "forecast" in targets:
            return "forecast_generation"
        if any(isinstance(step, dict) and step.get("writes") for step in macro_steps):
            return "macro_orchestrated_analysis"
        return "spreadsheet_analytics"

    def _infer_forecast_horizon(
        self,
        outputs: list[dict[str, Any]],
        formula_steps: list[dict[str, Any]],
    ) -> str:
        joined = " ".join(str(o.get("target", "")) for o in outputs if isinstance(o, dict))
        joined += " "
        joined += " ".join(str(s.get("target", "")) for s in formula_steps[:100] if isinstance(s, dict))
        text = joined.lower()
        if any(token in text for token in ["12", "1yr", "1_year", "12m", "12_month"]):
            return "1 year"
        return "not_explicitly_detected"

    def _recommendations(
        self,
        risks: list[str],
        endpoints: list[Any],
        macro_steps: list[dict[str, Any]],
    ) -> list[str]:
        recs = [
            "Externalize workbook inputs into a formal API request schema.",
            "Persist forecast outputs into a database table for auditability.",
            "Generate unit tests for formula-equivalent service logic.",
        ]
        if risks:
            recs.append("Address external file paths and volatile formulas before cloud migration.")
        if macro_steps:
            recs.append("Convert macro procedures into explicit service-layer orchestration steps.")
        if endpoints:
            recs.append("Use the synthesized API contract as the migration starting point.")
        return recs

    def _to_markdown(self, interpretation: dict[str, Any]) -> str:
        lines = [
            "# Forecast Interpretation Report",
            "",
            "## Executive Summary",
            interpretation["executive_summary"],
            "",
            "## Business Interpretation",
        ]
        for key, value in interpretation["business_interpretation"].items():
            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        lines += ["", "## Controls and Risks"]
        for risk in interpretation.get("controls_and_risks", []):
            lines.append(f"- {risk}")
        lines += ["", "## Recommendations"]
        for rec in interpretation.get("recommendations", []):
            lines.append(f"- {rec}")
        return "\n".join(lines)