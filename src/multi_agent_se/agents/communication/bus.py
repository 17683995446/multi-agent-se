"""Agent通信消息总线 - 阶段18.

实现Agent间的消息传递机制：
- 消息总线
- 点对点通信
- 广播通信
- 消息路由
"""

import queue
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Dict, List, Optional, Set

from multi_agent_se.agents.communication.message import (
    Message,
    MessageType,
    MessagePriority,
    MessageStatus,
    MessageFilter,
)
from multi_agent_se.agents.registry import AgentRegistry, get_registry


class MessageBusError(Exception):
    """消息总线错误."""
    pass


class MessageDeliveryError(MessageBusError):
    """消息投递错误."""
    pass


@dataclass
class MessageBusStats:
    """消息总线统计."""
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_broadcast: int = 0
    
    by_type: Dict[str, int] = field(default_factory=dict)
    by_priority: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_sent": self.total_sent,
            "total_delivered": self.total_delivered,
            "total_failed": self.total_failed,
            "total_broadcast": self.total_broadcast,
            "by_type": self.by_type,
            "by_priority": self.by_priority,
        }


class MessageBus:
    """Agent消息总线.
    
    负责Agent间的消息路由和传递
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None) -> None:
        """初始化消息总线.
        
        Args:
            registry: Agent注册表
        """
        self._registry = registry or get_registry()
        
        # 消息队列（按优先级）
        self._queues: Dict[MessagePriority, queue.Queue] = {
            priority: queue.Queue() for priority in MessagePriority
        }
        
        # 订阅者
        self._subscribers: Dict[str, Set[Callable[[Message], None]]] = {}
        self._role_subscribers: Dict[str, Set[Callable[[Message], None]]] = {}
        self._broadcast_subscribers: Set[Callable[[Message], None]] = set()
        
        # 消息历史（用于追踪）
        self._history: List[Message] = []
        self._max_history = 1000
        
        # 统计
        self._stats = MessageBusStats()
        
        # 锁
        self._lock = Lock()
    
    # ========== 发送消息 ==========
    
    def send(self, message: Message) -> bool:
        """发送消息（点对点）.
        
        Args:
            message: 消息
            
        Returns:
            是否成功入队
        """
        with self._lock:
            # 检查过期
            if message.is_expired:
                message.mark_failed("Message expired")
                self._stats.total_failed += 1
                return False
            
            # 更新统计
            self._stats.total_sent += 1
            msg_type = message.message_type.value
            self._stats.by_type[msg_type] = self._stats.by_type.get(msg_type, 0) + 1
            priority_name = message.priority.name
            self._stats.by_priority[priority_name] = self._stats.by_priority.get(priority_name, 0) + 1
            
            # 标记为已发送
            message.mark_sent()
            
            # 入队
            self._queues[message.priority].put(message)
            
            # 保存历史
            self._history.append(message)
            if len(self._history) > self._max_history:
                self._history.pop(0)
            
            return True
    
    def broadcast(self, message: Message) -> int:
        """广播消息.
        
        Args:
            message: 消息（receiver_id应为None）
            
        Returns:
            投递的订阅者数量
        """
        if not message.is_broadcast:
            raise MessageDeliveryError("Not a broadcast message")
        
        with self._lock:
            self._stats.total_broadcast += 1
            
            delivered_count = 0
            
            # 按角色广播
            if message.header.receiver_role:
                role = message.header.receiver_role
                for callback in self._role_subscribers.get(role, set()):
                    try:
                        callback(message)
                        delivered_count += 1
                    except Exception:
                        pass
            else:
                # 全局广播
                for callback in self._broadcast_subscribers:
                    try:
                        callback(message)
                        delivered_count += 1
                    except Exception:
                        pass
            
            message.mark_delivered()
            return delivered_count
    
    # ========== 订阅机制 ==========
    
    def subscribe(
        self,
        agent_id: str,
        callback: Callable[[Message], None],
    ) -> None:
        """订阅消息.
        
        Args:
            agent_id: Agent ID
            callback: 回调函数
        """
        with self._lock:
            if agent_id not in self._subscribers:
                self._subscribers[agent_id] = set()
            self._subscribers[agent_id].add(callback)
    
    def unsubscribe(
        self,
        agent_id: str,
        callback: Callable[[Message], None],
    ) -> bool:
        """取消订阅.
        
        Args:
            agent_id: Agent ID
            callback: 回调函数
            
        Returns:
            是否成功
        """
        with self._lock:
            if agent_id not in self._subscribers:
                return False
            
            try:
                self._subscribers[agent_id].remove(callback)
                return True
            except KeyError:
                return False
    
    def subscribe_by_role(
        self,
        role: str,
        callback: Callable[[Message], None],
    ) -> None:
        """按角色订阅.
        
        Args:
            role: 角色名
            callback: 回调函数
        """
        with self._lock:
            if role not in self._role_subscribers:
                self._role_subscribers[role] = set()
            self._role_subscribers[role].add(callback)
    
    def subscribe_broadcast(
        self,
        callback: Callable[[Message], None],
    ) -> None:
        """订阅广播消息.
        
        Args:
            callback: 回调函数
        """
        with self._lock:
            self._broadcast_subscribers.add(callback)
    
    def unsubscribe_broadcast(
        self,
        callback: Callable[[Message], None],
    ) -> bool:
        """取消广播订阅.
        
        Args:
            callback: 回调函数
            
        Returns:
            是否成功
        """
        with self._lock:
            try:
                self._broadcast_subscribers.remove(callback)
                return True
            except KeyError:
                return False
    
    # ========== 接收消息 ==========
    
    def receive(
        self,
        agent_id: str,
        timeout: Optional[float] = None,
        filter: Optional[MessageFilter] = None,
    ) -> Optional[Message]:
        """接收消息.
        
        Args:
            agent_id: Agent ID
            timeout: 超时时间（秒）
            filter: 消息过滤器
            
        Returns:
            消息或None
        """
        # 按优先级顺序尝试获取消息
        for priority in sorted(MessagePriority, key=lambda p: p.value):
            try:
                message = self._queues[priority].get(block=False)
                
                # 检查是否是发给该Agent的
                if message.receiver_id != agent_id and not message.is_broadcast:
                    # 不是给该Agent的，放回队列
                    self._queues[priority].put(message)
                    continue
                
                # 检查过滤器
                if filter and not filter.match(message):
                    self._queues[priority].put(message)
                    continue
                
                # 标记为已送达
                message.mark_delivered()
                self._stats.total_delivered += 1
                
                return message
                
            except queue.Empty:
                continue
        
        return None
    
    def receive_all(
        self,
        agent_id: str,
        filter: Optional[MessageFilter] = None,
    ) -> List[Message]:
        """接收所有匹配的消息.
        
        Args:
            agent_id: Agent ID
            filter: 消息过滤器
            
        Returns:
            消息列表
        """
        messages = []
        
        while True:
            message = self.receive(agent_id, filter=filter)
            if message is None:
                break
            messages.append(message)
        
        return messages
    
    # ========== 消息路由 ==========
    
    def route(self, message: Message) -> bool:
        """路由消息到目标Agent.
        
        Args:
            message: 消息
            
        Returns:
            是否成功路由
        """
        if message.is_broadcast:
            # 广播消息
            self.broadcast(message)
            return True
        
        receiver_id = message.receiver_id
        if receiver_id is None:
            return False
        
        # 检查目标Agent是否存在
        if not self._registry.has_agent(receiver_id):
            message.mark_failed(f"Agent '{receiver_id}' not found")
            return False
        
        # 发送消息
        return self.send(message)
    
    # ========== 查询与统计 ==========
    
    def get_stats(self) -> MessageBusStats:
        """获取统计信息."""
        return self._stats
    
    def get_queue_size(self, priority: Optional[MessagePriority] = None) -> int:
        """获取队列大小.
        
        Args:
            priority: 优先级（None表示所有）
            
        Returns:
            队列大小
        """
        if priority:
            return self._queues[priority].qsize()
        
        return sum(q.qsize() for q in self._queues.values())
    
    def get_history(
        self,
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Message]:
        """获取消息历史.
        
        Args:
            sender_id: 发送者ID过滤
            receiver_id: 接收者ID过滤
            limit: 限制数量
            
        Returns:
            消息列表
        """
        result = self._history[-limit:]
        
        if sender_id:
            result = [m for m in result if m.sender_id == sender_id]
        
        if receiver_id:
            result = [m for m in result if m.receiver_id == receiver_id]
        
        return result
    
    def clear(self) -> int:
        """清空所有队列.
        
        Returns:
            清空的数量
        """
        count = 0
        for q in self._queues.values():
            while not q.empty():
                try:
                    q.get(block=False)
                    count += 1
                except queue.Empty:
                    break
        return count


# ========== 便捷函数 ==========

def send_message(
    bus: MessageBus,
    sender_id: str,
    receiver_id: str,
    payload: Any,
    message_type: MessageType = MessageType.TEXT,
    priority: MessagePriority = MessagePriority.NORMAL,
) -> bool:
    """便捷函数：发送消息."""
    message = Message.create(
        sender_id=sender_id,
        receiver_id=receiver_id,
        payload=payload,
        message_type=message_type,
        priority=priority,
    )
    return bus.send(message)


def broadcast_message(
    bus: MessageBus,
    sender_id: str,
    payload: Any,
    message_type: MessageType = MessageType.SYSTEM_EVENT,
    receiver_role: Optional[str] = None,
) -> int:
    """便捷函数：广播消息."""
    message = Message.create_broadcast(
        sender_id=sender_id,
        payload=payload,
        message_type=message_type,
        receiver_role=receiver_role,
    )
    return bus.broadcast(message)


# ========== 全局实例 ==========

_global_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """获取全局消息总线."""
    global _global_bus
    if _global_bus is None:
        _global_bus = MessageBus()
    return _global_bus


def reset_message_bus() -> None:
    """重置全局消息总线."""
    global _global_bus
    if _global_bus is not None:
        _global_bus.clear()
    _global_bus = MessageBus()
