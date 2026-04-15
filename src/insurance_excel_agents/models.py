from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class WorkbookRole(BaseModel):
    name: str
    path: str
    role: str
    has_macros: bool = False
    has_external_links: bool = False
    domain_hint: str | None = None


class SheetInfo(BaseModel):
    name: str
    max_row: int
    max_column: int
    hidden: bool = False
    formulas: int = 0


class FormulaRecord(BaseModel):
    workbook: str
    sheet: str
    cell: str
    formula: str
    references: list[str] = Field(default_factory=list)


class DependencyRecord(BaseModel):
    dependency_type: Literal[
        "sheet_to_sheet",
        "cell_to_cell",
        "external_workbook",
        "local_file",
        "embedded_vba",
        "macro_to_range",
        "macro_to_file",
    ]
    source: str
    target: str
    relationship: str
    confidence: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class MacroProcedure(BaseModel):
    procedure: str
    procedure_type: Literal["Sub", "Function"]
    reads: list[str] = Field(default_factory=list)
    writes: list[str] = Field(default_factory=list)
    local_file_refs: list[str] = Field(default_factory=list)
    raw_excerpt: str = ""


class ApiEndpoint(BaseModel):
    method: str
    path: str
    purpose: str
    source_workbook: str
    depends_on: list[str] = Field(default_factory=list)


class AgentArtifact(BaseModel):
    agent: str
    payload: dict[str, Any]
