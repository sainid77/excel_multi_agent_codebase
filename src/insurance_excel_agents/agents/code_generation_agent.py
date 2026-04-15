from dataclasses import dataclass
from pathlib import Path
import json
import re


def _safe_python_name(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("/", "_")
    value = value.replace("\\", "_")
    value = value.replace("-", "_")
    value = value.replace(".", "_")
    value = re.sub(r"[^a-zA-Z0-9_]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")

    if not value:
        value = "endpoint"

    if value[0].isdigit():
        value = f"endpoint_{value}"

    return value


@dataclass
class CodeGenerationAgent:
    def run(self, output_dir: str):
        p = Path(output_dir)

        api_file = p / "api_contract.json"
        if not api_file.exists():
            return {"error": "no api contract"}

        with open(api_file, "r", encoding="utf-8") as f:
            api = json.load(f)

        code = [
            "from fastapi import FastAPI",
            "",
            "app = FastAPI()",
            "",
        ]

        seen_names = set()

        for i, ep in enumerate(api.get("endpoints", []), start=1):
            if isinstance(ep, dict):
                path = ep.get("path", "/endpoint")
            else:
                path = "/endpoint"

            base_name = _safe_python_name(path)
            func_name = base_name

            if func_name in seen_names:
                func_name = f"{base_name}_{i}"
            seen_names.add(func_name)

            code.append(f"@app.get('{path}')")
            code.append(f"def {func_name}():")
            code.append("    return {'ok': True, 'path': '" + path.replace("'", "\\'") + "'}")
            code.append("")

        out_file = p / "generated_api.py"
        out_file.write_text("\n".join(code), encoding="utf-8")

        return {"file": str(out_file)}