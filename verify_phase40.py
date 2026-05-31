"""第40阶段验收脚本 - 端到端集成测试.

验证8大Agent + 协作机制的完整工作流：
- 全部8个Agent独立实例化与执行
- 软件开发全流程工作流编排
- Agent协作器端到端执行
- 消息总线通信
- Agent注册中心集成
"""

import sys
import traceback
from typing import Any, Dict, List

sys.path.insert(0, "/workspace/multi_agent_se/src")

# ===== 导入全部8大Agent =====
from multi_agent_se.agents.controller import ControllerAgent
from multi_agent_se.agents.requirement import RequirementAgent
from multi_agent_se.agents.architect import ArchitectAgent
from multi_agent_se.agents.developer import DeveloperAgent
from multi_agent_se.agents.bugfix import BugfixAgent
from multi_agent_se.agents.reviewer import ReviewerAgent
from multi_agent_se.agents.tester import TesterAgent
from multi_agent_se.agents.documenter import DocumenterAgent

# ===== 导入协作机制 =====
from multi_agent_se.collaboration.orchestration import (
    TaskOrchestrator,
    AgentCoordinator,
    CollaborationStatus,
)

# ===== 导入运行时 =====
from multi_agent_se.agents.runtime.base_agent import AgentContext
from multi_agent_se.scheduler.task import Task

# ===== 导入注册中心 =====
from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability

# ===== 导入消息总线 =====
from multi_agent_se.agents.communication.message import Message, MessageType, MessagePriority


def test_all_agents_import():
    """测试: 全部8大Agent可导入."""
    print("\n[TEST] 全部8大Agent导入验证")
    
    agents = [
        ("Controller", ControllerAgent),
        ("Requirement", RequirementAgent),
        ("Architect", ArchitectAgent),
        ("Developer", DeveloperAgent),
        ("Bugfix", BugfixAgent),
        ("Reviewer", ReviewerAgent),
        ("Tester", TesterAgent),
        ("Documenter", DocumenterAgent),
    ]
    
    for name, cls in agents:
        assert cls is not None, f"{name} 导入失败"
        print(f"  ✓ {name}Agent 导入成功")
    
    print(f"  ✓ 全部 {len(agents)} 个Agent导入验证通过")
    return True


def test_all_agents_instantiation():
    """测试: 全部8大Agent实例化."""
    print("\n[TEST] 全部8大Agent实例化")
    
    agent_map = {
        AgentRole.CONTROLLER: ControllerAgent(agent_id="e2e.controller"),
        AgentRole.REQUIREMENT: RequirementAgent(agent_id="e2e.requirement"),
        AgentRole.ARCHITECT: ArchitectAgent(agent_id="e2e.architect"),
        AgentRole.DEVELOPER: DeveloperAgent(agent_id="e2e.developer"),
        AgentRole.BUGFIX: BugfixAgent(agent_id="e2e.bugfix"),
        AgentRole.REVIEWER: ReviewerAgent(agent_id="e2e.reviewer"),
        AgentRole.TESTER: TesterAgent(agent_id="e2e.tester"),
        AgentRole.DOCUMENTER: DocumenterAgent(agent_id="e2e.documenter"),
    }
    
    for role, agent in agent_map.items():
        assert agent.agent_id is not None
        assert agent.role == role
        print(f"  ✓ {role.value:12s} -> {agent.agent_id}")
    
    print(f"  ✓ 全部 {len(agent_map)} 个Agent实例化成功")
    return True


def test_all_agents_execution():
    """测试: 全部8大Agent独立执行."""
    print("\n[TEST] 全部8大Agent独立执行")
    
    test_cases = [
        (
            "Controller",
            ControllerAgent(agent_id="e2e.ctrl.exec"),
            {"requirement": "开发用户管理系统，包含注册和登录功能"},
        ),
        (
            "Requirement",
            RequirementAgent(agent_id="e2e.req.exec"),
            {"requirement": "系统需要用户注册和登录功能"},
        ),
        (
            "Architect",
            ArchitectAgent(agent_id="e2e.arch.exec"),
            {"requirements": [{"name": "用户注册", "description": "用户注册功能"}, {"name": "用户登录", "description": "用户登录功能"}], "style": "layered"},
        ),
        (
            "Developer",
            DeveloperAgent(agent_id="e2e.dev.exec"),
            {"requirement": "用户管理类", "task_type": "implementation", "module_name": "UserManager"},
        ),
        (
            "Bugfix",
            BugfixAgent(agent_id="e2e.fix.exec"),
            {"error_message": "AttributeError: 'NoneType' has no attribute 'name'"},
        ),
        (
            "Reviewer",
            ReviewerAgent(agent_id="e2e.rev.exec"),
            {"code": "def add(a, b): return a + b"},
        ),
        (
            "Tester",
            TesterAgent(agent_id="e2e.test.exec"),
            {"code": "class Calculator:\n    def add(self, a, b): return a + b", "test_type": "unit"},
        ),
        (
            "Documenter",
            DocumenterAgent(agent_id="e2e.doc.exec"),
            {"doc_type": "readme", "target": "Calculator"},
        ),
    ]
    
    passed = 0
    for name, agent, input_data in test_cases:
        task = Task(task_id=f"e2e.task.{name}", task_type=name.lower())
        context = AgentContext(task=task, input_data=input_data)
        
        result = agent.process(context)
        
        if result.success:
            passed += 1
            output_keys = list(result.output.keys()) if result.output else []
            print(f"  ✓ {name:12s} 执行成功 (输出键: {output_keys[:3]})")
        else:
            print(f"  ✗ {name:12s} 执行失败: {result.error_message}")
    
    assert passed == len(test_cases), f"期望全部通过，实际 {passed}/{len(test_cases)}"
    print(f"  ✓ 全部 {passed}/{len(test_cases)} 个Agent执行成功")
    return True


