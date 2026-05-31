"""事件总线引擎 - 阶段27.

提供发布/订阅模式的事件驱动通信：
- 同步/异步事件发布
- 通配符订阅
- 事件过滤
- 优先级排序
- 事件历史审计
- 中间件支持
"""

import threading
import traceback
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from multi_agent_se.core.events.models import (
    DomainEvent,
    Event,
    EventHandler,
    EventPriority,
    EventRecord,
    EventSubscription,
    create_event,
    create_handler,
)


# ========== 事件中间件 ==========

class EventMiddleware:
    """事件中间件基类."""

    def before_publish(self, event: Event) -> Optional[Event]:
        """发布前处理，返回None则取消发布."""
        return event

    def after_publish(self, event: Event, handlers_called: int) -> None:
        """发布后处理."""
        pass

    def before_handle(self, event: Event, handler: EventHandler) -> Optional[Event]:
        """处理前处理，返回None则跳过该handler."""
        return event

    def after_handle(self, event: Event, handler: EventHandler, error: Optional[str]) -> None:
        """处理后处理."""
        pass


class LoggingMiddleware(EventMiddleware):
    """日志中间件 - 记录所有事件."""

    def __init__(self) -> None:
        self.log: List[Dict[str, Any]] = []

    def before_publish(self, event: Event) -> Optional[Event]:
        self.log.append({
            "action": "publish",
            "event_type": event.event_type,
            "source": event.source,
            "timestamp": datetime.now().isoformat(),
        })
        return event

    def after_publish(self, event: Event, handlers_called: int) -> None:
        self.log.append({
            "action": "published",
            "event_id": event.event_id,
            "handlers_called": handlers_called,
        })


class ErrorHandlingMiddleware(EventMiddleware):
    """错误处理中间件 - 捕获处理器异常."""

    def __init__(self) -> None:
        self.errors: List[Dict[str, Any]] = []

    def after_handle(self, event: Event, handler: EventHandler, error: Optional[str]) -> None:
        if error:
            self.errors.append({
                "event_type": event.event_type,
                "handler": handler.name,
                "error": error,
            })


# ========== 事件总线 ==========

