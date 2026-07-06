from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.chat import SourceRead
from app.schemas.document import KnowledgeQuery
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/query", response_model=list[SourceRead])
def query_knowledge(request: KnowledgeQuery, db: DbSession) -> list[SourceRead]:
    return RAGService(db).retrieve(request.query, top_k=request.top_k)

