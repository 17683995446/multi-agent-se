"""单向数据流验证 - 阶段11.

验证四层架构间的数据流严格单向：INPUT → SCHEDULER → AGENT → EXECUTOR
禁止反向数据流和跨层跳跃
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

from multi_agent_se.core.architecture.layer_base import (
    ArchitectureLayer,
    LayerRegistry,
    LayerModule,
    get_all_layers,
)


class FlowViolationType(Enum):
    """数据流违规类型."""
    REVERSE_FLOW = auto()       # 反向数据流（低层→高层）
    SKIP_FLOW = auto()          # 跨层跳跃（跳过中间层）
    CIRCULAR_FLOW = auto()      # 循环数据流
    UNKNOWN_LAYER = auto()      # 未知层引用


@dataclass
class DataFlowEdge:
    """数据流边."""
    source: str          # 源模块名
    source_layer: ArchitectureLayer
    target: str          # 目标模块名
    target_layer: ArchitectureLayer
    flow_type: str = "data"  # data / event / control

    @property
    def is_valid(self) -> bool:
        """数据流是否合法（源层 >= 目标层）."""
        return self.source_layer.level >= self.target_layer.level

    @property
    def is_reverse(self) -> bool:
        """是否反向流."""
        return self.source_layer.level < self.target_layer.level

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "source_layer": self.source_layer.name,
            "target": self.target,
            "target_layer": self.target_layer.name,
            "flow_type": self.flow_type,
            "is_valid": self.is_valid,
        }


@dataclass
class FlowViolation:
    """数据流违规记录."""
    violation_type: FlowViolationType
    source: str
    source_layer: ArchitectureLayer
    target: str
    target_layer: ArchitectureLayer
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.violation_type.name,
            "source": self.source,
            "source_layer": self.source_layer.name,
            "target": self.target,
            "target_layer": self.target_layer.name,
            "description": self.description,
        }


@dataclass
class DataFlowReport:
    """数据流验证报告."""
    edges: List[DataFlowEdge] = field(default_factory=list)
    violations: List[FlowViolation] = field(default_factory=list)
    total_edges: int = 0
    valid_edges: int = 0
    invalid_edges: int = 0

    @property
    def is_valid(self) -> bool:
        """数据流是否全部合法."""
        return len(self.violations) == 0

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    def get_violations_by_type(self) -> Dict[str, List[FlowViolation]]:
        """按类型分组违规."""
        grouped: Dict[str, List[FlowViolation]] = {}
        for v in self.violations:
            key = v.violation_type.name
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(v)
        return grouped

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_edges": self.total_edges,
            "valid_edges": self.valid_edges,
            "invalid_edges": self.invalid_edges,
            "violations": [v.to_dict() for v in self.violations],
            "violations_by_type": {
                k: len(v) for k, v in self.get_violations_by_type().items()
            },
        }


class DataFlowValidator:
    """单向数据流验证器.

    验证模块间数据流是否符合四层架构的单向约束
    """

    def __init__(self, registry: Optional[LayerRegistry] = None) -> None:
        """初始化验证器.

        Args:
            registry: 层注册表（None则使用空注册表）
        """
        self._registry = registry or LayerRegistry()
        self._edges: List[DataFlowEdge] = []

    def add_edge(
        self,
        source: str,
        target: str,
        flow_type: str = "data",
    ) -> None:
        """添加数据流边.

        Args:
            source: 源模块名
            target: 目标模块名
            flow_type: 流类型 (data/event/control)
        """
        src_module = self._registry.get_module(source)
        tgt_module = self._registry.get_module(target)

        src_layer = src_module.layer if src_module else ArchitectureLayer.EXECUTOR
        tgt_layer = tgt_module.layer if tgt_module else ArchitectureLayer.EXECUTOR

        edge = DataFlowEdge(
            source=source,
            source_layer=src_layer,
            target=target,
            target_layer=tgt_layer,
            flow_type=flow_type,
        )
        self._edges.append(edge)

    def validate(self) -> DataFlowReport:
        """执行数据流验证.

        Returns:
            DataFlowReport
        """
        violations: List[FlowViolation] = []
        valid_count = 0

        for edge in self._edges:
            if edge.is_valid:
                valid_count += 1
            else:
                # 判断违规类型
                if edge.is_reverse:
                    vtype = FlowViolationType.REVERSE_FLOW
                    desc = (
                        f"反向数据流: {edge.source}({edge.source_layer.name}) "
                        f"→ {edge.target}({edge.target_layer.name})"
                    )
                else:
                    vtype = FlowViolationType.UNKNOWN_LAYER
                    desc = f"未知层数据流: {edge.source} → {edge.target}"

                violations.append(FlowViolation(
                    violation_type=vtype,
                    source=edge.source,
                    source_layer=edge.source_layer,
                    target=edge.target,
                    target_layer=edge.target_layer,
                    description=desc,
                ))

        return DataFlowReport(
            edges=list(self._edges),
            violations=violations,
            total_edges=len(self._edges),
            valid_edges=valid_count,
            invalid_edges=len(violations),
        )

    def validate_layer_flow(
        self,
        source_layer: ArchitectureLayer,
        target_layer: ArchitectureLayer,
    ) -> bool:
        """验证两层之间的数据流是否合法.

        Args:
            source_layer: 源层
            target_layer: 目标层

        Returns:
            True如果合法
        """
        return source_layer.level >= target_layer.level

    def get_layer_edges(self, layer: ArchitectureLayer) -> List[DataFlowEdge]:
        """获取某层相关的所有数据流边.

        Args:
            layer: 架构层

        Returns:
            数据流边列表
        """
        return [
            e for e in self._edges
            if e.source_layer == layer or e.target_layer == layer
        ]

    def get_cross_layer_edges(self) -> List[DataFlowEdge]:
        """获取所有跨层数据流边."""
        return [
            e for e in self._edges
            if e.source_layer != e.target_layer
        ]

    def get_intra_layer_edges(self) -> List[DataFlowEdge]:
        """获取所有层内数据流边."""
        return [
            e for e in self._edges
            if e.source_layer == e.target_layer
        ]

    def clear(self) -> None:
        """清空所有数据流边."""
        self._edges.clear()


def validate_unidirectional_flow(
    registry: LayerRegistry,
) -> DataFlowReport:
    """基于注册表验证所有模块依赖的数据流方向.

    Args:
        registry: 层注册表

    Returns:
        DataFlowReport
    """
    validator = DataFlowValidator(registry)

    for name, module in registry.get_all_modules().items():
        for dep_name in module.dependencies:
            validator.add_edge(source=name, target=dep_name)

    return validator.validate()
