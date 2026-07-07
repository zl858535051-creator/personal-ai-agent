import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.memory.base import MemoryBase

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConversationMessage:
    """A lightweight in-memory conversation message."""

    role: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


class ConversationMemory(MemoryBase):
    """Stores recent Agent conversation turns in process memory."""

    def __init__(self) -> None:
        self._messages: list[ConversationMessage] = []

    def save(self, key: str, value: Any) -> None:
        if key != "messages":
            raise KeyError(f"Unsupported conversation memory key: {key}")
        if not isinstance(value, list):
            raise TypeError("Conversation memory value must be a list.")
        self._messages = value

    def load(self, key: str) -> list[ConversationMessage]:
        if key != "messages":
            raise KeyError(f"Unsupported conversation memory key: {key}")
        return list(self._messages)

    def add_message(self, role: str, content: str) -> ConversationMessage:
        if role not in {"user", "assistant", "system"}:
            raise ValueError(f"Unsupported conversation role: {role}")
        message = ConversationMessage(role=role, content=content)
        self._messages.append(message)
        logger.info("Saved conversation memory message: role=%s", role)
        return message

    def get_recent_messages(self, limit: int = 10) -> list[ConversationMessage]:
        if limit <= 0:
            return []
        return self._messages[-limit:]

    def clear(self) -> None:
        self._messages.clear()
