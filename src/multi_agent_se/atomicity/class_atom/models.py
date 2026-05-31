"""类原子模型 - 阶段30.

第三级代码原子化：类原子（Class Atom）

封装单个类的完整信息：
- 名称、基类、元类
- 方法列表、属性列表、类变量
- 继承关系、实现接口
- 内聚性、耦合度指标
- 类级文档和元数据
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


# ========== 枚举定义 ==========

class ClassType(Enum):
    """类类型."""
    REGULAR = "regular"           # 普通类
    ABSTRACT = "abstract"         # 抽象类（ABC）
    DATACLASS = "dataclass"       # 数据类
    ENUM = "enum"                 # 枚举类
    NAMEDTUPLE = "namedtuple"     # 命名元组
    TYPEDDICT = "typeddict"       # 类型字典
    PROTOCOL = "protocol"         # 协议类
    EXCEPTION = "exception"       # 异常类
    MIXIN = "mixin"               # Mixin类
    METACLASS = "metaclass"       # 元类


class ClassVisibility(Enum):
    """类可见性."""
    PUBLIC = "public"             # 公开类
    PROTECTED = "protected"       # 保护类（模块级私有）
    PRIVATE = "private"           # 私有类（内部类）


class InheritanceType(Enum):
    """继承类型."""
    SINGLE = "single"             # 单继承
    MULTIPLE = "multiple"         # 多继承
    MIXIN = "mixin"               # Mixin模式
    DIAMOND = "diamond"           # 菱形继承


# ========== 数据类 ==========

@dataclass
class AttributeInfo:
    """属性信息."""
    name: str = ""
    type_annotation: str = ""
    default_value: str = ""
    is_class_attribute: bool = False   # 类属性 vs 实例属性
    is_property: bool = False          # 是否是@property
    is_readonly: bool = False          # 是否只读
    docstring: str = ""
    line_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type_annotation": self.type_annotation,
            "default_value": self.default_value,
            "is_class_attribute": self.is_class_attribute,
            "is_property": self.is_property,
            "is_readonly": self.is_readonly,
            "line_number": self.line_number,
        }


@dataclass
class MethodSignature:
    """方法签名信息."""
    name: str = ""
    is_abstract: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False
    is_async: bool = False
    is_magic: bool = False
    visibility: str = "public"         # public/protected/private/magic
    parameters: List[str] = field(default_factory=list)
    return_type: str = ""
    decorators: List[str] = field(default_factory=list)
    line_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "is_abstract": self.is_abstract,
            "is_classmethod": self.is_classmethod,
            "is_staticmethod": self.is_staticmethod,
            "is_property": self.is_property,
            "is_async": self.is_async,
            "is_magic": self.is_magic,
            "visibility": self.visibility,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "decorators": self.decorators,
            "line_number": self.line_number,
        }


@dataclass
class InheritanceInfo:
    """继承信息."""
    base_class: str = ""              # 基类名称
    module: str = ""                  # 基类所在模块
    is_builtin: bool = False          # 是否是内置类
    is_abstract: bool = False         # 基类是否是抽象类
    mro_position: int = 0             # 在MRO中的位置

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_class": self.base_class,
            "module": self.module,
            "is_builtin": self.is_builtin,
            "is_abstract": self.is_abstract,
            "mro_position": self.mro_position,
        }


@dataclass
class ClassMetrics:
    """类度量指标."""
    method_count: int = 0             # 方法数量
    public_method_count: int = 0      # 公开方法数量
    private_method_count: int = 0     # 私有方法数量
    property_count: int = 0           # 属性数量
    attribute_count: int = 0          # 属性数量
    class_attribute_count: int = 0    # 类属性数量
    
    lines_of_code: int = 0            # 代码行数
    docstring_lines: int = 0          # 文档字符串行数
    
    inheritance_depth: int = 0        # 继承深度
    child_class_count: int = 0        # 子类数量
    
    # 内聚性指标
    lcom: float = 0.0                 # Lack of Cohesion of Methods (0-1, 越低越好)
    
    # 耦合性指标
    afferent_coupling: int = 0        # 入度（被多少类依赖）
    efferent_coupling: int = 0        # 出度（依赖多少类）
    
    @property
    def is_god_class(self) -> bool:
        """是否为上帝类（方法过多）."""
        return self.method_count > 20 or self.lines_of_code > 500
    
    @property
    def is_data_class(self) -> bool:
        """是否为数据类（主要是属性和getter/setter）."""
        if self.method_count == 0:
            return self.attribute_count > 0
        ratio = self.attribute_count / self.method_count
        return ratio > 2.0
    
    @property
    def is_service_class(self) -> bool:
        """是否为服务类（主要是方法，少属性）."""
        if self.attribute_count == 0:
            return self.method_count > 0
        ratio = self.method_count / self.attribute_count
        return ratio > 3.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "method_count": self.method_count,
            "public_method_count": self.public_method_count,
            "private_method_count": self.private_method_count,
            "property_count": self.property_count,
            "attribute_count": self.attribute_count,
            "class_attribute_count": self.class_attribute_count,
            "lines_of_code": self.lines_of_code,
            "docstring_lines": self.docstring_lines,
            "inheritance_depth": self.inheritance_depth,
            "child_class_count": self.child_class_count,
            "lcom": round(self.lcom, 3),
            "afferent_coupling": self.afferent_coupling,
            "efferent_coupling": self.efferent_coupling,
            "is_god_class": self.is_god_class,
            "is_data_class": self.is_data_class,
            "is_service_class": self.is_service_class,
        }


@dataclass
class ClassAtom:
    """类原子.

    封装单个类的完整信息，是四级原子化体系的第三级。
    每个类原子代表代码中一个独立的类定义。
    """
    # 基础信息
    name: str = ""
    atom_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    class_type: ClassType = ClassType.REGULAR
    visibility: ClassVisibility = ClassVisibility.PUBLIC
    
    # 位置信息
    file_path: str = ""
    module_name: str = ""
    line_start: int = 0
    line_end: int = 0
    col_start: int = 0
    
    # 继承信息
    bases: List[InheritanceInfo] = field(default_factory=list)
    mro: List[str] = field(default_factory=list)              # 方法解析顺序
    inheritance_type: InheritanceType = InheritanceType.SINGLE
    metaclass: str = ""                                       # 元类名称
    
    # 成员信息
    methods: List[MethodSignature] = field(default_factory=list)
    attributes: List[AttributeInfo] = field(default_factory=list)
    inner_classes: List[str] = field(default_factory=list)    # 内部类名称列表
    
    # 文档信息
    docstring: str = ""
    decorators: List[str] = field(default_factory=list)
    
    # 实现信息
    implemented_interfaces: List[str] = field(default_factory=list)
    abstract_methods: List[str] = field(default_factory=list)
    
    # 度量指标
    metrics: ClassMetrics = field(default_factory=ClassMetrics)
    
    # 依赖信息
    imported_names: List[str] = field(default_factory=list)   # 导入的名称
    dependent_classes: List[str] = field(default_factory=list)  # 依赖的其他类
    
    # ========== 属性 ==========
    
    @property
    def full_name(self) -> str:
        """完整限定名."""
        if self.module_name:
            return f"{self.module_name}.{self.name}"
        return self.name
    
    @property
    def is_abstract(self) -> bool:
        """是否为抽象类."""
        return self.class_type == ClassType.ABSTRACT or len(self.abstract_methods) > 0
    
    @property
    def is_concrete(self) -> bool:
        """是否为具体类."""
        return not self.is_abstract
    
    @property
    def is_builtin_base(self) -> bool:
        """是否继承自内置类."""
        return any(b.is_builtin for b in self.bases)
    
    @property
    def has_multiple_inheritance(self) -> bool:
        """是否有多重继承."""
        return len(self.bases) > 1
    
    @property
    def public_methods(self) -> List[MethodSignature]:
        """获取公开方法列表."""
        return [m for m in self.methods if m.visibility == "public"]
    
    @property
    def private_methods(self) -> List[MethodSignature]:
        """获取私有方法列表."""
        return [m for m in self.methods if m.visibility == "private"]
    
    @property
    def magic_methods(self) -> List[MethodSignature]:
        """获取魔术方法列表."""
        return [m for m in self.methods if m.is_magic]
    
    @property
    def properties(self) -> List[AttributeInfo]:
        """获取属性列表（@property装饰的方法对应的属性）."""
        return [a for a in self.attributes if a.is_property]
    
    # ========== 方法 ==========
    
    def get_method(self, name: str) -> Optional[MethodSignature]:
        """按名称获取方法签名."""
        for method in self.methods:
            if method.name == name:
                return method
        return None
    
    def get_attribute(self, name: str) -> Optional[AttributeInfo]:
        """按名称获取属性信息."""
        for attr in self.attributes:
            if attr.name == name:
                return attr
        return None
    
    def has_method(self, name: str) -> bool:
        """检查是否有指定方法."""
        return any(m.name == name for m in self.methods)
    
    def has_attribute(self, name: str) -> bool:
        """检查是否有指定属性."""
        return any(a.name == name for a in self.attributes)
    
    def implements_interface(self, interface_name: str) -> bool:
        """检查是否实现了指定接口."""
        return interface_name in self.implemented_interfaces
    
    def is_subclass_of(self, class_name: str) -> bool:
        """检查是否是指定类的子类."""
        return class_name in [b.base_class for b in self.bases] or class_name in self.mro
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "atom_id": self.atom_id,
            "name": self.name,
            "full_name": self.full_name,
            "class_type": self.class_type.value,
            "visibility": self.visibility.value,
            "file_path": self.file_path,
            "module_name": self.module_name,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "bases": [b.to_dict() for b in self.bases],
            "mro": self.mro,
            "inheritance_type": self.inheritance_type.value,
            "metaclass": self.metaclass,
            "methods": [m.to_dict() for m in self.methods],
            "attributes": [a.to_dict() for a in self.attributes],
            "inner_classes": self.inner_classes,
            "docstring": self.docstring[:200] if self.docstring else "",
            "decorators": self.decorators,
            "implemented_interfaces": self.implemented_interfaces,
            "abstract_methods": self.abstract_methods,
            "is_abstract": self.is_abstract,
            "is_concrete": self.is_concrete,
            "has_multiple_inheritance": self.has_multiple_inheritance,
            "metrics": self.metrics.to_dict(),
            "dependent_classes": self.dependent_classes,
        }
    
    def summary(self) -> str:
        """生成类摘要."""
        parts = [f"类: {self.full_name}"]
        if self.bases:
            parts.append(f"继承: {', '.join(b.base_class for b in self.bases)}")
        parts.append(f"方法: {len(self.methods)}个")
        parts.append(f"属性: {len(self.attributes)}个")
        if self.is_abstract:
            parts.append("抽象类")
        if self.metrics.is_god_class:
            parts.append("⚠ 上帝类")
        return " | ".join(parts)
