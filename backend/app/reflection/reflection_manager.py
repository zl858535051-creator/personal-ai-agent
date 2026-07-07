import logging
from typing import Any

from app.reflection.evaluator import ReflectionResult, TaskEvaluator

logger = logging.getLogger(__name__)


class ReflectionManager:
    """Coordinates reflection evaluation for Agent executions."""

    def __init__(self, evaluator: TaskEvaluator | None = None) -> None:
        self.evaluator = evaluator or TaskEvaluator()

    def reflect(
        self,
        task: str,
        plan: Any,
        steps: list[Any],
        sources: list[Any],
        answer: str,
    ) -> ReflectionResult:
        result = self.evaluator.evaluate(
            task=task,
            plan=plan,
            steps=steps,
            sources=sources,
            answer=answer,
        )
        logger.info("Reflection result: success=%s score=%s", result.success, result.score)
        return result

