"""类提取器 - 阶段30.

从Python源码中提取所有类原子，基于标准库ast模块进行语义分析.

功能:
- 提取类定义、继承关系、元类
- 分析方法签名、属性、装饰器
- 计算内聚性、耦合度指标
- 识别类类型(数据类/抽象类/异常类等)
- 构建类继承图
"""

import ast
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from multi_agent_se.atomicity.class_atom.models import (
    AttributeInfo,
    ClassAtom,
    ClassMetrics,
    ClassType,
    ClassVisibility,
    InheritanceInfo,
    InheritanceType,
    MethodSignature,
)


class ClassExtractor:
    """类提取器.

    遍历Python AST，提取所有类原子信息.
    """

    # 内置类集合
    BUILTIN_CLASSES = {
        'object', 'type', 'int', 'float', 'str', 'bool', 'list', 'dict', 'set',
        'tuple', 'frozenset', 'bytes', 'bytearray', 'memoryview', 'complex',
        'Exception', 'BaseException', 'Warning', 'GeneratorExit', 'SystemExit',
        'KeyboardInterrupt', 'ArithmeticError', 'LookupError', 'AssertionError',
        'AttributeError', 'BufferError', 'EOFError', 'FloatingPointError',
        'OSError', 'ImportError', 'ModuleNotFoundError', 'IndexError', 'KeyError',
        'MemoryError', 'NameError', 'NotImplementedError', 'RecursionError',
        'ReferenceError', 'RuntimeError', 'StopAsyncIteration', 'StopIteration',
        'SyntaxError', 'IndentationError', 'TabError', 'SystemError', 'TypeError',
        'UnboundLocalError', 'UnicodeError', 'UnicodeDecodeError',
        'UnicodeEncodeError', 'UnicodeTranslateError', 'ValueError', 'ZeroDivisionError',
        'BlockingIOError', 'ChildProcessError', 'ConnectionError',
        'BrokenPipeError', 'ConnectionAbortedError', 'ConnectionRefusedError',
        'ConnectionResetError', 'FileExistsError', 'FileNotFoundError',
        'InterruptedError', 'IsADirectoryError', 'NotADirectoryError',
        'PermissionError', 'ProcessLookupError', 'TimeoutError',
        'EnvironmentError', 'IOError', 'WindowsError',
    }

    def __init__(self, source: str, file_path: str = "", module_name: str = "") -> None:
        """初始化提取器.

        Args:
            source: Python源码字符串
            file_path: 源文件路径
            module_name: 模块名称
        """
        self._source = source
        self._file_path = file_path
        self._module_name = module_name or Path(file_path).stem if file_path else ""
        self._tree = ast.parse(source)
        self._classes: Dict[str, ClassAtom] = {}
        self._imports: Dict[str, str] = {}  # 名称 -> 模块映射

    @classmethod
    def from_file(cls, file_path: str) -> "ClassExtractor":
        """从文件创建提取器.

        Args:
            file_path: Python源文件路径

        Returns:
            ClassExtractor实例
        """
        source = Path(file_path).read_text(encoding="utf-8")
        return cls(source, file_path=file_path)

    # ========== 公共接口 ==========

    def extract(self) -> List[ClassAtom]:
        """提取所有类原子.

        Returns:
            类原子列表
        """
        self._classes.clear()
        self._imports.clear()

        # 首先收集导入信息
        self._collect_imports()

        # 然后提取类定义
        self._visit_module(self._tree)

        # 计算类间关系
        self._calculate_relationships()

        return list(self._classes.values())

    def get_class(self, name: str) -> Optional[ClassAtom]:
        """按名称获取类原子.

        Args:
            name: 类名

        Returns:
            类原子或None
        """
        return self._classes.get(name)

    def get_classes_by_type(self, class_type: ClassType) -> List[ClassAtom]:
        """按类型筛选类.

        Args:
            class_type: 类类型

        Returns:
            匹配的类原子列表
        """
        return [c for c in self._classes.values() if c.class_type == class_type]

    def get_inheritance_graph(self) -> Dict[str, List[str]]:
        """获取类继承关系图.

        Returns:
            {类名: 基类名列表}
        """
        return {name: [b.base_class for b in c.bases] for name, c in self._classes.items()}

    def get_reverse_inheritance_graph(self) -> Dict[str, List[str]]:
        """获取反向继承关系图（哪些类继承自此类）.

        Returns:
            {类名: 子类名列表}
        """
        result: Dict[str, List[str]] = {}
        for name, cls in self._classes.items():
            for base in cls.bases:
                if base.base_class not in result:
                    result[base.base_class] = []
                result[base.base_class].append(name)
        return result

    def get_god_classes(self) -> List[ClassAtom]:
        """获取上帝类（过大类）.

        Returns:
            上帝类列表
        """
        return [c for c in self._classes.values() if c.metrics.is_god_class]

    def get_abstract_classes(self) -> List[ClassAtom]:
        """获取抽象类.

        Returns:
            抽象类列表
        """
        return [c for c in self._classes.values() if c.is_abstract]

    def summary(self) -> str:
        """生成提取结果摘要.

        Returns:
            摘要字符串
        """
        total = len(self._classes)
        by_type: Dict[str, int] = {}
        for c in self._classes.values():
            t = c.class_type.value
            by_type[t] = by_type.get(t, 0) + 1

        god_count = len(self.get_god_classes())
        abstract_count = len(self.get_abstract_classes())

        lines = [f"类原子提取结果: 共 {total} 个"]
        for type_name, count in sorted(by_type.items()):
            lines.append(f"  {type_name}: {count}")
        if god_count > 0:
            lines.append(f"  ⚠ 上帝类: {god_count}")
        if abstract_count > 0:
            lines.append(f"  抽象类: {abstract_count}")
        return "\n".join(lines)

    # ========== 内部方法 ==========

    def _collect_imports(self) -> None:
        """收集模块导入信息."""
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self._imports[name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    self._imports[name] = full_name

    def _visit_module(self, tree: ast.Module) -> None:
        """访问模块级节点."""
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                self._visit_class_def(node, is_inner=False)

    def _visit_class_def(self, node: ast.ClassDef, is_inner: bool = False) -> None:
        """访问类定义.

        Args:
            node: 类定义AST节点
            is_inner: 是否为内部类
        """
        class_name = node.name

        # 创建类原子
        atom = ClassAtom(
            name=class_name,
            file_path=self._file_path,
            module_name=self._module_name,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            col_start=node.col_offset,
        )

        # 判断可见性
        if class_name.startswith("__"):
            atom.visibility = ClassVisibility.PRIVATE
        elif class_name.startswith("_"):
            atom.visibility = ClassVisibility.PROTECTED
        else:
            atom.visibility = ClassVisibility.PUBLIC

        # 提取装饰器
        atom.decorators = self._get_decorator_names(node)

        # 判断类类型
        atom.class_type = self._determine_class_type(node, atom.decorators)

        # 提取继承信息
        atom.bases = self._extract_bases(node)
        atom.inheritance_type = self._determine_inheritance_type(atom.bases)

        # 提取文档字符串
        atom.docstring = ast.get_docstring(node) or ""

        # 提取类成员
        self._extract_class_members(node, atom)

        # 计算度量指标
        atom.metrics = self._calculate_metrics(node, atom)

        # 提取依赖的类
        atom.dependent_classes = self._extract_dependencies(node)

        self._classes[class_name] = atom

        # 递归访问内部类
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                inner_name = f"{class_name}.{child.name}"
                self._visit_class_def(child, is_inner=True)
                atom.inner_classes.append(inner_name)

    def _get_decorator_names(self, node: ast.ClassDef) -> List[str]:
        """获取装饰器名称列表."""
        names = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                names.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                names.append(dec.attr)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    names.append(dec.func.id)
                elif isinstance(dec.func, ast.Attribute):
                    names.append(dec.func.attr)
        return names

    def _determine_class_type(self, node: ast.ClassDef, decorators: List[str]) -> ClassType:
        """判断类类型."""
        name = node.name

        # 检查装饰器
        if "dataclass" in decorators:
            return ClassType.DATACLASS

        # 检查基类
        for base in node.bases:
            base_name = ""
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr

            if base_name == "Enum":
                return ClassType.ENUM
            elif base_name == "ABC" or base_name == "ABCMeta":
                return ClassType.ABSTRACT
            elif base_name.endswith("Exception") or base_name == "BaseException":
                return ClassType.EXCEPTION
            elif "Protocol" in base_name:
                return ClassType.PROTOCOL

        # 检查是否是异常类
        if name.endswith("Exception") or name.endswith("Error"):
            return ClassType.EXCEPTION

        # 检查是否是Mixin
        if "Mixin" in name:
            return ClassType.MIXIN

        # 检查元类
        for keyword in node.keywords:
            if keyword.arg == "metaclass":
                return ClassType.METACLASS

        return ClassType.REGULAR

    def _extract_bases(self, node: ast.ClassDef) -> List[InheritanceInfo]:
        """提取基类信息."""
        bases = []
        for i, base_node in enumerate(node.bases):
            base_name = ""
            module = ""

            if isinstance(base_node, ast.Name):
                base_name = base_node.id
                # 尝试解析模块
                if base_name in self._imports:
                    full_name = self._imports[base_name]
                    if "." in full_name:
                        module = full_name.rsplit(".", 1)[0]
            elif isinstance(base_node, ast.Attribute):
                base_name = base_node.attr
                # 尝试获取模块前缀
                if isinstance(base_node.value, ast.Name):
                    module = base_node.value.id

            is_builtin = base_name in self.BUILTIN_CLASSES

            bases.append(InheritanceInfo(
                base_class=base_name,
                module=module,
                is_builtin=is_builtin,
                mro_position=i,
            ))

        return bases

    def _determine_inheritance_type(self, bases: List[InheritanceInfo]) -> InheritanceType:
        """判断继承类型."""
        if len(bases) > 1:
            # 检查是否是Mixin模式
            mixin_count = sum(1 for b in bases if "Mixin" in b.base_class)
            if mixin_count > 0 and mixin_count < len(bases):
                return InheritanceType.MIXIN
            return InheritanceType.MULTIPLE
        return InheritanceType.SINGLE

    def _extract_class_members(self, node: ast.ClassDef, atom: ClassAtom) -> None:
        """提取类成员（方法和属性）."""
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._extract_method_signature(child)
                atom.methods.append(method)
            elif isinstance(child, ast.AnnAssign):
                # 带类型注解的属性
                attr = self._extract_attribute(child, is_class_attr=True)
                if attr:
                    atom.attributes.append(attr)
            elif isinstance(child, ast.Assign):
                # 类属性赋值
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attr = AttributeInfo(
                            name=target.id,
                            is_class_attribute=True,
                            line_number=child.lineno,
                        )
                        if child.value and hasattr(ast, "unparse"):
                            attr.default_value = ast.unparse(child.value)[:50]
                        atom.attributes.append(attr)

    def _extract_method_signature(self, node: ast.FunctionDef) -> MethodSignature:
        """提取方法签名."""
        sig = MethodSignature(
            name=node.name,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            line_number=node.lineno,
        )

        # 判断方法类型
        decorators = self._get_method_decorators(node)
        sig.decorators = decorators

        sig.is_classmethod = "classmethod" in decorators
        sig.is_staticmethod = "staticmethod" in decorators
        sig.is_property = "property" in decorators
        sig.is_abstract = any(d in ("abstractmethod", "abstract") for d in decorators)
        sig.is_magic = node.name.startswith("__") and node.name.endswith("__") and len(node.name) > 4

        # 判断可见性
        if sig.is_magic:
            sig.visibility = "magic"
        elif node.name.startswith("__"):
            sig.visibility = "private"
        elif node.name.startswith("_"):
            sig.visibility = "protected"
        else:
            sig.visibility = "public"

        # 提取参数
        sig.parameters = self._extract_parameters(node.args)

        # 提取返回类型
        if node.returns and hasattr(ast, "unparse"):
            sig.return_type = ast.unparse(node.returns)

        return sig

    def _get_method_decorators(self, node: ast.FunctionDef) -> List[str]:
        """获取方法装饰器名称."""
        names = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                names.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                names.append(dec.attr)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    names.append(dec.func.id)
        return names

    def _extract_parameters(self, args: ast.arguments) -> List[str]:
        """提取参数名称列表."""
        params = []
        for arg in args.args:
            params.append(arg.arg)
        if args.vararg:
            params.append(f"*{args.vararg.arg}")
        for arg in args.kwonlyargs:
            params.append(arg.arg)
        if args.kwarg:
            params.append(f"**{args.kwarg.arg}")
        return params

    def _extract_attribute(self, node: ast.AnnAssign, is_class_attr: bool = True) -> Optional[AttributeInfo]:
        """提取属性信息."""
        if isinstance(node.target, ast.Name):
            attr = AttributeInfo(
                name=node.target.id,
                is_class_attribute=is_class_attr,
                line_number=node.lineno,
            )

            if node.annotation and hasattr(ast, "unparse"):
                attr.type_annotation = ast.unparse(node.annotation)

            if node.value and hasattr(ast, "unparse"):
                attr.default_value = ast.unparse(node.value)[:50]

            return attr
        return None

    def _calculate_metrics(self, node: ast.ClassDef, atom: ClassAtom) -> ClassMetrics:
        """计算类度量指标."""
        metrics = ClassMetrics()

        # 方法数量
        metrics.method_count = len(atom.methods)
        metrics.public_method_count = len(atom.public_methods)
        metrics.private_method_count = len(atom.private_methods)

        # 属性数量
        metrics.attribute_count = len(atom.attributes)
        metrics.class_attribute_count = sum(1 for a in atom.attributes if a.is_class_attribute)
        metrics.property_count = len(atom.properties)

        # 代码行数
        metrics.lines_of_code = getattr(node, "end_lineno", node.lineno) - node.lineno + 1

        # 文档字符串行数
        if atom.docstring:
            metrics.docstring_lines = len(atom.docstring.splitlines())

        # 继承深度
        metrics.inheritance_depth = len(atom.bases)

        return metrics

    def _extract_dependencies(self, node: ast.ClassDef) -> List[str]:
        """提取类依赖的其他类."""
        dependencies: Set[str] = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                name = child.id
                if name not in self.BUILTIN_CLASSES and name != node.name:
                    dependencies.add(name)
            elif isinstance(child, ast.Attribute):
                dependencies.add(child.attr)

        return sorted(dependencies)

    def _calculate_relationships(self) -> None:
        """计算类间关系."""
        # 计算子类数量
        for cls in self._classes.values():
            for base in cls.bases:
                if base.base_class in self._classes:
                    self._classes[base.base_class].metrics.child_class_count += 1

        # 计算入度（被多少类依赖）
        for cls in self._classes.values():
            for dep in cls.dependent_classes:
                if dep in self._classes:
                    self._classes[dep].metrics.afferent_coupling += 1

        # 计算出度（依赖多少类）
        for cls in self._classes.values():
            cls.metrics.efferent_coupling = len(cls.dependent_classes)
