"""第35阶段验收脚本 - Bugfix Agent验证.

验证缺陷修复Agent的完整功能：
- 错误类型检测
- 堆栈跟踪解析
- 根因分析
- 修复建议生成
- 代码修复生成
- 修复历史追踪
"""

import sys
import traceback
from typing import Any, Dict, List

# 添加源码路径
sys.path.insert(0, "/workspace/multi_agent_se/src")

from multi_agent_se.agents.bugfix import (
    BugfixAgent,
    ErrorType,
    FixSeverity,
    ErrorLocation,
    BugReport,
    FixSuggestion,
    FixResult,
)
from multi_agent_se.agents.runtime.base_agent import AgentContext
from multi_agent_se.scheduler.task import Task


def test_error_type_enum():
    """测试: ErrorType枚举定义."""
    print("\n[TEST] ErrorType枚举定义")
    
    assert ErrorType.SYNTAX.value == "syntax"
    assert ErrorType.RUNTIME.value == "runtime"
    assert ErrorType.LOGIC.value == "logic"
    assert ErrorType.TYPE.value == "type"
    assert ErrorType.ATTRIBUTE.value == "attribute"
    assert ErrorType.INDEX.value == "index"
    assert ErrorType.KEY.value == "key"
    
    print("  ✓ ErrorType枚举定义正确")
    return True


def test_fix_severity_enum():
    """测试: FixSeverity枚举定义."""
    print("\n[TEST] FixSeverity枚举定义")
    
    assert FixSeverity.CRITICAL.value == "critical"
    assert FixSeverity.HIGH.value == "high"
    assert FixSeverity.MEDIUM.value == "medium"
    assert FixSeverity.LOW.value == "low"
    assert FixSeverity.TRIVIAL.value == "trivial"
    
    print("  ✓ FixSeverity枚举定义正确")
    return True


def test_error_location():
    """测试: ErrorLocation数据类."""
    print("\n[TEST] ErrorLocation数据类")
    
    location = ErrorLocation(
        file_path="/path/to/file.py",
        line_number=42,
        column_number=10,
        function_name="process_data",
        class_name="DataProcessor",
    )
    
    assert location.file_path == "/path/to/file.py"
    assert location.line_number == 42
    assert location.column_number == 10
    assert location.function_name == "process_data"
    assert location.class_name == "DataProcessor"
    
    # 测试to_dict
    data = location.to_dict()
    assert data["file_path"] == "/path/to/file.py"
    assert data["line_number"] == 42
    
    print("  ✓ ErrorLocation数据类工作正常")
    return True


def test_bug_report():
    """测试: BugReport数据类."""
    print("\n[TEST] BugReport数据类")
    
    location = ErrorLocation(
        file_path="src/module.py",
        line_number=25,
        function_name="calculate",
    )
    
    report = BugReport(
        error_type=ErrorType.TYPE,
        error_message="unsupported operand type(s) for +: 'int' and 'str'",
        stack_trace='File "src/module.py", line 25, in calculate',
        location=location,
        context_code="result = value + 'text'",
        related_files=["src/module.py", "tests/test_module.py"],
    )
    
    assert report.error_type == ErrorType.TYPE
    assert "unsupported operand" in report.error_message
    assert len(report.related_files) == 2
    
    # 测试to_dict
    data = report.to_dict()
    assert data["error_type"] == "type"
    assert "bug_id" in data
    
    print("  ✓ BugReport数据类工作正常")
    return True


def test_fix_suggestion():
    """测试: FixSuggestion数据类."""
    print("\n[TEST] FixSuggestion数据类")
    
    suggestion = FixSuggestion(
        description="添加类型检查",
        severity=FixSeverity.HIGH,
        confidence=0.85,
        file_path="src/module.py",
        original_code="result = a + b",
        fixed_code="result = int(a) + int(b)",
        line_start=25,
        line_end=25,
        explanation="确保操作数类型一致",
    )
    
    assert suggestion.severity == FixSeverity.HIGH
    assert suggestion.confidence == 0.85
    assert suggestion.line_start == 25
    
    # 测试to_dict
    data = suggestion.to_dict()
    assert data["severity"] == "high"
    assert data["confidence"] == 0.85
    
    print("  ✓ FixSuggestion数据类工作正常")
    return True


