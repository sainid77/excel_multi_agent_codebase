from __future__ import annotations

import argparse
import json
from pathlib import Path

from insurance_excel_agents.config import AnalysisConfig
from insurance_excel_agents.orchestrator import Orchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Insurance Excel multi-agent CLI"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze-bundle",
        help="Analyze a directory of Excel workbooks and generate core artifacts",
    )
    analyze_parser.add_argument(
        "--bundle-dir",
        required=True,
        help="Path to the folder containing Excel workbooks",
    )
    analyze_parser.add_argument(
        "--output-dir",
        required=True,
        help="Path to the output folder",
    )
    analyze_parser.add_argument(
        "--recurse",
        action="store_true",
        help="Recursively search for workbooks under bundle-dir",
    )

    report_parser = subparsers.add_parser(
        "generate-report",
        help="Run full pipeline: analysis, reporting, execution, validation, lineage graph, and code generation",
    )
    report_parser.add_argument(
        "--bundle-dir",
        required=True,
        help="Path to the folder containing Excel workbooks",
    )
    report_parser.add_argument(
        "--output-dir",
        required=True,
        help="Path to the output folder",
    )
    report_parser.add_argument(
        "--recurse",
        action="store_true",
        help="Recursively search for workbooks under bundle-dir",
    )

    return parser


def _make_config(args: argparse.Namespace) -> AnalysisConfig:
    return AnalysisConfig(
        bundle_dir=Path(args.bundle_dir).expanduser().resolve(),
        output_dir=Path(args.output_dir).expanduser().resolve(),
        recurse=bool(args.recurse),
    )


def cmd_analyze_bundle(args: argparse.Namespace) -> int:
    config = _make_config(args)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    orchestrator = Orchestrator()
    results = orchestrator.run(config)

    summary = {
        "bundle_dir": str(config.bundle_dir),
        "output_dir": str(config.output_dir),
        "status": "completed",
        "artifact_keys": sorted(list(results.keys())),
    }

    run_summary = results.get("run_summary")
    if isinstance(run_summary, dict) and run_summary:
        summary["run_summary"] = run_summary

    print(json.dumps(summary, indent=2, default=str))
    return 0


def cmd_generate_report(args: argparse.Namespace) -> int:
    config = _make_config(args)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    orchestrator = Orchestrator()
    results = orchestrator.run_full(config)

    summary = {
        "bundle_dir": str(config.bundle_dir),
        "output_dir": str(config.output_dir),
        "generated_files": [
            str(config.output_dir / "execution_trace.json"),
            str(config.output_dir / "forecast_interpretation.json"),
            str(config.output_dir / "forecast_interpretation.md"),
            str(config.output_dir / "execution_log.json"),
            str(config.output_dir / "local_dependencies.json"),
            str(config.output_dir / "validation_report.json"),
            str(config.output_dir / "lineage_graph.json"),
            str(config.output_dir / "generated_api.py"),
        ],
        "execution_trace_summary": (
            results.get("execution_trace", {}).get("summary", {})
            if isinstance(results.get("execution_trace"), dict)
            else {}
        ),
        "executive_summary": (
            results.get("forecast_interpretation", {}).get("executive_summary", "")
            if isinstance(results.get("forecast_interpretation"), dict)
            else ""
        ),
        "validation_status": (
            results.get("validation_report", {}).get("status", "UNKNOWN")
            if isinstance(results.get("validation_report"), dict)
            else "UNKNOWN"
        ),
    }

    print(json.dumps(summary, indent=2, default=str))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze-bundle":
        return cmd_analyze_bundle(args)

    if args.command == "generate-report":
        return cmd_generate_report(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())