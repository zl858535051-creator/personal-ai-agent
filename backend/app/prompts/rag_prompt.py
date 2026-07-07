from app.schemas.chat import SourceRead


def build_rag_messages(question: str, sources: list[SourceRead]) -> list[dict[str, str]]:
    """Build a strict RAG prompt that discourages unsupported claims."""
    context = "\n\n".join(
        (
            f"[Source {index}] filename={source.filename}; "
            f"chunk_id={source.chunk_id}; label={source.source_label}; score={source.score:.3f}\n"
            f"{source.content}"
        )
        for index, source in enumerate(sources, start=1)
    )
    if not context:
        context = "No relevant knowledge base context was found."

    system_prompt = (
        "你是一个严谨的本地知识库问答助手。必须遵守：\n"
        "1. 只根据提供的知识库上下文回答。\n"
        "2. 如果上下文不足以回答，明确说明“根据当前知识库资料无法确定”。\n"
        "3. 不要编造文件、事实、数字或结论。\n"
        "4. 回答中引用来源，格式使用文件名和 chunk 标识。\n"
        "5. 默认使用中文回答，结构清晰、结论优先。"
    )
    user_prompt = (
        f"知识库上下文：\n{context}\n\n"
        f"用户问题：{question}\n\n"
        "请基于上述上下文给出答案，并列出引用来源。"
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
