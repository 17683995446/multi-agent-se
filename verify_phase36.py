"""第36阶段验收脚本 - Reviewer Agent验证.

验证代码审查Agent的完整功能：
- 枚举定义
- 数据模型
- 质量指标分析
- 规则检查
- 审查决策
- 审查历史追踪
"""

import sys
import traceback
from typing import Any, Dict, List

sys.path.insert(0, "/workspace/multi_agent_se/src")

from multi_agent_se.agents.reviewer import (
    ReviewerAgent,
    ReviewCategory,
    IssueSeverity,
    ReviewDecision,
    ReviewIssue,
    ReviewComment,
    QualityMetrics,
    ReviewReport,
)
from multi_agent_se.agents.runtime.base_agent import AgentContext
from multi_agent_se.scheduler.task import Task


def test_review_category_enum():
    """测试: ReviewCategory枚举."""
    print("\n[TEST] ReviewCategory枚举")
    
    assert ReviewCategory.STYLE.value == "style"
    assert ReviewCategory.LOGIC.value == "logic"
    assert ReviewCategory.PERFORMANCE.value == "performance"
    assert ReviewCategory.SECURITY.value == "security"
    assert ReviewCategory.MAINTAINABILITY.value == "maintainability"
    assert ReviewCategory.DOCUMENTATION.value == "documentation"
    assert ReviewCategory.TESTING.value == "testing"
    assert ReviewCategory.ARCHITECTURE.value == "architecture"
    
    print("  ✓ ReviewCategory枚举定义正确（8个类别）")
    return True


def test_issue_severity_enum():
    """测试: IssueSeverity枚举."""
    print("\n[TEST] IssueSeverity枚举")
    
    assert IssueSeverity.CRITICAL.value == "critical"
    assert IssueSeverity.MAJOR.value == "major"
    assert IssueSeverity.MINOR.value == "minor"
    assert IssueSeverity.INFO.value == "info"
    assert IssueSeverity.SUGGESTION.value == "suggestion"
    
    print("  ✓ IssueSeverity枚举定义正确（5个级别）")
    return True


def test_review_decision_enum():
    """测试: ReviewDecision枚举."""
    print("\n[TEST] ReviewDecision枚举")
    
    assert ReviewDecision.APPROVED.value == "approved"
    assert ReviewDecision.CHANGES_REQUESTED.value == "changes_requested"
    assert ReviewDecision.REJECTED.value == "rejected"
    assert ReviewDecision.NEEDS_DISCUSSION.value == "needs_discussion"
    
    print("  ✓ ReviewDecision枚举定义正确（4种决策）")
    return True


def test_review_issue():
    """测试: ReviewIssue数据类."""
    print("\n[TEST] ReviewIssue数据类")
    
    issue = ReviewIssue(
        category=ReviewCategory.SECURITY,
        severity=IssueSeverity.CRITICAL,
        message="eval()存在代码注入风险",
        file_path="app/utils.py",
        line_start=42,
        line_end=42,
        code_snippet="result = eval(user_input)",
        suggestion="使用ast.literal_eval()替代",
        auto_fixable=False,
        rule_id="K001",
    )
    
    assert issue.category == ReviewCategory.SECURITY
    assert issue.severity == IssueSeverity.CRITICAL
    assert issue.rule_id == "K001"
    
    data = issue.to_dict()
    assert data["category"] == "security"
    assert data["severity"] == "critical"
    assert data["auto_fixable"] is False
    
    print("  ✓ ReviewIssue数据类工作正常")
    return True


def test_quality_metrics():
    """测试: QualityMetrics数据类."""
    print("\n[TEST] QualityMetrics数据类")
    
    metrics = QualityMetrics(
        total_lines=100,
        code_lines=60,
        comment_lines=20,
        blank_lines=20,
        cyclomatic_complexity=8.0,
        cognitive_complexity=10.0,
        maintainability_index=72.5,
        duplication_rate=0.03,
        doc_coverage=0.6,
    )
    
    assert metrics.total_lines == 100
    assert metrics.code_lines == 60
    assert metrics.maintainability_index == 72.5
    
    data = metrics.to_dict()
    assert data["total_lines"] == 100
    assert "comment_ratio" in data
    assert data["doc_coverage"] == 0.6
    
    print("  ✓ QualityMetrics数据类工作正常")
    return True


def test_review_report():
    """测试: ReviewReport数据类."""
    print("\n[TEST] ReviewReport数据类")
    
    report = ReviewReport(
        target_files=["src/main.py", "src/utils.py"],
        decision=ReviewDecision.APPROVED,
        overall_score=85.0,
        critical_count=0,
        major_count=1,
        minor_count=3,
        summary="代码审查通过，总体评分85分",
        strengths=["文档覆盖良好", "可维护性较高"],
        weaknesses=["存在1个重要问题"],
    )
    
    assert report.decision == ReviewDecision.APPROVED
    assert report.overall_score == 85.0
    assert len(report.strengths) == 2
    
    data = report.to_dict()
    assert data["decision"] == "approved"
    assert data["overall_score"] == 85.0
    assert data["issue_breakdown"]["major"] == 1
    
    print("  ✓ ReviewReport数据类工作正常")
    return True


