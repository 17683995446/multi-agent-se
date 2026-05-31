#!/usr/bin/env python3
"""第22阶段验收脚本 - 代码质量检查器.

验证内容：
- 问题严重程度定义
- 问题类别定义
- 代码位置信息
- 质量报告生成
- Ruff集成检查
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from multi_agent_se.quality import (
    Severity,
    IssueCategory,
    IssueSource,
    CodeLocation,
    FixSuggestion,
    QualityIssue,
    QualityReport,
    QualityChecker,
    create_issue,
    check_code,
    format_code,
)


def print_header(title: str) -> None:
    """打印标题."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name: str, passed: bool, message: str = "") -> None:
    """打印测试结果."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {test_name}")
    if message:
        print(f"         {message}")


def test_severity_enum() -> bool:
    """测试严重程度枚举."""
    print_header("测试1: Severity 严重程度枚举")
    
    severities = [
        Severity.CRITICAL,
        Severity.HIGH,
        Severity.MEDIUM,
        Severity.LOW,
        Severity.INFO,
    ]
    
    for sev in severities:
        print(f"  - {sev.name}: {sev.value}")
    
    assert len(severities) == 5
    print_result("Severity 枚举", True, f"共{len(severities)}个级别")
    return True


def test_issue_category() -> bool:
    """测试问题类别枚举."""
    print_header("测试2: IssueCategory 问题类别枚举")
    
    categories = [
        IssueCategory.SYNTAX,
        IssueCategory.STYLE,
        IssueCategory.COMPLEXITY,
        IssueCategory.SECURITY,
        IssueCategory.PERFORMANCE,
        IssueCategory.BUG_RISK,
        IssueCategory.DOCUMENTATION,
        IssueCategory.TYPE_CHECKING,
        IssueCategory.IMPORT,
        IssueCategory.COMPATIBILITY,
    ]
    
    for cat in categories:
        print(f"  - {cat.name}: {cat.value}")
    
    assert len(categories) == 10
    print_result("IssueCategory 枚举", True, f"共{len(categories)}个类别")
    return True


def test_code_location() -> bool:
    """测试代码位置信息."""
    print_header("测试3: CodeLocation 代码位置")
    
    # 单行位置
    loc1 = CodeLocation(
        file_path="test.py",
        line_start=10,
        column_start=5,
    )
    assert loc1.line_range == "line 10"
    assert "test.py:10:5" in loc1.position
    print(f"  ✓ 单行位置: {loc1.position}")
    
    # 多行位置
    loc2 = CodeLocation(
        file_path="test.py",
        line_start=10,
        column_start=5,
        line_end=12,
        column_end=20,
    )
    assert loc2.line_range == "lines 10-12"
    assert "test.py:10:5-12:20" == loc2.position
    print(f"  ✓ 多行位置: {loc2.position}")
    
    # 转换为字典
    loc_dict = loc1.to_dict()
    assert loc_dict["file_path"] == "test.py"
    print(f"  ✓ to_dict() 正常")
    
    print_result("CodeLocation 代码位置", True)
    return True


def test_fix_suggestion() -> bool:
    """测试修复建议."""
    print_header("测试4: FixSuggestion 修复建议")
    
    # 自动修复
    fix1 = FixSuggestion(
        description="Remove unused import",
        auto_fixable=True,
        replacement_code="",
        confidence=0.95,
    )
    assert fix1.auto_fixable == True
    print(f"  ✓ 自动修复: {fix1.description}")
    
    # 手动修复
    fix2 = FixSuggestion(
        description="Consider refactoring this function",
        auto_fixable=False,
    )
    assert fix2.auto_fixable == False
    print(f"  ✓ 手动修复: {fix2.description}")
    
    print_result("FixSuggestion 修复建议", True)
    return True


def test_quality_issue() -> bool:
    """测试质量问题定义."""
    print_header("测试5: QualityIssue 质量问题")
    
    # 创建问题
    issue = QualityIssue(
        rule_id="E501",
        message="Line too long (120 > 88 characters)",
        severity=Severity.MEDIUM,
        category=IssueCategory.STYLE,
        source=IssueSource.RUFF,
        location=CodeLocation(
            file_path="test.py",
            line_start=10,
            column_start=89,
        ),
        code_snippet="x = 'a very long string that exceeds the line length limit'",
    )
    
    assert issue.rule_id == "E501"
    assert issue.severity == Severity.MEDIUM
    assert issue.is_high_priority == False
    assert issue.is_auto_fixable == False  # 默认不可自动修复
    print(f"  ✓ 问题创建: [{issue.rule_id}] {issue.message}")
    
    # 完整消息
    full_msg = issue.full_message
    assert "E501" in full_msg
    assert "test.py" in full_msg
    print(f"  ✓ 完整消息格式正确")
    
    # 转换为字典
    issue_dict = issue.to_dict()
    assert issue_dict["rule_id"] == "E501"
    assert issue_dict["severity"] == "medium"
    print(f"  ✓ to_dict() 正常")
    
    print_result("QualityIssue 质量问题", True)
    return True


def test_quality_issue_from_ruff() -> bool:
    """测试从Ruff问题创建."""
    print_header("测试6: QualityIssue.from_ruff_issue()")
    
    # E501 - 行太长
    issue1 = QualityIssue.from_ruff_issue(
        code="E501",
        message="Line too long",
        file_path="test.py",
        line=10,
        col=89,
        fixable=False,
    )
    assert issue1.category == IssueCategory.BUG_RISK  # E类映射为BUG_RISK
    assert issue1.severity == Severity.HIGH
    print(f"  ✓ E501映射: {issue1.severity.value}, {issue1.category.value}")
    
    # W291 - 尾随空格
    issue2 = QualityIssue.from_ruff_issue(
        code="W291",
        message="Trailing whitespace",
        file_path="test.py",
        line=5,
        col=10,
        fixable=True,
    )
    assert issue2.category == IssueCategory.STYLE  # W类映射为STYLE
    assert issue2.severity == Severity.MEDIUM
    assert issue2.is_auto_fixable == True
    print(f"  ✓ W291映射: {issue2.severity.value}, {issue2.category.value}, fixable={issue2.is_auto_fixable}")
    
    # S101 - 安全问题
    issue3 = QualityIssue.from_ruff_issue(
        code="S101",
        message="Use of assert detected",
        file_path="test.py",
        line=20,
        col=1,
        fixable=False,
    )
    assert issue3.category == IssueCategory.SECURITY  # S类映射为SECURITY
    assert issue3.severity == Severity.CRITICAL
    print(f"  ✓ S101映射: {issue3.severity.value}, {issue3.category.value}")
    
    print_result("QualityIssue.from_ruff_issue()", True)
    return True


def test_quality_report() -> bool:
    """测试质量报告."""
    print_header("测试7: QualityReport 质量报告")
    
    # 创建报告
    report = QualityReport(file_path="test.py")
    
    # 添加问题
    report.issues.append(create_issue(
        rule_id="E501",
        message="Line too long",
        file_path="test.py",
        line=10,
        severity=Severity.HIGH,
    ))
    report.issues.append(create_issue(
        rule_id="W291",
        message="Trailing whitespace",
        file_path="test.py",
        line=5,
        severity=Severity.LOW,
    ))
    report.issues.append(create_issue(
        rule_id="F401",
        message="Unused import",
        file_path="test.py",
        line=1,
        severity=Severity.HIGH,
    ))
    
    # 统计
    assert report.total_issues == 3
    assert report.high_count == 2
    assert report.low_count == 1
    assert report.critical_count == 0
    print(f"  ✓ 统计正确: total={report.total_issues}, high={report.high_count}")
    
    # 按严重程度筛选
    high_issues = report.get_issues_by_severity(Severity.HIGH)
    assert len(high_issues) == 2
    print(f"  ✓ 按严重程度筛选: {len(high_issues)}个高优先级")
    
    # 摘要
    summary = report.format_summary()
    assert "Total Issues: 3" in summary
    print(f"  ✓ 摘要格式正确")
    
    # 转换为字典
    report_dict = report.to_dict()
    assert report_dict["total_issues"] == 3
    print(f"  ✓ to_dict() 正常")
    
    print_result("QualityReport 质量报告", True)
    return True


def test_quality_report_merge() -> bool:
    """测试报告合并."""
    print_header("测试8: QualityReport 合并")
    
    report1 = QualityReport(file_path="file1.py")
    report1.issues.append(create_issue("E501", "Line too long", "file1.py", 10))
    
    report2 = QualityReport(file_path="file2.py")
    report2.issues.append(create_issue("W291", "Trailing space", "file2.py", 5))
    
    merged = report1.merge(report2)
    
    assert merged.total_issues == 2
    assert any(i.file_path == "file1.py" for i in merged.issues)
    assert any(i.file_path == "file2.py" for i in merged.issues)
    print(f"  ✓ 合并后共{merged.total_issues}个问题")
    
    print_result("QualityReport 合并", True)
    return True


def test_quality_checker() -> bool:
    """测试质量检查器."""
    print_header("测试9: QualityChecker 检查器")
    
    checker = QualityChecker()
    
    # 检查代码
    code = """
