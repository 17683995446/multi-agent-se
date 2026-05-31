"""架构层约束 - 阶段11.

四层架构：输入层 → 调度层 → Agent层 → 执行层
"""

from multi_agent_se.core.architecture.layer_base import (
    ArchitectureLayer,
    LayerInterface,
    LayerModule,
    LayerRegistry,
    InputLayer,
    SchedulerLayer,
    AgentLayer,
    ExecutorLayer,
    layer_registry,
    get_all_layers,
    get_layer_by_name,
    get_layer_by_enum,
)

from multi_agent_se.core.architecture.data_flow import (
    FlowViolationType,
    DataFlowEdge,
    FlowViolation,
    DataFlowReport,
    DataFlowValidator,
    validate_unidirectional_flow,
)

from multi_agent_se.core.architecture.coupling_detector import (
    ImportInfo,
    CouplingRecord,
    CouplingReport,
    CouplingDetector,
)

__all__ = [
    # 层定义
    "ArchitectureLayer",
    "LayerInterface",
    "LayerModule",
    "LayerRegistry",
    "InputLayer",
    "SchedulerLayer",
    "AgentLayer",
    "ExecutorLayer",
    "layer_registry",
    "get_all_layers",
    "get_layer_by_name",
    "get_layer_by_enum",
    # 数据流
    "FlowViolationType",
    "DataFlowEdge",
    "FlowViolation",
    "DataFlowReport",
    "DataFlowValidator",
    "validate_unidirectional_flow",
    # 耦合检测
    "ImportInfo",
    "CouplingRecord",
    "CouplingReport",
    "CouplingDetector",
]
