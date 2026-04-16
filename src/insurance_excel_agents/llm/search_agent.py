from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from insurance_excel_agents.llm.client import LLMClient


def _compact_json(data: Any, max_chars: int = 14000) -> str:
    text = json.dumps(data, indent=2, default=str)
    return text[:max_chars]


def _to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


@dataclass
class SearchAgent:
    use_llm: bool = True

    def __post_init__(self) -> None:
        self.llm = None
        if self.use_llm:
            try:
                self.llm = LLMClient()
            except Exception:
                self.llm = None

    def run(self, results: dict[str, Any], query: str) -> dict[str, Any]:
        matches = self._keyword_matches(results, query)

        if self.llm is None:
            raise RuntimeError(
                "LLMClient could not be initialized. Check OPENAI_API_KEY, OPENAI_MODEL, "
                "and required packages in the active environment."
            )

        answer = self._llm_answer(results, query, matches)

        return {
            "answer": answer,
            "matches": matches,
            "mode": "llm_plus_keyword",
        }

    def _llm_answer(
        self,
        results: dict[str, Any],
        query: str,
        matches: dict[str, pd.DataFrame],
    ) -> str:
        serializable_matches = {
            section: df.to_dict(orient="records")
            for section, df in matches.items()
        }

        prompt = f"""
You are an expert Excel modernization analyst.

User query:
{query}

Workbook intelligence results:
{_compact_json(results, max_chars=12000)}

Structured supporting matches:
{_compact_json(serializable_matches, max_chars=8000)}

Instructions:
- Answer the user query clearly and directly.
- Use only the information present in the provided results.
- Mention relevant workbooks, sheets, formulas, dependencies, macros, APIs, or business rules when helpful.
- If the result is incomplete or uncertain, say so.
- Do not invent entities or formulas not present in the provided data.
"""

        return self.llm.complete(
            system_prompt=(
                "You answer questions about extracted Excel workbook intelligence. "
                "Be accurate, grounded, and concise."
            ),
            user_prompt=prompt,
        )

    def _keyword_matches(self, results: dict[str, Any], query: str) -> dict[str, pd.DataFrame]:
        q = query.strip().lower()
        if not q:
            return {}

        def contains(value: Any) -> bool:
            return q in str(value).lower()

        out: dict[str, pd.DataFrame] = {}

        deps = results.get("dependency_inventory", {}).get("dependencies", []) or []
        dep_rows = [
            d for d in deps
            if isinstance(d, dict) and any(contains(v) for v in d.values())
        ]
        if dep_rows:
            out["Dependencies"] = _to_dataframe(dep_rows)

        lineage_root = results.get("formula_lineage", {}) or {}
        lineage = (
            lineage_root.get("dependencies")
            or lineage_root.get("lineage")
            or lineage_root.get("formulas")
            or []
        )
        lineage_rows = [
            r for r in lineage
            if isinstance(r, dict) and any(contains(v) for v in r.values())
        ]
        if lineage_rows:
            out["Formula / Lineage"] = _to_dataframe(lineage_rows)

        macros = (
            results.get("macro_inventory", {}).get("procedures", [])
            or results.get("macro_inventory", {}).get("macros", [])
            or []
        )
        macro_rows: list[dict[str, Any]] = []
        for m in macros:
            if isinstance(m, dict):
                if any(contains(v) for v in m.values()):
                    macro_rows.append(m)
            else:
                if contains(m):
                    macro_rows.append({"value": str(m)})
        if macro_rows:
            out["Macros"] = _to_dataframe(macro_rows)

        workbooks = results.get("workbook_paths", []) or []
        wb_rows = [{"Workbook": w} for w in workbooks if contains(w)]
        if wb_rows:
            out["Workbooks / Files"] = _to_dataframe(wb_rows)

        inventory = results.get("schema_inventory", {}).get("inventory", []) or []
        sheet_rows: list[dict[str, Any]] = []
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
            out["Sheets"] = _to_dataframe(sheet_rows)

        endpoints = results.get("api_contract", {}).get("endpoints", []) or []
        api_rows: list[dict[str, Any]] = []
        for ep in endpoints:
            if isinstance(ep, dict) and any(contains(v) for v in ep.values()):
                api_rows.append(
                    {
                        "Method": ep.get("method", "GET"),
                        "Path": ep.get("path", ""),
                        "Description": ep.get("description", ep.get("desc", "")),
                    }
                )
        if api_rows:
            out["APIs"] = _to_dataframe(api_rows)

        summary = results.get("forecast_interpretation", {}).get("executive_summary", "")
        if contains(summary):
            out["NLP Summary"] = _to_dataframe(
                [{"Executive Summary": summary}]
            )

        rules = results.get("business_rules", {}).get("rules", []) or []
        rule_rows = [
            r for r in rules
            if isinstance(r, dict) and any(contains(v) for v in r.values())
        ]
        if rule_rows:
            out["Business Rules"] = _to_dataframe(rule_rows)

        cross_refs = results.get("interworkbook_dependencies", {}).get("cross_references", []) or []
        cross_rows = [
            r for r in cross_refs
            if isinstance(r, dict) and any(contains(v) for v in r.values())
        ]
        if cross_rows:
            out["Cross-Workbook References"] = _to_dataframe(cross_rows)

        return out
