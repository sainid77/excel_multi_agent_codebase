from pathlib import Path

from insurance_excel_agents.config import AnalysisConfig
from insurance_excel_agents.orchestrator import Orchestrator


def test_orchestrator_runs(tmp_path: Path) -> None:
    bundle_dir = Path("/mnt/data/insurance_claims_dataset")
    config = AnalysisConfig(bundle_dir=bundle_dir, output_dir=tmp_path)
    result = Orchestrator().run(config)
    assert result["summary"]["workbook_count"] >= 3
    assert result["summary"]["formula_count"] > 0
