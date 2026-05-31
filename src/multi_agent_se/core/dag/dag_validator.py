"""全局DAG单向依赖校验引擎 - 阶段12.

实现四大能力：
1. DAG检测算法 — 有向无环图校验
2. 循环依赖自动识别 — 运行时检测与报告
3. 依赖方向强制校验 — 与ArchitectureLayer集成
4. 违规阻断机制 — 阻止违规依赖注册
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from multi_agent_se.core.exceptions import (
    MASEError,
    SchedulerError,
    CyclicDependencyError,
)
from multi_agent_se.core.architecture.layer_base import (
    ArchitectureLayer,
    LayerModule,
    LayerRegistry,
)


# ========== 违规类型 ==========
class ViolationType(Enum):
    """依赖违规类型."""
    CYCLIC = auto()           # 循环依赖
    REVERSE_DIRECTION = auto() # 反向依赖（低层依赖高层）
    MISSING_MODULE = auto()    # 依赖的模块不存在
    DUPLICATE_EDGE = auto()    # 重复依赖边


@dataclass
class Violation:
    """依赖违规记录."""
    violation_type: ViolationType
    source: str
    target: str
    description: str = ""
    cycle_path: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.violation_type.name,
            "source": self.source,
            "target": self.target,
            "description": self.description,
        }
        if self.cycle_path:
            result["cycle_path"] = self.cycle_path
        return result


@dataclass
class DAGValidationResult:
    """DAG校验结果."""
    is_valid: bool = True
    is_dag: bool = True
    violations: List[Violation] = field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    topological_order: List[str] = field(default_factory=list)

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    @property
    def has_cycles(self) -> bool:
        return any(v.violation_type == ViolationType.CYCLIC for v in self.violations)

    @property
    def has_direction_violations(self) -> bool:
        return any(v.violation_type == ViolationType.REVERSE_DIRECTION for v in self.violations)

    def get_violations_by_type(self) -> Dict[str, List[Violation]]:
        grouped: Dict[str, List[Violation]] = {}
        for v in self.violations:
            key = v.violation_type.name
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(v)
        return grouped

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "is_dag": self.is_dag,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "violation_count": self.violation_count,
            "has_cycles": self.has_cycles,
            "has_direction_violations": self.has_direction_violations,
            "violations": [v.to_dict() for v in self.violations],
            "topological_order": self.topological_order,
        }


class DAGValidator:
    """全局DAG单向依赖校验引擎.

    核心能力：
    - 动态依赖注册（带实时校验）
    - 循环依赖自动识别（DFS算法）
    - 依赖方向强制校验（与ArchitectureLayer集成）
    - 违规阻断机制（可配置阻断策略）
    """

    def __init__(
        self,
        enforce_direction: bool = True,
        block_on_violation: bool = True,
        layer_registry: Optional[LayerRegistry] = None,
    ) -> None:
        """初始化DAG校验引擎.

        Args:
            enforce_direction: 是否强制校验依赖方向
            block_on_violation: 是否在违规时阻断注册
            layer_registry: 架构层注册表（用于方向校验）
        """
        self._adj: Dict[str, Set[str]] = {}       # 邻接表: node -> {dependents}
        self._reverse_adj: Dict[str, Set[str]] = {}  # 反向邻接表: node -> {dependencies}
        self._nodes: Set[str] = set()
        self._enforce_direction = enforce_direction
        self._block_on_violation = block_on_violation
        self._layer_registry = layer_registry or LayerRegistry()
        self._violation_history: List[Violation] = []

    # ========== 节点与边管理 ==========

    def add_node(self, name: str) -> None:
        """注册节点.

        Args:
            name: 节点名称
        """
        if name not in self._nodes:
            self._nodes.add(name)
            self._adj.setdefault(name, set())
            self._reverse_adj.setdefault(name, set())

    def add_dependency(
        self,
        source: str,
        target: str,
        layer: Optional[ArchitectureLayer] = None,
    ) -> DAGValidationResult:
        """注册依赖关系（source 依赖 target）.

        Args:
            source: 源模块（依赖方）
            target: 目标模块（被依赖方）
            layer: 源模块所属架构层（用于方向校验）

        Returns:
            DAGValidationResult

        Raises:
            CyclicDependencyError: 循环依赖且阻断模式开启
            SchedulerError: 方向违规且阻断模式开启
        """
        # 确保节点存在
        self.add_node(source)
        self.add_node(target)

        violations: List[Violation] = []

        # 1. 检查重复边
        if target in self._adj[source]:
            violations.append(Violation(
                violation_type=ViolationType.DUPLICATE_EDGE,
                source=source,
                target=target,
                description=f"重复依赖: {source} -> {target}",
            ))
            result = DAGValidationResult(
                is_valid=False,
                violations=violations,
                total_nodes=len(self._nodes),
                total_edges=self._count_edges(),
            )
            return result

        # 2. 检查循环依赖（添加边前预判）
        if self._would_create_cycle(source, target):
            cycle = self._find_cycle_if_added(source, target)
            cycle_str = " -> ".join(cycle) if cycle else f"{source} -> {target} -> ... -> {source}"
            violations.append(Violation(
                violation_type=ViolationType.CYCLIC,
                source=source,
                target=target,
                description=f"循环依赖: {cycle_str}",
                cycle_path=cycle,
            ))

            self._violation_history.extend(violations)

            if self._block_on_violation:
                raise CyclicDependencyError(
                    cycle=cycle,
                    details={"source": source, "target": target},
                )

            # 非阻断模式：记录违规但继续（不return，让下面的逻辑统一处理）

        # 3. 检查依赖方向
        if self._enforce_direction and layer is not None:
            target_layer = self._resolve_target_layer(target)
            if target_layer is not None and not layer.can_depend_on(target_layer):
                violations.append(Violation(
                    violation_type=ViolationType.REVERSE_DIRECTION,
                    source=source,
                    target=target,
                    description=(
                        f"反向依赖: {source}({layer.name}) "
                        f"不能依赖 {target}({target_layer.name})"
                    ),
                ))

                self._violation_history.extend(violations)

                if self._block_on_violation:
                    raise SchedulerError(
                        message=f"反向依赖被阻断: {source} -> {target}",
                        details={"source": source, "target": target,
                                 "source_layer": layer.name,
                                 "target_layer": target_layer.name},
                    )

        # 添加边（阻断模式下有违规则不添加）
        should_add = (not violations) or (not self._block_on_violation)
        if should_add:
            self._adj[source].add(target)
            self._reverse_adj[target].add(source)

        return DAGValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            total_nodes=len(self._nodes),
            total_edges=self._count_edges(),
        )

    def remove_dependency(self, source: str, target: str) -> bool:
        """移除依赖关系.

        Args:
            source: 源模块
            target: 目标模块

        Returns:
            是否成功移除
        """
        if target in self._adj.get(source, set()):
            self._adj[source].discard(target)
            self._reverse_adj[target].discard(source)
            return True
        return False

    def remove_node(self, name: str) -> bool:
        """移除节点及其所有关联边.

        Args:
            name: 节点名称

        Returns:
            是否成功移除
        """
        if name not in self._nodes:
            return False

        # 移除所有出边
        for dep in list(self._adj.get(name, set())):
            self._reverse_adj[dep].discard(name)
        self._adj.pop(name, None)

        # 移除所有入边
        for dep in list(self._reverse_adj.get(name, set())):
            self._adj[dep].discard(name)
        self._reverse_adj.pop(name, None)

        self._nodes.discard(name)
        return True

    # ========== DAG校验 ==========

    def is_dag(self) -> bool:
        """检查当前图是否为DAG.

        Returns:
            True如果无环
        """
        return len(self.find_cycles()) == 0

    def find_cycles(self) -> List[List[str]]:
        """查找所有循环依赖（DFS算法）.

        Returns:
            循环路径列表
        """
        cycles = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._adj.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # 找到循环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.discard(node)

        for node in sorted(self._nodes):
            if node not in visited:
                dfs(node)

        return cycles

    def validate_direction(self) -> List[Violation]:
        """校验所有边的依赖方向.

        Returns:
            违规列表
        """
        violations = []
        for source in self._nodes:
            source_layer = self._resolve_source_layer(source)
            if source_layer is None:
                continue
            for target in self._adj.get(source, set()):
                target_layer = self._resolve_target_layer(target)
                if target_layer is not None and not source_layer.can_depend_on(target_layer):
                    violations.append(Violation(
                        violation_type=ViolationType.REVERSE_DIRECTION,
                        source=source,
                        target=target,
                        description=(
                            f"反向依赖: {source}({source_layer.name}) "
                            f"-> {target}({target_layer.name})"
                        ),
                    ))
        return violations

    def full_validation(self) -> DAGValidationResult:
        """执行完整校验（DAG + 方向）.

        Returns:
            DAGValidationResult
        """
        all_violations: List[Violation] = []

        # 循环检测
        cycles = self.find_cycles()
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            all_violations.append(Violation(
                violation_type=ViolationType.CYCLIC,
                source=cycle[0] if cycle else "",
                target=cycle[-2] if len(cycle) >= 2 else "",
                description=f"循环依赖: {cycle_str}",
                cycle_path=cycle,
            ))

        # 方向校验
        if self._enforce_direction:
            all_violations.extend(self.validate_direction())

        # 拓扑排序
        topo_order = []
        if not cycles:
            topo_order = self.topological_sort()

        return DAGValidationResult(
            is_valid=len(all_violations) == 0,
            is_dag=len(cycles) == 0,
            violations=all_violations,
            total_nodes=len(self._nodes),
            total_edges=self._count_edges(),
            topological_order=topo_order,
        )

    # ========== 查询方法 ==========

    def topological_sort(self) -> List[str]:
        """拓扑排序（Kahn算法）.

        Returns:
            拓扑有序的节点列表

        Raises:
            ValueError: 存在循环依赖
        """
        if not self.is_dag():
            raise ValueError("依赖图存在循环，无法进行拓扑排序")

        in_degree: Dict[str, int] = {n: 0 for n in self._nodes}
        for source in self._nodes:
            for target in self._adj.get(source, set()):
                if target in in_degree:
                    in_degree[target] += 1

        queue = sorted([n for n, d in in_degree.items() if d == 0])
        result: List[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in sorted(self._adj.get(node, set())):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
                        queue.sort()

        return result

    def get_dependencies(self, node: str, recursive: bool = False) -> Set[str]:
        """获取节点的依赖.

        Args:
            node: 节点名称
            recursive: 是否递归获取所有传递依赖

        Returns:
            依赖节点集合
        """
        if not recursive:
            return set(self._adj.get(node, set()))

        result: Set[str] = set()
        to_visit = list(self._adj.get(node, set()))
        while to_visit:
            dep = to_visit.pop()
            if dep not in result:
                result.add(dep)
                to_visit.extend(self._adj.get(dep, set()))
        return result

    def get_dependents(self, node: str, recursive: bool = False) -> Set[str]:
        """获取依赖此节点的所有节点.

        Args:
            node: 节点名称
            recursive: 是否递归

        Returns:
            依赖方节点集合
        """
        if not recursive:
            return set(self._reverse_adj.get(node, set()))

        result: Set[str] = set()
        to_visit = list(self._reverse_adj.get(node, set()))
        while to_visit:
            dep = to_visit.pop()
            if dep not in result:
                result.add(dep)
                to_visit.extend(self._reverse_adj.get(dep, set()))
        return result

    def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """获取两节点间最短依赖路径（BFS）.

        Args:
            source: 起点
            target: 终点

        Returns:
            路径列表（不可达返回None）
        """
        if source not in self._nodes or target not in self._nodes:
            return None

        from collections import deque
        visited = {source}
        queue: deque = deque([(source, [source])])

        while queue:
            node, path = queue.popleft()
            if node == target:
                return path
            for neighbor in sorted(self._adj.get(node, set())):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    # ========== 内部方法 ==========

    def _would_create_cycle(self, source: str, target: str) -> bool:
        """预判添加边是否会创建循环.

        如果从target出发能到达source，则添加source->target会形成环
        """
        if source == target:
            return True

        visited: Set[str] = set()
        stack = [target]

        while stack:
            node = stack.pop()
            if node == source:
                return True
            if node in visited:
                continue
            visited.add(node)
            stack.extend(self._adj.get(node, set()))

        return False

    def _find_cycle_if_added(self, source: str, target: str) -> List[str]:
        """模拟添加边后查找循环路径."""
        # 临时添加边
        self._adj.setdefault(source, set()).add(target)
        self._reverse_adj.setdefault(target, set()).add(source)

        # 从source开始DFS找环
        cycle: List[str] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._adj.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    idx = path.index(neighbor)
                    cycle.extend(path[idx:] + [neighbor])
                    return True

            path.pop()
            rec_stack.discard(node)
            return False

        dfs(source)

        # 撤销临时边
        self._adj[source].discard(target)
        self._reverse_adj[target].discard(source)

        return cycle

    def _resolve_target_layer(self, target: str) -> Optional[ArchitectureLayer]:
        """根据目标模块名推断架构层."""
        # 先查注册表
        mod = self._layer_registry.get_module(target)
        if mod:
            return mod.layer

        # 按前缀推断
        prefix_map = {
            "agents.": ArchitectureLayer.AGENT,
            "agent_": ArchitectureLayer.AGENT,
            "collaboration.": ArchitectureLayer.SCHEDULER,
            "pipeline.": ArchitectureLayer.SCHEDULER,
            "core.": ArchitectureLayer.EXECUTOR,
            "core_": ArchitectureLayer.EXECUTOR,
            "atomicity.": ArchitectureLayer.EXECUTOR,
            "quality.": ArchitectureLayer.EXECUTOR,
            "quality_": ArchitectureLayer.EXECUTOR,
            "utils.": ArchitectureLayer.EXECUTOR,
            "utils_": ArchitectureLayer.EXECUTOR,
        }
        for prefix, layer in prefix_map.items():
            if target.startswith(prefix):
                return layer
        return None

    def _resolve_source_layer(self, source: str) -> Optional[ArchitectureLayer]:
        """根据源模块名推断架构层."""
        return self._resolve_target_layer(source)  # 同一逻辑

    def _count_edges(self) -> int:
        """计算总边数."""
        return sum(len(targets) for targets in self._adj.values())

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return self._count_edges()

    @property
    def violation_history(self) -> List[Violation]:
        """获取历史违规记录."""
        return list(self._violation_history)

    def clear(self) -> None:
        """清空DAG."""
        self._adj.clear()
        self._reverse_adj.clear()
        self._nodes.clear()
        self._violation_history.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取DAG统计信息."""
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "is_dag": self.is_dag(),
            "violation_history_count": len(self._violation_history),
        }


# ========== 全局DAG校验器实例 ==========
dag_validator = DAGValidator(
    enforce_direction=True,
    block_on_violation=True,
)
