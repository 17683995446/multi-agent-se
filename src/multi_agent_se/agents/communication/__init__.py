"""Agent通信协议 - 阶段18.

实现Agent间的消息格式定义与传递机制
"""

from multi_agent_se.agents.communication.message import (
    MessageType,
    MessagePriority,
    MessageStatus,
    MessageHeader,
    Message,
    MessageFilter,
    create_task_message,
    create_status_message,
)

from multi_agent_se.agents.communication.bus import (
    MessageBusError,
    MessageDeliveryError,
    MessageBusStats,
    MessageBus,
    send_message,
    broadcast_message,
    get_message_bus,
    reset_message_bus,
)

__all__ = [
    # 消息定义
    "MessageType",
    "MessagePriority",
    "MessageStatus",
    "MessageHeader",
    "Message",
    "MessageFilter",
    "create_task_message",
    "create_status_message",
    # 消息总线
    "MessageBusError",
    "MessageDeliveryError",
    "MessageBusStats",
    "MessageBus",
    "send_message",
    "broadcast_message",
    "get_message_bus",
    "reset_message_bus",
]
