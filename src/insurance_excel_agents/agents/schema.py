from __future__ import annotations

from pathlib import Path

from insurance_excel_agents.parsers.workbook_parser import WorkbookParser


class WorkbookSchemaAgent:
    def __init__(self) -> None:
        self.parser = WorkbookParser()

    def run(self, workbook_paths: list[Path]) -> dict:
        inventory = [self.parser.parse_workbook(path) for path in workbook_paths]
        return {"inventory": inventory}
