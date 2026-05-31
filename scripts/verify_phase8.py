#!/usr/bin/env python3
"""阶段8验收验证脚本."""
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
    print_header("阶段8验收验证 - 接入Ruff静态代码检查内核")
    all_passed = True
    project_root = Path(__file__).parent.parent
    
    # 1. Ruff安装检查
    print_header("1. Ruff安装检查")
    import subprocess
    result = subprocess.run(["ruff", "--version"], capture_output=True, text=True)
    all_passed = print_result("Ruff已安装", result.returncode == 0, result.stdout.strip()) and all_passed
    
    # 2. RuffChecker模块检查
    print_header("2. RuffChecker模块检查")
    
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.quality.linter.ruff_checker import (
            RuffChecker, RuffIssue, RuffResult, ruff_checker,
        )
        all_passed = print_result("RuffChecker模块可导入", True) and all_passed
        
        # 源码检查
        bad_code = '''import os
import sys
x=1
def foo( ):
    unused_var = "hello"
    pass
'''
        result = ruff_checker.check(source=bad_code)
        all_passed = print_result("check(source=)可用", True) and all_passed
        all_passed = print_result("发现违规问题", result.total > 0) and all_passed
        all_passed = print_result("问题解析正确", all(
            i.code and i.message and i.line > 0 for i in result.issues
        )) and all_passed
        
        # 规则过滤
        result_e = ruff_checker.check(source=bad_code, select=["E"])
        all_passed = print_result("select过滤可用", all(i.code.startswith("E") for i in result_e.issues)) and all_passed
        
        # 文件检查
        config_file = project_root / "src" / "multi_agent_se" / "core" / "config.py"
        if config_file.exists():
            file_result = ruff_checker.check_file(str(config_file))
            all_passed = print_result("check_file可用", True) and all_passed
            all_passed = print_result("结果可序列化", len(file_result.to_dict()) > 0) and all_passed
        
        # 格式化
        ugly = "x=1\ndef foo( ):\n    pass\n"
        formatted = ruff_checker.format_code(ugly)
        all_passed = print_result("format_code可用", "x = 1" in formatted) and all_passed
        
        diff = ruff_checker.format_diff(ugly)
        all_passed = print_result("format_diff可用", len(diff) > 0) and all_passed
        
        # RuffIssue
        issue = RuffIssue(code="E501", message="line too long", file="test.py", line=1, col=0, end_line=1, end_col=100)
        all_passed = print_result("RuffIssue可创建", issue.to_dict()["code"] == "E501") and all_passed
        
        # RuffResult
        res = RuffResult(issues=[issue], error_count=1)
        all_passed = print_result("RuffResult.has_errors", res.has_errors) and all_passed
        all_passed = print_result("RuffResult.total", res.total == 1) and all_passed
        
    except Exception as e:
        all_passed = print_result("RuffChecker模块", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()
    
    # 3. pyproject.toml配置检查
    print_header("3. pyproject.toml配置检查")
    
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        all_passed = print_result("pyproject.toml存在", True) and all_passed
        all_passed = print_result("包含Ruff配置", "[tool.ruff]" in content) and all_passed
        
        # 用配置创建检查器
        try:
            from multi_agent_se.quality.linter.ruff_checker import RuffChecker
            cfg_checker = RuffChecker(config_path=str(pyproject))
            all_passed = print_result("配置化检查器可创建", True) and all_passed
        except Exception as e:
            all_passed = print_result("配置化检查器", False, str(e)) and all_passed
    
    # 4. 文件结构检查
    print_header("4. 文件结构检查")
    all_passed = print_result(
        "文件: src/multi_agent_se/quality/linter/ruff_checker.py",
        (project_root / "src/multi_agent_se/quality/linter/ruff_checker.py").exists()
    ) and all_passed
    
    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段8验收通过！所有检查项均符合要求。")
        print("  📋 阶段8交付物清单：")
        print("     - ruff_checker.py (RuffChecker/RuffIssue/RuffResult)")
        print("     - 源码检查/文件检查/规则过滤")
        print("     - 代码格式化/格式化差异")
        print("     - pyproject.toml配置集成")
        print("     - scripts/verify_phase8.py (验收脚本)")
        return 0
    else:
        print("  ❌ 阶段8验收未通过！")
        return 1

if __name__ == "__main__":
    sys.exit(main())
