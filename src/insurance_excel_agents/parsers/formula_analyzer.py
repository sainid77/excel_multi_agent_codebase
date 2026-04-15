from __future__ import annotations

import re
from typing import Iterable

from insurance_excel_agents.models import DependencyRecord, FormulaRecord

# Handles references like A1, $B$2, Sheet1!C3, 'My Sheet'!D4, A:A, A1:B10
REF_PATTERN = re.compile(
    r"(?:(?:'[^']+'|[A-Za-z0-9_]+)!)?\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?"
    r"|(?:(?:'[^']+'|[A-Za-z0-9_]+)!)?\$?[A-Z]{1,3}:(?:\$?[A-Z]{1,3})"
)


class FormulaAnalyzer:
    def extract_references(self, formula: str) -> list[str]:
        refs = REF_PATTERN.findall(formula)
        return sorted(set(refs))

    def build_dependencies(self, formula_records: Iterable[FormulaRecord]) -> list[DependencyRecord]:
        dependencies: list[DependencyRecord] = []
        for record in formula_records:
            refs = self.extract_references(record.formula)
            record.references = refs
            for ref in refs:
                if "!" in ref:
                    target_sheet = ref.split("!", 1)[0].strip("'")
                    dep_type = "sheet_to_sheet" if target_sheet != record.sheet else "cell_to_cell"
                else:
                    dep_type = "cell_to_cell"
                dependencies.append(
                    DependencyRecord(
                        dependency_type=dep_type,
                        source=f"{record.workbook}:{record.sheet}!{record.cell}",
                        target=f"{record.workbook}:{ref if '!' in ref else record.sheet + '!' + ref}",
                        relationship="formula_reference",
                        metadata={"formula": record.formula},
                    )
                )
        return dependencies
