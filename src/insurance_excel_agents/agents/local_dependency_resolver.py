# src/insurance_excel_agents/agents/local_dependency_resolver.py

from dataclasses import dataclass
from pathlib import Path
import re
import json


@dataclass
class LocalDependencyResolverAgent:

    def run(self, bundle_dir: str, output_dir: str) -> dict:
        bundle_path = Path(bundle_dir)

        patterns = [
            r"[A-Za-z]:\\\\.*?\\.xlsx",
            r"/Users/.*?\\.xlsx",
            r"\\\\\\\\.*?\\\\.*?\\.xlsx"
        ]

        dependencies = []

        for file in bundle_path.glob("*.xlsm"):
            text = file.read_bytes().decode(errors="ignore")

            for pattern in patterns:
                matches = re.findall(pattern, text)
                for m in matches:
                    dependencies.append({
                        "file": str(file),
                        "path": m,
                        "type": "local_file"
                    })

        output = {"local_dependencies": dependencies}

        with open(Path(output_dir) / "local_dependencies.json", "w") as f:
            json.dump(output, f, indent=2)

        return output