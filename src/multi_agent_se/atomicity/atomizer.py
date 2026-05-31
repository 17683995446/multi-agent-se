"""CodeAtomizer - 四级代码原子化整合门面类 - 阶段30.

提供统一的代码原子化分解接口，整合：
- 第一级：变量原子 (VariableAtom)
- 第二级：方法原子 (MethodAtom)
- 第三级：类原子 (ClassAtom)
- 第四级：模块原子 (ModuleAtom)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from multi_agent_se.atomicity.variable.extractor import VariableExtractor
from multi_agent_se.atomicity.variable.models import VariableAtom
from multi_agent_se.atomicity.method.extractor import MethodExtractor
from multi_agent_se.atomicity.method.models import MethodAtom
from multi_agent_se.atomicity.class_atom.extractor import ClassExtractor
from multi_agent_se.atomicity.class_atom.models import ClassAtom
from multi_agent_se.atomicity.module_atom.extractor import ModuleExtractor
from multi_agent_se.atomicity.module_atom.models import ModuleAtom, ModuleMetrics


@dataclass
class AtomizationResult:
    """原子化结果."""
    file_path: str = ""
    module: Optional[ModuleAtom] = None
    classes: List[ClassAtom] = field(default_factory=list)
    methods: List[MethodAtom] = field(default_factory=list)
    variables: List[VariableAtom] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "module": self.module.to_dict() if self.module else None,
            "classes": [c.to_dict() for c in self.classes],
            "methods": [m.to_dict() for m in self.methods],
            "variables": [v.to_dict() for v in self.variables],
        }
    
    def summary(self) -> str:
        """生成摘要."""
        lines = [f"文件: {self.file_path}"]
        if self.module:
            lines.append(f"  模块: {self.module.name}")
        lines.append(f"  类: {len(self.classes)}个")
        lines.append(f"  方法: {len(self.methods)}个")
        lines.append(f"  变量: {len(self.variables)}个")
        return "\n".join(lines)


class CodeAtomizer:
    """代码原子化器.
    
    统一的四级代码原子化分解门面类。
    """
    
    def __init__(self) -> None:
        self._results: List[AtomizationResult] = []
    
    def atomize_file(self, file_path: str) -> AtomizationResult:
        """对单个文件进行原子化分解.
        
        Args:
            file_path: Python源文件路径
            
        Returns:
            原子化结果
        """
        source = Path(file_path).read_text(encoding="utf-8")
        return self.atomize_source(source, file_path)
    
    def atomize_source(self, source: str, file_path: str = "") -> AtomizationResult:
        """对源码进行原子化分解.
        
        Args:
            source: Python源码字符串
            file_path: 源文件路径（可选）
            
        Returns:
            原子化结果
        """
        result = AtomizationResult(file_path=file_path)
        
        # 第四级：模块原子
        module_extractor = ModuleExtractor(source, file_path)
        result.module = module_extractor.extract()
        
        # 第三级：类原子
        class_extractor = ClassExtractor(source, file_path)
        result.classes = class_extractor.extract()
        
        # 第二级：方法原子
        method_extractor = MethodExtractor(source, file_path)
        result.methods = method_extractor.extract()
        
        # 第一级：变量原子
        variable_extractor = VariableExtractor(source, file_path)
        result.variables = variable_extractor.extract()
        
        return result
    
    def atomize_directory(self, directory: str) -> List[AtomizationResult]:
        """对目录进行批量原子化分解.
        
        Args:
            directory: 目录路径
            
        Returns:
            原子化结果列表
        """
        results = []
        path = Path(directory)
        
        for py_file in path.rglob("*.py"):
            try:
                result = self.atomize_file(str(py_file))
                results.append(result)
            except Exception as e:
                print(f"处理文件失败 {py_file}: {e}")
        
        return results
    
    def get_metrics(self, results: List[AtomizationResult]) -> ModuleMetrics:
        """计算整体度量指标.
        
        Args:
            results: 原子化结果列表
            
        Returns:
            模块度量指标
        """
        metrics = ModuleMetrics()
        metrics.total_modules = len(results)
        
        for result in results:
            metrics.total_classes += len(result.classes)
            metrics.total_functions += len(result.methods)
            metrics.total_variables += len(result.variables)
        
        return metrics