class EventBus:
    """事件总线.

    发布/订阅模式的核心引擎
    """

    def __init__(self, name: str = "default") -> None:
        self.name = name
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: List[EventHandler] = []
        self._subscriptions: Dict[str, EventSubscription] = {}
        self._history: List[EventRecord] = []
        self._middlewares: List[EventMiddleware] = []
        self._enabled: bool = True
        self._lock = threading.Lock()
        self._event_count: int = 0

    # ========== 订阅管理 ==========

    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Event], None],
        name: str = "",
        priority: EventPriority = EventPriority.NORMAL,
        one_shot: bool = False,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> str:
        """订阅事件.

        Args:
            event_type: 事件类型（支持通配符如 "agent.*"）
            callback: 回调函数
            name: 处理器名称
            priority: 优先级
            one_shot: 是否只触发一次
            filter_fn: 过滤函数

        Returns:
            订阅ID
        """
        handler = EventHandler(
            callback=callback,
            name=name,
            event_type=event_type,
            priority=priority,
            one_shot=one_shot,
            filter_fn=filter_fn,
        )

        sub_id = str(uuid.uuid4())[:8]
        subscription = EventSubscription(
            subscription_id=sub_id,
            handler=handler,
            event_type=event_type,
        )
        self._subscriptions[sub_id] = subscription

        with self._lock:
            if "*" in event_type:
                self._wildcard_handlers.append(handler)
            else:
                self._handlers[event_type].append(handler)

            # 按优先级排序（高优先级先执行）
            self._handlers[event_type].sort(
                key=lambda h: h.priority.value, reverse=True
            )
            self._wildcard_handlers.sort(
                key=lambda h: h.priority.value, reverse=True
            )

        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅.

        Args:
            subscription_id: 订阅ID

        Returns:
            是否成功取消
        """
        subscription = self._subscriptions.pop(subscription_id, None)
        if subscription is None or subscription.handler is None:
            return False

        handler = subscription.handler
        event_type = subscription.event_type

        with self._lock:
            if "*" in event_type:
                if handler in self._wildcard_handlers:
                    self._wildcard_handlers.remove(handler)
            else:
                if event_type in self._handlers and handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)

        return True

    def get_subscriptions(self, event_type: str = "") -> List[Dict[str, Any]]:
        """获取订阅列表."""
        result = []
        for sub in self._subscriptions.values():
            if event_type and sub.event_type != event_type:
                continue
            result.append(sub.to_dict())
        return result

    def get_handlers(self, event_type: str) -> List[EventHandler]:
        """获取某事件类型的所有处理器."""
        with self._lock:
            specific = list(self._handlers.get(event_type, []))
            wildcards = [h for h in self._wildcard_handlers if h.should_handle(
                Event(event_type=event_type)
            )]
            return specific + wildcards

    # ========== 事件发布 ==========

    def publish(self, event: Event) -> int:
        """发布事件（同步）.

        Args:
            event: 事件对象

        Returns:
            被调用的处理器数量
        """
        if not self._enabled:
            return 0

        # 中间件：发布前
        for mw in self._middlewares:
            event = mw.before_publish(event)
            if event is None:
                return 0

        handlers = self.get_handlers(event.event_type)
        handlers_called = 0

        for handler in handlers:
            # 中间件：处理前
            processed_event = event
            for mw in self._middlewares:
                processed_event = mw.before_handle(event, handler)
                if processed_event is None:
                    continue

            # 执行处理器
            error = None
            try:
                if handler.should_handle(event):
                    handler.handle(event)
                    handlers_called += 1
            except Exception as e:
                error = str(e)
                traceback.print_exc()

            # 记录历史
            self._history.append(EventRecord(
                event=event,
                handler_name=handler.name,
                success=error is None,
                error=error or "",
            ))

            # 中间件：处理后
            for mw in self._middlewares:
                mw.after_handle(event, handler, error)

        # 中间件：发布后
        for mw in self._middlewares:
            mw.after_publish(event, handlers_called)

        self._event_count += 1
        event.propagated = True

        # 清理一次性处理器
        if handlers_called > 0:
            self._cleanup_one_shot(event.event_type)

        return handlers_called

    def emit(
        self,
        event_type: str,
        source: str = "",
        data: Optional[Dict[str, Any]] = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> int:
        """快速发布事件的便捷方法.

        Args:
            event_type: 事件类型
            source: 来源
            data: 事件数据
            priority: 优先级

        Returns:
            被调用的处理器数量
        """
        event = Event(
            event_type=event_type,
            source=source,
            data=data or {},
            priority=priority,
        )
        return self.publish(event)

    # ========== 中间件管理 ==========

    def add_middleware(self, middleware: EventMiddleware) -> None:
        """添加中间件."""
        self._middlewares.append(middleware)

    def remove_middleware(self, middleware: EventMiddleware) -> bool:
        """移除中间件."""
        if middleware in self._middlewares:
            self._middlewares.remove(middleware)
            return True
        return False

    # ========== 总线控制 ==========

    def enable(self) -> None:
        """启用事件总线."""
        self._enabled = True

    def disable(self) -> None:
        """禁用事件总线."""
        self._enabled = False

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def clear(self) -> None:
        """清除所有订阅和历史."""
        with self._lock:
            self._handlers.clear()
            self._wildcard_handlers.clear()
        self._subscriptions.clear()
        self._history.clear()
        self._event_count = 0

    def clear_history(self) -> None:
        """只清除历史记录."""
        self._history.clear()

    # ========== 查询 ==========

    @property
    def event_count(self) -> int:
        """已发布的事件总数."""
        return self._event_count

    @property
    def subscription_count(self) -> int:
        """当前订阅数."""
        return len(self._subscriptions)

    def get_history(
        self,
        event_type: str = "",
        limit: int = 100,
    ) -> List[EventRecord]:
        """获取事件历史."""
        records = self._history
        if event_type:
            records = [r for r in records if r.event.event_type == event_type]
        return records[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """获取总线统计信息."""
        handler_counts: Dict[str, int] = {}
        for event_type, handlers in self._handlers.items():
            handler_counts[event_type] = len(handlers)

        return {
            "name": self.name,
            "enabled": self._enabled,
            "event_count": self._event_count,
            "subscription_count": self.subscription_count,
            "handler_counts": handler_counts,
            "wildcard_handlers": len(self._wildcard_handlers),
            "middleware_count": len(self._middlewares),
            "history_size": len(self._history),
        }

    # ========== 内部方法 ==========

    def _cleanup_one_shot(self, event_type: str) -> None:
        """清理已触发的一次性处理器."""
        to_remove = []
        with self._lock:
            for handler in self._handlers.get(event_type, []):
                if handler.one_shot and handler._call_count > 0:
                    to_remove.append(handler)
            for handler in to_remove:
                self._handlers[event_type].remove(handler)

            # 清理订阅记录
            for sub_id, sub in list(self._subscriptions.items()):
                if (sub.handler and sub.handler.one_shot
                        and sub.handler._call_count > 0):
                    self._subscriptions.pop(sub_id, None)


# ========== 全局事件总线 ==========

global_bus = EventBus(name="global")
