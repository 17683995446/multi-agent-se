"""AST遍历器模块 - 阶段7.

封装Python标准库ast模块，提供统一AST遍历接口
与Tree-sitter互补：ast更擅长Python语义分析（类型注解、装饰器、推导式等）
"""

import ast
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ASTNodeInfo:
    """AST节点信息."""
    node_type: str
    name: str = ""
    lineno: int = 0
    col_offset: int = 0
    end_lineno: int = 0
    end_col_offset: int = 0
    parent_type: Optional[str] = None
    children_count: int = 0
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    annotations: Dict[str, str] = field(default_factory=dict)
    source_text: str = ""


class ASTWalker:
    """AST遍历器.
    
    提供统一的AST遍历与分析接口
    """
    
    def __init__(self, source: str) -> None:
        """初始化遍历器.
        
        Args:
            source: Python源码
        """
        self._source = source
        self._tree = ast.parse(source)
        self._lines = source.splitlines()
    
    @classmethod
    def from_file(cls, file_path: str) -> "ASTWalker":
        """从文件创建遍历器.
        
        Args:
            file_path: 文件路径
            
        Returns:
            ASTWalker实例
        """
        source = Path(file_path).read_text(encoding="utf-8")
        return cls(source)
    
    @property
    def tree(self) -> ast.Module:
        """获取AST树."""
        return self._tree
    
    @property
    def source(self) -> str:
        """获取源码."""
        return self._source
    
    # ========== 基础遍历 ==========
    
    def walk(
        self,
        node_filter: Optional[Callable[[ast.AST], bool]] = None,
    ) -> List[ast.AST]:
        """遍历AST节点.
        
        Args:
            node_filter: 节点过滤函数
            
        Returns:
            节点列表
        """
        nodes = []
        for node in ast.walk(self._tree):
            if node_filter is None or node_filter(node):
                nodes.append(node)
        return nodes
    
    def walk_by_type(self, node_type: Type[ast.AST]) -> List[ast.AST]:
        """按类型遍历.
        
        Args:
            node_type: AST节点类型
            
        Returns:
            匹配的节点列表
        """
        return [n for n in ast.walk(self._tree) if isinstance(n, node_type)]
    
    def get_node_info(self, node: ast.AST) -> ASTNodeInfo:
        """获取节点详细信息.
        
        Args:
            node: AST节点
            
        Returns:
            ASTNodeInfo
        """
        info = ASTNodeInfo(
            node_type=type(node).__name__,
            lineno=getattr(node, 'lineno', 0),
            col_offset=getattr(node, 'col_offset', 0),
            end_lineno=getattr(node, 'end_lineno', 0),
            end_col_offset=getattr(node, 'end_col_offset', 0),
        )
        
        # 名称
        if hasattr(node, 'name'):
            info.name = node.name
        elif hasattr(node, 'id'):
            info.name = node.id
        elif hasattr(node, 'attr'):
            info.name = node.attr
        
        # 源码文本
        if info.lineno > 0 and info.end_lineno > 0:
            if info.lineno == info.end_lineno:
                line = self._lines[info.lineno - 1] if info.lineno <= len(self._lines) else ""
                info.source_text = line[info.col_offset:info.end_col_offset]
            else:
                lines = []
                for i in range(info.lineno - 1, min(info.end_lineno, len(self._lines))):
                    lines.append(self._lines[i])
                info.source_text = "\n".join(lines)
        
        # 子节点数
        info.children_count = len(list(ast.iter_child_nodes(node)))
        
        # 装饰器
        if hasattr(node, 'decorator_list'):
            info.decorators = [ast.dump(d) for d in node.decorator_list]
        
        # 文档字符串
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            info.docstring = ast.get_docstring(node)
        
        return info
    
    # ========== 快捷查询 ==========
    
    def get_functions(self) -> List[ASTNodeInfo]:
        """获取所有函数（含异步函数）."""
        nodes = self.walk_by_type(ast.FunctionDef) + self.walk_by_type(ast.AsyncFunctionDef)
        return [self.get_node_info(n) for n in nodes]
    
    def get_function_names(self) -> List[str]:
        """获取所有函数名."""
        return [n.name for n in self.walk_by_type(ast.FunctionDef)]
    
    def get_async_functions(self) -> List[ASTNodeInfo]:
        """获取异步函数."""
        nodes = self.walk_by_type(ast.AsyncFunctionDef)
        return [self.get_node_info(n) for n in nodes]
    
    def get_classes(self) -> List[ASTNodeInfo]:
        """获取所有类."""
        nodes = self.walk_by_type(ast.ClassDef)
        return [self.get_node_info(n) for n in nodes]
    
    def get_class_names(self) -> List[str]:
        """获取所有类名."""
        return [n.name for n in self.walk_by_type(ast.ClassDef)]
    
    def get_class_methods(self, class_name: str) -> List[ASTNodeInfo]:
        """获取指定类的方法."""
        for cls in self.walk_by_type(ast.ClassDef):
            if cls.name == class_name:
                methods = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                return [self.get_node_info(m) for m in methods]
        return []
    
    def get_imports(self) -> List[Dict[str, Any]]:
        """获取所有导入."""
        result = []
        for node in self.walk_by_type(ast.Import):
            for alias in node.names:
                result.append({"type": "import", "module": alias.name, "alias": alias.asname})
        for node in self.walk_by_type(ast.ImportFrom):
            names = [{"name": a.name, "alias": a.asname} for a in node.names]
            result.append({"type": "from", "module": node.module, "names": names, "level": node.level})
        return result
    
    def get_class_variables(self, class_name: str) -> List[Dict[str, Any]]:
        """获取类变量（含类型注解）."""
        for cls in self.walk_by_type(ast.ClassDef):
            if cls.name == class_name:
                variables = []
                for node in cls.body:
                    if isinstance(node, ast.AnnAssign):
                        var_name = node.target.id if isinstance(node.target, ast.Name) else "?"
                        annotation = ast.dump(node.annotation) if node.annotation else None
                        variables.append({
                            "name": var_name,
                            "annotation": annotation,
                            "value": ast.dump(node.value) if node.value else None,
                            "lineno": node.lineno,
                        })
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                variables.append({
                                    "name": target.id,
                                    "annotation": None,
                                    "value": ast.dump(node.value),
                                    "lineno": node.lineno,
                                })
                return variables
        return []
    
    def get_type_annotations(self) -> List[Dict[str, Any]]:
        """获取所有类型注解."""
        annotations = []
        for func in self.walk_by_type(ast.FunctionDef) + self.walk_by_type(ast.AsyncFunctionDef):
            func_annotations = {}
            for arg in func.args.args:
                if arg.annotation:
                    func_annotations[arg.arg] = ast.dump(arg.annotation)
            if func.args.vararg and func.args.vararg.annotation:
                func_annotations[f"*{func.args.vararg.arg}"] = ast.dump(func.args.vararg.annotation)
            if func.args.kwarg and func.args.kwarg.annotation:
                func_annotations[f"**{func.args.kwarg.arg}"] = ast.dump(func.args.kwarg.annotation)
            if func.returns:
                func_annotations["return"] = ast.dump(func.returns)
            
            if func_annotations:
                annotations.append({
                    "function": func.name,
                    "annotations": func_annotations,
                    "lineno": func.lineno,
                })
        return annotations
    
    def get_decorators(self) -> List[Dict[str, Any]]:
        """获取所有装饰器."""
        result = []
        for node in self.walk_by_type(ast.FunctionDef) + self.walk_by_type(ast.AsyncFunctionDef) + self.walk_by_type(ast.ClassDef):
            for dec in node.decorator_list:
                result.append({
                    "target": node.name,
                    "target_type": type(node).__name__,
                    "decorator": ast.dump(dec),
                    "lineno": dec.lineno,
                })
        return result
    
    def get_comprehensions(self) -> List[Dict[str, Any]]:
        """获取推导式."""
        result = []
        comp_types = {
            ast.ListComp: "list_comp",
            ast.SetComp: "set_comp",
            ast.DictComp: "dict_comp",
            ast.GeneratorExp: "generator_exp",
        }
        for comp_type, comp_name in comp_types.items():
            for node in self.walk_by_type(comp_type):
                result.append({
                    "type": comp_name,
                    "lineno": getattr(node, 'lineno', 0),
                    "dump": ast.dump(node),
                })
        return result
    
    def get_all_node_types(self) -> Set[str]:
        """获取所有节点类型."""
        return {type(n).__name__ for n in ast.walk(self._tree)}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取AST统计信息."""
        type_counts: Dict[str, int] = {}
        for node in ast.walk(self._tree):
            t = type(node).__name__
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "total_nodes": sum(type_counts.values()),
            "unique_types": len(type_counts),
            "type_distribution": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
            "functions": len(self.walk_by_type(ast.FunctionDef)),
            "async_functions": len(self.walk_by_type(ast.AsyncFunctionDef)),
            "classes": len(self.walk_by_type(ast.ClassDef)),
            "imports": len(self.walk_by_type(ast.Import)) + len(self.walk_by_type(ast.ImportFrom)),
            "decorators": len(self.get_decorators()),
            "comprehensions": len(self.get_comprehensions()),
            "type_annotations": len(self.get_type_annotations()),
            "lines_of_code": len(self._lines),
        }
    
    def dump(self) -> str:
        """导出AST为字符串."""
        return ast.dump(self._tree, indent=2)
