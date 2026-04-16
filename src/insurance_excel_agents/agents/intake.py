from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import zipfile

from insurance_excel_agents.parsers.workbook_parser import WorkbookParser
from insurance_excel_agents.loaders.local_loader import LocalFolderLoader


@dataclass
class WorkbookIntakeAgent:
    parser: WorkbookParser = WorkbookParser()

    def run(self, bundle_dir, recurse=True):
        loader = LocalFolderLoader(bundle_dir, recurse)
        files = loader.list_files()

        return {
            "workbook_paths": [str(f) for f in files],
            "count": len(files),
        }

    def run(self, bundle_dir: Path, recurse: bool = False) -> dict[str, Any]:
        allowed_exts = {".xlsx", ".xlsm", ".xlsb", ".xltx", ".xltm"}
        pattern = "**/*" if recurse else "*"

        discovered = []
        skipped = []

        for path in sorted(bundle_dir.glob(pattern)):
            if not path.is_file():
                continue

            if path.suffix.lower() not in allowed_exts:
                skipped.append(
                    {
                        "path": str(path),
                        "reason": f"unsupported extension: {path.suffix.lower()}",
                    }
                )
                continue

            try:
                container = self.parser.inspect_container(path)
                discovered.append(
                    {
                        "path": str(path),
                        "filename": path.name,
                        "extension": path.suffix.lower(),
                        "container": container,
                    }
                )
            except zipfile.BadZipFile:
                skipped.append(
                    {
                        "path": str(path),
                        "reason": "bad zip / not a valid Open XML workbook container",
                    }
                )
            except Exception as exc:
                skipped.append(
                    {
                        "path": str(path),
                        "reason": f"{type(exc).__name__}: {exc}",
                    }
                )

        return {
            "workbook_paths": [{"path": item["path"]} for item in discovered],
            "files": discovered,
            "skipped": skipped,
            "count": len(discovered),
        }