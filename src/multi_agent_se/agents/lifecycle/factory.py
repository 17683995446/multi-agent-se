"""Agent工厂类 - 阶段17.

实现Agent的创建与实例化：
- AgentFactory工厂
- 实例创建配置
- 创建策略
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Type, Union

from multi_agent_se.agents.registry import (
    AgentRole,
    AgentStatus,
    AgentCapability,
    AgentMetadata,
    AgentRegistry,
    get_registry,
)
from multi_agent_se.agents.lifecycle.lifecycle import (
    LifecycleState,
    LifecycleEvent,
    LifecycleStateMachine,
)


class AgentCreationError(Exception):
    """Agent创建错误."""
    pass


@dataclass
class AgentCreationConfig:
    """Agent创建配置."""
    agent_id: str
    role: AgentRole
    name: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    auto_initialize: bool = True  # 创建后自动初始化
    auto_start: bool = False      # 初始化后自动启动
    
    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"{self.role.value.capitalize()}Agent"


@dataclass
class AgentInstance:
    """Agent实例包装."""
    instance_id: str              # 实例ID
    metadata: AgentMetadata       # 元数据
    instance: Any                 # 实际实例对象
    lifecycle: LifecycleStateMachine = field(default_factory=LifecycleStateMachine)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def state(self) -> LifecycleState:
        """当前生命周期状态."""
        return self.lifecycle.state
    
    @property
    def is_active(self) -> bool:
        """是否活跃."""
        return self.lifecycle.is_active
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "agent_id": self.metadata.agent_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
        }


class AgentFactory:
    """Agent工厂.
    
    负责创建和管理Agent实例
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None) -> None:
        """初始化工厂.
        
        Args:
            registry: Agent注册表
        """
        self._registry = registry or get_registry()
        self._instances: Dict[str, AgentInstance] = {}
        self._instance_counter = 0
        self._creation_hooks: List[Callable[[AgentInstance], None]] = []
    
    def _generate_instance_id(self, agent_id: str) -> str:
        """生成实例ID."""
        self._instance_counter += 1
        return f"{agent_id}:instance:{self._instance_counter}"
    
    def create(
        self,
        config: AgentCreationConfig,
    ) -> AgentInstance:
        """创建Agent实例.
        
        Args:
            config: 创建配置
            
        Returns:
            AgentInstance
            
        Raises:
            AgentCreationError: 创建失败
        """
        # 检查注册表中是否有该Agent定义
        if not self._registry.has_agent(config.agent_id):
            # 如果没有，自动注册一个基础定义
            metadata = AgentMetadata(
                agent_id=config.agent_id,
                name=config.name,
                role=config.role,
            )
            self._registry.register(metadata=metadata)
        
        # 获取注册信息
        reg_info = self._registry.get(config.agent_id)
        
        # 生成实例ID
        instance_id = self._generate_instance_id(config.agent_id)
        
        # 创建实际实例
        instance = self._create_instance(reg_info, config)
        
        # 创建实例包装
        agent_instance = AgentInstance(
            instance_id=instance_id,
            metadata=reg_info.metadata,
            instance=instance,
        )
        
        # 存储实例
        self._instances[instance_id] = agent_instance
        
        # 执行创建钩子
        for hook in self._creation_hooks:
            try:
                hook(agent_instance)
            except Exception:
                pass
        
        # 自动初始化
        if config.auto_initialize:
            self.initialize(instance_id)
            
            # 自动启动
            if config.auto_start:
                self.start(instance_id)
        
        return agent_instance
    
    def _create_instance(
        self,
        reg_info: Any,
        config: AgentCreationConfig,
    ) -> Any:
        """创建实际实例对象."""
        # 优先使用工厂函数
        if reg_info.factory:
            return reg_info.factory(**config.config)
        
        # 其次使用类
        if reg_info.agent_class:
            return reg_info.agent_class(**config.config)
        
        # 最后使用已有实例（单例模式）
        if reg_info.instance:
            return reg_info.instance
        
        # 如果都没有，返回一个基础对象
        return SimpleAgent(
            agent_id=config.agent_id,
            name=config.name,
            role=config.role,
            config=config.config,
        )
    
    def initialize(self, instance_id: str) -> bool:
        """初始化实例.
        
        Args:
            instance_id: 实例ID
            
        Returns:
            是否成功
        """
        if instance_id not in self._instances:
            return False
        
        agent_instance = self._instances[instance_id]
        
        try:
            # 开始初始化
            agent_instance.lifecycle.initialize()
            
            # 调用实例的初始化方法（如果有）
            if hasattr(agent_instance.instance, "initialize"):
                agent_instance.instance.initialize()
            
            # 初始化成功
            agent_instance.lifecycle.initialize_success()
            return True
            
        except Exception as e:
            # 初始化失败
            agent_instance.lifecycle.initialize_failure(str(e))
            return False
    
    def start(self, instance_id: str) -> bool:
        """启动实例.
        
        Args:
            instance_id: 实例ID
            
        Returns:
            是否成功
        """
        if instance_id not in self._instances:
            return False
        
        agent_instance = self._instances[instance_id]
        
        if not agent_instance.lifecycle.is_ready:
            return False
        
        try:
            agent_instance.lifecycle.start()
            
            if hasattr(agent_instance.instance, "start"):
                agent_instance.instance.start()
            
            return True
        except Exception:
            return False
    
    def pause(self, instance_id: str) -> bool:
        """暂停实例."""
        if instance_id not in self._instances:
            return False
        
        agent_instance = self._instances[instance_id]
        
        try:
            agent_instance.lifecycle.pause()
            
            if hasattr(agent_instance.instance, "pause"):
                agent_instance.instance.pause()
            
            return True
        except Exception:
            return False
    
    def resume(self, instance_id: str) -> bool:
        """恢复实例."""
        if instance_id not in self._instances:
            return False
        
        agent_instance = self._instances[instance_id]
        
        try:
            agent_instance.lifecycle.resume()
            
            if hasattr(agent_instance.instance, "resume"):
                agent_instance.instance.resume()
            
            return True
        except Exception:
            return False
    
    def stop(self, instance_id: str) -> bool:
        """停止实例."""
        if instance_id not in self._instances:
            return False
        
        agent_instance = self._instances[instance_id]
        
        try:
            agent_instance.lifecycle.stop()
            
            if hasattr(agent_instance.instance, "stop"):
                agent_instance.instance.stop()
            
            agent_instance.lifecycle.stop_success()
            return True
        except Exception:
            return False
    
    def terminate(self, instance_id: str) -> bool:
        """终止实例."""
        if instance_id not in self._instances:
            return False
        
        agent_instance = self._instances[instance_id]
        
        try:
            # 先停止（如果还在运行）
            if agent_instance.lifecycle.is_running:
                self.stop(instance_id)
            
            agent_instance.lifecycle.terminate()
            
            if hasattr(agent_instance.instance, "terminate"):
                agent_instance.instance.terminate()
            
            # 从实例列表移除
            del self._instances[instance_id]
            return True
        except Exception:
            return False
    
    def get(self, instance_id: str) -> Optional[AgentInstance]:
        """获取实例."""
        return self._instances.get(instance_id)
    
    def get_all(self) -> Dict[str, AgentInstance]:
        """获取所有实例."""
        return dict(self._instances)
    
    def get_by_state(self, state: LifecycleState) -> List[AgentInstance]:
        """按状态获取实例."""
        return [
            inst for inst in self._instances.values()
            if inst.state == state
        ]
    
    def get_active(self) -> List[AgentInstance]:
        """获取活跃实例."""
        return [
            inst for inst in self._instances.values()
            if inst.is_active
        ]
    
    def add_creation_hook(
        self,
        hook: Callable[[AgentInstance], None],
    ) -> None:
        """添加创建钩子."""
        self._creation_hooks.append(hook)
    
    @property
    def total_instances(self) -> int:
        """实例总数."""
        return len(self._instances)


