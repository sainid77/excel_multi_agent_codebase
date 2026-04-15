from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field


class AnalysisConfig(BaseModel):
    bundle_dir: Path = Field(..., description="Directory containing one or more Excel workbooks")
    output_dir: Path = Field(..., description="Directory to write analysis artifacts")
    recurse: bool = Field(default=False, description="Whether to search subdirectories for workbooks")


class ApiSettings(BaseModel):
    title: str = "Insurance Excel Multi-Agent API"
    version: str = "0.1.0"
