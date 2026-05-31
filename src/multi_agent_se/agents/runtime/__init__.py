"""Agent运行时集成 - 阶段20.

统一管理Agent的创建、注册、执行
"""

from multi_agent_se.agents.runtime.base_agent import (
    AgentExecutionError,
    AgentContext,
    BaseAgentImpl,
)

from multi_agent_se.agents.runtime.role_agents import (
    ControllerAgent,
    RequirementAgent,
    ArchitectAgent,
    DeveloperAgent,
    BugfixAgent,
    ReviewerAgent,
    TesterAgent,
    DocumenterAgent,
    AGENT_CLASSES,
    create_agent_by_role,
    create_all_agents,
)

from multi_agent_se.agents.runtime.runtime import (
    RuntimeError,
    RuntimeStats,
    AgentRuntime,
    get_runtime,
    reset_runtime,
)

__all__ = [
    # 基础
    "AgentExecutionError",
    "AgentContext",
    "BaseAgentImpl",
    # 角色Agent
    "ControllerAgent",
    "RequirementAgent",
    "ArchitectAgent",
    "DeveloperAgent",
    "BugfixAgent",
    "ReviewerAgent",
    "TesterAgent",
    "DocumenterAgent",
    "AGENT_CLASSES",
    "create_agent_by_role",
    "create_all_agents",
    # 运行时
    "RuntimeError",
    "RuntimeStats",
    "AgentRuntime",
    "get_runtime",
    "reset_runtime",
]
