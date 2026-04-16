from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from insurance_excel_agents.llm.client import LLMClient


def _safe_python_name(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("/", "_").replace("\\", "_").replace("-", "_").replace(".", "_")
    value = re.sub(r"[^a-zA-Z0-9_]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = "endpoint"
    if value[0].isdigit():
        value = f"endpoint_{value}"
    return value


@dataclass
class CodeGenerationAgent:
    use_llm: bool = True

    def __post_init__(self) -> None:
        self.llm = None
        if self.use_llm:
            try:
                self.llm = LLMClient()
            except Exception:
                self.llm = None

    def run(
        self,
        output_dir: str,
        api_contract: dict[str, Any] | None = None,
        business_rules: dict[str, Any] | None = None,
    ):
        p = Path(output_dir)
        p.mkdir(parents=True, exist_ok=True)

        if api_contract is None:
            api_file = p / "api_contract.json"
            if not api_file.exists():
                return {"error": "no api contract"}
            with open(api_file, "r", encoding="utf-8") as f:
                api_contract = json.load(f)

        if self.llm is not None:
            try:
                code = self._generate_with_llm(api_contract, business_rules)
                out_file = p / "generated_api.py"
                out_file.write_text(code, encoding="utf-8")
                return {"file": str(out_file), "mode": "llm"}
            except Exception:
                pass

        code = self._fallback_code(api_contract)
        out_file = p / "generated_api.py"
        out_file.write_text(code, encoding="utf-8")
        return {"file": str(out_file), "mode": "fallback"}

    def _generate_with_llm(self, api_contract: dict[str, Any], business_rules: dict[str, Any] | None) -> str:
        prompt = f"""
Generate a valid FastAPI application in Python.

API Contract:
{json.dumps(api_contract, indent=2, default=str)[:12000]}

Business Rules:
{json.dumps(business_rules, indent=2, default=str)[:12000] if business_rules else "null"}

Requirements:
- valid Python only
- include `from fastapi import FastAPI`
- define `app = FastAPI()`
- create safe endpoint function names
- return mock but meaningful structured JSON
- no markdown fences
"""
        return self.llm.complete(
            system_prompt="You generate valid production-style FastAPI starter code.",
            user_prompt=prompt,
        )

    def _fallback_code(self, api_contract: dict[str, Any]) -> str:
        code = [
            "from fastapi import FastAPI",
            "",
            "app = FastAPI()",
            "",
        ]

        seen_names = set()

        for i, ep in enumerate(api_contract.get("endpoints", []), start=1):
            path = ep.get("path", "/endpoint") if isinstance(ep, dict) else "/endpoint"
            base_name = _safe_python_name(path)
            func_name = base_name if base_name not in seen_names else f"{base_name}_{i}"
            seen_names.add(func_name)

            method = ep.get("method", "GET").lower() if isinstance(ep, dict) else "get"
            if method not in {"get", "post", "put", "delete", "patch"}:
                method = "get"

            code.append(f"@app.{method}('{path}')")
            code.append(f"def {func_name}():")
            code.append(f"    return {{'ok': True, 'path': '{path}'}}")
            code.append("")

        return "\n".join(code)