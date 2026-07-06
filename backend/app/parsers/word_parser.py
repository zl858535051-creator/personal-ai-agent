from pathlib import Path

from app.core.exceptions import AppError
from app.parsers.base import DocumentParser


class WordParser(DocumentParser):
    def parse(self, path: Path) -> str:
        try:
            import docx
        except ImportError as exc:
            raise AppError("python-docx is required to parse Word files.") from exc

        document = docx.Document(str(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())

