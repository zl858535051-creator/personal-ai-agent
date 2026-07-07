import logging
from dataclasses import dataclass, field
from typing import Any

from app.reflection.base import ReflectionBase

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReflectionResult:
    """Structured quality signal for one Agent execution."""

    success: bool
    score: float
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "score": self.score,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


class TaskEvaluator(ReflectionBase):
    """Rule-based evaluator for first-stage Agent reflection."""

    failure_markers = (
        "failed",
        "error",
        "exception",
        "traceback",
        "not found",
        "失败",
        "错误",
        "异常",
        "无法",
    )

    def evaluate(
        self,
        task: str,
        plan: Any,
        steps: list[Any],
        sources: list[Any],
        answer: str,
    ) -> ReflectionResult:
        issues: list[str] = []
        suggestions: list[str] = []
        score = 1.0

        if not steps:
            issues.append("No tool execution steps were recorded.")
            suggestions.append("Ensure the planner emits at least one valid tool step.")
            score -= 0.3
        elif not any(getattr(step, "status", "") == "done" for step in steps):
            issues.append("No tool step completed successfully.")
            suggestions.append("Review tool names, tool inputs, and registry configuration.")
            score -= 0.35

        failed_steps = [step for step in steps if getattr(step, "status", "") == "failed"]
        if failed_steps:
            issues.append(f"{len(failed_steps)} tool step(s) failed.")
            suggestions.append("Inspect failed tool details before trusting the final answer.")
            score -= min(0.3, 0.12 * len(failed_steps))

        if not answer or not answer.strip():
            issues.append("The final answer is empty.")
            suggestions.append("Regenerate the answer after verifying tool outputs.")
            score -= 0.4
        elif len(answer.strip()) < 20:
            issues.append("The final answer is very short.")
            suggestions.append("Ask the LLM to provide a more complete structured answer.")
            score -= 0.15

        lowered_answer = answer.lower()
        if any(marker in lowered_answer for marker in self.failure_markers):
            issues.append("The final answer contains obvious failure language.")
            suggestions.append("Review execution errors and consider replanning.")
            score -= 0.25

        if not sources:
            suggestions.append("No citation sources were returned; verify whether the task required knowledge retrieval.")
            score -= 0.05

        normalized_score = round(max(0.0, min(1.0, score)), 3)
        success = normalized_score >= 0.7 and not any("empty" in issue.lower() for issue in issues)
        logger.info("Reflection evaluated task: success=%s score=%s", success, normalized_score)
        return ReflectionResult(
            success=success,
            score=normalized_score,
            issues=issues,
            suggestions=suggestions,
        )

    def should_retry(self, result: ReflectionResult) -> bool:
        return not result.success and result.score < 0.6

    def generate_feedback(self, result: ReflectionResult) -> str:
        if result.success:
            return "Reflection passed; no retry needed."
        parts = []
        if result.issues:
            parts.append("Issues: " + "; ".join(result.issues))
        if result.suggestions:
            parts.append("Suggestions: " + "; ".join(result.suggestions))
        return "\n".join(parts) or "Reflection failed without detailed feedback."

