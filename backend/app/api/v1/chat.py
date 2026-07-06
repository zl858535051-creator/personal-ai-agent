from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionRead
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: DbSession) -> ChatResponse:
    return await ChatService(db).chat(request)


@router.get("/sessions", response_model=list[ChatSessionRead])
def list_sessions(db: DbSession) -> list[ChatSessionRead]:
    return ChatService(db).list_sessions()


@router.get("/sessions/{session_id}", response_model=ChatSessionRead)
def get_session(session_id: int, db: DbSession) -> ChatSessionRead:
    return ChatService(db).get_session(session_id)

