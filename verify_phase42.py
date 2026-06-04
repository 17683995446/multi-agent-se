"""第42阶段验收脚本 - 复杂场景压力测试与Bug发现.

通过大规模、高复杂度、边界条件的真实实践，发现系统运行时问题。
测试覆盖:
- 空值/None输入
- 超长字符串
- 特殊字符注入
- 循环依赖检测
- 并发任务执行
- 大规模数据处理
- 异常传播与捕获
"""

import sys
import traceback
from typing import Any, Dict, List

sys.path.insert(0, "/workspace/multi_agent_se/src")

from multi_agent_se.agents.controller import ControllerAgent
from multi_agent_se.agents.requirement import RequirementAgent
from multi_agent_se.agents.architect import ArchitectAgent
from multi_agent_se.agents.developer import DeveloperAgent
from multi_agent_se.agents.bugfix import BugfixAgent
from multi_agent_se.agents.reviewer import ReviewerAgent
from multi_agent_se.agents.tester import TesterAgent
from multi_agent_se.agents.documenter import DocumenterAgent
from multi_agent_se.agents.runtime.base_agent import AgentContext
from multi_agent_se.scheduler.task import Task
from multi_agent_se.collaboration.orchestration import TaskOrchestrator, AgentCoordinator
from multi_agent_se.agents.communication.message import Message, MessagePriority
from multi_agent_se.utils.logging_helper import get_logger, StructuredLogger

StructuredLogger.set_enabled(True)
StructuredLogger.set_min_level("DEBUG")

logger = get_logger("verify_phase42")

BUGS_FOUND = []
WARNINGS = []


def record_bug(test_name: str, description: str, exception: Exception = None) -> None:
    """记录发现的Bug."""
    bug = {"test": test_name, "desc": description}
    if exception:
        bug["exception"] = str(exception)
        bug["traceback"] = traceback.format_exc()
    BUGS_FOUND.append(bug)
    logger.error(f"BUG发现: [{test_name}] {description}", exc=exception)


def record_warning(test_name: str, description: str) -> None:
    """记录警告."""
    WARNINGS.append({"test": test_name, "desc": description})
    logger.warn(f"警告: [{test_name}] {description}")


# ========== 场景1: 空值与None输入 ==========

def test_none_inputs():
    """测试: 所有Agent对None/空输入的处理."""
    print("\n[场景1] 空值与None输入测试")
    logger.info("开始空值输入测试")
    
    agents = [
        ("Controller", ControllerAgent(), {"requirement": None}),
        ("Controller", ControllerAgent(), {}),
        ("Requirement", RequirementAgent(), {"requirement": None}),
        ("Requirement", RequirementAgent(), {}),
        ("Architect", ArchitectAgent(), {"requirements": None}),
        ("Architect", ArchitectAgent(), {}),
        ("Developer", DeveloperAgent(), {"requirement": None}),
        ("Developer", DeveloperAgent(), {}),
        ("Bugfix", BugfixAgent(), {"error_message": None}),
        ("Bugfix", BugfixAgent(), {}),
        ("Reviewer", ReviewerAgent(), {"code": None}),
        ("Reviewer", ReviewerAgent(), {}),
        ("Tester", TesterAgent(), {"code": None}),
        ("Tester", TesterAgent(), {}),
        ("Documenter", DocumenterAgent(), {"doc_type": None}),
        ("Documenter", DocumenterAgent(), {}),
    ]
    
    for name, agent, input_data in agents:
        try:
            task = Task(task_id=f"null.{name}", task_type=name.lower())
            context = AgentContext(task=task, input_data=input_data)
            result = agent.process(context)
            
            if result.success:
                # 空输入返回成功可能是设计选择，但需记录
                logger.info(f"{name} 空输入返回成功", input_keys=list(input_data.keys()))
            else:
                logger.info(f"{name} 空输入正确拒绝: {result.error_message}")
                
        except Exception as e:
            record_bug(f"null_input_{name}", f"空输入导致未捕获异常", e)
    
    return True


