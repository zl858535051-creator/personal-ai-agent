from app.utils.text_splitter import TextSplitter


def test_splitter_handles_empty_text() -> None:
    assert TextSplitter().split("  \n  ") == []


def test_splitter_overlaps_chunks() -> None:
    chunks = TextSplitter(chunk_size=10, chunk_overlap=2).split("abcdefghijklmnopqrstuvwxyz")
    assert chunks[0] == "abcdefghij"
    assert chunks[1].startswith("ij")

