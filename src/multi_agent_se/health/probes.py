"""健康探针 - 第50阶段.

提供Kubernetes风格的健康探针：
- LivenessProbe: 存活探针（进程是否运行）
- ReadinessProbe: 就绪探针（是否可以接收流量）
- StartupProbe: 启动探针（是否完成启动）
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from multi_agent_se.health.checker import HealthChecker, HealthReport, HealthStatus


@dataclass
class ProbeResult:
    """探针结果."""
    success: bool
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


class LivenessProbe:
    """存活探针.

    检测系统进程是否存活。如果失败，表示系统需要被重启。
    """

    def __init__(
        self,
        health_checker: Optional[HealthChecker] = None,
        max_failures: int = 3,
        check_interval_seconds: float = 10.0,
    ) -> None:
        self._checker = health_checker or HealthChecker()
        self._max_failures = max_failures
        self._interval = timedelta(seconds=check_interval_seconds)
        self._failure_count = 0
        self._last_check: Optional[datetime] = None

    def check(self) -> ProbeResult:
        """执行存活检查.

        规则：
        - 任一组件UNHEALTHY → 失败计数+1
        - 连续失败达到max_failures → 建议重启
        - 成功则重置失败计数
        """
        now = datetime.now()
        self._last_check = now

        report = self._checker.check()

        # 检查是否有严重故障
        unhealthy_components = [
            c.name for c in report.components
            if c.status == HealthStatus.UNHEALTHY
        ]

        if unhealthy_components:
            self._failure_count += 1
            if self._failure_count >= self._max_failures:
                return ProbeResult(
                    success=False,
                    message=f"存活检查失败 {self._failure_count} 次，建议重启. "
                            f"故障组件: {unhealthy_components}",
                    details={
                        "failure_count": self._failure_count,
                        "unhealthy_components": unhealthy_components,
                        "report": report.to_dict(),
                    },
                )
            return ProbeResult(
                success=True,
                message=f"存活检查警告: 故障组件 {unhealthy_components} "
                        f"(失败计数: {self._failure_count}/{self._max_failures})",
                details={
                    "failure_count": self._failure_count,
                    "unhealthy_components": unhealthy_components,
                },
            )
        else:
            self._failure_count = 0
            return ProbeResult(
                success=True,
                message="存活检查通过",
                details={"components_checked": len(report.components)},
            )

    @property
    def should_restart(self) -> bool:
        """是否需要重启."""
        return self._failure_count >= self._max_failures


class ReadinessProbe:
    """就绪探针.

    检测系统是否准备好接收流量。如果失败，表示系统不应接收新请求。
    """

    def __init__(
        self,
        health_checker: Optional[HealthChecker] = None,
        required_components: Optional[List[str]] = None,
    ) -> None:
        self._checker = health_checker or HealthChecker()
        self._required = required_components or []

    def check(self) -> ProbeResult:
        """执行就绪检查.

        规则：
        - 整体状态为HEALTHY或DEGRADED → 就绪
        - 有required_components时，这些组件必须HEALTHY
        """
        report = self._checker.check()

        if not report.is_ready:
            return ProbeResult(
                success=False,
                message=f"系统未就绪: {report.overall_status.value}",
                details={"report": report.to_dict()},
            )

        # 检查必需组件
        if self._required:
            component_map = {c.name: c for c in report.components}
            missing = [name for name in self._required if name not in component_map]
            if missing:
                return ProbeResult(
                    success=False,
                    message=f"必需组件缺失: {missing}",
                    details={"missing": missing},
                )

            not_healthy = [
                name for name in self._required
                if component_map[name].status != HealthStatus.HEALTHY
            ]
            if not_healthy:
                return ProbeResult(
                    success=False,
                    message=f"必需组件不健康: {not_healthy}",
                    details={"not_healthy": not_healthy},
                )

        return ProbeResult(
            success=True,
            message="系统已就绪",
            details={
                "overall_status": report.overall_status.value,
                "components": len(report.components),
            },
        )


class StartupProbe:
    """启动探针.

    检测系统是否完成启动。在启动期间，存活探针和就绪探针被禁用。
    """

    def __init__(
        self,
        health_checker: Optional[HealthChecker] = None,
        startup_timeout_seconds: float = 60.0,
        success_threshold: int = 1,
    ) -> None:
        self._checker = health_checker or HealthChecker()
        self._timeout = timedelta(seconds=startup_timeout_seconds)
        self._success_threshold = success_threshold
        self._success_count = 0
        self._start_time = datetime.now()
        self._started = False

    def check(self) -> ProbeResult:
        """执行启动检查.

        规则：
        - 超时前达到success_threshold次成功 → 启动完成
        - 超时未达标 → 启动失败
        """
        if self._started:
            return ProbeResult(
                success=True,
                message="系统已启动完成",
            )

        elapsed = datetime.now() - self._start_time
        if elapsed > self._timeout:
            return ProbeResult(
                success=False,
                message=f"启动超时 ({self._timeout.total_seconds()}s)",
                details={"elapsed_seconds": elapsed.total_seconds()},
            )

        report = self._checker.check()

        if report.is_healthy:
            self._success_count += 1
            if self._success_count >= self._success_threshold:
                self._started = True
                return ProbeResult(
                    success=True,
                    message="启动完成",
                    details={"elapsed_seconds": elapsed.total_seconds()},
                )
            return ProbeResult(
                success=True,
                message=f"启动中... ({self._success_count}/{self._success_threshold})",
                details={"success_count": self._success_count},
            )
        else:
            return ProbeResult(
                success=False,
                message=f"启动检查未通过: {report.overall_status.value}",
                details={
                    "elapsed_seconds": elapsed.total_seconds(),
                    "remaining_seconds": (self._timeout - elapsed).total_seconds(),
                },
            )

    @property
    def is_started(self) -> bool:
        """是否已完成启动."""
        return self._started
