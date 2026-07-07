from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.document import KnowledgeAnswer, KnowledgeQuery
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/query", response_model=KnowledgeAnswer)
async def query_knowledge(request: KnowledgeQuery, db: DbSession) -> KnowledgeAnswer:
    return await RAGService(db).answer_query(request.query, top_k=request.top_k)
