"""Pipeline模型定义 - 阶段26.

定义Pipeline编排的数据结构：
- 节点状态
- Pipeline节点（步骤）
- Pipeline边（依赖关系）
- Pipeline定义
- Pipeline执行结果
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class NodeStatus(Enum):
    """节点执行状态."""
    PENDING = "pending"          # 等待执行
    READY = "ready"              # 依赖已满足，可以执行
    RUNNING = "running"          # 正在执行
    SUCCESS = "success"          # 执行成功
    FAILED = "failed"            # 执行失败
    SKIPPED = "skipped"          # 被跳过（依赖失败）
    CANCELLED = "cancelled"      # 被取消
    RETRYING = "retrying"        # 重试中


class PipelineStatus(Enum):
    """Pipeline整体状态."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"          # 部分成功
    CANCELLED = "cancelled"


class RetryPolicy(Enum):
    """重试策略."""
    NONE = "none"                # 不重试
    FIXED = "fixed"              # 固定间隔重试
    EXPONENTIAL = "exponential"  # 指数退避重试


# ========== Pipeline节点 ==========

@dataclass
class PipelineNode:
    """Pipeline节点（一个执行步骤）.

    每个节点封装一个可执行的函数，以及其依赖关系。
    """
    name: str = ""                           # 节点唯一标识
    description: str = ""                     # 节点描述
    handler: Optional[Callable] = None        # 执行函数
    dependencies: List[str] = field(default_factory=list)  # 依赖的节点名
    timeout_seconds: float = 300.0            # 超时时间
    retry_count: int = 0                      # 重试次数
    retry_policy: RetryPolicy = RetryPolicy.NONE
    retry_delay_seconds: float = 1.0          # 重试间隔
    required: bool = True                     # 是否必须成功（失败则阻断下游）
    tags: List[str] = field(default_factory=list)

    # 运行时状态
    status: NodeStatus = NodeStatus.PENDING
    result: Any = None                        # 执行结果
    error: Optional[str] = None               # 错误信息
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    attempt: int = 0                          # 当前尝试次数

    @property
    def is_terminal(self) -> bool:
        """是否处于终态."""
        return self.status in (
            NodeStatus.SUCCESS, NodeStatus.FAILED,
            NodeStatus.SKIPPED, NodeStatus.CANCELLED,
        )

    @property
    def is_success(self) -> bool:
        return self.status == NodeStatus.SUCCESS

    @property
    def is_failed(self) -> bool:
        return self.status == NodeStatus.FAILED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "required": self.required,
            "tags": self.tags,
            "status": self.status.value,
            "duration_seconds": round(self.duration_seconds, 4),
            "error": self.error,
        }


# ========== Pipeline边 ==========

@dataclass
class PipelineEdge:
    """Pipeline边（节点间的依赖关系）."""
    source: str = ""       # 上游节点名
    target: str = ""       # 下游节点名
    data_key: str = ""     # 传递的数据键（空=传递全部结果）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "data_key": self.data_key,
        }


# ========== Pipeline定义 ==========

