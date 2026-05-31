"""单向依赖关系定义模块 - 阶段2.

遵循第一性原理：依赖单向性公理（DAG无环）
定义系统各模块间的单向依赖关系
"""

from enum import Enum
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
import networkx as nx


class LayerType(Enum):
    """四层架构层级枚举."""
    INPUT = "input"           # 输入收敛层
    SCHEDULER = "scheduler"   # 调度中枢层
    AGENT = "agent"           # 智能协作层
    EXECUTOR = "executor"     # 原子执行层


class ModuleType(Enum):
    """模块类型枚举."""
    # 核心层
    CORE_CONFIG = "core.config"
    CORE_LOGGING = "core.logging"
    CORE_EXCEPTIONS = "core.exceptions"
    CORE_PATHS = "core.paths"
    
    # Agent层
    AGENT_CONTROLLER = "agents.controller"
    AGENT_REQUIREMENT = "agents.requirement"
    AGENT_ARCHITECT = "agents.architect"
    AGENT_DEVELOPER = "agents.developer"
    AGENT_BUGFIX = "agents.bugfix"
    AGENT_REVIEWER = "agents.reviewer"
    AGENT_TESTER = "agents.tester"
    AGENT_DOCUMENTER = "agents.documenter"
    
    # 原子化层
    ATOMICITY_VARIABLE = "atomicity.variable"
    ATOMICITY_METHOD = "atomicity.method"
    ATOMICITY_CLASS = "atomicity.class_atom"
    ATOMICITY_MODULE = "atomicity.module_atom"
    
    # 协作层
    COLLABORATION_SCHEDULER = "collaboration.scheduler"
    COLLABORATION_DISPATCHER = "collaboration.dispatcher"
    COLLABORATION_NEGOTIATOR = "collaboration.negotiator"
    COLLABORATION_ALGORITHM = "collaboration.algorithm"
    
    # 流水线层
    PIPELINE_STAGES = "pipeline.stages"
    PIPELINE_BRANCHES = "pipeline.branches"
    PIPELINE_WORKFLOW = "pipeline.workflow"
    
    # 质量层
    QUALITY_LINTER = "quality.linter"
    QUALITY_SECURITY = "quality.security"
    QUALITY_COVERAGE = "quality.coverage"
    QUALITY_METRICS = "quality.metrics"
    
    # 工具层
    UTILS_HELPERS = "utils.helpers"
    UTILS_VALIDATORS = "utils.validators"
    UTILS_CONVERTERS = "utils.converters"


@dataclass
class ModuleInfo:
    """模块信息."""
    module_type: ModuleType
    layer: LayerType
    description: str
    dependencies: List[ModuleType] = field(default_factory=list)


