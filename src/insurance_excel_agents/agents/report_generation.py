from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class ReportGenerationAgent:
    def run(self, analysis_bundle: dict, output_dir: Path) -> dict:
        report = {
            "source_workbook": analysis_bundle.get("source_workbook"),
            "target_workbook": analysis_bundle.get("target_workbook"),
            "summary": analysis_bundle.get("summary"),
            "inputs": analysis_bundle.get("inputs", []),
            "forecast_logic": analysis_bundle.get("forecast_logic", []),
            "macros": analysis_bundle.get("macros", []),
            "outputs": analysis_bundle.get("outputs", []),
            "dependencies": analysis_bundle.get("dependencies", []),
            "risks": analysis_bundle.get("risks", []),
            "recommendations": analysis_bundle.get("recommendations", []),
        }

        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "forecast_execution_report.json"
        md_path = output_dir / "forecast_execution_report.md"

        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        md = self._to_markdown(report)
        md_path.write_text(md, encoding="utf-8")

        return {
            "json_report": str(json_path),
            "markdown_report": str(md_path),
        }

    def _to_markdown(self, report: dict) -> str:
        lines = [
            "# Forecast Execution Report",
            "",
            "## Executive Summary",
            report.get("summary", "No summary available."),
            "",
            f"## Source Workbook\n{report.get('source_workbook', 'Unknown')}",
            "",
            f"## Target Workbook\n{report.get('target_workbook', 'Unknown')}",
            "",
            "## Inputs",
        ]
        for item in report.get("inputs", []):
            lines.append(f"- {item}")
        lines += ["", "## Forecast Logic"]
        for item in report.get("forecast_logic", []):
            lines.append(f"- {item}")
        lines += ["", "## Macros"]
        for item in report.get("macros", []):
            lines.append(f"- {item}")
        lines += ["", "## Outputs"]
        for item in report.get("outputs", []):
            lines.append(f"- {item}")
        lines += ["", "## Dependencies"]
        for item in report.get("dependencies", []):
            lines.append(f"- {item}")
        lines += ["", "## Risks"]
        for item in report.get("risks", []):
            lines.append(f"- {item}")
        lines += ["", "## Recommendations"]
        for item in report.get("recommendations", []):
            lines.append(f"- {item}")
        return "\n".join(lines)