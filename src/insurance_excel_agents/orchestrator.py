from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from insurance_excel_agents.config import AnalysisConfig

# Core agents
from insurance_excel_agents.agents.intake import WorkbookIntakeAgent
from insurance_excel_agents.agents.schema import WorkbookSchemaAgent
from insurance_excel_agents.agents.lineage import FormulaLineageAgent
from insurance_excel_agents.agents.macros import MacroParsingAgent
from insurance_excel_agents.agents.dependencies import DependencyResolverAgent
from insurance_excel_agents.agents.business_rules import BusinessRuleExtractionAgent
from insurance_excel_agents.agents.api_synthesis import ApiSynthesisAgent

# LLM / advanced agents
from insurance_excel_agents.agents.planning_agent import PlanningAgent
from insurance_excel_agents.agents.execution_trace import ExecutionTraceAgent
from insurance_excel_agents.agents.forecast_interpretation import ForecastInterpretationAgent
from insurance_excel_agents.agents.validation_agent import ValidationAgent
from insurance_excel_agents.agents.lineage_graph_agent import LineageGraphAgent
from insurance_excel_agents.agents.code_generation_agent import CodeGenerationAgent

# Optional cross-workbook visualization agents
try:
    from insurance_excel_agents.agents.interworkbook_dependencies import InterWorkbookDependencyAgent
except Exception:
    class InterWorkbookDependencyAgent:  # type: ignore
        def run(self, schema_inventory: dict[str, Any]) -> dict[str, Any]:
            return {
                "cross_references": [],
                "file_level_edges": [],
            }

try:
    from insurance_excel_agents.agents.workbook_flow_graph import WorkbookFlowGraphAgent
