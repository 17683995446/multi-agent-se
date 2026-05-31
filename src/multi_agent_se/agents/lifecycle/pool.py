"""Agent实例池管理 - 阶段17.

实现Agent实例的池化管理：
- AgentPool实例池
- 实例复用
- 资源限制
"""

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional, Set

from multi_agent_se.agents.registry import (
    AgentRole,
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
from multi_agent_se.agents.lifecycle.factory import (
    AgentFactory,
    AgentInstance,
    AgentCreationConfig,
)


class PoolError(Exception):
    """池错误."""
    pass


class PoolFullError(PoolError):
    """池已满错误."""
    pass


class InstanceNotFoundError(PoolError):
    """实例未找到错误."""
    pass


@dataclass
class PoolConfig:
    """池配置."""
    max_instances: int = 100           # 最大实例数
    max_per_role: int = 20             # 每角色最大实例数
    idle_timeout_seconds: int = 300    # 空闲超时（秒）
    enable_auto_cleanup: bool = True   # 启用自动清理
    enable_instance_reuse: bool = True # 启用实例复用


@dataclass
class PoolStats:
    """池统计."""
    total_instances: int = 0
    active_instances: int = 0
    idle_instances: int = 0
    by_role: Dict[str, int] = field(default_factory=dict)
    by_state: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_instances": self.total_instances,
            "active_instances": self.active_instances,
            "idle_instances": self.idle_instances,
            "by_role": self.by_role,
            "by_state": self.by_state,
        }


