from pathlib import Path

from app.parsers.base import DocumentParser


class TextParser(DocumentParser):
    def parse(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")

