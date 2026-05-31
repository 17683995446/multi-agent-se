"""架构层基础定义 - 阶段11.

落地系统四层架构：输入层 → 调度层 → Agent层 → 执行层
定义层抽象基类、层注册表、层间接口协议
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type


# ========== 四层架构枚举 ==========
class ArchitectureLayer(Enum):
    """系统四层架构.

    层级从高到低：INPUT > SCHEDULER > AGENT > EXECUTOR
    数据流方向：INPUT → SCHEDULER → AGENT → EXECUTOR（单向）
    依赖方向：高层可依赖低层，低层不可依赖高层
    """
    INPUT = 3       # 输入收敛层 — 用户请求接入、预处理、标准化
    SCHEDULER = 2   # 调度中枢层 — 任务分解、DAG调度、状态管理
    AGENT = 1       # 智能协作层 — 8个正交Agent协作执行
    EXECUTOR = 0    # 原子执行层 — 代码解析、质量检查、文件操作

    @property
    def level(self) -> int:
        """层级序号（越大越高）."""
        return self.value

    @property
    def label(self) -> str:
        """中文标签."""
        labels = {
            ArchitectureLayer.INPUT: "输入收敛层",
            ArchitectureLayer.SCHEDULER: "调度中枢层",
            ArchitectureLayer.AGENT: "智能协作层",
            ArchitectureLayer.EXECUTOR: "原子执行层",
        }
        return labels[self]

    @property
    def description(self) -> str:
        """层描述."""
        descs = {
            ArchitectureLayer.INPUT: "用户请求接入、预处理、标准化",
            ArchitectureLayer.SCHEDULER: "任务分解、DAG调度、状态管理",
            ArchitectureLayer.AGENT: "8个正交Agent协作执行",
            ArchitectureLayer.EXECUTOR: "代码解析、质量检查、文件操作",
        }
        return descs[self]

    def can_depend_on(self, other: "ArchitectureLayer") -> bool:
        """判断本层是否可以依赖目标层.

        规则：只能依赖同级或更低层级（序号 <= 本层序号）

        Args:
            other: 目标层

        Returns:
            True如果允许依赖
        """
        return other.level <= self.level

    def is_lower_than(self, other: "ArchitectureLayer") -> bool:
        """判断本层是否低于目标层."""
        return self.level < other.level

    def is_higher_than(self, other: "ArchitectureLayer") -> bool:
        """判断本层是否高于目标层."""
        return self.level > other.level


# ========== 层接口协议 ==========
class LayerInterface(ABC):
    """架构层抽象基类.

    每个架构层实现此接口，定义：
    - 层级标识
    - 入口/出口数据格式
    - 层内模块注册
    """

    @property
    @abstractmethod
    def layer(self) -> ArchitectureLayer:
        """本层所属架构层级."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """层实例名称."""
        ...

    @abstractmethod
    def get_modules(self) -> List[str]:
        """获取本层包含的模块列表."""
        ...

    @abstractmethod
    def get_upstream_layers(self) -> List[ArchitectureLayer]:
        """获取上游层列表（数据来源）."""
        ...

    @abstractmethod
    def get_downstream_layers(self) -> List[ArchitectureLayer]:
        """获取下游层列表（数据去向）."""
        ...


# ========== 层注册信息 ==========
@dataclass
class LayerModule:
    """层内模块注册信息."""
    name: str
    layer: ArchitectureLayer
    description: str = ""
    dependencies: Set[str] = field(default_factory=set)
    is_entry_point: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "layer": self.layer.name,
            "description": self.description,
            "dependencies": sorted(self.dependencies),
            "is_entry_point": self.is_entry_point,
        }


# ========== 层注册表 ==========
class LayerRegistry:
    """架构层注册表.

    管理四层架构的模块注册、依赖关系、层级约束
    """

    def __init__(self) -> None:
        self._modules: Dict[str, LayerModule] = {}
        self._layer_modules: Dict[ArchitectureLayer, List[str]] = {
            layer: [] for layer in ArchitectureLayer
        }

    def register(self, module: LayerModule) -> None:
        """注册模块到架构层.

        Args:
            module: 层模块信息

        Raises:
            ValueError: 如果模块名已存在
        """
        if module.name in self._modules:
            raise ValueError(f"模块 '{module.name}' 已注册")

        # 验证依赖方向
        for dep_name in module.dependencies:
            if dep_name in self._modules:
                dep_layer = self._modules[dep_name].layer
                if not module.layer.can_depend_on(dep_layer):
                    raise ValueError(
                        f"违规依赖: {module.name}({module.layer.name}) "
                        f"不能依赖 {dep_name}({dep_layer.name})"
                    )

        self._modules[module.name] = module
        self._layer_modules[module.layer].append(module.name)

    def get_module(self, name: str) -> Optional[LayerModule]:
        """获取模块信息."""
        return self._modules.get(name)

    def get_layer_modules(self, layer: ArchitectureLayer) -> List[LayerModule]:
        """获取某层的所有模块."""
        names = self._layer_modules.get(layer, [])
        return [self._modules[n] for n in names if n in self._modules]

    def get_all_modules(self) -> Dict[str, LayerModule]:
        """获取所有已注册模块."""
        return dict(self._modules)

    def get_layer_summary(self) -> Dict[ArchitectureLayer, Dict[str, Any]]:
        """获取各层摘要."""
        summary = {}
        for layer in ArchitectureLayer:
            modules = self.get_layer_modules(layer)
            summary[layer] = {
                "count": len(modules),
                "modules": [m.name for m in modules],
                "label": layer.label,
            }
        return summary

    def validate_dependencies(self) -> List[str]:
        """验证所有模块依赖方向.

        Returns:
            违规列表（空列表表示全部合规）
        """
        violations = []
        for name, module in self._modules.items():
            for dep_name in module.dependencies:
                if dep_name in self._modules:
                    dep_layer = self._modules[dep_name].layer
                    if not module.layer.can_depend_on(dep_layer):
                        violations.append(
                            f"{name}({module.layer.name}) → "
                            f"{dep_name}({dep_layer.name}): 反向依赖"
                        )
        return violations

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取依赖图（邻接表）.

        Returns:
            {模块名: [依赖模块名列表]}
        """
        return {
            name: sorted(module.dependencies)
            for name, module in self._modules.items()
        }

    @property
    def total_modules(self) -> int:
        """已注册模块总数."""
        return len(self._modules)

    def clear(self) -> None:
        """清空注册表."""
        self._modules.clear()
        for layer in self._layer_modules:
            self._layer_modules[layer] = []