def test_agent_creation():
    """测试: ReviewerAgent创建."""
    print("\n[TEST] ReviewerAgent创建")
    
    from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
    
    agent = ReviewerAgent(agent_id="reviewer.001")
    
    assert agent.agent_id == "reviewer.001"
    assert agent.role == AgentRole.REVIEWER
    assert AgentCapability.CODE_REVIEW in agent.capabilities
    assert AgentCapability.QUALITY_CHECK in agent.capabilities
    
    print(f"  ✓ ReviewerAgent创建成功: {agent.agent_id}")
    print(f"    - 角色: {agent.role.value}")
    print(f"    - 能力: {[c.value for c in agent.capabilities]}")
    return True


def test_quality_metrics_analysis():
    """测试: 代码质量指标分析."""
    print("\n[TEST] 代码质量指标分析")
    
    agent = ReviewerAgent()
    
    code = '''"""模块文档."""
from typing import Any, Dict, List

class DataProcessor:
    """数据处理器."""
    
    def __init__(self) -> None:
        """初始化."""
        self.data: List[Dict] = []
    
    def process(self, item: Dict) -> Dict:
        """处理数据项."""
        if item and "name" in item:
            return {"result": item["name"].upper()}
        return {}
    
    def batch_process(self, items: List[Dict]) -> List[Dict]:
        """批量处理."""
        results = []
        for item in items:
            if item:
                results.append(self.process(item))
        return results
'''
    
    metrics = agent._analyze_quality_metrics(code)
    
    assert metrics.total_lines > 0
    assert metrics.code_lines > 0
    assert metrics.comment_lines > 0
    assert metrics.cyclomatic_complexity > 1.0
    assert metrics.doc_coverage > 0
    
    print(f"  ✓ 质量指标分析:")
    print(f"    - 总行数: {metrics.total_lines}")
    print(f"    - 代码行: {metrics.code_lines}")
    print(f"    - 注释行: {metrics.comment_lines}")
    print(f"    - 圈复杂度: {metrics.cyclomatic_complexity}")
    print(f"    - 文档覆盖: {metrics.doc_coverage}")
    return True


def test_rule_checks():
    """测试: 规则检查."""
    print("\n[TEST] 规则检查")
    
    agent = ReviewerAgent()
    
    # 包含安全问题的代码
    code = '''import os
import *

def process(data):
    result = eval(data)
    try:
        pass
    except:
        pass
'''
    
    issues = agent._run_rule_checks(code, ["app/bad_code.py"])
    
    assert len(issues) > 0
    
    # 应检测到安全问题
    security_issues = [i for i in issues if i.category == ReviewCategory.SECURITY]
    assert len(security_issues) > 0, "应检测到安全问题"
    
    # 应检测到通配符导入
    perf_issues = [i for i in issues if i.category == ReviewCategory.PERFORMANCE]
    assert len(perf_issues) > 0, "应检测到通配符导入"
    
    print(f"  ✓ 规则检查发现 {len(issues)} 个问题:")
    for i in issues[:4]:
        print(f"    - [{i.severity.value}] {i.message[:50]}")
    return True


def test_review_decision():
    """测试: 审查决策逻辑."""
    print("\n[TEST] 审查决策逻辑")
    
    agent = ReviewerAgent()
    
    # 测试1：高质量代码 -> APPROVED
    report_good = ReviewReport(
        overall_score=85.0,
        critical_count=0,
        major_count=0,
    )
    decision = agent._make_decision(report_good)
    assert decision == ReviewDecision.APPROVED
    print(f"  ✓ 高分代码决策: {decision.value}")
    
    # 测试2：有严重问题 -> CHANGES_REQUESTED
    report_bad = ReviewReport(
        overall_score=50.0,
        critical_count=2,
    )
    decision = agent._make_decision(report_bad)
    assert decision == ReviewDecision.CHANGES_REQUESTED
    print(f"  ✓ 有严重问题决策: {decision.value}")
    
    # 测试3：重大问题过多 -> CHANGES_REQUESTED
    report_many = ReviewReport(
        overall_score=55.0,
        critical_count=0,
        major_count=6,
    )
    decision = agent._make_decision(report_many)
    assert decision == ReviewDecision.CHANGES_REQUESTED
    print(f"  ✓ 重大问题过多决策: {decision.value}")
    
    return True


