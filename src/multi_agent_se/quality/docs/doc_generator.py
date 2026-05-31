"""文档生成器 - 阶段24.

从Python源码自动生成文档：
- AST解析提取函数/类/模块文档
- README生成
- API文档生成
- 变更日志生成
"""

import ast
import inspect
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from multi_agent_se.quality.docs.doc_models import (
    APIEntry,
    ChangelogEntry,
    ChangeType,
    DocFormat,
    DocMetadata,
    DocSection,
    DocType,
    Document,
    ParamInfo,
    create_api_entry,
    create_changelog,
    create_section,
)


# ========== AST文档提取器 ==========

class ASTDocExtractor:
    """从Python AST提取文档信息."""

    def extract_module(self, source: str, file_path: str = "") -> Dict[str, Any]:
        """提取模块级文档信息.

        Returns:
            {
                "docstring": str,
                "functions": List[APIEntry],
                "classes": List[APIEntry],
                "imports": List[str],
            }
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {"docstring": "", "functions": [], "classes": [], "imports": []}

        module_doc = ast.get_docstring(tree) or ""
        functions = []
        classes = []
        imports = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(self._extract_function(node, file_path))
            elif isinstance(node, ast.ClassDef):
                classes.append(self._extract_class(node, file_path))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(self._extract_import(node))

        return {
            "docstring": module_doc,
            "functions": functions,
            "classes": classes,
            "imports": imports,
        }

    def _extract_function(self, node: ast.FunctionDef, file_path: str = "") -> APIEntry:
        """提取函数文档."""
        name = node.name
        docstring = ast.get_docstring(node) or ""

        # 构建签名
        args = self._extract_args(node)
        signature = f"def {name}({args})"
        if node.returns and hasattr(node.returns, 'id'):
            signature += f" -> {node.returns.id}"
        elif node.returns:
            signature += " -> ..."

        # 提取参数信息
        params = self._extract_params(node)

        # 提取返回值描述
        returns = self._parse_returns(docstring)

        return APIEntry(
            name=name,
            doc_type=DocType.FUNCTION,
            signature=signature,
            description=docstring.split("\n\n")[0] if docstring else "",
            params=params,
            returns=returns,
            module=file_path,
        )

    def _extract_class(self, node: ast.ClassDef, file_path: str = "") -> APIEntry:
        """提取类文档."""
        name = node.name
        docstring = ast.get_docstring(node) or ""

        # 基类
        bases = [self._ast_to_str(b) for b in node.bases]
        signature = f"class {name}"
        if bases:
            signature += f"({', '.join(bases)})"

        # 提取方法列表
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)

        description = docstring.split("\n\n")[0] if docstring else ""
        if methods:
            description += f"\n\nMethods: {', '.join(methods)}"

        return APIEntry(
            name=name,
            doc_type=DocType.CLASS,
            signature=signature,
            description=description.strip(),
            module=file_path,
        )

    def _extract_args(self, node: ast.FunctionDef) -> str:
        """提取函数参数字符串."""
        args_parts = []
        for arg in node.args.args:
            arg_name = arg.arg
            if arg_name == "self":
                continue
            annotation = ""
            if arg.annotation and hasattr(arg.annotation, 'id'):
                annotation = f": {arg.annotation.id}"
            elif arg.annotation:
                annotation = ": ..."
            args_parts.append(f"{arg_name}{annotation}")

        # 默认参数
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            idx = defaults_offset + i
            if idx < len(args_parts):
                default_str = self._ast_to_str(default)
                args_parts[idx] += f" = {default_str}"

        # *args
        if node.args.vararg:
            args_parts.append(f"*{node.args.vararg.arg}")

        # **kwargs
        if node.args.kwarg:
            args_parts.append(f"**{node.args.kwarg.arg}")

        return ", ".join(args_parts)

    def _extract_params(self, node: ast.FunctionDef) -> List[ParamInfo]:
        """提取参数信息列表."""
        params = []
        defaults_offset = len(node.args.args) - len(node.args.defaults)

        for i, arg in enumerate(node.args.args):
            if arg.arg == "self":
                continue

            type_hint = ""
            if arg.annotation and hasattr(arg.annotation, 'id'):
                type_hint = arg.annotation.id
            elif arg.annotation:
                type_hint = "..."

            default = ""
            is_optional = False
            default_idx = i - defaults_offset
            if default_idx >= 0 and default_idx < len(node.args.defaults):
                default = self._ast_to_str(node.args.defaults[default_idx])
                is_optional = True

            params.append(ParamInfo(
                name=arg.arg,
                type_hint=type_hint,
                is_optional=is_optional,
                default=default,
            ))

        return params

    def _extract_import(self, node) -> str:
        """提取导入语句."""
        if isinstance(node, ast.Import):
            return ", ".join(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = ", ".join(alias.name for alias in node.names)
            return f"from {module} import {names}"
        return ""

    def _parse_returns(self, docstring: str) -> str:
        """从docstring中解析Returns部分."""
        if not docstring:
            return ""
        match = re.search(r"Returns:\s*\n?\s*(.+?)(?:\n\n|\Z)", docstring, re.DOTALL)
        if match:
            return match.group(1).strip().split("\n")[0]
        return ""

    def _ast_to_str(self, node) -> str:
        """将AST节点转为字符串."""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_to_str(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            func = self._ast_to_str(node.func)
            args = ", ".join(self._ast_to_str(a) for a in node.args)
            return f"{func}({args})"
        elif isinstance(node, ast.List):
            return f"[{', '.join(self._ast_to_str(e) for e in node.elts)}]"
        return "..."


# ========== 文档生成器 ==========

class DocGenerator:
    """文档生成器.

    从Python源码自动生成文档
    """

    def __init__(self, project_name: str = "", version: str = "") -> None:
        self.project_name = project_name
        self.version = version
        self._extractor = ASTDocExtractor()

    def generate_readme(
        self,
        description: str = "",
        features: Optional[List[str]] = None,
        install_cmd: str = "",
        usage_example: str = "",
    ) -> Document:
        """生成README文档.

        Args:
            description: 项目描述
            features: 功能列表
            install_cmd: 安装命令
            usage_example: 使用示例

        Returns:
            Document
        """
        sections = []

        # 项目描述
        if description:
            sections.append(create_section("项目简介", description, level=2))

        # 功能特性
        if features:
            feature_lines = "\n".join(f"- {f}" for f in features)
            sections.append(create_section("功能特性", feature_lines, level=2))

        # 安装
        if install_cmd:
            sections.append(create_section(
                "安装",
                f"```bash\n{install_cmd}\n```",
                level=2,
            ))

        # 使用示例
        if usage_example:
            sections.append(create_section(
                "使用示例",
                f"```python\n{usage_example}\n```",
                level=2,
            ))

        metadata = DocMetadata(
            title=self.project_name or "Project",
            version=self.version,
            doc_type=DocType.README,
        )

        return Document(metadata=metadata, sections=sections)

    def generate_api_doc(self, source: str, file_path: str = "") -> Document:
        """从源码生成API文档.

        Args:
            source: Python源码
            file_path: 文件路径

        Returns:
            Document
        """
        info = self._extractor.extract_module(source, file_path)

        sections = []
        if info["docstring"]:
            sections.append(create_section("模块说明", info["docstring"], level=2))

        # 函数文档
        if info["functions"]:
            sections.append(create_section("函数", "", level=2))

        # 类文档
        if info["classes"]:
            sections.append(create_section("类", "", level=2))

        metadata = DocMetadata(
            title=file_path or "API Documentation",
            doc_type=DocType.API,
        )

        return Document(
            metadata=metadata,
            sections=sections,
            api_entries=info["functions"] + info["classes"],
        )

    def generate_changelog(
        self,
        entries: Optional[List[ChangelogEntry]] = None,
    ) -> Document:
        """生成变更日志.

        Args:
            entries: 变更条目列表

        Returns:
            Document
        """
        metadata = DocMetadata(
            title="Changelog",
            doc_type=DocType.CHANGELOG,
        )

        return Document(
            metadata=metadata,
            changelog=entries or [],
        )

    def generate_module_doc(self, source: str, file_path: str = "") -> Document:
        """生成模块文档.

        Args:
            source: Python源码
            file_path: 文件路径

        Returns:
            Document
        """
        info = self._extractor.extract_module(source, file_path)

        sections = []

        # 模块文档字符串
        if info["docstring"]:
            sections.append(create_section("概述", info["docstring"], level=2))

        # 导入
        if info["imports"]:
            import_lines = "\n".join(f"- `{imp}`" for imp in info["imports"])
            sections.append(create_section("导入", import_lines, level=2))

        # API条目
        api_entries = info["functions"] + info["classes"]

        metadata = DocMetadata(
            title=file_path or "Module Documentation",
            doc_type=DocType.MODULE,
        )

        return Document(
            metadata=metadata,
            sections=sections,
            api_entries=api_entries,
        )


# ========== 便捷函数 ==========

def generate_readme(
    project_name: str,
    description: str = "",
    features: Optional[List[str]] = None,
) -> str:
    """快速生成README的便捷函数."""
    gen = DocGenerator(project_name=project_name)
    doc = gen.generate_readme(description=description, features=features)
    return doc.to_markdown()


def generate_api_doc(source: str, file_path: str = "") -> str:
    """快速生成API文档的便捷函数."""
    gen = DocGenerator()
    doc = gen.generate_api_doc(source, file_path)
    return doc.to_markdown()


def extract_docstring(source: str) -> str:
    """提取模块文档字符串."""
    extractor = ASTDocExtractor()
    info = extractor.extract_module(source)
    return info["docstring"]
