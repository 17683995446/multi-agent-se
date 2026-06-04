"""第46阶段验收脚本 - 消息总线可靠性增强.

验证增强后的消息总线：
- 按receiver_id分队列投递
- 消息正确送达
- 广播消息
- 队列统计
- 清空功能
"""

import sys
sys.path.insert(0, "/workspace/multi_agent_se/src")

from multi_agent_se.agents.communication.bus import MessageBus
from multi_agent_se.agents.communication.message import Message, MessageType, MessagePriority


def test_direct_delivery():
    """测试: 点对点消息直接投递."""
    print("\n[TEST] 点对点消息直接投递")
    
    bus = MessageBus()
    
    # 发送消息给特定Agent
    msg = Message.create(
        sender_id="sender.001",
        receiver_id="receiver.001",
        payload={"task": "hello"},
        priority=MessagePriority.HIGH,
    )
    sent = bus.send(msg)
    assert sent is True
    
    # receiver.001 应该能收到
    received = bus.receive("receiver.001")
    assert received is not None
    assert received.sender_id == "sender.001"
    assert received.payload == {"task": "hello"}
    print("  ✓ receiver.001 正确收到消息")
    
    # receiver.002 不应该收到
    not_received = bus.receive("receiver.002")
    assert not_received is None
    print("  ✓ receiver.002 未收到消息（正确）")
    
    # 统计验证
    stats = bus.get_stats()
    assert stats.total_sent == 1
    assert stats.total_delivered == 1
    print(f"  ✓ 统计: 发送{stats.total_sent}, 送达{stats.total_delivered}")
    
    return True


def test_multiple_receivers():
    """测试: 多个接收者独立队列."""
    print("\n[TEST] 多个接收者独立队列")
    
    bus = MessageBus()
    
    # 给不同Agent发送消息
    for i in range(5):
        msg = Message.create(
            sender_id="sender.001",
            receiver_id=f"receiver.{i:03d}",
            payload={"index": i},
        )
        bus.send(msg)
    
    # 每个Agent只收到自己的消息
    for i in range(5):
        received = bus.receive(f"receiver.{i:03d}")
        assert received is not None, f"receiver.{i:03d} 应该收到消息"
        assert received.payload["index"] == i
    
    # 没有多余消息
    extra = bus.receive("receiver.000")
    assert extra is None
    
    stats = bus.get_stats()
    assert stats.total_sent == 5
    assert stats.total_delivered == 5
    print(f"  ✓ 5条消息分别送达5个Agent")
    
    return True


def test_priority_order():
    """测试: 优先级顺序."""
    print("\n[TEST] 优先级顺序")
    
    bus = MessageBus()
    
    # 按不同优先级发送
    priorities = [
        MessagePriority.LOW,
        MessagePriority.HIGH,
        MessagePriority.NORMAL,
        MessagePriority.CRITICAL,
    ]
    
    for i, priority in enumerate(priorities):
        msg = Message.create(
            sender_id="sender.001",
            receiver_id="receiver.001",
            payload={"priority": priority.name, "index": i},
            priority=priority,
        )
        bus.send(msg)
    
    # 应该按优先级从高到低收到（同优先级内FIFO）
    expected_order = ["CRITICAL", "HIGH", "NORMAL", "LOW"]
    actual_order = []
    
    for _ in range(4):
        msg = bus.receive("receiver.001")
        assert msg is not None
        actual_order.append(msg.payload["priority"])
    
    # 验证：CRITICAL最先，LOW最后
    assert actual_order[0] == "CRITICAL", f"第一条应为CRITICAL，实际为{actual_order[0]}"
    assert actual_order[-1] == "LOW", f"最后一条应为LOW，实际为{actual_order[-1]}"
    print(f"  ✓ 优先级顺序正确: {actual_order}")
    
    return True


def test_broadcast():
    """测试: 广播消息."""
    print("\n[TEST] 广播消息")
    
    bus = MessageBus()
    
    # 注册广播订阅者
    received_by = []
    def callback(msg):
        received_by.append(msg.sender_id)
    
    bus.subscribe_broadcast(callback)
    
    # 发送广播
    msg = Message.create_broadcast(
        sender_id="broadcaster.001",
        payload={"announcement": "系统更新"},
    )
    count = bus.broadcast(msg)
    
    assert count == 1
    assert len(received_by) == 1
    print(f"  ✓ 广播消息送达 {count} 个订阅者")
    
    return True


def test_queue_size():
    """测试: 队列大小统计."""
    print("\n[TEST] 队列大小统计")
    
    bus = MessageBus()
    
    # 发送消息
    for i in range(3):
        bus.send(Message.create(
            sender_id="s", receiver_id="agent.a", payload={"i": i}
        ))
    for i in range(2):
        bus.send(Message.create(
            sender_id="s", receiver_id="agent.b", payload={"i": i}
        ))
    
    # 验证独立队列大小
    assert bus.get_queue_size(agent_id="agent.a") == 3
    assert bus.get_queue_size(agent_id="agent.b") == 2
    assert bus.get_queue_size() == 5
    print(f"  ✓ agent.a: 3, agent.b: 2, 总计: 5")
    
    return True


def test_clear():
    """测试: 清空队列."""
    print("\n[TEST] 清空队列")
    
    bus = MessageBus()
    
    for i in range(10):
        bus.send(Message.create(
            sender_id="s", receiver_id=f"agent.{i}", payload={}
        ))
    
    cleared = bus.clear()
    assert cleared == 10
    assert bus.get_queue_size() == 0
    print(f"  ✓ 清空 {cleared} 条消息")
    
    return True


def test_high_volume():
    """测试: 高吞吐量."""
    print("\n[TEST] 高吞吐量 (1000条消息)")
    
    bus = MessageBus()
    
    # 发送1000条消息
    for i in range(1000):
        bus.send(Message.create(
            sender_id="sender.001",
            receiver_id=f"receiver.{i % 10:03d}",
            payload={"index": i},
        ))
    
    # 接收所有消息
    received = 0
    for i in range(10):
        agent_id = f"receiver.{i:03d}"
        while True:
            msg = bus.receive(agent_id)
            if msg is None:
                break
            received += 1
    
    stats = bus.get_stats()
    assert stats.total_sent == 1000
    assert stats.total_delivered == 1000
    print(f"  ✓ 发送1000, 送达{stats.total_delivered}, 接收{received}")
    
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第46阶段验收测试 - 消息总线可靠性增强")
    print("=" * 60)
    
    tests = [
        ("点对点直接投递", test_direct_delivery),
        ("多个接收者独立队列", test_multiple_receivers),
        ("优先级顺序", test_priority_order),
        ("广播消息", test_broadcast),
        ("队列大小统计", test_queue_size),
        ("清空队列", test_clear),
        ("高吞吐量", test_high_volume),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"  ✓ {name} 通过")
            else:
                failed += 1
                print(f"  ✗ {name} 失败")
        except Exception as e:
            failed += 1
            print(f"  ✗ {name} 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 第46阶段验收通过！消息总线可靠性增强完成。")
    else:
        print("❌ 部分测试失败。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
