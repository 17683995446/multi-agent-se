"""消息通信模块 - 阶段4.

复用AutoGen消息通信能力，封装统一消息接口
遵循第一性原理：信息最小熵公理（信息全显式可追溯）
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class MessageType(Enum):
    """消息类型枚举."""
    TASK = "task"               # 任务消息
    RESULT = "result"           # 结果消息
    QUERY = "query"             # 查询消息
    RESPONSE = "response"       # 响应消息
    ERROR = "error"             # 错误消息
    NOTIFICATION = "notification"  # 通知消息
    NEGOTIATION = "negotiation"    # 协商消息


class MessagePriority(Enum):
    """消息优先级."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class Message:
    """消息实体 - 遵循信息最小熵公理，所有字段显式定义."""
    id: str = ""
    msg_type: MessageType = MessageType.TASK
    priority: MessagePriority = MessagePriority.NORMAL
    sender: str = ""
    receiver: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    trace_id: str = ""
    parent_msg_id: Optional[str] = None
    
    def __post_init__(self) -> None:
        """初始化后处理."""
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "id": self.id,
            "msg_type": self.msg_type.value,
            "priority": self.priority.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "trace_id": self.trace_id,
            "parent_msg_id": self.parent_msg_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建."""
        data = dict(data)
        if "msg_type" in data and isinstance(data["msg_type"], str):
            data["msg_type"] = MessageType(data["msg_type"])
        if "priority" in data and isinstance(data["priority"], int):
            data["priority"] = MessagePriority(data["priority"])
        return cls(**data)


class MessageBus:
    """消息总线 - 管理消息的发送、接收、追溯."""
    
    def __init__(self) -> None:
        """初始化消息总线."""
        self._messages: List[Message] = []
        self._pending: List[Message] = []
    
    def send(
        self,
        sender: str,
        receiver: str,
        content: str,
        msg_type: MessageType = MessageType.TASK,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: str = "",
        parent_msg_id: Optional[str] = None,
    ) -> Message:
        """发送消息.
        
        Args:
            sender: 发送方
            receiver: 接收方
            content: 消息内容
            msg_type: 消息类型
            priority: 优先级
            metadata: 元数据
            trace_id: 链路ID
            parent_msg_id: 父消息ID
            
        Returns:
            创建的消息实体
        """
        msg = Message(
            sender=sender,
            receiver=receiver,
            content=content,
            msg_type=msg_type,
            priority=priority,
            metadata=metadata or {},
            trace_id=trace_id,
            parent_msg_id=parent_msg_id,
        )
        self._messages.append(msg)
        return msg
    
    def receive(self, receiver: str) -> List[Message]:
        """接收消息.
        
        Args:
            receiver: 接收方名称
            
        Returns:
            该接收方的待处理消息列表
        """
        received = [m for m in self._messages if m.receiver == receiver and m not in self._pending]
        self._pending.extend(received)
        return received
    
    def get_history(
        self,
        sender: Optional[str] = None,
        receiver: Optional[str] = None,
        msg_type: Optional[MessageType] = None,
        trace_id: Optional[str] = None,
    ) -> List[Message]:
        """获取消息历史.
        
        Args:
            sender: 过滤发送方
            receiver: 过滤接收方
            msg_type: 过滤消息类型
            trace_id: 过滤链路ID
            
        Returns:
            匹配的消息列表
        """
        result = list(self._messages)
        if sender:
            result = [m for m in result if m.sender == sender]
        if receiver:
            result = [m for m in result if m.receiver == receiver]
        if msg_type:
            result = [m for m in result if m.msg_type == msg_type]
        if trace_id:
            result = [m for m in result if m.trace_id == trace_id]
        return result
    
    def get_conversation(
        self,
        agent_a: str,
        agent_b: str,
    ) -> List[Message]:
        """获取两个Agent之间的对话历史.
        
        Args:
            agent_a: Agent A名称
            agent_b: Agent B名称
            
        Returns:
            对话消息列表（按时间排序）
        """
        return sorted(
            [m for m in self._messages
             if (m.sender == agent_a and m.receiver == agent_b)
             or (m.sender == agent_b and m.receiver == agent_a)],
            key=lambda m: m.timestamp,
        )
    
    def get_message(self, msg_id: str) -> Optional[Message]:
        """根据ID获取消息.
        
        Args:
            msg_id: 消息ID
            
        Returns:
            消息实体
        """
        for m in self._messages:
            if m.id == msg_id:
                return m
        return None
    
    def get_message_chain(self, msg_id: str) -> List[Message]:
        """获取消息链（追溯完整对话链路）.
        
        Args:
            msg_id: 消息ID
            
        Returns:
            消息链列表
        """
        chain = []
        current_id = msg_id
        visited = set()
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            msg = self.get_message(current_id)
            if msg:
                chain.append(msg)
                current_id = msg.parent_msg_id or ""
            else:
                break
        
        return list(reversed(chain))
    
    def clear(self) -> None:
        """清空所有消息."""
        self._messages.clear()
        self._pending.clear()
    
    @property
    def total_messages(self) -> int:
        """消息总数."""
        return len(self._messages)
    
    def summary(self) -> Dict[str, Any]:
        """消息总线摘要."""
        from collections import Counter
        type_counts = Counter(m.msg_type.value for m in self._messages)
        return {
            "total_messages": len(self._messages),
            "pending_messages": len(self._pending),
            "type_distribution": dict(type_counts),
        }


# 全局消息总线实例
message_bus = MessageBus()
