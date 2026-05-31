"""Agent生命周期管理 - 阶段17.

实现Agent的创建、初始化、暂停、恢复、销毁等生命周期管理
"""

from multi_agent_se.agents.lifecycle.lifecycle import (
    LifecycleState,
    LifecycleEvent,
    LifecycleTransition,
    LifecycleTransitionRecord,
    LifecycleStateMachine,
    LifecycleHook,
    LoggingHook,
    MetricsHook,
)

from multi_agent_se.agents.lifecycle.factory import (
    AgentCreationError,
    AgentCreationConfig,
    AgentInstance,
    AgentFactory,
    SimpleAgent,
    create_agent,
)

from multi_agent_se.agents.lifecycle.pool import (
    PoolError,
    PoolFullError,
    InstanceNotFoundError,
    PoolConfig,
    PoolStats,
    AgentPool,
    get_pool,
    reset_pool,
)

__all__ = [
    # 生命周期状态机
    "LifecycleState",
    "LifecycleEvent",
    "LifecycleTransition",
    "LifecycleTransitionRecord",
    "LifecycleStateMachine",
    "LifecycleHook",
    "LoggingHook",
    "MetricsHook",
    # 工厂
    "AgentCreationError",
    "AgentCreationConfig",
    "AgentInstance",
    "AgentFactory",
    "SimpleAgent",
    "create_agent",
    # 实例池
    "PoolError",
    "PoolFullError",
    "InstanceNotFoundError",
    "PoolConfig",
    "PoolStats",
    "AgentPool",
    "get_pool",
    "reset_pool",
]
