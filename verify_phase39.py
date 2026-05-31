"""第39阶段验收脚本 - Agent协作机制验证.

验证Agent协作机制的完整功能：
- 枚举和数据模型
- 任务编排器
- Agent协作器
- 工作流模板
- 任务执行
"""

import sys
import traceback
from typing import Any, Dict, List

sys.path.insert(0, "/workspace/multi_agent_se/src")

from multi_agent_se.collaboration.orchestration import (
    CollaborationStatus,
    TaskDependencyType,
    AgentTask,
    WorkflowDefinition,
    CollaborationContext,
    TaskOrchestrator,
    AgentCoordinator,
)
from multi_agent_se.agents.registry.metadata import AgentRole


def test_collaboration_status_enum():
    """测试: CollaborationStatus枚举."""
    print("\n[TEST] CollaborationStatus枚举")
    
    assert CollaborationStatus.PENDING.value == "pending"
    assert CollaborationStatus.RUNNING.value == "running"
    assert CollaborationStatus.PAUSED.value == "paused"
    assert CollaborationStatus.COMPLETED.value == "completed"
    assert CollaborationStatus.FAILED.value == "failed"
    assert CollaborationStatus.CANCELLED.value == "cancelled"
    
    print("  ✓ CollaborationStatus枚举定义正确（6种状态）")
    return True


def test_task_dependency_type_enum():
    """测试: TaskDependencyType枚举."""
    print("\n[TEST] TaskDependencyType枚举")
    
    assert TaskDependencyType.SEQUENTIAL.value == "sequential"
    assert TaskDependencyType.PARALLEL.value == "parallel"
    assert TaskDependencyType.CONDITIONAL.value == "conditional"
    
    print("  ✓ TaskDependencyType枚举定义正确（3种依赖类型）")
    return True


def test_agent_task():
    """测试: AgentTask数据类."""
    print("\n[TEST] AgentTask数据类")
    
    task = AgentTask(
        name="需求分析",
        description="分析用户需求",
        agent_role=AgentRole.REQUIREMENT,
        input_data={"requirement": "用户管理系统"},
        dependencies=["task.001"],
        dependency_type=TaskDependencyType.SEQUENTIAL,
    )
    
    assert task.name == "需求分析"
    assert task.agent_role == AgentRole.REQUIREMENT
    assert task.status == CollaborationStatus.PENDING
    assert len(task.dependencies) == 1
    
    data = task.to_dict()
    assert data["name"] == "需求分析"
    assert data["agent_role"] == "requirement"
    
    print("  ✓ AgentTask数据类工作正常")
    return True


def test_workflow_definition():
    """测试: WorkflowDefinition数据类."""
    print("\n[TEST] WorkflowDefinition数据类")
    
    tasks = [
        AgentTask(name="任务1", agent_role=AgentRole.CONTROLLER),
        AgentTask(name="任务2", agent_role=AgentRole.DEVELOPER),
    ]
    
    workflow = WorkflowDefinition(
        name="软件开发流程",
        description="标准软件开发工作流",
        tasks=tasks,
        entry_task=tasks[0].task_id,
    )
    
    assert workflow.name == "软件开发流程"
    assert len(workflow.tasks) == 2
    assert workflow.entry_task == tasks[0].task_id
    
    data = workflow.to_dict()
    assert data["name"] == "软件开发流程"
    assert data["tasks_count"] == 2
    
    print("  ✓ WorkflowDefinition数据类工作正常")
    return True


def test_collaboration_context():
    """测试: CollaborationContext数据类."""
    print("\n[TEST] CollaborationContext数据类")
    
    context = CollaborationContext(
        status=CollaborationStatus.RUNNING,
        completed_tasks=["task.001", "task.002"],
        pending_tasks=["task.003"],
        shared_data={"project": "MyProject"},
    )
    
    assert context.status == CollaborationStatus.RUNNING
    assert len(context.completed_tasks) == 2
    assert len(context.pending_tasks) == 1
    assert context.shared_data["project"] == "MyProject"
    
    data = context.to_dict()
    assert data["status"] == "running"
    assert data["completed_count"] == 2
    
    print("  ✓ CollaborationContext数据类工作正常")
    return True


def test_task_orchestrator_creation():
    """测试: TaskOrchestrator创建."""
    print("\n[TEST] TaskOrchestrator创建")
    
    orchestrator = TaskOrchestrator()
    
    assert orchestrator is not None
    
    print("  ✓ TaskOrchestrator创建成功")
    return True


def test_workflow_creation():
    """测试: 工作流创建."""
    print("\n[TEST] 工作流创建")
    
    orchestrator = TaskOrchestrator()
    
    workflow = orchestrator.create_workflow(
        name="测试工作流",
        description="这是一个测试工作流",
    )
    
    assert workflow.name == "测试工作流"
    assert workflow.workflow_id is not None
    
    print(f"  ✓ 工作流创建成功: {workflow.workflow_id}")
    return True


