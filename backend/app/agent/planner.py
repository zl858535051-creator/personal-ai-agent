from dataclasses import dataclass


@dataclass
class Plan:
    task_type: str
    steps: list[str]


class Planner:
    """Keyword-based planner for the MVP agent workflow."""

    def plan(self, task: str) -> Plan:
        lowered = task.lower()
        if any(keyword in lowered for keyword in ["漏洞", "vulnerability", "cve", "风险", "安全"]):
            return Plan("security_analysis", ["retrieve_context", "analyze_risk", "structure_output"])
        if any(keyword in lowered for keyword in ["报告", "report", "总结", "summary"]):
            return Plan("report_generation", ["retrieve_context", "summarize", "generate_report"])
        return Plan("general_analysis", ["retrieve_context", "reason", "structure_output"])

