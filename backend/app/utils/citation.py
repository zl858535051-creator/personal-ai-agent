from app.schemas.chat import SourceRead


def render_sources(sources: list[SourceRead]) -> str:
    if not sources:
        return "No local sources matched."
    return "\n".join(
        f"[{index}] {source.filename} / {source.source_label}: {source.content[:500]}"
        for index, source in enumerate(sources, start=1)
    )

