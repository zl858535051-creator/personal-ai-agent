"""Concrete tools available to the agent."""

from sqlalchemy.orm import Session

from app.agent.tool_registry import ToolRegistry
from app.agent.tools.rag_tool import create_knowledge_search_tool
from app.schemas.chat import SourceRead


class AgentTools:
    """Compatibility wrapper around the agent tool registry."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = ToolRegistry()
        self.registry.register_tool(create_knowledge_search_tool(db))

    async def search_knowledge(self, query: str) -> list[SourceRead]:
        return await self.registry.call_tool("knowledge_search", query=query)


__all__ = ["AgentTools", "create_knowledge_search_tool"]
