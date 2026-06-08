"""故障恢复与自愈机制 - 第51阶段.

提供系统级故障恢复能力：
- Agent异常自动重启
- 消息总线断线重连
- 任务失败自动重试策略
- 级联故障隔离

遵循第一性原理：正交拆分、闭环自愈、最小依赖.
"""

from multi_agent_se.resilience.recovery import (
    RecoveryManager,
    RecoveryStrategy,
    RecoveryResult,
)
from multi_agent_se.resilience.retry import (
    RetryPolicy,
    ExponentialBackoff,
    CircuitBreaker,
)
from multi_agent_se.resilience.isolation import (
    FaultIsolator,
    IsolationZone,
)

__all__ = [
    # 恢复管理
    "RecoveryManager",
    "RecoveryStrategy",
    "RecoveryResult",
    # 重试策略
    "RetryPolicy",
    "ExponentialBackoff",
    "CircuitBreaker",
    # 故障隔离
    "FaultIsolator",
    "IsolationZone",
]
