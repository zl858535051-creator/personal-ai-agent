import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """OpenAI-compatible chat client.

    The service reads provider configuration from .env via app settings. It
    keeps the model provider behind one method so later providers can be
    swapped without touching API or RAG code.
    """

    async def chat_completion(self, messages: list[dict[str, str]]) -> str:
        """Return the assistant response for a chat-style message list."""
        if not settings.llm_api_key:
            logger.info("LLM_API_KEY is not configured; using local fallback response.")
            return self._fallback_response(messages)

        try:
            return await self._call_openai_compatible_api(messages)
        except Exception as exc:
            logger.exception("LLM chat completion failed: %s", exc)
            return (
                "LLM API 调用失败，已返回本地兜底结果。\n\n"
                f"错误信息：{exc}\n\n"
                f"{self._fallback_response(messages)}"
            )

    async def complete(self, messages: list[dict[str, str]]) -> str:
        """Backward-compatible alias for existing callers."""
        return await self.chat_completion(messages)

    async def _call_openai_compatible_api(self, messages: list[dict[str, str]]) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
        response: Any = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            logger.warning("LLM returned an empty response.")
            return ""
        return str(content)

    def _fallback_response(self, messages: list[dict[str, str]]) -> str:
        user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
        system_context = next((item["content"] for item in messages if item["role"] == "system"), "")
        return (
            "当前未配置可用的 LLM 服务，以下是本地兜底回答。\n\n"
            f"用户问题：{user_message}\n\n"
            "系统已完成消息接收和上下文整理。配置 LLM_API_KEY 后将返回真实模型回答。"
            f"\n\n上下文摘要：{system_context[:900]}"
        )
