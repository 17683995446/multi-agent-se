"""Agent元数据定义 - 阶段16.

定义Agent的元数据结构：
- Agent能力声明
- Agent配置信息
- Agent状态信息
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Type


class AgentRole(Enum):
    """Agent角色类型（8个正交角色）."""
    CONTROLLER = "controller"       # 控制器Agent
    REQUIREMENT = "requirement"     # 需求分析Agent
    ARCHITECT = "architect"         # 架构设计Agent
    DEVELOPER = "developer"         # 开发Agent
    BUGFIX = "bugfix"              # 修复Agent
    REVIEWER = "reviewer"          # 审查Agent
    TESTER = "tester"              # 测试Agent
    DOCUMENTER = "documenter"      # 文档Agent


class AgentStatus(Enum):
    """Agent状态."""
    CREATED = "created"           # 已创建
    INITIALIZING = "initializing" # 初始化中
    READY = "ready"              # 就绪
    RUNNING = "running"          # 运行中
    PAUSED = "paused"            # 已暂停
    ERROR = "error"              # 错误
    TERMINATED = "terminated"     # 已终止


class AgentCapability(Enum):
    """Agent能力类型."""
    CODE_GENERATION = "code_generation"       # 代码生成
    CODE_REVIEW = "code_review"              # 代码审查
    CODE_TESTING = "code_testing"            # 代码测试
    CODE_REFACTORING = "code_refactoring"    # 代码重构
    CODE_DEBUGGING = "code_debugging"        # 代码调试
    REQUIREMENT_ANALYSIS = "requirement_analysis"  # 需求分析
    ARCHITECTURE_DESIGN = "architecture_design"    # 架构设计
    DOCUMENTATION = "documentation"          # 文档生成
    TASK_DECOMPOSITION = "task_decomposition"  # 任务分解
    TASK_SCHEDULING = "task_scheduling"      # 任务调度
    QUALITY_CHECK = "quality_check"          # 质量检查
    FILE_OPERATION = "file_operation"        # 文件操作


@dataclass
class AgentCapabilityDeclaration:
    """Agent能力声明."""
    capability: AgentCapability
    proficiency: float = 1.0  # 熟练度 0.0-1.0
    constraints: Dict[str, Any] = field(default_factory=dict)  # 能力约束
    metadata: Dict[str, Any] = field(default_factory=dict)  # 能力元数据
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability": self.capability.value,
            "proficiency": self.proficiency,
            "constraints": self.constraints,
            "metadata": self.metadata,
        }


@dataclass
class AgentMetadata:
    """Agent元数据.
    
    描述Agent的基本信息、能力、配置等
    """
    # 基本信息
    agent_id: str                          # 唯一标识
    name: str                              # 名称
    role: AgentRole                        # 角色
    version: str = "1.0.0"                 # 版本
    
    # 描述信息
    description: str = ""                  # 描述
    author: str = ""                       # 作者
    tags: Set[str] = field(default_factory=set)  # 标签
    
    # 能力声明
    capabilities: List[AgentCapabilityDeclaration] = field(default_factory=list)
    
    # 配置
    config: Dict[str, Any] = field(default_factory=dict)
    default_config: Dict[str, Any] = field(default_factory=dict)
    
    # 依赖
    dependencies: Set[str] = field(default_factory=set)  # 依赖的其他Agent
    required_tools: Set[str] = field(default_factory=set)  # 需要的工具
    
    # 状态
    status: AgentStatus = AgentStatus.CREATED
    last_active: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    # 统计
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    
    # 模块路径
    module_path: str = ""                  # 模块路径
    class_name: str = ""                   # 类名
    
    def __post_init__(self) -> None:
        """初始化后处理."""
        if not self.last_active:
            self.last_active = self.created_at
    
    @property
    def success_rate(self) -> float:
        """成功率."""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks
    
    @property
    def is_available(self) -> bool:
        """是否可用."""
        return self.status in (
            AgentStatus.READY,
            AgentStatus.RUNNING,
        )
    
    @property
    def capability_types(self) -> Set[AgentCapability]:
        """获取能力类型集合."""
        return {c.capability for c in self.capabilities}
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """检查是否具有某能力."""
        return capability in self.capability_types
    
    def get_capability(
        self,
        capability: AgentCapability,
    ) -> Optional[AgentCapabilityDeclaration]:
        """获取能力声明."""
        for c in self.capabilities:
            if c.capability == capability:
                return c
        return None
    
    def get_capability_proficiency(
        self,
        capability: AgentCapability,
    ) -> float:
        """获取能力熟练度."""
        cap = self.get_capability(capability)
        return cap.proficiency if cap else 0.0
    
    def add_capability(
        self,
        capability: AgentCapability,
        proficiency: float = 1.0,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> None:
        """添加能力."""
        self.capabilities.append(AgentCapabilityDeclaration(
            capability=capability,
            proficiency=proficiency,
            constraints=constraints or {},
        ))
    
    def update_status(self, status: AgentStatus) -> None:
        """更新状态."""
        self.status = status
        self.last_active = datetime.now()
    
    def record_task(self, success: bool) -> None:
        """记录任务执行."""
        self.total_tasks += 1
        if success:
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1
        self.last_active = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role.value,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "tags": sorted(self.tags),
            "capabilities": [c.to_dict() for c in self.capabilities],
            "config": self.config,
            "default_config": self.default_config,
            "dependencies": sorted(self.dependencies),
            "required_tools": sorted(self.required_tools),
            "status": self.status.value,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "created_at": self.created_at.isoformat(),
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": round(self.success_rate, 4),
            "is_available": self.is_available,
            "module_path": self.module_path,
            "class_name": self.class_name,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMetadata":
        """从字典创建."""
        # 解析能力
        capabilities = []
        for cap_data in data.get("capabilities", []):
            capabilities.append(AgentCapabilityDeclaration(
                capability=AgentCapability(cap_data["capability"]),
                proficiency=cap_data.get("proficiency", 1.0),
                constraints=cap_data.get("constraints", {}),
                metadata=cap_data.get("metadata", {}),
            ))
        
        # 解析时间
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        last_active = datetime.fromisoformat(data["last_active"]) if data.get("last_active") else created_at
        
        return cls(
            agent_id=data["agent_id"],
            name=data["name"],
            role=AgentRole(data["role"]),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            tags=set(data.get("tags", [])),
            capabilities=capabilities,
            config=data.get("config", {}),
            default_config=data.get("default_config", {}),
            dependencies=set(data.get("dependencies", [])),
            required_tools=set(data.get("required_tools", [])),
            status=AgentStatus(data.get("status", "created")),
            last_active=last_active,
            created_at=created_at,
            total_tasks=data.get("total_tasks", 0),
            successful_tasks=data.get("successful_tasks", 0),
            failed_tasks=data.get("failed_tasks", 0),
            module_path=data.get("module_path", ""),
            class_name=data.get("class_name", ""),
        )


@dataclass
class AgentRegistrationInfo:
    """Agent注册信息."""
    metadata: AgentMetadata
    agent_class: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    
    @property
    def has_class(self) -> bool:
        """是否有类定义."""
        return self.agent_class is not None
    
    @property
    def has_factory(self) -> bool:
        """是否有工厂函数."""
        return self.factory is not None
    
    @property
    def has_instance(self) -> bool:
        """是否有实例."""
        return self.instance is not None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "has_class": self.has_class,
            "has_factory": self.has_factory,
            "has_instance": self.has_instance,
        }