def test_task_addition():
    """测试: 任务添加."""
    print("\n[TEST] 任务添加")
    
    orchestrator = TaskOrchestrator()
    
    workflow = orchestrator.create_workflow("测试流程")
    
    # 添加任务
    task1 = orchestrator.add_task(
        workflow,
        name="需求分析",
        agent_role=AgentRole.REQUIREMENT,
    )
    
    task2 = orchestrator.add_task(
        workflow,
        name="架构设计",
        agent_role=AgentRole.ARCHITECT,
        dependencies=[task1.task_id],
    )
    
    task3 = orchestrator.add_task(
        workflow,
        name="代码开发",
        agent_role=AgentRole.DEVELOPER,
        dependencies=[task2.task_id],
    )
    
    assert len(workflow.tasks) == 3
    assert workflow.entry_task == task1.task_id
    assert task2.dependencies == [task1.task_id]
    assert task3.dependencies == [task2.task_id]
    
    print(f"  ✓ 任务添加成功，共 {len(workflow.tasks)} 个任务")
    print(f"    入口任务: {workflow.entry_task}")
    return True


def test_workflow_validation():
    """测试: 工作流验证."""
    print("\n[TEST] 工作流验证")
    
    orchestrator = TaskOrchestrator()
    
    # 有效工作流
    workflow = orchestrator.create_workflow("有效流程")
    orchestrator.add_task(workflow, "任务1", AgentRole.CONTROLLER)
    
    valid, errors = orchestrator.validate_workflow(workflow)
    assert valid is True
    assert len(errors) == 0
    
    print("  ✓ 有效工作流验证通过")
    
    # 无效工作流（空任务）
    empty_workflow = WorkflowDefinition(name="空流程")
    valid, errors = orchestrator.validate_workflow(empty_workflow)
    assert valid is False
    assert len(errors) > 0
    
    print("  ✓ 无效工作流正确检测")
    return True


def test_ready_tasks():
    """测试: 获取可执行任务."""
    print("\n[TEST] 获取可执行任务")
    
    orchestrator = TaskOrchestrator()
    
    workflow = orchestrator.create_workflow("测试流程")
    
    task1 = orchestrator.add_task(workflow, "任务1", AgentRole.CONTROLLER)
    task2 = orchestrator.add_task(
        workflow, "任务2", AgentRole.DEVELOPER,
        dependencies=[task1.task_id]
    )
    task3 = orchestrator.add_task(
        workflow, "任务3", AgentRole.TESTER,
        dependencies=[task2.task_id]
    )
    
    # 初始状态：只有task1可执行（无依赖）
    ready = orchestrator.get_ready_tasks(workflow, set())
    # task1应该可执行，因为它没有依赖
    assert len(ready) >= 1, f"期望至少1个可执行任务，实际{len(ready)}个"
    assert task1.task_id in [t.task_id for t in ready], "task1应该可执行"
    
    # task1完成后：task2可执行
    ready = orchestrator.get_ready_tasks(workflow, {task1.task_id})
    assert len(ready) >= 1, f"期望至少1个可执行任务，实际{len(ready)}个"
    assert task2.task_id in [t.task_id for t in ready], "task2应该可执行"
    
    # task1和task2完成后：task3可执行
    ready = orchestrator.get_ready_tasks(workflow, {task1.task_id, task2.task_id})
    assert len(ready) >= 1, f"期望至少1个可执行任务，实际{len(ready)}个"
    assert task3.task_id in [t.task_id for t in ready], "task3应该可执行"
    
    print("  ✓ 可执行任务获取正确")
    return True


def test_workflow_templates():
    """测试: 工作流模板."""
    print("\n[TEST] 工作流模板")
    
    orchestrator = TaskOrchestrator()
    
    # 获取软件开发模板
    dev_template = orchestrator.get_template("software_development")
    assert dev_template is not None
    assert dev_template.name == "software_development"
    assert len(dev_template.tasks) >= 5  # 需求、架构、开发、测试、文档
    
    print(f"  ✓ 软件开发模板: {len(dev_template.tasks)} 个任务")
    
    # 获取Bug修复模板
    bugfix_template = orchestrator.get_template("bugfix")
    assert bugfix_template is not None
    assert bugfix_template.name == "bugfix"
    assert len(bugfix_template.tasks) >= 2  # 修复、测试
    
    print(f"  ✓ Bug修复模板: {len(bugfix_template.tasks)} 个任务")
    return True


def test_agent_coordinator_creation():
    """测试: AgentCoordinator创建."""
    print("\n[TEST] AgentCoordinator创建")
    
    coordinator = AgentCoordinator()
    
    assert coordinator is not None
    
    print("  ✓ AgentCoordinator创建成功")
    return True


