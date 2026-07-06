from abc import ABC, abstractmethod
from pathlib import Path


class DocumentParser(ABC):
    """Base class for file-to-text parsers."""

    @abstractmethod
    def parse(self, path: Path) -> str:
        raise NotImplementedError

