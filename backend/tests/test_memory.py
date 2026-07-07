from app.memory import ConversationMemory, MemoryManager, TaskMemory


def test_conversation_memory_saves_messages() -> None:
    memory = ConversationMemory()

    memory.add_message("user", "hello")
    memory.add_message("assistant", "hi")

    messages = memory.get_recent_messages()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].content == "hi"


def test_conversation_memory_gets_recent_messages() -> None:
    memory = ConversationMemory()
    for index in range(5):
        memory.add_message("user", f"message {index}")

    messages = memory.get_recent_messages(limit=2)

    assert [message.content for message in messages] == ["message 3", "message 4"]


def test_task_memory_saves_task() -> None:
    memory = TaskMemory()

    record = memory.save_task(
        task_id="task-1",
        task_type="security_analysis",
        status="running",
        steps=[{"name": "Search", "status": "done"}],
        tool_results=[{"tool": "knowledge_search", "result": "ok"}],
        final_result="pending",
    )

    assert record.task_id == "task-1"
    assert memory.get_task("task-1") is record


def test_task_memory_updates_status() -> None:
    memory = TaskMemory()
    memory.save_task(task_id="task-1", task_type="general_analysis", status="running")

    record = memory.update_task_status("task-1", "completed")

    assert record.status == "completed"


def test_memory_manager_coordinates_memories() -> None:
    manager = MemoryManager()

    manager.save_conversation("user task", "agent answer")
    task = manager.save_task(
        task_id="1",
        task_type="general_analysis",
        status="completed",
        final_result="agent answer",
    )

    context = manager.get_context(limit=2)

    assert [message.content for message in context.recent_messages] == ["user task", "agent answer"]
    assert manager.get_task("1") is task
