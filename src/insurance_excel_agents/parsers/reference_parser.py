from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ReferenceParser:
    """
    Extracts cross-sheet and cross-workbook references from Excel formulas.

    Supported examples:
    - =Summary!B12
    - ='[Claims_Input.xlsx]RawData'!C7
    - =VLOOKUP(A2,'[Rates.xlsx]Table'!A:F,3,FALSE)
    """

    # Matches workbook + sheet + cell/range references like:
    # '[Workbook.xlsx]Sheet Name'!A1
    # [Workbook.xlsx]Sheet1!B2:C5
    CROSS_WORKBOOK_PATTERN = re.compile(
        r"(?:'|\")?\[([^\]]+)\]([^'\"!]+)(?:'|\")?!([A-Z]{1,3}\d+(?::[A-Z]{1,3}\d+)?|[A-Z]{1,3}:[A-Z]{1,3})"
    )

    # Matches same-workbook cross-sheet refs like:
    # Summary!B12
    # 'Audit Input'!C7
    CROSS_SHEET_PATTERN = re.compile(
        r"(?:'([^']+)'|([A-Za-z0-9_ ]+))!([A-Z]{1,3}\d+(?::[A-Z]{1,3}\d+)?|[A-Z]{1,3}:[A-Z]{1,3})"
    )

    def extract_references(
        self,
        formula: str,
        current_workbook: str,
        current_sheet: str,
        current_cell: str,
    ) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []

        if not formula or not isinstance(formula, str):
            return refs

        # 1) Cross-workbook refs
        for match in self.CROSS_WORKBOOK_PATTERN.finditer(formula):
            workbook, sheet, ref = match.groups()
            refs.append(
                {
                    "source_workbook": current_workbook,
                    "source_sheet": current_sheet,
                    "source_cell": current_cell,
                    "target_workbook": workbook.strip(),
                    "target_sheet": sheet.strip(),
                    "target_ref": ref.strip(),
                    "dependency_type": "cross_workbook",
                }
            )

        # 2) Cross-sheet refs within same workbook
        for match in self.CROSS_SHEET_PATTERN.finditer(formula):
            quoted_sheet, unquoted_sheet, ref = match.groups()
            sheet = (quoted_sheet or unquoted_sheet or "").strip()

            # Skip false positives that are already part of cross-workbook references
            if f"]{sheet}!" in formula or f"]{sheet}'!" in formula:
                continue

            refs.append(
                {
                    "source_workbook": current_workbook,
                    "source_sheet": current_sheet,
                    "source_cell": current_cell,
                    "target_workbook": current_workbook,
                    "target_sheet": sheet,
                    "target_ref": ref.strip(),
                    "dependency_type": (
                        "intra_sheet" if sheet == current_sheet else "cross_sheet"
                    ),
                }
            )

        return refs