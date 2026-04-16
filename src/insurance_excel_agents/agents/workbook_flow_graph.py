from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class WorkbookFlowGraphAgent:
    """
    Converts inter-workbook dependency output into a graph artifact.

    Writes:
    - workbook_flow_graph.json

    Returns:
    {
      "nodes": [...],
      "edges": [...]
    }
    """

    def run(self, interworkbook_result: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []

        for edge in interworkbook_result.get("file_level_edges", []) or []:
            src = edge.get("source_workbook")
            tgt = edge.get("target_workbook")
            ref_count = edge.get("reference_count", 1)

            if not src or not tgt:
                continue

            nodes[src] = {
                "id": src,
                "label": src,
                "type": "workbook",
            }
            nodes[tgt] = {
                "id": tgt,
                "label": tgt,
                "type": "workbook",
            }

            edges.append(
                {
                    "source": src,
                    "target": tgt,
                    "weight": ref_count,
                    "label": f"{ref_count} refs",
                }
            )

        graph = {
            "nodes": list(nodes.values()),
            "edges": edges,
        }

        out_file = output_path / "workbook_flow_graph.json"
        out_file.write_text(json.dumps(graph, indent=2), encoding="utf-8")

        return graph