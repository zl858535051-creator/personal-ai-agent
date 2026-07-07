import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.memory.base import MemoryBase

logger = logging.getLogger(__name__)


@dataclass
class TaskMemoryRecord:
    """In-memory record of an Agent task execution."""

    task_id: str
    task_type: str
    status: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    final_result: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status,
            "steps": self.steps,
            "tool_results": self.tool_results,
            "final_result": self.final_result,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class TaskMemory(MemoryBase):
    """Stores Agent task execution state in process memory."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskMemoryRecord] = {}

    def save(self, key: str, value: Any) -> None:
        if not isinstance(value, TaskMemoryRecord):
            raise TypeError("Task memory value must be a TaskMemoryRecord.")
        self._tasks[key] = value

    def load(self, key: str) -> TaskMemoryRecord | None:
        return self._tasks.get(key)

    def save_task(
        self,
        task_id: str,
        task_type: str,
        status: str,
        steps: list[dict[str, Any]] | None = None,
        tool_results: list[dict[str, Any]] | None = None,
        final_result: str = "",
    ) -> TaskMemoryRecord:
        record = TaskMemoryRecord(
            task_id=task_id,
            task_type=task_type,
            status=status,
            steps=steps or [],
            tool_results=tool_results or [],
            final_result=final_result,
        )
        self._tasks[task_id] = record
        logger.info("Saved task memory record: task_id=%s status=%s", task_id, status)
        return record

    def get_task(self, task_id: str) -> TaskMemoryRecord | None:
        return self._tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str) -> TaskMemoryRecord:
        record = self.get_task(task_id)
        if record is None:
            raise KeyError(f"Task memory record not found: {task_id}")
        record.status = status
        record.updated_at = datetime.now(UTC)
        logger.info("Updated task memory status: task_id=%s status=%s", task_id, status)
        return record

    def clear(self) -> None:
        self._tasks.clear()
