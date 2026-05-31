"""测试运行器 - 阶段23.

提供统一的测试执行接口：
- TestRunner: Pytest集成测试运行器
- TestCaseResult: 单用例结果
- TestSessionResult: 测试会话结果
- CoverageData: 覆盖率数据
"""

from multi_agent_se.quality.coverage.test_result import (
    TestStatus,
    TestCaseResult,
    TestSessionResult,
    CoverageData,
    create_test_result,
)

from multi_agent_se.quality.coverage.test_runner import (
    TestRunner,
    run_tests,
    run_tests_with_coverage,
)

__all__ = [
    # 结果定义
    "TestStatus",
    "TestCaseResult",
    "TestSessionResult",
    "CoverageData",
    "create_test_result",
    # 运行器
    "TestRunner",
    "run_tests",
    "run_tests_with_coverage",
]
