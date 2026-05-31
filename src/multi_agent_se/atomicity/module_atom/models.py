"""模块原子模型 - 阶段30.

第四级代码原子化：模块原子（Module Atom）

封装单个模块的完整信息：
- 导入导出符号
- 全局变量和函数
- 模块级文档
- 依赖关系图
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class ImportInfo:
    """导入信息."""
    name: str = ""
    module: str = ""
    is_from_import: bool = False
    is_relative: bool = False
    alias: str = ""
    line_number: int = 0


@dataclass
class ExportInfo:
    """导出信息."""
    name: str = ""
    type: str = ""  # class/function/variable
    is_public: bool = True
    line_number: int = 0


@dataclass
class ModuleAtom:
    """模块原子.

    封装单个模块的完整信息，是四级原子化体系的第四级。
    """
    name: str = ""
    atom_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    file_path: str = ""
    
    # 文档
    docstring: str = ""
    
    # 导入导出
    imports: List[ImportInfo] = field(default_factory=list)
    exports: List[ExportInfo] = field(default_factory=list)
    
    # 模块级成员
    global_variables: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    
    # 依赖
    dependent_modules: List[str] = field(default_factory=list)
    
    # 度量
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    
    @property
    def all_exports(self) -> List[str]:
        """获取所有导出符号."""
        return [e.name for e in self.exports if e.is_public]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "name": self.name,
            "file_path": self.file_path,
            "docstring": self.docstring[:200] if self.docstring else "",
            "imports": len(self.imports),
            "exports": len(self.exports),
            "classes": len(self.classes),
            "functions": len(self.functions),
            "lines_of_code": self.lines_of_code,
        }


@dataclass
class ModuleMetrics:
    """模块度量指标."""
    total_modules: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_variables: int = 0
    
    # 依赖复杂度
    avg_dependencies: float = 0.0
    max_dependencies: int = 0
    circular_dependencies: List[List[str]] = field(default_factory=list)
