"""方法提取器 - 阶段29.

从Python源码中提取所有方法/函数原子，基于标准库ast模块进行语义分析。

功能：
- 提取模块级函数、类方法、嵌套函数
- 分析方法签名（参数、返回类型）
- 计算圈复杂度和其他复杂度指标
- 构建方法调用关系图
- 识别方法类型（实例方法/类方法/静态方法/异步方法）
- 检测异常抛出和捕获
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from multi_agent_se.atomicity.method.models import (
    CallRelation,
    ComplexityMetrics,
    MethodAtom,
    MethodType,
    MethodVisibility,
    ParameterInfo,
)


class MethodExtractor:
    """方法提取器.

    遍历Python AST，提取所有方法/函数原子信息。
    """

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
        self._methods: Dict[str, MethodAtom] = {}
        self._class_stack: List[str] = []  # 当前所在类名栈

    @classmethod
    def from_file(cls, file_path: str) -> "MethodExtractor":
        """从文件创建提取器.

        Args:
            file_path: Python源文件路径

        Returns:
            MethodExtractor实例
        """
        source = Path(file_path).read_text(encoding="utf-8")
        return cls(source, file_path=file_path)

    # ========== 公共接口 ==========

    def extract(self) -> List[MethodAtom]:
        """提取所有方法原子.

        Returns:
            方法原子列表
        """
        self._methods.clear()
        self._class_stack = []
        self._visit_module(self._tree)
        self._resolve_call_relations()
        return list(self._methods.values())

    def get_method(self, name: str) -> Optional[MethodAtom]:
        """按名称获取方法原子.

        Args:
            name: 方法名

        Returns:
            方法原子或None
        """
        return self._methods.get(name)

    def get_methods_by_type(self, method_type: MethodType) -> List[MethodAtom]:
        """按类型筛选方法.

        Args:
            method_type: 方法类型

        Returns:
            匹配的方法原子列表
        """
        return [m for m in self._methods.values() if m.method_type == method_type]

    def get_methods_by_class(self, class_name: str) -> List[MethodAtom]:
        """获取指定类的所有方法.

        Args:
            class_name: 类名

        Returns:
            该类的方法列表
        """
        return [m for m in self._methods.values() if m.class_name == class_name]

    def get_complex_methods(self) -> List[MethodAtom]:
        """获取需要重构的复杂方法.

        Returns:
            复杂方法列表
        """
        return [m for m in self._methods.values() if m.needs_refactoring]

    def get_methods_without_docstring(self) -> List[MethodAtom]:
        """获取缺少文档字符串的方法.

        Returns:
            缺少文档字符串的方法列表
        """
        return [m for m in self._methods.values() if not m.docstring.strip()]

    def get_call_graph(self) -> Dict[str, Set[str]]:
        """获取方法调用关系图.

        Returns:
            {方法名: 调用的方法名集合}
        """
        return {name: set(m.call_targets) for name, m in self._methods.items()}

    def get_reverse_call_graph(self) -> Dict[str, List[str]]:
        """获取反向调用关系图（被谁调用）.

        Returns:
            {方法名: 调用它的方法名列表}
        """
        result: Dict[str, List[str]] = {}
        for name, method in self._methods.items():
            for call in method.calls:
                if call.target_name not in result:
                    result[call.target_name] = []
                result[call.target_name].append(name)
        return result

    def summary(self) -> str:
        """生成提取结果摘要.

        Returns:
            摘要字符串
        """
        total = len(self._methods)
        by_type: Dict[str, int] = {}
        for m in self._methods.values():
            t = m.method_type.value
            by_type[t] = by_type.get(t, 0) + 1

        complex_count = len(self.get_complex_methods())
        no_doc = len(self.get_methods_without_docstring())

        lines = [f"方法原子提取结果: 共 {total} 个"]
        for type_name, count in sorted(by_type.items()):
            lines.append(f"  {type_name}: {count}")
        if complex_count > 0:
            lines.append(f"  ⚠ 需要重构: {complex_count}")
        if no_doc > 0:
            lines.append(f"  ⚠ 缺少文档: {no_doc}")
        return "\n".join(lines)

    # ========== 内部方法 ==========

    def _unique_key(self, name: str) -> str:
        """生成唯一键."""
        if self._class_stack:
            return f"{'.'.join(self._class_stack)}.{name}"
        return name

    def _determine_method_type(
        self,
        node: ast.FunctionDef,
        class_name: str = "",
    ) -> MethodType:
        """判断方法类型."""
        name = node.name

        # 检查装饰器
        decorators = self._get_decorator_names(node)

        if isinstance(node, ast.AsyncFunctionDef):
            if class_name:
                if "classmethod" in decorators:
                    return MethodType.CLASSMETHOD
                if "staticmethod" in decorators:
                    return MethodType.STATICMETHOD
                return MethodType.ASYNC_METHOD
            return MethodType.ASYNC_FUNCTION

        if class_name:
            if "classmethod" in decorators:
                return MethodType.CLASSMETHOD
            if "staticmethod" in decorators:
                return MethodType.STATICMETHOD
            if "property" in decorators:
                return MethodType.PROPERTY
            if name.startswith("__") and name.endswith("__") and len(name) > 4:
                return MethodType.MAGIC
            return MethodType.METHOD

        return MethodType.FUNCTION

    def _determine_visibility(self, name: str) -> MethodVisibility:
        """判断方法可见性."""
        if name.startswith("__") and name.endswith("__") and len(name) > 4:
            return MethodVisibility.MAGIC
        if name.startswith("__"):
            return MethodVisibility.PRIVATE
        if name.startswith("_"):
            return MethodVisibility.PROTECTED
        return MethodVisibility.PUBLIC

    def _get_decorator_names(self, node: ast.FunctionDef) -> List[str]:
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

    def _build_signature(self, node: ast.FunctionDef) -> str:
        """构建方法签名字符串."""
        params = self._extract_parameters(node.args)
        param_strs = []
        for p in params:
            s = p.name
            if p.type_annotation:
                s += f": {p.type_annotation}"
            if p.has_default:
                s += f" = {p.default_value}"
            param_strs.append(s)

        prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        sig = f"{prefix}def {node.name}({', '.join(param_strs)})"
        if node.returns and hasattr(ast, "unparse"):
            sig += f" -> {ast.unparse(node.returns)}"
        return sig

    def _extract_parameters(self, args: ast.arguments) -> List[ParameterInfo]:
        """提取参数信息."""
        params: List[ParameterInfo] = []
        pos = 0

        # 普通位置参数
        for arg in args.args:
            type_ann = ""
            if arg.annotation and hasattr(ast, "unparse"):
                type_ann = ast.unparse(arg.annotation)

            default = ""
            has_default = False
            defaults = args.defaults
            num_without_default = len(args.args) - len(defaults)
            arg_pos = args.args.index(arg)
            if arg_pos >= num_without_default and defaults:
                default_idx = arg_pos - num_without_default
                if default_idx < len(defaults) and hasattr(ast, "unparse"):
                    default = ast.unparse(defaults[default_idx])
                    has_default = True

            params.append(ParameterInfo(
                name=arg.arg,
                type_annotation=type_ann,
                default_value=default,
                has_default=has_default,
                kind="positional",
                position=pos,
            ))
            pos += 1

        # *args
        if args.vararg:
            type_ann = ""
            if args.vararg.annotation and hasattr(ast, "unparse"):
                type_ann = ast.unparse(args.vararg.annotation)
            params.append(ParameterInfo(
                name=args.vararg.arg,
                type_annotation=type_ann,
                kind="vararg",
                position=pos,
            ))
            pos += 1

        # 仅关键字参数
        for arg in args.kwonlyargs:
            type_ann = ""
            if arg.annotation and hasattr(ast, "unparse"):
                type_ann = ast.unparse(arg.annotation)

            default = ""
            has_default = False
            kw_defaults = args.kw_defaults
            kw_pos = args.kwonlyargs.index(arg)
            if kw_pos < len(kw_defaults) and kw_defaults[kw_pos] and hasattr(ast, "unparse"):
                default = ast.unparse(kw_defaults[kw_pos])
                has_default = True

            params.append(ParameterInfo(
                name=arg.arg,
                type_annotation=type_ann,
                default_value=default,
                has_default=has_default,
                kind="kwonly",
                position=pos,
            ))
            pos += 1

        # **kwargs
        if args.kwarg:
            type_ann = ""
            if args.kwarg.annotation and hasattr(ast, "unparse"):
                type_ann = ast.unparse(args.kwarg.annotation)
            params.append(ParameterInfo(
                name=args.kwarg.arg,
                type_annotation=type_ann,
                kind="varkeyword",
                position=pos,
            ))

        return params

    # ========== AST访问方法 ==========

    def _visit_module(self, tree: ast.Module) -> None:
        """访问模块级节点."""
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_function_def(node, class_name="")
            elif isinstance(node, ast.ClassDef):
                self._visit_class_def(node)

    def _visit_function_def(
        self,
        node: ast.FunctionDef,
        class_name: str = "",
        is_nested: bool = False,
    ) -> None:
        """访问函数/方法定义."""
        name = node.name
        key = self._unique_key(name)

        # 判断方法类型
        method_type = self._determine_method_type(node, class_name)
        if is_nested:
            method_type = MethodType.NESTED

        # 判断可见性
        visibility = self._determine_visibility(name)

        # 提取返回类型
        return_type = ""
        if node.returns and hasattr(ast, "unparse"):
            return_type = ast.unparse(node.returns)

        # 提取文档字符串
        docstring = ast.get_docstring(node) or ""

        # 提取装饰器
        decorators = self._get_decorator_names(node)

        # 检查是否为抽象方法
        is_abstract = any(d in ("abstractmethod", "abstract") for d in decorators)

        # 构建方法原子
        atom = MethodAtom(
            name=name,
            method_type=method_type,
            visibility=visibility,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            parameters=self._extract_parameters(node.args),
            return_type=return_type,
            signature=self._build_signature(node),
            docstring=docstring,
            decorators=decorators,
            file_path=self._file_path,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            col_start=node.col_offset,
            class_name=class_name,
            module_name=self._module_name,
            is_abstract=is_abstract,
        )

        # 计算复杂度
        atom.complexity = self._compute_complexity(node)

        # 提取调用关系
        atom.calls = self._extract_calls(node)

        # 提取异常信息
        atom.exceptions_raised = self._extract_raised_exceptions(node)
        atom.exceptions_caught = self._extract_caught_exceptions(node)

        self._methods[key] = atom

        # 递归访问嵌套函数
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_function_def(child, class_name=class_name, is_nested=True)

    def _visit_class_def(self, node: ast.ClassDef) -> None:
        """访问类定义."""
        class_name = node.name
        self._class_stack.append(class_name)

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_function_def(child, class_name=class_name)

        self._class_stack.pop()

    # ========== 复杂度计算 ==========

    def _compute_complexity(self, node: ast.FunctionDef) -> ComplexityMetrics:
        """计算方法复杂度指标.

        Args:
            node: 函数定义AST节点

        Returns:
            复杂度指标
        """
        cc = 1  # 基础圈复杂度
        line_count = 0
        branch_count = 0
        nesting_depth = 0
        max_nesting = 0
        return_count = 0
        call_count = 0
        local_vars: Set[str] = set()

        def _count_complexity(n: ast.AST, depth: int) -> None:
            nonlocal cc, line_count, branch_count, max_nesting, return_count, call_count

            if isinstance(n, (ast.If, ast.IfExp)):
                cc += 1
                branch_count += 1
            elif isinstance(n, (ast.For, ast.AsyncFor, ast.While)):
                cc += 1
                branch_count += 1
            elif isinstance(n, ast.ExceptHandler):
                cc += 1
                branch_count += 1
            elif isinstance(n, (ast.And, ast.Or)):
                cc += 1
            elif isinstance(n, ast.comprehension):
                cc += 1
                branch_count += 1
            elif isinstance(n, ast.Return):
                return_count += 1
            elif isinstance(n, ast.Call):
                call_count += 1
            elif isinstance(n, ast.Assign):
                for target in n.targets:
                    if isinstance(target, ast.Name):
                        local_vars.add(target.id)
                    elif isinstance(target, ast.Tuple):
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                local_vars.add(elt.id)

            # 计算嵌套深度
            if isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.Try)):
                new_depth = depth + 1
                if new_depth > max_nesting:
                    max_nesting = new_depth
            else:
                new_depth = depth

            # 计算非空行数
            if hasattr(n, "lineno") and hasattr(n, "end_lineno"):
                for line_num in range(n.lineno, n.end_lineno + 1):
                    line = self._source.splitlines()[line_num - 1].strip()
                    if line and not line.startswith("#"):
                        line_count += 1

            for child in ast.iter_child_nodes(n):
                _count_complexity(child, new_depth)

        _count_complexity(node, 0)

        # 去重行数
        if line_count > 0:
            line_count = len(set(
                i for i, line in enumerate(self._source.splitlines())
                if line.strip() and not line.strip().startswith("#")
                and node.lineno <= i + 1 <= getattr(node, "end_lineno", node.lineno)
            ))

        return ComplexityMetrics(
            cyclomatic_complexity=cc,
            line_count=line_count,
            parameter_count=len(node.args.args) + len(node.args.kwonlyargs) + (1 if node.args.vararg else 0) + (1 if node.args.kwarg else 0),
            return_statement_count=return_count,
            branch_count=branch_count,
            nesting_depth=max_nesting,
            local_variable_count=len(local_vars),
            call_count=call_count,
        )

    # ========== 调用关系提取 ==========

    def _extract_calls(self, node: ast.FunctionDef) -> List[CallRelation]:
        """提取方法内的所有调用关系.

        Args:
            node: 函数定义AST节点

        Returns:
            调用关系列表
        """
        calls: List[CallRelation] = []

        def _visit(n: ast.AST) -> None:
            if isinstance(n, ast.Call):
                target_name = ""
                target_class = ""

                if isinstance(n.func, ast.Name):
                    target_name = n.func.id
                elif isinstance(n.func, ast.Attribute):
                    target_name = n.func.attr
                    # 尝试获取调用对象
                    if isinstance(n.func.value, ast.Name):
                        target_class = n.func.value.id
                elif isinstance(n.func, ast.Call):
                    # 链式调用如 Class().method()
                    if isinstance(n.func.func, ast.Attribute):
                        target_name = n.func.func.attr

                if target_name:
                    calls.append(CallRelation(
                        target_name=target_name,
                        target_class=target_class,
                        location_line=n.lineno,
                    ))

            for child in ast.iter_child_nodes(n):
                _visit(child)

        for child in ast.iter_child_nodes(node):
            _visit(child)

        return calls

    # ========== 异常提取 ==========

    def _extract_raised_exceptions(self, node: ast.FunctionDef) -> List[str]:
        """提取方法抛出的异常类型.

        Args:
            node: 函数定义AST节点

        Returns:
            异常类型名称列表
        """
        exceptions: List[str] = []

        def _visit(n: ast.AST) -> None:
            if isinstance(n, ast.Raise):
                if isinstance(n.exc, ast.Name):
                    exceptions.append(n.exc.id)
                elif isinstance(n.exc, ast.Call):
                    if isinstance(n.exc.func, ast.Name):
                        exceptions.append(n.exc.func.id)
                    elif isinstance(n.exc.func, ast.Attribute):
                        exceptions.append(n.exc.func.attr)
            for child in ast.iter_child_nodes(n):
                _visit(child)

        for child in ast.iter_child_nodes(node):
            _visit(child)

        return list(set(exceptions))

    def _extract_caught_exceptions(self, node: ast.FunctionDef) -> List[str]:
        """提取方法捕获的异常类型.

        Args:
            node: 函数定义AST节点

        Returns:
            异常类型名称列表
        """
        exceptions: List[str] = []

        def _visit(n: ast.AST) -> None:
            if isinstance(n, ast.Try):
                for handler in n.handlers:
                    if handler.type:
                        if isinstance(handler.type, ast.Name):
                            exceptions.append(handler.type.id)
                        elif isinstance(handler.type, ast.Tuple):
                            for elt in handler.type.elts:
                                if isinstance(elt, ast.Name):
                                    exceptions.append(elt.id)
            for child in ast.iter_child_nodes(n):
                _visit(child)

        for child in ast.iter_child_nodes(node):
            _visit(child)

        return list(set(exceptions))

    # ========== 调用关系解析 ==========

    def _resolve_call_relations(self) -> None:
        """解析调用关系，填充called_by字段."""
        for caller_name, caller_method in self._methods.items():
            for call in caller_method.calls:
                target_key = call.target_name
                if target_key in self._methods:
                    self._methods[target_key].add_called_by(caller_name)
                else:
                    # 尝试带类名匹配
                    if call.target_class:
                        qualified = f"{call.target_class}.{call.target_name}"
                        if qualified in self._methods:
                            self._methods[qualified].add_called_by(caller_name)
