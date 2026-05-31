"""全局状态注册表 - 阶段14.

显式化管理所有状态，消灭隐式状态：
- 状态注册与注销
- 状态作用域管理
- 状态依赖关系
- 状态生命周期
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Callable
import uuid


class StateScope(Enum):
    """状态作用域."""
    GLOBAL = "global"       # 全局作用域
    SESSION = "session"     # 会话作用域
    TASK = "task"           # 任务作用域
    REQUEST = "request"     # 请求作用域


@dataclass
class ExplicitState:
    """显式状态记录."""
    name: str
    value: Any
    scope: StateScope
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    dependencies: Set[str] = field(default_factory=set)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    owner: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def touch(self) -> None:
        """更新访问时间."""
        self.updated_at = datetime.now().isoformat()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "state_id": self.state_id,
            "name": self.name,
            "scope": self.scope.value,
            "description": self.description,
            "dependencies": sorted(self.dependencies),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "owner": self.owner,
            "metadata": self.metadata,
        }


@dataclass
class RegistryStats:
    """注册表统计."""
    total_states: int = 0
    by_scope: Dict[str, int] = field(default_factory=dict)
    by_owner: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_states": self.total_states,
            "by_scope": self.by_scope,
            "by_owner": self.by_owner,
        }


class StateRegistry:
    """全局状态注册表.
    
    显式化管理所有状态，提供：
    - 状态注册/注销
    - 按作用域查询
    - 依赖关系管理
    - 生命周期追踪
    """
    
    def __init__(self) -> None:
        """初始化注册表."""
        self._states: Dict[str, ExplicitState] = {}  # state_id -> state
        self._name_index: Dict[str, str] = {}  # name -> state_id
        self._scope_index: Dict[StateScope, Set[str]] = {
            scope: set() for scope in StateScope
        }
        self._hooks: Dict[str, List[Callable[[ExplicitState], None]]] = {
            "register": [],
            "update": [],
            "unregister": [],
        }
    
    def register(
        self,
        name: str,
        value: Any,
        scope: StateScope = StateScope.GLOBAL,
        description: str = "",
        dependencies: Optional[Set[str]] = None,
        owner: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExplicitState:
        """注册状态.
        
        Args:
            name: 状态名称
            value: 状态值
            scope: 作用域
            description: 描述
            dependencies: 依赖的状态名集合
            owner: 所有者
            metadata: 元数据
            
        Returns:
            ExplicitState
            
        Raises:
            ValueError: 状态名已存在
        """
        if name in self._name_index:
            raise ValueError(f"状态 '{name}' 已存在")
        
        state = ExplicitState(
            name=name,
            value=value,
            scope=scope,
            description=description,
            dependencies=dependencies or set(),
            owner=owner,
            metadata=metadata or {},
        )
        
        self._states[state.state_id] = state
        self._name_index[name] = state.state_id
        self._scope_index[scope].add(state.state_id)
        
        # 触发钩子
        for hook in self._hooks["register"]:
            hook(state)
        
        return state
    
    def unregister(self, name: str) -> bool:
        """注销状态.
        
        Args:
            name: 状态名称
            
        Returns:
            是否成功注销
        """
        if name not in self._name_index:
            return False
        
        state_id = self._name_index[name]
        state = self._states.get(state_id)
        
        if state:
            # 触发钩子
            for hook in self._hooks["unregister"]:
                hook(state)
            
            # 清理索引
            self._scope_index[state.scope].discard(state_id)
            del self._states[state_id]
        
        del self._name_index[name]
        return True
    
    def get(self, name: str) -> Optional[Any]:
        """获取状态值.
        
        Args:
            name: 状态名称
            
        Returns:
            状态值（不存在返回None）
        """
        state_id = self._name_index.get(name)
        if not state_id:
            return None
        
        state = self._states.get(state_id)
        if state:
            state.touch()
            return state.value
        return None
    
    def get_state(self, name: str) -> Optional[ExplicitState]:
        """获取完整状态记录.
        
        Args:
            name: 状态名称
            
        Returns:
            ExplicitState（不存在返回None）
        """
        state_id = self._name_index.get(name)
        if not state_id:
            return None
        return self._states.get(state_id)
    
    def update(self, name: str, value: Any) -> bool:
        """更新状态值.
        
        Args:
            name: 状态名称
            value: 新值
            
        Returns:
            是否成功更新
        """
        state = self.get_state(name)
        if not state:
            return False
        
        state.value = value
        state.touch()
        
        # 触发钩子
        for hook in self._hooks["update"]:
            hook(state)
        
        return True
    
    def exists(self, name: str) -> bool:
        """检查状态是否存在.
        
        Args:
            name: 状态名称
            
        Returns:
            True如果存在
        """
        return name in self._name_index
    
    def get_by_scope(self, scope: StateScope) -> List[ExplicitState]:
        """按作用域获取状态.
        
        Args:
            scope: 作用域
            
        Returns:
            状态列表
        """
        state_ids = self._scope_index.get(scope, set())
        return [self._states[sid] for sid in state_ids if sid in self._states]
    
    def get_by_owner(self, owner: str) -> List[ExplicitState]:
        """按所有者获取状态.
        
        Args:
            owner: 所有者
            
        Returns:
            状态列表
        """
        return [
            state for state in self._states.values()
            if state.owner == owner
        ]
    
    def get_dependencies(self, name: str) -> List[ExplicitState]:
        """获取状态的依赖.
        
        Args:
            name: 状态名称
            
        Returns:
            依赖的状态列表
        """
        state = self.get_state(name)
        if not state:
            return []
        
        return [
            self.get_state(dep_name)
            for dep_name in state.dependencies
            if self.exists(dep_name)
        ]
    
    def get_dependents(self, name: str) -> List[ExplicitState]:
        """获取依赖此状态的状态.
        
        Args:
            name: 状态名称
            
        Returns:
            依赖方状态列表
        """
        return [
            state for state in self._states.values()
            if name in state.dependencies
        ]
    
    def get_all_names(self) -> List[str]:
        """获取所有状态名称."""
        return sorted(self._name_index.keys())
    
    def get_stats(self) -> RegistryStats:
        """获取统计信息."""
        by_scope: Dict[str, int] = {}
        by_owner: Dict[str, int] = {}
        
        for state in self._states.values():
            scope_key = state.scope.value
            by_scope[scope_key] = by_scope.get(scope_key, 0) + 1
            
            owner_key = state.owner or "(unowned)"
            by_owner[owner_key] = by_owner.get(owner_key, 0) + 1
        
        return RegistryStats(
            total_states=len(self._states),
            by_scope=by_scope,
            by_owner=by_owner,
        )
    
    def register_hook(
        self,
        event: str,
        hook: Callable[[ExplicitState], None],
    ) -> None:
        """注册事件钩子.
        
        Args:
            event: 事件类型 (register/update/unregister)
            hook: 钩子函数
        """
        if event in self._hooks:
            self._hooks[event].append(hook)
    
    def clear(self) -> None:
        """清空注册表."""
        self._states.clear()
        self._name_index.clear()
        for scope in self._scope_index:
            self._scope_index[scope].clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典."""
        return {
            "states": [s.to_dict() for s in self._states.values()],
            "stats": self.get_stats().to_dict(),
        }


# 全局状态注册表实例
global_state_registry = StateRegistry()
