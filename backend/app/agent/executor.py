import json
import logging
from dataclasses import dataclass
from typing import Any

from app.agent.planner import Plan, PlanStep
from app.agent.tool_registry import ToolExecutionError, ToolNotFoundError, ToolRegistry
from app.schemas.agent import AgentStep
from app.schemas.chat import SourceRead
from app.services.llm_service import LLMService
from app.utils.citation import render_sources

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionRecord:
    """Captured result for a single tool call."""

    step: PlanStep
    status: str
    result: Any = None
    error: str | None = None


class Executor:
    """Executes planned tool calls and asks the LLM to summarize results."""

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        self.llm_service = llm_service or LLMService()
        self.tool_registry = tool_registry

    async def execute(self, task: str, plan: Plan) -> tuple[str, list[AgentStep], list[SourceRead]]:
        records = await self._execute_steps(plan)
        sources = self._extract_sources(records)
        steps = [
            AgentStep(
                name=record.step.description,
                status=record.status,
                detail=record.error or f"tool={record.step.tool_name}",
            )
            for record in records
        ]
        answer = await self._summarize(task, plan, records, sources)
        return answer, steps, sources

    async def _execute_steps(self, plan: Plan) -> list[ToolExecutionRecord]:
        records: list[ToolExecutionRecord] = []
        for step in plan.steps:
            if self.tool_registry is None:
                records.append(ToolExecutionRecord(step=step, status="failed", error="Tool registry is not configured."))
                continue

            try:
                logger.info("Executor calling tool: %s", step.tool_name)
                result = await self.tool_registry.call_tool(step.tool_name, **step.tool_input)
                records.append(ToolExecutionRecord(step=step, status="done", result=result))
            except ToolNotFoundError as exc:
                logger.warning("Executor blocked unknown tool: %s", step.tool_name)
                records.append(ToolExecutionRecord(step=step, status="failed", error=str(exc)))
            except TypeError as exc:
                logger.exception("Executor tool parameter error: %s", step.tool_name)
                records.append(
                    ToolExecutionRecord(
                        step=step,
                        status="failed",
                        error=f"Invalid parameters for tool {step.tool_name}: {exc}",
                    )
                )
            except ToolExecutionError as exc:
                logger.exception("Executor tool failed: %s", step.tool_name)
                records.append(ToolExecutionRecord(step=step, status="failed", error=str(exc)))
        return records

    async def _summarize(
        self,
        task: str,
        plan: Plan,
        records: list[ToolExecutionRecord],
        sources: list[SourceRead],
    ) -> str:
        prompt = (
            "你是一个本地 AI Agent，请根据工具执行结果输出结构化中文结果。\n"
            f"任务类型：{plan.task_type}\n"
            f"用户任务：{task}\n\n"
            f"工具执行结果：\n{self._render_records(records)}\n\n"
            f"可引用资料：\n{render_sources(sources)}\n\n"
            "输出要求：包含结论、关键依据、风险/影响、建议动作。"
        )
        return await self.llm_service.chat_completion([{"role": "user", "content": prompt}])

    def _extract_sources(self, records: list[ToolExecutionRecord]) -> list[SourceRead]:
        sources: list[SourceRead] = []
        for record in records:
            result = record.result
            if isinstance(result, list):
                sources.extend(item for item in result if isinstance(item, SourceRead))
            elif hasattr(result, "retrieved_sources"):
                retrieved = getattr(result, "retrieved_sources")
                if isinstance(retrieved, list):
                    sources.extend(item for item in retrieved if isinstance(item, SourceRead))
        return sources

    def _render_records(self, records: list[ToolExecutionRecord]) -> str:
        if not records:
            return "No tool calls were executed."
        rendered = []
        for index, record in enumerate(records, start=1):
            payload = {
                "tool_name": record.step.tool_name,
                "tool_input": record.step.tool_input,
                "description": record.step.description,
                "status": record.status,
                "error": record.error,
                "result": self._safe_result(record.result),
            }
            rendered.append(f"[{index}] {json.dumps(payload, ensure_ascii=False, default=str)}")
        return "\n".join(rendered)

    def _safe_result(self, result: Any) -> Any:
        if isinstance(result, list):
            return [self._safe_result(item) for item in result]
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return result
