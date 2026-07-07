import asyncio

from app.agent.planner import PlanStep, Planner
from app.agent.tool_registry import AgentTool, ToolRegistry


class FakeLLM:
    def __init__(self, response: str | None = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error

    async def chat_completion(self, messages):
        if self.error:
            raise self.error
        return self.response or "{}"


def make_registry(*names: str) -> ToolRegistry:
    registry = ToolRegistry()
    for name in names:
        registry.register_tool(
            AgentTool(
                name=name,
                description=f"{name} description",
                parameters={"query": {"type": "string"}},
                function=lambda **kwargs: kwargs,
            )
        )
    return registry


def test_llm_planner_parses_normal_json() -> None:
    llm = FakeLLM(
        """{"task_type":"security_analysis","steps":[{"tool_name":"knowledge_search","tool_input":{"query":"SQL injection"},"description":"Search vulnerabilities"}]}"""
    )
    planner = Planner(llm_service=llm, tool_registry=make_registry("knowledge_search"))

    plan = asyncio.run(planner.plan("分析 SQL 注入漏洞"))

    assert plan.task_type == "security_analysis"
    assert plan.steps[0].tool_name == "knowledge_search"
    assert plan.steps[0].tool_input == {"query": "SQL injection"}
    assert str(plan.steps[0]) == "Search vulnerabilities"


def test_llm_planner_supports_multiple_tools() -> None:
    llm = FakeLLM(
        """{"task_type":"security_analysis","steps":[{"tool_name":"knowledge_search","tool_input":{"query":"CVE"},"description":"Search KB"},{"tool_name":"report_generator","tool_input":{"format":"markdown"},"description":"Create report"}]}"""
    )
    planner = Planner(llm_service=llm, tool_registry=make_registry("knowledge_search", "report_generator"))

    plan = asyncio.run(planner.plan("分析漏洞并生成报告"))

    assert [step.tool_name for step in plan.steps] == ["knowledge_search", "report_generator"]


def test_llm_planner_rejects_unknown_tool_and_falls_back() -> None:
    llm = FakeLLM(
        """{"task_type":"general_analysis","steps":[{"tool_name":"shell_exec","tool_input":{"cmd":"dir"},"description":"Run shell"}]}"""
    )
    planner = Planner(llm_service=llm, tool_registry=make_registry("knowledge_search"))

    plan = asyncio.run(planner.plan("运行命令"))

    assert plan.steps[0].tool_name == "knowledge_search"
    assert plan.steps[0].tool_input == {"query": "运行命令"}


def test_llm_planner_handles_json_parse_failure() -> None:
    planner = Planner(llm_service=FakeLLM("not json"), tool_registry=make_registry("knowledge_search"))

    plan = asyncio.run(planner.plan("总结资料"))

    assert plan.task_type == "report_generation"
    assert plan.steps[0].tool_name == "knowledge_search"


def test_llm_planner_handles_llm_exception() -> None:
    planner = Planner(
        llm_service=FakeLLM(error=RuntimeError("provider down")),
        tool_registry=make_registry("knowledge_search"),
    )

    plan = asyncio.run(planner.plan("hello"))

    assert plan.task_type == "general_analysis"
    assert plan.steps[0].tool_name == "knowledge_search"


def test_plan_step_is_string_compatible() -> None:
    step = PlanStep("knowledge_search", {"query": "abc"}, "Search context")

    assert isinstance(step, str)
    assert step == "Search context"
