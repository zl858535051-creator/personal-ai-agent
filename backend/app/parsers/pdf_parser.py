from pathlib import Path

from app.core.exceptions import AppError
from app.parsers.base import DocumentParser


class PDFParser(DocumentParser):
    def parse(self, path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise AppError("pypdf is required to parse PDF files.") from exc

        reader = PdfReader(str(path))
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[Page {index}]\n{text}")
        return "\n\n".join(pages)

