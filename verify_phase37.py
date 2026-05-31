"""第37阶段验收脚本 - Tester Agent验证.

验证测试Agent的完整功能：
- 枚举定义
- 数据模型
- 测试用例生成
- 测试执行
- 覆盖率分析
- 测试历史追踪
"""

import sys
import traceback
from typing import Any, Dict, List

sys.path.insert(0, "/workspace/multi_agent_se/src")

from multi_agent_se.agents.tester import (
    TesterAgent,
    TestType,
    TestStatus,
    AssertionType,
    TestAssertion,
    TestCase,
    CoverageData,
    TestResult,
)
from multi_agent_se.agents.runtime.base_agent import AgentContext
from multi_agent_se.scheduler.task import Task


def test_test_type_enum():
    """测试: TestType枚举."""
    print("\n[TEST] TestType枚举")
    
    assert TestType.UNIT.value == "unit"
    assert TestType.INTEGRATION.value == "integration"
    assert TestType.E2E.value == "e2e"
    assert TestType.REGRESSION.value == "regression"
    assert TestType.PERFORMANCE.value == "performance"
    assert TestType.SECURITY.value == "security"
    assert TestType.PROPERTY.value == "property"
    assert TestType.MUTATION.value == "mutation"
    
    print("  ✓ TestType枚举定义正确（8种测试类型）")
    return True


def test_test_status_enum():
    """测试: TestStatus枚举."""
    print("\n[TEST] TestStatus枚举")
    
    assert TestStatus.PENDING.value == "pending"
    assert TestStatus.RUNNING.value == "running"
    assert TestStatus.PASSED.value == "passed"
    assert TestStatus.FAILED.value == "failed"
    assert TestStatus.SKIPPED.value == "skipped"
    assert TestStatus.ERROR.value == "error"
    assert TestStatus.TIMEOUT.value == "timeout"
    
    print("  ✓ TestStatus枚举定义正确（7种状态）")
    return True


def test_assertion_type_enum():
    """测试: AssertionType枚举."""
    print("\n[TEST] AssertionType枚举")
    
    assert AssertionType.EQUAL.value == "equal"
    assert AssertionType.NOT_EQUAL.value == "not_equal"
    assert AssertionType.TRUE.value == "true"
    assert AssertionType.FALSE.value == "false"
    assert AssertionType.IS_NONE.value == "is_none"
    assert AssertionType.IS_NOT_NONE.value == "is_not_none"
    assert AssertionType.IN.value == "in"
    assert AssertionType.NOT_IN.value == "not_in"
    assert AssertionType.RAISES.value == "raises"
    assert AssertionType.ALMOST_EQUAL.value == "almost_equal"
    
    print("  ✓ AssertionType枚举定义正确（10种断言类型）")
    return True


def test_test_assertion():
    """测试: TestAssertion数据类."""
    print("\n[TEST] TestAssertion数据类")
    
    assertion = TestAssertion(
        assertion_type=AssertionType.EQUAL,
        description="验证返回值等于预期",
        expected_value=42,
        actual_value=42,
        passed=True,
    )
    
    assert assertion.assertion_type == AssertionType.EQUAL
    assert assertion.passed is True
    assert assertion.expected_value == 42
    
    data = assertion.to_dict()
    assert data["type"] == "equal"
    assert data["passed"] is True
    
    print("  ✓ TestAssertion数据类工作正常")
    return True


def test_test_case():
    """测试: TestCase数据类."""
    print("\n[TEST] TestCase数据类")
    
    assertions = [
        TestAssertion(assertion_type=AssertionType.IS_NOT_NONE, passed=True),
        TestAssertion(assertion_type=AssertionType.EQUAL, passed=True),
    ]
    
    test_case = TestCase(
        name="test_calculator_add",
        description="测试计算器加法功能",
        test_type=TestType.UNIT,
        target_class="Calculator",
        target_function="add",
        inputs={"a": 1, "b": 2},
        expected_output=3,
        assertions=assertions,
        status=TestStatus.PASSED,
        execution_time_ms=15.5,
        generated_code="def test_add(): assert add(1, 2) == 3",
    )
    
    assert test_case.name == "test_calculator_add"
    assert test_case.target_class == "Calculator"
    assert test_case.target_function == "add"
    assert len(test_case.assertions) == 2
    
    data = test_case.to_dict()
    assert data["name"] == "test_calculator_add"
    assert data["status"] == "passed"
    assert data["assertions_count"] == 2
    
    print("  ✓ TestCase数据类工作正常")
    return True


def test_coverage_data():
    """测试: CoverageData数据类."""
    print("\n[TEST] CoverageData数据类")
    
    coverage = CoverageData(
        total_lines=100,
        covered_lines=85,
        line_coverage_rate=0.85,
        total_branches=20,
        covered_branches=16,
        branch_coverage_rate=0.80,
        total_functions=10,
        covered_functions=9,
        function_coverage_rate=0.90,
        uncovered_lines=[15, 23, 45, 67, 89],
    )
    
    assert coverage.line_coverage_rate == 0.85
    assert coverage.branch_coverage_rate == 0.80
    assert len(coverage.uncovered_lines) == 5
    
    data = coverage.to_dict()
    assert "85/100 (85.0%)" in data["line_coverage"]
    assert "16/20 (80.0%)" in data["branch_coverage"]
    assert data["uncovered_lines_count"] == 5
    
    print("  ✓ CoverageData数据类工作正常")
    return True


