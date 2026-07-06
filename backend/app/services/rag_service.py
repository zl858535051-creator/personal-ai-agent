from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.schemas.chat import SourceRead
from app.services.embedding_service import EmbeddingService
from app.vectorstore.chroma_store import ChromaVectorStore


class RAGService:
    """Retrieves relevant chunks from the local vector index."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_service = EmbeddingService()
        self.vector_store = ChromaVectorStore()

    def retrieve(self, query: str, top_k: int | None = None) -> list[SourceRead]:
        query_embedding = self.embedding_service.embed_text(query)
        results = self.vector_store.query(query_embedding, top_k or settings.retrieval_top_k)
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

