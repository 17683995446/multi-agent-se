#!/usr/bin/env python3
"""第18阶段验收脚本 - Agent通信协议.

验证内容：
1. 消息格式定义 (message.py)
2. 消息总线实现 (bus.py)
3. 点对点与广播通信
4. 统一导出接口 (__init__.py)
"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, "/workspace/multi_agent_se/src")


def print_header(title: str) -> None:
    """打印标题."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    """打印测试结果."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test_name}")
    if details:
        print(f"       {details}")


def main() -> int:
    """主函数."""
    print_header("第18阶段验收：Agent通信协议")
    
    passed = 0
    failed = 0
    
    # ========== 1. 测试消息格式定义 ==========
    print_header("1. 消息格式定义 (message.py)")
    
    try:
        from multi_agent_se.agents.communication import (
            MessageType,
            MessagePriority,
            MessageStatus,
            MessageHeader,
            Message,
            MessageFilter,
            create_task_message,
            create_status_message,
        )
        print_result("导入消息模块", True)
        passed += 1
    except Exception as e:
        print_result("导入消息模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 MessageType 枚举
    try:
        assert MessageType.TASK_ASSIGN.value == "task_assign"
        assert MessageType.TASK_COMPLETE.value == "task_complete"
        assert MessageType.STATUS_UPDATE.value == "status_update"
        assert MessageType.HEARTBEAT.value == "heartbeat"
        assert MessageType.SYSTEM_EVENT.value == "system_event"
        assert MessageType.TEXT.value == "text"
        assert len(MessageType) >= 15  # 至少15种消息类型
        print_result("MessageType 枚举定义", True, f"共{len(MessageType)}种类型")
        passed += 1
    except Exception as e:
        print_result("MessageType 枚举定义", False, str(e))
        failed += 1
    
    # 测试 MessagePriority 枚举
    try:
        assert MessagePriority.CRITICAL.value == 0
        assert MessagePriority.HIGH.value == 1
        assert MessagePriority.NORMAL.value == 2
        assert MessagePriority.LOW.value == 3
        assert MessagePriority.BACKGROUND.value == 4
        assert len(MessagePriority) == 5
        print_result("MessagePriority 枚举定义", True, f"共{len(MessagePriority)}级优先级")
        passed += 1
    except Exception as e:
        print_result("MessagePriority 枚举定义", False, str(e))
        failed += 1
    
    # 测试 MessageStatus 枚举
    try:
        assert MessageStatus.PENDING.value == "pending"
        assert MessageStatus.SENT.value == "sent"
        assert MessageStatus.DELIVERED.value == "delivered"
        assert MessageStatus.READ.value == "read"
        assert MessageStatus.FAILED.value == "failed"
        assert MessageStatus.EXPIRED.value == "expired"
        print_result("MessageStatus 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("MessageStatus 枚举定义", False, str(e))
        failed += 1
    
    # 测试 MessageHeader
    try:
        header = MessageHeader(
            sender_id="agent.sender",
            receiver_id="agent.receiver",
            message_type=MessageType.TEXT,
            priority=MessagePriority.HIGH,
            ttl_seconds=60,
        )
        
        assert header.sender_id == "agent.sender"
        assert header.receiver_id == "agent.receiver"
        assert header.message_type == MessageType.TEXT
        assert header.priority == MessagePriority.HIGH
        assert header.ttl_seconds == 60
        assert header.is_broadcast == False
        assert header.is_expired == False
        assert "message_id" in header.to_dict()
        
        print_result("MessageHeader 数据类", True)
        passed += 1
    except Exception as e:
        print_result("MessageHeader 数据类", False, str(e))
        failed += 1
    
    # 测试 Message
    try:
        message = Message.create(
            sender_id="agent.sender",
            receiver_id="agent.receiver",
            payload={"content": "Hello"},
            message_type=MessageType.TEXT,
            priority=MessagePriority.NORMAL,
        )
        
        assert message.sender_id == "agent.sender"
        assert message.receiver_id == "agent.receiver"
        assert message.payload == {"content": "Hello"}
        assert message.message_type == MessageType.TEXT
        assert message.priority == MessagePriority.NORMAL
        
        print_result("Message.create 工厂方法", True)
        passed += 1
    except Exception as e:
        print_result("Message.create 工厂方法", False, str(e))
        failed += 1
    
    # 测试消息状态转换
    try:
        message = Message.create(
            sender_id="agent.sender",
            receiver_id="agent.receiver",
            payload="test",
        )
        
        assert message.header.status == MessageStatus.PENDING
        
        message.mark_sent()
        assert message.header.status == MessageStatus.SENT
        
        message.mark_delivered()
        assert message.header.status == MessageStatus.DELIVERED
        assert message.delivered_at is not None
        
        message.mark_read()
        assert message.header.status == MessageStatus.READ
        assert message.read_at is not None
        
        print_result("消息状态转换", True)
        passed += 1
    except Exception as e:
        print_result("消息状态转换", False, str(e))
        failed += 1
    
    # 测试广播消息
    try:
        broadcast = Message.create_broadcast(
            sender_id="agent.controller",
            payload={"event": "system_start"},
            message_type=MessageType.SYSTEM_EVENT,
            receiver_role="developer",
        )
        
        assert broadcast.is_broadcast == True
        assert broadcast.receiver_id is None
        assert broadcast.header.receiver_role == "developer"
        assert broadcast.message_type == MessageType.SYSTEM_EVENT
        
        print_result("Message.create_broadcast 广播消息", True)
        passed += 1
    except Exception as e:
        print_result("Message.create_broadcast 广播消息", False, str(e))
        failed += 1
    
    # 测试响应消息创建
    try:
        request = Message.create(
            sender_id="agent.a",
            receiver_id="agent.b",
            payload="request",
        )
        
        response = request.create_response(
            payload="response",
            sender_id="agent.b",
        )
        
        assert response.header.correlation_id == request.message_id
        assert response.header.receiver_id == "agent.a"
        assert response.header.sender_id == "agent.b"
        assert response.metadata.get("is_response") == True
        
        print_result("Message.create_response 响应消息", True)
        passed += 1
    except Exception as e:
        print_result("Message.create_response 响应消息", False, str(e))
        failed += 1
    
    # 测试消息过期
    try:
        from datetime import datetime, timedelta
        
        expired_header = MessageHeader(
            sender_id="agent.sender",
            receiver_id="agent.receiver",
            created_at=datetime.now() - timedelta(seconds=10),
            ttl_seconds=5,  # 5秒前已过期
        )
        
        expired_message = Message(header=expired_header, payload="test")
        assert expired_message.is_expired == True
        
        print_result("消息过期检测", True)
        passed += 1
    except Exception as e:
        print_result("消息过期检测", False, str(e))
        failed += 1
    
    # 测试 MessageFilter
    try:
        filter = MessageFilter(
            message_types={MessageType.TEXT, MessageType.JSON},
            min_priority=MessagePriority.NORMAL,
        )
        
        message1 = Message.create(
            sender_id="agent.a",
            receiver_id="agent.b",
            payload="test",
            message_type=MessageType.TEXT,
            priority=MessagePriority.NORMAL,
        )
        
        message2 = Message.create(
            sender_id="agent.a",
            receiver_id="agent.b",
            payload="test",
            message_type=MessageType.BINARY,  # 不匹配
            priority=MessagePriority.NORMAL,
        )
        
        message3 = Message.create(
            sender_id="agent.a",
            receiver_id="agent.b",
            payload="test",
            message_type=MessageType.TEXT,
            priority=MessagePriority.LOW,  # 低于min_priority
        )
        
        assert filter.match(message1) == True
        assert filter.match(message2) == False
        assert filter.match(message3) == False  # LOW > NORMAL
        
        print_result("MessageFilter 过滤器", True)
        passed += 1
    except Exception as e:
        print_result("MessageFilter 过滤器", False, str(e))
        failed += 1
    
    # 测试便捷函数
    try:
        task_msg = create_task_message(
            sender_id="agent.controller",
            receiver_id="agent.developer",
            task_id="task-001",
            task_data={"action": "write_code"},
            priority=MessagePriority.HIGH,
        )
        
        assert task_msg.message_type == MessageType.TASK_ASSIGN
        assert task_msg.priority == MessagePriority.HIGH
        assert task_msg.payload["task_id"] == "task-001"
        
        status_msg = create_status_message(
            sender_id="agent.developer",
            status="working",
            details={"progress": 50},
        )
        
        assert status_msg.message_type == MessageType.STATUS_UPDATE
        assert status_msg.payload["status"] == "working"
        
        print_result("便捷函数 create_task_message/create_status_message", True)
        passed += 1
    except Exception as e:
        print_result("便捷函数", False, str(e))
        failed += 1
    
    # ========== 2. 测试消息总线 ==========
    print_header("2. 消息总线实现 (bus.py)")
    
    try:
        from multi_agent_se.agents.communication import (
            MessageBusError,
            MessageDeliveryError,
            MessageBusStats,
            MessageBus,
            send_message,
            broadcast_message,
            get_message_bus,
            reset_message_bus,
        )
        from multi_agent_se.agents.registry import reset_registry, discover_agents
        print_result("导入消息总线模块", True)
        passed += 1
    except Exception as e:
        print_result("导入消息总线模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 MessageBus 创建
    try:
        reset_registry()
        discover_agents(include_builtin=True)  # 注册内置Agent
        
        bus = MessageBus()
        assert bus is not None
        assert bus.get_queue_size() == 0
        
        print_result("MessageBus 创建", True)
        passed += 1
    except Exception as e:
        print_result("MessageBus 创建", False, str(e))
        failed += 1
    
    # 测试点对点发送
    try:
        message = Message.create(
            sender_id="builtin.controller",
            receiver_id="builtin.developer",
            payload={"task": "write_code"},
            message_type=MessageType.TASK_ASSIGN,
            priority=MessagePriority.HIGH,
        )
        
        result = bus.send(message)
        assert result == True
        assert bus.get_queue_size() == 1
        assert bus.get_queue_size(MessagePriority.HIGH) == 1
        
        stats = bus.get_stats()
        assert stats.total_sent == 1
        
        print_result("点对点消息发送", True)
        passed += 1
    except Exception as e:
        print_result("点对点消息发送", False, str(e))
        failed += 1
    
    # 测试消息接收
    try:
        received = bus.receive("builtin.developer")
        assert received is not None
        assert received.payload == {"task": "write_code"}
        assert received.header.status == MessageStatus.DELIVERED
        
        stats = bus.get_stats()
        assert stats.total_delivered == 1
        
        print_result("消息接收", True, f"收到消息: {received.payload}")
        passed += 1
    except Exception as e:
        print_result("消息接收", False, str(e))
        failed += 1
    
    # 测试订阅机制
    try:
        received_messages = []
        
        def callback(msg):
            received_messages.append(msg)
        
        bus.subscribe("builtin.tester", callback)
        
        # 发送消息给订阅者
        message = Message.create(
            sender_id="builtin.controller",
            receiver_id="builtin.tester",
            payload="test",
        )
        bus.send(message)
        
        # 接收消息
        received = bus.receive("builtin.tester")
        assert received is not None
        
        # 取消订阅
        result = bus.unsubscribe("builtin.tester", callback)
        assert result == True
        
        print_result("订阅/取消订阅机制", True)
        passed += 1
    except Exception as e:
        print_result("订阅/取消订阅机制", False, str(e))
        failed += 1
    
    # 测试广播
    try:
        reset_message_bus()
        reset_registry()
        discover_agents(include_builtin=True)
        bus = get_message_bus()
        
        broadcast_received = []
        
        def broadcast_callback(msg):
            broadcast_received.append(msg)
        
        bus.subscribe_broadcast(broadcast_callback)
        
        # 发送广播
        broadcast = Message.create_broadcast(
            sender_id="builtin.controller",
            payload={"event": "system_alert"},
            message_type=MessageType.SYSTEM_ALERT,
        )
        
        count = bus.broadcast(broadcast)
        assert count >= 1  # 至少有一个订阅者收到
        assert len(broadcast_received) >= 1
        
        stats = bus.get_stats()
        assert stats.total_broadcast == 1
        
        print_result("广播消息", True, f"投递到{count}个订阅者")
        passed += 1
    except Exception as e:
        print_result("广播消息", False, str(e))
        failed += 1
    
    # 测试按角色广播
    try:
        role_received = []
        
        def role_callback(msg):
            role_received.append(msg)
        
        bus.subscribe_by_role("developer", role_callback)
        
        # 发送角色广播
        broadcast = Message.create_broadcast(
            sender_id="builtin.controller",
            payload={"task": "new_project"},
            receiver_role="developer",
        )
        
        count = bus.broadcast(broadcast)
        assert len(role_received) >= 1
        
        print_result("按角色广播", True, f"投递到{count}个订阅者")
        passed += 1
    except Exception as e:
        print_result("按角色广播", False, str(e))
        failed += 1
    
    # 测试消息路由
    try:
        reset_registry()
        discover_agents(include_builtin=True)
        reset_message_bus()  # 在registry之后重置，确保使用同一个registry
        bus = get_message_bus()
        
        # 路由点对点消息
        message = Message.create(
            sender_id="builtin.controller",
            receiver_id="builtin.developer",
            payload="routed",
        )
        
        result = bus.route(message)
        assert result == True
        
        # 路由广播消息
        broadcast = Message.create_broadcast(
            sender_id="builtin.controller",
            payload="broadcast_routed",
        )
        
        result = bus.route(broadcast)
        assert result == True
        
        print_result("消息路由", True)
        passed += 1
    except Exception as e:
        print_result("消息路由", False, str(e))
        failed += 1
    
    # 测试消息历史
    try:
        reset_message_bus()
        reset_registry()
        discover_agents(include_builtin=True)
        bus = get_message_bus()
        
        # 发送多条消息
        for i in range(5):
            message = Message.create(
                sender_id="builtin.controller",
                receiver_id="builtin.developer",
                payload=f"msg-{i}",
            )
            bus.send(message)
        
        history = bus.get_history(limit=3)
        assert len(history) == 3
        
        filtered_history = bus.get_history(
            sender_id="builtin.controller",
            limit=10,
        )
        assert len(filtered_history) == 5
        
        print_result("消息历史", True, f"历史记录{len(filtered_history)}条")
        passed += 1
    except Exception as e:
        print_result("消息历史", False, str(e))
        failed += 1
    
    # 测试清空队列
    try:
        count = bus.clear()
        assert count == 5  # 清空了之前发送的5条
        assert bus.get_queue_size() == 0
        
        print_result("清空队列", True, f"清空了{count}条消息")
        passed += 1
    except Exception as e:
        print_result("清空队列", False, str(e))
        failed += 1
    
    # 测试便捷函数
    try:
        reset_message_bus()
        reset_registry()
        discover_agents(include_builtin=True)
        bus = get_message_bus()
        
        result = send_message(
            bus=bus,
            sender_id="builtin.controller",
            receiver_id="builtin.developer",
            payload="convenience",
            message_type=MessageType.TEXT,
            priority=MessagePriority.HIGH,
        )
        assert result == True
        
        count = broadcast_message(
            bus=bus,
            sender_id="builtin.controller",
            payload="broadcast_convenience",
        )
        assert count >= 0
        
        print_result("便捷函数 send_message/broadcast_message", True)
        passed += 1
    except Exception as e:
        print_result("便捷函数", False, str(e))
        failed += 1
    
    # 测试全局消息总线
    try:
        reset_message_bus()
        bus1 = get_message_bus()
        bus2 = get_message_bus()
        
        assert bus1 is bus2  # 同一个实例
        
        print_result("全局消息总线", True)
        passed += 1
    except Exception as e:
        print_result("全局消息总线", False, str(e))
        failed += 1
    
    # ========== 3. 测试统一导出接口 ==========
    print_header("3. 统一导出接口 (__init__.py)")
    
    try:
        from multi_agent_se.agents.communication import __all__
        
        expected_exports = [
            # 消息定义
            "MessageType", "MessagePriority", "MessageStatus",
            "MessageHeader", "Message", "MessageFilter",
            "create_task_message", "create_status_message",
            # 消息总线
            "MessageBusError", "MessageDeliveryError", "MessageBusStats",
            "MessageBus", "send_message", "broadcast_message",
            "get_message_bus", "reset_message_bus",
        ]
        
        for export in expected_exports:
            assert export in __all__, f"缺少导出: {export}"
        
        print_result("__all__ 导出列表完整", True, f"共{len(__all__)}个导出")
        passed += 1
    except Exception as e:
        print_result("__all__ 导出列表完整", False, str(e))
        failed += 1
    
    # ========== 验收总结 ==========
    print_header("验收总结")
    total = passed + failed
    print(f"  总测试数: {total}")
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")
    print(f"  通过率: {passed/total*100:.1f}%")
    
    if failed == 0:
        print("\n  🎉 第18阶段验收通过！")
        return 0
    else:
        print(f"\n  ⚠️ 第18阶段有 {failed} 项测试未通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
