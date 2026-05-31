#!/usr/bin/env python3
"""第23阶段验收脚本 - 测试运行器.

验证内容：
- TestStatus 枚举
- TestCaseResult 单用例结果
- TestSessionResult 测试会话结果
- CoverageData 覆盖率数据
- TestCaseResult.from_status_line() 解析
- TestRunner 运行真实测试
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from multi_agent_se.quality.coverage import (
    TestStatus,
    TestCaseResult,
    TestSessionResult,
    CoverageData,
    TestRunner,
    create_test_result,
    run_tests,
)


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name: str, passed: bool, message: str = "") -> None:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {test_name}")
    if message:
        print(f"         {message}")


def test_test_status() -> bool:
    """测试TestStatus枚举."""
    print_header("测试1: TestStatus 枚举")

    statuses = [
        TestStatus.PASSED, TestStatus.FAILED, TestStatus.SKIPPED,
        TestStatus.ERROR, TestStatus.XFAILED, TestStatus.XPASSED,
        TestStatus.UNKNOWN,
    ]
    for s in statuses:
        print(f"  - {s.name}: {s.value}")

    assert len(statuses) == 7
    print_result("TestStatus 枚举", True, f"共{len(statuses)}个状态")
    return True


def test_test_case_result() -> bool:
    """测试TestCaseResult."""
    print_header("测试2: TestCaseResult 单用例结果")

    # 通过
    r1 = create_test_result("tests/test_foo.py::test_bar", TestStatus.PASSED, 0.05)
    assert r1.is_passed is True
    assert r1.is_failed is False
    assert r1.is_unexpected is False
    assert r1.name == "test_bar"
    print(f"  ✓ 通过: {r1.nodeid}")

    # 失败
    r2 = create_test_result("tests/test_foo.py::test_baz", TestStatus.FAILED, 0.1, "assert 1 == 2")
    assert r2.is_failed is True
    assert r2.is_unexpected is True
    print(f"  ✓ 失败: {r2.nodeid}, msg={r2.message}")

    # 跳过
    r3 = create_test_result("tests/test_foo.py::test_skip", TestStatus.SKIPPED)
    assert r3.is_skipped is True
    print(f"  ✓ 跳过: {r3.nodeid}")

    # 错误
    r4 = create_test_result("tests/test_foo.py::test_err", TestStatus.ERROR, message="TypeError")
    assert r4.is_error is True
    print(f"  ✓ 错误: {r4.nodeid}")

    # 序列化
    d = r1.to_dict()
    assert d["status"] == "passed"
    assert d["name"] == "test_bar"
    print(f"  ✓ to_dict() 正常")

    print_result("TestCaseResult", True)
    return True


def test_from_status_line() -> bool:
    """测试从pytest输出行解析."""
    print_header("测试3: TestCaseResult.from_status_line()")

    cases = [
        ("tests/test_foo.py::test_bar PASSED", TestStatus.PASSED),
        ("tests/test_foo.py::test_baz FAILED", TestStatus.FAILED),
        ("tests/test_foo.py::test_skip SKIPPED", TestStatus.SKIPPED),
        ("tests/test_foo.py::test_err ERROR", TestStatus.ERROR),
        ("tests/test_foo.py::test_xfail XFAILED", TestStatus.XFAILED),
    ]

    for line, expected in cases:
        result = TestCaseResult.from_status_line(line)
        assert result is not None, f"解析失败: {line}"
        assert result.status == expected, f"期望{expected}, 得到{result.status}"
        print(f"  ✓ {line} -> {result.status.value}")

    # 带百分比的行
    result = TestCaseResult.from_status_line("tests/test_foo.py::test_bar PASSED [ 50%]")
    assert result is not None
    assert result.status == TestStatus.PASSED
    print(f"  ✓ 带百分比: PASSED [ 50%] -> {result.status.value}")

    # 无效行
    result = TestCaseResult.from_status_line("some random text")
    assert result is None
    print(f"  ✓ 无效行返回None")

    print_result("from_status_line() 解析", True)
    return True


def test_test_session_result() -> bool:
    """测试TestSessionResult."""
    print_header("测试4: TestSessionResult 测试会话结果")

    session = TestSessionResult(
        test_cases=[
            create_test_result("t1", TestStatus.PASSED),
            create_test_result("t2", TestStatus.PASSED),
            create_test_result("t3", TestStatus.FAILED, message="assert fail"),
            create_test_result("t4", TestStatus.PASSED),
            create_test_result("t5", TestStatus.SKIPPED),
            create_test_result("t6", TestStatus.ERROR, message="err"),
        ],
        duration=1.5,
        exit_code=1,
    )

    assert session.total == 6
    assert session.passed == 3
    assert session.failed == 1
    assert session.errors == 1
    assert session.skipped == 1
    assert session.has_failures is True
    assert session.all_passed is False
    assert abs(session.pass_rate - 50.0) < 0.01
    print(f"  ✓ 统计: total={session.total}, passed={session.passed}, "
          f"failed={session.failed}, errors={session.errors}, rate={session.pass_rate:.1f}%")

    # 筛选
    failures = session.get_failures()
    assert len(failures) == 1
    print(f"  ✓ get_failures(): {len(failures)}个")

    errors = session.get_errors()
    assert len(errors) == 1
    print(f"  ✓ get_errors(): {len(errors)}个")

    # 摘要
    summary = session.format_summary()
    assert "Tests: 6" in summary
    assert "HAS FAILURES" in summary
    print(f"  ✓ 摘要: {summary}")

    # 序列化
    d = session.to_dict()
    assert d["total"] == 6
    assert d["all_passed"] is False
    print(f"  ✓ to_dict() 正常")

    print_result("TestSessionResult", True)
    return True


def test_coverage_data() -> bool:
    """测试CoverageData."""
    print_header("测试5: CoverageData 覆盖率数据")

    cov = CoverageData(
        total_coverage=85.5,
        covered_lines=855,
        total_lines=1000,
        missing_lines=145,
        file_coverages={
            "module_a.py": {"coverage": 90.0, "covered_lines": 450, "total_lines": 500},
            "module_b.py": {"coverage": 81.0, "covered_lines": 405, "total_lines": 500},
        },
    )

    assert cov.is_sufficient() is True
    assert cov.is_sufficient(threshold=90.0) is False
    assert cov.coverage_gap == 145
    print(f"  ✓ 覆盖率: {cov.total_coverage}%, sufficient(80)={cov.is_sufficient()}, "
          f"sufficient(90)={cov.is_sufficient(90.0)}")

    summary = cov.format_summary()
    assert "85.5%" in summary
    print(f"  ✓ 摘要: {summary}")

    d = cov.to_dict()
    assert d["total_coverage"] == 85.5
    assert len(d["file_coverages"]) == 2
    print(f"  ✓ to_dict() 正常")

    print_result("CoverageData", True)
    return True


def test_test_runner_real() -> bool:
    """测试TestRunner运行真实测试."""
    print_header("测试6: TestRunner 运行真实测试")

    # 创建临时测试文件
    test_dir = project_root / "tests_phase23"
    test_dir.mkdir(exist_ok=True)

    test_file = test_dir / "test_sample.py"
    test_file.write_text("""
