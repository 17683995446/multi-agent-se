"""层间耦合检测 - 阶段11.

静态分析模块间的import关系，检测跨层耦合和违规依赖
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from multi_agent_se.core.architecture.layer_base import (
    ArchitectureLayer,
    LayerModule,
    LayerRegistry,
)


@dataclass
class ImportInfo:
    """导入信息."""
    module: str           # 导入的模块名
    source_file: str      # 来源文件
    import_type: str      # import / from_import
    line: int = 0
    names: List[str] = field(default_factory=list)  # 具体导入的名称

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "source_file": self.source_file,
            "import_type": self.import_type,
            "line": self.line,
            "names": self.names,
        }


@dataclass
class CouplingRecord:
    """耦合记录."""
    source_module: str
    source_layer: Optional[ArchitectureLayer]
    target_module: str
    target_layer: Optional[ArchitectureLayer]
    source_file: str
    line: int = 0
    is_cross_layer: bool = False
    is_violation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_module,
            "source_layer": self.source_layer.name if self.source_layer else "unknown",
            "target": self.target_module,
            "target_layer": self.target_layer.name if self.target_layer else "unknown",
            "source_file": self.source_file,
            "line": self.line,
            "is_cross_layer": self.is_cross_layer,
            "is_violation": self.is_violation,
        }


@dataclass
class CouplingReport:
    """耦合检测报告."""
    records: List[CouplingRecord] = field(default_factory=list)
    total_imports: int = 0
    cross_layer_imports: int = 0
    violations: int = 0
    intra_layer_imports: int = 0
    unknown_layer_imports: int = 0

    @property
    def coupling_score(self) -> float:
        """耦合评分 (0-100, 越高越好).

        100 = 零违规, 0 = 全部违规
        """
        if self.total_imports == 0:
            return 100.0
        return (1.0 - self.violations / self.total_imports) * 100.0

    @property
    def is_healthy(self) -> bool:
        """耦合是否健康（无违规）."""
        return self.violations == 0

    def get_violations(self) -> List[CouplingRecord]:
        """获取所有违规记录."""
        return [r for r in self.records if r.is_violation]

    def get_cross_layer(self) -> List[CouplingRecord]:
        """获取所有跨层记录."""
        return [r for r in self.records if r.is_cross_layer]

    def get_by_source_layer(self) -> Dict[str, List[CouplingRecord]]:
        """按源层分组."""
        grouped: Dict[str, List[CouplingRecord]] = {}
        for r in self.records:
            key = r.source_layer.name if r.source_layer else "unknown"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)
        return grouped

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_healthy": self.is_healthy,
            "coupling_score": round(self.coupling_score, 2),
            "total_imports": self.total_imports,
            "cross_layer_imports": self.cross_layer_imports,
            "intra_layer_imports": self.intra_layer_imports,
            "unknown_layer_imports": self.unknown_layer_imports,
            "violations": self.violations,
            "by_source_layer": {
                k: len(v) for k, v in self.get_by_source_layer().items()
            },
        }


class CouplingDetector:
    """层间耦合检测器.

    通过静态分析Python源码中的import语句，
    检测跨层耦合和违规依赖
    """

    # 模块名到架构层的映射规则
    LAYER_PREFIX_MAP: Dict[str, ArchitectureLayer] = {
        "multi_agent_se.agents": ArchitectureLayer.AGENT,
        "multi_agent_se.collaboration": ArchitectureLayer.SCHEDULER,
        "multi_agent_se.pipeline": ArchitectureLayer.SCHEDULER,
        "multi_agent_se.core": ArchitectureLayer.EXECUTOR,
        "multi_agent_se.atomicity": ArchitectureLayer.EXECUTOR,
        "multi_agent_se.quality": ArchitectureLayer.EXECUTOR,
        "multi_agent_se.utils": ArchitectureLayer.EXECUTOR,
    }

    def __init__(
        self,
        registry: Optional[LayerRegistry] = None,
        project_root: Optional[str] = None,
    ) -> None:
        """初始化检测器.

        Args:
            registry: 层注册表
            project_root: 项目根目录
        """
        self._registry = registry or LayerRegistry()
        self._project_root = Path(project_root) if project_root else None

    def _resolve_layer(self, module_name: str) -> Optional[ArchitectureLayer]:
        """根据模块名推断所属架构层.

        Args:
            module_name: 模块名（如 multi_agent_se.agents.controller）

        Returns:
            架构层（无法推断返回None）
        """
        for prefix, layer in self.LAYER_PREFIX_MAP.items():
            if module_name == prefix or module_name.startswith(prefix + "."):
                return layer
        return None

    def _extract_imports(self, source: str, file_path: str = "") -> List[ImportInfo]:
        """从Python源码中提取import信息.

        Args:
            source: Python源码
            file_path: 文件路径（用于记录）

        Returns:
            ImportInfo列表
        """
        imports = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        source_file=file_path,
                        import_type="import",
                        line=node.lineno,
                        names=[alias.asname or alias.name],
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [
                        alias.asname or alias.name
                        for alias in node.names
                    ]
                    imports.append(ImportInfo(
                        module=node.module,
                        source_file=file_path,
                        import_type="from_import",
                        line=node.lineno,
                        names=names,
                    ))

        return imports

    def analyze_source(
        self,
        source: str,
        file_path: str = "",
        source_layer: Optional[ArchitectureLayer] = None,
    ) -> List[CouplingRecord]:
        """分析单个源文件的耦合.

        Args:
            source: Python源码
            file_path: 文件路径
            source_layer: 来源文件所属层（None则自动推断）

        Returns:
            CouplingRecord列表
        """
        imports = self._extract_imports(source, file_path)
        records = []

        for imp in imports:
            # 只分析项目内部模块
            if not imp.module.startswith("multi_agent_se"):
                continue

            target_layer = self._resolve_layer(imp.module)
            is_cross = (
                source_layer is not None
                and target_layer is not None
                and source_layer != target_layer
            )
            is_violation = False
            if source_layer is not None and target_layer is not None:
                is_violation = not source_layer.can_depend_on(target_layer)

            records.append(CouplingRecord(
                source_module=file_path,
                source_layer=source_layer,
                target_module=imp.module,
                target_layer=target_layer,
                source_file=file_path,
                line=imp.line,
                is_cross_layer=is_cross,
                is_violation=is_violation,
            ))

        return records

    def analyze_file(
        self,
        file_path: str,
        source_layer: Optional[ArchitectureLayer] = None,
    ) -> List[CouplingRecord]:
        """分析单个文件的耦合.

        Args:
            file_path: 文件路径
            source_layer: 所属层

        Returns:
            CouplingRecord列表
        """
        path = Path(file_path)
        if not path.exists():
            return []

        source = path.read_text(encoding="utf-8", errors="ignore")

        # 自动推断所属层
        if source_layer is None and self._project_root:
            try:
                rel = path.resolve().relative_to(self._project_root / "src")
                module_name = "multi_agent_se." + str(rel.with_suffix("")).replace("/", ".")
                source_layer = self._resolve_layer(module_name)
            except ValueError:
                pass

        return self.analyze_source(source, str(path), source_layer)

    def analyze_directory(
        self,
        directory: str,
        pattern: str = "*.py",
    ) -> CouplingReport:
        """分析目录下所有Python文件.

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            CouplingReport
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return CouplingReport()

        all_records: List[CouplingRecord] = []
        for py_file in sorted(dir_path.rglob(pattern)):
            records = self.analyze_file(str(py_file))
            all_records.extend(records)

        return self._build_report(all_records)

    def _build_report(self, records: List[CouplingRecord]) -> CouplingReport:
        """构建耦合报告."""
        total = len(records)
        cross = sum(1 for r in records if r.is_cross_layer)
        violations = sum(1 for r in records if r.is_violation)
        intra = sum(
            1 for r in records
            if r.source_layer is not None
            and r.target_layer is not None
            and r.source_layer == r.target_layer
        )
        unknown = sum(
            1 for r in records
            if r.source_layer is None or r.target_layer is None
        )

        return CouplingReport(
            records=records,
            total_imports=total,
            cross_layer_imports=cross,
            violations=violations,
            intra_layer_imports=intra,
            unknown_layer_imports=unknown,
        )
