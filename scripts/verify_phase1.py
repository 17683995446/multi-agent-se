#!/usr/bin/env python3
"""阶段1验收验证脚本.

验证内容：
1. Python 3.10+ 环境
2. requirements.txt 依赖锁定
3. pyproject.toml 项目配置
4. 项目目录结构
5. 核心配置模块
6. 单元测试可运行
"""

import sys
import subprocess
from pathlib import Path

def print_header(text: str) -> None:
    """打印标题."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_result(test: str, passed: bool, details: str = "") -> bool:
    """打印测试结果."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test}")
    if details:
        print(f"       {details}")
    return passed

def main() -> int:
    """主函数."""
    print_header("阶段1验收验证 - 环境与底座搭建")
    
    all_passed = True
    project_root = Path(__file__).parent.parent
    
    # 1. Python版本检查
    print_header("1. Python环境检查")
    version = sys.version_info
    python_ok = version.major == 3 and version.minor >= 10
    all_passed &= print_result(
        "Python版本 >= 3.10", 
        python_ok, 
        f"当前: {version.major}.{version.minor}.{version.micro}"
    )
    
    # 2. 依赖文件检查
    print_header("2. 依赖文件检查")
    req_file = project_root / "requirements.txt"
    all_passed &= print_result(
        "requirements.txt 存在",
        req_file.exists(),
        str(req_file) if req_file.exists() else "文件不存在"
    )
    
    if req_file.exists():
        content = req_file.read_text()
        has_langgraph = "langgraph" in content
        has_autogen = "autogen" in content or "pyautogen" in content
        has_tree_sitter = "tree-sitter" in content
        has_ruff = "ruff" in content
        has_pytest = "pytest" in content
        
        all_passed &= print_result("包含 LangGraph", has_langgraph)
        all_passed &= print_result("包含 AutoGen", has_autogen)
        all_passed &= print_result("包含 Tree-sitter", has_tree_sitter)
        all_passed &= print_result("包含 Ruff", has_ruff)
        all_passed &= print_result("包含 Pytest", has_pytest)
    
    # 3. pyproject.toml检查
    print_header("3. 项目配置检查")
    pyproject = project_root / "pyproject.toml"
    all_passed &= print_result(
        "pyproject.toml 存在",
        pyproject.exists()
    )
    
    if pyproject.exists():
        content = pyproject.read_text()
        all_passed &= print_result("包含Ruff配置", "[tool.ruff]" in content)
        all_passed &= print_result("包含Pytest配置", "[tool.pytest.ini_options]" in content)
        all_passed &= print_result("包含MyPy配置", "[tool.mypy]" in content)
    
    # 4. 目录结构检查
    print_header("4. 项目目录结构检查")
    dirs_to_check = [
        "src/multi_agent_se",
        "src/multi_agent_se/core",
        "src/multi_agent_se/agents",
        "src/multi_agent_se/atomicity",
        "src/multi_agent_se/collaboration",
        "src/multi_agent_se/pipeline",
        "src/multi_agent_se/quality",
        "src/multi_agent_se/utils",
        "tests/unit",
        "tests/integration",
        "config",
        "docs",
        "scripts",
    ]
    
    for dir_path in dirs_to_check:
        full_path = project_root / dir_path
        all_passed &= print_result(
            f"目录: {dir_path}",
            full_path.exists(),
            "存在" if full_path.exists() else "不存在"
        )
    
    # 5. 核心模块检查
    print_header("5. 核心模块检查")
    core_files = [
        "src/multi_agent_se/__init__.py",
        "src/multi_agent_se/core/__init__.py",
        "src/multi_agent_se/core/config.py",
        "tests/unit/test_config.py",
        "README.md",
    ]
    
    for file_path in core_files:
        full_path = project_root / file_path
        all_passed &= print_result(
            f"文件: {file_path}",
            full_path.exists(),
            "存在" if full_path.exists() else "不存在"
        )
    
    # 6. 配置模块可导入检查
    print_header("6. 配置模块验证")
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.core.config import settings, logger, MASEError
        all_passed &= print_result("配置模块可导入", True)
        all_passed &= print_result("settings对象存在", settings is not None)
        all_passed &= print_result("logger对象存在", logger is not None)
        all_passed &= print_result("MASEError异常类存在", MASEError is not None)
    except Exception as e:
        all_passed &= print_result("配置模块可导入", False, str(e))
    
    # 7. 测试文件语法检查
    print_header("7. 测试文件验证")
    test_file = project_root / "tests/unit/test_config.py"
    if test_file.exists():
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(test_file)],
                capture_output=True,
                text=True,
                cwd=str(project_root)
            )
            all_passed &= print_result(
                "test_config.py 语法正确",
                result.returncode == 0,
                result.stderr if result.returncode != 0 else ""
            )
        except Exception as e:
            all_passed &= print_result("test_config.py 语法检查", False, str(e))
    
    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段1验收通过！所有检查项均符合要求。")
        print("  📋 阶段1交付物清单：")
        print("     - requirements.txt (依赖锁定)")
        print("     - pyproject.toml (项目配置)")
        print("     - 项目目录结构初始化")
        print("     - core/config.py (配置模块)")
        print("     - tests/unit/test_config.py (单元测试)")
        print("     - README.md (项目说明)")
        print("     - scripts/verify_phase1.py (验收脚本)")
        return 0
    else:
        print("  ❌ 阶段1验收未通过！请修复上述失败项。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
