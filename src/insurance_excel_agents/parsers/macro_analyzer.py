from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

from insurance_excel_agents.models import MacroProcedure

PROC_PATTERN = re.compile(
    r"\b(?P<ptype>Sub|Function)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\b(?P<body>.*?)(?=\bEnd\s+(?:Sub|Function)\b)",
    re.IGNORECASE | re.DOTALL,
)
RANGE_PATTERN = re.compile(r'Range\("([^"]+)"\)|Cells\(([^\)]+)\)', re.IGNORECASE)
WRITE_PATTERN = re.compile(r'Range\("([^"]+)"\)\s*=', re.IGNORECASE)
WORKBOOK_OPEN_PATTERN = re.compile(r'Workbooks\.Open\("([^"]+)"\)', re.IGNORECASE)
FILE_PATTERN = re.compile(r'([A-Za-z]:\\[^"\n\r]+|\\\\[^"\n\r]+|[^"\n\r]+\.(?:csv|xlsx|xlsm|xlsb|txt|accdb))')


class MacroAnalyzer:
    def detect_embedded_vba(self, workbook_path: Path) -> bool:
        with zipfile.ZipFile(workbook_path) as zf:
            return any(name.endswith("vbaProject.bin") for name in zf.namelist())

    def find_companion_macro_sources(self, workbook_path: Path) -> list[Path]:
        directory = workbook_path.parent
        candidates = []
        stem = workbook_path.stem.lower()
        for ext in ("*.txt", "*.bas", "*.cls", "*.vba"):
            for path in directory.glob(ext):
                content = path.read_text(encoding="utf-8", errors="ignore")
                if "Sub " in content or "Function " in content or stem.split("_")[0] in path.name.lower():
                    candidates.append(path)
        return sorted(set(candidates))

    def parse_macro_text(self, text: str) -> list[MacroProcedure]:
        procedures: list[MacroProcedure] = []
        for match in PROC_PATTERN.finditer(text):
            body = match.group("body")
            reads = [m.group(1) or m.group(2) for m in RANGE_PATTERN.finditer(body)]
            writes = [m.group(1) for m in WRITE_PATTERN.finditer(body)]
            local_refs = [m.group(1) for m in WORKBOOK_OPEN_PATTERN.finditer(body)]
            local_refs.extend(FILE_PATTERN.findall(body))
            procedures.append(
                MacroProcedure(
                    procedure=match.group("name"),
                    procedure_type=match.group("ptype").title(),
                    reads=sorted(set(filter(None, reads))),
                    writes=sorted(set(filter(None, writes))),
                    local_file_refs=sorted(set(filter(None, local_refs))),
                    raw_excerpt=body.strip()[:1000],
                )
            )
        return procedures

    def analyze_workbook_macros(self, workbook_path: Path) -> dict[str, Any]:
        embedded = self.detect_embedded_vba(workbook_path)
        companion_sources = self.find_companion_macro_sources(workbook_path)
        procedures: list[MacroProcedure] = []
        for source in companion_sources:
            text = source.read_text(encoding="utf-8", errors="ignore")
            procedures.extend(self.parse_macro_text(text))
        return {
            "workbook": workbook_path.name,
            "embedded_vba_present": embedded,
            "companion_sources": [str(path) for path in companion_sources],
            "procedures": [item.model_dump() for item in procedures],
            "embedded_vba_note": (
                "Embedded VBA detected. Source extraction hook not implemented in this starter project. "
                "Extend MacroAnalyzer.extract_embedded_vba() for your preferred extractor."
                if embedded
                else "No embedded VBA detected."
            ),
        }
