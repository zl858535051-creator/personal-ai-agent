from app.agent.planner import Planner


def test_planner_detects_security_task() -> None:
    plan = Planner().plan("帮我分析这个漏洞报告")
    assert plan.task_type == "security_analysis"

