#!/usr/bin/env python3
"""阶段9验收验证脚本 - Pytest测试运行器封装."""
import sys
from pathlib import Path


def print_header(text: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_result(test: str, passed: bool, details: str = "") -> bool:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test}")
    if details:
        print(f"       {details}")
    return passed


def main() -> int:
    print_header("阶段9验收验证 - Pytest测试运行器封装")
    all_passed = True
    project_root = Path(__file__).parent.parent

    # 1. Pytest安装检查
    print_header("1. Pytest安装检查")
    import subprocess
    result = subprocess.run(
        ["pytest", "--version"], capture_output=True, text=True
    )
    all_passed = print_result(
        "Pytest已安装", result.returncode == 0, result.stdout.strip()
    ) and all_passed

    # 2. pytest-cov安装检查
    result_cov = subprocess.run(
        ["python3", "-c", "import pytest_cov; print('ok')"],
        capture_output=True, text=True,
    )
    all_passed = print_result(
        "pytest-cov已安装", result_cov.returncode == 0
    ) and all_passed

    # 3. TestCaseResult数据类检查
    print_header("2. TestCaseResult数据类检查")
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.quality.coverage.test_runner import (
            TestCaseResult, TestSessionResult, CoverageData,
            TestRunner, test_runner,
        )
        all_passed = print_result("模块可导入", True) and all_passed

        # TestCaseResult
        tc = TestCaseResult(
            nodeid="test_foo.py::test_bar",
            name="test_bar",
            outcome="passed",
            duration=0.123,
        )
        all_passed = print_result("TestCaseResult可创建", True) and all_passed
        all_passed = print_result("is_passed", tc.is_passed) and all_passed
        all_passed = print_result("is_failed", not tc.is_failed) and all_passed
        all_passed = print_result("is_skipped", not tc.is_skipped) and all_passed
        all_passed = print_result("is_error", not tc.is_error) and all_passed
        all_passed = print_result("to_dict", "nodeid" in tc.to_dict()) and all_passed

        # 失败用例
        tc_fail = TestCaseResult(
            nodeid="test_foo.py::test_baz",
            name="test_baz",
            outcome="failed",
            message="assert 1 == 2",
        )
        all_passed = print_result("失败用例is_failed", tc_fail.is_failed) and all_passed
        all_passed = print_result("失败用例not is_passed", not tc_fail.is_passed) and all_passed

        # 跳过用例
        tc_skip = TestCaseResult(nodeid="x.py::y", name="y", outcome="skipped")
        all_passed = print_result("跳过用例is_skipped", tc_skip.is_skipped) and all_passed

        # 错误用例
        tc_err = TestCaseResult(nodeid="x.py::z", name="z", outcome="error")
        all_passed = print_result("错误用例is_error", tc_err.is_error) and all_passed

    except Exception as e:
        all_passed = print_result("TestCaseResult模块", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 4. TestSessionResult数据类检查
    print_header("3. TestSessionResult数据类检查")
    try:
        session = TestSessionResult(
            test_cases=[tc, tc_fail, tc_skip, tc_err],
            duration=1.5,
            exit_code=1,
        )
        all_passed = print_result("TestSessionResult可创建", True) and all_passed
        all_passed = print_result("total", session.total == 4) and all_passed
        all_passed = print_result("passed", session.passed == 1) and all_passed
        all_passed = print_result("failed", session.failed == 1) and all_passed
        all_passed = print_result("skipped", session.skipped == 1) and all_passed
        all_passed = print_result("errors", session.errors == 1) and all_passed
        all_passed = print_result(
            "pass_rate", abs(session.pass_rate - 25.0) < 0.01
        ) and all_passed
        all_passed = print_result("all_passed=False", not session.all_passed) and all_passed
        all_passed = print_result("get_failures", len(session.get_failures()) == 1) and all_passed
        all_passed = print_result("get_errors", len(session.get_errors()) == 1) and all_passed
        all_passed = print_result("get_skipped", len(session.get_skipped()) == 1) and all_passed
        all_passed = print_result("to_dict", "pass_rate" in session.to_dict()) and all_passed

        # 全部通过的场景
        session_ok = TestSessionResult(
            test_cases=[tc, TestCaseResult(nodeid="a::b", name="b", outcome="passed")],
            exit_code=0,
        )
        all_passed = print_result("all_passed=True", session_ok.all_passed) and all_passed
        all_passed = print_result(
            "pass_rate=100", abs(session_ok.pass_rate - 100.0) < 0.01
        ) and all_passed

        # 空场景
        session_empty = TestSessionResult()
        all_passed = print_result("空会话total=0", session_empty.total == 0) and all_passed
        all_passed = print_result("空会话pass_rate=0", session_empty.pass_rate == 0.0) and all_passed

    except Exception as e:
        all_passed = print_result("TestSessionResult", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 5. CoverageData数据类检查
    print_header("4. CoverageData数据类检查")
    try:
        cov = CoverageData(
            total_coverage=85.5,
            covered_lines=171,
            total_lines=200,
            missing_lines=29,
            file_coverages={
                "module_a.py": {
                    "coverage": 90.0,
                    "covered_lines": 90,
                    "total_lines": 100,
                    "missing_lines": 10,
                },
            },
        )
        all_passed = print_result("CoverageData可创建", True) and all_passed
        all_passed = print_result("total_coverage", cov.total_coverage == 85.5) and all_passed
        all_passed = print_result("covered_lines", cov.covered_lines == 171) and all_passed
        all_passed = print_result("total_lines", cov.total_lines == 200) and all_passed
        all_passed = print_result("missing_lines", cov.missing_lines == 29) and all_passed
        all_passed = print_result("is_sufficient(>=80)", cov.is_sufficient) and all_passed
        all_passed = print_result("file_coverages", len(cov.file_coverages) == 1) and all_passed
        all_passed = print_result("to_dict", "total_coverage" in cov.to_dict()) and all_passed

        # 不足覆盖率
        cov_low = CoverageData(total_coverage=60.0)
        all_passed = print_result("is_sufficient(<80)=False", not cov_low.is_sufficient) and all_passed

    except Exception as e:
        all_passed = print_result("CoverageData", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 6. TestRunner类检查
    print_header("5. TestRunner类检查")
    try:
        # 默认实例
        runner = TestRunner()
        all_passed = print_result("TestRunner默认实例", True) and all_passed

        # 带参数实例
        runner_cfg = TestRunner(
            project_root=str(project_root),
            config_path=str(project_root / "pyproject.toml"),
        )
        all_passed = print_result("TestRunner配置化实例", True) and all_passed

        # 全局实例
        all_passed = print_result("全局test_runner实例", test_runner is not None) and all_passed

        # _build_args
        args = runner._build_args(paths=["tests/"], verbose=True)
        all_passed = print_result("_build_args基础", "pytest" in args and "-v" in args) and all_passed

        args_marker = runner._build_args(markers=["slow"])
        all_passed = print_result("_build_args标记", "-m" in args_marker and "slow" in args_marker) and all_passed

        args_kw = runner._build_args(keywords="test_config")
        all_passed = print_result("_build_args关键词", "-k" in args_kw and "test_config" in args_kw) and all_passed

        args_cov = runner._build_args(coverage=True, coverage_source=["src"])
        all_passed = print_result("_build_args覆盖率", "--cov-report=json" in args_cov) and all_passed

    except Exception as e:
        all_passed = print_result("TestRunner类", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 7. 实际测试执行
    print_header("6. 实际测试执行")
    try:
        runner = TestRunner(project_root=str(project_root))

        # 运行已有测试文件
        test_file = project_root / "tests" / "unit" / "test_config.py"
        if test_file.exists():
            result = runner.run_single_file(str(test_file))
            all_passed = print_result("run_single_file执行成功", True) and all_passed
            all_passed = print_result(
                "测试结果非空", result.total > 0,
                f"共{result.total}个测试",
            ) and all_passed
            all_passed = print_result(
                "exit_code可获取", isinstance(result.exit_code, int),
                f"exit_code={result.exit_code}",
            ) and all_passed
            all_passed = print_result(
                "to_dict可序列化", "total" in result.to_dict(),
            ) and all_passed
        else:
            all_passed = print_result("测试文件存在", False, f"{test_file} 不存在") and all_passed

    except Exception as e:
        all_passed = print_result("实际测试执行", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 8. 测试发现
    print_header("7. 测试发现")
    try:
        runner = TestRunner(project_root=str(project_root))
        discovered = runner.discover_tests(paths=["tests/unit/"])
        all_passed = print_result(
            "discover_tests可调用", True,
            f"发现 {len(discovered)} 个测试",
        ) and all_passed
        all_passed = print_result(
            "发现结果为列表", isinstance(discovered, list),
        ) and all_passed
        if discovered:
            all_passed = print_result(
                "测试ID格式正确", "::test_" in discovered[0],
                f"示例: {discovered[0]}",
            ) and all_passed

    except Exception as e:
        all_passed = print_result("测试发现", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 9. 文件结构检查
    print_header("8. 文件结构检查")
    all_passed = print_result(
        "文件: src/multi_agent_se/quality/coverage/test_runner.py",
        (project_root / "src/multi_agent_se/quality/coverage/test_runner.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: scripts/verify_phase9.py",
        Path(__file__).exists(),
    ) and all_passed

    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段9验收通过！所有检查项均符合要求。")
        print("  📋 阶段9交付物清单：")
        print("     - test_runner.py (TestRunner/TestCaseResult/TestSessionResult/CoverageData)")
        print("     - 测试执行/单文件运行/标记过滤/关键词过滤")
        print("     - 覆盖率收集与分析")
        print("     - 测试发现功能")
        print("     - scripts/verify_phase9.py (验收脚本)")
        return 0
    else:
        print("  ❌ 阶段9验收未通过！")
        return 1


if __name__ == "__main__":
    sys.exit(main())