# 模块依赖关系定义（单向DAG）
MODULE_DEPENDENCIES: Dict[ModuleType, ModuleInfo] = {
    # ========== 核心层（无依赖，最底层）==========
    ModuleType.CORE_CONFIG: ModuleInfo(
        module_type=ModuleType.CORE_CONFIG,
        layer=LayerType.EXECUTOR,
        description="全局配置管理",
        dependencies=[]
    ),
    ModuleType.CORE_LOGGING: ModuleInfo(
        module_type=ModuleType.CORE_LOGGING,
        layer=LayerType.EXECUTOR,
        description="日志管理",
        dependencies=[ModuleType.CORE_CONFIG]
    ),
    ModuleType.CORE_EXCEPTIONS: ModuleInfo(
        module_type=ModuleType.CORE_EXCEPTIONS,
        layer=LayerType.EXECUTOR,
        description="异常处理",
        dependencies=[ModuleType.CORE_CONFIG]
    ),
    ModuleType.CORE_PATHS: ModuleInfo(
        module_type=ModuleType.CORE_PATHS,
        layer=LayerType.EXECUTOR,
        description="路径管理",
        dependencies=[ModuleType.CORE_CONFIG]
    ),
    
    # ========== 工具层 ==========
    ModuleType.UTILS_HELPERS: ModuleInfo(
        module_type=ModuleType.UTILS_HELPERS,
        layer=LayerType.EXECUTOR,
        description="辅助工具函数",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.CORE_LOGGING]
    ),
    ModuleType.UTILS_VALIDATORS: ModuleInfo(
        module_type=ModuleType.UTILS_VALIDATORS,
        layer=LayerType.EXECUTOR,
        description="验证器",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.CORE_EXCEPTIONS]
    ),
    ModuleType.UTILS_CONVERTERS: ModuleInfo(
        module_type=ModuleType.UTILS_CONVERTERS,
        layer=LayerType.EXECUTOR,
        description="转换器",
        dependencies=[ModuleType.CORE_CONFIG]
    ),
    
    # ========== 原子化层 ==========
    ModuleType.ATOMICITY_VARIABLE: ModuleInfo(
        module_type=ModuleType.ATOMICITY_VARIABLE,
        layer=LayerType.EXECUTOR,
        description="变量原子扫描",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.CORE_LOGGING, ModuleType.UTILS_VALIDATORS]
    ),
    ModuleType.ATOMICITY_METHOD: ModuleInfo(
        module_type=ModuleType.ATOMICITY_METHOD,
        layer=LayerType.EXECUTOR,
        description="方法原子校验",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.CORE_LOGGING, ModuleType.ATOMICITY_VARIABLE]
    ),
    ModuleType.ATOMICITY_CLASS: ModuleInfo(
        module_type=ModuleType.ATOMICITY_CLASS,
        layer=LayerType.EXECUTOR,
        description="类原子分析",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.ATOMICITY_METHOD]
    ),
    ModuleType.ATOMICITY_MODULE: ModuleInfo(
        module_type=ModuleType.ATOMICITY_MODULE,
        layer=LayerType.EXECUTOR,
        description="模块原子边界",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.ATOMICITY_CLASS]
    ),
    
    # ========== 质量层 ==========
    ModuleType.QUALITY_LINTER: ModuleInfo(
        module_type=ModuleType.QUALITY_LINTER,
        layer=LayerType.EXECUTOR,
        description="代码检查",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.ATOMICITY_MODULE]
    ),
    ModuleType.QUALITY_SECURITY: ModuleInfo(
        module_type=ModuleType.QUALITY_SECURITY,
        layer=LayerType.EXECUTOR,
        description="安全扫描",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.QUALITY_LINTER]
    ),
    ModuleType.QUALITY_COVERAGE: ModuleInfo(
        module_type=ModuleType.QUALITY_COVERAGE,
        layer=LayerType.EXECUTOR,
        description="覆盖率分析",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.QUALITY_LINTER]
    ),
    ModuleType.QUALITY_METRICS: ModuleInfo(
        module_type=ModuleType.QUALITY_METRICS,
        layer=LayerType.EXECUTOR,
        description="质量指标",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.QUALITY_COVERAGE]
    ),
    
    # ========== Agent层 ==========
    ModuleType.AGENT_CONTROLLER: ModuleInfo(
        module_type=ModuleType.AGENT_CONTROLLER,
        layer=LayerType.AGENT,
        description="总控Agent",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.CORE_LOGGING, ModuleType.CORE_EXCEPTIONS]
    ),
    ModuleType.AGENT_REQUIREMENT: ModuleInfo(
        module_type=ModuleType.AGENT_REQUIREMENT,
        layer=LayerType.AGENT,
        description="需求拆解Agent",
        dependencies=[ModuleType.AGENT_CONTROLLER, ModuleType.UTILS_VALIDATORS]
    ),
    ModuleType.AGENT_ARCHITECT: ModuleInfo(
        module_type=ModuleType.AGENT_ARCHITECT,
        layer=LayerType.AGENT,
        description="架构Agent",
        dependencies=[ModuleType.AGENT_CONTROLLER, ModuleType.ATOMICITY_MODULE]
    ),
    ModuleType.AGENT_DEVELOPER: ModuleInfo(
        module_type=ModuleType.AGENT_DEVELOPER,
        layer=LayerType.AGENT,
        description="开发Agent",
        dependencies=[ModuleType.AGENT_CONTROLLER, ModuleType.ATOMICITY_METHOD]
    ),
    ModuleType.AGENT_BUGFIX: ModuleInfo(
        module_type=ModuleType.AGENT_BUGFIX,
        layer=LayerType.AGENT,
        description="缺陷排查Agent",
        dependencies=[ModuleType.AGENT_CONTROLLER, ModuleType.ATOMICITY_VARIABLE]
    ),
    ModuleType.AGENT_REVIEWER: ModuleInfo(
        module_type=ModuleType.AGENT_REVIEWER,
        layer=LayerType.AGENT,
        description="评审Agent",
        dependencies=[ModuleType.AGENT_CONTROLLER, ModuleType.QUALITY_LINTER]
    ),
    ModuleType.AGENT_TESTER: ModuleInfo(
        module_type=ModuleType.AGENT_TESTER,
        layer=LayerType.AGENT,
        description="测试Agent",
        dependencies=[ModuleType.AGENT_CONTROLLER, ModuleType.QUALITY_COVERAGE]
    ),
    ModuleType.AGENT_DOCUMENTER: ModuleInfo(
        module_type=ModuleType.AGENT_DOCUMENTER,
        layer=LayerType.AGENT,
        description="文档Agent",
        dependencies=[ModuleType.AGENT_CONTROLLER, ModuleType.UTILS_CONVERTERS]
    ),
    
    # ========== 协作层 ==========
    ModuleType.COLLABORATION_ALGORITHM: ModuleInfo(
        module_type=ModuleType.COLLABORATION_ALGORITHM,
        layer=LayerType.SCHEDULER,
        description="协作算法",
        dependencies=[ModuleType.CORE_CONFIG, ModuleType.UTILS_HELPERS]
    ),
    ModuleType.COLLABORATION_SCHEDULER: ModuleInfo(
        module_type=ModuleType.COLLABORATION_SCHEDULER,
        layer=LayerType.SCHEDULER,
        description="调度器",
        dependencies=[ModuleType.COLLABORATION_ALGORITHM, ModuleType.AGENT_CONTROLLER]
    ),
    ModuleType.COLLABORATION_DISPATCHER: ModuleInfo(
        module_type=ModuleType.COLLABORATION_DISPATCHER,
        layer=LayerType.SCHEDULER,
        description="分发器",
        dependencies=[ModuleType.COLLABORATION_SCHEDULER]
    ),
    ModuleType.COLLABORATION_NEGOTIATOR: ModuleInfo(
        module_type=ModuleType.COLLABORATION_NEGOTIATOR,
        layer=LayerType.SCHEDULER,
        description="协商器",
        dependencies=[ModuleType.COLLABORATION_SCHEDULER, ModuleType.AGENT_CONTROLLER]
    ),
    
    # ========== 流水线层 ==========
    ModuleType.PIPELINE_STAGES: ModuleInfo(
        module_type=ModuleType.PIPELINE_STAGES,
        layer=LayerType.SCHEDULER,
        description="流水线阶段",
        dependencies=[ModuleType.COLLABORATION_SCHEDULER]
    ),
    ModuleType.PIPELINE_BRANCHES: ModuleInfo(
        module_type=ModuleType.PIPELINE_BRANCHES,
        layer=LayerType.SCHEDULER,
        description="流水线分支",
        dependencies=[ModuleType.PIPELINE_STAGES]
    ),
    ModuleType.PIPELINE_WORKFLOW: ModuleInfo(
        module_type=ModuleType.PIPELINE_WORKFLOW,
        layer=LayerType.SCHEDULER,
        description="工作流",
        dependencies=[ModuleType.PIPELINE_STAGES, ModuleType.PIPELINE_BRANCHES]
    ),
}


