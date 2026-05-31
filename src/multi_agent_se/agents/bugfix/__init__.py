"""Bugfix Agent模块.

第35阶段：缺陷修复Agent实现.
"""

from multi_agent_se.agents.bugfix.agent import (
    BugfixAgent,
    ErrorType,
    FixSeverity,
    ErrorLocation,
    BugReport,
    FixSuggestion,
    FixResult,
)

__all__ = [
    "BugfixAgent",
    "ErrorType",
    "FixSeverity",
    "ErrorLocation",
    "BugReport",
    "FixSuggestion",
    "FixResult",
]
