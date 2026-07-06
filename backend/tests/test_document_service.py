from pathlib import Path

import pytest

from app.services.document_service import DocumentService


def test_txt_document_parsing_and_chunking(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_text("第一段内容。\n\n第二段内容。" * 20, encoding="utf-8")

    result = DocumentService().process_file(path, chunk_size=40, chunk_overlap=5)

    assert result.filename == "notes.txt"
    assert result.metadata["file_type"] == "text"
    assert len(result.chunks) > 1
    assert result.chunks[0].metadata["chunk_index"] == 0


def test_markdown_document_parsing(tmp_path: Path) -> None:
    path = tmp_path / "guide.md"
    path.write_text("# 标题\n\n- 要点一\n- 要点二", encoding="utf-8")

    result = DocumentService().process_file(path)

    assert result.metadata["file_type"] == "markdown"
    assert "# 标题" in result.chunks[0].content


def test_text_cleaning_normalizes_whitespace() -> None:
    cleaned = DocumentService().clean_text("alpha   beta\r\n\r\n\r\n gamma")

    assert cleaned == "alpha beta\n\n gamma"


def test_docx_document_parsing(tmp_path: Path) -> None:
    docx = pytest.importorskip("docx")
    path = tmp_path / "sample.docx"
    document = docx.Document()
    document.add_paragraph("这是 Word 文档内容")
    document.save(path)

    result = DocumentService().process_file(path)

    assert result.metadata["file_type"] == "word"
    assert "Word 文档内容" in result.chunks[0].content


def test_pdf_document_parsing(tmp_path: Path) -> None:
    pytest.importorskip("pypdf")
    reportlab_canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    path = tmp_path / "sample.pdf"

    pdf = reportlab_canvas.Canvas(str(path))
    pdf.drawString(72, 720, "PDF document content")
    pdf.save()

    result = DocumentService().process_file(path)

    assert result.metadata["file_type"] == "pdf"
    assert "PDF document content" in result.chunks[0].content
