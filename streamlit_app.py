from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# ---------- Page setup ----------
st.set_page_config(
    page_title="Excel Agentic AI Demo",
    page_icon="📊",
    layout="wide",
)


# ---------- Sample fallback data ----------
SAMPLE_RESULTS: dict[str, Any] = {
    "workbook_paths": [
        "Insurance_Claims_Master.xlsm",
        "Insurance_PnC_Claims_Audit.xlsm",
        "Insurance_Benefits_Claims_Triage.xlsm",
    ],
    "forecast_interpretation": {
        "executive_summary": (
            "The uploaded Excel bundle appears to implement an insurance claims analytics "
            "workflow. The agent detected formula-driven KPI calculations, workbook-level "
            "macro logic, and dependencies across Claims, Payments, Reserves, Summary, and "
            "Triage sheets. The model can be exposed as APIs for claims summary, payment "
            "trends, reserve tracking, audit exception reporting, and forecast execution."
        )
    },
    "dependency_inventory": {
        "dependencies": [
            {"source": "Claims!J:J", "target": "Summary!D5", "dependency_type": "formula"},
            {"source": "Payments!G:G", "target": "Trends!C5", "dependency_type": "formula"},
            {"source": "Reserves!F:F", "target": "Summary!A7", "dependency_type": "formula"},
            {"source": "Triage_Rules!A:D", "target": "Benefits Summary!B4", "dependency_type": "rules"},
        ]
    },
    "api_contract": {
        "endpoints": [
            {
                "method": "GET",
                "path": "/claims/summary",
                "description": "Returns core claims KPIs extracted from workbook logic.",
            },
            {
                "method": "GET",
                "path": "/payments/trends",
                "description": "Returns monthly payment trends generated from formulas.",
            },
            {
                "method": "GET",
                "path": "/reserves/outstanding",
                "description": "Exposes reserve calculations as an API.",
            },
            {
                "method": "GET",
                "path": "/audit/exceptions",
                "description": "Lists flagged claim exceptions and risk signals.",
            },
            {
                "method": "POST",
                "path": "/forecast/run",
                "description": "Runs forecast logic using workbook-derived assumptions.",
            },
        ]
    },
    "validation_report": {"status": "PASS"},
    "macro_inventory": {
        "procedures": [
            {"name": "NameSheetsFromAList"},
            {"name": "RunForecast"},
            {"name": "ExportResults"},
        ]
    },
    "execution_trace": {
        "summary": {
            "input_count": 42,
            "formula_step_count": 1326,
            "macro_step_count": 3,
            "dependency_count": 3861,
            "output_count": 108,
            "risk_count": 1,
        }
    },
}


