#!/usr/bin/env python3
"""第17阶段验收脚本 - Agent生命周期管理.

验证内容：
1. 生命周期状态机 (lifecycle.py)
2. Agent工厂类 (factory.py)
3. Agent实例池 (pool.py)
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
    print_header("第17阶段验收：Agent生命周期管理")
    
    passed = 0
    failed = 0
    
    # ========== 1. 测试生命周期状态机 ==========
    print_header("1. 生命周期状态机 (lifecycle.py)")
    
    try:
        from multi_agent_se.agents.lifecycle import (
            LifecycleState,
            LifecycleEvent,
            LifecycleTransition,
            LifecycleTransitionRecord,
            LifecycleStateMachine,
            LifecycleHook,
            LoggingHook,
            MetricsHook,
        )
        print_result("导入生命周期模块", True)
        passed += 1
    except Exception as e:
        print_result("导入生命周期模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 LifecycleState 枚举
    try:
        assert LifecycleState.CREATED.value == "created"
        assert LifecycleState.INITIALIZING.value == "initializing"
        assert LifecycleState.READY.value == "ready"
        assert LifecycleState.RUNNING.value == "running"
        assert LifecycleState.PAUSED.value == "paused"
        assert LifecycleState.STOPPED.value == "stopped"
        assert LifecycleState.ERROR.value == "error"
        assert LifecycleState.TERMINATED.value == "terminated"
        print_result("LifecycleState 枚举定义", True, f"共{len(LifecycleState)}种状态")
        passed += 1
    except Exception as e:
        print_result("LifecycleState 枚举定义", False, str(e))
        failed += 1
    
    # 测试 LifecycleEvent 枚举
    try:
        assert LifecycleEvent.CREATE.value == "create"
        assert LifecycleEvent.INITIALIZE.value == "initialize"
        assert LifecycleEvent.START.value == "start"
        assert LifecycleEvent.PAUSE.value == "pause"
        assert LifecycleEvent.RESUME.value == "resume"
        assert LifecycleEvent.STOP.value == "stop"
        assert LifecycleEvent.TERMINATE.value == "terminate"
        print_result("LifecycleEvent 枚举定义", True, f"共{len(LifecycleEvent)}种事件")
        passed += 1
    except Exception as e:
        print_result("LifecycleEvent 枚举定义", False, str(e))
        failed += 1
    
    # 测试 LifecycleStateMachine
    try:
        sm = LifecycleStateMachine()
        assert sm.state == LifecycleState.CREATED
        assert sm.is_created == True
        assert sm.is_active == False
        print_result("LifecycleStateMachine 初始状态", True)
        passed += 1
    except Exception as e:
        print_result("LifecycleStateMachine 初始状态", False, str(e))
        failed += 1
    
    # 测试状态转换
    try:
        # CREATED -> INITIALIZING
        sm.initialize()
        assert sm.state == LifecycleState.INITIALIZING
        
        # INITIALIZING -> READY
        sm.initialize_success()
        assert sm.state == LifecycleState.READY
        assert sm.is_ready == True
        
        # READY -> RUNNING
        sm.start()
        assert sm.state == LifecycleState.RUNNING
        assert sm.is_running == True
        assert sm.is_active == True
        
        print_result("状态转换流程", True, "CREATED->INITIALIZING->READY->RUNNING")
        passed += 1
    except Exception as e:
        print_result("状态转换流程", False, str(e))
        failed += 1
    
    # 测试暂停/恢复
    try:
        sm2 = LifecycleStateMachine()
        sm2.initialize()
        sm2.initialize_success()
        sm2.start()
        
        # RUNNING -> PAUSED
        sm2.pause()
        assert sm2.state == LifecycleState.PAUSED
        assert sm2.is_paused == True
        
        # PAUSED -> RUNNING
        sm2.resume()
        assert sm2.state == LifecycleState.RUNNING
        
        print_result("暂停/恢复流程", True)
        passed += 1
    except Exception as e:
        print_result("暂停/恢复流程", False, str(e))
        failed += 1
    
    # 测试停止/终止
    try:
        sm3 = LifecycleStateMachine()
        sm3.initialize()
        sm3.initialize_success()
        sm3.start()
        
        # RUNNING -> STOPPING
        sm3.stop()
        assert sm3.state == LifecycleState.STOPPING
        
        # STOPPING -> STOPPED
        sm3.stop_success()
        assert sm3.state == LifecycleState.STOPPED
        
        # STOPPED -> TERMINATED
        sm3.terminate()
        assert sm3.state == LifecycleState.TERMINATED
        assert sm3.is_terminated == True
        assert sm3.is_recoverable == False
        
        print_result("停止/终止流程", True)
        passed += 1
    except Exception as e:
        print_result("停止/终止流程", False, str(e))
        failed += 1
    
    # 测试非法转换
    try:
        sm4 = LifecycleStateMachine()
        # 尝试从CREATED直接跳到RUNNING（非法）
        try:
            sm4.transition(LifecycleEvent.START)
            print_result("非法转换检测", False, "应该抛出异常")
            failed += 1
        except ValueError as e:
            assert "Invalid transition" in str(e)
            print_result("非法转换检测", True, "正确拒绝非法转换")
            passed += 1
    except Exception as e:
        print_result("非法转换检测", False, str(e))
        failed += 1
    
    # 测试转换历史
    try:
        sm5 = LifecycleStateMachine()
        sm5.initialize()
        sm5.initialize_success()
        
        history = sm5.history
        assert len(history) == 2
        assert history[0].from_state == LifecycleState.CREATED
        assert history[0].to_state == LifecycleState.INITIALIZING
        assert history[1].from_state == LifecycleState.INITIALIZING
        assert history[1].to_state == LifecycleState.READY
        
        print_result("转换历史记录", True, f"记录了{len(history)}次转换")
        passed += 1
    except Exception as e:
        print_result("转换历史记录", False, str(e))
        failed += 1
    
    # 测试事件钩子
    try:
        hook_calls = []
        
        def test_hook(state, event, is_pre):
            hook_calls.append((state.value, event.value, is_pre))
        
        sm6 = LifecycleStateMachine()
        sm6.add_hook(LifecycleEvent.INITIALIZE, test_hook)
        
        sm6.initialize()
        
        # 应该有PRE和POST两次调用
        assert len(hook_calls) == 2
        assert hook_calls[0][2] == True   # PRE
        assert hook_calls[1][2] == False  # POST
        
        print_result("事件钩子机制", True, f"钩子调用{len(hook_calls)}次")
        passed += 1
    except Exception as e:
        print_result("事件钩子机制", False, str(e))
        failed += 1
    
    # 测试 MetricsHook
    try:
        metrics_hook = MetricsHook()
        sm7 = LifecycleStateMachine()
        sm7.add_hook(LifecycleEvent.INITIALIZE, metrics_hook.on_event)
        sm7.add_hook(LifecycleEvent.INITIALIZE_SUCCESS, metrics_hook.on_event)
        
        sm7.initialize()
        sm7.initialize_success()
        
        counts = metrics_hook.get_counts()
        assert counts["initialize"] == 1
        assert counts["initialize_success"] == 1
        
        print_result("MetricsHook 指标收集", True)
        passed += 1
    except Exception as e:
        print_result("MetricsHook 指标收集", False, str(e))
        failed += 1
    
    # ========== 2. 测试Agent工厂类 ==========
    print_header("2. Agent工厂类 (factory.py)")
    
    try:
        from multi_agent_se.agents.lifecycle import (
            AgentCreationError,
            AgentCreationConfig,
            AgentInstance,
            AgentFactory,
            SimpleAgent,
            create_agent,
        )
        from multi_agent_se.agents.registry import AgentRole, reset_registry
        print_result("导入工厂模块", True)
        passed += 1
    except Exception as e:
        print_result("导入工厂模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 AgentCreationConfig
    try:
        config = AgentCreationConfig(
            agent_id="test.agent",
            role=AgentRole.DEVELOPER,
            name="TestAgent",
            auto_initialize=True,
        )
        assert config.agent_id == "test.agent"
        assert config.role == AgentRole.DEVELOPER
        assert config.auto_initialize == True
        print_result("AgentCreationConfig 数据类", True)
        passed += 1
    except Exception as e:
        print_result("AgentCreationConfig 数据类", False, str(e))
        failed += 1
    
    # 测试 AgentFactory 创建实例
    try:
        reset_registry()
        factory = AgentFactory()
        
        config = AgentCreationConfig(
            agent_id="factory.test",
            role=AgentRole.CONTROLLER,
            name="FactoryTestAgent",
            auto_initialize=True,
        )
        
        instance = factory.create(config)
        
        assert instance is not None
        assert instance.metadata.role == AgentRole.CONTROLLER
        assert instance.lifecycle.state == LifecycleState.READY  # 自动初始化
        
        print_result("AgentFactory 创建实例", True, f"ID={instance.instance_id}")
        passed += 1
    except Exception as e:
        print_result("AgentFactory 创建实例", False, str(e))
        failed += 1
    
    # 测试 AgentFactory 启动/停止
    try:
        reset_registry()
        factory = AgentFactory()
        
        config = AgentCreationConfig(
            agent_id="lifecycle.test",
            role=AgentRole.DEVELOPER,
            auto_initialize=True,
            auto_start=False,
        )
        
        instance = factory.create(config)
        instance_id = instance.instance_id
        
        # 启动
        result = factory.start(instance_id)
        assert result == True
        assert factory.get(instance_id).lifecycle.state == LifecycleState.RUNNING
        
        # 暂停
        result = factory.pause(instance_id)
        assert result == True
        assert factory.get(instance_id).lifecycle.state == LifecycleState.PAUSED
        
        # 恢复
        result = factory.resume(instance_id)
        assert result == True
        assert factory.get(instance_id).lifecycle.state == LifecycleState.RUNNING
        
        # 停止
        result = factory.stop(instance_id)
        assert result == True
        assert factory.get(instance_id).lifecycle.state == LifecycleState.STOPPED
        
        print_result("AgentFactory 生命周期操作", True)
        passed += 1
    except Exception as e:
        print_result("AgentFactory 生命周期操作", False, str(e))
        failed += 1
    
    # 测试 AgentFactory 终止
    try:
        reset_registry()
        factory = AgentFactory()
        
        config = AgentCreationConfig(
            agent_id="terminate.test",
            role=AgentRole.TESTER,
            auto_initialize=True,
        )
        
        instance = factory.create(config)
        instance_id = instance.instance_id
        
        assert factory.total_instances == 1
        
        # 终止
        result = factory.terminate(instance_id)
        assert result == True
        assert factory.total_instances == 0  # 终止后移除
        assert factory.get(instance_id) is None
        
        print_result("AgentFactory 终止实例", True)
        passed += 1
    except Exception as e:
        print_result("AgentFactory 终止实例", False, str(e))
        failed += 1
    
    # 测试 SimpleAgent
    try:
        from multi_agent_se.agents.registry import AgentStatus
        
        agent = SimpleAgent(
            agent_id="simple.test",
            name="SimpleTest",
            role=AgentRole.REVIEWER,
        )
        
        assert agent.status == AgentStatus.CREATED
        
        agent.initialize()
        assert agent.status == AgentStatus.READY
        
        agent.start()
        assert agent.status == AgentStatus.RUNNING
        
        agent.pause()
        assert agent.status == AgentStatus.PAUSED
        
        print_result("SimpleAgent 基础实现", True)
        passed += 1
    except Exception as e:
        print_result("SimpleAgent 基础实现", False, str(e))
        failed += 1
    
    # 测试 create_agent 便捷函数
    try:
        reset_registry()
        instance = create_agent(
            role=AgentRole.ARCHITECT,
            name="ConvenienceAgent",
            auto_initialize=True,
        )
        
        assert instance is not None
        assert instance.metadata.role == AgentRole.ARCHITECT
        assert instance.lifecycle.state == LifecycleState.READY
        
        print_result("create_agent 便捷函数", True)
        passed += 1
    except Exception as e:
        print_result("create_agent 便捷函数", False, str(e))
        failed += 1
    
    # ========== 3. 测试Agent实例池 ==========
    print_header("3. Agent实例池 (pool.py)")
    
    try:
        from multi_agent_se.agents.lifecycle import (
            PoolError,
            PoolFullError,
            InstanceNotFoundError,
            PoolConfig,
            PoolStats,
            AgentPool,
            get_pool,
            reset_pool,
        )
        print_result("导入实例池模块", True)
        passed += 1
    except Exception as e:
        print_result("导入实例池模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 PoolConfig
    try:
        config = PoolConfig(
            max_instances=50,
            max_per_role=10,
            idle_timeout_seconds=120,
        )
        assert config.max_instances == 50
        assert config.max_per_role == 10
        assert config.enable_instance_reuse == True
        print_result("PoolConfig 配置", True)
        passed += 1
    except Exception as e:
        print_result("PoolConfig 配置", False, str(e))
        failed += 1
    
    # 测试 AgentPool 创建实例池
    try:
        reset_registry()
        pool = AgentPool()
        
        assert pool.total_instances == 0
        assert pool.is_full == False
        
        print_result("AgentPool 初始化", True)
        passed += 1
    except Exception as e:
        print_result("AgentPool 初始化", False, str(e))
        failed += 1
    
    # 测试 acquire/release
    try:
        reset_registry()
        pool = AgentPool()
        
        # 获取实例
        instance = pool.acquire(role=AgentRole.DEVELOPER)
        assert instance is not None
        assert instance.lifecycle.state == LifecycleState.RUNNING
        assert pool.total_instances == 1
        assert pool.active_count == 1
        
        # 释放实例
        result = pool.release(instance.instance_id)
        assert result == True
        assert pool.idle_count == 1  # 进入空闲列表
        
        print_result("AgentPool acquire/release", True, f"总数={pool.total_instances}, 空闲={pool.idle_count}")
        passed += 1
    except Exception as e:
        print_result("AgentPool acquire/release", False, str(e))
        failed += 1
    
    # 测试实例复用
    try:
        reset_registry()
        pool = AgentPool()
        
        # 获取并释放
        instance1 = pool.acquire(role=AgentRole.CONTROLLER)
        pool.release(instance1.instance_id)
        
        # 再次获取相同角色（应该复用）
        instance2 = pool.acquire(role=AgentRole.CONTROLLER)
        
        # 应该是同一个实例
        assert instance1.instance_id == instance2.instance_id
        assert pool.total_instances == 1  # 没有新建
        
        print_result("AgentPool 实例复用", True)
        passed += 1
    except Exception as e:
        print_result("AgentPool 实例复用", False, str(e))
        failed += 1
    
    # 测试池限制
    try:
        reset_registry()
        config = PoolConfig(max_instances=2, max_per_role=10)
        pool = AgentPool(config=config)
        
        # 创建2个实例
        pool.acquire(role=AgentRole.DEVELOPER)
        pool.acquire(role=AgentRole.TESTER)
        
        assert pool.is_full == True
        
        # 尝试创建第3个（应该失败）
        try:
            pool.acquire(role=AgentRole.REVIEWER)
            print_result("AgentPool 池限制", False, "应该抛出PoolFullError")
            failed += 1
        except PoolFullError:
            print_result("AgentPool 池限制", True, "正确拒绝超出限制")
            passed += 1
    except Exception as e:
        print_result("AgentPool 池限制", False, str(e))
        failed += 1
    
    # 测试按角色获取
    try:
        reset_registry()
        pool = AgentPool()
        
        pool.acquire(role=AgentRole.DEVELOPER)
        pool.acquire(role=AgentRole.DEVELOPER)
        pool.acquire(role=AgentRole.TESTER)
        
        developers = pool.get_by_role(AgentRole.DEVELOPER)
        assert len(developers) == 2
        
        testers = pool.get_by_role(AgentRole.TESTER)
        assert len(testers) == 1
        
        print_result("AgentPool 按角色获取", True, f"DEVELOPER={len(developers)}, TESTER={len(testers)}")
        passed += 1
    except Exception as e:
        print_result("AgentPool 按角色获取", False, str(e))
        failed += 1
    
    # 测试池统计
    try:
        reset_registry()
        pool = AgentPool()
        
        inst1 = pool.acquire(role=AgentRole.CONTROLLER)
        inst2 = pool.acquire(role=AgentRole.DEVELOPER)
        pool.release(inst1.instance_id)  # 一个空闲
        
        stats = pool.get_stats()
        assert stats.total_instances == 2
        assert stats.idle_instances == 1
        # release后inst1变成READY状态，is_active仍然为True
        assert stats.active_instances == 2  # READY和RUNNING都是活跃状态
        
        print_result("AgentPool 统计", True, f"总数={stats.total_instances}, 活跃={stats.active_instances}, 空闲={stats.idle_instances}")
        passed += 1
    except Exception as e:
        print_result("AgentPool 统计", False, str(e))
        failed += 1
    
    # 测试移除实例
    try:
        reset_registry()
        pool = AgentPool()
        
        instance = pool.acquire(role=AgentRole.REVIEWER)
        instance_id = instance.instance_id
        
        assert pool.total_instances == 1
        
        result = pool.remove(instance_id)
        assert result == True
        assert pool.total_instances == 0
        assert pool.get(instance_id) is None
        
        print_result("AgentPool 移除实例", True)
        passed += 1
    except Exception as e:
        print_result("AgentPool 移除实例", False, str(e))
        failed += 1
    
    # 测试清空池
    try:
        reset_registry()
        pool = AgentPool()
        
        pool.acquire(role=AgentRole.CONTROLLER)
        pool.acquire(role=AgentRole.DEVELOPER)
        pool.acquire(role=AgentRole.TESTER)
        
        assert pool.total_instances == 3
        
        count = pool.clear()
        assert count == 3
        assert pool.total_instances == 0
        
        print_result("AgentPool 清空", True, f"清除了{count}个实例")
        passed += 1
    except Exception as e:
        print_result("AgentPool 清空", False, str(e))
        failed += 1
    
    # 测试全局实例池
    try:
        reset_pool()
        pool1 = get_pool()
        pool2 = get_pool()
        
        assert pool1 is pool2  # 同一个实例
        
        print_result("全局实例池", True)
        passed += 1
    except Exception as e:
        print_result("全局实例池", False, str(e))
        failed += 1
    
    # ========== 4. 测试统一导出接口 ==========
    print_header("4. 统一导出接口 (__init__.py)")
    
    try:
        from multi_agent_se.agents.lifecycle import __all__
        
        expected_exports = [
            # 生命周期
            "LifecycleState", "LifecycleEvent", "LifecycleTransition",
            "LifecycleTransitionRecord", "LifecycleStateMachine",
            "LifecycleHook", "LoggingHook", "MetricsHook",
            # 工厂
            "AgentCreationError", "AgentCreationConfig", "AgentInstance",
            "AgentFactory", "SimpleAgent", "create_agent",
            # 实例池
            "PoolError", "PoolFullError", "InstanceNotFoundError",
            "PoolConfig", "PoolStats", "AgentPool",
            "get_pool", "reset_pool",
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
        print("\n  🎉 第17阶段验收通过！")
        return 0
    else:
        print(f"\n  ⚠️ 第17阶段有 {failed} 项测试未通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