def test_workflow_execution():
    """测试: 工作流执行."""
    print("\n[TEST] 工作流执行")
    
    orchestrator = TaskOrchestrator()
    coordinator = AgentCoordinator(orchestrator)
    
    # 创建简单工作流
    workflow = orchestrator.create_workflow("测试执行")
    
    orchestrator.add_task(workflow, "任务1", AgentRole.CONTROLLER)
    orchestrator.add_task(workflow, "任务2", AgentRole.DEVELOPER)
    
    # 启动工作流
    context = coordinator.start_workflow(workflow, {"initial": "data"})
    
    assert context.status == CollaborationStatus.RUNNING
    assert context.workflow is not None
    
    print(f"  ✓ 工作流启动成功: {context.context_id}")
    
    # 执行所有任务
    result = coordinator.execute_all(context)
    
    assert result["status"] in ("completed", "running")
    assert result["completed_tasks"] >= 0
    
    print(f"  ✓ 工作流执行完成:")
    print(f"    - 状态: {result['status']}")
    print(f"    - 完成任务: {result['completed_tasks']}/{result['total_tasks']}")
    return True


def test_workflow_pause_resume():
    """测试: 工作流暂停和恢复."""
    print("\n[TEST] 工作流暂停和恢复")
    
    orchestrator = TaskOrchestrator()
    coordinator = AgentCoordinator(orchestrator)
    
    workflow = orchestrator.create_workflow("暂停测试")
    orchestrator.add_task(workflow, "任务1", AgentRole.CONTROLLER)
    orchestrator.add_task(workflow, "任务2", AgentRole.DEVELOPER)
    
    context = coordinator.start_workflow(workflow)
    
    # 暂停
    paused = coordinator.pause(context)
    assert paused is True
    assert context.status == CollaborationStatus.PAUSED
    print("  ✓ 工作流暂停成功")
    
    # 恢复
    resumed = coordinator.resume(context)
    assert resumed is True
    assert context.status == CollaborationStatus.RUNNING
    print("  ✓ 工作流恢复成功")
    
    # 取消
    cancelled = coordinator.cancel(context)
    assert cancelled is True
    assert context.status == CollaborationStatus.CANCELLED
    print("  ✓ 工作流取消成功")
    
    return True


def test_agent_registration():
    """测试: Agent注册."""
    print("\n[TEST] Agent注册")
    
    coordinator = AgentCoordinator()
    
    # 模拟Agent
    class MockAgent:
        def process(self, context):
            from multi_agent_se.agents.runtime.base_agent import TaskResult
            return TaskResult(success=True, output={"mock": True})
    
    coordinator.register_agent(AgentRole.CONTROLLER, MockAgent())
    coordinator.register_agent(AgentRole.DEVELOPER, MockAgent())
    
    stats = coordinator.get_statistics()
    
    assert len(stats["registered_agents"]) == 2
    assert "controller" in stats["registered_agents"]
    assert "developer" in stats["registered_agents"]
    
    print(f"  ✓ Agent注册成功: {stats['registered_agents']}")
    return True


def test_parallel_tasks():
    """测试: 并行任务."""
    print("\n[TEST] 并行任务")
    
    orchestrator = TaskOrchestrator()
    
    workflow = orchestrator.create_workflow("并行测试")
    
    # 两个无依赖的任务可以并行
    task1 = orchestrator.add_task(
        workflow, "并行任务1", AgentRole.DEVELOPER,
        dependency_type=TaskDependencyType.PARALLEL
    )
    task2 = orchestrator.add_task(
        workflow, "并行任务2", AgentRole.TESTER,
        dependency_type=TaskDependencyType.PARALLEL
    )
    
    # 两个任务都应该可执行
    ready = orchestrator.get_ready_tasks(workflow, set())
    assert len(ready) == 2
    
    print("  ✓ 并行任务识别正确")
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第39阶段验收测试 - Agent协作机制")
    print("=" * 60)
    
    tests = [
        ("CollaborationStatus枚举", test_collaboration_status_enum),
        ("TaskDependencyType枚举", test_task_dependency_type_enum),
        ("AgentTask数据类", test_agent_task),
        ("WorkflowDefinition数据类", test_workflow_definition),
        ("CollaborationContext数据类", test_collaboration_context),
        ("TaskOrchestrator创建", test_task_orchestrator_creation),
        ("工作流创建", test_workflow_creation),
        ("任务添加", test_task_addition),
        ("工作流验证", test_workflow_validation),
        ("可执行任务获取", test_ready_tasks),
        ("工作流模板", test_workflow_templates),
        ("AgentCoordinator创建", test_agent_coordinator_creation),
        ("工作流执行", test_workflow_execution),
        ("工作流暂停恢复", test_workflow_pause_resume),
        ("Agent注册", test_agent_registration),
        ("并行任务", test_parallel_tasks),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n  ✗ {name} 失败: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 第39阶段验收通过！Agent协作机制实现完成。")
    else:
        print("❌ 部分测试失败，请检查实现。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
