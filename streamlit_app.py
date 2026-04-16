from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

# Make local package importable
sys.path.append(str(Path(__file__).parent / "src"))

BACKEND_AVAILABLE = False
BACKEND_IMPORT_ERROR = None

try:
    from insurance_excel_agents.config import AnalysisConfig
    from insurance_excel_agents.orchestrator import Orchestrator
    from insurance_excel_agents.llm.search_agent import SearchAgent

    BACKEND_AVAILABLE = True
except Exception as exc:
    BACKEND_IMPORT_ERROR = str(exc)


st.set_page_config(
    page_title="Excel Agentic AI",
    page_icon="📊",
    layout="wide",
)

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
            "macro logic, and dependencies across Claims, Payments, Reserves, Summary, "
            "Audit, and Triage sheets. The model can be exposed as APIs for claims "
            "summary, payment trends, reserve tracking, audit exception reporting, and "
            "forecast execution."
        )
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
    "dependency_inventory": {
        "dependencies": [
            {"source": "Claims!J:J", "target": "Summary!D5", "dependency_type": "formula"},
            {"source": "Payments!G:G", "target": "Trends!C5", "dependency_type": "formula"},
            {"source": "Reserves!F:F", "target": "Summary!A7", "dependency_type": "formula"},
            {"source": "Triage_Rules!A:D", "target": "Benefits Summary!B4", "dependency_type": "rules"},
        ]
    },
    "formula_lineage": {
        "dependencies": [
            {
                "source": "Claims!J:J",
                "target": "Summary!D5",
                "formula": "=SUM(Claims!J:J)",
                "dependency_type": "formula",
            },
            {
                "source": "Payments!G:G",
                "target": "Trends!C5",
                "formula": "=SUM(Payments!G:G)",
                "dependency_type": "formula",
            },
            {
                "source": "Reserves!F:F",
                "target": "Summary!A7",
                "formula": "=SUM(Reserves!F:F)",
                "dependency_type": "formula",
            },
        ]
    },
    "schema_inventory": {
        "inventory": [
            {
                "workbook_name": "Insurance_Claims_Master.xlsm",
                "sheets": [
                    {
                        "sheet_name": "Claims",
                        "columns": ["Claim_ID", "Policy_ID", "Claim_Date", "Claim_Amount", "Status"],
                        "formulas": [],
                    },
                    {
                        "sheet_name": "Summary",
                        "columns": ["Metric", "Value"],
                        "formulas": [
                            {"cell": "D5", "formula": "=SUM(Claims!J:J)"},
                            {"cell": "A7", "formula": "=SUM(Reserves!F:F)"},
                        ],
                    },
                    {
                        "sheet_name": "Benefits_Summary",
                        "columns": ["Metric", "Value"],
                        "formulas": [
                            {
                                "cell": "B4",
                                "formula": "='[Insurance_Benefits_Claims_Triage.xlsm]Triage_Rules'!A:D",
                            }
                        ],
                    },
                ],
            },
            {
                "workbook_name": "Insurance_PnC_Claims_Audit.xlsm",
                "sheets": [
                    {
                        "sheet_name": "Audit_Input",
                        "columns": ["Claim_ID", "Audit_Flag", "Status"],
                        "formulas": [],
                    }
                ],
            },
            {
                "workbook_name": "Insurance_Benefits_Claims_Triage.xlsm",
                "sheets": [
                    {
                        "sheet_name": "Triage_Rules",
                        "columns": ["Rule_Name", "Condition", "Priority"],
                        "formulas": [],
                    }
                ],
            },
        ]
    },
    "interworkbook_dependencies": {
        "cross_references": [
            {
                "source_workbook": "Insurance_Claims_Master.xlsm",
                "source_sheet": "Summary",
                "source_cell": "D8",
                "target_workbook": "Insurance_PnC_Claims_Audit.xlsm",
                "target_sheet": "Audit_Input",
                "target_ref": "B12",
                "dependency_type": "cross_workbook",
            },
            {
                "source_workbook": "Insurance_Claims_Master.xlsm",
                "source_sheet": "Summary",
                "source_cell": "E11",
                "target_workbook": "Insurance_PnC_Claims_Audit.xlsm",
                "target_sheet": "Audit_Input",
                "target_ref": "C17",
                "dependency_type": "cross_workbook",
            },
            {
                "source_workbook": "Insurance_Claims_Master.xlsm",
                "source_sheet": "Benefits_Summary",
                "source_cell": "B4",
                "target_workbook": "Insurance_Benefits_Claims_Triage.xlsm",
                "target_sheet": "Triage_Rules",
                "target_ref": "A:D",
                "dependency_type": "cross_workbook",
            },
        ],
        "file_level_edges": [
            {
                "source_workbook": "Insurance_Claims_Master.xlsm",
                "target_workbook": "Insurance_PnC_Claims_Audit.xlsm",
                "reference_count": 2,
            },
            {
                "source_workbook": "Insurance_Claims_Master.xlsm",
                "target_workbook": "Insurance_Benefits_Claims_Triage.xlsm",
                "reference_count": 1,
            },
        ],
    },
    "business_rules": {
        "rules": [
            {
                "rule_name": "claims_summary_logic",
                "business_meaning": "Workbook calculates aggregate claims KPIs for reporting.",
                "inputs": ["Claims", "Payments", "Reserves"],
                "outputs": ["Summary metrics"],
                "confidence": 0.88,
            },
            {
                "rule_name": "triage_flagging",
                "business_meaning": "Workbook applies triage rules to identify high-priority claim cases.",
                "inputs": ["Benefits Summary", "Triage_Rules"],
                "outputs": ["Triage decisions"],
                "confidence": 0.84,
            },
        ],
        "summary": "Two major business rule groups were detected: claims KPI aggregation and triage logic.",
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
    "macro_inventory": {
        "procedures": [
            {"name": "NameSheetsFromAList", "module": "WorkbookUtilities"},
            {"name": "RunForecast", "module": "ForecastModule"},
            {"name": "ExportResults", "module": "ExportModule"},
        ]
    },
    "validation": {"status": "PASS"},
}


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


