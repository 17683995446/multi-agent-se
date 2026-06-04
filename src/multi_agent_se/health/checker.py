"""健康检查核心 - 第50阶段.

提供统一的健康检查框架：
- 组件健康状态枚举
- 健康报告生成
- 聚合健康状态判定
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable


class HealthStatus(Enum):
    """健康状态."""
    HEALTHY = "healthy"       # 健康
    DEGRADED = "degraded"     # 降级（可用但有问题）
    UNHEALTHY = "unhealthy"   # 不健康
    UNKNOWN = "unknown"       # 未知（未检查）


@dataclass
class ComponentHealth:
    """单个组件健康信息."""
    name: str                           # 组件名称
    status: HealthStatus                # 健康状态
    message: str = ""                   # 状态说明
    last_check: Optional[datetime] = None  # 最后检查时间
    metrics: Dict[str, Any] = field(default_factory=dict)  # 指标数据
    details: Dict[str, Any] = field(default_factory=dict)  # 详细信息

    def __post_init__(self):
        if self.last_check is None:
            self.last_check = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "metrics": self.metrics,
            "details": self.details,
        }


@dataclass
class HealthReport:
    """系统健康报告."""
    overall_status: HealthStatus        # 整体状态
    components: List[ComponentHealth]   # 各组件状态
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"

    @property
    def healthy_count(self) -> int:
        return sum(1 for c in self.components if c.status == HealthStatus.HEALTHY)

    @property
    def degraded_count(self) -> int:
        return sum(1 for c in self.components if c.status == HealthStatus.DEGRADED)

    @property
    def unhealthy_count(self) -> int:
        return sum(1 for c in self.components if c.status == HealthStatus.UNHEALTHY)

    @property
    def is_healthy(self) -> bool:
        return self.overall_status == HealthStatus.HEALTHY

    @property
    def is_ready(self) -> bool:
        return self.overall_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "components": [c.to_dict() for c in self.components],
            "generated_at": self.generated_at.isoformat(),
            "version": self.version,
            "summary": {
                "healthy": self.healthy_count,
                "degraded": self.degraded_count,
                "unhealthy": self.unhealthy_count,
                "total": len(self.components),
            },
        }


class HealthChecker:
    """健康检查器.

    统一管理所有组件的健康检查，支持：
    - 注册自定义检查器
    - 定时/手动触发检查
    - 聚合状态判定
    """

    def __init__(self) -> None:
        self._checkers: Dict[str, Callable[[], ComponentHealth]] = {}
        self._last_report: Optional[HealthReport] = None

    def register(
        self,
        name: str,
        checker: Callable[[], ComponentHealth],
    ) -> None:
        """注册健康检查器.

        Args:
            name: 组件名称
            checker: 返回ComponentHealth的函数
        """
        self._checkers[name] = checker

    def unregister(self, name: str) -> bool:
        """注销健康检查器."""
        if name in self._checkers:
            del self._checkers[name]
            return True
        return False

    def check(self, component_name: Optional[str] = None) -> HealthReport:
        """执行健康检查.

        Args:
            component_name: 指定组件（None表示全部）

        Returns:
            HealthReport
        """
        components: List[ComponentHealth] = []

        if component_name:
            checker = self._checkers.get(component_name)
            if checker:
                try:
                    components.append(checker())
                except Exception as e:
                    components.append(ComponentHealth(
                        name=component_name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"检查异常: {e}",
                    ))
        else:
            for name, checker in self._checkers.items():
                try:
                    components.append(checker())
                except Exception as e:
                    components.append(ComponentHealth(
                        name=name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"检查异常: {e}",
                    ))

        # 聚合状态判定
        overall = self._aggregate_status(components)

        report = HealthReport(
            overall_status=overall,
            components=components,
        )
        self._last_report = report
        return report

    def _aggregate_status(self, components: List[ComponentHealth]) -> HealthStatus:
        """聚合状态判定.

        规则：
        - 任一UNHEALTHY → UNHEALTHY
        - 任一DEGRADED且无UNHEALTHY → DEGRADED
        - 全部HEALTHY → HEALTHY
        - 无组件 → UNKNOWN
        """
        if not components:
            return HealthStatus.UNKNOWN

        statuses = [c.status for c in components]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        return HealthStatus.UNKNOWN

    def get_last_report(self) -> Optional[HealthReport]:
        """获取上次检查报告."""
        return self._last_report

    def is_healthy(self) -> bool:
        """快速检查：是否健康."""
        report = self.check()
        return report.is_healthy

    def is_ready(self) -> bool:
        """快速检查：是否就绪（健康或降级）."""
        report = self.check()
        return report.is_ready
