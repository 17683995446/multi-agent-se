"""AST遍历与查询接口 - 阶段6.

复用Tree-sitter查询能力，封装统一AST遍历接口
为后续四级原子化体系（阶段21-30）提供基础
"""

from typing import Any, Callable, Dict, List, Optional, Set

import tree_sitter as ts
import tree_sitter_python as tspython

from multi_agent_se.atomicity.parser_manager import (
    ParserManager,
    ParseResult,
    NodeInfo,
    parser_manager,
)

# Python语言实例
PY_LANGUAGE = ts.Language(tspython.language())


# ========== AST遍历工具 ==========

def walk_tree(
    node: ts.Node,
    callback: Callable[[ts.Node, int], None],
    max_depth: int = 100,
) -> None:
    """递归遍历AST.
    
    Args:
        node: 起始节点
        callback: 回调函数(node, depth)
        max_depth: 最大深度
    """
    def _walk(n: ts.Node, depth: int) -> None:
        if depth > max_depth:
            return
        callback(n, depth)
        for child in n.children:
            _walk(child, depth + 1)
    
    _walk(node, 0)


def collect_nodes(
    node: ts.Node,
    node_type: Optional[str] = None,
    max_depth: int = 100,
) -> List[ts.Node]:
    """收集指定类型的所有节点.
    
    Args:
        node: 起始节点
        node_type: 节点类型（None则收集所有）
        max_depth: 最大深度
        
    Returns:
        节点列表
    """
    result: List[ts.Node] = []
    
    def _collect(n: ts.Node, depth: int) -> None:
        if depth > max_depth:
            return
        if node_type is None or n.type == node_type:
            result.append(n)
        for child in n.children:
            _collect(child, depth + 1)
    
    _collect(node, 0)
    return result


def get_node_info(node: ts.Node, source: bytes, parent_type: Optional[str] = None) -> NodeInfo:
    """获取节点信息.
    
    Args:
        node: AST节点
        source: 源码字节
        parent_type: 父节点类型
        
    Returns:
        NodeInfo
    """
    return NodeInfo(
        node_type=node.type,
        text=source[node.start_byte:node.end_byte].decode("utf-8", errors="replace"),
        start_line=node.start_point[0] + 1,
        start_col=node.start_point[1],
        end_line=node.end_point[0] + 1,
        end_col=node.end_point[1],
        children_count=node.child_count,
        parent_type=parent_type,
    )


# ========== 查询接口 ==========

class ASTQuery:
    """AST查询类.
    
    封装Tree-sitter查询能力，提供常用代码查询接口
    """
    
    def __init__(self, parse_result: ParseResult) -> None:
        """初始化查询.
        
        Args:
            parse_result: 解析结果
        """
        self.result = parse_result
        self._root = parse_result.root_node
        self._source = parse_result.source
        self._language = parser_manager._languages.get(parse_result.language, PY_LANGUAGE)
    
    def query(self, pattern: str) -> Dict[str, List[ts.Node]]:
        """执行自定义查询.
        
        Args:
            pattern: Tree-sitter查询模式
            
        Returns:
            {capture_name: [nodes]}
        """
        query = ts.Query(self._language, pattern)
        cursor = ts.QueryCursor(query)
        return cursor.captures(self._root)
    
    def query_matches(self, pattern: str) -> List[tuple]:
        """执行查询获取matches.
        
        Args:
            pattern: Tree-sitter查询模式
            
        Returns:
            matches列表
        """
        query = ts.Query(self._language, pattern)
        cursor = ts.QueryCursor(query)
        return cursor.matches(self._root)
    
    # ========== 常用查询快捷方法 ==========
    
    def get_functions(self) -> List[NodeInfo]:
        """获取所有函数定义."""
        captures = self.query("(function_definition) @func")
        nodes = captures.get("func", [])
        return [get_node_info(n, self._source) for n in nodes]
    
    def get_function_names(self) -> List[str]:
        """获取所有函数名."""
        captures = self.query("(function_definition name: (identifier) @name)")
        nodes = captures.get("name", [])
        return [self._source[n.start_byte:n.end_byte].decode() for n in nodes]
    
    def get_classes(self) -> List[NodeInfo]:
        """获取所有类定义."""
        captures = self.query("(class_definition) @cls")
        nodes = captures.get("cls", [])
        return [get_node_info(n, self._source) for n in nodes]
    
    def get_class_names(self) -> List[str]:
        """获取所有类名."""
        captures = self.query("(class_definition name: (identifier) @name)")
        nodes = captures.get("name", [])
        return [self._source[n.start_byte:n.end_byte].decode() for n in nodes]
    
    def get_class_methods(self, class_name: str) -> List[NodeInfo]:
        """获取指定类的所有方法."""
        pattern = f"(class_definition name: (identifier) @cls_name) @cls"
        captures = self.query(pattern)
        class_nodes = captures.get("cls", [])
        
        methods: List[NodeInfo] = []
        for cls_node in class_nodes:
            cls_text = self._source[cls_node.start_byte:cls_node.end_byte].decode()
            if class_name in cls_text:
                for child in cls_node.children:
                    if child.type == "block":
                        for item in child.children:
                            if item.type == "function_definition":
                                methods.append(get_node_info(item, self._source, "class"))
        return methods
    
    def get_imports(self) -> List[str]:
        """获取所有导入语句."""
        captures = self.query("(import_statement) @imp")
        nodes = captures.get("imp", [])
        return [self._source[n.start_byte:n.end_byte].decode().strip() for n in nodes]
    
    def get_variable_assignments(self) -> List[NodeInfo]:
        """获取所有变量赋值."""
        captures = self.query("(assignment left: (identifier) @var)")
        nodes = captures.get("var", [])
        return [get_node_info(n, self._source) for n in nodes]
    
    def get_variable_names(self) -> List[str]:
        """获取所有变量名."""
        captures = self.query("(assignment left: (identifier) @var)")
        nodes = captures.get("var", [])
        return [self._source[n.start_byte:n.end_byte].decode() for n in nodes]
    
    def get_decorators(self) -> List[str]:
        """获取所有装饰器."""
        captures = self.query("(decorator) @dec")
        nodes = captures.get("dec", [])
        return [self._source[n.start_byte:n.end_byte].decode().strip() for n in nodes]
    
    def get_all_node_types(self) -> Set[str]:
        """获取AST中所有节点类型."""
        types: Set[str] = set()
        walk_tree(self._root, lambda n, _: types.add(n.type))
        return types
    
    def get_node_count(self, node_type: Optional[str] = None) -> int:
        """获取节点数量."""
        return len(collect_nodes(self._root, node_type))
    
    def get_tree_stats(self) -> Dict[str, Any]:
        """获取AST统计信息."""
        all_types = self.get_all_node_types()
        type_counts: Dict[str, int] = {}
        for t in all_types:
            type_counts[t] = len(collect_nodes(self._root, t))
        
        return {
            "total_nodes": sum(type_counts.values()),
            "unique_types": len(all_types),
            "type_distribution": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
            "functions": len(self.get_function_names()),
            "classes": len(self.get_class_names()),
            "imports": len(self.get_imports()),
            "variables": len(self.get_variable_names()),
        }


def create_query(source: str, language: str = "python") -> ASTQuery:
    """快捷创建查询.
    
    Args:
        source: 源码
        language: 语言
        
    Returns:
        ASTQuery
    """
    result = parser_manager.parse(source, language)
    return ASTQuery(result)
