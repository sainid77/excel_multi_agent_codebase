# src/insurance_excel_agents/agents/validation_agent.py

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class ValidationAgent:

    def run(self, output_dir: str) -> dict:
        output_path = Path(output_dir)

        checks = {
            "has_lineage": (output_path / "formula_lineage.json").exists(),
            "has_schema": (output_path / "schema_inventory.json").exists(),
            "has_api": (output_path / "api_contract.json").exists(),
        }

        validation = {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks
        }

        with open(output_path / "validation_report.json", "w") as f:
            json.dump(validation, f, indent=2)

        return validation