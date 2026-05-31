"""测试结果封装 - 阶段23.

定义测试运行的结果封装：
- 测试状态枚举
- 单用例结果
- 测试会话结果
- 覆盖率数据
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TestStatus(Enum):
    """测试状态."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    XFAILED = "xfailed"      # 预期失败
    XPASSED = "xpassed"      # 预期失败但通过
    UNKNOWN = "unknown"


@dataclass
class TestCaseResult:
    """单个测试用例结果."""
    nodeid: str = ""                    # pytest节点ID
    name: str = ""                      # 测试名
    status: TestStatus = TestStatus.UNKNOWN
    duration: float = 0.0               # 执行时间(秒)
    message: str = ""                   # 失败/跳过消息
    traceback: str = ""                 # 错误堆栈
    markers: List[str] = field(default_factory=list)
    file_path: str = ""                 # 所在文件
    line_number: int = 0                # 所在行号

    # ---- 便捷属性 ----

    @property
    def is_passed(self) -> bool:
        return self.status == TestStatus.PASSED

    @property
    def is_failed(self) -> bool:
        return self.status == TestStatus.FAILED

    @property
    def is_skipped(self) -> bool:
        return self.status == TestStatus.SKIPPED

    @property
    def is_error(self) -> bool:
        return self.status == TestStatus.ERROR

    @property
    def is_unexpected(self) -> bool:
        """是否有意外结果（失败或错误）."""
        return self.status in (TestStatus.FAILED, TestStatus.ERROR)

    # ---- 序列化 ----

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodeid": self.nodeid,
            "name": self.name,
            "status": self.status.value,
            "duration": round(self.duration, 4),
            "message": self.message[:500] if self.message else "",
            "markers": self.markers,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }

    @classmethod
    def from_status_line(cls, line: str) -> Optional["TestCaseResult"]:
        """从pytest输出行解析.

        解析格式: "tests/test_foo.py::test_bar PASSED"
        """
        status_map = {
            "PASSED": TestStatus.PASSED,
            "FAILED": TestStatus.FAILED,
            "SKIPPED": TestStatus.SKIPPED,
            "ERROR": TestStatus.ERROR,
            "XFAILED": TestStatus.XFAILED,
            "XPASSED": TestStatus.XPASSED,
        }

        outcome = None
        for label, st in status_map.items():
            if f" {label}" in line:
                outcome = st
                nodeid = line[:line.index(f" {label}")].strip()
                break

        if outcome is None:
            return None

        # 去掉末尾 [N%]
        if nodeid.endswith("]"):
            bracket_idx = nodeid.rfind("[")
            if bracket_idx != -1:
                nodeid = nodeid[:bracket_idx].strip()

        name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
        file_path = nodeid.split("::")[0] if "::" in nodeid else nodeid

        return cls(
            nodeid=nodeid,
            name=name,
            status=outcome,
            file_path=file_path,
        )


@dataclass
class TestSessionResult:
    """测试会话结果."""
    test_cases: List[TestCaseResult] = field(default_factory=list)
    duration: float = 0.0
    exit_code: int = 0
    root_dir: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None

    # ---- 统计属性 ----

    @property
    def total(self) -> int:
        return len(self.test_cases)

    @property
    def passed(self) -> int:
        return sum(1 for t in self.test_cases if t.is_passed)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.test_cases if t.is_failed)

    @property
    def skipped(self) -> int:
        return sum(1 for t in self.test_cases if t.is_skipped)

    @property
    def errors(self) -> int:
        return sum(1 for t in self.test_cases if t.is_error)

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total * 100.0

    @property
    def all_passed(self) -> bool:
        return self.failed == 0 and self.errors == 0

    @property
    def has_failures(self) -> bool:
        return self.failed > 0 or self.errors > 0

    @property
    def total_duration(self) -> float:
        """所有用例执行时间之和."""
        return sum(t.duration for t in self.test_cases)

    # ---- 筛选方法 ----

    def get_failures(self) -> List[TestCaseResult]:
        return [t for t in self.test_cases if t.is_failed]

    def get_errors(self) -> List[TestCaseResult]:
        return [t for t in self.test_cases if t.is_error]

    def get_skipped(self) -> List[TestCaseResult]:
        return [t for t in self.test_cases if t.is_skipped]

    def get_passed(self) -> List[TestCaseResult]:
        return [t for t in self.test_cases if t.is_passed]

    def get_slowest(self, n: int = 5) -> List[TestCaseResult]:
        """获取最慢的N个测试."""
        return sorted(self.test_cases, key=lambda t: t.duration, reverse=True)[:n]

    # ---- 序列化 ----

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "pass_rate": round(self.pass_rate, 2),
            "duration": round(self.duration, 3),
            "total_duration": round(self.total_duration, 3),
            "exit_code": self.exit_code,
            "all_passed": self.all_passed,
            "root_dir": self.root_dir,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "test_cases": [t.to_dict() for t in self.test_cases],
        }

    def format_summary(self) -> str:
        """格式化摘要."""
        parts = [
            f"Tests: {self.total}",
            f"Passed: {self.passed}",
            f"Failed: {self.failed}",
            f"Errors: {self.errors}",
            f"Skipped: {self.skipped}",
            f"Pass Rate: {self.pass_rate:.1f}%",
            f"Duration: {self.duration:.3f}s",
        ]
        status = "ALL PASSED" if self.all_passed else "HAS FAILURES"
        parts.append(f"Status: {status}")
        return " | ".join(parts)


@dataclass
class CoverageData:
    """覆盖率数据."""
    total_coverage: float = 0.0
    covered_lines: int = 0
    total_lines: int = 0
    missing_lines: int = 0
    file_coverages: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def is_sufficient(self, threshold: float = 80.0) -> bool:
        """覆盖率是否达标."""
        return self.total_coverage >= threshold

    @property
    def coverage_gap(self) -> int:
        return self.total_lines - self.covered_lines

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_coverage": round(self.total_coverage, 2),
            "covered_lines": self.covered_lines,
            "total_lines": self.total_lines,
            "missing_lines": self.missing_lines,
            "coverage_gap": self.coverage_gap,
            "file_coverages": self.file_coverages,
        }

    def format_summary(self) -> str:
        return (
            f"Coverage: {self.total_coverage:.1f}% "
            f"({self.covered_lines}/{self.total_lines} lines)"
        )


# ========== 便捷函数 ==========

def create_test_result(
    nodeid: str,
    status: TestStatus = TestStatus.PASSED,
    duration: float = 0.0,
    message: str = "",
) -> TestCaseResult:
    """创建测试结果的便捷函数."""
    name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
    return TestCaseResult(
        nodeid=nodeid,
        name=name,
        status=status,
        duration=duration,
        message=message,
    )
