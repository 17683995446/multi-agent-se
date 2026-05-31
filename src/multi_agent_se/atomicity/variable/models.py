"""变量原子模型 - 阶段29.

第一级代码原子化：变量原子（Variable Atom）

封装单个变量的完整信息：
- 名称、类型注解、默认值
- 作用域（局部/全局/类属性/函数参数）
- 定义位置（文件/行/列）
- 引用位置列表
- 读写依赖关系
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ========== 枚举定义 ==========

class VariableScope(Enum):
    """变量作用域."""
    GLOBAL = "global"           # 模块级全局变量
    LOCAL = "local"             # 函数/方法内局部变量
    PARAMETER = "parameter"     # 函数/方法参数
    CLASS_ATTRIBUTE = "class_attribute"  # 类属性
    INSTANCE_ATTRIBUTE = "instance_attribute"  # 实例属性
    CLOSURE = "closure"         # 闭包捕获变量
    IMPORT = "import"           # 导入绑定


class VariableMutability(Enum):
    """变量可变性."""
    CONSTANT = "constant"       # 常量（全大写命名约定）
    READONLY = "readonly"       # 只读（无赋值操作）
    MUTABLE = "mutable"         # 可变（有赋值操作）
    UNKNOWN = "unknown"         # 未知


# ========== 数据类 ==========

@dataclass
class CodeLocation:
    """代码位置."""
    file_path: str = ""
    line: int = 0
    col: int = 0
    end_line: int = 0
    end_col: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line": self.line,
            "col": self.col,
            "end_line": self.end_line,
            "end_col": self.end_col,
        }

    def __str__(self) -> str:
        if self.file_path:
            return f"{self.file_path}:{self.line}:{self.col}"
        return f"line {self.line}, col {self.col}"


@dataclass
class VariableReference:
    """变量引用记录."""
    location: CodeLocation = field(default_factory=CodeLocation)
    context: str = ""           # 引用上下文（读/写/删除）
    scope_name: str = ""        # 所在作用域名称

    def to_dict(self) -> Dict[str, Any]:
        return {
            "location": self.location.to_dict(),
            "context": self.context,
            "scope_name": self.scope_name,
        }


@dataclass
class VariableAtom:
    """变量原子.

    封装单个变量的完整信息，是四级原子化体系的第一级。
    每个变量原子代表代码中一个独立的变量实体。
    """
    # 基础信息
    name: str = ""
    atom_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    scope: VariableScope = VariableScope.LOCAL
    mutability: VariableMutability = VariableMutability.UNKNOWN

    # 类型信息
    type_annotation: str = ""           # 类型注解字符串（如 "int", "List[str]"）
    inferred_type: str = ""             # 推断类型（如需要）
    default_value: str = ""             # 默认值表达式

    # 位置信息
    definition: CodeLocation = field(default_factory=CodeLocation)

    # 引用信息
    references: List[VariableReference] = field(default_factory=list)
    read_count: int = 0
    write_count: int = 0

    # 依赖信息
    dependencies: Set[str] = field(default_factory=set)   # 依赖的变量名
    dependents: Set[str] = field(default_factory=set)     # 被依赖的变量名

    # 所属容器
    container_name: str = ""   # 所属函数/类/模块名称
    container_type: str = ""   # 所属容器类型（function/class/module）

    # 元数据
    is_type_hint_only: bool = False    # 是否仅出现在类型注解中
    doc_comment: str = ""              # 行内文档注释

    # ========== 属性 ==========

    @property
    def full_name(self) -> str:
        """完整限定名（如 MyClass.my_attr 或 func.param）."""
        if self.container_name:
            return f"{self.container_name}.{self.name}"
        return self.name

    @property
    def is_constant(self) -> bool:
        """是否为常量（全大写命名）."""
        return self.name.isupper() and "_" in self.name

    @property
    def is_private(self) -> bool:
        """是否为私有变量（以下划线开头但不以双下划线开头）."""
        return self.name.startswith("_") and not self.name.startswith("__")

    @property
    def is_dunder(self) -> bool:
        """是否为双下划线特殊名称（__x__）."""
        return self.name.startswith("__") and self.name.endswith("__") and len(self.name) > 4

    @property
    def total_references(self) -> int:
        """总引用次数."""
        return self.read_count + self.write_count

    @property
    def has_type_info(self) -> bool:
        """是否有类型信息."""
        return bool(self.type_annotation or self.inferred_type)

    @property
    def is_used(self) -> bool:
        """是否被使用（有引用）."""
        return self.total_references > 0

    @property
    def is_dead_code(self) -> bool:
        """是否为死代码（定义后从未使用）."""
        return self.total_references == 0 and self.scope != VariableScope.PARAMETER

    # ========== 方法 ==========

    def add_reference(
        self,
        location: CodeLocation,
        context: str = "read",
        scope_name: str = "",
    ) -> None:
        """添加引用记录.

        Args:
            location: 引用位置
            context: 引用上下文（read/write/delete）
            scope_name: 所在作用域名称
        """
        ref = VariableReference(
            location=location,
            context=context,
            scope_name=scope_name,
        )
        self.references.append(ref)
        if context == "write":
            self.write_count += 1
        else:
            self.read_count += 1

    def add_dependency(self, var_name: str) -> None:
        """添加依赖变量."""
        self.dependencies.add(var_name)

    def add_dependent(self, var_name: str) -> None:
        """添加被依赖变量."""
        self.dependents.add(var_name)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "atom_id": self.atom_id,
            "name": self.name,
            "full_name": self.full_name,
            "scope": self.scope.value,
            "mutability": self.mutability.value,
            "type_annotation": self.type_annotation,
            "inferred_type": self.inferred_type,
            "default_value": self.default_value,
            "definition": self.definition.to_dict(),
            "references": [r.to_dict() for r in self.references],
            "read_count": self.read_count,
            "write_count": self.write_count,
            "dependencies": sorted(self.dependencies),
            "dependents": sorted(self.dependents),
            "container_name": self.container_name,
            "container_type": self.container_type,
            "is_private": self.is_private,
            "is_constant": self.is_constant,
            "is_dead_code": self.is_dead_code,
            "has_type_info": self.has_type_info,
        }

    def summary(self) -> str:
        """生成变量摘要."""
        parts = [f"变量: {self.full_name}"]
        if self.type_annotation:
            parts.append(f"类型: {self.type_annotation}")
        parts.append(f"作用域: {self.scope.value}")
        parts.append(f"读写: {self.read_count}读/{self.write_count}写")
        if self.is_dead_code:
            parts.append("⚠ 死代码")
        return " | ".join(parts)
