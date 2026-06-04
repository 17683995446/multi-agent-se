"""Architect Agent - 第33阶段.

架构师Agent - 负责系统架构设计、模块划分和技术选型.

职责:
- 分析需求并设计系统架构
- 划分模块和定义接口
- 选择技术栈和框架
- 设计数据模型和流程
- 评估架构风险和可行性
- 生成架构文档
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
from multi_agent_se.agents.runtime.base_agent import BaseAgentImpl, AgentContext, TaskResult


class ArchitectureStyle(Enum):
    """架构风格."""
    LAYERED = "layered"                 # 分层架构
    MICROSERVICES = "microservices"     # 微服务架构
    MONOLITHIC = "monolithic"           # 单体架构
    EVENT_DRIVEN = "event_driven"       # 事件驱动架构
    PIPELINE = "pipeline"               # 管道架构
    PLUGIN = "plugin"                   # 插件架构
    MODULAR = "modular"                 # 模块化架构


class ModuleType(Enum):
    """模块类型."""
    CORE = "core"                       # 核心模块
    SERVICE = "service"                 # 服务模块
    ADAPTER = "adapter"                 # 适配器模块
    REPOSITORY = "repository"           # 数据访问模块
    CONTROLLER = "controller"           # 控制层模块
    UTILITY = "utility"                 # 工具模块


@dataclass
class ModuleDefinition:
    """模块定义."""
    module_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    module_type: ModuleType = ModuleType.SERVICE
    
    # 职责
    responsibilities: List[str] = field(default_factory=list)
    
    # 接口
    provides: List[str] = field(default_factory=list)   # 提供的接口
    requires: List[str] = field(default_factory=list)   # 依赖的接口
    
    # 依赖
    dependencies: List[str] = field(default_factory=list)  # 依赖的模块名
    depended_by: List[str] = field(default_factory=list)   # 被依赖的模块名
    
    # 复杂度
    complexity: str = "medium"          # low/medium/high
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "name": self.name,
            "type": self.module_type.value,
            "description": self.description[:100] if self.description else "",
            "responsibilities": self.responsibilities[:3],
            "dependencies": self.dependencies,
        }


@dataclass
class InterfaceDefinition:
    """接口定义."""
    name: str = ""
    description: str = ""
    methods: List[Dict[str, Any]] = field(default_factory=list)
    module: str = ""                    # 所属模块


@dataclass
class DataModel:
    """数据模型."""
    name: str = ""
    description: str = ""
    fields: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ArchitectureDesign:
    """架构设计结果."""
    design_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    style: ArchitectureStyle = ArchitectureStyle.LAYERED
    
    # 模块
    modules: List[ModuleDefinition] = field(default_factory=list)
    
    # 接口
    interfaces: List[InterfaceDefinition] = field(default_factory=list)
    
    # 数据模型
    data_models: List[DataModel] = field(default_factory=list)
    
    # 技术栈
    tech_stack: Dict[str, str] = field(default_factory=dict)
    
    # 质量属性
    quality_attributes: Dict[str, str] = field(default_factory=dict)
    
    # 评估
    complexity_score: float = 0.0       # 复杂度评分 (0-1, 越低越好)
    coupling_score: float = 0.0         # 耦合度评分 (0-1, 越低越好)
    cohesion_score: float = 0.0         # 内聚度评分 (0-1, 越高越好)
    
    def get_module(self, name: str) -> Optional[ModuleDefinition]:
        """按名称获取模块."""
        for m in self.modules:
            if m.name == name:
                return m
        return None
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """获取模块依赖图."""
        return {m.name: m.dependencies for m in self.modules}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_id": self.design_id,
            "name": self.name,
            "style": self.style.value,
            "module_count": len(self.modules),
            "interface_count": len(self.interfaces),
            "data_model_count": len(self.data_models),
            "tech_stack": self.tech_stack,
            "quality_scores": {
                "complexity": round(self.complexity_score, 2),
                "coupling": round(self.coupling_score, 2),
                "cohesion": round(self.cohesion_score, 2),
            },
        }


class ArchitectAgent(BaseAgentImpl):
    """架构师Agent - 系统架构设计.
    
    8大正交角色Agent之一，负责将需求转化为可实现的架构设计。
    """
    
    AGENT_ROLE = AgentRole.ARCHITECT
    AGENT_CAPABILITIES = [
        AgentCapability.ARCHITECTURE_DESIGN,
    ]
    AGENT_DESCRIPTION = "架构师Agent - 负责系统架构设计、模块划分和技术选型"
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None) -> None:
        super().__init__(agent_id, config)
        self._design_history: List[ArchitectureDesign] = []
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理架构设计任务.
        
        Args:
            context: Agent执行上下文
            
        Returns:
            任务执行结果
        """
        input_data = context.input_data
        
        # 输入类型验证
        if not isinstance(input_data, dict):
            return TaskResult(
                success=False,
                error_message=f"输入数据必须是字典类型，实际为 {type(input_data).__name__}",
            )
        
        requirements = input_data.get("requirements", [])
        style_hint = input_data.get("style", "layered")
        
        if not requirements:
            return TaskResult(
                success=False,
                error_message="缺少需求列表",
            )
        
        # 1. 确定架构风格
        style = self._determine_architecture_style(style_hint, requirements)
        
        # 2. 创建架构设计
        design = ArchitectureDesign(
            name=input_data.get("name", "未命名架构"),
            description=input_data.get("description", ""),
            style=style,
        )
        
        # 3. 设计模块
        self._design_modules(design, requirements)
        
        # 4. 设计接口
        self._design_interfaces(design)
        
        # 5. 设计数据模型
        self._design_data_models(design, requirements)
        
        # 6. 选择技术栈
        self._select_tech_stack(design, requirements)
        
        # 7. 评估架构
        self._evaluate_architecture(design)
        
        # 保存设计
        self._design_history.append(design)
        
        # 构建输出
        output = {
            "design": design.to_dict(),
            "modules": [m.to_dict() for m in design.modules],
            "interfaces": [{"name": i.name, "module": i.module} for i in design.interfaces],
            "data_models": [{"name": d.name} for d in design.data_models],
            "quality_assessment": {
                "complexity": round(design.complexity_score, 2),
                "coupling": round(design.coupling_score, 2),
                "cohesion": round(design.cohesion_score, 2),
            },
        }
        
        return TaskResult(
            success=True,
            output=output,
            artifacts={
                "design": design,
            },
        )
    
    def _determine_architecture_style(
        self,
        hint: str,
        requirements: List[Dict[str, Any]],
    ) -> ArchitectureStyle:
        """确定架构风格."""
        style_map = {
            "layered": ArchitectureStyle.LAYERED,
            "microservices": ArchitectureStyle.MICROSERVICES,
            "monolithic": ArchitectureStyle.MONOLITHIC,
            "event": ArchitectureStyle.EVENT_DRIVEN,
            "pipeline": ArchitectureStyle.PIPELINE,
            "plugin": ArchitectureStyle.PLUGIN,
            "modular": ArchitectureStyle.MODULAR,
        }
        return style_map.get(hint, ArchitectureStyle.LAYERED)
    
    def _design_modules(
        self,
        design: ArchitectureDesign,
        requirements: List[Dict[str, Any]],
    ) -> None:
        """设计模块."""
        if design.style == ArchitectureStyle.LAYERED:
            # 分层架构：表示层 -> 业务层 -> 数据层
            layers = [
                ("controller", "控制层", ["处理输入", "调用业务逻辑"]),
                ("service", "业务层", ["业务逻辑", "协调数据访问"]),
                ("repository", "数据层", ["数据持久化", "数据库访问"]),
            ]
            
            prev_layer = None
            for name, desc, resp in layers:
                module = ModuleDefinition(
                    name=name,
                    description=desc,
                    module_type=ModuleType.SERVICE if name == "service" else ModuleType.CONTROLLER if name == "controller" else ModuleType.REPOSITORY,
                    responsibilities=resp,
                )
                
                if prev_layer:
                    module.dependencies.append(prev_layer)
                
                design.modules.append(module)
                prev_layer = name
        
        elif design.style == ArchitectureStyle.MODULAR:
            # 模块化架构：按功能划分
            modules = [
                ("core", "核心模块", ["基础功能", "通用工具"]),
                ("config", "配置模块", ["配置管理", "环境适配"]),
                ("api", "API模块", ["接口定义", "协议处理"]),
            ]
            
            for name, desc, resp in modules:
                module = ModuleDefinition(
                    name=name,
                    description=desc,
                    module_type=ModuleType.CORE if name == "core" else ModuleType.UTILITY,
                    responsibilities=resp,
                )
                design.modules.append(module)
        
        else:
            # 默认：至少一个核心模块
            design.modules.append(ModuleDefinition(
                name="core",
                description="核心模块",
                module_type=ModuleType.CORE,
                responsibilities=["核心业务逻辑"],
            ))
    
    def _design_interfaces(self, design: ArchitectureDesign) -> None:
        """设计模块间接口."""
        for module in design.modules:
            if module.module_type == ModuleType.SERVICE:
                interface = InterfaceDefinition(
                    name=f"I{module.name.capitalize()}",
                    description=f"{module.name}服务接口",
                    module=module.name,
                    methods=[
                        {"name": "process", "params": ["data"]},
                        {"name": "validate", "params": ["input"]},
                    ],
                )
                design.interfaces.append(interface)
                module.provides.append(interface.name)
    
    def _design_data_models(
        self,
        design: ArchitectureDesign,
        requirements: List[Dict[str, Any]],
    ) -> None:
        """设计数据模型."""
        # 从需求中提取实体
        entities: Set[str] = set()
        for req in requirements:
            desc = req.get("description", "")
            # 简单提取：识别可能的实体名词
            words = desc.split()
            for word in words:
                if word in ["用户", "User", "订单", "Order", "产品", "Product"]:
                    entities.add(word)
        
        # 如果没有识别到，创建默认模型
        if not entities:
            entities = {"Entity"}
        
        for entity in entities:
            model = DataModel(
                name=entity,
                description=f"{entity}数据模型",
                fields=[
                    {"name": "id", "type": "string"},
                    {"name": "created_at", "type": "datetime"},
                ],
            )
            design.data_models.append(model)
    
    def _select_tech_stack(
        self,
        design: ArchitectureDesign,
        requirements: List[Dict[str, Any]],
    ) -> None:
        """选择技术栈."""
        design.tech_stack = {
            "language": "Python",
            "framework": "FastAPI" if design.style == ArchitectureStyle.MICROSERVICES else "Flask",
            "database": "PostgreSQL",
            "cache": "Redis",
            "message_queue": "RabbitMQ" if design.style == ArchitectureStyle.EVENT_DRIVEN else "None",
        }
    
    def _evaluate_architecture(self, design: ArchitectureDesign) -> None:
        """评估架构质量."""
        module_count = len(design.modules)
        
        # 复杂度评分（模块越多越复杂）
        if module_count <= 3:
            design.complexity_score = 0.3
        elif module_count <= 6:
            design.complexity_score = 0.5
        else:
            design.complexity_score = 0.8
        
        # 耦合度评分（计算依赖关系）
        total_deps = sum(len(m.dependencies) for m in design.modules)
        if total_deps == 0:
            design.coupling_score = 0.0
        elif total_deps <= module_count:
            design.coupling_score = 0.3
        else:
            design.coupling_score = 0.6
        
        # 内聚度评分（基于职责清晰度）
        clear_resp_count = sum(1 for m in design.modules if len(m.responsibilities) >= 2)
        design.cohesion_score = clear_resp_count / module_count if module_count > 0 else 0.0
    
    def get_design_history(self) -> List[ArchitectureDesign]:
        """获取设计历史."""
        return self._design_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        total_designs = len(self._design_history)
        total_modules = sum(len(d.modules) for d in self._design_history)
        
        return {
            "total_designs": total_designs,
            "total_modules_designed": total_modules,
            "avg_modules_per_design": (
                total_modules / total_designs if total_designs > 0 else 0
            ),
        }
