from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceRead(BaseModel):
    document_id: int
    chunk_id: int
    filename: str
    source_label: str
    content: str
    score: float


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None
    use_knowledge_base: bool = True


class ChatResponse(BaseModel):
    session_id: int
    message: str
    sources: list[SourceRead] = []


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageRead] = []

