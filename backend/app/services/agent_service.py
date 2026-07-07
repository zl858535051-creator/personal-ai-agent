from sqlalchemy.orm import Session

from app.agent.executor import Executor
from app.agent.planner import Planner
from app.agent.tools import AgentTools
from app.models.task import AgentTask
from app.schemas.agent import AgentRunRequest, AgentRunResponse
from app.schemas.report import ReportCreate
from app.services.report_service import ReportService


class AgentService:
    """Runs planned tasks and optionally turns the output into a report."""

    def __init__(self, db: Session) -> None:
        self.db = db

    async def run(self, request: AgentRunRequest) -> AgentRunResponse:
        agent_tools = AgentTools(self.db)
        plan = await Planner(tool_registry=agent_tools.registry).plan(request.task)
        result, steps, sources = await Executor(tool_registry=agent_tools.registry).execute(request.task, plan)
        task = AgentTask(user_input=request.task, task_type=plan.task_type, result=result)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        report_id = None
        if request.generate_report:
            report = ReportService(self.db).create_report(
                ReportCreate(title=f"Agent Report {task.id}", content=result, format="markdown")
            )
            report_id = report.id

        return AgentRunResponse(
            task_id=task.id,
            task_type=plan.task_type,
            result=result,
            steps=steps,
            sources=sources,
            report_id=report_id,
        )
