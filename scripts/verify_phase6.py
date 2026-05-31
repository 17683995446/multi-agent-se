#!/usr/bin/env python3
"""阶段6验收验证脚本."""

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
    print_header("阶段6验收验证 - 接入Tree-sitter跨语言代码解析底座")
    
    all_passed = True
    project_root = Path(__file__).parent.parent
    
    # 1. Tree-sitter安装检查
    print_header("1. Tree-sitter安装检查")
    
    try:
        import tree_sitter as ts
        all_passed = print_result("tree_sitter已安装", True) and all_passed
        all_passed = print_result("Parser可用", hasattr(ts, 'Parser')) and all_passed
        all_passed = print_result("Query可用", hasattr(ts, 'Query')) and all_passed
        all_passed = print_result("QueryCursor可用", hasattr(ts, 'QueryCursor')) and all_passed
    except ImportError as e:
        all_passed = print_result("tree_sitter已安装", False, str(e)) and all_passed
    
    try:
        import tree_sitter_python as tspython
        all_passed = print_result("tree_sitter_python已安装", True) and all_passed
    except ImportError as e:
        all_passed = print_result("tree_sitter_python", False, str(e)) and all_passed
    
    # 2. 解析器管理模块检查
    print_header("2. 解析器管理模块检查")
    
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.atomicity.parser_manager import (
            ParserManager, ParseResult, NodeInfo, parser_manager,
        )
        
        all_passed = print_result("parser_manager模块可导入", True) and all_passed
        
        # 解析测试
        source = 'def hello():\n    return "world"'
        result = parser_manager.parse(source)
        all_passed = print_result("parse可用", True) and all_passed
        all_passed = print_result("根节点类型正确", result.root_node.type == "module") and all_passed
        all_passed = print_result("get_source_text可用", result.get_source_text(result.root_node) == source) and all_passed
        
        # 语言支持
        langs = parser_manager.get_supported_languages()
        all_passed = print_result("Python语言已注册", "python" in langs) and all_passed
        
        # 不支持语言
        try:
            parser_manager.parse(source, "unsupported")
            all_passed = print_result("不支持语言抛异常", False) and all_passed
        except ValueError:
            all_passed = print_result("不支持语言抛异常", True) and all_passed
        
    except Exception as e:
        all_passed = print_result("parser_manager模块", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()
    
    # 3. AST查询接口检查
    print_header("3. AST查询接口检查")
    
    try:
        from multi_agent_se.atomicity.ast_query import (
            ASTQuery, create_query, walk_tree, collect_nodes, get_node_info,
        )
        
        all_passed = print_result("ast_query模块可导入", True) and all_passed
        
        # 使用复杂源码测试
        test_source = '''import os
from typing import List

class MyClass:
    """A test class."""
    
    def __init__(self, name: str):
        self.name = name
        self._items: List[str] = []
    
    def add_item(self, item: str) -> None:
        self._items.append(item)
    
    def get_items(self) -> List[str]:
        return list(self._items)

def helper_function(x: int) -> int:
    return x * 2

def main():
    obj = MyClass("test")
    obj.add_item("hello")
    items = obj.get_items()
    return items
'''
        
        query = create_query(test_source)
        
        # 函数查询
        func_names = query.get_function_names()
        all_passed = print_result("get_function_names可用", len(func_names) >= 2) and all_passed
        all_passed = print_result("函数名正确", "helper_function" in func_names and "main" in func_names) and all_passed
        
        # 类查询
        class_names = query.get_class_names()
        all_passed = print_result("get_class_names可用", class_names == ["MyClass"]) and all_passed
        
        # 类方法查询
        methods = query.get_class_methods("MyClass")
        all_passed = print_result("get_class_methods可用", len(methods) == 3) and all_passed
        method_names = [m.text.split("(")[0].strip().split()[-1] for m in methods]
        all_passed = print_result("方法名正确", "add_item" in method_names and "get_items" in method_names) and all_passed
        
        # 导入查询
        imports = query.get_imports()
        all_passed = print_result("get_imports可用", len(imports) >= 1) and all_passed
        
        # 变量查询
        var_names = query.get_variable_names()
        all_passed = print_result("get_variable_names可用", True) and all_passed
        
        # 自定义查询
        custom = query.query("(return_statement) @ret")
        ret_nodes = custom.get("ret", [])
        all_passed = print_result("自定义query可用", len(ret_nodes) >= 2) and all_passed
        
        # AST统计
        stats = query.get_tree_stats()
        all_passed = print_result("get_tree_stats可用", True) and all_passed
        all_passed = print_result("统计函数数正确", stats["functions"] >= 2) and all_passed
        all_passed = print_result("统计类数正确", stats["classes"] == 1) and all_passed
        all_passed = print_result("总节点数>0", stats["total_nodes"] > 0) and all_passed
        
        # 节点类型
        all_types = query.get_all_node_types()
        all_passed = print_result("get_all_node_types可用", len(all_types) > 5) and all_passed
        
        # walk_tree
        visited = []
        walk_tree(query._root, lambda n, d: visited.append(n.type))
        all_passed = print_result("walk_tree可用", len(visited) > 10) and all_passed
        
        # collect_nodes
        fn_nodes = collect_nodes(query._root, "function_definition")
        all_passed = print_result("collect_nodes可用", len(fn_nodes) >= 2) and all_passed
        
    except Exception as e:
        all_passed = print_result("ast_query模块", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()
    
    # 4. 文件解析检查
    print_header("4. 文件解析检查")
    
    try:
        # 解析自身文件
        config_file = project_root / "src" / "multi_agent_se" / "core" / "config.py"
        if config_file.exists():
            result = parser_manager.parse_file(str(config_file))
            all_passed = print_result("parse_file可用", True) and all_passed
            all_passed = print_result("文件解析根节点正确", result.root_node.type == "module") and all_passed
            
            file_query = ASTQuery(result)
            file_funcs = file_query.get_function_names()
            all_passed = print_result("文件函数查询可用", len(file_funcs) >= 2) and all_passed
        else:
            all_passed = print_result("parse_file可用", False, "config.py不存在") and all_passed
    except Exception as e:
        all_passed = print_result("文件解析", False, str(e)) and all_passed
    
    # 5. 文件结构检查
    print_header("5. 文件结构检查")
    
    required_files = [
        "src/multi_agent_se/atomicity/parser_manager.py",
        "src/multi_agent_se/atomicity/ast_query.py",
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        all_passed = print_result(
            f"文件: {file_path}",
            full_path.exists(),
            "存在" if full_path.exists() else "不存在"
        ) and all_passed
    
    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段6验收通过！所有检查项均符合要求。")
        print("  📋 阶段6交付物清单：")
        print("     - parser_manager.py (解析器管理/多语言支持/文件解析)")
        print("     - ast_query.py (AST遍历/查询/统计)")
        print("     - 查询能力: 函数/类/方法/导入/变量/装饰器/自定义")
        print("     - scripts/verify_phase6.py (验收脚本)")
        return 0
    else:
        print("  ❌ 阶段6验收未通过！请修复上述失败项。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