# ========== 简单Agent实现 ==========

class SimpleAgent:
    """简单Agent实现（作为默认实现）."""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: AgentRole,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.config = config or {}
        self._status = AgentStatus.CREATED
    
    def initialize(self) -> None:
        """初始化."""
        self._status = AgentStatus.READY
    
    def start(self) -> None:
        """启动."""
        self._status = AgentStatus.RUNNING
    
    def pause(self) -> None:
        """暂停."""
        self._status = AgentStatus.PAUSED
    
    def resume(self) -> None:
        """恢复."""
        self._status = AgentStatus.RUNNING
    
    def stop(self) -> None:
        """停止."""
        self._status = AgentStatus.TERMINATED
    
    def terminate(self) -> None:
        """终止."""
        self._status = AgentStatus.TERMINATED
    
    @property
    def status(self) -> AgentStatus:
        return self._status


# ========== 工厂函数 ==========

def create_agent(
    role: AgentRole,
    name: str = "",
    config: Optional[Dict[str, Any]] = None,
    auto_initialize: bool = True,
) -> AgentInstance:
    """便捷函数：创建Agent实例."""
    factory = AgentFactory()
    creation_config = AgentCreationConfig(
        agent_id=f"agent.{role.value}",
        role=role,
        name=name,
        config=config or {},
        auto_initialize=auto_initialize,
    )
    return factory.create(creation_config)
