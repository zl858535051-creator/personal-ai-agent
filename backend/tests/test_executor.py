import asyncio

from app.agent.executor import Executor
from app.agent.planner import Plan, PlanStep
from app.agent.tool_registry import AgentTool, ToolRegistry
from app.schemas.chat import SourceRead


class FakeLLM:
    def __init__(self) -> None:
        self.messages = []

    async def chat_completion(self, messages):
        self.messages = messages
        return "final answer"


def test_executor_runs_single_tool() -> None:
    registry = ToolRegistry()
    source = SourceRead(
        document_id=1,
        chunk_id=2,
        filename="demo.md",
        source_label="chunk 1",
        content="hello",
        score=0.9,
    )
    registry.register_tool(
        AgentTool(
            name="knowledge_search",
            description="Search",
            parameters={"query": {"type": "string"}},
            function=lambda query: [source],
        )
    )

    result, steps, sources = asyncio.run(
        Executor(llm_service=FakeLLM(), tool_registry=registry).execute(
            "question",
            Plan("general_analysis", [PlanStep("knowledge_search", {"query": "hello"}, "Search KB")]),
        )
    )

    assert result == "final answer"
    assert steps[0].status == "done"
    assert sources == [source]


def test_executor_runs_multiple_tools_in_order() -> None:
    calls = []
    registry = ToolRegistry()
    registry.register_tool(
        AgentTool(name="first", description="First", parameters={}, function=lambda: calls.append("first") or "a")
    )
    registry.register_tool(
        AgentTool(name="second", description="Second", parameters={}, function=lambda: calls.append("second") or "b")
    )

    result, steps, sources = asyncio.run(
        Executor(llm_service=FakeLLM(), tool_registry=registry).execute(
            "task",
            Plan(
                "general_analysis",
                [
                    PlanStep("first", {}, "First step"),
                    PlanStep("second", {}, "Second step"),
                ],
            ),
        )
    )

    assert result == "final answer"
    assert calls == ["first", "second"]
    assert [step.status for step in steps] == ["done", "done"]
    assert sources == []


def test_executor_records_tool_exception() -> None:
    def broken_tool() -> None:
        raise RuntimeError("boom")

    registry = ToolRegistry()
    registry.register_tool(AgentTool(name="broken", description="Broken", parameters={}, function=broken_tool))

    result, steps, sources = asyncio.run(
        Executor(llm_service=FakeLLM(), tool_registry=registry).execute(
            "task",
            Plan("general_analysis", [PlanStep("broken", {}, "Broken step")]),
        )
    )

    assert result == "final answer"
    assert steps[0].status == "failed"
    assert "broken" in steps[0].detail
    assert sources == []


def test_executor_passes_tool_parameters() -> None:
    seen = {}
    registry = ToolRegistry()

    def capture(query: str, top_k: int) -> list:
        seen["query"] = query
        seen["top_k"] = top_k
        return []

    registry.register_tool(
        AgentTool(
            name="knowledge_search",
            description="Search",
            parameters={"query": {"type": "string"}, "top_k": {"type": "integer"}},
            function=capture,
        )
    )

    asyncio.run(
        Executor(llm_service=FakeLLM(), tool_registry=registry).execute(
            "task",
            Plan("general_analysis", [PlanStep("knowledge_search", {"query": "abc", "top_k": 3}, "Search")]),
        )
    )

    assert seen == {"query": "abc", "top_k": 3}
