from abc import ABC, abstractmethod
from typing import Any


class MemoryBase(ABC):
    """Abstract memory contract for future SQLite, Redis, or vector backends."""

    @abstractmethod
    def save(self, key: str, value: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    def load(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError

