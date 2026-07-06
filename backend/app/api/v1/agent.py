from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.agent import AgentRunRequest, AgentRunResponse
from app.services.agent_service import AgentService

router = APIRouter()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest, db: DbSession) -> AgentRunResponse:
    return await AgentService(db).run(request)