# ========== 场景2: 超长字符串压力测试 ==========

def test_extremely_long_strings():
    """测试: 超长字符串输入."""
    print("\n[场景2] 超长字符串压力测试")
    logger.info("开始超长字符串测试")
    
    long_requirement = "用户管理系统" * 1000  # 6000字符
    long_code = "def func():\n    pass\n" * 500  # 大量代码
    
    test_cases = [
        ("Requirement", RequirementAgent(), {"requirement": long_requirement}),
        ("Developer", DeveloperAgent(), {"requirement": long_requirement[:100], "code": long_code}),
        ("Reviewer", ReviewerAgent(), {"code": long_code}),
        ("Documenter", DocumenterAgent(), {"code": long_code, "target": "Test"}),
    ]
    
    for name, agent, input_data in test_cases:
        try:
            task = Task(task_id=f"long.{name}", task_type=name.lower())
            context = AgentContext(task=task, input_data=input_data)
            result = agent.process(context)
            
            if result.success:
                logger.info(f"{name} 处理超长字符串成功")
            else:
                logger.info(f"{name} 处理超长字符串失败: {result.error_message}")
                
        except Exception as e:
            record_bug(f"long_string_{name}", f"超长字符串导致异常", e)
    
    return True


# ========== 场景3: 特殊字符与注入测试 ==========

def test_special_characters():
    """测试: 特殊字符和潜在注入."""
    print("\n[场景3] 特殊字符与注入测试")
    logger.info("开始特殊字符测试")
    
    special_inputs = [
        {"requirement": "<script>alert('xss')</script>"},
        {"requirement": "'; DROP TABLE users; --"},
        {"requirement": "\n\n\n\n\n\n\n\n\n\n"},
        {"requirement": "\x00\x01\x02\x03"},
        {"requirement": "日本語テスト中文测试"},
        {"requirement": "🔥🚀💻🐍"},
    ]
    
    for i, input_data in enumerate(special_inputs):
        try:
            agent = RequirementAgent()
            task = Task(task_id=f"special.{i}", task_type="requirement")
            context = AgentContext(task=task, input_data=input_data)
            result = agent.process(context)
            
            if result.success:
                logger.info(f"特殊字符测试 {i} 通过")
            else:
                logger.info(f"特殊字符测试 {i} 被拒绝: {result.error_message}")
                
        except Exception as e:
            record_bug(f"special_char_{i}", f"特殊字符导致异常", e)
    
    return True


# ========== 场景4: 循环依赖检测 ==========

def test_circular_dependency_detection():
    """测试: 循环依赖检测."""
    print("\n[场景4] 循环依赖检测测试")
    logger.info("开始循环依赖检测测试")
    
    orchestrator = TaskOrchestrator()
    
    # 创建有循环依赖的工作流
    workflow = orchestrator.create_workflow("循环依赖测试")
    task_a = orchestrator.add_task(workflow, "任务A", RequirementAgent.AGENT_ROLE)
    task_b = orchestrator.add_task(workflow, "任务B", DeveloperAgent.AGENT_ROLE, dependencies=[task_a.task_id])
    
    # 手动制造循环：让task_a依赖task_b（这不应该被允许）
    task_a.dependencies.append(task_b.task_id)
    
    valid, errors = orchestrator.validate_workflow(workflow)
    
    if valid:
        record_bug("circular_dep", "循环依赖未被检测到！")
    else:
        logger.info(f"循环依赖正确检测: {errors}")
    
    return True


# ========== 场景5: 大规模任务执行 ==========

