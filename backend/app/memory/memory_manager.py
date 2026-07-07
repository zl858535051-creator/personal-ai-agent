import logging
from dataclasses import dataclass
from typing import Any

from app.memory.conversation_memory import ConversationMemory, ConversationMessage
from app.memory.task_memory import TaskMemory, TaskMemoryRecord

logger = logging.getLogger(__name__)
_default_memory_manager: "MemoryManager | None" = None


@dataclass(frozen=True)
class MemoryContext:
    """Context bundle returned to Agent workflows."""

    recent_messages: list[ConversationMessage]

    def to_prompt_text(self) -> str:
        if not self.recent_messages:
            return "No recent conversation memory."
        return "\n".join(f"{message.role}: {message.content}" for message in self.recent_messages)


class MemoryManager:
    """Coordinates conversation and task memory for Agent workflows."""

    def __init__(
        self,
        conversation_memory: ConversationMemory | None = None,
        task_memory: TaskMemory | None = None,
    ) -> None:
        self.conversation_memory = conversation_memory or ConversationMemory()
        self.task_memory = task_memory or TaskMemory()

    def save_conversation(self, user_message: str, assistant_message: str) -> None:
        self.conversation_memory.add_message("user", user_message)
        self.conversation_memory.add_message("assistant", assistant_message)
        logger.info("Saved conversation turn to memory.")

    def get_context(self, limit: int = 10) -> MemoryContext:
        return MemoryContext(recent_messages=self.conversation_memory.get_recent_messages(limit=limit))

    def save_task(
        self,
        task_id: str,
        task_type: str,
        status: str,
        steps: list[dict[str, Any]] | None = None,
        tool_results: list[dict[str, Any]] | None = None,
        final_result: str = "",
        reflection_result: dict[str, Any] | None = None,
        retry_count: int = 0,
        reflection_history: list[dict[str, Any]] | None = None,
    ) -> TaskMemoryRecord:
        return self.task_memory.save_task(
            task_id=task_id,
            task_type=task_type,
            status=status,
            steps=steps,
            tool_results=tool_results,
            final_result=final_result,
            reflection_result=reflection_result,
            retry_count=retry_count,
            reflection_history=reflection_history,
        )

    def get_task(self, task_id: str) -> TaskMemoryRecord | None:
        return self.task_memory.get_task(task_id)


def get_default_memory_manager() -> MemoryManager:
    """Return the process-local memory manager used by AgentService."""
    global _default_memory_manager
    if _default_memory_manager is None:
        _default_memory_manager = MemoryManager()
    return _default_memory_manager
