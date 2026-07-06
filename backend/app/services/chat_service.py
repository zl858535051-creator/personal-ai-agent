import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionRead
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.utils.citation import render_sources


class ChatService:
    """Coordinates conversation memory, RAG context, and LLM responses."""

    def __init__(self, db: Session) -> None:
        self.db = db

    async def chat(self, request: ChatRequest) -> ChatResponse:
        session = self._get_or_create_session(request)
        sources = RAGService(self.db).retrieve(request.message) if request.use_knowledge_base else []
        history = self._recent_messages(session.id)
        system_prompt = (
            "You are a local personal AI assistant. Answer in Chinese by default, "
            "use retrieved context when relevant, and cite sources by filename/chunk.\n\n"
            f"Retrieved context:\n{render_sources(sources)}"
        )
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend({"role": item.role, "content": item.content} for item in history)
        messages.append({"role": "user", "content": request.message})

        self.db.add(ChatMessage(session_id=session.id, role="user", content=request.message))
        answer = await LLMService().chat_completion(messages)
        self.db.add(
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content=answer,
                sources_json=json.dumps([source.model_dump() for source in sources], ensure_ascii=False),
            )
        )
        session.updated_at = datetime.utcnow()
        self.db.commit()
        return ChatResponse(session_id=session.id, message=answer, sources=sources)

    def list_sessions(self) -> list[ChatSession]:
        return self.db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()

    def get_session(self, session_id: int) -> ChatSessionRead:
        session = self.db.get(ChatSession, session_id)
        if session is None:
            raise AppError("Chat session not found", 404)
        return session

    def _get_or_create_session(self, request: ChatRequest) -> ChatSession:
        if request.session_id:
            session = self.db.get(ChatSession, request.session_id)
            if session is None:
                raise AppError("Chat session not found", 404)
            return session
        title = request.message[:40] or "New chat"
        session = ChatSession(title=title)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def _recent_messages(self, session_id: int, limit: int = 8) -> list[ChatMessage]:
        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))
