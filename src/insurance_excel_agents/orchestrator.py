from __future__ import annotations

from pathlib import Path
from typing import Any

from insurance_excel_agents.config import AnalysisConfig

from insurance_excel_agents.agents.intake import WorkbookIntakeAgent
from insurance_excel_agents.agents.schema import WorkbookSchemaAgent
from insurance_excel_agents.agents.lineage import FormulaLineageAgent
from insurance_excel_agents.agents.macros import MacroParsingAgent
from insurance_excel_agents.agents.dependencies import DependencyResolverAgent
from insurance_excel_agents.agents.business_rules import BusinessRuleExtractionAgent
from insurance_excel_agents.agents.api_synthesis import ApiSynthesisAgent

from insurance_excel_agents.agents.execution_trace import ExecutionTraceAgent
from insurance_excel_agents.agents.forecast_interpretation import ForecastInterpretationAgent
from insurance_excel_agents.agents.execution_agent import ExecutionAgent
from insurance_excel_agents.agents.local_dependency_resolver import LocalDependencyResolverAgent
from insurance_excel_agents.agents.validation_agent import ValidationAgent
from insurance_excel_agents.agents.lineage_graph_agent import LineageGraphAgent
from insurance_excel_agents.agents.code_generation_agent import CodeGenerationAgent


class Orchestrator:
    def __init__(self) -> None:
        self.intake_agent = WorkbookIntakeAgent()
        self.schema_agent = WorkbookSchemaAgent()
        self.lineage_agent = FormulaLineageAgent()
        self.macro_agent = MacroParsingAgent()
        self.dependency_agent = DependencyResolverAgent()
        self.business_rules_agent = BusinessRuleExtractionAgent()
        self.api_agent = ApiSynthesisAgent()

        self.execution_trace_agent = ExecutionTraceAgent()
        self.forecast_interpretation_agent = ForecastInterpretationAgent()
        self.execution_agent = ExecutionAgent()
        self.local_dependency_agent = LocalDependencyResolverAgent()
        self.validation_agent = ValidationAgent()
        self.lineage_graph_agent = LineageGraphAgent()
        self.code_generation_agent = CodeGenerationAgent()

    def _extract_workbook_paths(self, intake_result: Any) -> list[Path]:
        """
        Normalize intake output into list[Path].

        Supports:
        - [Path(...), Path(...)]
        - [".../a.xlsm", ".../b.xlsm"]
        - [{"path": ".../a.xlsm"}, {"file_path": ".../b.xlsm"}]
        - {"workbook_paths": [...]}
        - {"files": [...]}
        - {"paths": [...]}
        - {"workbooks": [...]}
        """
        if isinstance(intake_result, list):
            items = intake_result
        elif isinstance(intake_result, dict):
            items = None
            for key in ("workbook_paths", "files", "paths", "workbooks"):
                value = intake_result.get(key)
                if isinstance(value, list):
                    items = value
                    break
            if items is None:
                raise ValueError(
                    "Could not extract workbook paths from intake result. "
                    f"Available keys: {list(intake_result.keys())}"
                )
        else:
            raise ValueError(
                "Unsupported intake result type: "
                f"{type(intake_result).__name__}"
            )

        paths: list[Path] = []
        for item in items:
            if isinstance(item, Path):
                paths.append(item)
            elif isinstance(item, str):
                paths.append(Path(item))
            elif isinstance(item, dict):
                raw = (
                    item.get("path")
                    or item.get("file_path")
                    or item.get("workbook_path")
                    or item.get("source_path")
                    or item.get("filename")
                )
                if raw:
                    paths.append(Path(raw))

        if not paths:
            raise ValueError("No valid workbook paths found in intake result")

        return paths

    def run(self, config: AnalysisConfig) -> dict[str, Any]:
        bundle_dir = Path(config.bundle_dir)
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        intake_result = self.intake_agent.run(
            bundle_dir=bundle_dir,
            recurse=bool(config.recurse),
        )
        workbook_paths = self._extract_workbook_paths(intake_result)

        schema_result = self.schema_agent.run(workbook_paths)
        lineage_result = self.lineage_agent.run(schema_result)
        macro_result = self.macro_agent.run(workbook_paths)

        dependency_result = self.dependency_agent.run(
            schema_result,
            lineage_result,
            macro_result,
        )

        business_rules_result = self.business_rules_agent.run(
            schema_result,
            lineage_result,
        )

        api_result = self.api_agent.run(
            schema_result,
            business_rules_result,
        )

        return {
            "bundle_dir": str(bundle_dir),
            "output_dir": str(output_dir),
            "workbook_paths": [str(p) for p in workbook_paths],
            "intake": intake_result,
            "schema_inventory": schema_result,
            "formula_lineage": lineage_result,
            "macro_inventory": macro_result,
            "dependency_inventory": dependency_result,
            "business_rules": business_rules_result,
            "api_contract": api_result,
        }

    def run_full(self, config: AnalysisConfig) -> dict[str, Any]:
        base = self.run(config)

        bundle_dir = Path(config.bundle_dir)
        output_dir = Path(config.output_dir)

        execution_trace = self.execution_trace_agent.run(
            schema_inventory=base.get("schema_inventory", {}),
            formula_lineage=base.get("formula_lineage", {}),
            macro_inventory=base.get("macro_inventory", {}),
            dependency_inventory=base.get("dependency_inventory", {}),
            output_dir=output_dir,
        )

        if execution_trace.get("workbook_name") == "unknown_workbook":
            execution_trace["workbook_name"] = bundle_dir.name

        forecast_interpretation = self.forecast_interpretation_agent.run(
            execution_trace=execution_trace,
            api_contract=base.get("api_contract", {}),
            output_dir=output_dir,
        )

        execution_log = self.execution_agent.run(
            str(bundle_dir),
            str(output_dir),
        )

        local_dependencies = self.local_dependency_agent.run(
            str(bundle_dir),
            str(output_dir),
        )

        validation_report = self.validation_agent.run(
            str(output_dir),
        )

        lineage_graph = self.lineage_graph_agent.run(
            str(output_dir),
        )

        generated_code = self.code_generation_agent.run(
            str(output_dir),
        )

        return {
            **base,
            "execution_trace": execution_trace,
            "forecast_interpretation": forecast_interpretation,
            "execution_log": execution_log,
            "local_dependencies": local_dependencies,
            "validation_report": validation_report,
            "lineage_graph": lineage_graph,
            "generated_code": generated_code,
        }