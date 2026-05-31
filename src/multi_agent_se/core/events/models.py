"""事件模型定义 - 阶段27.

定义事件驱动架构的数据结构：
- 事件类型
- 事件基类
- 事件处理器
- 事件订阅
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class EventPriority(Enum):
    """事件优先级."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class DomainEvent(Enum):
    """系统预定义事件类型."""
    # Agent事件
    AGENT_CREATED = "agent.created"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    AGENT_MESSAGE = "agent.message"

    # Pipeline事件
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"
    PIPELINE_NODE_STARTED = "pipeline.node.started"
    PIPELINE_NODE_COMPLETED = "pipeline.node.completed"
    PIPELINE_NODE_FAILED = "pipeline.node.failed"

    # 任务事件
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # 质量事件
    QUALITY_CHECK_STARTED = "quality.check.started"
    QUALITY_CHECK_COMPLETED = "quality.check.completed"
    QUALITY_ISSUE_FOUND = "quality.issue.found"
    TEST_RUN_COMPLETED = "quality.test.completed"

    # 配置事件
    CONFIG_CHANGED = "config.changed"
    CONFIG_RELOADED = "config.reloaded"

    # 系统事件
    SYSTEM_STARTED = "system.started"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"


# ========== 事件基类 ==========

class Event:
    """事件基类.

    所有事件的统一接口
    """

    def __init__(
        self,
        event_type: str,
        source: str = "",
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        self.event_id = event_id or str(uuid.uuid4())[:8]
        self.event_type = event_type
        self.source = source
        self.data = data or {}
        self.priority = priority
        self.timestamp = timestamp or datetime.now()
        self.propagated: bool = False  # 是否已传播

    @property
    def type_domain(self) -> str:
        """事件类型域（如 'agent', 'pipeline'）."""
        return self.event_type.split(".")[0] if "." in self.event_type else ""

    @property
    def type_action(self) -> str:
        """事件动作（如 'created', 'completed'）."""
        return self.event_type.split(".")[1] if "." in self.event_type else self.event_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "data": self.data,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        return f"Event({self.event_type}, id={self.event_id}, src={self.source})"


# ========== 事件处理器 ==========

@dataclass
class EventHandler:
    """事件处理器.

    封装回调函数及其元信息
    """
    callback: Callable[[Event], None]
    name: str = ""
    event_type: str = ""           # 订阅的事件类型（空=通配）
    priority: EventPriority = EventPriority.NORMAL
    one_shot: bool = False          # 是否只触发一次
    filter_fn: Optional[Callable[[Event], bool]] = None  # 过滤函数
    _call_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not self.name:
            self.name = getattr(self.callback, "__name__", "anonymous")

    def should_handle(self, event: Event) -> bool:
        """判断是否应处理该事件."""
        # 类型匹配
        if self.event_type and self.event_type != event.event_type:
            # 支持通配符: "agent.*" 匹配 "agent.created"
            if not self.event_type.endswith(".*"):
                return False
            prefix = self.event_type[:-1]  # "agent."
            if not event.event_type.startswith(prefix):
                return False

        # 过滤函数
        if self.filter_fn and not self.filter_fn(event):
            return False

        return True

    def handle(self, event: Event) -> None:
        """处理事件."""
        if self.one_shot and self._call_count > 0:
            return
        self.callback(event)
        self._call_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "event_type": self.event_type or "*",
            "priority": self.priority.value,
            "one_shot": self.one_shot,
            "call_count": self._call_count,
        }


# ========== 事件订阅 ==========

@dataclass
class EventSubscription:
    """事件订阅记录."""
    subscription_id: str = ""
    handler: Optional[EventHandler] = None
    event_type: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "event_type": self.event_type,
            "handler": self.handler.to_dict() if self.handler else None,
            "created_at": self.created_at.isoformat(),
        }


# ========== 事件历史 ==========

@dataclass
class EventRecord:
    """事件记录（用于审计和调试）."""
    event: Event = field(default_factory=lambda: Event("unknown"))
    handler_name: str = ""
    handled_at: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.to_dict(),
            "handler_name": self.handler_name,
            "handled_at": self.handled_at.isoformat(),
            "success": self.success,
            "error": self.error,
        }


# ========== 便捷函数 ==========

def create_event(
    event_type: str,
    source: str = "",
    data: Optional[Dict[str, Any]] = None,
) -> Event:
    """创建事件的便捷函数."""
    return Event(event_type=event_type, source=source, data=data)


def create_handler(
    callback: Callable[[Event], None],
    event_type: str = "",
    name: str = "",
    one_shot: bool = False,
) -> EventHandler:
    """创建事件处理器的便捷函数."""
    return EventHandler(
        callback=callback,
        event_type=event_type,
        name=name,
        one_shot=one_shot,
    )
