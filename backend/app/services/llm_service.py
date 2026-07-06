from app.core.config import settings


class LLMService:
    """OpenAI-compatible chat client with an offline fallback response."""

    async def complete(self, messages: list[dict[str, str]]) -> str:
        if settings.llm_api_key:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
                response = await client.chat.completions.create(
                    model=settings.llm_model,
                    messages=messages,
                    temperature=0.2,
                )
                return response.choices[0].message.content or ""
            except Exception as exc:
                return f"LLM API 调用失败，已返回本地兜底结果：{exc}"

        user_message = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
        context = next((item["content"] for item in messages if item["role"] == "system"), "")
        return (
            "当前未配置 LLM_API_KEY，以下是本地兜底回答。\n\n"
            f"你的问题：{user_message}\n\n"
            "我已经根据可用的知识库上下文整理了初步结论。"
            f"\n\n上下文摘要：{context[:900]}"
        )

