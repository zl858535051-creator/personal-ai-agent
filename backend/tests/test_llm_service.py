import asyncio

from app.core.config import settings
from app.services.llm_service import LLMService


def test_chat_completion_uses_local_fallback_without_api_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", None)

    answer = asyncio.run(
        LLMService().chat_completion(
            [
                {"role": "system", "content": "knowledge context"},
                {"role": "user", "content": "总结文档"},
            ]
        )
    )

    assert "当前未配置可用的 LLM 服务" in answer
    assert "总结文档" in answer


def test_chat_completion_handles_api_exception(monkeypatch) -> None:
    async def raise_api_error(self, messages):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(LLMService, "_call_openai_compatible_api", raise_api_error)

    answer = asyncio.run(LLMService().chat_completion([{"role": "user", "content": "hello"}]))

    assert "LLM API 调用失败" in answer
    assert "provider unavailable" in answer


def test_complete_keeps_backward_compatibility(monkeypatch) -> None:
    monkeypatch.setattr(settings, "llm_api_key", None)

    answer = asyncio.run(LLMService().complete([{"role": "user", "content": "hello"}]))

    assert "hello" in answer
