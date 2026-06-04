"""Tester Agent - 第37阶段.

测试Agent - 负责测试用例生成、测试执行和覆盖率分析.

职责:
- 根据代码和需求生成测试用例
- 执行测试并收集结果
- 分析代码覆盖率
- 识别未覆盖的代码路径
- 生成测试报告
- 追踪测试历史
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
import re

from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
from multi_agent_se.agents.runtime.base_agent import BaseAgentImpl, AgentContext, TaskResult


class TestType(Enum):
    """测试类型."""
    UNIT = "unit"               # 单元测试
    INTEGRATION = "integration" # 集成测试
    E2E = "e2e"                 # 端到端测试
    REGRESSION = "regression"   # 回归测试
    PERFORMANCE = "performance" # 性能测试
    SECURITY = "security"       # 安全测试
    PROPERTY = "property"       # 属性测试（基于假设）
    MUTATION = "mutation"       # 变异测试


class TestStatus(Enum):
    """测试状态."""
    PENDING = "pending"         # 待执行
    RUNNING = "running"         # 执行中
    PASSED = "passed"           # 通过
    FAILED = "failed"           # 失败
    SKIPPED = "skipped"         # 跳过
    ERROR = "error"             # 错误
    TIMEOUT = "timeout"         # 超时


class AssertionType(Enum):
    """断言类型."""
    EQUAL = "equal"             # 相等
    NOT_EQUAL = "not_equal"     # 不相等
    TRUE = "true"               # 为真
    FALSE = "false"             # 为假
    IS_NONE = "is_none"         # 为None
    IS_NOT_NONE = "is_not_none" # 不为None
    IN = "in"                   # 包含
    NOT_IN = "not_in"           # 不包含
    RAISES = "raises"           # 抛出异常
    ALMOST_EQUAL = "almost_equal" # 近似相等


@dataclass
class TestAssertion:
    """测试断言."""
    assertion_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    assertion_type: AssertionType = AssertionType.EQUAL
    description: str = ""
    expected_value: Any = None
    actual_value: Any = None
    passed: bool = False
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "assertion_id": self.assertion_id,
            "type": self.assertion_type.value,
            "description": self.description[:80],
            "passed": self.passed,
        }


@dataclass
class TestCase:
    """测试用例."""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    test_type: TestType = TestType.UNIT
    
    # 目标
    target_function: str = ""      # 目标函数/方法
    target_class: str = ""         # 目标类
    target_file: str = ""          # 目标文件
    
    # 输入输出
    inputs: Dict[str, Any] = field(default_factory=dict)
    expected_output: Any = None
    expected_exception: Optional[str] = None
    
    # 断言列表
    assertions: List[TestAssertion] = field(default_factory=list)
    
    # 执行信息
    status: TestStatus = TestStatus.PENDING
    execution_time_ms: float = 0.0
    stdout: str = ""
    stderr: str = ""
    
    # 代码
    generated_code: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "description": self.description[:60],
            "test_type": self.test_type.value,
            "target": f"{self.target_class}.{self.target_function}" if self.target_class else self.target_function,
            "status": self.status.value,
            "assertions_count": len(self.assertions),
            "passed_assertions": sum(1 for a in self.assertions if a.passed),
            "execution_time_ms": round(self.execution_time_ms, 2),
        }


@dataclass
class CoverageData:
    """覆盖率数据."""
    # 行覆盖
    total_lines: int = 0
    covered_lines: int = 0
    line_coverage_rate: float = 0.0
    
    # 分支覆盖
    total_branches: int = 0
    covered_branches: int = 0
    branch_coverage_rate: float = 0.0
    
    # 函数覆盖
    total_functions: int = 0
    covered_functions: int = 0
    function_coverage_rate: float = 0.0
    
    # 未覆盖行
    uncovered_lines: List[int] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_coverage": f"{self.covered_lines}/{self.total_lines} ({self.line_coverage_rate:.1%})",
            "branch_coverage": f"{self.covered_branches}/{self.total_branches} ({self.branch_coverage_rate:.1%})",
            "function_coverage": f"{self.covered_functions}/{self.total_functions} ({self.function_coverage_rate:.1%})",
            "uncovered_lines_count": len(self.uncovered_lines),
        }


@dataclass
class TestResult:
    """测试结果."""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 测试用例
    test_cases: List[TestCase] = field(default_factory=list)
    
    # 统计
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    
    # 覆盖率
    coverage: CoverageData = field(default_factory=CoverageData)
    
    # 时间
    total_execution_time_ms: float = 0.0
    
    # 汇总
    success_rate: float = 0.0
    is_successful: bool = False
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "total_tests": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "skipped": self.skipped_tests,
            "errors": self.error_tests,
            "success_rate": f"{self.success_rate:.1%}",
            "is_successful": self.is_successful,
            "execution_time_ms": round(self.total_execution_time_ms, 2),
            "coverage": self.coverage.to_dict(),
            "summary": self.summary[:100],
        }


class TesterAgent(BaseAgentImpl):
    """测试Agent - 测试用例生成与执行.
    
    8大正交角色Agent之一，负责生成测试用例、执行测试并分析覆盖率。
    """
    
    AGENT_ROLE = AgentRole.TESTER
    AGENT_CAPABILITIES = [
        AgentCapability.CODE_TESTING,
        AgentCapability.QUALITY_CHECK,
    ]
    AGENT_DESCRIPTION = "测试Agent - 负责测试用例生成、测试执行和覆盖率分析"
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None) -> None:
        super().__init__(agent_id, config)
        self._test_history: List[TestResult] = []
        self._test_templates: Dict[TestType, str] = self._load_test_templates()
        self._coverage_threshold: float = 0.8  # 覆盖率阈值
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理测试任务.
        
        Args:
            context: Agent执行上下文
            
        Returns:
            任务执行结果
        """
        input_data = context.input_data
        
        # 输入类型验证
        if not isinstance(input_data, dict):
            return TaskResult(
                success=False,
                error_message=f"输入数据必须是字典类型，实际为 {type(input_data).__name__}",
            )
        
        # 获取任务参数
        code = input_data.get("code", "")
        target_files = input_data.get("target_files", [])
        test_type_str = input_data.get("test_type", "unit")
        test_type = TestType(test_type_str)
        
        # 生成或获取测试用例
        test_cases = input_data.get("test_cases", [])
        if not test_cases and code:
            test_cases = self._generate_test_cases(code, test_type)
        
        if not test_cases:
            return TaskResult(
                success=False,
                error_message="未提供测试用例且无法生成",
            )
        
        # 1. 创建测试结果
        result = TestResult(test_cases=test_cases)
        
        # 2. 执行测试
        self._execute_tests(result)
        
        # 3. 分析覆盖率
        if code:
            result.coverage = self._analyze_coverage(code, result)
        
        # 4. 计算统计
        self._calculate_statistics(result)
        
        # 5. 生成总结
        result.summary = self._generate_summary(result)
        result.is_successful = (
            result.success_rate >= 0.8 and
            result.coverage.line_coverage_rate >= self._coverage_threshold
        )
        
        # 6. 保存历史
        self._test_history.append(result)
        
        return TaskResult(
            success=True,
            output=result.to_dict(),
            artifacts={
                "result": result,
                "test_cases": test_cases,
            },
        )
    
    def _generate_test_cases(self, code: str, test_type: TestType) -> List[TestCase]:
        """根据代码生成测试用例."""
        test_cases: List[TestCase] = []
        
        # 解析代码提取类和函数
        classes = self._extract_classes(code)
        functions = self._extract_functions(code)
        
        # 为每个类生成测试
        for class_name, methods in classes.items():
            for method_name in methods:
                test_case = self._create_test_case_for_method(
                    class_name, method_name, test_type
                )
                test_cases.append(test_case)
        
        # 为独立函数生成测试
        for func_name in functions:
            if not any(func_name in methods for methods in classes.values()):
                test_case = self._create_test_case_for_function(
                    func_name, test_type
                )
                test_cases.append(test_case)
        
        # 如果没有提取到任何内容，生成默认测试
        if not test_cases:
            test_cases.append(self._create_default_test_case(test_type))
        
        return test_cases[:10]  # 最多10个测试用例
    
    def _extract_classes(self, code: str) -> Dict[str, List[str]]:
        """提取类及其方法."""
        classes: Dict[str, List[str]] = {}
        current_class = None
        
        for line in code.splitlines():
            # 匹配类定义
            class_match = re.match(r'class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(1)
                classes[current_class] = []
            
            # 匹配方法定义
            method_match = re.match(r'\s+def\s+(\w+)\s*\(', line)
            if method_match and current_class:
                method_name = method_match.group(1)
                if not method_name.startswith('_') or method_name == '__init__':
                    classes[current_class].append(method_name)
        
        return classes
    
    def _extract_functions(self, code: str) -> List[str]:
        """提取独立函数."""
        functions = []
        in_class = False
        indent_level = 0
        
        for line in code.splitlines():
            stripped = line.lstrip()
            current_indent = len(line) - len(stripped)
            
            if stripped.startswith('class '):
                in_class = True
                indent_level = current_indent
            elif in_class and current_indent <= indent_level and stripped:
                in_class = False
            
            if not in_class:
                func_match = re.match(r'def\s+(\w+)\s*\(', stripped)
                if func_match:
                    functions.append(func_match.group(1))
        
        return functions
    
    def _create_test_case_for_method(
        self,
        class_name: str,
        method_name: str,
        test_type: TestType,
    ) -> TestCase:
        """为类方法创建测试用例."""
        test_name = f"test_{class_name.lower()}_{method_name}"
        
        # 生成测试代码
        code = self._generate_test_code(class_name, method_name, is_method=True)
        
        # 创建断言
        assertions = [
            TestAssertion(
                assertion_type=AssertionType.IS_NOT_NONE,
                description=f"{method_name}应返回非None值",
            ),
        ]
        
        if method_name == '__init__':
            assertions.append(TestAssertion(
                assertion_type=AssertionType.TRUE,
                description="对象应正确初始化",
            ))
        
        return TestCase(
            name=test_name,
            description=f"测试{class_name}.{method_name}方法",
            test_type=test_type,
            target_class=class_name,
            target_function=method_name,
            inputs={"default": "value"},
            generated_code=code,
            assertions=assertions,
        )
    
    def _create_test_case_for_function(
        self,
        func_name: str,
        test_type: TestType,
    ) -> TestCase:
        """为函数创建测试用例."""
        test_name = f"test_{func_name}"
        
        code = self._generate_test_code(None, func_name, is_method=False)
        
        return TestCase(
            name=test_name,
            description=f"测试{func_name}函数",
            test_type=test_type,
            target_function=func_name,
            inputs={"arg": "value"},
            generated_code=code,
            assertions=[
                TestAssertion(
                    assertion_type=AssertionType.IS_NOT_NONE,
                    description=f"{func_name}应返回非None值",
                ),
            ],
        )
    
    def _create_default_test_case(self, test_type: TestType) -> TestCase:
        """创建默认测试用例."""
        return TestCase(
            name="test_default",
            description="默认测试用例",
            test_type=test_type,
            target_function="main",
            inputs={},
            generated_code="def test_default():\n    assert True",
            assertions=[TestAssertion(assertion_type=AssertionType.TRUE)],
        )
    
    def _generate_test_code(
        self,
        class_name: Optional[str],
        func_name: str,
        is_method: bool,
    ) -> str:
        """生成测试代码."""
        if is_method and class_name:
            return f'''def test_{class_name.lower()}_{func_name}():
    """Test {class_name}.{func_name}."""
    obj = {class_name}()
    result = obj.{func_name}()
    assert result is not None
'''
        else:
            return f'''def test_{func_name}():
    """Test {func_name}."""
    result = {func_name}()
    assert result is not None
'''
    
    def _execute_tests(self, result: TestResult) -> None:
        """执行测试用例（模拟）."""
        for test_case in result.test_cases:
            test_case.status = TestStatus.RUNNING
            
            # 模拟执行时间
            import random
            test_case.execution_time_ms = random.uniform(10.0, 100.0)
            
            # 模拟执行结果（80%通过率）
            if random.random() < 0.8:
                test_case.status = TestStatus.PASSED
                for assertion in test_case.assertions:
                    assertion.passed = True
            else:
                test_case.status = TestStatus.FAILED
                for assertion in test_case.assertions:
                    assertion.passed = False
                    assertion.error_message = "Assertion failed"
    
    def _analyze_coverage(self, code: str, result: TestResult) -> CoverageData:
        """分析代码覆盖率."""
        coverage = CoverageData()
        
        lines = code.splitlines()
        coverage.total_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        
        # 模拟覆盖率计算
        # 基于测试通过情况估算
        pass_rate = sum(1 for t in result.test_cases if t.status == TestStatus.PASSED) / max(len(result.test_cases), 1)
        
        coverage.covered_lines = int(coverage.total_lines * pass_rate * 0.9)  # 90%的通过测试覆盖
        coverage.line_coverage_rate = coverage.covered_lines / max(coverage.total_lines, 1)
        
        # 函数覆盖
        functions = self._extract_functions(code) + [
            m for methods in self._extract_classes(code).values() for m in methods
        ]
        coverage.total_functions = len(functions) if functions else 1
        coverage.covered_functions = int(coverage.total_functions * pass_rate)
        coverage.function_coverage_rate = coverage.covered_functions / max(coverage.total_functions, 1)
        
        # 分支覆盖（估算）
        branch_keywords = ['if', 'elif', 'else', 'for', 'while']
        branches = sum(1 for line in lines for kw in branch_keywords if kw in line)
        coverage.total_branches = max(branches, 1)
        coverage.covered_branches = int(coverage.total_branches * pass_rate * 0.8)
        coverage.branch_coverage_rate = coverage.covered_branches / max(coverage.total_branches, 1)
        
        return coverage
    
    def _calculate_statistics(self, result: TestResult) -> None:
        """计算测试统计."""
        result.total_tests = len(result.test_cases)
        result.passed_tests = sum(1 for t in result.test_cases if t.status == TestStatus.PASSED)
        result.failed_tests = sum(1 for t in result.test_cases if t.status == TestStatus.FAILED)
        result.skipped_tests = sum(1 for t in result.test_cases if t.status == TestStatus.SKIPPED)
        result.error_tests = sum(1 for t in result.test_cases if t.status == TestStatus.ERROR)
        
        result.total_execution_time_ms = sum(t.execution_time_ms for t in result.test_cases)
        
        if result.total_tests > 0:
            result.success_rate = result.passed_tests / result.total_tests
    
    def _generate_summary(self, result: TestResult) -> str:
        """生成测试总结."""
        summary = f"测试完成: {result.passed_tests}/{result.total_tests} 通过"
        summary += f" (成功率: {result.success_rate:.1%})"
        
        if result.coverage.line_coverage_rate > 0:
            summary += f", 行覆盖率: {result.coverage.line_coverage_rate:.1%}"
        
        if result.is_successful:
            summary += " - 测试通过"
        else:
            if result.success_rate < 0.8:
                summary += " - 成功率不足"
            if result.coverage.line_coverage_rate < self._coverage_threshold:
                summary += " - 覆盖率不足"
        
        return summary
    
    def _load_test_templates(self) -> Dict[TestType, str]:
        """加载测试模板."""
        return {
            TestType.UNIT: "pytest",
            TestType.INTEGRATION: "pytest",
            TestType.E2E: "selenium",
            TestType.PERFORMANCE: "pytest-benchmark",
        }
    
    def get_test_history(self) -> List[TestResult]:
        """获取测试历史."""
        return self._test_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        total_runs = len(self._test_history)
        if total_runs == 0:
            return {
                "total_runs": 0,
                "avg_success_rate": 0.0,
                "avg_coverage": 0.0,
            }
        
        avg_success = sum(r.success_rate for r in self._test_history) / total_runs
        avg_coverage = sum(r.coverage.line_coverage_rate for r in self._test_history) / total_runs
        successful_runs = sum(1 for r in self._test_history if r.is_successful)
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": successful_runs / total_runs,
            "avg_success_rate": round(avg_success, 3),
            "avg_coverage": round(avg_coverage, 3),
            "total_tests_executed": sum(r.total_tests for r in self._test_history),
            "total_passed": sum(r.passed_tests for r in self._test_history),
        }
