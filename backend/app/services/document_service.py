import re
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import AppError
from app.parsers.markdown_parser import MarkdownParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.text_parser import TextParser
from app.parsers.word_parser import WordParser
from app.utils.file_utils import SUPPORTED_EXTENSIONS, detect_file_type
from app.utils.text_splitter import TextSplitter


@dataclass(frozen=True)
class ProcessedChunk:
    """A text chunk ready for embedding and vector indexing."""

    index: int
    content: str
    source_label: str
    metadata: dict


@dataclass(frozen=True)
class ProcessedDocument:
    """Structured document output from parsing, cleaning, and chunking."""

    filename: str
    chunks: list[ProcessedChunk]
    metadata: dict


class DocumentService:
    """Unified document parser and chunker for the RAG pipeline."""

    def process_file(
        self,
        path: Path,
        filename: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> ProcessedDocument:
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise AppError(f"Unsupported file type: {suffix}")

        display_name = filename or path.name
        file_type = detect_file_type(display_name)
        raw_text = self._parser_for(file_type).parse(path)
        cleaned_text = self.clean_text(raw_text)
        chunk_texts = TextSplitter(
            chunk_size or settings.chunk_size,
            chunk_overlap if chunk_overlap is not None else settings.chunk_overlap,
        ).split(cleaned_text)

        chunks = [
            ProcessedChunk(
                index=index,
                content=content,
                source_label=f"chunk {index + 1}",
                metadata={
                    "filename": display_name,
                    "file_type": file_type,
                    "chunk_index": index,
                    "source_label": f"chunk {index + 1}",
                },
            )
            for index, content in enumerate(chunk_texts)
        ]

        return ProcessedDocument(
            filename=display_name,
            chunks=chunks,
            metadata={
                "filename": display_name,
                "file_type": file_type,
                "path": str(path),
                "chunk_size": chunk_size or settings.chunk_size,
                "chunk_overlap": chunk_overlap if chunk_overlap is not None else settings.chunk_overlap,
                "chunk_count": len(chunks),
                "text_length": len(cleaned_text),
            },
        )

    def clean_text(self, text: str) -> str:
        """Normalize whitespace while preserving paragraph boundaries."""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        normalized = re.sub(r"[ \t]+", " ", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

    def _parser_for(self, file_type: str):
        return {
            "pdf": PDFParser(),
            "word": WordParser(),
            "markdown": MarkdownParser(),
            "text": TextParser(),
        }[file_type]
