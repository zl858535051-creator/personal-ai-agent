import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent.planner import Plan, PlanStep
from app.core.database import Base
from app.memory import MemoryManager
from app.models import task as task_models  # noqa: F401
from app.reflection import ReflectionManager, TaskEvaluator
from app.schemas.agent import AgentRunRequest, AgentStep
from app.schemas.chat import SourceRead
from app.services.agent_service import AgentService


def make_step(status: str = "done") -> AgentStep:
    return AgentStep(name="Search KB", status=status, detail="tool=knowledge_search")


def make_source() -> SourceRead:
    return SourceRead(
        document_id=1,
        chunk_id=2,
        filename="demo.md",
        source_label="chunk 1",
        content="Relevant context",
        score=0.9,
    )


def test_successful_task_evaluation() -> None:
    result = TaskEvaluator().evaluate(
        task="分析资料",
        plan=Plan("general_analysis", [PlanStep("knowledge_search", {"query": "资料"}, "Search")]),
        steps=[make_step()],
        sources=[make_source()],
        answer="这是一个结构化且足够完整的回答，包含结论、依据和建议。",
    )

    assert result.success is True
    assert result.score >= 0.7
    assert result.issues == []


def test_failed_task_evaluation() -> None:
    result = TaskEvaluator().evaluate(
        task="分析资料",
        plan=Plan("general_analysis", [PlanStep("knowledge_search", {"query": "资料"}, "Search")]),
        steps=[make_step(status="failed")],
        sources=[],
        answer="error",
    )

    assert result.success is False
    assert result.score < 0.7
    assert result.issues
    assert result.suggestions


def test_reflection_manager_calls_evaluator() -> None:
    result = ReflectionManager().reflect(
        task="总结资料",
        plan=Plan("general_analysis", [PlanStep("knowledge_search", {"query": "资料"}, "Search")]),
        steps=[make_step()],
        sources=[make_source()],
        answer="这是一个结构化且足够完整的回答，包含结论、依据和建议。",
    )

    assert result.success is True
    assert result.to_dict()["score"] == result.score


def test_agent_service_saves_reflection_result(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    memory_manager = MemoryManager()

    async def fake_plan(self, task):
        return Plan("general_analysis", [PlanStep("knowledge_search", {"query": "资料"}, "Search")])

    async def fake_execute(self, task, plan):
        return (
            "这是一个结构化且足够完整的回答，包含结论、依据和建议。",
            [make_step()],
            [make_source()],
        )

    monkeypatch.setattr("app.services.agent_service.get_default_memory_manager", lambda: memory_manager)
    monkeypatch.setattr("app.services.agent_service.Planner.plan", fake_plan)
    monkeypatch.setattr("app.services.agent_service.Executor.execute", fake_execute)

    response = asyncio.run(AgentService(db).run(AgentRunRequest(task="总结资料")))
    task_record = memory_manager.get_task(str(response.task_id))

    assert response.result.startswith("这是一个结构化")
    assert task_record is not None
    assert task_record.reflection_result is not None
    assert task_record.reflection_result["success"] is True

