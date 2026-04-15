from __future__ import annotations

from insurance_excel_agents.models import FormulaRecord
from insurance_excel_agents.parsers.formula_analyzer import FormulaAnalyzer


class FormulaLineageAgent:
    def __init__(self) -> None:
        self.analyzer = FormulaAnalyzer()

    def run(self, schema_inventory: dict) -> dict:
        records: list[FormulaRecord] = []
        for workbook in schema_inventory.get("inventory", []):
            for item in workbook.get("formulas", []):
                records.append(FormulaRecord(**item))
        dependencies = self.analyzer.build_dependencies(records)
        return {
            "formulas": [record.model_dump() for record in records],
            "dependencies": [dep.model_dump() for dep in dependencies],
        }
