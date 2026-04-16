from pathlib import Path
from typing import List

from .base_loader import BaseLoader


class LocalFolderLoader(BaseLoader):
    def __init__(self, folder_path: str, recurse: bool = True):
        self.folder_path = Path(folder_path)
        self.recurse = recurse

    def list_files(self) -> List[Path]:
        patterns = ["*.xlsx", "*.xlsm", "*.xls"]

        files = []
        for pattern in patterns:
            if self.recurse:
                files.extend(self.folder_path.rglob(pattern))
            else:
                files.extend(self.folder_path.glob(pattern))

        return sorted(set(files))