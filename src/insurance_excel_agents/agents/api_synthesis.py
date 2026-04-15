from __future__ import annotations

from insurance_excel_agents.models import ApiEndpoint


class ApiSynthesisAgent:
    def run(self, schema_inventory: dict, business_rules: dict) -> dict:
        endpoints: list[ApiEndpoint] = []
        for workbook in schema_inventory.get("inventory", []):
            workbook_name = workbook["workbook"]
            sheets = {sheet["name"] for sheet in workbook.get("sheet_infos", [])}

            if "Claims" in sheets:
                endpoints.append(
                    ApiEndpoint(
                        method="GET",
                        path=f"/workbooks/{workbook_name}/claims/summary",
                        purpose="Return claims summary metrics derived from workbook tabs.",
                        source_workbook=workbook_name,
                        depends_on=["Claims", "Summary"],
                    )
                )
            if "Payments" in sheets:
                endpoints.append(
                    ApiEndpoint(
                        method="GET",
                        path=f"/workbooks/{workbook_name}/payments/trends",
                        purpose="Return payment trend aggregates.",
                        source_workbook=workbook_name,
                        depends_on=["Payments", "Trends"],
                    )
                )
            if "Exceptions" in sheets:
                endpoints.append(
                    ApiEndpoint(
                        method="GET",
                        path=f"/workbooks/{workbook_name}/audit/exceptions",
                        purpose="Return audit exception outputs.",
                        source_workbook=workbook_name,
                        depends_on=["Claims", "Exceptions", "Summary"],
                    )
                )
            if "Triage_Rules" in sheets:
                endpoints.append(
                    ApiEndpoint(
                        method="POST",
                        path=f"/workbooks/{workbook_name}/benefits/triage",
                        purpose="Apply benefits triage rules to a claim payload.",
                        source_workbook=workbook_name,
                        depends_on=["Claims", "Triage_Rules", "Care_Providers"],
                    )
                )
        return {"endpoints": [endpoint.model_dump() for endpoint in endpoints]}
