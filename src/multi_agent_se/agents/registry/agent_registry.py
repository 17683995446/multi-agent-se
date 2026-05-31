"""Agent注册表 - 阶段16.

实现Agent的注册、发现、查询功能：
- AgentRegistry: 中央注册表
- 动态发现机制
- 能力查询
"""

import importlib
import inspect
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from multi_agent_se.agents.registry.metadata import (
    AgentRole,
    AgentStatus,
    AgentCapability,
    AgentMetadata,
    AgentCapabilityDeclaration,
    AgentRegistrationInfo,
)


class AgentRegistryError(Exception):
    """Agent注册表错误."""
    pass


class AgentNotFoundError(AgentRegistryError):
    """Agent未找到错误."""
    pass


class AgentAlreadyRegisteredError(AgentRegistryError):
    """Agent已注册错误."""
    pass


@dataclass
class RegistryStats:
    """注册表统计."""
    total_agents: int = 0
    by_role: Dict[str, int] = field(default_factory=dict)
    by_status: Dict[str, int] = field(default_factory=dict)
    by_capability: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_agents": self.total_agents,
            "by_role": self.by_role,
            "by_status": self.by_status,
            "by_capability": self.by_capability,
        }


class AgentRegistry:
    """Agent注册表.
    
    管理所有Agent的注册、发现、查询
    """
    
    def __init__(self) -> None:
        """初始化注册表."""
        self._agents: Dict[str, AgentRegistrationInfo] = {}
        self._by_role: Dict[AgentRole, Set[str]] = {role: set() for role in AgentRole}
        self._by_capability: Dict[AgentCapability, Set[str]] = {
            cap: set() for cap in AgentCapability
        }
        self._by_status: Dict[AgentStatus, Set[str]] = {
            status: set() for status in AgentStatus
        }
    
    # ========== 注册操作 ==========
    
    def register(
        self,
        metadata: AgentMetadata,
        agent_class: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
    ) -> str:
        """注册Agent.
        
        Args:
            metadata: Agent元数据
            agent_class: Agent类（可选）
            factory: 工厂函数（可选）
            instance: 实例（可选）
            
        Returns:
            agent_id
            
        Raises:
            AgentAlreadyRegisteredError: 如果agent_id已存在
        """
        agent_id = metadata.agent_id
        
        if agent_id in self._agents:
            raise AgentAlreadyRegisteredError(f"Agent '{agent_id}' 已注册")
        
        # 创建注册信息
        info = AgentRegistrationInfo(
            metadata=metadata,
            agent_class=agent_class,
            factory=factory,
            instance=instance,
        )
        
        # 存储到主字典
        self._agents[agent_id] = info
        
        # 更新索引
        self._by_role[metadata.role].add(agent_id)
        self._by_status[metadata.status].add(agent_id)
        
        for cap in metadata.capabilities:
            self._by_capability[cap.capability].add(agent_id)
        
        return agent_id
    
    def unregister(self, agent_id: str) -> bool:
        """注销Agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功注销
        """
        if agent_id not in self._agents:
            return False
        
        info = self._agents[agent_id]
        metadata = info.metadata
        
        # 从索引中移除
        self._by_role[metadata.role].discard(agent_id)
        self._by_status[metadata.status].discard(agent_id)
        
        for cap in metadata.capabilities:
            self._by_capability[cap.capability].discard(agent_id)
        
        # 从主字典移除
        del self._agents[agent_id]
        
        return True
    
    def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
    ) -> bool:
        """更新Agent状态.
        
        Args:
            agent_id: Agent ID
            status: 新状态
            
        Returns:
            是否成功更新
        """
        if agent_id not in self._agents:
            return False
        
        info = self._agents[agent_id]
        old_status = info.metadata.status
        
        # 更新状态索引
        self._by_status[old_status].discard(agent_id)
        self._by_status[status].add(agent_id)
        
        # 更新元数据
        info.metadata.update_status(status)
        
        return True
    
    # ========== 查询操作 ==========
    
    def get(self, agent_id: str) -> AgentRegistrationInfo:
        """获取Agent注册信息.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentRegistrationInfo
            
        Raises:
            AgentNotFoundError: 如果Agent不存在
        """
        if agent_id not in self._agents:
            raise AgentNotFoundError(f"Agent '{agent_id}' 未找到")
        return self._agents[agent_id]
    
    def get_metadata(self, agent_id: str) -> AgentMetadata:
        """获取Agent元数据."""
        return self.get(agent_id).metadata
    
    def get_instance(self, agent_id: str) -> Optional[Any]:
        """获取Agent实例."""
        return self.get(agent_id).instance
    
    def get_all(self) -> Dict[str, AgentRegistrationInfo]:
        """获取所有Agent."""
        return dict(self._agents)
    
    def get_by_role(self, role: AgentRole) -> List[AgentRegistrationInfo]:
        """按角色获取Agent."""
        return [
            self._agents[agent_id]
            for agent_id in self._by_role[role]
            if agent_id in self._agents
        ]
    
    def get_by_capability(
        self,
        capability: AgentCapability,
        min_proficiency: float = 0.0,
    ) -> List[AgentRegistrationInfo]:
        """按能力获取Agent.
        
        Args:
            capability: 能力类型
            min_proficiency: 最小熟练度
            
        Returns:
            符合条件的Agent列表
        """
        result = []
        for agent_id in self._by_capability[capability]:
            if agent_id not in self._agents:
                continue
            
            info = self._agents[agent_id]
            proficiency = info.metadata.get_capability_proficiency(capability)
            
            if proficiency >= min_proficiency:
                result.append(info)
        
        return result
    
    def get_by_status(self, status: AgentStatus) -> List[AgentRegistrationInfo]:
        """按状态获取Agent."""
        return [
            self._agents[agent_id]
            for agent_id in self._by_status[status]
            if agent_id in self._agents
        ]
    
    def get_available(self) -> List[AgentRegistrationInfo]:
        """获取可用的Agent."""
        return self.get_by_status(AgentStatus.READY) + self.get_by_status(AgentStatus.RUNNING)
    
    def find_best_for_capability(
        self,
        capability: AgentCapability,
        exclude: Optional[Set[str]] = None,
    ) -> Optional[AgentRegistrationInfo]:
        """找到最适合某能力的Agent.
        
        Args:
            capability: 能力类型
            exclude: 排除的Agent ID集合
            
        Returns:
            最佳Agent（熟练度最高且可用）
        """
        exclude = exclude or set()
        candidates = self.get_by_capability(capability)
        
        # 过滤：可用且不在排除列表
        available = [
            info for info in candidates
            if info.metadata.is_available and info.metadata.agent_id not in exclude
        ]
        
        if not available:
            return None
        
        # 按熟练度排序
        available.sort(
            key=lambda info: info.metadata.get_capability_proficiency(capability),
            reverse=True,
        )
        
        return available[0]
    
    def has_agent(self, agent_id: str) -> bool:
        """检查Agent是否存在."""
        return agent_id in self._agents
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """检查是否有Agent具有某能力."""
        return len(self._by_capability[capability]) > 0
    
    # ========== 统计 ==========
    
    def get_stats(self) -> RegistryStats:
        """获取注册表统计."""
        by_role = {role.value: len(ids) for role, ids in self._by_role.items()}
        by_status = {status.value: len(ids) for status, ids in self._by_status.items()}
        by_capability = {
            cap.value: len(ids)
            for cap, ids in self._by_capability.items()
            if len(ids) > 0
        }
        
        return RegistryStats(
            total_agents=len(self._agents),
            by_role=by_role,
            by_status=by_status,
            by_capability=by_capability,
        )
    
    @property
    def total_agents(self) -> int:
        """Agent总数."""
        return len(self._agents)
    
    # ========== 清理 ==========
    
    def clear(self) -> None:
        """清空注册表."""
        self._agents.clear()
        for role in self._by_role:
            self._by_role[role].clear()
        for cap in self._by_capability:
            self._by_capability[cap].clear()
        for status in self._by_status:
            self._by_status[status].clear()


# ========== 全局注册表实例 ==========
_global_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """获取全局注册表实例."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def reset_registry() -> None:
    """重置全局注册表."""
    global _global_registry
    if _global_registry is not None:
        _global_registry.clear()
    _global_registry = AgentRegistry()
