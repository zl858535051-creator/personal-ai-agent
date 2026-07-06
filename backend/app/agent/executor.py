from app.agent.planner import Plan
from app.schemas.agent import AgentStep
from app.schemas.chat import SourceRead
from app.services.llm_service import LLMService
from app.utils.citation import render_sources


class Executor:
    """Executes a plan with retrieved context and LLM reasoning."""

    async def execute(self, task: str, plan: Plan, sources: list[SourceRead]) -> tuple[str, list[AgentStep]]:
        steps = [AgentStep(name=step, status="done", detail="completed") for step in plan.steps]
        prompt = (
            "你是一个本地 AI Agent，请根据任务类型输出结构化中文结果。\n"
            f"任务类型：{plan.task_type}\n"
            f"任务：{task}\n\n"
            f"可用资料：\n{render_sources(sources)}\n\n"
            "输出要求：包含结论、关键依据、风险/影响、建议动作。"
        )
        result = await LLMService().chat_completion([{"role": "user", "content": prompt}])
        return result, steps
