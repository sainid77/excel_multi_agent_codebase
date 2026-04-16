from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class BaseLoader(ABC):
    @abstractmethod
    def list_files(self) -> List[Path]:
        pass