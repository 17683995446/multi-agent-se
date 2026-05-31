"""代码质量检查器 - 阶段22.

整合多种代码质量工具，提供统一的检查接口：
- Ruff: 静态代码检查与格式化
- 统一的问题定义和报告格式
"""

from multi_agent_se.quality.issue import (
    CodeLocation,
    FixSuggestion,
    IssueCategory,
    IssueSource,
    QualityIssue,
    QualityReport,
    Severity,
    create_issue,
)

from multi_agent_se.quality.checker import (
    QualityChecker,
    check_code,
    check_file,
    format_code,
)

__all__ = [
    # 问题定义
    "Severity",
    "IssueCategory",
    "IssueSource",
    "CodeLocation",
    "FixSuggestion",
    "QualityIssue",
    "QualityReport",
    "create_issue",
    # 检查器
    "QualityChecker",
    "check_code",
    "check_file",
    "format_code",
]