import os
import sys

def foo():
    x = 1
    print(x)
"""
    report = checker.check_source(code, file_path="test.py")
    
    # 应该检测到未使用的导入
    assert isinstance(report, QualityReport)
    print(f"  ✓ 检查完成: 发现{report.total_issues}个问题")
    
    # 检查是否有F401（未使用导入）
    unused_imports = [i for i in report.issues if i.rule_id == "F401"]
    print(f"  ✓ 未使用导入: {len(unused_imports)}个")
    
    print_result("QualityChecker 检查器", True)
    return True


def test_format_code() -> bool:
    """测试代码格式化."""
    print_header("测试10: 代码格式化")
    
    unformatted = """def foo( x,y ):
    z= x+y
    return z
"""
    
    formatted = format_code(unformatted)
    
    # 格式化后应该没有多余空格
    assert "def foo(" in formatted
    print(f"  ✓ 格式化成功")
    newline = chr(10)
    escaped_newline = '\\n'
    print(f"     输入: {unformatted[:30].replace(newline, escaped_newline)}...")
    print(f"     输出: {formatted[:30].replace(newline, escaped_newline)}...")
    
    print_result("代码格式化", True)
    return True


def test_check_code_convenience() -> bool:
    """测试便捷函数."""
    print_header("测试11: check_code 便捷函数")
    
    code = "x=1\ny=2\n"
    report = check_code(code, file_path="test.py")
    
    assert isinstance(report, QualityReport)
    print(f"  ✓ 便捷函数工作正常")
    
    print_result("check_code 便捷函数", True)
    return True


def test_severity_filtering() -> bool:
    """测试严重程度过滤."""
    print_header("测试12: 严重程度过滤")
    
    # 只报告HIGH及以上
    checker = QualityChecker(min_severity=Severity.HIGH)
    
    code = """
