"""模块提取器 - 阶段30."""

import ast
from pathlib import Path
from typing import List, Optional

from multi_agent_se.atomicity.module_atom.models import ImportInfo, ModuleAtom, ExportInfo


class ModuleExtractor:
    """模块提取器."""

    def __init__(self, source: str, file_path: str = "") -> None:
        self._source = source
        self._file_path = file_path
        self._tree = ast.parse(source)
        self._module_name = Path(file_path).stem if file_path else ""

    @classmethod
    def from_file(cls, file_path: str) -> "ModuleExtractor":
        source = Path(file_path).read_text(encoding="utf-8")
        return cls(source, file_path=file_path)

    def extract(self) -> ModuleAtom:
        """提取模块原子."""
        atom = ModuleAtom(
            name=self._module_name,
            file_path=self._file_path,
        )

        # 文档字符串
        atom.docstring = ast.get_docstring(self._tree) or ""

        # 分析模块内容
        for node in ast.iter_child_nodes(self._tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    atom.imports.append(ImportInfo(
                        name=alias.asname if alias.asname else alias.name,
                        module=alias.name,
                        is_from_import=False,
                        alias=alias.asname or "",
                        line_number=node.lineno,
                    ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    atom.imports.append(ImportInfo(
                        name=alias.asname if alias.asname else alias.name,
                        module=module,
                        is_from_import=True,
                        is_relative=node.level > 0,
                        alias=alias.asname or "",
                        line_number=node.lineno,
                    ))
            elif isinstance(node, ast.ClassDef):
                atom.classes.append(node.name)
                atom.exports.append(ExportInfo(
                    name=node.name,
                    type="class",
                    is_public=not node.name.startswith("_"),
                    line_number=node.lineno,
                ))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                atom.functions.append(node.name)
                atom.exports.append(ExportInfo(
                    name=node.name,
                    type="function",
                    is_public=not node.name.startswith("_"),
                    line_number=node.lineno,
                ))
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        atom.global_variables.append(target.id)

        # 代码统计
        lines = self._source.splitlines()
        atom.lines_of_code = len(lines)
        atom.blank_lines = sum(1 for line in lines if not line.strip())
        atom.comment_lines = sum(1 for line in lines if line.strip().startswith("#"))

        return atom
