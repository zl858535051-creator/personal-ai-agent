import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class ToolRegistryError(Exception):
    """Base exception for agent tool registry failures."""


class ToolNotFoundError(ToolRegistryError):
    """Raised when an agent asks for an unknown tool."""


class ToolExecutionError(ToolRegistryError):
    """Raised when a registered tool fails during execution."""


@dataclass(frozen=True)
class AgentTool:
    """Definition for a callable agent tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    function: Callable[..., Any]


class ToolRegistry:
    """Registry for discovering and invoking agent tools."""

    def __init__(self) -> None:
        self._tools: dict[str, AgentTool] = {}

    def register_tool(self, tool: AgentTool) -> None:
        if not tool.name:
            raise ToolRegistryError("Tool name cannot be empty.")
        if tool.name in self._tools:
            raise ToolRegistryError(f"Tool already registered: {tool.name}")

        logger.info("Registering agent tool: %s", tool.name)
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> AgentTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(f"Agent tool not found: {name}") from exc

    def list_tools(self) -> list[AgentTool]:
        return list(self._tools.values())

    async def call_tool(self, name: str, **kwargs: Any) -> Any:
        tool = self.get_tool(name)
        logger.info("Calling agent tool: %s", name)

        try:
            result = tool.function(**kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        except ToolRegistryError:
            raise
        except Exception as exc:
            logger.exception("Agent tool execution failed: %s", name)
            raise ToolExecutionError(f"Agent tool execution failed: {name}: {exc}") from exc
