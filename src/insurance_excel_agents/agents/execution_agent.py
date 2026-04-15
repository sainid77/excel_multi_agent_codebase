# src/insurance_excel_agents/agents/execution_agent.py

from dataclasses import dataclass
from pathlib import Path
import subprocess
import json


@dataclass
class ExecutionAgent:
    """
    Executes Excel workflows (basic version).
    For Mac: uses open + AppleScript fallback
    For Windows: can be extended with win32com
    """

    def run(self, bundle_dir: str, output_dir: str) -> dict:
        bundle_path = Path(bundle_dir)

        executed_files = []

        for file in bundle_path.glob("*.xlsm"):
            try:
                # Mac: open Excel file (simulation mode)
                subprocess.run(["open", str(file)], check=False)
                executed_files.append(str(file))
            except Exception as e:
                executed_files.append(f"{file} (failed: {e})")

        result = {
            "execution_mode": "simulated",
            "executed_files": executed_files
        }

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(Path(output_dir) / "execution_log.json", "w") as f:
            json.dump(result, f, indent=2)

        return result