def build_entity_nodes_edges(results: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    deps = results.get("dependency_inventory", {}).get("dependencies", []) or []
    nodes: dict[str, dict[str, str]] = {}
    edges: list[dict[str, str]] = []

    def infer_group(name: str) -> str:
        lowered = str(name).lower()
        if "claims" in lowered:
            return "claims"
        if "payment" in lowered:
            return "payments"
        if "reserve" in lowered:
            return "reserves"
        if "summary" in lowered or "trend" in lowered:
            return "reporting"
        if "triage" in lowered or "rules" in lowered:
            return "rules"
        return "other"

    for dep in deps:
        source = dep.get("source") or dep.get("from") or dep.get("upstream")
        target = dep.get("target") or dep.get("to") or dep.get("downstream")
        dep_type = dep.get("dependency_type", "unknown")
        if not source or not target:
            continue

        nodes[source] = {"id": source, "label": source, "group": infer_group(source)}
        nodes[target] = {"id": target, "label": target, "group": infer_group(target)}
        edges.append(
            {
                "source": source,
                "target": target,
                "type": dep_type,
                "label": dep_type,
            }
        )

    return pd.DataFrame(nodes.values()), pd.DataFrame(edges)


def build_workbook_flow_nodes_edges(results: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    file_edges = results.get("interworkbook_dependencies", {}).get("file_level_edges", []) or []
    nodes: dict[str, dict[str, str]] = {}
    edges: list[dict[str, Any]] = []

    for edge in file_edges:
        src = edge.get("source_workbook")
        tgt = edge.get("target_workbook")
        count = edge.get("reference_count", 1)

        if not src or not tgt:
            continue

        nodes[src] = {"id": src, "label": src, "group": "workbook"}
        nodes[tgt] = {"id": tgt, "label": tgt, "group": "workbook"}

        edges.append(
            {
                "source": src,
                "target": tgt,
                "label": f"{count} refs",
                "weight": count,
            }
        )

    return pd.DataFrame(nodes.values()), pd.DataFrame(edges)


def workbook_flow_details_df(results: dict[str, Any]) -> pd.DataFrame:
    inter = results.get("interworkbook_dependencies", {}) or {}
    file_edges = inter.get("file_level_edges", []) or []
    cross_refs = inter.get("cross_references", []) or []

    rows: list[dict[str, Any]] = []

    for edge in file_edges:
        src = edge.get("source_workbook", "")
        tgt = edge.get("target_workbook", "")
        count = edge.get("reference_count", 0)

        matching_refs = [
            ref for ref in cross_refs
            if ref.get("source_workbook") == src and ref.get("target_workbook") == tgt
        ]

        if matching_refs:
            details = []
            for ref in matching_refs:
                details.append(
                    f"{ref.get('source_sheet', '?')}!{ref.get('source_cell', '?')} → "
                    f"{ref.get('target_sheet', '?')}!{ref.get('target_ref', '?')} "
                    f"({ref.get('dependency_type', 'unknown')})"
                )
            details_text = "\n".join(details)
        else:
            details_text = "No detailed references available."

        rows.append(
            {
                "Source Workbook": src,
                "Target Workbook": tgt,
                "Reference Count": count,
                "Details": details_text,
            }
        )

    return pd.DataFrame(rows)


def render_network(nodes_df: pd.DataFrame, edges_df: pd.DataFrame, title: str, height: int = 560) -> None:
    if nodes_df.empty or edges_df.empty:
        st.info(f"No data available for {title}.")
        return

    net = Network(
        height=f"{height}px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#0f172a",
        directed=True,
    )
    net.barnes_hut(
        gravity=-22000,
        central_gravity=0.2,
        spring_length=180,
        spring_strength=0.03,
        damping=0.09,
    )

    color_map = {
        "claims": "#2563eb",
        "payments": "#059669",
        "reserves": "#dc2626",
        "reporting": "#7c3aed",
        "rules": "#d97706",
        "workbook": "#0f766e",
        "other": "#64748b",
    }

    for _, row in nodes_df.iterrows():
        group = row.get("group", "other")
        node_id = str(row["id"])
        label = str(row.get("label", node_id))
        net.add_node(
            node_id,
            label=label,
            title=f"{label}<br>Group: {group}",
            color=color_map.get(group, color_map["other"]),
            shape="dot",
            size=18 if group != "workbook" else 24,
        )

    for _, row in edges_df.iterrows():
        net.add_edge(
            str(row["source"]),
            str(row["target"]),
            title=str(row.get("label", "")),
            label=str(row.get("label", "")),
            color="#94a3b8",
            arrows="to",
        )

    options = {
        "interaction": {
            "hover": True,
            "navigationButtons": True,
            "keyboard": True,
        },
        "physics": {
            "stabilization": False,
        },
        "nodes": {
            "font": {"size": 12, "face": "Arial"},
            "borderWidth": 1,
        },
        "edges": {
            "font": {"size": 10, "align": "middle"},
            "smooth": {"type": "dynamic"},
        },
    }

    net.set_options(json.dumps(options))
    components.html(net.generate_html(), height=height + 20, scrolling=True)


def try_run_orchestrator(uploaded_files) -> dict[str, Any]:
    if not BACKEND_AVAILABLE:
        raise RuntimeError(
            f"Backend imports failed. Reason: {BACKEND_IMPORT_ERROR}"
        )

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


def ai_search(results: dict[str, Any], query: str) -> dict[str, Any]:
    """
    AI-only search.
    No keyword fallback.
    Works for both SAMPLE_RESULTS and live uploaded-file results,
    but requires SearchAgent backend to be importable.
    """
    if not BACKEND_AVAILABLE:
        raise RuntimeError(
            f"AI search backend is unavailable. Import error: {BACKEND_IMPORT_ERROR}"
        )

    agent = SearchAgent()
    return agent.run(results=results, query=query)


st.title("Excel Multi-Agentic AI")
st.caption(
    "Upload Excel workbooks and generate an NLP summary, dependency graphs, cross-workbook flow, and API catalog."
)

with st.sidebar:
    st.subheader("Run Mode")
    mode = st.radio(
        "Choose mode",
        options=["Use sample demo", "Run with uploaded files"],
        index=0,
    )

    uploaded_files = st.file_uploader(
        "Upload Excel files",
        type=["xlsx", "xlsm", "xlsb"],
        accept_multiple_files=True,
    )

    run_clicked = st.button("Run multi-agent pipeline", type="primary", use_container_width=True)

    st.markdown("---")
    st.caption(f"Backend available: {BACKEND_AVAILABLE}")
    if BACKEND_IMPORT_ERROR:
        st.error(f"Backend import error: {BACKEND_IMPORT_ERROR}")

if "results" not in st.session_state:
    st.session_state.results = SAMPLE_RESULTS

if run_clicked:
    if mode == "Use sample demo":
        st.session_state.results = SAMPLE_RESULTS
        st.success("Loaded sample stakeholder demo.")
    elif not uploaded_files:
        st.warning("Please upload at least one Excel workbook.")
    else:
        with st.spinner("Running multi-agent analysis..."):
            st.session_state.results = try_run_orchestrator(uploaded_files)
        st.success("Analysis complete.")

results = st.session_state.results

st.subheader("AI Search Across Excel")
search_prompt = st.text_input(
    "Ask anything about dependencies, formulas, lineage, macros, workbooks, sheets, files, APIs, or NLP summary",
    placeholder="e.g. Which workbook depends on audit inputs? Show reserve formulas. Which macro runs forecast logic?",
)

if search_prompt.strip():
    try:
        ai_result = ai_search(results, search_prompt)
        answer = ai_result.get("answer", "No answer generated.")
        match_tables = ai_result.get("matches", {}) or {}
        mode_used = ai_result.get("mode", "llm")

        st.success(f"Search completed using: {mode_used}")
        st.markdown("### Search Results")
        st.write(answer)

        if match_tables:
            st.markdown("### Supporting Matches")
            for i, (section_name, df) in enumerate(match_tables.items()):
                if isinstance(df, pd.DataFrame):
                    with st.expander(f"{section_name} ({len(df)})", expanded=(i == 0)):
                        st.dataframe(df, use_container_width=True, hide_index=True)
                elif isinstance(df, list):
                    with st.expander(f"{section_name} ({len(df)})", expanded=(i == 0)):
                        st.dataframe(pd.DataFrame(df), use_container_width=True, hide_index=True)
        else:
            st.info("No structured supporting matches found.")
    except Exception as exc:
        st.error(f"AI search failed: {exc}")

st.markdown("---")

trace_summary = results.get("execution_trace", {}).get("summary", {})
api_df = endpoints_df(results)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Workbooks", len(results.get("workbook_paths", [])))
c2.metric(
    "Dependencies",
    trace_summary.get(
        "dependency_count",
        len(results.get("dependency_inventory", {}).get("dependencies", [])),
    ),
)
c3.metric("APIs", len(api_df))
c4.metric("Validation", results.get("validation", {}).get("status", "UNKNOWN"))

left, right = st.columns([1.15, 1])

with left:
    st.subheader("Executive NLP Summary")
    st.write(
        results.get("forecast_interpretation", {}).get(
            "executive_summary",
            "No summary available yet.",
        )
    )

    st.subheader("Detected Workbooks")
    workbook_df = pd.DataFrame({"Workbook": results.get("workbook_paths", [])})
    st.dataframe(workbook_df, use_container_width=True, hide_index=True)

    st.subheader("Generated API Catalog")
    api_search = st.text_input("Search APIs", placeholder="claims, forecast, reserves...")
    filtered_api_df = api_df.copy()
    if api_search:
        mask = filtered_api_df.apply(
            lambda r: api_search.lower() in " ".join(map(str, r.values)).lower(),
            axis=1,
        )
        filtered_api_df = filtered_api_df[mask]
    st.dataframe(filtered_api_df, use_container_width=True, hide_index=True)

with right:
    st.subheader("Macro Procedures")
    macros = results.get("macro_inventory", {}).get("procedures", []) or []
    if macros:
        macro_names = [m.get("name", str(m)) if isinstance(m, dict) else str(m) for m in macros]
        st.dataframe(
            pd.DataFrame({"Procedure": macro_names}),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No macros detected.")

    st.subheader("Execution Trace Summary")
    if trace_summary:
        st.json(trace_summary)
    else:
        st.info("No execution trace available.")

st.subheader("Entity Network Graph")
entity_nodes_df, entity_edges_df = build_entity_nodes_edges(results)
render_network(entity_nodes_df, entity_edges_df, "Entity Network Graph")

with st.expander("Show all entity nodes and edges"):
    st.markdown("**Nodes**")
    st.dataframe(entity_nodes_df, use_container_width=True, hide_index=True)
    st.markdown("**Edges**")
    st.dataframe(entity_edges_df, use_container_width=True, hide_index=True)

st.subheader("Workbook Interconnection Flow")
wb_nodes_df, wb_edges_df = build_workbook_flow_nodes_edges(results)
render_network(wb_nodes_df, wb_edges_df, "Workbook Flow Graph")

with st.expander("Show workbook flow edges"):
    flow_df = workbook_flow_details_df(results)
    st.dataframe(flow_df, use_container_width=True, hide_index=True)

with st.expander("Show business rules"):
    st.json(results.get("business_rules", {}))

with st.expander("Show API contract"):
    st.json(results.get("api_contract", {}))

with st.expander("Show full results JSON"):
    st.code(json.dumps(results, indent=2, default=str), language="json")

st.markdown("---")
st.caption(
    "Demo UI for stakeholder review. AI search is enforced in both sample mode and uploaded-file mode. "
    "If backend imports fail, the app shows the real import error instead of falling back to keyword search."
)