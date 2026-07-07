import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.prompts.rag_prompt import build_rag_messages
from app.schemas.chat import SourceRead
from app.schemas.document import KnowledgeAnswer, KnowledgeAnswerSource
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.vectorstore.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class RAGService:
    """Retrieves relevant chunks from the local vector index."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_store = ChromaVectorStore()

    def retrieve(self, query: str, top_k: int | None = None) -> list[SourceRead]:
        try:
            query_embedding = self.embedding_service.embed_text(query)
            results = self.vector_store.query(query_embedding, top_k or settings.retrieval_top_k)
        except Exception:
            logger.exception("RAG retrieval failed.")
            return []

        sources: list[SourceRead] = []
        for result in results:
            chunk_id = result.metadata.get("chunk_id")
            if not chunk_id:
                continue
            chunk = self.db.get(DocumentChunk, int(chunk_id))
            if chunk is None:
                continue
            document = self.db.get(Document, chunk.document_id)
            if document is None:
                continue
            sources.append(
                SourceRead(
                    document_id=document.id,
                    chunk_id=chunk.id,
                    filename=document.filename,
                    source_label=chunk.source_label,
                    content=chunk.content,
                    score=result.score,
                )
            )
        return sources

    async def answer_query(self, query: str, top_k: int | None = None) -> KnowledgeAnswer:
        """Run retrieval, build a RAG prompt, call the LLM, and return an answer."""
        sources = self.retrieve(query, top_k=top_k)
        messages = build_rag_messages(query, sources)
        try:
            answer = await LLMService().chat_completion(messages)
        except Exception as exc:
            logger.exception("RAG answer generation failed.")
            answer = f"知识库问答生成失败：{exc}"

        return KnowledgeAnswer(
            answer=answer,
            sources=[
                KnowledgeAnswerSource(filename=source.filename, chunk_index=source.source_label)
                for source in sources
            ],
            confidence=self._confidence(sources),
            retrieved_sources=sources,
        )

    def _confidence(self, sources: list[SourceRead]) -> float:
        if not sources:
            return 0.0
        avg_score = sum(source.score for source in sources) / len(sources)
        return round(max(0.0, min(1.0, avg_score)), 3)
