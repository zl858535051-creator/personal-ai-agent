import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent.planner import Plan, PlanStep
from app.agent.self_correction import SelfCorrectionManager
from app.agent.tool_registry import ToolRegistry
from app.core.database import Base
from app.memory import MemoryManager
from app.models import task as task_models  # noqa: F401
from app.reflection import ReflectionResult
from app.schemas.agent import AgentRunRequest, AgentStep
from app.services.agent_service import AgentService


def make_step(status: str = "done") -> AgentStep:
    return AgentStep(name="Search", status=status, detail="tool=knowledge_search")


def reflection(success: bool, score: float) -> ReflectionResult:
    return ReflectionResult(
        success=success,
        score=score,
        issues=[] if success else ["missing information"],
        suggestions=[] if success else ["retry with better query"],
    )


class FakeReflectionManager:
    def __init__(self, results: list[ReflectionResult]) -> None:
        self.results = results
        self.calls = 0

    def reflect(self, **kwargs):
        result = self.results[min(self.calls, len(self.results) - 1)]
        self.calls += 1
        return result


def patch_attempts(monkeypatch, outputs):
    async def fake_attempt(self, task, planner_task, tool_registry):
        index = min(fake_attempt.calls, len(outputs) - 1)
        fake_attempt.calls += 1
        return outputs[index]

    fake_attempt.calls = 0
    monkeypatch.setattr(SelfCorrectionManager, "_attempt", fake_attempt)
    return fake_attempt


def test_first_success_does_not_retry(monkeypatch) -> None:
    attempt = patch_attempts(
        monkeypatch,
        [
            (
                Plan("general_analysis", [PlanStep("knowledge_search", {"query": "a"}, "Search")]),
                "good answer with enough detail",
                [make_step()],
                [],
                reflection(True, 0.95),
            )
        ],
    )

    result = asyncio.run(SelfCorrectionManager().run("task", "planner task", ToolRegistry()))

    assert result.retry_count == 0
    assert len(result.reflection_history) == 1
    assert result.reflection_result.success is True
    assert attempt.calls == 1


def test_reflection_failure_triggers_retry(monkeypatch) -> None:
    attempt = patch_attempts(
        monkeypatch,
        [
            (
                Plan("general_analysis", [PlanStep("knowledge_search", {"query": "bad"}, "Search")]),
                "bad",
                [make_step(status="failed")],
                [],
                reflection(False, 0.4),
            ),
            (
                Plan("general_analysis", [PlanStep("knowledge_search", {"query": "better"}, "Search again")]),
                "better answer with enough detail",
                [make_step()],
                [],
                reflection(True, 0.9),
            ),
        ],
    )

    result = asyncio.run(SelfCorrectionManager().run("task", "planner task", ToolRegistry()))

    assert result.retry_count == 1
    assert result.result == "better answer with enough detail"
    assert len(result.reflection_history) == 2
    assert attempt.calls == 2


def test_retry_success_returns_second_attempt(monkeypatch) -> None:
    patch_attempts(
        monkeypatch,
        [
            (
                Plan("general_analysis", []),
                "bad",
                [],
                [],
                reflection(False, 0.3),
            ),
            (
                Plan("general_analysis", [PlanStep("knowledge_search", {"query": "fixed"}, "Search")]),
                "fixed answer with enough detail",
                [make_step()],
                [],
                reflection(True, 0.8),
            ),
        ],
    )

    result = asyncio.run(SelfCorrectionManager(max_retry=2).run("task", "planner task", ToolRegistry()))

    assert result.reflection_result.success is True
    assert result.retry_count == 1
    assert result.result.startswith("fixed")


def test_exits_after_max_retry(monkeypatch) -> None:
    attempt = patch_attempts(
        monkeypatch,
        [
            (Plan("general_analysis", []), "bad 1", [], [], reflection(False, 0.2)),
            (Plan("general_analysis", []), "bad 2", [], [], reflection(False, 0.3)),
            (Plan("general_analysis", []), "bad 3", [], [], reflection(False, 0.4)),
        ],
    )

    result = asyncio.run(SelfCorrectionManager(max_retry=2).run("task", "planner task", ToolRegistry()))

    assert result.retry_count == 2
    assert result.result == "bad 3"
    assert len(result.reflection_history) == 3
    assert attempt.calls == 3


def test_agent_service_saves_retry_history(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    memory_manager = MemoryManager()

    async def fake_run(self, task, planner_task, tool_registry):
        return type(
            "CorrectionResult",
            (),
            {
                "plan": Plan("general_analysis", [PlanStep("knowledge_search", {"query": "fixed"}, "Search")]),
                "result": "fixed answer with enough detail",
                "steps": [make_step()],
                "sources": [],
                "reflection_result": reflection(True, 0.9),
                "retry_count": 1,
                "reflection_history": [reflection(False, 0.3).to_dict(), reflection(True, 0.9).to_dict()],
            },
        )()

    monkeypatch.setattr("app.services.agent_service.get_default_memory_manager", lambda: memory_manager)
    monkeypatch.setattr("app.services.agent_service.SelfCorrectionManager.run", fake_run)

    response = asyncio.run(AgentService(db).run(AgentRunRequest(task="分析资料")))
    task_record = memory_manager.get_task(str(response.task_id))

    assert task_record is not None
    assert task_record.retry_count == 1
    assert len(task_record.reflection_history) == 2
    assert task_record.reflection_result["success"] is True