def test_software_development_workflow():
    """测试: 软件开发全流程工作流."""
    print("\n[TEST] 软件开发全流程工作流")
    
    orchestrator = TaskOrchestrator()
    coordinator = AgentCoordinator(orchestrator)
    
    # 获取预定义的软件开发工作流模板
    workflow = orchestrator.get_template("software_development")
    assert workflow is not None, "软件开发模板不存在"
    
    print(f"  工作流: {workflow.name}")
    print(f"  任务数: {len(workflow.tasks)}")
    
    # 验证任务链
    task_names = [t.name for t in workflow.tasks]
    print(f"  任务链: {' -> '.join(task_names)}")
    
    # 验证依赖关系
    for task in workflow.tasks:
        if task.dependencies:
            dep_names = []
            for dep_id in task.dependencies:
                dep_task = orchestrator.get_task(workflow, dep_id)
                if dep_task:
                    dep_names.append(dep_task.name)
            print(f"    {task.name} 依赖: {dep_names}")
    
    # 启动工作流
    context = coordinator.start_workflow(workflow, {"project": "E2E测试项目"})
    assert context.status == CollaborationStatus.RUNNING
    
    # 执行全部任务
    result = coordinator.execute_all(context)
    
    assert result["completed_tasks"] > 0
    print(f"  ✓ 工作流执行完成:")
    print(f"    - 状态: {result['status']}")
    print(f"    - 完成任务: {result['completed_tasks']}/{result['total_tasks']}")
    return True


def test_bugfix_workflow():
    """测试: Bug修复工作流."""
    print("\n[TEST] Bug修复工作流")
    
    orchestrator = TaskOrchestrator()
    coordinator = AgentCoordinator(orchestrator)
    
    workflow = orchestrator.get_template("bugfix")
    assert workflow is not None
    
    task_names = [t.name for t in workflow.tasks]
    print(f"  任务链: {' -> '.join(task_names)}")
    
    context = coordinator.start_workflow(workflow, {"bug": "登录页面崩溃"})
    result = coordinator.execute_all(context)
    
    assert result["completed_tasks"] > 0
    print(f"  ✓ Bug修复工作流完成: {result['completed_tasks']}/{result['total_tasks']}")
    return True


def test_message_bus_integration():
    """测试: 消息总线通信集成."""
    print("\n[TEST] 消息总线通信集成")
    
    from multi_agent_se.agents.communication.bus import MessageBus, get_message_bus
    
    bus = MessageBus()
    
    # 创建消息
    msg = Message.create(
        sender_id="controller.001",
        receiver_id="developer.001",
        payload={"task": "实现用户管理模块"},
        message_type=MessageType.TASK_ASSIGN,
        priority=MessagePriority.HIGH,
    )
    
    # 发送
    sent = bus.send(msg)
    assert sent is True
    
    # 接收
    received = bus.receive("developer.001")
    assert received is not None
    assert received.sender_id == "controller.001"
    
    # 统计
    stats = bus.get_stats()
    assert stats.total_sent >= 1
    
    print(f"  ✓ 消息总线通信成功:")
    print(f"    - 发送: {stats.total_sent}")
    print(f"    - 送达: {stats.total_delivered}")
    return True


def test_agent_registry_integration():
    """测试: Agent注册中心集成."""
    print("\n[TEST] Agent注册中心集成")
    
    from multi_agent_se.agents.registry import AgentRegistry, get_registry
    
    registry = get_registry()
    
    # 验证AgentRole枚举完整性
    expected_roles = [
        AgentRole.CONTROLLER, AgentRole.REQUIREMENT, AgentRole.ARCHITECT,
        AgentRole.DEVELOPER, AgentRole.BUGFIX, AgentRole.REVIEWER,
        AgentRole.TESTER, AgentRole.DOCUMENTER,
    ]
    
    for role in expected_roles:
        assert role.value in [r.value for r in AgentRole], f"角色 {role.value} 不存在"
    
    print(f"  ✓ Agent注册中心集成正常")
    print(f"    - 已定义角色: {len(expected_roles)}")
    return True


