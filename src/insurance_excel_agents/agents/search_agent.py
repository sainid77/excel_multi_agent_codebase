from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from insurance_excel_agents.llm.client import LLMClient


@dataclass
class SearchAgent:
    llm: LLMClient

    def run(self, results: dict[str, Any], query: str) -> dict[str, Any]:
        matches = self._search_matches(results, query)

        system_prompt = """
You are an expert analyst of Excel workbook intelligence.

Search ONLY across these categories:
- workbooks
- sheets
- dependencies
- formulas
- macros

Do not use API catalog, business rules, executive summary, or other sections.

Answer the user's question clearly and only using the matched data.
If nothing relevant is found, say so.
Keep the answer concise and factual.
"""

        user_prompt = f"""
User Query:
{query}

Matched Structured Data:
{self._matches_to_dict(matches)}
"""

        answer = self.llm.complete(system_prompt, user_prompt)

        return {
            "answer": answer,
            "matches": matches,
            "mode": "llm_workbook_search",
        }

    def _matches_to_dict(self, matches: dict[str, pd.DataFrame]) -> dict[str, list[dict[str, Any]]]:
        return {
            section: df.to_dict(orient="records")
            for section, df in matches.items()
        }

    def _search_matches(self, results: dict[str, Any], query: str) -> dict[str, pd.DataFrame]:
        q = query.strip().lower()
        if not q:
            return {}

        def contains(value: Any) -> bool:
            return q in str(value).lower()

        out: dict[str, pd.DataFrame] = {}

        # Workbooks
        workbooks = results.get("workbook_paths", []) or []
        workbook_rows = [{"Workbook": w} for w in workbooks if contains(w)]
        if workbook_rows:
            out["Workbooks"] = pd.DataFrame(workbook_rows)

        # Sheets
        inventory = results.get("schema_inventory", {}).get("inventory", []) or []
        sheet_rows = []
        for wb in inventory:
            wb_name = wb.get("workbook_name", "unknown_workbook")
            for sheet in wb.get("sheets", []) or []:
                row = {
                    "Workbook": wb_name,
                    "Sheet": sheet.get("sheet_name", "unknown_sheet"),
                    "Column Count": len(sheet.get("columns", []) or []),
                    "Formula Count": len(sheet.get("formulas", []) or []),
                }
                if any(contains(v) for v in row.values()):
                    sheet_rows.append(row)
        if sheet_rows:
            out["Sheets"] = pd.DataFrame(sheet_rows)

        # Dependencies
        deps = results.get("dependency_inventory", {}).get("dependencies", []) or []
        dep_rows = [
            d for d in deps
            if isinstance(d, dict) and any(contains(v) for v in d.values())
        ]
        if dep_rows:
            out["Dependencies"] = pd.DataFrame(dep_rows)

        # Formulas / lineage
        lineage_root = results.get("formula_lineage", {}) or {}
        lineage = (
            lineage_root.get("dependencies")
            or lineage_root.get("lineage")
            or lineage_root.get("formulas")
            or []
        )
        formula_rows = [
            r for r in lineage
            if isinstance(r, dict) and any(contains(v) for v in r.values())
        ]
        if formula_rows:
            out["Formulas"] = pd.DataFrame(formula_rows)

        # Macros
        macros = (
            results.get("macro_inventory", {}).get("procedures", [])
            or results.get("macro_inventory", {}).get("macros", [])
            or []
        )
        macro_rows = []
        for m in macros:
            if isinstance(m, dict):
                if any(contains(v) for v in m.values()):
                    macro_rows.append(m)
            else:
                if contains(m):
                    macro_rows.append({"value": str(m)})
        if macro_rows:
            out["Macros"] = pd.DataFrame(macro_rows)

        return out