@dataclass
class PipelineDefinition:
    """Pipeline定义.

    描述一个完整的DAG工作流
    """
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    nodes: List[PipelineNode] = field(default_factory=list)
    edges: List[PipelineEdge] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    def add_node(self, node: PipelineNode) -> "PipelineDefinition":
        """添加节点（链式调用）."""
        self.nodes.append(node)
        return self

    def add_edge(self, source: str, target: str, data_key: str = "") -> "PipelineDefinition":
        """添加边（链式调用）."""
        self.edges.append(PipelineEdge(source=source, target=target, data_key=data_key))
        return self

    def get_node(self, name: str) -> Optional[PipelineNode]:
        """按名称获取节点."""
        for node in self.nodes:
            if node.name == name:
                return node
        return None

    def get_root_nodes(self) -> List[PipelineNode]:
        """获取根节点（无依赖的节点）."""
        return [n for n in self.nodes if len(n.dependencies) == 0]

    def get_downstream(self, node_name: str) -> List[str]:
        """获取直接下游节点."""
        return [e.target for e in self.edges if e.source == node_name]

    def get_upstream(self, node_name: str) -> List[str]:
        """获取直接上游节点."""
        return [e.source for e in self.edges if e.target == node_name]

    def topological_order(self) -> List[str]:
        """拓扑排序（Kahn算法）.

        Returns:
            节点名列表（按执行顺序）
        """
        in_degree: Dict[str, int] = {n.name: 0 for n in self.nodes}
        adj: Dict[str, List[str]] = {n.name: [] for n in self.nodes}

        # 从边构建邻接表
        for edge in self.edges:
            if edge.source in adj and edge.target in in_degree:
                if edge.target not in adj[edge.source]:
                    adj[edge.source].append(edge.target)
                    in_degree[edge.target] += 1

        # 从节点依赖补充（仅当边中未声明时）
        for node in self.nodes:
            for dep in node.dependencies:
                if dep in adj and node.name not in adj[dep]:
                    adj[dep].append(node.name)
                    in_degree[node.name] += 1

        queue = [name for name, deg in in_degree.items() if deg == 0]
        result: List[str] = []

        while queue:
            # 按添加顺序取出（保证确定性）
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            for neighbor in adj.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result

    def validate(self) -> List[str]:
        """验证Pipeline定义.

        Returns:
            错误列表，空列表表示合法
        """
        errors: List[str] = []
        node_names = {n.name for n in self.nodes}

        # 检查节点名唯一
        name_count: Dict[str, int] = {}
        for n in self.nodes:
            name_count[n.name] = name_count.get(n.name, 0) + 1
        for name, count in name_count.items():
            if count > 1:
                errors.append(f"节点名 '{name}' 重复")

        # 检查依赖引用
        for node in self.nodes:
            for dep in node.dependencies:
                if dep not in node_names:
                    errors.append(f"节点 '{node.name}' 依赖了不存在的节点 '{dep}'")

        # 检查边引用
        for edge in self.edges:
            if edge.source not in node_names:
                errors.append(f"边的源节点 '{edge.source}' 不存在")
            if edge.target not in node_names:
                errors.append(f"边的目标节点 '{edge.target}' 不存在")

        # 检查环
        order = self.topological_order()
        if len(order) != len(self.nodes):
            errors.append("Pipeline中存在循环依赖")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "tags": self.tags,
        }


# ========== Pipeline执行结果 ==========

@dataclass
class PipelineResult:
    """Pipeline执行结果."""
    pipeline_name: str = ""
    status: PipelineStatus = PipelineStatus.PENDING
    node_results: Dict[str, PipelineNode] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None

    @property
    def total_nodes(self) -> int:
        return len(self.node_results)

    @property
    def success_count(self) -> int:
        return sum(1 for n in self.node_results.values() if n.is_success)

    @property
    def failed_count(self) -> int:
        return sum(1 for n in self.node_results.values() if n.is_failed)

    @property
    def skipped_count(self) -> int:
        return sum(1 for n in self.node_results.values() if n.status == NodeStatus.SKIPPED)

    @property
    def success_rate(self) -> float:
        if self.total_nodes == 0:
            return 0.0
        return self.success_count / self.total_nodes * 100.0

    def get_failed_nodes(self) -> List[PipelineNode]:
        return [n for n in self.node_results.values() if n.is_failed]

    def get_success_nodes(self) -> List[PipelineNode]:
        return [n for n in self.node_results.values() if n.is_success]

    def format_summary(self) -> str:
        parts = [
            f"Pipeline: {self.pipeline_name}",
            f"Status: {self.status.value}",
            f"Nodes: {self.total_nodes} (success={self.success_count}, failed={self.failed_count}, skipped={self.skipped_count})",
            f"Duration: {self.duration_seconds:.3f}s",
        ]
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_name": self.pipeline_name,
            "status": self.status.value,
            "total_nodes": self.total_nodes,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "success_rate": round(self.success_rate, 2),
            "duration_seconds": round(self.duration_seconds, 3),
            "error": self.error,
            "nodes": {name: n.to_dict() for name, n in self.node_results.items()},
        }


# ========== 便捷函数 ==========

def create_node(
    name: str,
    handler: Optional[Callable] = None,
    dependencies: Optional[List[str]] = None,
    description: str = "",
    required: bool = True,
) -> PipelineNode:
    """创建Pipeline节点的便捷函数."""
    return PipelineNode(
        name=name,
        handler=handler,
        dependencies=dependencies or [],
        description=description,
        required=required,
    )


def create_pipeline(name: str, description: str = "") -> PipelineDefinition:
    """创建Pipeline定义的便捷函数."""
    return PipelineDefinition(name=name, description=description)