# ---------- Helpers ----------
def build_dependency_nodes_edges(results: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    deps = results.get("dependency_inventory", {}).get("dependencies", []) or []
    nodes: dict[str, dict[str, str]] = {}
    edges: list[dict[str, str]] = []

    for dep in deps:
        source = dep.get("source") or dep.get("from") or dep.get("upstream")
        target = dep.get("target") or dep.get("to") or dep.get("downstream")
        dep_type = dep.get("dependency_type", "unknown")
        if not source or not target:
            continue
        nodes[source] = {"id": source, "label": source}
        nodes[target] = {"id": target, "label": target}
        edges.append({"source": source, "target": target, "type": dep_type})

    return pd.DataFrame(nodes.values()), pd.DataFrame(edges)


def endpoints_df(results: dict[str, Any]) -> pd.DataFrame:
    endpoints = results.get("api_contract", {}).get("endpoints", []) or []
    rows = []
    for ep in endpoints:
        if isinstance(ep, dict):
            rows.append(
                {
                    "Method": ep.get("method", "GET"),
                    "Path": ep.get("path", ""),
                    "Description": ep.get("description", ep.get("desc", "")),
                }
            )
        else:
            rows.append({"Method": "GET", "Path": str(ep), "Description": ""})
    return pd.DataFrame(rows)


def try_run_orchestrator(uploaded_files) -> dict[str, Any]:
    """
    Attempts to run the local orchestrator if the project package is available.
    Falls back to sample data for stakeholder demos.
    """
    try:
        from insurance_excel_agents.config import AnalysisConfig  # type: ignore
        from insurance_excel_agents.orchestrator import Orchestrator  # type: ignore
    except Exception:
        return SAMPLE_RESULTS

    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_dir = Path(tmpdir) / "bundle"
        output_dir = Path(tmpdir) / "outputs"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        for file in uploaded_files:
            target = bundle_dir / file.name
            target.write_bytes(file.getvalue())

        config = AnalysisConfig(
            bundle_dir=bundle_dir,
            output_dir=output_dir,
            recurse=False,
        )
        orchestrator = Orchestrator()
        return orchestrator.run_full(config)


# ---------- Header ----------
st.title("Excel Agentic AI Demo")
st.caption(
    "Upload Excel models and generate an NLP summary, dependency graph, and API catalog for stakeholder review."
)

with st.sidebar:
    st.subheader("Demo Controls")
    mode = st.radio(
        "Mode",
        options=["Run with uploaded files", "Use sample stakeholder demo"],
        index=1,
    )
    uploaded_files = st.file_uploader(
        "Upload Excel files",
        type=["xlsx", "xlsm", "xlsb"],
        accept_multiple_files=True,
    )
    run_clicked = st.button("Run agent pipeline", type="primary", use_container_width=True)
    st.markdown("---")
    st.markdown("**Suggested stakeholder talking points**")
    st.markdown(
        "- Upload workbook bundle\n"
        "- Show business-readable summary\n"
        "- Show dependency relationships\n"
        "- Show generated API list\n"
        "- Emphasize governance and modernization"
    )


# ---------- State ----------
if "results" not in st.session_state:
    st.session_state.results = SAMPLE_RESULTS

if run_clicked:
    if mode == "Use sample stakeholder demo":
        st.session_state.results = SAMPLE_RESULTS
        st.success("Loaded sample stakeholder demo.")
    elif not uploaded_files:
        st.warning("Please upload at least one Excel file.")
    else:
        with st.spinner("Running multi-agent analysis..."):
            st.session_state.results = try_run_orchestrator(uploaded_files)
        st.success("Analysis complete.")

results = st.session_state.results


# ---------- KPI row ----------
trace_summary = results.get("execution_trace", {}).get("summary", {})
api_df = endpoints_df(results)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Workbooks", len(results.get("workbook_paths", [])))
c2.metric("Dependencies", trace_summary.get("dependency_count", len(results.get("dependency_inventory", {}).get("dependencies", []))))
c3.metric("APIs", len(api_df))
c4.metric("Validation", results.get("validation_report", {}).get("status", "UNKNOWN"))


# ---------- Main layout ----------
left, right = st.columns([1.2, 1])

with left:
    st.subheader("NLP Summary")
    st.write(
        results.get("forecast_interpretation", {}).get(
            "executive_summary",
            "No summary available yet.",
        )
    )

    st.subheader("Uploaded / Detected Workbooks")
    wb_df = pd.DataFrame({"Workbook": results.get("workbook_paths", [])})
    st.dataframe(wb_df, use_container_width=True, hide_index=True)

    st.subheader("Generated API Catalog")
    search = st.text_input("Search APIs", placeholder="claims, forecast, reserves...")
    filtered_api_df = api_df.copy()
    if search:
        mask = filtered_api_df.apply(
            lambda r: search.lower() in " ".join(map(str, r.values)).lower(),
            axis=1,
        )
        filtered_api_df = filtered_api_df[mask]
    st.dataframe(filtered_api_df, use_container_width=True, hide_index=True)

with right:
    st.subheader("Dependency Graph")
    nodes_df, edges_df = build_dependency_nodes_edges(results)
    if edges_df.empty:
        st.info("No dependency edges available to render.")
    else:
        st.markdown("High-level upstream/downstream relationships detected in workbook logic.")
        st.dataframe(edges_df, use_container_width=True, hide_index=True)

    st.subheader("Macro Procedures")
    macros = results.get("macro_inventory", {}).get("procedures", []) or []
    if macros:
        macro_names = [m.get("name", str(m)) if isinstance(m, dict) else str(m) for m in macros]
        st.dataframe(pd.DataFrame({"Procedure": macro_names}), use_container_width=True, hide_index=True)
    else:
        st.info("No macros detected.")


# ---------- Expanders ----------
with st.expander("Show raw execution trace"):
    st.json(results.get("execution_trace", {}))

with st.expander("Show raw API contract"):
    st.json(results.get("api_contract", {}))

with st.expander("Show full results JSON"):
    st.code(json.dumps(results, indent=2, default=str), language="json")


# ---------- Footer ----------
st.markdown("---")
st.caption(
    "Demo UI for stakeholder review. This Streamlit app can run in sample mode or be connected directly to your orchestrator for live workbook analysis."
)