def test_test_result():
    """测试: TestResult数据类."""
    print("\n[TEST] TestResult数据类")
    
    test_cases = [
        TestCase(name="test1", status=TestStatus.PASSED),
        TestCase(name="test2", status=TestStatus.PASSED),
        TestCase(name="test3", status=TestStatus.FAILED),
    ]
    
    result = TestResult(
        test_cases=test_cases,
        total_tests=3,
        passed_tests=2,
        failed_tests=1,
        success_rate=0.667,
        is_successful=False,
        summary="2/3 测试通过",
        coverage=CoverageData(line_coverage_rate=0.75),
    )
    
    assert result.total_tests == 3
    assert result.passed_tests == 2
    assert result.is_successful is False
    
    data = result.to_dict()
    assert data["total_tests"] == 3
    assert data["passed"] == 2
    assert "66.7%" in data["success_rate"]
    
    print("  ✓ TestResult数据类工作正常")
    return True


def test_agent_creation():
    """测试: TesterAgent创建."""
    print("\n[TEST] TesterAgent创建")
    
    from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
    
    agent = TesterAgent(agent_id="tester.001")
    
    assert agent.agent_id == "tester.001"
    assert agent.role == AgentRole.TESTER
    assert AgentCapability.CODE_TESTING in agent.capabilities
    assert AgentCapability.QUALITY_CHECK in agent.capabilities
    
    print(f"  ✓ TesterAgent创建成功: {agent.agent_id}")
    print(f"    - 角色: {agent.role.value}")
    print(f"    - 能力: {[c.value for c in agent.capabilities]}")
    return True


def test_code_parsing():
    """测试: 代码解析（类和函数提取）."""
    print("\n[TEST] 代码解析")
    
    agent = TesterAgent()
    
    code = '''
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def _private_method(self):
        pass

def helper_function():
    return "helper"

def another_function():
    return "another"
'''
    
    classes = agent._extract_classes(code)
    functions = agent._extract_functions(code)
    
    assert "Calculator" in classes
    assert "add" in classes["Calculator"]
    assert "subtract" in classes["Calculator"]
    assert "_private_method" not in classes["Calculator"]  # 私有方法被过滤
    
    assert "helper_function" in functions
    assert "another_function" in functions
    
    print(f"  ✓ 代码解析成功:")
    print(f"    - 提取到 {len(classes)} 个类")
    print(f"    - 提取到 {len(functions)} 个独立函数")
    return True


def test_test_case_generation():
    """测试: 测试用例生成."""
    print("\n[TEST] 测试用例生成")
    
    agent = TesterAgent()
    
    code = '''
class UserManager:
    def __init__(self):
        self.users = {}
    
    def add_user(self, name):
        self.users[name] = {"name": name}
        return self.users[name]
    
    def get_user(self, name):
        return self.users.get(name)

def process_data(data):
    return data.upper()
'''
    
    test_cases = agent._generate_test_cases(code, TestType.UNIT)
    
    assert len(test_cases) > 0
    
    # 检查是否生成了类方法的测试
    class_tests = [t for t in test_cases if t.target_class == "UserManager"]
    assert len(class_tests) >= 2  # __init__ 和 add_user, get_user
    
    # 检查是否生成了独立函数的测试
    func_tests = [t for t in test_cases if t.target_function == "process_data"]
    assert len(func_tests) >= 1
    
    print(f"  ✓ 生成 {len(test_cases)} 个测试用例:")
    for tc in test_cases[:3]:
        target = f"{tc.target_class}.{tc.target_function}" if tc.target_class else tc.target_function
        print(f"    - {tc.name} -> {target}")
    return True


def test_test_code_generation():
    """测试: 测试代码生成."""
    print("\n[TEST] 测试代码生成")
    
    agent = TesterAgent()
    
    # 测试类方法
    code_method = agent._generate_test_code("Calculator", "add", is_method=True)
    assert "Calculator" in code_method
    assert "add" in code_method
    assert "assert" in code_method
    
    # 测试独立函数
    code_func = agent._generate_test_code(None, "process", is_method=False)
    assert "process" in code_func
    assert "assert" in code_func
    
    print("  ✓ 测试代码生成成功")
    print(f"    方法测试代码长度: {len(code_method)} 字符")
    print(f"    函数测试代码长度: {len(code_func)} 字符")
    return True