import pytest

def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 5 - 3 == 2

def test_will_fail():
    assert 1 == 2

@pytest.mark.skip(reason="demo skip")
def test_skipped():
    assert True
""")

    runner = TestRunner(project_root=str(project_root))
    result = runner.run_single_file(str(test_file))

    assert result.total >= 3
    assert result.passed >= 2
    assert result.failed >= 1
    assert result.skipped >= 1
    print(f"  ✓ 运行结果: total={result.total}, passed={result.passed}, "
          f"failed={result.failed}, skipped={result.skipped}")

    # 测试发现
    discovered = runner.discover_tests([str(test_file)])
    assert len(discovered) >= 4
    print(f"  ✓ 发现测试: {len(discovered)}个")

    # 清理
    import shutil
    test_file.unlink(missing_ok=True)
    shutil.rmtree(test_dir, ignore_errors=True)

    print_result("TestRunner 真实测试", True)
    return True


def test_run_tests_convenience() -> bool:
    """测试便捷函数."""
    print_header("测试7: run_tests 便捷函数")

    # 创建临时测试
    test_dir = project_root / "tests_phase23_conv"
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "test_quick.py"
    test_file.write_text("""
def test_hello():
    assert "hello" == "hello"
""")

    result = run_tests(paths=[str(test_file)], project_root=str(project_root))
    assert isinstance(result, TestSessionResult)
    assert result.total >= 1
    print(f"  ✓ 便捷函数: total={result.total}, all_passed={result.all_passed}")

    # 清理
    import shutil
    test_file.unlink(missing_ok=True)
    shutil.rmtree(test_dir, ignore_errors=True)

    print_result("run_tests 便捷函数", True)
    return True


def main() -> int:
    print("\n" + "="*60)
    print("  第23阶段验收: 测试运行器 (Test Runner)")
    print("="*60)

    tests = [
        test_test_status,
        test_test_case_result,
        test_from_status_line,
        test_test_session_result,
        test_coverage_data,
        test_test_runner_real,
        test_run_tests_convenience,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"  验收结果: {passed} 通过, {failed} 失败")
    print("="*60)

    if failed == 0:
        print("\n  ✓ 第23阶段验收通过！")
        print("\n  实现功能:")
        print("    - TestStatus: 7种测试状态")
        print("    - TestCaseResult: 单用例结果（含from_status_line解析）")
        print("    - TestSessionResult: 会话结果（统计/筛选/摘要）")
        print("    - CoverageData: 覆盖率数据")
        print("    - TestRunner: Pytest集成（run/单文件/标记/关键词/发现）")
        print("    - 便捷函数: run_tests / run_tests_with_coverage")
        print("="*60)
        return 0
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
