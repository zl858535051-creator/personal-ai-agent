import logging
from dataclasses import dataclass, field
from typing import Any

from app.agent.executor import Executor
from app.agent.planner import Plan, Planner
from app.agent.tool_registry import ToolRegistry
from app.reflection import ReflectionManager, ReflectionResult
from app.schemas.agent import AgentStep
from app.schemas.chat import SourceRead

logger = logging.getLogger(__name__)

MAX_RETRY = 2


@dataclass
class SelfCorrectionResult:
    """Final result of a bounded Agent self-correction run."""

    plan: Plan
    result: str
    steps: list[AgentStep]
    sources: list[SourceRead]
    reflection_result: ReflectionResult
    retry_count: int
    reflection_history: list[dict[str, Any]] = field(default_factory=list)


class SelfCorrectionManager:
    """Runs Planner -> Executor -> Reflection with a bounded retry loop."""

    def __init__(
        self,
        reflection_manager: ReflectionManager | None = None,
        max_retry: int = MAX_RETRY,
    ) -> None:
        self.reflection_manager = reflection_manager or ReflectionManager()
        self.max_retry = max(0, max_retry)

    async def run(
        self,
        task: str,
        planner_task: str,
        tool_registry: ToolRegistry,
    ) -> SelfCorrectionResult:
        retry_count = 0
        reflection_history: list[dict[str, Any]] = []
        current_planner_task = planner_task
        last_result: SelfCorrectionResult | None = None

        for attempt in range(self.max_retry + 1):
            plan, result, steps, sources, reflection = await self._attempt(
                task=task,
                planner_task=current_planner_task,
                tool_registry=tool_registry,
            )
            reflection_history.append(reflection.to_dict())
            last_result = SelfCorrectionResult(
                plan=plan,
                result=result,
                steps=steps,
                sources=sources,
                reflection_result=reflection,
                retry_count=retry_count,
                reflection_history=list(reflection_history),
            )

            if reflection.success:
                logger.info("Self-correction succeeded on attempt %s.", attempt)
                return last_result

            if attempt >= self.max_retry:
                logger.info("Self-correction reached max retry count: %s.", self.max_retry)
                return last_result

            retry_count += 1
            current_planner_task = self._build_retry_planner_task(
                task=task,
                previous_plan=plan,
                reflection=reflection,
                previous_result=result,
            )

        return last_result or self._empty_failure(task)

    async def _attempt(
        self,
        task: str,
        planner_task: str,
        tool_registry: ToolRegistry,
    ) -> tuple[Plan, str, list[AgentStep], list[SourceRead], ReflectionResult]:
        try:
            plan = await Planner(tool_registry=tool_registry).plan(planner_task)
        except Exception as exc:
            logger.exception("Planner failed during self-correction.")
            plan = Plan(task_type="planning_failed", steps=[])
            result = f"Planner failed: {exc}"
            steps: list[AgentStep] = []
            sources: list[SourceRead] = []
            return plan, result, steps, sources, self._reflection_failure(str(exc))

        try:
            result, steps, sources = await Executor(tool_registry=tool_registry).execute(task, plan)
        except Exception as exc:
            logger.exception("Executor failed during self-correction.")
            result = f"Executor failed: {exc}"
            steps = []
            sources = []

        try:
            reflection = self.reflection_manager.reflect(
                task=task,
                plan=plan,
                steps=steps,
                sources=sources,
                answer=result,
            )
        except Exception as exc:
            logger.exception("Reflection failed during self-correction.")
            reflection = self._reflection_failure(str(exc))

        return plan, result, steps, sources, reflection

    def _build_retry_planner_task(
        self,
        task: str,
        previous_plan: Plan,
        reflection: ReflectionResult,
        previous_result: str,
    ) -> str:
        return (
            "The previous agent attempt failed quality reflection.\n\n"
            f"Original task:\n{task}\n\n"
            f"Previous plan:\n{[step.to_dict() for step in previous_plan.steps]}\n\n"
            f"Reflection issues:\n{reflection.issues}\n\n"
            f"Reflection suggestions:\n{reflection.suggestions}\n\n"
            f"Previous result:\n{previous_result}\n\n"
            "Create a corrected plan using only available tools."
        )

    def _reflection_failure(self, message: str) -> ReflectionResult:
        return ReflectionResult(
            success=False,
            score=0.0,
            issues=[message],
            suggestions=["Retry with a safer plan if retry budget remains."],
        )

    def _empty_failure(self, task: str) -> SelfCorrectionResult:
        reflection = self._reflection_failure("Self-correction did not produce a result.")
        return SelfCorrectionResult(
            plan=Plan(task_type="self_correction_failed", steps=[]),
            result=f"Self-correction failed for task: {task}",
            steps=[],
            sources=[],
            reflection_result=reflection,
            retry_count=0,
            reflection_history=[reflection.to_dict()],
        )
