#!/usr/bin/env python3
"""阶段7验收验证脚本."""

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
    print_header("阶段7验收验证 - 接入AST语法树遍历工具")
    
    all_passed = True
    project_root = Path(__file__).parent.parent
    
    # 1. ast模块检查
    print_header("1. Python标准库ast模块检查")
    
    import ast
    all_passed = print_result("ast模块可用", True) and all_passed
    all_passed = print_result("ast.parse可用", True) and all_passed
    all_passed = print_result("ast.walk可用", True) and all_passed
    all_passed = print_result("ast.get_docstring可用", True) and all_passed
    all_passed = print_result("ast.FunctionDef可用", True) and all_passed
    all_passed = print_result("ast.ClassDef可用", True) and all_passed
    all_passed = print_result("ast.AsyncFunctionDef可用", True) and all_passed
    
    # 2. ASTWalker模块检查
    print_header("2. ASTWalker模块检查")
    
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.atomicity.ast_walker import (
            ASTWalker, ASTNodeInfo,
        )
        
        all_passed = print_result("ASTWalker模块可导入", True) and all_passed
        
        test_source = '''import os
from typing import List, Optional

class MyClass:
    """A test class."""
    
    MAX_SIZE: int = 100
    
    def __init__(self, name: str, items: Optional[List[str]] = None):
        self.name = name
        self._items: List[str] = items or []
    
    @property
    def count(self) -> int:
        return len(self._items)
    
    def add_item(self, item: str) -> None:
        self._items.append(item)
    
    async def async_process(self) -> None:
        pass

def helper(x: int = 0) -> int:
    result = [i * 2 for i in range(x)]
    return sum(result)
'''
        
        walker = ASTWalker(test_source)
        all_passed = print_result("ASTWalker创建成功", True) and all_passed
        all_passed = print_result("tree属性可用", walker.tree is not None) and all_passed
        
        # 函数查询
        func_names = walker.get_function_names()
        all_passed = print_result("get_function_names可用", len(func_names) >= 4) and all_passed
        all_passed = print_result("包含helper", "helper" in func_names) and all_passed
        
        # 异步函数
        async_funcs = walker.get_async_functions()
        all_passed = print_result("get_async_functions可用", len(async_funcs) >= 1) and all_passed
        all_passed = print_result("包含async_process", any(f.name == "async_process" for f in async_funcs)) and all_passed
        
        # 类查询
        class_names = walker.get_class_names()
        all_passed = print_result("get_class_names可用", class_names == ["MyClass"]) and all_passed
        
        # 类方法
        methods = walker.get_class_methods("MyClass")
        all_passed = print_result("get_class_methods可用", len(methods) >= 3) and all_passed
        method_names = [m.name for m in methods]
        all_passed = print_result("包含add_item", "add_item" in method_names) and all_passed
        
        # 导入
        imports = walker.get_imports()
        all_passed = print_result("get_imports可用", len(imports) >= 2) and all_passed
        
        # 类型注解
        annotations = walker.get_type_annotations()
        all_passed = print_result("get_type_annotations可用", len(annotations) >= 2) and all_passed
        has_return_type = any("return" in a["annotations"] for a in annotations)
        all_passed = print_result("包含返回类型注解", has_return_type) and all_passed
        
        # 装饰器
        decorators = walker.get_decorators()
        all_passed = print_result("get_decorators可用", len(decorators) >= 1) and all_passed
        
        # 推导式
        comprehensions = walker.get_comprehensions()
        all_passed = print_result("get_comprehensions可用", len(comprehensions) >= 1) and all_passed
        
        # 类变量
        class_vars = walker.get_class_variables("MyClass")
        all_passed = print_result("get_class_variables可用", len(class_vars) >= 1) and all_passed
        has_max_size = any(v["name"] == "MAX_SIZE" for v in class_vars)
        all_passed = print_result("包含MAX_SIZE", has_max_size) and all_passed
        
        # AST统计
        stats = walker.get_stats()
        all_passed = print_result("get_stats可用", True) and all_passed
        all_passed = print_result("函数数正确", stats["functions"] >= 4) and all_passed
        all_passed = print_result("类数正确", stats["classes"] == 1) and all_passed
        all_passed = print_result("总节点数>0", stats["total_nodes"] > 0) and all_passed
        all_passed = print_result("导入数正确", stats["imports"] >= 2) and all_passed
        all_passed = print_result("装饰器数正确", stats["decorators"] >= 1) and all_passed
        
        # 节点类型
        all_types = walker.get_all_node_types()
        all_passed = print_result("get_all_node_types可用", len(all_types) > 10) and all_passed
        
        # walk_by_type
        assigns = walker.walk_by_type(ast.Assign)
        all_passed = print_result("walk_by_type可用", len(assigns) >= 1) and all_passed
        
        # get_node_info
        node_info = walker.get_node_info(walker.walk_by_type(ast.ClassDef)[0])
        all_passed = print_result("get_node_info可用", node_info.name == "MyClass") and all_passed
        all_passed = print_result("节点信息包含docstring", node_info.docstring == "A test class.") and all_passed
        
        # dump
        dump_str = walker.dump()
        all_passed = print_result("dump可用", len(dump_str) > 0) and all_passed
        
    except Exception as e:
        all_passed = print_result("ASTWalker模块", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()
    
    # 3. 文件解析检查
    print_header("3. 文件解析检查")
    
    try:
        config_file = project_root / "src" / "multi_agent_se" / "core" / "config.py"
        if config_file.exists():
            walker = ASTWalker.from_file(str(config_file))
            all_passed = print_result("from_file可用", True) and all_passed
            file_funcs = walker.get_function_names()
            all_passed = print_result("文件函数查询可用", len(file_funcs) >= 2) and all_passed
        else:
            all_passed = print_result("from_file可用", False, "文件不存在") and all_passed
    except Exception as e:
        all_passed = print_result("文件解析", False, str(e)) and all_passed
    
    # 4. 文件结构检查
    print_header("4. 文件结构检查")
    
    required_files = ["src/multi_agent_se/atomicity/ast_walker.py"]
    for file_path in required_files:
        full_path = project_root / file_path
        all_passed = print_result(
            f"文件: {file_path}", full_path.exists(),
            "存在" if full_path.exists() else "不存在"
        ) and all_passed
    
    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段7验收通过！所有检查项均符合要求。")
        print("  📋 阶段7交付物清单：")
        print("     - ast_walker.py (AST遍历器/语义分析)")
        print("     - 能力: 函数/类/方法/导入/类型注解/装饰器/推导式/类变量")
        print("     - 与Tree-sitter互补: ast擅长Python语义分析")
        print("     - scripts/verify_phase7.py (验收脚本)")
        return 0
    else:
        print("  ❌ 阶段7验收未通过！请修复上述失败项。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