def test_massive_task_execution():
    """测试: 大规模任务执行."""
    print("\n[场景5] 大规模任务执行测试")
    logger.info("开始大规模任务执行测试")
    
    orchestrator = TaskOrchestrator()
    coordinator = AgentCoordinator(orchestrator)
    
    # 创建包含大量任务的工作流
    workflow = orchestrator.create_workflow("大规模测试")
    
    prev_task = None
    for i in range(20):  # 20个任务链
        deps = [prev_task.task_id] if prev_task else []
        prev_task = orchestrator.add_task(
            workflow, f"任务{i}", RequirementAgent.AGENT_ROLE,
            dependencies=deps
        )
    
    try:
        context = coordinator.start_workflow(workflow, {"test": "massive"})
        result = coordinator.execute_all(context)
        
        logger.info(f"大规模执行完成: {result['completed_tasks']}/{result['total_tasks']}")
        
        if result['completed_tasks'] != result['total_tasks']:
            record_warning("massive_exec", f"未全部完成: {result}")
            
    except Exception as e:
        record_bug("massive_exec", "大规模执行失败", e)
    
    return True


# ========== 场景6: 并发/并行任务测试 ==========

def test_parallel_execution():
    """测试: 并行任务执行."""
    print("\n[场景6] 并行任务执行测试")
    logger.info("开始并行任务测试")
    
    orchestrator = TaskOrchestrator()
    coordinator = AgentCoordinator(orchestrator)
    
    workflow = orchestrator.create_workflow("并行测试")
    
    # 创建多个无依赖的并行任务
    for i in range(5):
        orchestrator.add_task(workflow, f"并行任务{i}", RequirementAgent.AGENT_ROLE)
    
    try:
        context = coordinator.start_workflow(workflow)
        result = coordinator.execute_all(context)
        
        logger.info(f"并行执行完成: {result['completed_tasks']}/{result['total_tasks']}")
        
    except Exception as e:
        record_bug("parallel_exec", "并行执行失败", e)
    
    return True


# ========== 场景7: 异常传播测试 ==========

def test_exception_handling():
    """测试: 异常传播与捕获."""
    print("\n[场景7] 异常传播测试")
    logger.info("开始异常传播测试")
    
    # 测试1: 输入非字典类型
    try:
        agent = ControllerAgent()
        task = Task(task_id="exc.1", task_type="controller")
        context = AgentContext(task=task, input_data="not_a_dict")
        result = agent.process(context)
        
        if not result.success:
            logger.info("非字典输入正确拒绝")
        else:
            record_warning("exception_1", "非字典输入被接受")
            
    except (AttributeError, TypeError) as e:
        record_bug("exception_1", "非字典输入导致AttributeError/TypeError", e)
    except Exception as e:
        record_bug("exception_1", "非字典输入导致未预期异常", e)
    
    # 测试2: 嵌套异常输入
    try:
        agent = BugfixAgent()
        task = Task(task_id="exc.2", task_type="bugfix")
        context = AgentContext(task=task, input_data={
            "error_message": {"nested": "dict"},  # 期望字符串，传入字典
        })
        result = agent.process(context)
        
        if result.success:
            logger.info("嵌套字典输入被接受")
        else:
            logger.info("嵌套字典输入正确拒绝")
            
    except Exception as e:
        record_bug("exception_2", "嵌套字典输入导致异常", e)
    
    return True


# ========== 场景8: 数据一致性测试 ==========

def test_data_consistency():
    """测试: 数据一致性."""
    print("\n[场景8] 数据一致性测试")
    logger.info("开始数据一致性测试")
    
    # 测试Agent历史记录一致性
    agent = DeveloperAgent()
    
    # 执行多次任务
    for i in range(3):
        task = Task(task_id=f"consistency.{i}", task_type="developer")
        context = AgentContext(task=task, input_data={
            "requirement": f"功能{i}",
            "task_type": "implementation",
        })
        agent.process(context)
    
    history = agent.get_development_history()
    stats = agent.get_statistics()
    
    if stats["total_tasks"] != len(history):
        record_bug("data_consistency", f"统计与历史不一致: stats={stats['total_tasks']}, history={len(history)}")
    else:
        logger.info(f"数据一致性验证通过: {stats['total_tasks']} 条记录")
    
    return True


# ========== 场景9: 边界阈值测试 ==========

