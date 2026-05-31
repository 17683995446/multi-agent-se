"""变量提取器 - 阶段29.

从Python源码中提取所有变量原子，基于标准库ast模块进行语义分析。

功能：
- 提取全局变量、局部变量、函数参数、类属性、实例属性
- 分析变量类型注解和默认值
- 追踪变量引用位置（读/写）
- 构建变量依赖关系图
- 检测死代码（定义后未使用的变量）
"""

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from multi_agent_se.atomicity.variable.models import (
    CodeLocation,
    VariableAtom,
    VariableMutability,
    VariableReference,
    VariableScope,
)


class VariableExtractor:
    """变量提取器.

    遍历Python AST，提取所有变量原子信息。
    """

    def __init__(self, source: str, file_path: str = "") -> None:
        """初始化提取器.

        Args:
            source: Python源码字符串
            file_path: 源文件路径（用于位置信息）
        """
        self._source = source
        self._file_path = file_path
        self._tree = ast.parse(source)
        self._variables: Dict[str, VariableAtom] = {}
        self._scope_stack: List[str] = ["module"]  # 作用域栈

    @classmethod
    def from_file(cls, file_path: str) -> "VariableExtractor":
        """从文件创建提取器.

        Args:
            file_path: Python源文件路径

        Returns:
            VariableExtractor实例
        """
        source = Path(file_path).read_text(encoding="utf-8")
        return cls(source, file_path=file_path)

    # ========== 公共接口 ==========

    def extract(self) -> List[VariableAtom]:
        """提取所有变量原子.

        Returns:
            变量原子列表
        """
        self._variables.clear()
        self._scope_stack = ["module"]
        self._visit_module(self._tree)
        self._analyze_references()
        return list(self._variables.values())

    def get_variable(self, name: str) -> Optional[VariableAtom]:
        """按名称获取变量原子.

        Args:
            name: 变量名

        Returns:
            变量原子或None
        """
        return self._variables.get(name)

    def get_variables_by_scope(self, scope: VariableScope) -> List[VariableAtom]:
        """按作用域筛选变量.

        Args:
            scope: 变量作用域

        Returns:
            匹配的变量原子列表
        """
        return [v for v in self._variables.values() if v.scope == scope]

    def get_dead_variables(self) -> List[VariableAtom]:
        """获取死代码变量（定义后未使用）.

        Returns:
            死代码变量列表
        """
        return [v for v in self._variables.values() if v.is_dead_code]

    def get_variables_without_type(self) -> List[VariableAtom]:
        """获取缺少类型注解的变量.

        Returns:
            缺少类型注解的变量列表
        """
        return [v for v in self._variables.values() if not v.has_type_info]

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """获取变量依赖关系图.

        Returns:
            {变量名: 依赖的变量名集合}
        """
        return {name: set(v.dependencies) for name, v in self._variables.items()}

    def summary(self) -> str:
        """生成提取结果摘要.

        Returns:
            摘要字符串
        """
        total = len(self._variables)
        by_scope: Dict[str, int] = {}
        for v in self._variables.values():
            s = v.scope.value
            by_scope[s] = by_scope.get(s, 0) + 1

        dead = len(self.get_dead_variables())
        no_type = len(self.get_variables_without_type())

        lines = [f"变量原子提取结果: 共 {total} 个"]
        for scope_name, count in sorted(by_scope.items()):
            lines.append(f"  {scope_name}: {count}")
        if dead > 0:
            lines.append(f"  ⚠ 死代码: {dead}")
        if no_type > 0:
            lines.append(f"  ⚠ 缺少类型注解: {no_type}")
        return "\n".join(lines)

    # ========== 内部方法 ==========

    def _make_location(self, node: ast.AST) -> CodeLocation:
        """从AST节点创建代码位置."""
        return CodeLocation(
            file_path=self._file_path,
            line=getattr(node, "lineno", 0),
            col=getattr(node, "col_offset", 0),
            end_line=getattr(node, "end_lineno", 0),
            end_col=getattr(node, "end_col_offset", 0),
        )

    def _current_scope(self) -> str:
        """获取当前作用域名称."""
        return self._scope_stack[-1] if self._scope_stack else "module"

    def _current_scope_type(self) -> str:
        """获取当前作用域类型."""
        if len(self._scope_stack) >= 2:
            return self._scope_stack[-2]
        return "module"

    def _unique_key(self, name: str) -> str:
        """生成唯一键（避免同名变量冲突）."""
        scope_path = ".".join(self._scope_stack)
        return f"{scope_path}.{name}"

    def _register_variable(
        self,
        name: str,
        scope: VariableScope,
        node: ast.AST,
        type_annotation: str = "",
        default_value: str = "",
    ) -> VariableAtom:
        """注册一个变量原子."""
        key = self._unique_key(name)
        atom = VariableAtom(
            name=name,
            scope=scope,
            definition=self._make_location(node),
            type_annotation=type_annotation,
            default_value=default_value,
            container_name=self._current_scope(),
            container_type=self._current_scope_type(),
        )

        # 推断可变性
        if atom.is_constant:
            atom.mutability = VariableMutability.CONSTANT
        elif scope == VariableScope.PARAMETER:
            atom.mutability = VariableMutability.READONLY
        else:
            atom.mutability = VariableMutability.MUTABLE

        self._variables[key] = atom
        return atom

    # ========== AST访问方法 ==========

    def _visit_module(self, tree: ast.Module) -> None:
        """访问模块级节点."""
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                self._visit_assign(node, VariableScope.GLOBAL)
            elif isinstance(node, ast.AnnAssign):
                self._visit_ann_assign(node, VariableScope.GLOBAL)
            elif isinstance(node, ast.AugAssign):
                self._visit_aug_assign(node)
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                self._visit_function_def(node)
            elif isinstance(node, ast.ClassDef):
                self._visit_class_def(node)
            elif isinstance(node, ast.For) or isinstance(node, ast.AsyncFor):
                self._visit_for_loop(node)
            elif isinstance(node, ast.With) or isinstance(node, ast.AsyncWith):
                self._visit_with_statement(node)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._visit_import(node)
            elif isinstance(node, ast.If):
                self._visit_if_statement(node)
            elif isinstance(node, ast.Try):
                self._visit_try_statement(node)

    def _visit_assign(
        self,
        node: ast.Assign,
        scope: VariableScope,
    ) -> None:
        """访问赋值语句."""
        # 提取默认值表达式
        default_value = ast.unparse(node.value) if hasattr(ast, "unparse") else ""

        for target in node.targets:
            if isinstance(target, ast.Name):
                self._register_variable(
                    name=target.id,
                    scope=scope,
                    node=target,
                    default_value=default_value,
                )
                # 分析右侧表达式的依赖
                self._extract_dependencies(node.value, target.id)
            elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                # 解构赋值
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self._register_variable(
                            name=elt.id,
                            scope=scope,
                            node=elt,
                        )
            elif isinstance(target, ast.Attribute):
                # 实例属性赋值（如 self.x = ...）
                attr_name = target.attr
                key = self._unique_key(attr_name)
                if key not in self._variables:
                    self._register_variable(
                        name=attr_name,
                        scope=VariableScope.INSTANCE_ATTRIBUTE,
                        node=target,
                        default_value=default_value,
                    )

    def _visit_ann_assign(
        self,
        node: ast.AnnAssign,
        scope: VariableScope,
    ) -> None:
        """访问带类型注解的赋值语句."""
        type_annotation = ""
        if node.annotation and hasattr(ast, "unparse"):
            type_annotation = ast.unparse(node.annotation)

        default_value = ""
        if node.value and hasattr(ast, "unparse"):
            default_value = ast.unparse(node.value)

        if isinstance(node.target, ast.Name):
            self._register_variable(
                name=node.target.id,
                scope=scope,
                node=node.target,
                type_annotation=type_annotation,
                default_value=default_value,
            )
            if node.value:
                self._extract_dependencies(node.value, node.target.id)

    def _visit_aug_assign(self, node: ast.AugAssign) -> None:
        """访问增强赋值语句（如 x += 1）."""
        if isinstance(node.target, ast.Name):
            key = self._unique_key(node.target.id)
            if key in self._variables:
                self._variables[key].write_count += 1

    def _visit_function_def(self, node: ast.FunctionDef) -> None:
        """访问函数定义."""
        func_name = node.name
        self._scope_stack.append("function")
        self._scope_stack.append(func_name)

        # 提取参数
        self._visit_arguments(node.args)

        # 提取函数体内的局部变量
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Assign):
                self._visit_assign(child, VariableScope.LOCAL)
            elif isinstance(child, ast.AnnAssign):
                self._visit_ann_assign(child, VariableScope.LOCAL)
            elif isinstance(child, ast.AugAssign):
                self._visit_aug_assign(child)
            elif isinstance(child, (ast.For, ast.AsyncFor)):
                self._visit_for_loop(child)
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                self._visit_with_statement(child)
            elif isinstance(child, ast.If):
                self._visit_if_statement(child)
            elif isinstance(child, ast.Try):
                self._visit_try_statement(child)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 嵌套函数
                self._visit_function_def(child)
            elif isinstance(child, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
                self._visit_comprehension(child)
            elif isinstance(child, ast.DictComp):
                self._visit_dict_comprehension(child)

        self._scope_stack.pop()
        self._scope_stack.pop()

    def _visit_arguments(self, args: ast.arguments) -> None:
        """访问函数参数列表."""
        # 普通参数
        for arg in args.args:
            type_ann = ""
            if arg.annotation and hasattr(ast, "unparse"):
                type_ann = ast.unparse(arg.annotation)
            default = ""
            # 检查是否有默认值
            defaults = args.defaults
            pos = args.args.index(arg)
            num_without_default = len(args.args) - len(defaults)
            if pos >= num_without_default and defaults:
                default_idx = pos - num_without_default
                if default_idx < len(defaults) and hasattr(ast, "unparse"):
                    default = ast.unparse(defaults[default_idx])

            self._register_variable(
                name=arg.arg,
                scope=VariableScope.PARAMETER,
                node=arg,
                type_annotation=type_ann,
                default_value=default,
            )

        # *args
        if args.vararg:
            type_ann = ""
            if args.vararg.annotation and hasattr(ast, "unparse"):
                type_ann = ast.unparse(args.vararg.annotation)
            self._register_variable(
                name=args.vararg.arg,
                scope=VariableScope.PARAMETER,
                node=args.vararg,
                type_annotation=type_ann,
            )

        # **kwargs
        if args.kwarg:
            type_ann = ""
            if args.kwarg.annotation and hasattr(ast, "unparse"):
                type_ann = ast.unparse(args.kwarg.annotation)
            self._register_variable(
                name=args.kwarg.arg,
                scope=VariableScope.PARAMETER,
                node=args.kwarg,
                type_annotation=type_ann,
            )

        # 仅关键字参数
        for arg in args.kwonlyargs:
            type_ann = ""
            if arg.annotation and hasattr(ast, "unparse"):
                type_ann = ast.unparse(arg.annotation)
            default = ""
            kw_defaults = args.kw_defaults
            pos = args.kwonlyargs.index(arg)
            if pos < len(kw_defaults) and kw_defaults[pos] and hasattr(ast, "unparse"):
                default = ast.unparse(kw_defaults[pos])

            self._register_variable(
                name=arg.arg,
                scope=VariableScope.PARAMETER,
                node=arg,
                type_annotation=type_ann,
                default_value=default,
            )

    def _visit_class_def(self, node: ast.ClassDef) -> None:
        """访问类定义."""
        class_name = node.name
        self._scope_stack.append("class")
        self._scope_stack.append(class_name)

        # 提取类属性
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Assign):
                self._visit_assign(child, VariableScope.CLASS_ATTRIBUTE)
            elif isinstance(child, ast.AnnAssign):
                self._visit_ann_assign(child, VariableScope.CLASS_ATTRIBUTE)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 类方法（同时提取self参数作为实例属性提示）
                self._visit_method_in_class(child, class_name)

        self._scope_stack.pop()
        self._scope_stack.pop()

    def _visit_method_in_class(
        self,
        node: ast.FunctionDef,
        class_name: str,
    ) -> None:
        """访问类中的方法定义."""
        func_name = node.name
        self._scope_stack.append("function")
        self._scope_stack.append(func_name)

        # 提取方法参数
        self._visit_arguments(node.args)

        # 提取方法体内的变量
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Assign):
                self._visit_assign(child, VariableScope.LOCAL)
            elif isinstance(child, ast.AnnAssign):
                self._visit_ann_assign(child, VariableScope.LOCAL)
            elif isinstance(child, ast.AugAssign):
                self._visit_aug_assign(child)
            elif isinstance(child, (ast.For, ast.AsyncFor)):
                self._visit_for_loop(child)
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                self._visit_with_statement(child)
            elif isinstance(child, ast.If):
                self._visit_if_statement(child)
            elif isinstance(child, ast.Try):
                self._visit_try_statement(child)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_function_def(child)

        self._scope_stack.pop()
        self._scope_stack.pop()

    def _visit_for_loop(self, node: ast.For) -> None:
        """访问for循环."""
        if isinstance(node.target, ast.Name):
            self._register_variable(
                name=node.target.id,
                scope=VariableScope.LOCAL,
                node=node.target,
            )
        elif isinstance(node.target, (ast.Tuple, ast.List)):
            for elt in node.target.elts:
                if isinstance(elt, ast.Name):
                    self._register_variable(
                        name=elt.id,
                        scope=VariableScope.LOCAL,
                        node=elt,
                    )

        # 遍历循环体
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Assign):
                self._visit_assign(child, VariableScope.LOCAL)
            elif isinstance(child, ast.AnnAssign):
                self._visit_ann_assign(child, VariableScope.LOCAL)

    def _visit_with_statement(self, node: ast.With) -> None:
        """访问with语句."""
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                self._register_variable(
                    name=item.optional_vars.id,
                    scope=VariableScope.LOCAL,
                    node=item.optional_vars,
                )

    def _visit_import(self, node: ast.Import) -> None:
        """访问import语句."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name.split(".")[0]
            self._register_variable(
                name=name,
                scope=VariableScope.IMPORT,
                node=node,
            )

    def _visit_if_statement(self, node: ast.If) -> None:
        """访问if语句（提取条件中的变量赋值）."""
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Assign):
                self._visit_assign(child, VariableScope.LOCAL)
            elif isinstance(child, ast.AnnAssign):
                self._visit_ann_assign(child, VariableScope.LOCAL)
            elif isinstance(child, ast.If):
                self._visit_if_statement(child)

    def _visit_try_statement(self, node: ast.Try) -> None:
        """访问try语句（提取except中的变量）."""
        for handler in node.handlers:
            if handler.name:
                self._register_variable(
                    name=handler.name,
                    scope=VariableScope.LOCAL,
                    node=handler,
                    type_annotation="BaseException" if not handler.type else "",
                )

        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.Assign):
                self._visit_assign(child, VariableScope.LOCAL)
            elif isinstance(child, ast.AnnAssign):
                self._visit_ann_assign(child, VariableScope.LOCAL)

    def _visit_comprehension(self, node: ast.AST) -> None:
        """访问列表/集合/生成器推导式."""
        if hasattr(node, "generators"):
            for gen in node.generators:
                if isinstance(gen.target, ast.Name):
                    self._register_variable(
                        name=gen.target.id,
                        scope=VariableScope.LOCAL,
                        node=gen.target,
                    )

    def _visit_dict_comprehension(self, node: ast.DictComp) -> None:
        """访问字典推导式."""
        for gen in node.generators:
            if isinstance(gen.target, ast.Name):
                self._register_variable(
                    name=gen.target.id,
                    scope=VariableScope.LOCAL,
                    node=gen.target,
                )

    # ========== 依赖分析 ==========

    def _extract_dependencies(self, value_node: ast.AST, var_name: str) -> None:
        """从赋值右侧表达式提取变量依赖.

        Args:
            value_node: 右侧表达式AST节点
            var_name: 被赋值的变量名
        """
        dep_names: Set[str] = set()
        self._collect_names(value_node, dep_names)

        key = self._unique_key(var_name)
        if key in self._variables:
            for dep in dep_names:
                self._variables[key].add_dependency(dep)
                # 反向依赖
                dep_key = self._unique_key(dep)
                if dep_key in self._variables:
                    self._variables[dep_key].add_dependent(var_name)

    def _collect_names(self, node: ast.AST, names: Set[str]) -> None:
        """递归收集AST节点中引用的所有名称."""
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (ast.Call, ast.Subscript)):
            for child in ast.iter_child_nodes(node):
                self._collect_names(child, names)
        elif isinstance(node, ast.BinOp):
            self._collect_names(node.left, names)
            self._collect_names(node.right, names)
        elif isinstance(node, ast.UnaryOp):
            self._collect_names(node.operand, names)
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for elt in node.elts:
                self._collect_names(elt, names)
        elif isinstance(node, ast.Dict):
            for k in node.keys:
                if k:
                    self._collect_names(k, names)
            for v in node.values:
                self._collect_names(v, names)
        elif isinstance(node, ast.IfExp):
            self._collect_names(node.test, names)
            self._collect_names(node.body, names)
            self._collect_names(node.orelse, names)
        elif isinstance(node, (ast.Lambda,)):
            pass  # lambda内部作用域，不收集
        elif isinstance(node, (ast.JoinedStr,)):  # f-string
            for value in node.values:
                if isinstance(value, ast.FormattedValue):
                    self._collect_names(value.value, names)

    # ========== 引用分析 ==========

    def _analyze_references(self) -> None:
        """分析所有变量的引用情况（后处理）.

        遍历整个AST，统计每个Name节点的读写情况。
        """
        # 收集所有赋值目标名称
        assigned_names: Set[str] = set()
        self._collect_assigned_names(self._tree, assigned_names)

        # 遍历所有Name节点
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Name):
                name = node.id
                # 查找对应的变量原子
                atom = self._find_variable(name)
                if atom:
                    ctx = "write" if isinstance(node.ctx, ast.Store) else "read"
                    atom.add_reference(
                        location=self._make_location(node),
                        context=ctx,
                        scope_name=self._current_scope(),
                    )

    def _collect_assigned_names(self, node: ast.AST, names: Set[str]) -> None:
        """收集所有被赋值的名称."""
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                names.add(child.id)

    def _find_variable(self, name: str) -> Optional[VariableAtom]:
        """按名称查找变量原子（支持模糊匹配）."""
        # 精确匹配
        key = self._unique_key(name)
        if key in self._variables:
            return self._variables[key]

        # 回退：按名称搜索
        for var in self._variables.values():
            if var.name == name:
                return var

        return None
