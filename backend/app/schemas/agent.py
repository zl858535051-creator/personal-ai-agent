from pydantic import BaseModel

from app.schemas.chat import SourceRead


class AgentRunRequest(BaseModel):
    task: str
    generate_report: bool = False


class AgentStep(BaseModel):
    name: str
    status: str
    detail: str


class AgentRunResponse(BaseModel):
    task_id: int
    task_type: str
    result: str
    steps: list[AgentStep]
    sources: list[SourceRead] = []
    report_id: int | None = None

