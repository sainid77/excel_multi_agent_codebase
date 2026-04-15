# Insurance Excel Multi-Agent Codebase

A Python starter project for converting Excel insurance models into cloud-ready APIs while preserving workbook lineage, formula dependencies, and macro/dependency metadata.

This codebase is pre-wired to analyze the following synthetic insurance workbooks:

- `Insurance_Claims_Master.xlsm`
- `Insurance_PnC_Claims_Audit.xlsm`
- `Insurance_Benefits_Claims_Triage.xlsm`

## What it does

- Registers workbook bundles and classifies workbook roles
- Extracts workbook structure: sheets, tables, named ranges, formulas, hidden sheets
- Builds formula lineage across cells and sheets
- Detects dependencies:
  - sheet-to-sheet
  - workbook external references
  - local file references in VBA / companion macro text
- Synthesizes API endpoints from workbook metrics and domain entities
- Exposes the analysis as a FastAPI service and CLI

## Architecture

Agents:

1. `WorkbookIntakeAgent`
2. `WorkbookSchemaAgent`
3. `FormulaLineageAgent`
4. `MacroParsingAgent`
5. `DependencyResolverAgent`
6. `BusinessRuleExtractionAgent`
7. `ApiSynthesisAgent`
8. `Orchestrator`

Parsers:

- `WorkbookParser`: OpenPyXL-based workbook inspection
- `FormulaAnalyzer`: formula reference extraction and lineage edges
- `MacroAnalyzer`: companion macro text parsing and embedded-VBA detection

## Embedded VBA support

The sample `.xlsm` files contain `vbaProject.bin` streams. This project detects that fact today.

For full extraction of embedded VBA source, install an extractor supported by your environment. The codebase is designed to work even when source extraction is not available:

- always: detect embedded VBA presence
- always: parse companion `.txt` / `.bas` macro source files if present
- optional: extend `MacroAnalyzer.extract_embedded_vba()` to use `oletools`, LibreOffice export, or a Windows COM-based workflow

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# analyze the included insurance bundle
python -m insurance_excel_agents.cli analyze-bundle \
  --bundle-dir /path/to/insurance_claims_dataset \
  --output-dir ./outputs

# run the API
uvicorn insurance_excel_agents.api.main:app --reload
```

## Example API calls

```bash
# health
curl http://127.0.0.1:8000/health

# analyze known bundle on disk
curl -X POST http://127.0.0.1:8000/analyze/bundle \
  -H "Content-Type: application/json" \
  -d '{"bundle_dir":"/path/to/insurance_claims_dataset","output_dir":"./outputs"}'
```

## Output artifacts

The analysis writes:

- `bundle_manifest.json`
- `schema_inventory.json`
- `formula_lineage.json`
- `macro_inventory.json`
- `dependency_inventory.json`
- `business_rules.json`
- `api_contract.json`
- `run_summary.json`

## Notes about the supplied insurance workbooks

Observed workbook patterns:

- shared core sheets: `Claims`, `Payments`, `Reserves`, `Policies`, `Summary`, `Trends`
- P&C workbook includes `Exceptions`
- Benefits workbook includes `Care_Providers` and `Triage_Rules`
- formulas include reserve math and duration/aging logic in claims sheets
- the workbooks contain embedded `vbaProject.bin`

## Nice next steps

- add Neo4j persistence for lineage graphs
- generate OpenAPI schemas from extracted metrics
- convert metrics to Python service functions automatically
- add an HTML lineage viewer
- plug into Azure Functions / Cloud Run / Lambda deployment
