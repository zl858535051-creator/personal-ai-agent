from sqlalchemy.orm import Session

from app.agent.tool_registry import AgentTool
from app.services.rag_service import RAGService


def create_knowledge_search_tool(db: Session) -> AgentTool:
    """Create a tool that delegates knowledge retrieval to RAGService."""

    def knowledge_search(query: str):
        return RAGService(db).retrieve(query)

    return AgentTool(
        name="knowledge_search",
        description="Search knowledge base and retrieve relevant information.",
        parameters={
            "query": {
                "type": "string",
                "description": "Natural language search query.",
                "required": True,
            }
        },
        function=knowledge_search,
    )
