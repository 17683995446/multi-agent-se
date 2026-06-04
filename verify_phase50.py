"""第50阶段验收测试 - 健康检查与监控体系

测试内容：
1. HealthChecker核心框架
2. AgentHeartbeatMonitor心跳检测
3. MessageBusMonitor消息总线监控
4. PoolLoadMonitor实例池负载监控
5. ConfigMonitor配置监控
6. LivenessProbe存活探针
7. ReadinessProbe就绪探针
8. StartupProbe启动探针
9. 集成测试：完整健康检查流程
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_health_checker_framework():
    """测试HealthChecker核心框架."""
    from multi_agent_se.health.checker import HealthChecker, HealthStatus, ComponentHealth

    checker = HealthChecker()

    # 注册自定义检查器
    def mock_healthy():
        return ComponentHealth(name="mock_ok", status=HealthStatus.HEALTHY, message="正常")

    def mock_degraded():
        return ComponentHealth(name="mock_warn", status=HealthStatus.DEGRADED, message="降级")

    def mock_unhealthy():
        return ComponentHealth(name="mock_fail", status=HealthStatus.UNHEALTHY, message="故障")

    checker.register("mock_ok", mock_healthy)
    checker.register("mock_warn", mock_degraded)
    checker.register("mock_fail", mock_unhealthy)

    # 测试整体检查
    report = checker.check()
    assert report.overall_status == HealthStatus.UNHEALTHY, "应有UNHEALTHY组件"
    assert report.unhealthy_count == 1
    assert report.degraded_count == 1
    assert report.healthy_count == 1
    assert len(report.components) == 3

    # 测试单组件检查
    single = checker.check("mock_ok")
    assert single.overall_status == HealthStatus.HEALTHY
    assert len(single.components) == 1

    # 测试注销
    checker.unregister("mock_fail")
    report2 = checker.check()
    assert report2.overall_status == HealthStatus.DEGRADED, "移除UNHEALTHY后应为DEGRADED"

    # 测试快速检查
    assert not checker.is_healthy()
    assert checker.is_ready()

    print("  ✓ HealthChecker框架功能完整")
    return True


def test_agent_heartbeat_monitor():
    """测试Agent心跳监控."""
    from multi_agent_se.health.monitors import AgentHeartbeatMonitor
    from multi_agent_se.health.checker import HealthStatus

    monitor = AgentHeartbeatMonitor(timeout_seconds=0.5)

    # 无Agent时
    result = monitor.check()
    assert result.status == HealthStatus.UNKNOWN

    # 注册Agent但未心跳
    monitor.register_agent("agent.001")
    monitor.register_agent("agent.002")
    result = monitor.check()
    assert result.status == HealthStatus.UNHEALTHY
    assert result.metrics["unhealthy"] == 2
    assert "agent.001" in result.details["missing_agents"]

    # 发送心跳
    monitor.heartbeat("agent.001", status="ok")
    monitor.heartbeat("agent.002", status="ok")
    result = monitor.check()
    assert result.status == HealthStatus.HEALTHY
    assert result.metrics["healthy"] == 2

    # 等待超时
    time.sleep(0.6)
    result = monitor.check()
    assert result.status == HealthStatus.UNHEALTHY
    assert result.metrics["unhealthy"] == 2
    assert "agent.001" in result.details["stale_agents"]

    # 注销Agent
    monitor.unregister_agent("agent.001")
    result = monitor.check()
    assert result.metrics["total_agents"] == 1

    print("  ✓ AgentHeartbeatMonitor心跳检测正常")
    return True


def test_message_bus_monitor():
    """测试消息总线监控."""
    from multi_agent_se.health.monitors import MessageBusMonitor
    from multi_agent_se.agents.communication.bus import MessageBus
    from multi_agent_se.agents.communication.message import Message, MessageType
    from multi_agent_se.health.checker import HealthStatus

    bus = MessageBus()
    monitor = MessageBusMonitor(max_queue_size=100, max_error_rate=0.1)
    monitor.attach(bus)

    # 空总线
    result = monitor.check()
    assert result.status == HealthStatus.HEALTHY

    # 发送消息
    for i in range(50):
        msg = Message.create(
            sender_id="test",
            receiver_id="recv",
            payload={"index": i},
            message_type=MessageType.TASK_ASSIGN,
        )
        bus.send(msg)

    result = monitor.check()
    assert result.status == HealthStatus.HEALTHY
    assert result.metrics["queue_size"] == 50
    assert result.metrics["total_sent"] == 50

    # 模拟高错误率（手动修改stats）
    bus._stats.total_failed = 20
    bus._stats.total_sent = 100
    result = monitor.check()
    assert result.status == HealthStatus.UNHEALTHY
    assert result.metrics["error_rate"] == 0.2

    # 恢复
    bus._stats.total_failed = 0
    bus._stats.total_sent = 50

    print("  ✓ MessageBusMonitor消息总线监控正常")
    return True


def test_pool_load_monitor():
    """测试实例池负载监控."""
    from multi_agent_se.health.monitors import PoolLoadMonitor
    from multi_agent_se.agents.lifecycle.pool import AgentPool, PoolConfig
    from multi_agent_se.agents.registry import AgentRole
    from multi_agent_se.health.checker import HealthStatus

    pool = AgentPool(config=PoolConfig(max_instances=10))
    monitor = PoolLoadMonitor(max_load_ratio=0.8, max_idle_ratio=0.5)
    monitor.attach(pool)

    # 空池
    result = monitor.check()
    assert result.status == HealthStatus.HEALTHY
    assert result.metrics["total_instances"] == 0

    # 创建实例
    instances = []
    for i in range(5):
        inst = pool.acquire(AgentRole.CONTROLLER)
        instances.append(inst)

    result = monitor.check()
    assert result.status == HealthStatus.HEALTHY
    assert result.metrics["active_instances"] == 5

    # 释放部分
    for inst in instances[:3]:
        pool.release(inst.instance_id)

    result = monitor.check()
    assert result.metrics["idle_instances"] == 3

    # 清理
    pool.clear()

    print("  ✓ PoolLoadMonitor实例池负载监控正常")
    return True


def test_config_monitor():
    """测试配置监控."""
    from multi_agent_se.health.monitors import ConfigMonitor
    from multi_agent_se.health.checker import HealthStatus

    monitor = ConfigMonitor()

    # 首次检查
    result = monitor.check()
    assert result.status == HealthStatus.HEALTHY
    assert result.metrics["check_count"] == 1

    # 再次检查（无变更）
    result = monitor.check()
    assert result.status == HealthStatus.HEALTHY
    assert result.metrics["config_changed"] is False
    assert result.metrics["check_count"] == 2

    print("  ✓ ConfigMonitor配置监控正常")
    return True


def test_liveness_probe():
    """测试存活探针."""
    from multi_agent_se.health.probes import LivenessProbe
    from multi_agent_se.health.checker import HealthChecker, HealthStatus, ComponentHealth

    checker = HealthChecker()
    probe = LivenessProbe(health_checker=checker, max_failures=2)

    # 注册健康组件
    checker.register("ok", lambda: ComponentHealth(name="ok", status=HealthStatus.HEALTHY))

    # 正常检查
    result = probe.check()
    assert result.success is True
    assert not probe.should_restart

    # 注册故障组件
    checker.register("fail", lambda: ComponentHealth(name="fail", status=HealthStatus.UNHEALTHY))

    # 第一次失败
    result = probe.check()
    assert result.success is True  # 警告但不算失败
    assert not probe.should_restart

    # 第二次失败
    result = probe.check()
    assert result.success is False
    assert probe.should_restart

    print("  ✓ LivenessProbe存活探针正常")
    return True


def test_readiness_probe():
    """测试就绪探针."""
    from multi_agent_se.health.probes import ReadinessProbe
    from multi_agent_se.health.checker import HealthChecker, HealthStatus, ComponentHealth

    checker = HealthChecker()
    probe = ReadinessProbe(health_checker=checker, required_components=["db", "cache"])

    # 无组件注册时，系统状态为UNKNOWN，未就绪
    result = probe.check()
    assert result.success is False
    assert "未就绪" in result.message

    # 注册健康组件
    checker.register("db", lambda: ComponentHealth(name="db", status=HealthStatus.HEALTHY))
    checker.register("cache", lambda: ComponentHealth(name="cache", status=HealthStatus.HEALTHY))

    result = probe.check()
    assert result.success is True  # 全部健康，就绪

    # 注册降级状态 - required_components要求必须HEALTHY
    checker.register("db", lambda: ComponentHealth(name="db", status=HealthStatus.DEGRADED))
    result = probe.check()
    assert result.success is False  # DEGRADED不满足required的HEALTHY要求
    assert "必需组件不健康" in result.message

    # 恢复健康后，再测试UNHEALTHY
    checker.register("db", lambda: ComponentHealth(name="db", status=HealthStatus.HEALTHY))
    result = probe.check()
    assert result.success is True

    # 注册不健康 - 整体状态变为UNHEALTHY，is_ready返回False
    checker.register("db", lambda: ComponentHealth(name="db", status=HealthStatus.UNHEALTHY))
    result = probe.check()
    assert result.success is False  # UNHEALTHY不算就绪
    assert "未就绪" in result.message

    print("  ✓ ReadinessProbe就绪探针正常")
    return True


def test_startup_probe():
    """测试启动探针."""
    from multi_agent_se.health.probes import StartupProbe
    from multi_agent_se.health.checker import HealthChecker, HealthStatus, ComponentHealth

    checker = HealthChecker()
    probe = StartupProbe(health_checker=checker, startup_timeout_seconds=1.0)

    # 未注册组件时
    result = probe.check()
    assert result.success is False  # 没有组件 = 不健康

    # 注册健康组件
    checker.register("svc", lambda: ComponentHealth(name="svc", status=HealthStatus.HEALTHY))
    result = probe.check()
    assert result.success is True
    assert probe.is_started

    # 已启动后再次检查
    result = probe.check()
    assert result.message == "系统已启动完成"

    print("  ✓ StartupProbe启动探针正常")
    return True


def test_integration_full_pipeline():
    """集成测试：完整健康检查流程."""
    from multi_agent_se.health.checker import HealthChecker, HealthStatus
    from multi_agent_se.health.monitors import (
        AgentHeartbeatMonitor,
        MessageBusMonitor,
        PoolLoadMonitor,
        ConfigMonitor,
    )
    from multi_agent_se.health.probes import LivenessProbe, ReadinessProbe
    from multi_agent_se.agents.communication.bus import MessageBus
    from multi_agent_se.agents.lifecycle.pool import AgentPool, PoolConfig

    # 构建完整系统
    bus = MessageBus()
    pool = AgentPool(config=PoolConfig(max_instances=5))

    # 创建HealthChecker并注册所有监控器
    checker = HealthChecker()

    heartbeat = AgentHeartbeatMonitor(timeout_seconds=10.0)
    heartbeat.register_agent("controller.001")
    heartbeat.heartbeat("controller.001")
    checker.register("agent_heartbeat", heartbeat.check)

    bus_monitor = MessageBusMonitor()
    bus_monitor.attach(bus)
    checker.register("message_bus", bus_monitor.check)

    pool_monitor = PoolLoadMonitor()
    pool_monitor.attach(pool)
    checker.register("agent_pool", pool_monitor.check)

    config_monitor = ConfigMonitor()
    checker.register("configuration", config_monitor.check)

    # 执行完整检查
    report = checker.check()
    assert report.overall_status == HealthStatus.HEALTHY
    assert report.healthy_count == 4
    assert len(report.components) == 4

    # 验证报告结构
    report_dict = report.to_dict()
    assert "overall_status" in report_dict
    assert "components" in report_dict
    assert "summary" in report_dict
    assert report_dict["summary"]["total"] == 4

    # 探针测试
    liveness = LivenessProbe(health_checker=checker)
    readiness = ReadinessProbe(health_checker=checker)

    live_result = liveness.check()
    ready_result = readiness.check()

    assert live_result.success is True
    assert ready_result.success is True

    print("  ✓ 集成测试：完整健康检查流程通过")
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第50阶段验收测试 - 健康检查与监控体系")
    print("=" * 60)
    print()

    tests = [
        ("HealthChecker核心框架", test_health_checker_framework),
        ("AgentHeartbeatMonitor", test_agent_heartbeat_monitor),
        ("MessageBusMonitor", test_message_bus_monitor),
        ("PoolLoadMonitor", test_pool_load_monitor),
        ("ConfigMonitor", test_config_monitor),
        ("LivenessProbe", test_liveness_probe),
        ("ReadinessProbe", test_readiness_probe),
        ("StartupProbe", test_startup_probe),
        ("集成测试", test_integration_full_pipeline),
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
        print("🎉 第50阶段验收通过！健康检查与监控体系完成。")
        return True
    else:
        print(f"❌ 部分测试失败 ({failed} 个)")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
