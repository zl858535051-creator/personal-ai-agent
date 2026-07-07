import json
import logging
from dataclasses import dataclass, field
from typing import Any

from app.agent.tool_registry import ToolRegistry
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class PlanStep(str):
    """A structured plan step that remains compatible with string consumers."""

    tool_name: str
    tool_input: dict[str, Any]
    description: str

    def __new__(cls, tool_name: str, tool_input: dict[str, Any] | None = None, description: str = ""):
        display = description or tool_name
        instance = str.__new__(cls, display)
        instance.tool_name = tool_name
        instance.tool_input = tool_input or {}
        instance.description = display
        return instance

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "description": self.description,
        }


@dataclass
class Plan:
    task_type: str
    steps: list[PlanStep] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.steps = [self._coerce_step(step) for step in self.steps]

    def _coerce_step(self, step: PlanStep | str | dict[str, Any]) -> PlanStep:
        if isinstance(step, PlanStep):
            return step
        if isinstance(step, str):
            return PlanStep(tool_name="knowledge_search", tool_input={"query": step}, description=step)
        if isinstance(step, dict):
            return PlanStep(
                tool_name=str(step.get("tool_name") or step.get("tool") or ""),
                tool_input=step.get("tool_input") or step.get("input") or {},
                description=str(step.get("description") or step.get("tool_name") or step.get("tool") or ""),
            )
        raise TypeError(f"Unsupported plan step type: {type(step)!r}")


class Planner:
    """LLM-driven planner that only emits calls to registered tools."""

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.llm_service = llm_service or LLMService()
        self.tool_registry = tool_registry or ToolRegistry()

    async def plan(self, task: str) -> Plan:
        tools = self.tool_registry.list_tools()
        if not tools:
            logger.warning("Planner has no registered tools; using fallback plan.")
            return self._fallback_plan(task)

        try:
            response = await self.llm_service.chat_completion(self._build_messages(task, tools))
            payload = self._parse_json(response)
            return self._build_plan(payload, task)
        except Exception:
            logger.exception("Planner failed; using fallback plan.")
            return self._fallback_plan(task)

    def _build_messages(self, task: str, tools: list[Any]) -> list[dict[str, str]]:
        tool_descriptions = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in tools
        ]
        system_prompt = (
            "You are an Agent planner. Return only valid JSON. "
            "Use only tools from the provided tool list. "
            "Do not invent tool names. "
            "Schema: {\"task_type\":\"...\","
            "\"steps\":[{\"tool_name\":\"...\",\"tool_input\":{},\"description\":\"...\"}]}"
        )
        user_prompt = (
            f"User task:\n{task}\n\n"
            f"Available tools:\n{json.dumps(tool_descriptions, ensure_ascii=False)}\n\n"
            "Create the safest minimal plan."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _parse_json(self, response: str) -> dict[str, Any]:
        text = response.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("Planner response does not contain a JSON object.")
        return json.loads(text[start : end + 1])

    def _build_plan(self, payload: dict[str, Any], task: str) -> Plan:
        allowed_tools = {tool.name for tool in self.tool_registry.list_tools()}
        task_type = str(payload.get("task_type") or self._classify_task(task))
        raw_steps = payload.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError("Planner response must contain a non-empty steps list.")

        steps: list[PlanStep] = []
        for raw_step in raw_steps:
            if not isinstance(raw_step, dict):
                raise ValueError("Planner step must be an object.")
            tool_name = str(raw_step.get("tool_name") or raw_step.get("tool") or "")
            if tool_name not in allowed_tools:
                raise ValueError(f"Planner requested unavailable tool: {tool_name}")
            tool_input = raw_step.get("tool_input") or raw_step.get("input") or {}
            if not isinstance(tool_input, dict):
                tool_input = {"query": str(tool_input)}
            steps.append(
                PlanStep(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    description=str(raw_step.get("description") or tool_name),
                )
            )

        return Plan(task_type=task_type, steps=steps)

    def _fallback_plan(self, task: str) -> Plan:
        available = {tool.name for tool in self.tool_registry.list_tools()}
        if "knowledge_search" in available:
            return Plan(
                task_type=self._classify_task(task),
                steps=[
                    PlanStep(
                        tool_name="knowledge_search",
                        tool_input={"query": task},
                        description="Search the knowledge base for relevant context.",
                    )
                ],
            )
        return Plan(task_type=self._classify_task(task), steps=[])

    def _classify_task(self, task: str) -> str:
        lowered = task.lower()
        if any(keyword in lowered for keyword in ["漏洞", "vulnerability", "cve", "风险", "安全"]):
            return "security_analysis"
        if any(keyword in lowered for keyword in ["报告", "report", "总结", "summary"]):
            return "report_generation"
        return "general_analysis"
