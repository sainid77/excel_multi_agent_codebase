from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from insurance_excel_agents.parsers.reference_parser import ReferenceParser


@dataclass
class InterWorkbookDependencyAgent:
    """
    Builds cross-reference intelligence from schema inventory.

    Output includes:
    - cross_references: detailed row-level references
    - file_level_edges: aggregated workbook-to-workbook links
    """

    parser: ReferenceParser = field(default_factory=ReferenceParser)

    def run(self, schema_inventory: dict[str, Any]) -> dict[str, Any]:
        edges: list[dict[str, Any]] = []

        inventory = schema_inventory.get("inventory", []) if isinstance(schema_inventory, dict) else []

        for workbook in inventory:
            workbook_name = workbook.get("workbook_name", "unknown_workbook")

            for sheet in workbook.get("sheets", []) or []:
                sheet_name = sheet.get("sheet_name", "unknown_sheet")

                for formula_item in sheet.get("formulas", []) or []:
                    cell = (
                        formula_item.get("cell")
                        or formula_item.get("address")
                        or formula_item.get("target")
                        or "unknown_cell"
                    )
                    formula = formula_item.get("formula", "")

                    refs = self.parser.extract_references(
                        formula=formula,
                        current_workbook=workbook_name,
                        current_sheet=sheet_name,
                        current_cell=cell,
                    )
                    edges.extend(refs)

        file_edges = self._aggregate_file_edges(edges)

        return {
            "cross_references": edges,
            "file_level_edges": file_edges,
        }

    def _aggregate_file_edges(self, edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Aggregate detailed references into workbook-level edges.
        """
        agg: dict[tuple[str, str], int] = {}

        for edge in edges:
            src = edge.get("source_workbook", "unknown_source")
            tgt = edge.get("target_workbook", "unknown_target")
            dep_type = edge.get("dependency_type", "unknown")

            # Ignore same-workbook non-cross-workbook edges at file level
            if src == tgt and dep_type != "cross_workbook":
                continue

            agg[(src, tgt)] = agg.get((src, tgt), 0) + 1

        return [
            {
                "source_workbook": src,
                "target_workbook": tgt,
                "reference_count": count,
            }
            for (src, tgt), count in agg.items()
        ]