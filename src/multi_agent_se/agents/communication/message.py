"""Agent通信消息定义 - 阶段18.

定义Agent间通信的消息格式：
- 消息类型
- 消息优先级
- 消息内容结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Union
import uuid


class MessageType(Enum):
    """消息类型."""
    # 任务相关
    TASK_ASSIGN = "task_assign"           # 任务分配
    TASK_COMPLETE = "task_complete"       # 任务完成
    TASK_FAILED = "task_failed"           # 任务失败
    TASK_CANCEL = "task_cancel"           # 任务取消
    
    # 协作相关
    COLLABORATION_REQUEST = "collab_request"   # 协作请求
    COLLABORATION_RESPONSE = "collab_response" # 协作响应
    COLLABORATION_RESULT = "collab_result"     # 协作结果
    
    # 状态相关
    STATUS_UPDATE = "status_update"       # 状态更新
    HEARTBEAT = "heartbeat"              # 心跳
    ERROR_REPORT = "error_report"        # 错误报告
    
    # 数据相关
    DATA_REQUEST = "data_request"        # 数据请求
    DATA_RESPONSE = "data_response"      # 数据响应
    DATA_SHARE = "data_share"            # 数据共享
    
    # 控制相关
    CONTROL_COMMAND = "control_command"  # 控制命令
    CONTROL_ACK = "control_ack"          # 控制确认
    
    # 系统相关
    SYSTEM_EVENT = "system_event"        # 系统事件
    SYSTEM_ALERT = "system_alert"        # 系统告警
    
    # 通用
    TEXT = "text"                        # 纯文本
    JSON = "json"                        # JSON数据
    BINARY = "binary"                    # 二进制数据


class MessagePriority(Enum):
    """消息优先级."""
    CRITICAL = 0     # 关键（立即处理）
    HIGH = 1         # 高优先级
    NORMAL = 2       # 普通
    LOW = 3          # 低优先级
    BACKGROUND = 4   # 后台（可延迟）


class MessageStatus(Enum):
    """消息状态."""
    PENDING = "pending"       # 待发送
    SENT = "sent"            # 已发送
    DELIVERED = "delivered"  # 已送达
    READ = "read"            # 已读
    FAILED = "failed"        # 发送失败
    EXPIRED = "expired"      # 已过期


@dataclass
class MessageHeader:
    """消息头."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None  # 关联消息ID（用于请求-响应）
    trace_id: Optional[str] = None        # 追踪ID（用于链路追踪）
    
    sender_id: str = ""                   # 发送者ID
    sender_role: str = ""                 # 发送者角色
    receiver_id: Optional[str] = None     # 接收者ID（None表示广播）
    receiver_role: Optional[str] = None   # 接收者角色（用于角色广播）
    
    message_type: MessageType = MessageType.TEXT
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None  # 过期时间
    ttl_seconds: int = 300                 # 默认TTL 5分钟
    
    def __post_init__(self) -> None:
        """初始化后处理."""
        if self.expires_at is None and self.ttl_seconds > 0:
            from datetime import timedelta
            self.expires_at = self.created_at + timedelta(seconds=self.ttl_seconds)
    
    @property
    def is_expired(self) -> bool:
        """是否已过期."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def is_broadcast(self) -> bool:
        """是否是广播消息."""
        return self.receiver_id is None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "sender_id": self.sender_id,
            "sender_role": self.sender_role,
            "receiver_id": self.receiver_id,
            "receiver_role": self.receiver_role,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "ttl_seconds": self.ttl_seconds,
            "is_expired": self.is_expired,
            "is_broadcast": self.is_broadcast,
        }


@dataclass
class Message:
    """Agent消息.
    
    完整的Agent间通信消息
    """
    header: MessageHeader = field(default_factory=MessageHeader)
    payload: Any = None                   # 消息内容
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    # 传输相关（由消息总线填充）
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    delivery_attempts: int = 0
    
    @property
    def message_id(self) -> str:
        return self.header.message_id
    
    @property
    def sender_id(self) -> str:
        return self.header.sender_id
    
    @property
    def receiver_id(self) -> Optional[str]:
        return self.header.receiver_id
    
    @property
    def message_type(self) -> MessageType:
        return self.header.message_type
    
    @property
    def priority(self) -> MessagePriority:
        return self.header.priority
    
    @property
    def is_expired(self) -> bool:
        return self.header.is_expired
    
    @property
    def is_broadcast(self) -> bool:
        return self.header.is_broadcast
    
    def mark_sent(self) -> None:
        """标记为已发送."""
        self.header.status = MessageStatus.SENT
    
    def mark_delivered(self) -> None:
        """标记为已送达."""
        self.header.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.now()
    
    def mark_read(self) -> None:
        """标记为已读."""
        self.header.status = MessageStatus.READ
        self.read_at = datetime.now()
    
    def mark_failed(self, reason: str = "") -> None:
        """标记为发送失败."""
        self.header.status = MessageStatus.FAILED
        self.metadata["failure_reason"] = reason
    
    def create_response(
        self,
        payload: Any = None,
        sender_id: str = "",
    ) -> "Message":
        """创建响应消息.
        
        Args:
            payload: 响应内容
            sender_id: 响应发送者ID
            
        Returns:
            响应消息
        """
        response_header = MessageHeader(
            correlation_id=self.header.message_id,
            trace_id=self.header.trace_id,
            sender_id=sender_id,
            receiver_id=self.header.sender_id,  # 原发送者变为接收者
            message_type=MessageType.TEXT,  # 默认文本响应
            priority=self.header.priority,
        )
        
        return Message(
            header=response_header,
            payload=payload,
            metadata={"is_response": True, "request_id": self.header.message_id},
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header.to_dict(),
            "payload": self.payload,
            "metadata": self.metadata,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "delivery_attempts": self.delivery_attempts,
        }
    
    @classmethod
    def create(
        cls,
        sender_id: str,
        receiver_id: Optional[str],
        payload: Any,
        message_type: MessageType = MessageType.TEXT,
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Message":
        """工厂方法：创建消息.
        
        Args:
            sender_id: 发送者ID
            receiver_id: 接收者ID（None表示广播）
            payload: 消息内容
            message_type: 消息类型
            priority: 优先级
            correlation_id: 关联消息ID
            trace_id: 追踪ID
            metadata: 元数据
            
        Returns:
            Message实例
        """
        header = MessageHeader(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            priority=priority,
            correlation_id=correlation_id,
            trace_id=trace_id,
        )
        
        return cls(
            header=header,
            payload=payload,
            metadata=metadata or {},
        )
    
    @classmethod
    def create_broadcast(
        cls,
        sender_id: str,
        payload: Any,
        receiver_role: Optional[str] = None,
        message_type: MessageType = MessageType.SYSTEM_EVENT,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> "Message":
        """工厂方法：创建广播消息.
        
        Args:
            sender_id: 发送者ID
            payload: 消息内容
            receiver_role: 目标角色（None表示所有Agent）
            message_type: 消息类型
            priority: 优先级
            
        Returns:
            广播消息
        """
        header = MessageHeader(
            sender_id=sender_id,
            receiver_id=None,  # 广播
            receiver_role=receiver_role,
            message_type=message_type,
            priority=priority,
        )
        
        return cls(
            header=header,
            payload=payload,
            metadata={"is_broadcast": True},
        )


# ========== 消息过滤器 ==========

class MessageFilter:
    """消息过滤器."""
    
    def __init__(
        self,
        message_types: Optional[Set[MessageType]] = None,
        priorities: Optional[Set[MessagePriority]] = None,
        senders: Optional[Set[str]] = None,
        min_priority: Optional[MessagePriority] = None,
    ) -> None:
        self.message_types = message_types
        self.priorities = priorities
        self.senders = senders
        self.min_priority = min_priority
    
    def match(self, message: Message) -> bool:
        """检查消息是否匹配过滤器."""
        if self.message_types and message.message_type not in self.message_types:
            return False
        
        if self.priorities and message.priority not in self.priorities:
            return False
        
        if self.senders and message.sender_id not in self.senders:
            return False
        
        if self.min_priority and message.priority.value > self.min_priority.value:
            return False
        
        return True


# ========== 便捷函数 ==========

def create_task_message(
    sender_id: str,
    receiver_id: str,
    task_id: str,
    task_data: Dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL,
) -> Message:
    """创建任务分配消息."""
    return Message.create(
        sender_id=sender_id,
        receiver_id=receiver_id,
        payload={"task_id": task_id, "task_data": task_data},
        message_type=MessageType.TASK_ASSIGN,
        priority=priority,
    )


def create_status_message(
    sender_id: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> Message:
    """创建状态更新消息."""
    return Message.create(
        sender_id=sender_id,
        receiver_id=None,  # 广播给控制器
        payload={"status": status, "details": details or {}},
        message_type=MessageType.STATUS_UPDATE,
        priority=MessagePriority.NORMAL,
    )
