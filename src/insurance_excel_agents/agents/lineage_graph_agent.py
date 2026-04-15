# src/insurance_excel_agents/agents/lineage_graph_agent.py

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class LineageGraphAgent:

    def run(self, output_dir: str) -> dict:
        output_path = Path(output_dir)

        lineage_file = output_path / "formula_lineage.json"
        if not lineage_file.exists():
            return {"error": "no lineage file"}

        data = json.load(open(lineage_file))

        nodes = []
        edges = []

        lineage_items = data.get("lineage", [])

        for item in lineage_items:
            target = item.get("target")
            sources = item.get("depends_on", [])

            nodes.append({"id": target, "type": "cell"})

            for s in sources:
                edges.append({"from": s, "to": target})

        graph = {"nodes": nodes, "edges": edges}

        with open(output_path / "lineage_graph.json", "w") as f:
            json.dump(graph, f, indent=2)

        return graph