def test_fix_result():
    """测试: FixResult数据类."""
    print("\n[TEST] FixResult数据类")
    
    report = BugReport(error_type=ErrorType.ATTRIBUTE)
    suggestion = FixSuggestion(description="Test fix")
    
    result = FixResult(
        bug_report=report,
        root_cause="属性访问错误",
        suggestions=[suggestion],
        total_suggestions=1,
        verified=True,
        verification_method="单元测试",
    )
    
    assert result.root_cause == "属性访问错误"
    assert result.verified is True
    assert len(result.suggestions) == 1
    
    # 测试to_dict
    data = result.to_dict()
    assert data["verified"] is True
    assert data["total_suggestions"] == 1
    
    print("  ✓ FixResult数据类工作正常")
    return True


def test_agent_creation():
    """测试: BugfixAgent创建."""
    print("\n[TEST] BugfixAgent创建")
    
    from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
    
    agent = BugfixAgent(agent_id="bugfix.001")
    
    assert agent.agent_id == "bugfix.001"
    assert agent.role == AgentRole.BUGFIX
    assert AgentCapability.CODE_DEBUGGING in agent.capabilities
    assert AgentCapability.CODE_GENERATION in agent.capabilities
    
    print(f"  ✓ BugfixAgent创建成功: {agent.agent_id}")
    print(f"    - 角色: {agent.role.value}")
    print(f"    - 能力: {[c.value for c in agent.capabilities]}")
    return True


def test_error_type_detection():
    """测试: 错误类型检测."""
    print("\n[TEST] 错误类型检测")
    
    agent = BugfixAgent()
    
    # 测试各种错误类型
    test_cases = [
        ("TypeError: unsupported operand", "", ErrorType.TYPE),
        ("AttributeError: 'NoneType' has no attribute", "", ErrorType.ATTRIBUTE),
        ("IndexError: list index out of range", "", ErrorType.INDEX),
        ("KeyError: 'missing_key'", "", ErrorType.KEY),
        ("ImportError: No module named", "", ErrorType.IMPORT),
        ("SyntaxError: invalid syntax", "", ErrorType.SYNTAX),
        ("ValueError: invalid literal", "", ErrorType.VALUE),
    ]
    
    for error_msg, stack, expected_type in test_cases:
        detected = agent._detect_error_type(error_msg, stack)
        assert detected == expected_type, f"期望 {expected_type}, 得到 {detected}"
    
    print(f"  ✓ 成功识别 {len(test_cases)} 种错误类型")
    return True


def test_stack_trace_parsing():
    """测试: 堆栈跟踪解析."""
    print("\n[TEST] 堆栈跟踪解析")
    
    agent = BugfixAgent()
    
    stack_trace = '''Traceback (most recent call last):
  File "/app/main.py", line 45, in process_request
    result = handler.handle(data)
  File "/app/handlers.py", line 23, in handle
    return self.process(data)
  File "/app/handlers.py", line 89, in process
    value = items[index]
IndexError: list index out of range'''
    
    location = agent._parse_error_location(stack_trace)
    
    assert location.file_path == "/app/handlers.py"
    assert location.line_number == 89
    assert location.function_name == "process"
    
    print(f"  ✓ 堆栈解析正确:")
    print(f"    - 文件: {location.file_path}")
    print(f"    - 行号: {location.line_number}")
    print(f"    - 函数: {location.function_name}")
    return True


def test_root_cause_analysis():
    """测试: 根因分析."""
    print("\n[TEST] 根因分析")
    
    agent = BugfixAgent()
    
    report = BugReport(
        error_type=ErrorType.INDEX,
        error_message="list index out of range",
    )
    
    root_cause = agent._analyze_root_cause(report)
    
    assert "索引越界" in root_cause
    assert "list index out of range" in root_cause
    
    print(f"  ✓ 根因分析: {root_cause[:50]}...")
    return True


def test_fix_suggestion_generation():
    """测试: 修复建议生成."""
    print("\n[TEST] 修复建议生成")
    
    agent = BugfixAgent()
    
    report = BugReport(
        error_type=ErrorType.KEY,
        error_message="KeyError: 'user_id'",
        location=ErrorLocation(file_path="src/auth.py", line_number=15),
    )
    
    root_cause = "字典中缺少指定的键"
    suggestions = agent._generate_fix_suggestions(report, root_cause)
    
    assert len(suggestions) >= 1
    assert any("dict.get()" in s.description or "get方法" in s.description for s in suggestions)
    
    print(f"  ✓ 生成 {len(suggestions)} 个修复建议")
    for s in suggestions[:2]:
        print(f"    - {s.description} (置信度: {s.confidence})")
    return True