# ========== 四层具体实现 ==========
class InputLayer(LayerInterface):
    """输入收敛层."""

    @property
    def layer(self) -> ArchitectureLayer:
        return ArchitectureLayer.INPUT

    @property
    def name(self) -> str:
        return "input_layer"

    def get_modules(self) -> List[str]:
        return []  # 待后续阶段填充

    def get_upstream_layers(self) -> List[ArchitectureLayer]:
        return []  # 最顶层，无上游

    def get_downstream_layers(self) -> List[ArchitectureLayer]:
        return [ArchitectureLayer.SCHEDULER]


class SchedulerLayer(LayerInterface):
    """调度中枢层."""

    @property
    def layer(self) -> ArchitectureLayer:
        return ArchitectureLayer.SCHEDULER

    @property
    def name(self) -> str:
        return "scheduler_layer"

    def get_modules(self) -> List[str]:
        return [
            "collaboration_algorithm", "collaboration_scheduler",
            "collaboration_dispatcher", "collaboration_negotiator",
            "pipeline_stages", "pipeline_branches", "pipeline_workflow",
        ]

    def get_upstream_layers(self) -> List[ArchitectureLayer]:
        return [ArchitectureLayer.INPUT]

    def get_downstream_layers(self) -> List[ArchitectureLayer]:
        return [ArchitectureLayer.AGENT]


class AgentLayer(LayerInterface):
    """智能协作层."""

    @property
    def layer(self) -> ArchitectureLayer:
        return ArchitectureLayer.AGENT

    @property
    def name(self) -> str:
        return "agent_layer"

    def get_modules(self) -> List[str]:
        return [
            "agent_controller", "agent_requirement", "agent_architect",
            "agent_developer", "agent_bugfix", "agent_reviewer",
            "agent_tester", "agent_documenter",
        ]

    def get_upstream_layers(self) -> List[ArchitectureLayer]:
        return [ArchitectureLayer.SCHEDULER]

    def get_downstream_layers(self) -> List[ArchitectureLayer]:
        return [ArchitectureLayer.EXECUTOR]


class ExecutorLayer(LayerInterface):
    """原子执行层."""

    @property
    def layer(self) -> ArchitectureLayer:
        return ArchitectureLayer.EXECUTOR

    @property
    def name(self) -> str:
        return "executor_layer"

    def get_modules(self) -> List[str]:
        return [
            "core_config", "core_logging", "core_exceptions", "core_paths",
            "utils_helpers", "utils_validators", "utils_converters",
            "atomicity_variable", "atomicity_method", "atomicity_class",
            "atomicity_module",
            "quality_linter", "quality_security", "quality_coverage",
            "quality_metrics",
        ]

    def get_upstream_layers(self) -> List[ArchitectureLayer]:
        return [ArchitectureLayer.AGENT]

    def get_downstream_layers(self) -> List[ArchitectureLayer]:
        return []  # 最底层，无下游


# ========== 全局层注册表 ==========
layer_registry = LayerRegistry()


def get_all_layers() -> List[LayerInterface]:
    """获取四层架构实例列表（从高到低）."""
    return [
        InputLayer(),
        SchedulerLayer(),
        AgentLayer(),
        ExecutorLayer(),
    ]


def get_layer_by_name(name: str) -> Optional[LayerInterface]:
    """按名称获取层实例."""
    for layer in get_all_layers():
        if layer.name == name:
            return layer
    return None


def get_layer_by_enum(layer_enum: ArchitectureLayer) -> Optional[LayerInterface]:
    """按枚举获取层实例."""
    for layer in get_all_layers():
        if layer.layer == layer_enum:
            return layer
    return None
