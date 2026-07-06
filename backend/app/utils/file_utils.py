from pathlib import Path
from uuid import uuid4


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".markdown"}


def safe_storage_name(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    stem = Path(filename).stem.replace(" ", "_")[:80] or "document"
    return f"{stem}_{uuid4().hex[:10]}{suffix}"


def detect_file_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix == ".docx":
        return "word"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".txt":
        return "text"
    raise ValueError(f"Unsupported file type: {suffix}")