def test_code_fix_generation():
    """测试: 代码修复生成."""
    print("\n[TEST] 代码修复生成")
    
    agent = BugfixAgent()
    
    # 测试KeyError修复
    report = BugReport(
        error_type=ErrorType.KEY,
        error_message="KeyError: 'name'",
        context_code="user_name = user['name']",
        location=ErrorLocation(file_path="src/users.py", line_number=10),
    )
    
    fix = agent._generate_code_fix(report, "键不存在")
    
    assert fix is not None
    assert "get" in fix.fixed_code.lower()
    assert fix.original_code == "user_name = user['name']"
    
    print(f"  ✓ 代码修复生成成功:")
    print(f"    原代码: {fix.original_code[:40]}...")
    print(f"    修复后: {fix.fixed_code[:40]}...")
    return True


def test_agent_process():
    """测试: Agent完整处理流程."""
    print("\n[TEST] Agent完整处理流程")
    
    agent = BugfixAgent(agent_id="bugfix.test")
    
    # 创建任务上下文
    task = Task(
        task_id="task.fix.001",
        task_type="bugfix",
        description="修复类型错误",
    )
    
    context = AgentContext(
        task=task,
        input_data={
            "error_message": "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
            "stack_trace": '''File "app.py", line 42, in calculate
    result = count + name''',
            "context_code": "result = count + name",
            "affected_files": ["app.py"],
        },
    )
    
    # 执行Agent
    result = agent.process(context)
    
    assert result.success is True
    assert result.output is not None
    assert "bug_id" in result.output
    assert "root_cause" in result.output
    assert "total_suggestions" in result.output
    
    print(f"  ✓ Agent处理成功:")
    print(f"    - Bug ID: {result.output['bug_id']}")
    print(f"    - 根因: {result.output['root_cause'][:40]}...")
    print(f"    - 建议数: {result.output['total_suggestions']}")
    print(f"    - 已验证: {result.output['verified']}")
    return True


def test_fix_history():
    """测试: 修复历史追踪."""
    print("\n[TEST] 修复历史追踪")
    
    agent = BugfixAgent()
    
    # 执行多次修复
    for i in range(3):
        task = Task(task_id=f"task.fix.{i}")
        context = AgentContext(
            task=task,
            input_data={
                "error_message": f"Error {i}",
                "error_type": "runtime",
            },
        )
        agent.process(context)
    
    history = agent.get_fix_history()
    stats = agent.get_statistics()
    
    assert len(history) == 3
    assert stats["total_fixes"] == 3
    assert stats["verification_rate"] >= 0
    
    print(f"  ✓ 历史追踪正常:")
    print(f"    - 总修复数: {stats['total_fixes']}")
    print(f"    - 验证率: {stats['verification_rate']:.1%}")
    print(f"    - 平均建议数: {stats['avg_suggestions_per_fix']:.1f}")
    return True


def test_error_handling():
    """测试: 错误处理."""
    print("\n[TEST] 错误处理")
    
    agent = BugfixAgent()
    
    # 测试缺少错误信息
    task = Task(task_id="task.empty")
    context = AgentContext(
        task=task,
        input_data={},  # 空输入
    )
    
    result = agent.process(context)
    
    assert result.success is False
    assert "缺少错误信息" in result.error_message
    
    print(f"  ✓ 错误处理正确: {result.error_message}")
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第35阶段验收测试 - Bugfix Agent")
    print("=" * 60)
    
    tests = [
        ("ErrorType枚举", test_error_type_enum),
        ("FixSeverity枚举", test_fix_severity_enum),
        ("ErrorLocation数据类", test_error_location),
        ("BugReport数据类", test_bug_report),
        ("FixSuggestion数据类", test_fix_suggestion),
        ("FixResult数据类", test_fix_result),
        ("Agent创建", test_agent_creation),
        ("错误类型检测", test_error_type_detection),
        ("堆栈跟踪解析", test_stack_trace_parsing),
        ("根因分析", test_root_cause_analysis),
        ("修复建议生成", test_fix_suggestion_generation),
        ("代码修复生成", test_code_fix_generation),
        ("Agent处理流程", test_agent_process),
        ("修复历史追踪", test_fix_history),
        ("错误处理", test_error_handling),
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
        print("🎉 第35阶段验收通过！Bugfix Agent实现完成。")
    else:
        print("❌ 部分测试失败，请检查实现。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
