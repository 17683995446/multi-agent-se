"""故障隔离 - 第51阶段.

实现级联故障隔离机制：
- 隔离域划分
- 故障扩散阻断
- 资源隔离保护
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set


@dataclass
class IsolationZone:
    """隔离域."""
    zone_id: str
    name: str = ""
    components: Set[str] = field(default_factory=set)
    isolated_at: Optional[datetime] = None
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_isolated(self) -> bool:
        return self.isolated_at is not None

    def isolate(self, reason: str = "") -> None:
        """隔离域."""
        self.isolated_at = datetime.now()
        self.reason = reason

    def restore(self) -> None:
        """恢复域."""
        self.isolated_at = None
        self.reason = ""

    def add_component(self, component_id: str) -> None:
        """添加组件."""
        self.components.add(component_id)

    def remove_component(self, component_id: str) -> None:
        """移除组件."""
        self.components.discard(component_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "name": self.name,
            "components": list(self.components),
            "is_isolated": self.is_isolated,
            "isolated_at": self.isolated_at.isoformat() if self.isolated_at else None,
            "reason": self.reason,
        }


class FaultIsolator:
    """故障隔离器.

    管理隔离域，阻断故障扩散：
    - 按域隔离故障组件
    - 限制跨域影响
    - 支持手动/自动隔离
    """

    def __init__(
        self,
        auto_isolate_threshold: int = 3,
        isolation_timeout_seconds: float = 300.0,
    ) -> None:
        self._auto_threshold = auto_isolate_threshold
        self._isolation_timeout = timedelta(seconds=isolation_timeout_seconds)

        self._zones: Dict[str, IsolationZone] = {}
        self._component_zone: Dict[str, str] = {}
        self._failure_counts: Dict[str, int] = {}

    def create_zone(self, zone_id: str, name: str = "") -> IsolationZone:
        """创建隔离域."""
        zone = IsolationZone(zone_id=zone_id, name=name or zone_id)
        self._zones[zone_id] = zone
        return zone

    def delete_zone(self, zone_id: str) -> bool:
        """删除隔离域."""
        if zone_id not in self._zones:
            return False

        zone = self._zones[zone_id]
        for comp in zone.components:
            self._component_zone.pop(comp, None)
        del self._zones[zone_id]
        return True

    def assign_component(self, component_id: str, zone_id: str) -> bool:
        """将组件分配到隔离域."""
        if zone_id not in self._zones:
            return False

        # 从旧域移除
        old_zone = self._component_zone.get(component_id)
        if old_zone and old_zone in self._zones:
            self._zones[old_zone].remove_component(component_id)

        # 添加到新域
        self._zones[zone_id].add_component(component_id)
        self._component_zone[component_id] = zone_id
        return True

    def isolate_zone(self, zone_id: str, reason: str = "") -> bool:
        """隔离指定域."""
        if zone_id not in self._zones:
            return False

        self._zones[zone_id].isolate(reason)
        return True

    def isolate_component(self, component_id: str, reason: str = "") -> bool:
        """隔离组件所在域."""
        zone_id = self._component_zone.get(component_id)
        if zone_id:
            return self.isolate_zone(zone_id, reason)
        return False

    def restore_zone(self, zone_id: str) -> bool:
        """恢复指定域."""
        if zone_id not in self._zones:
            return False

        self._zones[zone_id].restore()
        self._failure_counts[zone_id] = 0
        return True

    def record_failure(self, component_id: str) -> bool:
        """记录组件故障，可能触发自动隔离.

        Returns:
            是否触发了隔离
        """
        zone_id = self._component_zone.get(component_id)
        if not zone_id:
            return False

        self._failure_counts[zone_id] = self._failure_counts.get(zone_id, 0) + 1

        # 检查是否达到自动隔离阈值
        if self._failure_counts[zone_id] >= self._auto_threshold:
            if not self._zones[zone_id].is_isolated:
                self.isolate_zone(
                    zone_id,
                    reason=f"自动隔离：故障次数达到阈值 {self._auto_threshold}",
                )
                return True
        return False

    def can_communicate(self, from_id: str, to_id: str) -> bool:
        """检查两个组件是否可以通信.

        规则：
        - 任一组件所在域被隔离 → 不能通信
        """
        from_zone = self._component_zone.get(from_id)
        to_zone = self._component_zone.get(to_id)

        if from_zone and from_zone in self._zones:
            if self._zones[from_zone].is_isolated:
                return False

        if to_zone and to_zone in self._zones:
            if self._zones[to_zone].is_isolated:
                return False

        return True

    def get_zone(self, component_id: str) -> Optional[IsolationZone]:
        """获取组件所在域."""
        zone_id = self._component_zone.get(component_id)
        if zone_id:
            return self._zones.get(zone_id)
        return None

    def get_isolated_zones(self) -> List[IsolationZone]:
        """获取所有被隔离的域."""
        return [z for z in self._zones.values() if z.is_isolated]

    def cleanup_expired(self) -> int:
        """清理过期的隔离.

        Returns:
            恢复的域数量
        """
        now = datetime.now()
        restored = 0

        for zone in self._zones.values():
            if zone.is_isolated and zone.isolated_at:
                elapsed = now - zone.isolated_at
                if elapsed > self._isolation_timeout:
                    zone.restore()
                    restored += 1

        return restored

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息."""
        total = len(self._zones)
        isolated = len(self.get_isolated_zones())
        return {
            "total_zones": total,
            "isolated_zones": isolated,
            "healthy_zones": total - isolated,
            "total_components": len(self._component_zone),
            "failure_counts": dict(self._failure_counts),
        }