class AgentPool:
    """Agent实例池.
    
    管理Agent实例的生命周期和资源
    """
    
    def __init__(
        self,
        config: Optional[PoolConfig] = None,
        registry: Optional[AgentRegistry] = None,
    ) -> None:
        """初始化实例池.
        
        Args:
            config: 池配置
            registry: Agent注册表
        """
        self._config = config or PoolConfig()
        self._registry = registry or get_registry()
        self._factory = AgentFactory(self._registry)
        
        # 实例存储
        self._instances: Dict[str, AgentInstance] = {}
        self._by_role: Dict[AgentRole, Set[str]] = {role: set() for role in AgentRole}
        
        # 空闲实例（可复用）
        self._idle: Dict[str, datetime] = {}  # instance_id -> 进入空闲时间
        
        # 锁（线程安全）
        self._lock = Lock()
    
    # ========== 实例获取 ==========
    
    def acquire(
        self,
        role: AgentRole,
        config: Optional[Dict[str, Any]] = None,
        prefer_idle: bool = True,
    ) -> AgentInstance:
        """获取实例（用于执行任务）.
        
        Args:
            role: 角色类型
            config: 创建配置（如果需要新建）
            prefer_idle: 是否优先使用空闲实例
            
        Returns:
            AgentInstance
            
        Raises:
            PoolFullError: 池已满
        """
        with self._lock:
            # 尝试复用空闲实例
            if prefer_idle and self._config.enable_instance_reuse:
                idle_instance = self._find_idle_instance(role)
                if idle_instance:
                    # 从空闲列表移除
                    self._idle.pop(idle_instance.instance_id, None)
                    # 启动实例
                    if idle_instance.lifecycle.is_ready:
                        idle_instance.lifecycle.start()
                    return idle_instance
            
            # 检查池是否已满
            if len(self._instances) >= self._config.max_instances:
                raise PoolFullError(
                    f"Pool is full (max: {self._config.max_instances})"
                )
            
            # 检查角色限制
            if len(self._by_role[role]) >= self._config.max_per_role:
                raise PoolFullError(
                    f"Role {role.value} pool is full (max: {self._config.max_per_role})"
                )
            
            # 创建新实例
            creation_config = AgentCreationConfig(
                agent_id=f"pool.{role.value}",
                role=role,
                config=config or {},
                auto_initialize=True,
                auto_start=True,
            )
            
            instance = self._factory.create(creation_config)
            
            # 添加到池
            self._instances[instance.instance_id] = instance
            self._by_role[role].add(instance.instance_id)
            
            return instance
    
    def release(self, instance_id: str) -> bool:
        """释放实例（任务完成后）.
        
        Args:
            instance_id: 实例ID
            
        Returns:
            是否成功
        """
        with self._lock:
            if instance_id not in self._instances:
                return False
            
            instance = self._instances[instance_id]
            
            # 将实例恢复到READY状态（以便复用）
            current_state = instance.lifecycle.state
            if current_state == LifecycleState.RUNNING:
                # RUNNING -> READY (直接指定目标状态)
                instance.lifecycle.transition(
                    LifecycleEvent.RUN,
                    target=LifecycleState.READY,
                )
            elif current_state == LifecycleState.PAUSED:
                # PAUSED -> RUNNING -> READY
                instance.lifecycle.resume()
                instance.lifecycle.transition(
                    LifecycleEvent.RUN,
                    target=LifecycleState.READY,
                )
            
            # 添加到空闲列表
            if self._config.enable_instance_reuse:
                self._idle[instance_id] = datetime.now()
            
            return True
    
    def _find_idle_instance(self, role: AgentRole) -> Optional[AgentInstance]:
        """查找空闲实例."""
        for instance_id in self._by_role[role]:
            if instance_id in self._idle:
                instance = self._instances.get(instance_id)
                if instance and instance.lifecycle.is_ready:
                    return instance
        return None
    
    # ========== 实例管理 ==========
    
    def get(self, instance_id: str) -> Optional[AgentInstance]:
        """获取实例."""
        return self._instances.get(instance_id)
    
    def get_all(self) -> Dict[str, AgentInstance]:
        """获取所有实例."""
        return dict(self._instances)
    
    def get_by_role(self, role: AgentRole) -> List[AgentInstance]:
        """按角色获取实例."""
        return [
            self._instances[inst_id]
            for inst_id in self._by_role[role]
            if inst_id in self._instances
        ]
    
    def get_active(self) -> List[AgentInstance]:
        """获取活跃实例."""
        return [
            inst for inst in self._instances.values()
            if inst.is_active
        ]
    
    def get_idle(self) -> List[AgentInstance]:
        """获取空闲实例."""
        return [
            self._instances[inst_id]
            for inst_id in self._idle
            if inst_id in self._instances
        ]
    
    def pause(self, instance_id: str) -> bool:
        """暂停实例."""
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        
        try:
            instance.lifecycle.pause()
            return True
        except Exception:
            return False
    
    def resume(self, instance_id: str) -> bool:
        """恢复实例."""
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        
        try:
            instance.lifecycle.resume()
            # 从空闲列表移除
            self._idle.pop(instance_id, None)
            return True
        except Exception:
            return False
    
    def stop(self, instance_id: str) -> bool:
        """停止实例."""
        instance = self._instances.get(instance_id)
        if not instance:
            return False
        
        try:
            instance.lifecycle.stop()
            instance.lifecycle.stop_success()
            # 从空闲列表移除
            self._idle.pop(instance_id, None)
            return True
        except Exception:
            return False
    
    def remove(self, instance_id: str) -> bool:
        """移除实例（从池中删除）."""
        with self._lock:
            if instance_id not in self._instances:
                return False
            
            instance = self._instances[instance_id]
            
            # 先停止
            self.stop(instance_id)
            
            # 终止
            try:
                instance.lifecycle.terminate()
            except Exception:
                pass
            
            # 从各索引移除
            del self._instances[instance_id]
            self._by_role[instance.metadata.role].discard(instance_id)
            self._idle.pop(instance_id, None)
            
            return True
    
    # ========== 池操作 ==========
    
    def clear(self) -> int:
        """清空池.
        
        Returns:
            移除的实例数
        """
        with self._lock:
            count = len(self._instances)
            
            # 停止所有实例
            for instance in self._instances.values():
                try:
                    instance.lifecycle.stop()
                    instance.lifecycle.stop_success()
                    instance.lifecycle.terminate()
                except Exception:
                    pass
            
            # 清空索引
            self._instances.clear()
            for role in self._by_role:
                self._by_role[role].clear()
            self._idle.clear()
            
            return count
    
    def cleanup_idle(self, timeout_seconds: Optional[int] = None) -> int:
        """清理超时的空闲实例.
        
        Args:
            timeout_seconds: 超时时间（秒）
            
        Returns:
            清理的实例数
        """
        timeout = timeout_seconds or self._config.idle_timeout_seconds
        now = datetime.now()
        
        to_remove = []
        for instance_id, idle_time in self._idle.items():
            elapsed = (now - idle_time).total_seconds()
            if elapsed > timeout:
                to_remove.append(instance_id)
        
        for instance_id in to_remove:
            self.remove(instance_id)
        
        return len(to_remove)
    
    def cleanup_stopped(self) -> int:
        """清理已停止的实例."""
        to_remove = [
            inst.instance_id
            for inst in self._instances.values()
            if inst.lifecycle.is_stopped or inst.lifecycle.is_terminated
        ]
        
        for instance_id in to_remove:
            self.remove(instance_id)
        
        return len(to_remove)
    
    # ========== 统计 ==========
    
    def get_stats(self) -> PoolStats:
        """获取池统计."""
        by_role = {
            role.value: len(ids)
            for role, ids in self._by_role.items()
            if len(ids) > 0
        }
        
        by_state: Dict[str, int] = {}
        for instance in self._instances.values():
            state = instance.state.value
            by_state[state] = by_state.get(state, 0) + 1
        
        return PoolStats(
            total_instances=len(self._instances),
            active_instances=len(self.get_active()),
            idle_instances=len(self._idle),
            by_role=by_role,
            by_state=by_state,
        )
    
    @property
    def total_instances(self) -> int:
        """实例总数."""
        return len(self._instances)
    
    @property
    def active_count(self) -> int:
        """活跃实例数."""
        return len(self.get_active())
    
    @property
    def idle_count(self) -> int:
        """空闲实例数."""
        return len(self._idle)
    
    @property
    def is_full(self) -> bool:
        """是否已满."""
        return len(self._instances) >= self._config.max_instances


# ========== 全局实例池 ==========

_global_pool: Optional[AgentPool] = None


def get_pool() -> AgentPool:
    """获取全局实例池."""
    global _global_pool
    if _global_pool is None:
        _global_pool = AgentPool()
    return _global_pool


def reset_pool() -> None:
    """重置全局实例池."""
    global _global_pool
    if _global_pool is not None:
        _global_pool.clear()
    _global_pool = AgentPool()
