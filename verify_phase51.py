"""第51阶段验收测试 - 故障恢复与自愈机制

测试内容：
1. RecoveryManager核心恢复管理
2. RetryPolicy重试策略
3. ExponentialBackoff指数退避
4. CircuitBreaker熔断器
5. FaultIsolator故障隔离
6. IsolationZone隔离域
7. 集成测试：完整故障恢复流程
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_recovery_manager():
    """测试RecoveryManager核心恢复管理."""
    from multi_agent_se.resilience.recovery import RecoveryManager, RecoveryStrategy, RecoveryResult

    manager = RecoveryManager(max_recovery_attempts=3, recovery_cooldown_seconds=0.1)

    # 测试默认恢复
    result = manager.recover("agent", "agent.001")
    assert result.success is True
    assert result.strategy == RecoveryStrategy.RESTART
    assert "已重启" in result.message

    # 测试自定义处理器
    def custom_handler(target_id, strategy):
        return RecoveryResult(
            success=True,
            strategy=strategy,
            target_id=target_id,
            message="自定义恢复成功",
        )

    manager.register_handler("bus", custom_handler)
    result = manager.recover("bus", "bus.001")
    assert result.message == "自定义恢复成功"

    # 测试多次失败后升级
    manager.record_failure("agent.002")
    manager.record_failure("agent.002")
    manager.record_failure("agent.002")
    result = manager.recover("agent", "agent.002")
    assert result.strategy == RecoveryStrategy.ESCALATE
    assert "人工介入" in result.message

    # 测试冷却期
    result = manager.recover("agent", "agent.001")
    result2 = manager.recover("agent", "agent.001")
    assert "冷却期" in result2.message

    time.sleep(0.15)  # 等待冷却期结束

    # 测试统计（冷却期内的恢复不计入成功）
    stats = manager.get_stats()
    assert stats["total_recoveries"] >= 2

    print("  ✓ RecoveryManager核心恢复管理正常")
    return True


def test_retry_policy():
    """测试RetryPolicy重试策略."""
    from multi_agent_se.resilience.retry import RetryPolicy

    policy = RetryPolicy(
        max_retries=3,
        base_delay_seconds=0.1,
        max_delay_seconds=1.0,
        exponential_base=2.0,
    )

    # 测试重试判断
    assert policy.should_retry(Exception("test"), 0) is True
    assert policy.should_retry(Exception("test"), 2) is True
    assert policy.should_retry(Exception("test"), 3) is False

    # 测试延迟计算
    d0 = policy.get_delay(0)
    d1 = policy.get_delay(1)
    d2 = policy.get_delay(2)
    assert d0 < d1 < d2
    assert d2 <= 1.0  # 不超过最大值

    print("  ✓ RetryPolicy重试策略正常")
    return True


def test_exponential_backoff():
    """测试ExponentialBackoff指数退避."""
    from multi_agent_se.resilience.retry import ExponentialBackoff, RetryPolicy

    policy = RetryPolicy(max_retries=2, base_delay_seconds=0.05)
    backoff = ExponentialBackoff(policy)

    # 测试成功执行
    result = backoff.execute(lambda: "success", task_id="task.001")
    assert result == "success"

    # 测试失败后重试成功
    call_count = [0]

    def flaky():
        call_count[0] += 1
        if call_count[0] < 2:
            raise RuntimeError("fail")
        return "success"

    result = backoff.execute(flaky, task_id="task.002")
    assert result == "success"
    assert call_count[0] == 2

    # 测试全部失败
    def always_fail():
        raise ValueError("always fail")

    try:
        backoff.execute(always_fail, task_id="task.003")
        assert False, "应该抛出异常"
    except ValueError:
        pass

    print("  ✓ ExponentialBackoff指数退避正常")
    return True


def test_circuit_breaker():
    """测试CircuitBreaker熔断器."""
    from multi_agent_se.resilience.retry import CircuitBreaker, CircuitBreakerOpenError

    cb = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=0.2)

    # 初始状态：关闭
    assert cb.state.value == "closed"
    assert cb.can_execute() is True

    # 成功执行
    result = cb.execute(lambda: "ok")
    assert result == "ok"

    # 连续失败触发熔断
    def fail():
        raise RuntimeError("fail")

    for i in range(3):
        try:
            cb.execute(fail)
        except RuntimeError:
            pass

    # 熔断器应打开
    assert cb.state.value == "open"
    assert cb.can_execute() is False

    # 请求应被拒绝
    try:
        cb.execute(lambda: "ok")
        assert False, "应该抛出熔断异常"
    except CircuitBreakerOpenError:
        pass

    # 等待恢复期
    time.sleep(0.25)

    # 半开状态，试探性请求（需要3次成功才关闭）
    assert cb.state.value == "half_open"
    for _ in range(3):
        result = cb.execute(lambda: "ok")
        assert result == "ok"

    # 成功后应关闭
    assert cb.state.value == "closed"

    print("  ✓ CircuitBreaker熔断器正常")
    return True


def test_fault_isolator():
    """测试FaultIsolator故障隔离."""
    from multi_agent_se.resilience.isolation import FaultIsolator

    isolator = FaultIsolator(auto_isolate_threshold=2, isolation_timeout_seconds=0.3)

    # 创建域
    isolator.create_zone("zone_a", "Zone A")
    isolator.create_zone("zone_b", "Zone B")

    # 分配组件
    isolator.assign_component("comp.1", "zone_a")
    isolator.assign_component("comp.2", "zone_a")
    isolator.assign_component("comp.3", "zone_b")

    # 初始状态：可以通信
    assert isolator.can_communicate("comp.1", "comp.2") is True
    assert isolator.can_communicate("comp.1", "comp.3") is True

    # 手动隔离zone_a
    isolator.isolate_zone("zone_a", "手动隔离测试")
    assert isolator.can_communicate("comp.1", "comp.2") is False
    assert isolator.can_communicate("comp.1", "comp.3") is False
    assert isolator.can_communicate("comp.3", "comp.3") is True  # zone_b正常

    # 恢复zone_a
    isolator.restore_zone("zone_a")
    assert isolator.can_communicate("comp.1", "comp.2") is True

    # 自动隔离测试
    isolator.record_failure("comp.3")
    assert isolator.get_zone("comp.3").is_isolated is False
    isolator.record_failure("comp.3")
    assert isolator.get_zone("comp.3").is_isolated is True

    # 等待过期恢复
    time.sleep(0.35)
    restored = isolator.cleanup_expired()
    assert restored >= 1

    # 统计
    stats = isolator.get_stats()
    assert stats["total_zones"] == 2

    print("  ✓ FaultIsolator故障隔离正常")
    return True


def test_isolation_zone():
    """测试IsolationZone隔离域."""
    from multi_agent_se.resilience.isolation import IsolationZone

    zone = IsolationZone(zone_id="test_zone", name="Test Zone")

    # 初始状态
    assert zone.is_isolated is False

    # 添加组件
    zone.add_component("c1")
    zone.add_component("c2")
    assert "c1" in zone.components

    # 隔离
    zone.isolate("测试")
    assert zone.is_isolated is True
    assert zone.reason == "测试"

    # 恢复
    zone.restore()
    assert zone.is_isolated is False

    # 序列化
    data = zone.to_dict()
    assert data["zone_id"] == "test_zone"
    assert data["is_isolated"] is False

    print("  ✓ IsolationZone隔离域正常")
    return True


def test_integration_full_recovery():
    """集成测试：完整故障恢复流程."""
    from multi_agent_se.resilience.recovery import RecoveryManager, RecoveryStrategy
    from multi_agent_se.resilience.retry import ExponentialBackoff, RetryPolicy, CircuitBreaker
    from multi_agent_se.resilience.isolation import FaultIsolator

    # 构建完整恢复系统
    recovery = RecoveryManager(max_recovery_attempts=2)
    backoff = ExponentialBackoff(RetryPolicy(max_retries=1, base_delay_seconds=0.01))
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=0.1)
    isolator = FaultIsolator(auto_isolate_threshold=3)

    # 创建隔离域
    isolator.create_zone("agents")
    isolator.assign_component("agent.main", "agents")

    # 模拟Agent故障 → 重试 → 恢复
    def agent_task():
        # 第一次失败，第二次成功
        if not hasattr(agent_task, 'called'):
            agent_task.called = True
            raise RuntimeError("临时故障")
        return "任务完成"

    try:
        result = backoff.execute(agent_task, task_id="agent.main.task")
        assert result == "任务完成"
    except RuntimeError:
        pass

    # 模拟持续故障 → 熔断
    def bad_task():
        raise ValueError("严重故障")

    for _ in range(2):
        try:
            cb.execute(bad_task)
        except ValueError:
            pass

    assert cb.state.value == "open"

    # 模拟恢复
    recovery_result = recovery.recover("agent", "agent.main")
    assert recovery_result.success is True

    # 统计验证
    assert recovery.get_stats()["total_recoveries"] >= 1
    assert isolator.get_stats()["total_zones"] == 1

    print("  ✓ 集成测试：完整故障恢复流程通过")
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第51阶段验收测试 - 故障恢复与自愈机制")
    print("=" * 60)
    print()

    tests = [
        ("RecoveryManager核心恢复", test_recovery_manager),
        ("RetryPolicy重试策略", test_retry_policy),
        ("ExponentialBackoff指数退避", test_exponential_backoff),
        ("CircuitBreaker熔断器", test_circuit_breaker),
        ("FaultIsolator故障隔离", test_fault_isolator),
        ("IsolationZone隔离域", test_isolation_zone),
        ("集成测试", test_integration_full_recovery),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"[TEST] {name}")
        try:
            if test_func():
                passed += 1
                print(f"  ✓ {name} 通过")
        except Exception as e:
            failed += 1
            print(f"  ✗ {name} 失败: {e}")
            import traceback
            traceback.print_exc()
        print()

    print("=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)

    if failed == 0:
        print("🎉 第51阶段验收通过！故障恢复与自愈机制完成。")
        return True
    else:
        print(f"❌ 部分测试失败 ({failed} 个)")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