def test_coverage_analysis():
    """测试: 覆盖率分析."""
    print("\n[TEST] 覆盖率分析")
    
    agent = TesterAgent()
    
    code = '''
def calculate(a, b):
    if a > 0:
        result = a + b
    else:
        result = a - b
    return result

def process(items):
    for item in items:
        if item:
            yield item.upper()
'''
    
    # 创建模拟测试结果
    test_cases = [
        TestCase(name="test1", status=TestStatus.PASSED),
        TestCase(name="test2", status=TestStatus.PASSED),
        TestCase(name="test3", status=TestStatus.FAILED),
    ]
    result = TestResult(test_cases=test_cases)
    
    coverage = agent._analyze_coverage(code, result)
    
    assert coverage.total_lines > 0
    assert coverage.covered_lines > 0
    assert coverage.line_coverage_rate > 0
    assert coverage.total_functions > 0
    assert coverage.total_branches > 0
    
    print(f"  ✓ 覆盖率分析:")
    print(f"    - 总行数: {coverage.total_lines}")
    print(f"    - 覆盖行数: {coverage.covered_lines}")
    print(f"    - 行覆盖率: {coverage.line_coverage_rate:.1%}")
    print(f"    - 函数覆盖率: {coverage.function_coverage_rate:.1%}")
    print(f"    - 分支覆盖率: {coverage.branch_coverage_rate:.1%}")
    return True


def test_agent_full_process():
    """测试: Agent完整处理流程."""
    print("\n[TEST] Agent完整处理流程")
    
    agent = TesterAgent(agent_id="tester.test")
    
    code = '''
class StringProcessor:
    def __init__(self):
        self.cache = {}
    
    def reverse(self, text):
        return text[::-1]
    
    def capitalize(self, text):
        return text.capitalize()

def helper():
    return "help"
'''
    
    task = Task(
        task_id="task.test.001",
        task_type="code_testing",
        description="生成并执行测试",
    )
    
    context = AgentContext(
        task=task,
        input_data={
            "code": code,
            "target_files": ["src/processor.py"],
            "test_type": "unit",
        },
    )
    
    result = agent.process(context)
    
    assert result.success is True
    assert result.output is not None
    assert "result_id" in result.output
    assert "total_tests" in result.output
    assert "passed" in result.output
    assert "success_rate" in result.output
    assert "coverage" in result.output
    assert "is_successful" in result.output
    
    print(f"  ✓ Agent处理成功:")
    print(f"    - 结果ID: {result.output['result_id']}")
    print(f"    - 总测试数: {result.output['total_tests']}")
    print(f"    - 通过数: {result.output['passed']}")
    print(f"    - 成功率: {result.output['success_rate']}")
    print(f"    - 是否成功: {result.output['is_successful']}")
    print(f"    - 覆盖率: {result.output['coverage']['line_coverage']}")
    return True


def test_test_history():
    """测试: 测试历史追踪."""
    print("\n[TEST] 测试历史追踪")
    
    agent = TesterAgent()
    
    # 执行多次测试
    for i in range(3):
        task = Task(task_id=f"task.test.{i}")
        context = AgentContext(
            task=task,
            input_data={
                "code": f"def func{i}(): return {i}",
                "test_type": "unit",
            },
        )
        agent.process(context)
    
    history = agent.get_test_history()
    stats = agent.get_statistics()
    
    assert len(history) == 3
    assert stats["total_runs"] == 3
    assert stats["total_tests_executed"] > 0
    
    print(f"  ✓ 历史追踪正常:")
    print(f"    - 总运行数: {stats['total_runs']}")
    print(f"    - 成功运行: {stats['successful_runs']}")
    print(f"    - 平均成功率: {stats['avg_success_rate']:.1%}")
    print(f"    - 平均覆盖率: {stats['avg_coverage']:.1%}")
    return True


def test_error_handling():
    """测试: 错误处理."""
    print("\n[TEST] 错误处理")
    
    agent = TesterAgent()
    
    task = Task(task_id="task.empty")
    context = AgentContext(
        task=task,
        input_data={},  # 空输入
    )
    
    result = agent.process(context)
    
    assert result.success is False
    assert "未提供测试用例" in result.error_message
    
    print(f"  ✓ 错误处理正确: {result.error_message}")
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第37阶段验收测试 - Tester Agent")
    print("=" * 60)
    
    tests = [
        ("TestType枚举", test_test_type_enum),
        ("TestStatus枚举", test_test_status_enum),
        ("AssertionType枚举", test_assertion_type_enum),
        ("TestAssertion数据类", test_test_assertion),
        ("TestCase数据类", test_test_case),
        ("CoverageData数据类", test_coverage_data),
        ("TestResult数据类", test_test_result),
        ("Agent创建", test_agent_creation),
        ("代码解析", test_code_parsing),
        ("测试用例生成", test_test_case_generation),
        ("测试代码生成", test_test_code_generation),
        ("覆盖率分析", test_coverage_analysis),
        ("Agent完整处理流程", test_agent_full_process),
        ("测试历史追踪", test_test_history),
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
        print("🎉 第37阶段验收通过！Tester Agent实现完成。")
    else:
        print("❌ 部分测试失败，请检查实现。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