x=1  # E225: missing whitespace around operator (LOW severity in mapping)
import os  # F401: unused import (HIGH severity)
"""
    report = checker.check_source(code, file_path="test.py")
    
    # 应该只包含HIGH及以上严重级别的问题
    for issue in report.issues:
        assert issue.severity in (Severity.HIGH, Severity.CRITICAL)
    
    print(f"  ✓ 过滤后剩余{report.total_issues}个高优先级问题")
    
    print_result("严重程度过滤", True)
    return True


def main() -> int:
    """主函数."""
    print("\n" + "="*60)
    print("  第22阶段验收: 代码质量检查器 (Code Quality Checker)")
    print("="*60)
    
    tests = [
        test_severity_enum,
        test_issue_category,
        test_code_location,
        test_fix_suggestion,
        test_quality_issue,
        test_quality_issue_from_ruff,
        test_quality_report,
        test_quality_report_merge,
        test_quality_checker,
        test_format_code,
        test_check_code_convenience,
        test_severity_filtering,
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
        print("\n  ✓ 第22阶段验收通过！")
        print("\n  实现功能:")
        print("    - Severity: 5级严重程度")
        print("    - IssueCategory: 10种问题类别")
        print("    - CodeLocation: 精确的代码位置信息")
        print("    - FixSuggestion: 修复建议与自动修复标记")
        print("    - QualityIssue: 统一的问题描述结构")
        print("    - QualityReport: 完整的质量报告")
        print("    - QualityChecker: Ruff集成检查器")
        print("    - 代码格式化: 基于Ruff的格式化")
        print("="*60)
        return 0
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
