"""隐式状态扫描工具 - 阶段14.

扫描代码中的隐式状态：
- 模块级可变全局变量
- 类级可变类变量
- 函数默认参数中的可变对象
- 单例模式中的状态
"""

import ast
import inspect
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type


class ImplicitStateType(Enum):
    """隐式状态类型."""
    MODULE_GLOBAL = auto()      # 模块级全局变量
    CLASS_VARIABLE = auto()     # 类级可变变量
    MUTABLE_DEFAULT = auto()    # 可变默认参数
    SINGLETON_STATE = auto()    # 单例状态
    THREAD_LOCAL = auto()       # 线程本地存储
    CONTEXT_VAR = auto()        # 上下文变量


@dataclass
class ImplicitState:
    """隐式状态记录."""
    name: str
    state_type: ImplicitStateType
    file_path: str
    line_number: int
    description: str = ""
    suggested_fix: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.state_type.name,
            "file": self.file_path,
            "line": self.line_number,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class ScanResult:
    """扫描结果."""
    implicit_states: List[ImplicitState] = field(default_factory=list)
    scanned_files: int = 0
    scanned_lines: int = 0
    
    @property
    def total_issues(self) -> int:
        return len(self.implicit_states)
    
    @property
    def issues_by_type(self) -> Dict[str, List[ImplicitState]]:
        grouped: Dict[str, List[ImplicitState]] = {}
        for state in self.implicit_states:
            key = state.state_type.name
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(state)
        return grouped
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_issues": self.total_issues,
            "scanned_files": self.scanned_files,
            "scanned_lines": self.scanned_lines,
            "issues_by_type": {
                k: len(v) for k, v in self.issues_by_type.items()
            },
            "issues": [s.to_dict() for s in self.implicit_states],
        }


class StateScanner:
    """隐式状态扫描器.
    
    通过AST分析扫描Python源码中的隐式状态
    """
    
    # 常见的可变类型
    MUTABLE_TYPES: Set[str] = {
        "list", "dict", "set", "defaultdict", "OrderedDict",
        "Counter", "deque", "ChainMap",
    }
    
    # 常见的单例模式标识
    SINGLETON_PATTERNS: Set[str] = {
        "_instance", "__instance", "_singleton", "instance",
    }
    
    def __init__(self) -> None:
        """初始化扫描器."""
        self._results: List[ImplicitState] = []
        self._scanned_files = 0
        self._scanned_lines = 0
    
    def scan_file(self, file_path: str) -> List[ImplicitState]:
        """扫描单个文件.
        
        Args:
            file_path: 文件路径
            
        Returns:
            发现的隐式状态列表
        """
        path = Path(file_path)
        if not path.exists() or not path.suffix == ".py":
            return []
        
        try:
            source = path.read_text(encoding="utf-8")
            self._scanned_lines += len(source.splitlines())
        except Exception:
            return []
        
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        
        self._scanned_files += 1
        issues: List[ImplicitState] = []
        
        # 扫描模块级全局变量
        issues.extend(self._scan_module_globals(tree, str(path)))
        
        # 扫描类定义
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                issues.extend(self._scan_class_variables(node, str(path)))
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                issues.extend(self._scan_function_defaults(node, str(path)))
        
        self._results.extend(issues)
        return issues
    
    def _scan_module_globals(
        self,
        tree: ast.Module,
        file_path: str,
    ) -> List[ImplicitState]:
        """扫描模块级全局可变变量."""
        issues: List[ImplicitState] = []
        
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # 检查是否是可变类型
                        if self._is_mutable_assignment(node.value):
                            # 排除全大写的常量
                            if not target.id.isupper():
                                issues.append(ImplicitState(
                                    name=target.id,
                                    state_type=ImplicitStateType.MODULE_GLOBAL,
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    description=f"模块级可变全局变量: {target.id}",
                                    suggested_fix=f"将 {target.id} 移到显式状态注册表中管理",
                                ))
        
        return issues
    
    def _scan_class_variables(
        self,
        node: ast.ClassDef,
        file_path: str,
    ) -> List[ImplicitState]:
        """扫描类级可变变量."""
        issues: List[ImplicitState] = []
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # 先检查是否是单例模式（不限制类型）
                        if target.id in self.SINGLETON_PATTERNS:
                            issues.append(ImplicitState(
                                name=f"{node.name}.{target.id}",
                                state_type=ImplicitStateType.SINGLETON_STATE,
                                file_path=file_path,
                                line_number=item.lineno,
                                description=f"单例状态: {node.name}.{target.id}",
                                suggested_fix="使用显式注册表管理单例实例",
                            ))
                        # 再检查是否是可变类型
                        elif self._is_mutable_assignment(item.value):
                            issues.append(ImplicitState(
                                name=f"{node.name}.{target.id}",
                                state_type=ImplicitStateType.CLASS_VARIABLE,
                                file_path=file_path,
                                line_number=item.lineno,
                                description=f"类级可变变量: {node.name}.{target.id}",
                                suggested_fix="考虑使用实例变量或显式状态管理",
                            ))
        
        return issues
    
    def _scan_function_defaults(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        file_path: str,
    ) -> List[ImplicitState]:
        """扫描函数默认参数中的可变对象."""
        issues: List[ImplicitState] = []
        
        for default in node.args.defaults + node.args.kw_defaults:
            if default is None:
                continue
            if self._is_mutable_assignment(default):
                issues.append(ImplicitState(
                    name=node.name,
                    state_type=ImplicitStateType.MUTABLE_DEFAULT,
                    file_path=file_path,
                    line_number=node.lineno,
                    description=f"函数 {node.name} 使用可变默认参数",
                    suggested_fix="使用 None 作为默认值，在函数体内初始化",
                ))
                break  # 一个函数只报告一次
        
        return issues
    
    def _is_mutable_assignment(self, node: Optional[ast.expr]) -> bool:
        """检查赋值是否是可变类型."""
        if node is None:
            return False
        
        # 直接构造 list/dict/set
        if isinstance(node, (ast.List, ast.Dict, ast.Set)):
            return True
        
        # 调用构造函数
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id in self.MUTABLE_TYPES
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr in self.MUTABLE_TYPES
        
        return False
    
    def scan_directory(
        self,
        directory: str,
        pattern: str = "*.py",
    ) -> ScanResult:
        """扫描目录.
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            
        Returns:
            ScanResult
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return ScanResult()
        
        for py_file in sorted(dir_path.rglob(pattern)):
            self.scan_file(str(py_file))
        
        return ScanResult(
            implicit_states=self._results,
            scanned_files=self._scanned_files,
            scanned_lines=self._scanned_lines,
        )
    
    def scan_module(self, module: Type) -> List[ImplicitState]:
        """扫描已加载的模块.
        
        Args:
            module: 模块对象
            
        Returns:
            隐式状态列表
        """
        try:
            file_path = inspect.getfile(module)
            return self.scan_file(file_path)
        except (TypeError, ValueError):
            return []
    
    def clear(self) -> None:
        """清空扫描结果."""
        self._results.clear()
        self._scanned_files = 0
        self._scanned_lines = 0


def scan_module(module: Type) -> List[ImplicitState]:
    """便捷函数：扫描模块.
    
    Args:
        module: 模块对象
        
    Returns:
        隐式状态列表
    """
    scanner = StateScanner()
    return scanner.scan_module(module)
