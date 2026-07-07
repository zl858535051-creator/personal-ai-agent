from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.chat import SourceRead


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    file_path: str
    status: str
    error_message: str | None = None
    created_at: datetime


class KnowledgeQuery(BaseModel):
    query: str
    top_k: int = 5


class KnowledgeAnswerSource(BaseModel):
    filename: str
    chunk_index: str


class KnowledgeAnswer(BaseModel):
    answer: str
    sources: list[KnowledgeAnswerSource]
    confidence: float
    retrieved_sources: list[SourceRead] = []
