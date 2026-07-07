from abc import ABC, abstractmethod
from typing import Any


class ReflectionBase(ABC):
    """Base contract for Agent reflection strategies."""

    @abstractmethod
    def evaluate(
        self,
        task: str,
        plan: Any,
        steps: list[Any],
        sources: list[Any],
        answer: str,
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def should_retry(self, result: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    def generate_feedback(self, result: Any) -> str:
        raise NotImplementedError