def test_boundary_conditions():
    """测试: 边界条件."""
    print("\n[场景9] 边界条件测试")
    logger.info("开始边界条件测试")
    
    # 测试1: 空列表
    try:
        agent = ArchitectAgent()
        task = Task(task_id="boundary.1", task_type="architect")
        context = AgentContext(task=task, input_data={"requirements": []})
        result = agent.process(context)
        
        if result.success:
            record_warning("boundary_1", "空requirements列表被接受，可能产生无意义结果")
        else:
            logger.info("空requirements列表正确拒绝")
            
    except Exception as e:
        record_bug("boundary_1", "空列表导致异常", e)
    
    # 测试2: 极大数值
    try:
        agent = ControllerAgent()
        task = Task(task_id="boundary.2", task_type="controller")
        context = AgentContext(task=task, input_data={
            "requirement": "测试",
            "max_depth": 999999999,  # 极大值
        })
        result = agent.process(context)
        logger.info("极大数值测试完成")
        
    except Exception as e:
        record_bug("boundary_2", "极大数值导致异常", e)
    
    return True


# ========== 场景10: 跨模块集成测试 ==========

def test_cross_module_integration():
    """测试: 跨模块集成."""
    print("\n[场景10] 跨模块集成测试")
    logger.info("开始跨模块集成测试")
    
    # 测试消息总线 + Agent协作
    from multi_agent_se.agents.communication.bus import MessageBus
    
    bus = MessageBus()
    
    # 创建大量消息
    for i in range(100):
        msg = Message.create(
            sender_id="sender.001",
            receiver_id=f"receiver.{i % 5}",
            payload={"index": i, "data": "x" * 100},
            priority=MessagePriority.NORMAL,
        )
        bus.send(msg)
    
    stats = bus.get_stats()
    logger.info(f"消息总线: 发送{stats.total_sent}, 送达{stats.total_delivered}")
    
    if stats.total_sent != 100:
        record_warning("cross_module", f"消息发送数量不匹配: {stats.total_sent}")
    
    return True


def run_all_tests():
    """运行所有复杂场景测试."""
    print("=" * 70)
    print("第42阶段 - 复杂场景压力测试与Bug发现")
    print("=" * 70)
    
    tests = [
        ("空值与None输入", test_none_inputs),
        ("超长字符串压力", test_extremely_long_strings),
        ("特殊字符与注入", test_special_characters),
        ("循环依赖检测", test_circular_dependency_detection),
        ("大规模任务执行", test_massive_task_execution),
        ("并行任务执行", test_parallel_execution),
        ("异常传播与捕获", test_exception_handling),
        ("数据一致性", test_data_consistency),
        ("边界条件", test_boundary_conditions),
        ("跨模块集成", test_cross_module_integration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            record_bug(f"test_framework_{name}", "测试框架自身异常", e)
    
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    print(f"测试场景: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print(f"发现Bug: {len(BUGS_FOUND)}")
    print(f"发现警告: {len(WARNINGS)}")
    
    if BUGS_FOUND:
        print("\n--- Bug详情 ---")
        for i, bug in enumerate(BUGS_FOUND, 1):
            print(f"\n[{i}] {bug['test']}")
            print(f"    描述: {bug['desc']}")
            if 'exception' in bug:
                print(f"    异常: {bug['exception']}")
    
    if WARNINGS:
        print("\n--- 警告详情 ---")
        for i, w in enumerate(WARNINGS, 1):
            print(f"[{i}] {w['test']}: {w['desc']}")
    
    print("\n" + "=" * 70)
    
    if not BUGS_FOUND and not WARNINGS:
        print("🎉 所有测试通过，未发现Bug！")
    elif not BUGS_FOUND:
        print("⚠️  发现警告但无严重Bug，建议优化。")
    else:
        print(f"❌ 发现 {len(BUGS_FOUND)} 个Bug，需要修复。")
    
    return len(BUGS_FOUND) == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
