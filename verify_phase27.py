#!/usr/bin/env python3
"""第27阶段验收脚本 - 事件总线.

验证内容：
- 事件枚举
- 事件创建与属性
- 事件处理器
- 事件总线（订阅/发布/取消）
- 通配符订阅
- 事件过滤
- 一次性处理器
- 优先级排序
- 中间件
- 事件历史
- 全局总线
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from multi_agent_se.core.events import (
    EventPriority,
    DomainEvent,
    Event,
    EventHandler,
    EventBus,
    EventMiddleware,
    LoggingMiddleware,
    ErrorHandlingMiddleware,
    global_bus,
    create_event,
    create_handler,
)


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name: str, passed: bool, message: str = "") -> None:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {test_name}")
    if message:
        print(f"         {message}")


def test_enums() -> bool:
    """测试枚举类型."""
    print_header("测试1: 枚举类型")

    priorities = list(EventPriority)
    print(f"  EventPriority: {[p.value for p in priorities]}")
    assert len(priorities) == 4

    domain_events = list(DomainEvent)
    print(f"  DomainEvent: {len(domain_events)}个预定义事件")
    assert len(domain_events) >= 20

    print_result("枚举类型", True, f"Priority={len(priorities)}, DomainEvent={len(domain_events)}")
    return True


def test_event_creation() -> bool:
    """测试事件创建."""
    print_header("测试2: Event 事件创建")

    e1 = create_event("agent.created", source="registry", data={"agent_id": "a1"})
    assert e1.event_type == "agent.created"
    assert e1.source == "registry"
    assert e1.data["agent_id"] == "a1"
    assert e1.type_domain == "agent"
    assert e1.type_action == "created"
    assert len(e1.event_id) > 0
    print(f"  ✓ 事件创建: {e1}")

    d = e1.to_dict()
    assert d["event_type"] == "agent.created"
    assert d["source"] == "registry"
    print(f"  ✓ to_dict() 正常")

    print_result("Event 事件创建", True)
    return True


def test_handler_creation() -> bool:
    """测试处理器创建."""
    print_header("测试3: EventHandler 处理器")

    def my_handler(event):
        pass

    h = create_handler(my_handler, event_type="agent.*", name="my_handler")
    assert h.name == "my_handler"
    assert h.event_type == "agent.*"
    print(f"  ✓ 处理器创建: {h.name}, type={h.event_type}")

    # should_handle 测试
    e1 = Event("agent.created")
    assert h.should_handle(e1) is True
    print(f"  ✓ 通配符匹配: agent.created -> True")

    e2 = Event("pipeline.started")
    assert h.should_handle(e2) is False
    print(f"  ✓ 通配符不匹配: pipeline.started -> False")

    print_result("EventHandler 处理器", True)
    return True


def test_subscribe_publish() -> bool:
    """测试订阅与发布."""
    print_header("测试4: 订阅与发布")

    bus = EventBus("test")
    received = []

    bus.subscribe("task.completed", lambda e: received.append(e.data))
    bus.emit("task.completed", source="scheduler", data={"task_id": "t1"})

    assert len(received) == 1
    assert received[0]["task_id"] == "t1"
    print(f"  ✓ 事件接收: {received[0]}")

    # 多个处理器
    count = {"n": 0}
    bus.subscribe("task.completed", lambda e: count.__setitem__("n", count["n"] + 1))
    bus.emit("task.completed", data={"task_id": "t2"})

    assert count["n"] == 1
    assert len(received) == 2
    print(f"  ✓ 多处理器: received={len(received)}, count={count['n']}")

    print_result("订阅与发布", True)
    return True


def test_unsubscribe() -> bool:
    """测试取消订阅."""
    print_header("测试5: 取消订阅")

    bus = EventBus("test")
    received = []

    sub_id = bus.subscribe("test.event", lambda e: received.append(1))
    bus.emit("test.event")
    assert len(received) == 1

    bus.unsubscribe(sub_id)
    bus.emit("test.event")
    assert len(received) == 1  # 不再触发
    print(f"  ✓ 取消订阅后不再触发")

    # 无效ID
    assert bus.unsubscribe("nonexistent") is False
    print(f"  ✓ 无效ID返回False")

    print_result("取消订阅", True)
    return True


def test_wildcard_subscription() -> bool:
    """测试通配符订阅."""
    print_header("测试6: 通配符订阅")

    bus = EventBus("test")
    received = []

    bus.subscribe("agent.*", lambda e: received.append(e.event_type))

    bus.emit("agent.created")
    bus.emit("agent.completed")
    bus.emit("pipeline.started")

    assert len(received) == 2
    assert "agent.created" in received
    assert "agent.completed" in received
    assert "pipeline.started" not in received
    print(f"  ✓ 通配符匹配: {received}")

    print_result("通配符订阅", True)
    return True


def test_event_filter() -> bool:
    """测试事件过滤."""
    print_header("测试7: 事件过滤")

    bus = EventBus("test")
    received = []

    bus.subscribe(
        "task.completed",
        lambda e: received.append(e.data),
        filter_fn=lambda e: e.data.get("priority") == "high",
    )

    bus.emit("task.completed", data={"priority": "high", "id": "t1"})
    bus.emit("task.completed", data={"priority": "low", "id": "t2"})
    bus.emit("task.completed", data={"priority": "high", "id": "t3"})

    assert len(received) == 2
    assert received[0]["id"] == "t1"
    assert received[1]["id"] == "t3"
    print(f"  ✓ 过滤结果: {len(received)}个high优先级事件")

    print_result("事件过滤", True)
    return True


def test_one_shot_handler() -> bool:
    """测试一次性处理器."""
    print_header("测试8: 一次性处理器")

    bus = EventBus("test")
    count = {"n": 0}

    bus.subscribe("once.event", lambda e: count.__setitem__("n", count["n"] + 1), one_shot=True)

    bus.emit("once.event")
    bus.emit("once.event")
    bus.emit("once.event")

    assert count["n"] == 1
    print(f"  ✓ 一次性处理器只触发1次")

    print_result("一次性处理器", True)
    return True


def test_priority_ordering() -> bool:
    """测试优先级排序."""
    print_header("测试9: 优先级排序")

    bus = EventBus("test")
    order = []

    bus.subscribe("priority.test", lambda e: order.append("low"),
                  priority=EventPriority.LOW)
    bus.subscribe("priority.test", lambda e: order.append("critical"),
                  priority=EventPriority.CRITICAL)
    bus.subscribe("priority.test", lambda e: order.append("normal"),
                  priority=EventPriority.NORMAL)
    bus.subscribe("priority.test", lambda e: order.append("high"),
                  priority=EventPriority.HIGH)

    bus.emit("priority.test")

    assert order == ["critical", "high", "normal", "low"]
    print(f"  ✓ 执行顺序: {order}")

    print_result("优先级排序", True)
    return True


def test_middleware() -> bool:
    """测试中间件."""
    print_header("测试10: 中间件")

    bus = EventBus("test")

    # 日志中间件
    logger = LoggingMiddleware()
    bus.add_middleware(logger)

    bus.emit("test.event", data={"msg": "hello"})
    assert len(logger.log) >= 2
    assert logger.log[0]["action"] == "publish"
    print(f"  ✓ 日志中间件: {len(logger.log)}条记录")

    # 错误处理中间件
    err_mw = ErrorHandlingMiddleware()
    bus.add_middleware(err_mw)

    def bad_handler(e):
        raise RuntimeError("handler error")

    bus.subscribe("error.event", bad_handler)
    bus.emit("error.event")
    assert len(err_mw.errors) == 1
    assert "handler error" in err_mw.errors[0]["error"]
    print(f"  ✓ 错误中间件捕获: {err_mw.errors[0]['error']}")

    # 移除中间件
    assert bus.remove_middleware(logger) is True
    assert bus.remove_middleware(logger) is False
    print(f"  ✓ 中间件移除正常")

    print_result("中间件", True)
    return True


def test_event_history() -> bool:
    """测试事件历史."""
    print_header("测试11: 事件历史")

    bus = EventBus("test")

    bus.subscribe("hist.event", lambda e: None)
    bus.emit("hist.event", data={"n": 1})
    bus.emit("hist.event", data={"n": 2})
    bus.emit("other.event", data={"n": 3})

    history = bus.get_history()
    assert len(history) == 2
    print(f"  ✓ 全部历史: {len(history)}条")

    filtered = bus.get_history(event_type="hist.event")
    assert len(filtered) == 2
    print(f"  ✓ 按类型过滤: {len(filtered)}条")

    limited = bus.get_history(limit=1)
    assert len(limited) == 1
    print(f"  ✓ 限制数量: {len(limited)}条")

    bus.clear_history()
    assert len(bus.get_history()) == 0
    print(f"  ✓ 清除历史正常")

    print_result("事件历史", True)
    return True


def test_bus_control() -> bool:
    """测试总线控制."""
    print_header("测试12: 总线控制")

    bus = EventBus("test")
    received = []

    bus.subscribe("ctrl.event", lambda e: received.append(1))

    bus.emit("ctrl.event")
    assert len(received) == 1

    # 禁用
    bus.disable()
    bus.emit("ctrl.event")
    assert len(received) == 1  # 不再触发
    assert bus.is_enabled is False
    print(f"  ✓ 禁用后不触发")

    # 启用
    bus.enable()
    bus.emit("ctrl.event")
    assert len(received) == 2
    print(f"  ✓ 启用后恢复")

    # 统计
    stats = bus.get_stats()
    assert stats["name"] == "test"
    print(f"  ✓ 统计: event_count={stats['event_count']}, subscription_count={stats['subscription_count']}")

    # 清除
    bus.clear()
    assert bus.subscription_count == 0
    print(f"  ✓ clear() 清除所有")

    print_result("总线控制", True)
    return True


def test_global_bus() -> bool:
    """测试全局总线."""
    print_header("测试13: 全局总线")

    received = []

    global_bus.subscribe("global.test", lambda e: received.append(e.data))
    global_bus.emit("global.test", data={"msg": "from global"})

    assert len(received) == 1
    assert received[0]["msg"] == "from global"
    print(f"  ✓ 全局总线正常: {received[0]}")

    # 清理
    global_bus.clear()
    print(f"  ✓ 全局总线已清理")

    print_result("全局总线", True)
    return True


def test_emit_convenience() -> bool:
    """测试emit便捷方法."""
    print_header("测试14: emit便捷方法")

    bus = EventBus("test")
    results = []

    bus.subscribe("quick.event", lambda e: results.append((e.event_type, e.source, e.data)))

    n = bus.emit("quick.event", source="test_source", data={"key": "val"})

    assert n == 1
    assert results[0] == ("quick.event", "test_source", {"key": "val"})
    print(f"  ✓ emit() 返回处理器数: {n}")

    print_result("emit便捷方法", True)
    return True


def main() -> int:
    print("\n" + "="*60)
    print("  第27阶段验收: 事件总线 (Event Bus)")
    print("="*60)

    tests = [
        test_enums,
        test_event_creation,
        test_handler_creation,
        test_subscribe_publish,
        test_unsubscribe,
        test_wildcard_subscription,
        test_event_filter,
        test_one_shot_handler,
        test_priority_ordering,
        test_middleware,
        test_event_history,
        test_bus_control,
        test_global_bus,
        test_emit_convenience,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"  验收结果: {passed} 通过, {failed} 失败")
    print("="*60)

    if failed == 0:
        print("\n  ✓ 第27阶段验收通过！")
        print("\n  实现功能:")
        print("    - EventPriority: 4级优先级")
        print("    - DomainEvent: 20+预定义事件类型")
        print("    - Event: 事件基类（类型/来源/数据/优先级/域/动作）")
        print("    - EventHandler: 处理器（通配符匹配/过滤/一次性）")
        print("    - EventBus: 事件总线")
        print("      - subscribe/unsubscribe（订阅管理）")
        print("      - publish/emit（事件发布）")
        print("      - 通配符订阅（agent.* 匹配所有agent事件）")
        print("      - 事件过滤（filter_fn）")
        print("      - 优先级排序（critical > high > normal > low）")
        print("      - 一次性处理器（one_shot）")
        print("      - 中间件（日志/错误处理/自定义）")
        print("      - 事件历史审计")
        print("      - 启用/禁用/清除/统计")
        print("    - global_bus: 全局事件总线实例")
        print("="*60)
        return 0
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
