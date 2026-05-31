"""方法原子模型 - 阶段29.

第二级代码原子化：方法原子（Method Atom）

封装单个方法/函数的完整信息：
- 名称、签名、参数列表、返回类型
- 文档字符串和装饰器
- 调用关系（调用者和被调用者）
- 复杂度指标（圈复杂度、参数数量、行数）
- 所属类/模块信息
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ========== 枚举定义 ==========

class MethodType(Enum):
    """方法类型."""
    FUNCTION = "function"             # 模块级函数
    METHOD = "method"                 # 实例方法
    CLASSMETHOD = "classmethod"       # 类方法
    STATICMETHOD = "staticmethod"     # 静态方法
    ASYNC_FUNCTION = "async_function"  # 异步函数
    ASYNC_METHOD = "async_method"     # 异步方法
    PROPERTY = "property"             # 属性方法
    LAMBDA = "lambda"                 # lambda表达式
    NESTED = "nested"                 # 嵌套函数
    MAGIC = "magic"                   # 魔术方法（__x__）


class MethodVisibility(Enum):
    """方法可见性."""
    PUBLIC = "public"         # 公开方法
    PROTECTED = "protected"   # 保护方法（单下划线）
    PRIVATE = "private"       # 私有方法（双下划线）
    MAGIC = "magic"           # 魔术方法（__x__）


# ========== 数据类 ==========

@dataclass
class ParameterInfo:
    """参数信息."""
    name: str = ""
    type_annotation: str = ""
    default_value: str = ""
    has_default: bool = False
    kind: str = "positional"  # positional/keyword/vararg/kwonly/varkeyword
    position: int = 0         # 参数位置索引

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type_annotation": self.type_annotation,
            "default_value": self.default_value,
            "has_default": self.has_default,
            "kind": self.kind,
            "position": self.position,
        }


@dataclass
class CallRelation:
    """调用关系."""
    target_name: str = ""           # 被调用方法/函数名
    target_class: str = ""          # 被调用方法所属类（如果是方法调用）
    location_line: int = 0          # 调用位置行号
    is_external: bool = False       # 是否为外部调用（非本项目定义）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_name": self.target_name,
            "target_class": self.target_class,
            "location_line": self.location_line,
            "is_external": self.is_external,
        }


@dataclass
class ComplexityMetrics:
    """复杂度指标."""
    cyclomatic_complexity: int = 1     # 圈复杂度
    line_count: int = 0                 # 行数（不含空行和注释）
    parameter_count: int = 0            # 参数数量
    return_statement_count: int = 0     # return语句数量
    branch_count: int = 0               # 分支数量（if/for/while/try/except）
    nesting_depth: int = 0              # 最大嵌套深度
    local_variable_count: int = 0       # 局部变量数量
    call_count: int = 0                 # 调用其他函数/方法的次数

    @property
    def is_simple(self) -> bool:
        """是否为简单方法（圈复杂度<=5，参数<=4，行数<=20）."""
        return (
            self.cyclomatic_complexity <= 5
            and self.parameter_count <= 4
            and self.line_count <= 20
        )

    @property
    def is_complex(self) -> bool:
        """是否为复杂方法（圈复杂度>10 或 行数>50）."""
        return (
            self.cyclomatic_complexity > 10
            or self.line_count > 50
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "line_count": self.line_count,
            "parameter_count": self.parameter_count,
            "return_statement_count": self.return_statement_count,
            "branch_count": self.branch_count,
            "nesting_depth": self.nesting_depth,
            "local_variable_count": self.local_variable_count,
            "call_count": self.call_count,
            "is_simple": self.is_simple,
            "is_complex": self.is_complex,
        }


@dataclass
class MethodAtom:
    """方法原子.

    封装单个方法/函数的完整信息，是四级原子化体系的第二级。
    每个方法原子代表代码中一个独立的函数/方法实体。
    """
    # 基础信息
    name: str = ""
    atom_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    method_type: MethodType = MethodType.FUNCTION
    visibility: MethodVisibility = MethodVisibility.PUBLIC
    is_async: bool = False

    # 签名信息
    parameters: List[ParameterInfo] = field(default_factory=list)
    return_type: str = ""
    signature: str = ""            # 完整签名字符串

    # 文档信息
    docstring: str = ""
    decorators: List[str] = field(default_factory=list)

    # 位置信息
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    col_start: int = 0

    # 调用关系
    calls: List[CallRelation] = field(default_factory=list)       # 调用了哪些方法
    called_by: List[str] = field(default_factory=list)            # 被哪些方法调用

    # 复杂度
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)

    # 所属信息
    class_name: str = ""           # 所属类名（空则为模块级函数）
    module_name: str = ""          # 所属模块名

    # 元数据
    is_abstract: bool = False      # 是否为抽象方法
    is_override: bool = False      # 是否为重写方法
    is_deprecated: bool = False    # 是否已废弃
    exceptions_raised: List[str] = field(default_factory=list)   # 抛出的异常类型
    exceptions_caught: List[str] = field(default_factory=list)   # 捕获的异常类型

    # ========== 属性 ==========

    @property
    def full_name(self) -> str:
        """完整限定名."""
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        if self.module_name:
            return f"{self.module_name}.{self.name}"
        return self.name

    @property
    def qualified_name(self) -> str:
        """带模块的完整限定名."""
        parts = []
        if self.module_name:
            parts.append(self.module_name)
        if self.class_name:
            parts.append(self.class_name)
        parts.append(self.name)
        return ".".join(parts)

    @property
    def parameter_names(self) -> List[str]:
        """参数名列表."""
        return [p.name for p in self.parameters]

    @property
    def required_parameter_count(self) -> int:
        """必需参数数量（无默认值的参数）."""
        return sum(1 for p in self.parameters if not p.has_default and p.kind in ("positional", "keyword"))

    @property
    def has_varargs(self) -> bool:
        """是否有可变参数（*args）."""
        return any(p.kind == "vararg" for p in self.parameters)

    @property
    def has_kwargs(self) -> bool:
        """是否有关键字可变参数（**kwargs）."""
        return any(p.kind == "varkeyword" for p in self.parameters)

    @property
    def call_targets(self) -> Set[str]:
        """调用的目标方法名集合."""
        return {c.target_name for c in self.calls}

    @property
    def is_magic_method(self) -> bool:
        """是否为魔术方法."""
        return self.name.startswith("__") and self.name.endswith("__") and len(self.name) > 4

    @property
    def is_dunder(self) -> bool:
        """是否为双下划线方法."""
        return self.is_magic_method

    @property
    def is_private(self) -> bool:
        """是否为私有方法."""
        return self.visibility in (MethodVisibility.PRIVATE, MethodVisibility.MAGIC)

    @property
    def needs_refactoring(self) -> bool:
        """是否需要重构（复杂方法）."""
        return self.complexity.is_complex

    # ========== 方法 ==========

    def add_call(self, target_name: str, line: int = 0, target_class: str = "") -> None:
        """添加调用关系.

        Args:
            target_name: 被调用方法名
            line: 调用位置行号
            target_class: 被调用方法所属类
        """
        relation = CallRelation(
            target_name=target_name,
            target_class=target_class,
            location_line=line,
        )
        self.calls.append(relation)

    def add_called_by(self, caller_name: str) -> None:
        """添加被调用关系.

        Args:
            caller_name: 调用者名称
        """
        if caller_name not in self.called_by:
            self.called_by.append(caller_name)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "atom_id": self.atom_id,
            "name": self.name,
            "full_name": self.full_name,
            "qualified_name": self.qualified_name,
            "method_type": self.method_type.value,
            "visibility": self.visibility.value,
            "is_async": self.is_async,
            "parameters": [p.to_dict() for p in self.parameters],
            "return_type": self.return_type,
            "signature": self.signature,
            "docstring": self.docstring[:200] if self.docstring else "",
            "decorators": self.decorators,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "calls": [c.to_dict() for c in self.calls],
            "called_by": self.called_by,
            "complexity": self.complexity.to_dict(),
            "class_name": self.class_name,
            "module_name": self.module_name,
            "is_abstract": self.is_abstract,
            "is_override": self.is_override,
            "is_magic_method": self.is_magic_method,
            "needs_refactoring": self.needs_refactoring,
            "exceptions_raised": self.exceptions_raised,
            "exceptions_caught": self.exceptions_caught,
        }

    def summary(self) -> str:
        """生成方法摘要."""
        parts = [f"方法: {self.full_name}"]
        if self.return_type:
            parts.append(f"返回: {self.return_type}")
        parts.append(f"复杂度: {self.complexity.cyclomatic_complexity}")
        parts.append(f"行数: {self.complexity.line_count}")
        if self.complexity.is_complex:
            parts.append("⚠ 需要重构")
        if self.calls:
            parts.append(f"调用: {len(self.calls)}个")
        return " | ".join(parts)
