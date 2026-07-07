import asyncio

from app.schemas.chat import SourceRead
from app.services.rag_service import RAGService


def test_rag_confidence_uses_average_source_score() -> None:
    service = RAGService(db=None)
    sources = [
        SourceRead(
            document_id=1,
            chunk_id=1,
            filename="a.md",
            source_label="chunk 1",
            content="alpha",
            score=0.6,
        ),
        SourceRead(
            document_id=1,
            chunk_id=2,
            filename="a.md",
            source_label="chunk 2",
            content="beta",
            score=0.8,
        ),
    ]

    assert service._confidence(sources) == 0.7


def test_answer_query_uses_retrieval_and_llm(monkeypatch) -> None:
    async def fake_chat_completion(self, messages):
        assert "知识库上下文" in messages[1]["content"]
        return "这是基于知识库的回答。"

    source = SourceRead(
        document_id=1,
        chunk_id=3,
        filename="manual.md",
        source_label="chunk 4",
        content="项目支持 RAG 问答。",
        score=0.9,
    )
    monkeypatch.setattr(RAGService, "retrieve", lambda self, query, top_k=None: [source])
    monkeypatch.setattr("app.services.rag_service.LLMService.chat_completion", fake_chat_completion)

    result = asyncio.run(RAGService(db=None).answer_query("是否支持 RAG？"))

    assert result.answer == "这是基于知识库的回答。"
    assert result.sources[0].filename == "manual.md"
    assert result.sources[0].chunk_index == "chunk 4"
    assert result.confidence == 0.9