except Exception:
    class WorkbookFlowGraphAgent:  # type: ignore
        def run(self, interworkbook_result: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
            return {
                "nodes": [],
                "edges": [],
            }


@dataclass
class Orchestrator:
    def __post_init__(self) -> None:
        # Core deterministic agents
        self.intake_agent = WorkbookIntakeAgent()
        self.schema_agent = WorkbookSchemaAgent()
        self.lineage_agent = FormulaLineageAgent()
        self.macro_agent = MacroParsingAgent()
        self.dependency_agent = DependencyResolverAgent()
        self.business_rules_agent = BusinessRuleExtractionAgent()
        self.api_agent = ApiSynthesisAgent()

        # LLM / higher-order agents
        self.planning_agent = PlanningAgent()
        self.execution_trace_agent = ExecutionTraceAgent()
        self.forecast_interpretation_agent = ForecastInterpretationAgent()
        self.validation_agent = ValidationAgent()
        self.graph_agent = LineageGraphAgent()
        self.codegen_agent = CodeGenerationAgent()

        # Cross-workbook / visualization agents
        self.interworkbook_agent = InterWorkbookDependencyAgent()
        self.workbook_flow_graph_agent = WorkbookFlowGraphAgent()

    # -------------------------
    # Helpers
    # -------------------------
    def _to_path(self, p: Any) -> Path:
        if isinstance(p, Path):
            return p
        if isinstance(p, str):
            return Path(p)
        raise TypeError(f"Cannot convert to Path: {type(p).__name__}")

    def _extract_workbook_paths(self, intake_result: Any) -> List[Path]:
        """
        Normalize intake output into List[Path].

        Supports:
        - {"workbook_paths": ["/a.xlsm", "/b.xlsm"]}
        - {"workbook_paths": [{"path": "/a.xlsm"}, {"file_path": "/b.xlsm"}]}
        - {"files": [...]}
        - {"inventory": [{"path": ...}, ...]}
        - {"workbooks": [...]}
        - {"paths": [...]}
        """
        if not isinstance(intake_result, dict):
            return []

        candidates: list[Any] = []

        for key in ("workbook_paths", "files", "inventory", "workbooks", "paths"):
            value = intake_result.get(key)
            if isinstance(value, list):
                candidates = value
                break

        paths: List[Path] = []
        for item in candidates:
            try:
                if isinstance(item, (str, Path)):
                    paths.append(self._to_path(item))
                elif isinstance(item, dict):
                    raw = (
                        item.get("path")
                        or item.get("file_path")
                        or item.get("workbook_path")
                        or item.get("source_path")
                        or item.get("filename")
                    )
                    if raw:
                        paths.append(self._to_path(raw))
            except Exception:
                continue

        return paths

    # -------------------------
    # Core pipeline
    # -------------------------
    def run(self, config: AnalysisConfig) -> dict[str, Any]:
        bundle_dir = self._to_path(config.bundle_dir)
        output_dir = self._to_path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1) Intake
        intake_result = self.intake_agent.run(
            bundle_dir=bundle_dir,
            recurse=bool(config.recurse),
        )

        # 2) Planning
        try:
            plan_result = self.planning_agent.run(intake_result)
        except Exception as exc:
            plan_result = {
                "status": "planner_failed",
                "reason": str(exc),
                "execution_order": [],
                "optional_agents": [],
            }

        # 3) Workbook paths
        workbook_paths = self._extract_workbook_paths(intake_result)

        # 4) Schema
        schema_result = self.schema_agent.run(workbook_paths)

        # 5) Formula lineage
        lineage_result = self.lineage_agent.run(schema_result)

        # 6) Macros
        macro_result = self.macro_agent.run(workbook_paths)

        # 7) Dependencies
        dependency_result = self.dependency_agent.run(
            schema_result,
            lineage_result,
            macro_result,
        )

        # 8) Cross-workbook references
        interworkbook_result = self.interworkbook_agent.run(schema_result)

        # 9) Business rules
        business_rules_result = self.business_rules_agent.run(
            schema_result,
            lineage_result,
        )

        # 10) API synthesis
        api_result = self.api_agent.run(
            schema_result,
            business_rules_result,
        )

        return {
            "bundle_dir": str(bundle_dir),
            "output_dir": str(output_dir),
            "workbook_paths": [str(p) for p in workbook_paths],
            "intake": intake_result,
            "plan": plan_result,
            "schema_inventory": schema_result,
            "formula_lineage": lineage_result,
            "macro_inventory": macro_result,
            "dependency_inventory": dependency_result,
            "interworkbook_dependencies": interworkbook_result,
            "business_rules": business_rules_result,
            "api_contract": api_result,
        }

    # -------------------------
    # Full pipeline
    # -------------------------
    def run_full(self, config: AnalysisConfig) -> dict[str, Any]:
        base = self.run(config)
        output_dir = self._to_path(base["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        # Execution trace
        execution_trace = self.execution_trace_agent.run(
            schema_inventory=base.get("schema_inventory", {}),
            formula_lineage=base.get("formula_lineage", {}),
            macro_inventory=base.get("macro_inventory", {}),
            dependency_inventory=base.get("dependency_inventory", {}),
            output_dir=str(output_dir),
        )

        # Stakeholder-friendly interpretation
        forecast_interpretation = self.forecast_interpretation_agent.run(
            execution_trace=execution_trace,
            api_contract=base.get("api_contract", {}),
            output_dir=str(output_dir),
        )

        # Validation
        try:
            validation_result = self.validation_agent.run(str(output_dir))
        except Exception as exc:
            validation_result = {
                "status": "skipped",
                "reason": str(exc),
            }

        # Entity graph
        try:
            graph_result = self.graph_agent.run(str(output_dir))
        except Exception as exc:
            graph_result = {
                "status": "skipped",
                "reason": str(exc),
            }

        # Workbook flow graph
        try:
            workbook_flow_graph = self.workbook_flow_graph_agent.run(
                base.get("interworkbook_dependencies", {}),
                str(output_dir),
            )
        except Exception as exc:
            workbook_flow_graph = {
                "status": "skipped",
                "reason": str(exc),
                "nodes": [],
                "edges": [],
            }

        # Code generation
        codegen_result = self.codegen_agent.run(
            output_dir=str(output_dir),
            api_contract=base.get("api_contract", {}),
            business_rules=base.get("business_rules", {}),
        )

        return {
            **base,
            "execution_trace": execution_trace,
            "forecast_interpretation": forecast_interpretation,
            "validation": validation_result,
            "graph": graph_result,
            "workbook_flow_graph": workbook_flow_graph,
            "codegen": codegen_result,
            "status": "completed",
        }