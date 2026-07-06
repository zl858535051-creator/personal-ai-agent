import shutil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.document import Document, DocumentChunk
from app.services.document_service import DocumentService, ProcessedChunk
from app.services.embedding_service import EmbeddingService
from app.utils.file_utils import SUPPORTED_EXTENSIONS, detect_file_type, safe_storage_name
from app.vectorstore.chroma_store import ChromaVectorStore


class FileService:
    """Handles upload, parsing, chunking, and vector indexing."""

    def __init__(self, db: Session) -> None:
        self.db = db

    async def upload_and_index(self, upload: UploadFile) -> Document:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise AppError(f"Unsupported file type: {suffix}")

        stored_name = safe_storage_name(upload.filename or "document")
        path = settings.absolute_upload_dir / stored_name
        with path.open("wb") as output:
            shutil.copyfileobj(upload.file, output)

        document = Document(
            filename=upload.filename or stored_name,
            file_type=detect_file_type(stored_name),
            file_path=str(path),
            status="processing",
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        try:
            processed = DocumentService().process_file(path, filename=document.filename)
            if not processed.chunks:
                raise AppError("No readable text was extracted from this file.")
            self._index_chunks(document, processed.chunks)
            document.status = "indexed"
            document.error_message = None
        except Exception as exc:
            document.status = "failed"
            document.error_message = str(exc)
        self.db.commit()
        self.db.refresh(document)
        return document

    def list_documents(self) -> list[Document]:
        return self.db.query(Document).order_by(Document.created_at.desc()).all()

    def delete_document(self, document_id: int) -> None:
        document = self.db.get(Document, document_id)
        if document is None:
            raise AppError("Document not found", 404)
        ChromaVectorStore().delete_by_document(document.id)
        path = Path(document.file_path)
        if path.exists():
            path.unlink()
        self.db.delete(document)
        self.db.commit()

    def _index_chunks(self, document: Document, chunks: list[ProcessedChunk]) -> None:
        vector_ids: list[str] = []
        metadatas: list[dict] = []
        chunk_texts = [chunk.content for chunk in chunks]
        for processed_chunk in chunks:
            vector_id = f"doc-{document.id}-chunk-{processed_chunk.index}"
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=processed_chunk.index,
                content=processed_chunk.content,
                source_label=processed_chunk.source_label,
                vector_id=vector_id,
            )
            self.db.add(db_chunk)
            self.db.flush()
            vector_ids.append(vector_id)
            metadatas.append(
                {
                    "document_id": document.id,
                    "chunk_id": db_chunk.id,
                    "chunk_index": db_chunk.chunk_index,
                    **processed_chunk.metadata,
                }
            )

        embeddings = EmbeddingService().embed_texts(chunk_texts)
        ChromaVectorStore().add_texts(vector_ids, embeddings, metadatas)
