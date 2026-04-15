from __future__ import annotations

from pathlib import Path

from insurance_excel_agents.parsers.macro_analyzer import MacroAnalyzer


class MacroParsingAgent:
    def __init__(self) -> None:
        self.analyzer = MacroAnalyzer()

    def run(self, workbook_paths: list[Path]) -> dict:
        results = [self.analyzer.analyze_workbook_macros(path) for path in workbook_paths]
        return {"macros": results}
