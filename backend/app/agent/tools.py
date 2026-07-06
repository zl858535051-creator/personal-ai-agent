from sqlalchemy.orm import Session

from app.schemas.chat import SourceRead
from app.services.rag_service import RAGService


class AgentTools:
    """Tool registry for the MVP agent."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def search_knowledge(self, query: str) -> list[SourceRead]:
        return RAGService(self.db).retrieve(query)