class DependencyGraph:
    """依赖关系图管理类."""
    
    def __init__(self) -> None:
        """初始化依赖图."""
        self._graph = nx.DiGraph()
        self._build_graph()
    
    def _build_graph(self) -> None:
        """构建依赖图."""
        for module_type, info in MODULE_DEPENDENCIES.items():
            self._graph.add_node(module_type.value, layer=info.layer.value, description=info.description)
            for dep in info.dependencies:
                self._graph.add_edge(dep.value, module_type.value)
    
    def is_dag(self) -> bool:
        """检查是否为DAG（无环）."""
        return nx.is_directed_acyclic_graph(self._graph)
    
    def find_cycles(self) -> List[List[str]]:
        """查找所有循环依赖."""
        try:
            return list(nx.simple_cycles(self._graph))
        except nx.NetworkXError:
            return []
    
    def get_dependencies(self, module: ModuleType) -> List[ModuleType]:
        """获取模块的直接依赖."""
        info = MODULE_DEPENDENCIES.get(module)
        return info.dependencies if info else []
    
    def get_all_dependencies(self, module: ModuleType) -> Set[ModuleType]:
        """获取模块的所有依赖（递归）."""
        result = set()
        to_process = list(self.get_dependencies(module))
        while to_process:
            dep = to_process.pop()
            if dep not in result:
                result.add(dep)
                to_process.extend(self.get_dependencies(dep))
        return result
    
    def get_dependents(self, module: ModuleType) -> List[ModuleType]:
        """获取依赖此模块的所有模块."""
        result = []
        for mt, info in MODULE_DEPENDENCIES.items():
            if module in info.dependencies:
                result.append(mt)
        return result
    
    def topological_sort(self) -> List[str]:
        """拓扑排序."""
        if not self.is_dag():
            raise ValueError("依赖图存在循环，无法进行拓扑排序")
        return list(nx.topological_sort(self._graph))
    
    def get_layer_modules(self, layer: LayerType) -> List[ModuleType]:
        """获取指定层级的所有模块."""
        return [mt for mt, info in MODULE_DEPENDENCIES.items() if info.layer == layer]
    
    def validate_dependency_direction(self) -> Tuple[bool, List[str]]:
        """验证依赖方向（只能依赖更底层）."""
        layer_order = {
            LayerType.EXECUTOR: 0,
            LayerType.AGENT: 1,
            LayerType.SCHEDULER: 2,
            LayerType.INPUT: 3,
        }
        
        violations = []
        for module_type, info in MODULE_DEPENDENCIES.items():
            module_layer = layer_order[info.layer]
            for dep in info.dependencies:
                dep_info = MODULE_DEPENDENCIES.get(dep)
                if dep_info:
                    dep_layer = layer_order[dep_info.layer]
                    if dep_layer > module_layer:
                        violations.append(
                            f"{module_type.value} ({info.layer.value}) -> {dep.value} ({dep_info.layer.value})"
                        )
        
        return len(violations) == 0, violations


# 全局依赖图实例
dependency_graph = DependencyGraph()