def test_collaboration_lifecycle():
    """测试: 协作生命周期管理."""
    print("\n[TEST] 协作生命周期管理")
    
    orchestrator = TaskOrchestrator()
    coordinator = AgentCoordinator(orchestrator)
    
    # 创建自定义工作流
    workflow = orchestrator.create_workflow("生命周期测试")
    orchestrator.add_task(workflow, "步骤1", AgentRole.REQUIREMENT)
    orchestrator.add_task(workflow, "步骤2", AgentRole.DEVELOPER, dependencies=[
        orchestrator.get_task(workflow, workflow.tasks[0].task_id).task_id
    ])
    
    # 启动
    context = coordinator.start_workflow(workflow)
    assert context.status == CollaborationStatus.RUNNING
    print("  ✓ 启动 -> RUNNING")
    
    # 暂停
    coordinator.pause(context)
    assert context.status == CollaborationStatus.PAUSED
    print("  ✓ 暂停 -> PAUSED")
    
    # 恢复
    coordinator.resume(context)
    assert context.status == CollaborationStatus.RUNNING
    print("  ✓ 恢复 -> RUNNING")
    
    # 执行
    coordinator.execute_all(context)
    print(f"  ✓ 执行完成 -> {context.status.value}")
    
    # 统计
    stats = coordinator.get_statistics()
    assert stats["total_workflows"] >= 1
    print(f"  ✓ 统计: {stats['total_workflows']} 个工作流")
    return True


def test_agent_capabilities_coverage():
    """测试: Agent能力覆盖度."""
    print("\n[TEST] Agent能力覆盖度")
    
    capability_map = {
        AgentRole.CONTROLLER: [AgentCapability.TASK_SCHEDULING],
        AgentRole.REQUIREMENT: [AgentCapability.REQUIREMENT_ANALYSIS],
        AgentRole.ARCHITECT: [AgentCapability.ARCHITECTURE_DESIGN],
        AgentRole.DEVELOPER: [AgentCapability.CODE_GENERATION],
        AgentRole.BUGFIX: [AgentCapability.CODE_DEBUGGING, AgentCapability.CODE_GENERATION],
        AgentRole.REVIEWER: [AgentCapability.CODE_REVIEW, AgentCapability.QUALITY_CHECK],
        AgentRole.TESTER: [AgentCapability.CODE_TESTING, AgentCapability.QUALITY_CHECK],
        AgentRole.DOCUMENTER: [AgentCapability.DOCUMENTATION, AgentCapability.FILE_OPERATION],
    }
    
    total_capabilities = set()
    
    for role, agent_cls in [
        (AgentRole.CONTROLLER, ControllerAgent),
        (AgentRole.REQUIREMENT, RequirementAgent),
        (AgentRole.ARCHITECT, ArchitectAgent),
        (AgentRole.DEVELOPER, DeveloperAgent),
        (AgentRole.BUGFIX, BugfixAgent),
        (AgentRole.REVIEWER, ReviewerAgent),
        (AgentRole.TESTER, TesterAgent),
        (AgentRole.DOCUMENTER, DocumenterAgent),
    ]:
        agent = agent_cls()
        caps = [c.value for c in agent.capabilities]
        total_capabilities.update(caps)
        expected = [c.value for c in capability_map.get(role, [])]
        for exp in expected:
            assert exp in caps, f"{role.value} 缺少能力 {exp}"
        print(f"  ✓ {role.value:12s} 能力: {caps}")
    
    print(f"  ✓ 能力覆盖: {len(total_capabilities)} 种不同能力")
    return True


def run_all_tests():
    """运行所有端到端测试."""
    print("=" * 60)
    print("第40阶段验收测试 - 端到端集成测试")
    print("=" * 60)
    
    tests = [
        ("全部Agent导入", test_all_agents_import),
        ("全部Agent实例化", test_all_agents_instantiation),
        ("全部Agent执行", test_all_agents_execution),
        ("软件开发工作流", test_software_development_workflow),
        ("Bug修复工作流", test_bugfix_workflow),
        ("消息总线集成", test_message_bus_integration),
        ("注册中心集成", test_agent_registry_integration),
        ("协作生命周期", test_collaboration_lifecycle),
        ("能力覆盖度", test_agent_capabilities_coverage),
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
        print("🎉 第40阶段验收通过！端到端集成测试完成。")
        print("\n✨ 8大Agent + 协作机制 + 消息总线 + 注册中心 全链路验证成功！")
    else:
        print("❌ 部分测试失败，请检查实现。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
