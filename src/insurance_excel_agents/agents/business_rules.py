from __future__ import annotations


class BusinessRuleExtractionAgent:
    """Very lightweight rule summarizer from formula patterns and workbook names."""

    def run(self, schema_inventory: dict, lineage: dict) -> dict:
        rules: list[dict] = []
        for workbook in schema_inventory.get("inventory", []):
            workbook_name = workbook["workbook"]
            sheets = {sheet["name"] for sheet in workbook.get("sheet_infos", [])}
            if "Summary" in sheets:
                rules.append(
                    {
                        "workbook": workbook_name,
                        "rule_name": "summary_kpis",
                        "description": "Workbook computes claims KPIs from base transaction sheets.",
                    }
                )
            if "Trends" in sheets:
                rules.append(
                    {
                        "workbook": workbook_name,
                        "rule_name": "trend_aggregation",
                        "description": "Workbook aggregates monthly claim or payment trends.",
                    }
                )
            if "Exceptions" in sheets:
                rules.append(
                    {
                        "workbook": workbook_name,
                        "rule_name": "audit_exceptions",
                        "description": "Workbook contains audit-style exception detection outputs.",
                    }
                )
            if "Triage_Rules" in sheets:
                rules.append(
                    {
                        "workbook": workbook_name,
                        "rule_name": "benefits_triage",
                        "description": "Workbook stores triage rules and provider-driven decision logic.",
                    }
                )
        return {"rules": rules}
