from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json


@dataclass
class ExecutionTraceAgent:
    """
    Builds a static execution trace from workbook analysis artifacts.
    """

    workbook_name: str | None = None

    def run(
        self,
        schema_inventory: dict[str, Any],
        formula_lineage: dict[str, Any],
        macro_inventory: dict[str, Any],
        dependency_inventory: dict[str, Any],
        output_dir: str | Path,
    ) -> dict[str, Any]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        workbook_name = self.workbook_name or schema_inventory.get("workbook_name", "unknown_workbook")

        trace = {
            "workbook_name": workbook_name,
            "trace_mode": "static_analysis",
            "inputs": self._infer_inputs(schema_inventory),
            "formula_steps": self._infer_formula_steps(formula_lineage),
            "macro_steps": self._infer_macro_steps(macro_inventory),
            "dependencies": self._infer_dependencies(dependency_inventory),
            "outputs": self._infer_outputs(schema_inventory, formula_lineage),
            "risks": self._infer_risks(formula_lineage, macro_inventory, dependency_inventory),
        }

        trace["summary"] = {
            "input_count": len(trace["inputs"]),
            "formula_step_count": len(trace["formula_steps"]),
            "macro_step_count": len(trace["macro_steps"]),
            "dependency_count": len(trace["dependencies"]),
            "output_count": len(trace["outputs"]),
            "risk_count": len(trace["risks"]),
        }

        json_file = output_path / "execution_trace.json"
        json_file.write_text(json.dumps(trace, indent=2), encoding="utf-8")

        return trace

    def _infer_inputs(self, schema_inventory: dict[str, Any]) -> list[dict[str, Any]]:
        inputs: list[dict[str, Any]] = []

        sheets = schema_inventory.get("sheets", [])
        if isinstance(sheets, dict):
            iterable = [{"sheet_name": k, **(v if isinstance(v, dict) else {})} for k, v in sheets.items()]
        else:
            iterable = sheets

        for sheet in iterable:
            sheet_name = sheet.get("sheet_name", "Unknown")
            for cell in sheet.get("cells", []):
                if not cell.get("formula") and cell.get("value") not in (None, ""):
                    inputs.append(
                        {
                            "sheet": sheet_name,
                            "address": cell.get("address"),
                            "value": cell.get("value"),
                            "input_type": "literal_or_seed_value",
                        }
                    )

        return inputs[:200]

    def _infer_formula_steps(self, formula_lineage: dict[str, Any]) -> list[dict[str, Any]]:
        lineage_items = (
            formula_lineage.get("lineage")
            or formula_lineage.get("formulas")
            or formula_lineage.get("dependencies")
            or []
        )

        steps: list[dict[str, Any]] = []
        for item in lineage_items:
            if not isinstance(item, dict):
                continue
            steps.append(
                {
                    "target": item.get("target") or item.get("cell"),
                    "depends_on": item.get("depends_on", []),
                    "formula": item.get("formula"),
                    "step_type": "formula_evaluation",
                }
            )
        return steps[:500]

    def _infer_macro_steps(self, macro_inventory: dict[str, Any]) -> list[dict[str, Any]]:
        procedures = macro_inventory.get("procedures") or macro_inventory.get("macros") or []

        steps: list[dict[str, Any]] = []
        for proc in procedures:
            if not isinstance(proc, dict):
                continue
            steps.append(
                {
                    "procedure": proc.get("name") or proc.get("procedure"),
                    "module": proc.get("module"),
                    "reads": proc.get("reads", []),
                    "writes": proc.get("writes", []),
                    "external_calls": proc.get("external_calls", []),
                    "step_type": "macro_execution",
                }
            )
        return steps

    def _infer_dependencies(self, dependency_inventory: dict[str, Any]) -> list[dict[str, Any]]:
        deps = dependency_inventory.get("dependencies", [])
        return deps if isinstance(deps, list) else []

    def _infer_outputs(
        self,
        schema_inventory: dict[str, Any],
        formula_lineage: dict[str, Any],
    ) -> list[dict[str, Any]]:
        outputs: list[dict[str, Any]] = []

        lineage_items = (
            formula_lineage.get("lineage")
            or formula_lineage.get("formulas")
            or formula_lineage.get("dependencies")
            or []
        )
        formula_targets = set()
        for item in lineage_items:
            if isinstance(item, dict):
                tgt = item.get("target") or item.get("cell")
                if tgt:
                    formula_targets.add(tgt)

        for target in sorted(formula_targets):
            outputs.append({"target": target, "output_type": "formula_result"})

        sheets = schema_inventory.get("sheets", [])
        if isinstance(sheets, dict):
            sheet_names = list(sheets.keys())
        else:
            sheet_names = [s.get("sheet_name", "") for s in sheets if isinstance(s, dict)]

        for sheet_name in sheet_names:
            if str(sheet_name).lower() in {"summary", "trends", "forecast", "output", "results"}:
                outputs.append({"target": sheet_name, "output_type": "reporting_sheet"})

        return outputs[:200]

    def _infer_risks(
        self,
        formula_lineage: dict[str, Any],
        macro_inventory: dict[str, Any],
        dependency_inventory: dict[str, Any],
    ) -> list[str]:
        risks: list[str] = []

        lineage_items = (
            formula_lineage.get("lineage")
            or formula_lineage.get("formulas")
            or formula_lineage.get("dependencies")
            or []
        )
        for item in lineage_items:
            if not isinstance(item, dict):
                continue
            formula = str(item.get("formula") or "").upper()
            target = item.get("target") or item.get("cell")
            if "INDIRECT(" in formula or "OFFSET(" in formula:
                risks.append(f"Volatile or indirect formula detected at {target}")

        procedures = macro_inventory.get("procedures") or macro_inventory.get("macros") or []
        for proc in procedures:
            if not isinstance(proc, dict):
                continue
            for call in proc.get("external_calls", []):
                risks.append(f"External macro dependency detected in {proc.get('name') or proc.get('procedure')}: {call}")

        deps = dependency_inventory.get("dependencies", [])
        for dep in deps:
            if not isinstance(dep, dict):
                continue
            dep_type = dep.get("dependency_type", "")
            if dep_type in {"local_file", "external_workbook", "network_path"}:
                risks.append(f"External dependency detected: {dep}")

        return list(dict.fromkeys(risks))