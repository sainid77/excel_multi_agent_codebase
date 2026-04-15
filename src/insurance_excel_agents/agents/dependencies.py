from __future__ import annotations

from insurance_excel_agents.models import DependencyRecord


class DependencyResolverAgent:
    def run(self, schema_inventory: dict, lineage: dict, macros: dict) -> dict:
        dependencies: list[DependencyRecord] = []

        for item in lineage.get("dependencies", []):
            dependencies.append(DependencyRecord(**item))

        for workbook in schema_inventory.get("inventory", []):
            name = workbook["workbook"]
            if workbook["container"].get("has_embedded_vba"):
                dependencies.append(
                    DependencyRecord(
                        dependency_type="embedded_vba",
                        source=name,
                        target="vbaProject.bin",
                        relationship="contains_embedded_macro_project",
                        metadata={"workbook": name},
                    )
                )
            for link in workbook.get("external_links", []):
                dependencies.append(
                    DependencyRecord(
                        dependency_type="external_workbook",
                        source=name,
                        target=link,
                        relationship="workbook_external_link",
                    )
                )

        for macro_result in macros.get("macros", []):
            workbook = macro_result["workbook"]
            for proc in macro_result.get("procedures", []):
                proc_name = proc["procedure"]
                for ref in proc.get("reads", []):
                    dependencies.append(
                        DependencyRecord(
                            dependency_type="macro_to_range",
                            source=f"{workbook}:{proc_name}",
                            target=ref,
                            relationship="macro_reads_range",
                        )
                    )
                for ref in proc.get("writes", []):
                    dependencies.append(
                        DependencyRecord(
                            dependency_type="macro_to_range",
                            source=f"{workbook}:{proc_name}",
                            target=ref,
                            relationship="macro_writes_range",
                        )
                    )
                for local_file in proc.get("local_file_refs", []):
                    dependencies.append(
                        DependencyRecord(
                            dependency_type="macro_to_file",
                            source=f"{workbook}:{proc_name}",
                            target=local_file,
                            relationship="macro_local_file_dependency",
                        )
                    )

        return {"dependencies": [dep.model_dump() for dep in dependencies]}
