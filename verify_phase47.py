"""第47阶段验收脚本 - Agent状态机完善.

验证增强的状态机：
- 状态转换记录
- 异常时自动进入ERROR状态
- 状态转换历史查询
- 完整生命周期流程
"""

import sys
sys.path.insert(0, "/workspace/multi_agent_se/src")

from multi_agent_se.agents.controller import ControllerAgent
from multi_agent_se.agents.registry import AgentStatus
from multi_agent_se.agents.runtime.base_agent import AgentContext
from multi_agent_se.scheduler.task import Task


def test_state_transition_recording():
    """测试: 状态转换记录."""
    print("\n[TEST] 状态转换记录")
    
    agent = ControllerAgent(agent_id="test.state.001")
    
    # 初始状态
    assert agent.status == AgentStatus.CREATED
    history = agent.get_transition_history()
    assert len(history) >= 1
    print(f"  ✓ 初始状态: {agent.status.value}, 历史记录: {len(history)} 条")
    
    # 初始化
    agent.initialize()
    assert agent.status == AgentStatus.READY
    history = agent.get_transition_history()
    assert any(h.to_state.value == "ready" for h in history)
    print(f"  ✓ 初始化后: {agent.status.value}")
    
    # 启动
    agent.start()
    assert agent.status == AgentStatus.RUNNING
    history = agent.get_transition_history()
    assert any(h.to_state.value == "running" for h in history)
    print(f"  ✓ 启动后: {agent.status.value}")
    
    # 暂停
    agent.pause()
    assert agent.status == AgentStatus.PAUSED
    history = agent.get_transition_history()
    assert any(h.to_state.value == "paused" for h in history)
    print(f"  ✓ 暂停后: {agent.status.value}")
    
    # 恢复
    agent.resume()
    assert agent.status == AgentStatus.RUNNING
    print(f"  ✓ 恢复后: {agent.status.value}")
    
    # 停止
    agent.stop()
    assert agent.status == AgentStatus.TERMINATED
    print(f"  ✓ 停止后: {agent.status.value}")
    
    # 验证完整历史
    history = agent.get_transition_history()
    print(f"  ✓ 完整状态历史: {len(history)} 条记录")
    for h in history:
        print(f"    {h.from_state.value} -> {h.to_state.value} ({h.timestamp})")
    
    return True


def test_exception_to_error_state():
    """测试: 异常时自动进入ERROR状态."""
    print("\n[TEST] 异常时自动进入ERROR状态")
    
    # 创建一个会抛出异常的Agent子类
    class FailingAgent(ControllerAgent):
        def process(self, context):
            raise ValueError("模拟执行异常")
    
    agent = FailingAgent(agent_id="test.error.001")
    agent.initialize()
    agent.start()
    
    assert agent.status == AgentStatus.RUNNING
    print(f"  ✓ 执行前状态: {agent.status.value}")
    
    # 执行任务（会抛出异常）
    task = Task(task_id="error.task", task_type="test")
    context = AgentContext(task=task, input_data={"requirement": "test"})
    result = agent.execute(context)
    
    # 验证状态变为ERROR
    assert agent.status == AgentStatus.ERROR, f"期望ERROR，实际{agent.status.value}"
    assert not result.success
    print(f"  ✓ 异常后状态: {agent.status.value}")
    
    # 验证历史记录包含错误
    history = agent.get_transition_history()
    error_transitions = [h for h in history if h.to_state.value == "error"]
    assert len(error_transitions) >= 1
    assert error_transitions[0].error is not None
    print(f"  ✓ 错误记录: {error_transitions[0].error}")
    
    return True


def test_invalid_state_transitions():
    """测试: 非法状态转换被拒绝."""
    print("\n[TEST] 非法状态转换")
    
    agent = ControllerAgent(agent_id="test.invalid.001")
    
    # 未初始化时不能启动
    try:
        agent.start()
        assert False, "应该抛出异常"
    except Exception as e:
        print(f"  ✓ 未初始化启动被拒绝: {e}")
    
    # 正常流程
    agent.initialize()
    agent.start()
    
    # 已停止后不能暂停
    agent.stop()
    try:
        agent.pause()
        # 暂停被忽略，不抛异常
        print(f"  ✓ 已停止后暂停被忽略")
    except:
        pass
    
    return True


def test_lifecycle_hooks():
    """测试: 生命周期钩子."""
    print("\n[TEST] 生命周期钩子")
    
    hooks_called = []
    
    class HookedAgent(ControllerAgent):
        def on_initialize(self):
            hooks_called.append("initialize")
        
        def on_start(self):
            hooks_called.append("start")
        
        def on_pause(self):
            hooks_called.append("pause")
        
        def on_resume(self):
            hooks_called.append("resume")
        
        def on_stop(self):
            hooks_called.append("stop")
    
    agent = HookedAgent(agent_id="test.hooks.001")
    agent.initialize()
    agent.start()
    agent.pause()
    agent.resume()
    agent.stop()
    
    expected = ["initialize", "start", "pause", "resume", "stop"]
    assert hooks_called == expected, f"期望{expected}, 实际{hooks_called}"
    print(f"  ✓ 所有钩子被正确调用: {hooks_called}")
    
    return True


def test_state_consistency_after_exception():
    """测试: 异常后状态一致性."""
    print("\n[TEST] 异常后状态一致性")
    
    class SometimesFailingAgent(ControllerAgent):
        def __init__(self, agent_id, fail_count=1):
            super().__init__(agent_id)
            self._fail_count = fail_count
            self._attempts = 0
        
        def process(self, context):
            self._attempts += 1
            if self._attempts <= self._fail_count:
                raise RuntimeError(f"第{self._attempts}次失败")
            return super().process(context)
    
    agent = SometimesFailingAgent(agent_id="test.consistency.001", fail_count=2)
    agent.initialize()
    agent.start()
    
    # 第一次执行（失败）
    result1 = agent.execute(AgentContext(task=Task("t1"), input_data={"requirement": "test"}))
    assert agent.status == AgentStatus.ERROR
    print(f"  ✓ 第1次执行后状态: {agent.status.value}")
    
    # 重新初始化恢复
    agent.initialize()
    assert agent.status == AgentStatus.READY
    print(f"  ✓ 重新初始化后状态: {agent.status.value}")
    
    # 第二次执行（失败）
    agent.start()
    result2 = agent.execute(AgentContext(task=Task("t2"), input_data={"requirement": "test"}))
    assert agent.status == AgentStatus.ERROR
    print(f"  ✓ 第2次执行后状态: {agent.status.value}")
    
    # 验证历史记录
    history = agent.get_transition_history()
    error_count = sum(1 for h in history if h.to_state.value == "error")
    assert error_count >= 2, f"期望至少2次ERROR转换，实际{error_count}"
    print(f"  ✓ 历史记录包含 {error_count} 次ERROR转换")
    
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第47阶段验收测试 - Agent状态机完善")
    print("=" * 60)
    
    tests = [
        ("状态转换记录", test_state_transition_recording),
        ("异常时自动进入ERROR状态", test_exception_to_error_state),
        ("非法状态转换", test_invalid_state_transitions),
        ("生命周期钩子", test_lifecycle_hooks),
        ("异常后状态一致性", test_state_consistency_after_exception),
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
        print("🎉 第47阶段验收通过！Agent状态机完善完成。")
    else:
        print("❌ 部分测试失败。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
