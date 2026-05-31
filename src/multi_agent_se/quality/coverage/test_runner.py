"""Pytest测试运行器 - 阶段23.

复用Pytest开源内核，提供统一测试执行接口：
- 运行测试/单文件/按标记/按关键词
- 覆盖率收集
- 测试发现
- 结果解析
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from multi_agent_se.quality.coverage.test_result import (
    CoverageData,
    TestCaseResult,
    TestSessionResult,
    TestStatus,
    create_test_result,
)


class TestRunner:
    """Pytest测试运行器.

    封装Pytest CLI，提供Python接口
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        config_path: Optional[str] = None,
    ) -> None:
        self._project_root = project_root
        self._config_path = config_path

    # ========== 环境构建 ==========

    def _build_env(self) -> Dict[str, str]:
        """构建子进程环境变量."""
        env = os.environ.copy()
        if self._project_root:
            src_path = str(Path(self._project_root) / "src")
            existing = env.get("PYTHONPATH", "")
            if src_path not in existing:
                env["PYTHONPATH"] = f"{src_path}:{existing}" if existing else src_path
        return env

    def _build_args(
        self,
        paths: Optional[List[str]] = None,
        markers: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        verbose: bool = False,
        coverage: bool = False,
        coverage_source: Optional[List[str]] = None,
        extra_args: Optional[List[str]] = None,
    ) -> List[str]:
        """构建pytest命令行参数."""
        args = ["pytest"]

        # 覆盖pyproject.toml中的addopts（避免依赖未安装的插件如pytest-cov）
        args.extend(["-o", "addopts="])

        if self._config_path:
            args.extend(["-c", self._config_path])

        if verbose:
            args.append("-v")

        if markers:
            for marker in markers:
                args.extend(["-m", marker])

        if keywords:
            args.extend(["-k", keywords])

        if coverage:
            args.append("--cov-report=json")
            if coverage_source:
                args.extend(["--cov", ",".join(coverage_source)])
            else:
                args.append("--cov")

        if extra_args:
            args.extend(extra_args)

        if paths:
            args.extend(paths)

        return args

    # ========== 结果解析 ==========

    def _parse_from_output(
        self, stdout: str, stderr: str
    ) -> List[TestCaseResult]:
        """从pytest输出解析测试结果."""
        results: List[TestCaseResult] = []
        combined = stdout + "\n" + stderr

        for line in combined.split("\n"):
            line = line.strip()
            if "::" not in line:
                continue

            parsed = TestCaseResult.from_status_line(line)
            if parsed is not None:
                results.append(parsed)

        return results

    def _parse_duration_from_summary(self, output: str) -> float:
        """从pytest摘要中提取总耗时."""
        match = re.search(r"==.*?in ([\d.]+)s.*?==", output)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return 0.0

    def _read_coverage_report(self) -> Optional[CoverageData]:
        """读取coverage.json报告."""
        cov_path = Path(self._project_root or ".") / "coverage.json"
        if not cov_path.exists():
            return None

        try:
            with open(cov_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        totals = data.get("totals", {})
        total_coverage = totals.get("percent_covered", 0.0)
        covered_lines = totals.get("covered_lines", 0)
        total_lines = totals.get("num_statements", 0)
        missing_lines = total_lines - covered_lines

        file_coverages: Dict[str, Dict[str, Any]] = {}
        for fp, fd in data.get("files", {}).items():
            summary = fd.get("summary", {})
            file_coverages[fp] = {
                "coverage": summary.get("percent_covered", 0.0),
                "covered_lines": summary.get("covered_lines", 0),
                "total_lines": summary.get("num_statements", 0),
                "missing_lines": summary.get("missing_lines", 0),
            }

        return CoverageData(
            total_coverage=total_coverage,
            covered_lines=covered_lines,
            total_lines=total_lines,
            missing_lines=missing_lines,
            file_coverages=file_coverages,
        )

    # ========== 核心运行方法 ==========

    def run(
        self,
        paths: Optional[List[str]] = None,
        markers: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        verbose: bool = False,
        timeout: int = 60,
    ) -> TestSessionResult:
        """执行测试.

        Args:
            paths: 测试路径列表
            markers: pytest标记过滤
            keywords: 关键词过滤
            verbose: 详细输出
            timeout: 超时秒数

        Returns:
            TestSessionResult
        """
        from datetime import datetime

        started_at = datetime.now()

        args = self._build_args(
            paths=paths,
            markers=markers,
            keywords=keywords,
            verbose=True,
            extra_args=["--tb=short", "-rN"],
        )

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._project_root,
                env=self._build_env(),
            )
            exit_code = result.returncode
            stdout = result.stdout
            stderr = result.stderr
        except subprocess.TimeoutExpired:
            return TestSessionResult(
                exit_code=-1,
                started_at=started_at,
                finished_at=datetime.now(),
                test_cases=[create_test_result(
                    "timeout",
                    TestStatus.ERROR,
                    message=f"测试执行超时 ({timeout}s)",
                )],
            )

        test_cases = self._parse_from_output(stdout, stderr)
        duration = self._parse_duration_from_summary(stdout)

        return TestSessionResult(
            test_cases=test_cases,
            duration=duration,
            exit_code=exit_code,
            root_dir=self._project_root or ".",
            started_at=started_at,
            finished_at=datetime.now(),
        )

    def run_with_coverage(
        self,
        paths: Optional[List[str]] = None,
        coverage_source: Optional[List[str]] = None,
        markers: Optional[List[str]] = None,
        keywords: Optional[str] = None,
        timeout: int = 120,
    ) -> Tuple[TestSessionResult, Optional[CoverageData]]:
        """执行测试并收集覆盖率."""
        from datetime import datetime

        started_at = datetime.now()

        args = self._build_args(
            paths=paths,
            markers=markers,
            keywords=keywords,
            coverage=True,
            coverage_source=coverage_source,
            extra_args=["--tb=short", "-rN"],
        )

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._project_root,
                env=self._build_env(),
            )
            exit_code = result.returncode
        except subprocess.TimeoutExpired:
            session = TestSessionResult(
                exit_code=-1,
                started_at=started_at,
                finished_at=datetime.now(),
                test_cases=[create_test_result(
                    "timeout",
                    TestStatus.ERROR,
                    message=f"测试执行超时 ({timeout}s)",
                )],
            )
            return session, None

        test_cases = self._parse_from_output(result.stdout, result.stderr)
        duration = self._parse_duration_from_summary(result.stdout)

        session = TestSessionResult(
            test_cases=test_cases,
            duration=duration,
            exit_code=exit_code,
            root_dir=self._project_root or ".",
            started_at=started_at,
            finished_at=datetime.now(),
        )

        coverage = self._read_coverage_report()
        return session, coverage

    # ========== 便捷运行方法 ==========

    def run_single_file(
        self,
        file_path: str,
        verbose: bool = False,
    ) -> TestSessionResult:
        """运行单个测试文件."""
        return self.run(paths=[file_path], verbose=verbose)

    def run_by_marker(
        self,
        marker: str,
        verbose: bool = False,
    ) -> TestSessionResult:
        """按标记运行测试."""
        return self.run(markers=[marker], verbose=verbose)

    def run_by_keyword(
        self,
        keyword: str,
        verbose: bool = False,
    ) -> TestSessionResult:
        """按关键词运行测试."""
        return self.run(keywords=keyword, verbose=verbose)

    # ========== 测试发现 ==========

    def discover_tests(
        self,
        paths: Optional[List[str]] = None,
    ) -> List[str]:
        """发现测试用例（收集模式，不执行）."""
        args = self._build_args(
            paths=paths,
            extra_args=["--collect-only", "-q"],
        )

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=self._project_root,
                env=self._build_env(),
            )
            output = result.stdout
        except Exception:
            return []

        test_ids: List[str] = []
        for line in output.split("\n"):
            line = line.strip()
            if "::" in line and "::test_" in line:
                test_ids.append(line)

        return test_ids


# ========== 便捷函数 ==========

def run_tests(
    paths: Optional[List[str]] = None,
    project_root: Optional[str] = None,
    timeout: int = 60,
) -> TestSessionResult:
    """快速运行测试的便捷函数."""
    runner = TestRunner(project_root=project_root)
    return runner.run(paths=paths, timeout=timeout)


def run_tests_with_coverage(
    paths: Optional[List[str]] = None,
    project_root: Optional[str] = None,
    coverage_source: Optional[List[str]] = None,
) -> Tuple[TestSessionResult, Optional[CoverageData]]:
    """快速运行测试并收集覆盖率的便捷函数."""
    runner = TestRunner(project_root=project_root)
    return runner.run_with_coverage(
        paths=paths,
        coverage_source=coverage_source,
    )


# 全局实例
test_runner = TestRunner()
