"""事件总线 - 阶段27.

发布/订阅模式的事件驱动通信：
- 事件定义与创建
- 事件处理器（通配符/过滤/一次性）
- 事件总线（发布/订阅/中间件/历史审计）
"""

from multi_agent_se.core.events.models import (
    EventPriority,
    DomainEvent,
    Event,
    EventHandler,
    EventSubscription,
    EventRecord,
    create_event,
    create_handler,
)

from multi_agent_se.core.events.bus import (
    EventBus,
    EventMiddleware,
    LoggingMiddleware,
    ErrorHandlingMiddleware,
    global_bus,
)

__all__ = [
    # 模型
    "EventPriority",
    "DomainEvent",
    "Event",
    "EventHandler",
    "EventSubscription",
    "EventRecord",
    # 便捷函数
    "create_event",
    "create_handler",
    # 总线
    "EventBus",
    "EventMiddleware",
    "LoggingMiddleware",
    "ErrorHandlingMiddleware",
    "global_bus",
]
