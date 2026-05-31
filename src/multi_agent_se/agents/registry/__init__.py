"""Agent注册中心 - 阶段16.

实现Agent的动态发现与注册机制
"""

from multi_agent_se.agents.registry.metadata import (
    AgentRole,
    AgentStatus,
    AgentCapability,
    AgentCapabilityDeclaration,
    AgentMetadata,
    AgentRegistrationInfo,
)

from multi_agent_se.agents.registry.agent_registry import (
    AgentRegistry,
    AgentRegistryError,
    AgentNotFoundError,
    AgentAlreadyRegisteredError,
    RegistryStats,
    get_registry,
    reset_registry,
)

from multi_agent_se.agents.registry.discovery import (
    DiscoveryResult,
    AgentDiscovery,
    discover_agents,
)

__all__ = [
    # 元数据
    "AgentRole",
    "AgentStatus",
    "AgentCapability",
    "AgentCapabilityDeclaration",
    "AgentMetadata",
    "AgentRegistrationInfo",
    # 注册表
    "AgentRegistry",
    "AgentRegistryError",
    "AgentNotFoundError",
    "AgentAlreadyRegisteredError",
    "RegistryStats",
    "get_registry",
    "reset_registry",
    # 发现
    "DiscoveryResult",
    "AgentDiscovery",
    "discover_agents",
]