def test_agent_full_process():
    """测试: Agent完整处理流程."""
    print("\n[TEST] Agent完整处理流程")
    
    agent = ReviewerAgent(agent_id="reviewer.test")
    
    code = '''"""用户管理模块."""
from typing import Any, Dict, List, Optional

class UserManager:
    """用户管理器."""
    
    def __init__(self) -> None:
        """初始化."""
        self._users: Dict[str, Dict] = {}
    
    def add_user(self, name: str, email: str) -> Dict:
        """添加用户."""
        user = {"name": name, "email": email}
        self._users[email] = user
        return user
    
    def get_user(self, email: str) -> Optional[Dict]:
        """获取用户."""
        return self._users.get(email)
    
    def list_users(self) -> List[Dict]:
        """列出所有用户."""
        return list(self._users.values())
'''
    
    task = Task(
        task_id="task.review.001",
        task_type="code_review",
        description="审查用户管理模块",
    )
    
    context = AgentContext(
        task=task,
        input_data={
            "code": code,
            "files": ["src/user_manager.py"],
            "review_scope": "full",
        },
    )
    
    result = agent.process(context)
    
    assert result.success is True
    assert result.output is not None
    assert "report_id" in result.output
    assert "decision" in result.output
    assert "overall_score" in result.output
    assert "total_issues" in result.output
    assert "quality_metrics" in result.output
    
    print(f"  ✓ Agent处理成功:")
    print(f"    - 报告ID: {result.output['report_id']}")
    print(f"    - 决策: {result.output['decision']}")
    print(f"    - 总分: {result.output['overall_score']}")
    print(f"    - 问题数: {result.output['total_issues']}")
    print(f"    - 优点: {result.output['strengths'][:2]}")
    return True


def test_security_detection():
    """测试: 安全问题检测."""
    print("\n[TEST] 安全问题检测")
    
    agent = ReviewerAgent()
    
    dangerous_code = '''def process_input(user_input):
    result = eval(user_input)
    exec(result)
    password = "hardcoded_secret_123"
    return result
'''
    
    issues = agent._run_rule_checks(dangerous_code, ["dangerous.py"])
    security_issues = [i for i in issues if i.category == ReviewCategory.SECURITY]
    
    assert len(security_issues) >= 2, f"应检测到至少2个安全问题，实际{len(security_issues)}个"
    
    print(f"  ✓ 检测到 {len(security_issues)} 个安全问题:")
    for i in security_issues:
        print(f"    - [{i.severity.value}] {i.message}")
    return True


def test_review_history():
    """测试: 审查历史追踪."""
    print("\n[TEST] 审查历史追踪")
    
    agent = ReviewerAgent()
    
    # 执行多次审查
    for i in range(3):
        task = Task(task_id=f"task.review.{i}")
        context = AgentContext(
            task=task,
            input_data={
                "code": f"class Test{i}: pass",
                "files": [f"test{i}.py"],
            },
        )
        agent.process(context)
    
    history = agent.get_review_history()
    stats = agent.get_statistics()
    
    assert len(history) == 3
    assert stats["total_reviews"] == 3
    assert stats["avg_score"] > 0
    
    print(f"  ✓ 历史追踪正常:")
    print(f"    - 总审查数: {stats['total_reviews']}")
    print(f"    - 平均分: {stats['avg_score']}")
    print(f"    - 通过率: {stats['approval_rate']:.1%}")
    return True


def test_error_handling():
    """测试: 错误处理."""
    print("\n[TEST] 错误处理")
    
    agent = ReviewerAgent()
    
    task = Task(task_id="task.empty")
    context = AgentContext(
        task=task,
        input_data={},  # 空输入
    )
    
    result = agent.process(context)
    
    assert result.success is False
    assert "缺少代码" in result.error_message
    
    print(f"  ✓ 错误处理正确: {result.error_message}")
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第36阶段验收测试 - Reviewer Agent")
    print("=" * 60)
    
    tests = [
        ("ReviewCategory枚举", test_review_category_enum),
        ("IssueSeverity枚举", test_issue_severity_enum),
        ("ReviewDecision枚举", test_review_decision_enum),
        ("ReviewIssue数据类", test_review_issue),
        ("QualityMetrics数据类", test_quality_metrics),
        ("ReviewReport数据类", test_review_report),
        ("Agent创建", test_agent_creation),
        ("质量指标分析", test_quality_metrics_analysis),
        ("规则检查", test_rule_checks),
        ("审查决策逻辑", test_review_decision),
        ("Agent完整处理流程", test_agent_full_process),
        ("安全问题检测", test_security_detection),
        ("审查历史追踪", test_review_history),
        ("错误处理", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n  ✗ {name} 失败: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 第36阶段验收通过！Reviewer Agent实现完成。")
    else:
        print("❌ 部分测试失败，请检查实现。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
