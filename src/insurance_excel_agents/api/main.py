from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from insurance_excel_agents.config import AnalysisConfig
from insurance_excel_agents.orchestrator import Orchestrator

app = FastAPI(title="Insurance Excel Multi-Agent API", version="0.1.0")


class AnalyzeBundleRequest(BaseModel):
    bundle_dir: str
    output_dir: str
    recurse: bool = False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze/bundle")
def analyze_bundle(request: AnalyzeBundleRequest) -> dict:
    config = AnalysisConfig(
        bundle_dir=Path(request.bundle_dir),
        output_dir=Path(request.output_dir),
        recurse=request.recurse,
    )
    return Orchestrator().run(config)
