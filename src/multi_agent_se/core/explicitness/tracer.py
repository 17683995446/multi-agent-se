"""状态变更追踪器 - 阶段14.

实现状态可追溯验证：
- 状态变更记录
- 变更历史查询
- 变更原因追踪
- 审计日志生成
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable
import uuid


class ChangeType(Enum):
    """变更类型."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    READ = "read"


@dataclass
class StateChange:
    """状态变更记录."""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state_name: str = ""
    change_type: ChangeType = ChangeType.READ
    old_value: Any = None
    new_value: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    actor: str = ""  # 变更执行者
    reason: str = ""  # 变更原因
    stack_trace: str = ""  # 调用栈
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "change_id": self.change_id,
            "state_name": self.state_name,
            "change_type": self.change_type.value,
            "old_value": str(self.old_value) if self.old_value is not None else None,
            "new_value": str(self.new_value) if self.new_value is not None else None,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "reason": self.reason,
            "metadata": self.metadata,
        }


@dataclass
class TraceQuery:
    """追踪查询条件."""
    state_name: Optional[str] = None
    change_type: Optional[ChangeType] = None
    actor: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class StateTracer:
    """状态追踪器.
    
    记录所有状态变更，支持：
    - 变更历史查询
    - 变更原因追踪
    - 审计报告生成
    """
    
    def __init__(self, max_history: int = 10000) -> None:
        """初始化追踪器.
        
        Args:
            max_history: 最大历史记录数
        """
        self._changes: List[StateChange] = []
        self._max_history = max_history
        self._hooks: List[Callable[[StateChange], None]] = []
    
    def record(
        self,
        state_name: str,
        change_type: ChangeType,
        old_value: Any = None,
        new_value: Any = None,
        actor: str = "",
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateChange:
        """记录状态变更.
        
        Args:
            state_name: 状态名称
            change_type: 变更类型
            old_value: 旧值
            new_value: 新值
            actor: 执行者
            reason: 变更原因
            metadata: 元数据
            
        Returns:
            StateChange
        """
        change = StateChange(
            state_name=state_name,
            change_type=change_type,
            old_value=old_value,
            new_value=new_value,
            actor=actor,
            reason=reason,
            metadata=metadata or {},
        )
        
        self._changes.append(change)
        
        # 限制历史记录数
        if len(self._changes) > self._max_history:
            self._changes = self._changes[-self._max_history:]
        
        # 触发钩子
        for hook in self._hooks:
            hook(change)
        
        return change
    
    def query(self, query: TraceQuery) -> List[StateChange]:
        """查询变更历史.
        
        Args:
            query: 查询条件
            
        Returns:
            变更记录列表
        """
        results = self._changes
        
        if query.state_name:
            results = [c for c in results if c.state_name == query.state_name]
        
        if query.change_type:
            results = [c for c in results if c.change_type == query.change_type]
        
        if query.actor:
            results = [c for c in results if c.actor == query.actor]
        
        if query.start_time:
            results = [c for c in results if c.timestamp >= query.start_time]
        
        if query.end_time:
            results = [c for c in results if c.timestamp <= query.end_time]
        
        return results
    
    def get_history(self, state_name: str) -> List[StateChange]:
        """获取状态的完整变更历史.
        
        Args:
            state_name: 状态名称
            
        Returns:
            变更记录列表
        """
        return [c for c in self._changes if c.state_name == state_name]
    
    def get_last_change(self, state_name: str) -> Optional[StateChange]:
        """获取状态的最后变更.
        
        Args:
            state_name: 状态名称
            
        Returns:
            最后变更记录（无记录返回None）
        """
        history = self.get_history(state_name)
        return history[-1] if history else None
    
    def get_changes_between(
        self,
        start_time: str,
        end_time: str,
    ) -> List[StateChange]:
        """获取时间段内的变更.
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            变更记录列表
        """
        return [
            c for c in self._changes
            if start_time <= c.timestamp <= end_time
        ]
    
    def get_all_changes(self) -> List[StateChange]:
        """获取所有变更记录."""
        return list(self._changes)
    
    def get_change_count(self) -> int:
        """获取变更记录总数."""
        return len(self._changes)
    
    def get_unique_states(self) -> List[str]:
        """获取所有追踪过的状态名称."""
        return sorted(set(c.state_name for c in self._changes))
    
    def get_audit_report(self, state_name: Optional[str] = None) -> Dict[str, Any]:
        """生成审计报告.
        
        Args:
            state_name: 状态名称（None则生成全局报告）
            
        Returns:
            审计报告
        """
        changes = self.get_history(state_name) if state_name else self._changes
        
        if not changes:
            return {
                "state_name": state_name or "(all)",
                "total_changes": 0,
                "changes_by_type": {},
                "unique_actors": [],
                "time_range": None,
            }
        
        # 按类型统计
        by_type: Dict[str, int] = {}
        for c in changes:
            key = c.change_type.value
            by_type[key] = by_type.get(key, 0) + 1
        
        # 执行者
        actors = sorted(set(c.actor for c in changes if c.actor))
        
        # 时间范围
        timestamps = [c.timestamp for c in changes]
        
        return {
            "state_name": state_name or "(all)",
            "total_changes": len(changes),
            "changes_by_type": by_type,
            "unique_actors": actors,
            "time_range": {
                "start": min(timestamps),
                "end": max(timestamps),
            },
            "changes": [c.to_dict() for c in changes[-10:]],  # 最近10条
        }
    
    def register_hook(self, hook: Callable[[StateChange], None]) -> None:
        """注册变更钩子.
        
        Args:
            hook: 钩子函数
        """
        self._hooks.append(hook)
    
    def clear(self) -> None:
        """清空追踪历史."""
        self._changes.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典."""
        return {
            "total_changes": self.get_change_count(),
            "unique_states": self.get_unique_states(),
            "changes": [c.to_dict() for c in self._changes],
        }


# 全局状态追踪器实例
global_state_tracer = StateTracer()
