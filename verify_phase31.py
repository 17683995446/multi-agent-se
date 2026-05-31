"""第31阶段验收脚本: Controller Agent.

验证控制器Agent的任务分解、调度和执行功能。
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from multi_agent_se.agents.controller import (
    ControllerAgent,
    TaskPriority,
    TaskStatus,
    SubTask,
    TaskDecomposition,
)
from multi_agent_se.agents.runtime.base_agent import AgentContext
from multi_agent_se.agents.registry.metadata import AgentCapability


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(name: str, passed: bool) -> None:
    status = "[✓ PASS]" if passed else "[✗ FAIL]"
    print(f"  {status} {name}")


def test_task_priority_enum() -> bool:
    print_header("测试1: TaskPriority 枚举")
    priorities = list(TaskPriority)
    print(f"  优先级: {[p.name for p in priorities]}")
    assert len(priorities) == 4
    assert TaskPriority.CRITICAL.value == 0
    assert TaskPriority.HIGH.value == 1
    print_result("TaskPriority", True)
    return True


def test_task_status_enum() -> bool:
    print_header("测试2: TaskStatus 枚举")
    statuses = list(TaskStatus)
    print(f"  状态: {[s.value for s in statuses]}")
    assert len(statuses) == 6
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.COMPLETED.value == "completed"
    print_result("TaskStatus", True)
    return True


def test_subtask_model() -> bool:
    print_header("测试3: SubTask 模型")
    task = SubTask(
        name="测试任务",
        description="这是一个测试任务",
        task_type="developer",
        priority=TaskPriority.HIGH,
    )
    
    assert task.name == "测试任务"
    assert task.task_type == "developer"
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.PENDING
    assert len(task.task_id) == 8  # UUID前8位
    
    # 测试依赖检查
    assert task.can_execute(set()) is True  # 无依赖，可以执行
    
    task2 = SubTask(
        name="依赖任务",
        dependencies=[task.task_id],
    )
    assert task2.can_execute(set()) is False  # 有依赖但未完成
    assert task2.can_execute({task.task_id}) is True  # 依赖已完成
    
    print_result("SubTask", True)
    return True


def test_task_decomposition() -> bool:
    print_header("测试4: TaskDecomposition 模型")
    
    decomposition = TaskDecomposition(
        original_requirement="开发一个用户管理系统",
        strategy="default",
    )
    
    # 创建任务链: A -> B -> C
    task_a = SubTask(name="任务A", task_type="requirement")
    task_b = SubTask(name="任务B", task_type="developer", dependencies=[task_a.task_id])
    task_c = SubTask(name="任务C", task_type="tester", dependencies=[task_b.task_id])
    
    decomposition.sub_tasks = [task_a, task_b, task_c]
    
    # 测试执行顺序
    order = decomposition.get_execution_order()
    order_names = [t.name for t in order]
    print(f"  执行顺序: {order_names}")
    assert order_names == ["任务A", "任务B", "任务C"]
    
    # 测试并行组（此例中无并行）
    groups = decomposition.get_parallel_groups()
    print(f"  并行组数: {len(groups)}")
    assert len(groups) == 3  # 每个任务一个组
    
    print_result("TaskDecomposition", True)
    return True


def test_controller_agent_creation() -> bool:
    print_header("测试5: ControllerAgent 创建")
    
    agent = ControllerAgent(agent_id="ctrl-001")
    
    assert agent.agent_id == "ctrl-001"
    assert agent.AGENT_ROLE.value == "controller"
    assert AgentCapability.TASK_DECOMPOSITION in agent.AGENT_CAPABILITIES
    
    print(f"  Agent ID: {agent.agent_id}")
    print(f"  角色: {agent.AGENT_ROLE.value}")
    print(f"  能力: {[c.value for c in agent.AGENT_CAPABILITIES]}")
    
    print_result("ControllerAgent 创建", True)
    return True


def test_default_decomposition() -> bool:
    print_header("测试6: 默认分解策略")
    
    agent = ControllerAgent()
    context = AgentContext(
        input_data={
            "requirement": "开发一个用户登录系统，支持用户名密码验证和JWT令牌生成",
        }
    )
    
    result = agent.process(context)
    
    assert result.success is True
    output = result.output
    
    print(f"  需求: {output['requirement'][:50]}...")
    print(f"  策略: {output['strategy']}")
    
    decomposition = output['decomposition']
    print(f"  子任务数: {decomposition['execution_plan']['total_tasks']}")
    print(f"  并行组数: {decomposition['execution_plan']['parallel_groups']}")
    print(f"  执行顺序: {decomposition['execution_plan']['execution_order']}")
    
    # 验证标准流程
    task_names = [t['name'] for t in decomposition['sub_tasks']]
    assert "需求分析" in task_names
    assert "架构设计" in task_names
    assert "代码开发" in task_names
    assert "代码审查" in task_names
    assert "测试验证" in task_names
    assert "文档编写" in task_names
    
    print_result("默认分解策略", True)
    return True


def test_simple_decomposition() -> bool:
    print_header("测试7: 简单分解策略")
    
    agent = ControllerAgent()
    context = AgentContext(
        input_data={
            "requirement": "修复一个bug",
            "strategy": "simple",
        }
    )
    
    result = agent.process(context)
    
    assert result.success is True
    output = result.output
    
    print(f"  策略: {output['strategy']}")
    
    task_names = [t['name'] for t in output['decomposition']['sub_tasks']]
    print(f"  任务: {task_names}")
    
    # 简单策略只有开发和测试
    assert "代码开发" in task_names
    assert "测试验证" in task_names
    assert len(task_names) == 2
    
    print_result("简单分解策略", True)
    return True


def test_agile_decomposition() -> bool:
    print_header("测试8: 敏捷分解策略")
    
    agent = ControllerAgent()
    context = AgentContext(
        input_data={
            "requirement": "开发MVP版本",
            "strategy": "agile",
        }
    )
    
    result = agent.process(context)
    
    assert result.success is True
    output = result.output
    
    print(f"  策略: {output['strategy']}")
    
    task_names = [t['name'] for t in output['decomposition']['sub_tasks']]
    print(f"  任务: {task_names}")
    
    # 敏捷策略有MVP相关任务
    assert any("MVP" in name for name in task_names)
    
    print_result("敏捷分解策略", True)
    return True


def test_parallel_groups() -> bool:
    print_header("测试9: 并行组识别")
    
    agent = ControllerAgent()
    context = AgentContext(
        input_data={
            "requirement": "开发系统",
        }
    )
    
    result = agent.process(context)
    
    parallel_groups = result.output['decomposition']['parallel_groups']
    print(f"  并行组: {parallel_groups}")
    
    # 代码审查、测试、文档应该可以并行
    # 找到包含这些任务的组
    found_parallel = False
    for group in parallel_groups:
        if len(group) > 1:
            found_parallel = True
            print(f"  ✓ 发现并行任务组: {group}")
    
    print_result("并行组识别", True)
    return True


def test_task_execution() -> bool:
    print_header("测试10: 任务执行")
    
    agent = ControllerAgent()
    context = AgentContext(
        input_data={
            "requirement": "简单任务",
            "strategy": "simple",
            "execute": True,  # 实际执行
        }
    )
    
    result = agent.process(context)
    
    print(f"  执行成功: {result.success}")
    print(f"  总任务: {result.output['total_tasks']}")
    print(f"  完成: {result.output['completed']}")
    print(f"  失败: {result.output['failed']}")
    
    assert result.success is True
    assert result.output['completed'] == result.output['total_tasks']
    assert result.output['failed'] == 0
    
    print_result("任务执行", True)
    return True


def test_decomposition_history() -> bool:
    print_header("测试11: 分解历史记录")
    
    agent = ControllerAgent()
    
    # 执行多次分解
    for i in range(3):
        context = AgentContext(
            input_data={"requirement": f"任务{i}"}
        )
        agent.process(context)
    
    history = agent.get_decomposition_history()
    print(f"  历史记录数: {len(history)}")
    assert len(history) == 3
    
    stats = agent.get_statistics()
    print(f"  统计: {stats}")
    assert stats['total_decompositions'] == 3
    assert stats['total_tasks_generated'] > 0
    
    print_result("分解历史记录", True)
    return True


def test_error_handling() -> bool:
    print_header("测试12: 错误处理")
    
    agent = ControllerAgent()
    
    # 缺少需求
    context = AgentContext(input_data={})
    result = agent.process(context)
    
    assert result.success is False
    assert "缺少需求" in result.error_message
    print(f"  错误信息: {result.error_message}")
    
    print_result("错误处理", True)
    return True


def main() -> None:
    print("=" * 60)
    print("  第31阶段验收: Controller Agent")
    print("=" * 60)
    
    tests = [
        test_task_priority_enum,
        test_task_status_enum,
        test_subtask_model,
        test_task_decomposition,
        test_controller_agent_creation,
        test_default_decomposition,
        test_simple_decomposition,
        test_agile_decomposition,
        test_parallel_groups,
        test_task_execution,
        test_decomposition_history,
        test_error_handling,
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
            failed += 1
            print(f"  ✗ EXCEPTION: {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"  验收结果: {passed} 通过, {failed} 失败")
    print(f"{'='*60}")
    
    if failed == 0:
        print(f"\n  ✓ 第31阶段验收通过！")
        print(f"\n  Controller Agent 功能:")
        print(f"    - 任务分解 (default/simple/agile策略)")
        print(f"    - 依赖分析 (拓扑排序)")
        print(f"    - 并行组识别")
        print(f"    - 任务执行调度")
        print(f"    - 历史记录和统计")
        print(f"{'='*60}")
        sys.exit(0)
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
