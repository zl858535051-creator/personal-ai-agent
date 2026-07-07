import asyncio

import pytest

from app.agent.tool_registry import AgentTool, ToolExecutionError, ToolNotFoundError, ToolRegistry


def test_register_tool() -> None:
    registry = ToolRegistry()
    tool = AgentTool(
        name="echo",
        description="Echo input.",
        parameters={"text": {"type": "string"}},
        function=lambda text: text,
    )

    registry.register_tool(tool)

    assert registry.list_tools() == [tool]


def test_get_tool() -> None:
    registry = ToolRegistry()
    tool = AgentTool(name="noop", description="No operation.", parameters={}, function=lambda: None)
    registry.register_tool(tool)

    assert registry.get_tool("noop") is tool


def test_call_sync_tool() -> None:
    registry = ToolRegistry()
    registry.register_tool(
        AgentTool(
            name="add",
            description="Add two numbers.",
            parameters={"left": {"type": "number"}, "right": {"type": "number"}},
            function=lambda left, right: left + right,
        )
    )

    result = asyncio.run(registry.call_tool("add", left=2, right=3))

    assert result == 5


def test_call_async_tool() -> None:
    async def async_echo(text: str) -> str:
        return text

    registry = ToolRegistry()
    registry.register_tool(
        AgentTool(
            name="async_echo",
            description="Echo input asynchronously.",
            parameters={"text": {"type": "string"}},
            function=async_echo,
        )
    )

    result = asyncio.run(registry.call_tool("async_echo", text="hello"))

    assert result == "hello"


def test_unknown_tool_raises_clear_error() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError, match="Agent tool not found"):
        registry.get_tool("missing")


def test_tool_execution_exception_is_wrapped() -> None:
    def broken_tool() -> None:
        raise RuntimeError("boom")

    registry = ToolRegistry()
    registry.register_tool(
        AgentTool(name="broken", description="Broken tool.", parameters={}, function=broken_tool)
    )

    with pytest.raises(ToolExecutionError, match="broken"):
        asyncio.run(registry.call_tool("broken"))
