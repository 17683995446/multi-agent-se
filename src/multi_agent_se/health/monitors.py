"""组件监控器 - 第50阶段.

提供各组件的具体健康检查实现：
- AgentHeartbeatMonitor: Agent心跳检测
- MessageBusMonitor: 消息总线健康度
- PoolLoadMonitor: 实例池负载监控
- ConfigMonitor: 配置热加载检测
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from multi_agent_se.health.checker import ComponentHealth, HealthStatus


@dataclass
class HeartbeatRecord:
    """心跳记录."""
    agent_id: str
    timestamp: datetime
    status: str = "ok"
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentHeartbeatMonitor:
    """Agent心跳监控器.

    追踪Agent的心跳信号，检测失联Agent。
    """

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self._timeout = timedelta(seconds=timeout_seconds)
        self._heartbeats: Dict[str, HeartbeatRecord] = {}
        self._expected_agents: Set[str] = set()

    def register_agent(self, agent_id: str) -> None:
        """注册预期Agent."""
        self._expected_agents.add(agent_id)

    def unregister_agent(self, agent_id: str) -> None:
        """注销Agent."""
        self._expected_agents.discard(agent_id)
        self._heartbeats.pop(agent_id, None)

    def heartbeat(self, agent_id: str, status: str = "ok", metadata: Optional[Dict[str, Any]] = None) -> None:
        """记录心跳.

        Args:
            agent_id: Agent ID
            status: 状态标识
            metadata: 附加信息
        """
        self._heartbeats[agent_id] = HeartbeatRecord(
            agent_id=agent_id,
            timestamp=datetime.now(),
            status=status,
            metadata=metadata or {},
        )

    def check(self) -> ComponentHealth:
        """执行健康检查.

        Returns:
            ComponentHealth
        """
        now = datetime.now()
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        missing_agents: List[str] = []
        stale_agents: List[str] = []

        for agent_id in self._expected_agents:
            record = self._heartbeats.get(agent_id)
            if record is None:
                missing_agents.append(agent_id)
                unhealthy_count += 1
                continue

            elapsed = now - record.timestamp
            if elapsed > self._timeout:
                stale_agents.append(agent_id)
                unhealthy_count += 1
            elif elapsed > self._timeout * 0.5:
                degraded_count += 1
            else:
                healthy_count += 1

        total = len(self._expected_agents)
        if total == 0:
            status = HealthStatus.UNKNOWN
            message = "无注册Agent"
        elif unhealthy_count > 0:
            status = HealthStatus.UNHEALTHY
            message = f"{unhealthy_count}/{total} Agent失联: missing={missing_agents}, stale={stale_agents}"
        elif degraded_count > 0:
            status = HealthStatus.DEGRADED
            message = f"{degraded_count}/{total} Agent心跳延迟"
        else:
            status = HealthStatus.HEALTHY
            message = f"全部 {total} 个Agent心跳正常"

        return ComponentHealth(
            name="agent_heartbeat",
            status=status,
            message=message,
            metrics={
                "total_agents": total,
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "timeout_seconds": self._timeout.total_seconds(),
            },
            details={
                "missing_agents": missing_agents,
                "stale_agents": stale_agents,
            },
        )


class MessageBusMonitor:
    """消息总线监控器.

    监控消息总线的队列状态、吞吐量和错误率。
    """

    def __init__(
        self,
        max_queue_size: int = 10000,
        max_error_rate: float = 0.05,
    ) -> None:
        self._max_queue_size = max_queue_size
        self._max_error_rate = max_error_rate
        self._bus: Optional[Any] = None

    def attach(self, bus: Any) -> None:
        """附加到消息总线实例."""
        self._bus = bus

    def check(self) -> ComponentHealth:
        """执行健康检查."""
        if self._bus is None:
            return ComponentHealth(
                name="message_bus",
                status=HealthStatus.UNKNOWN,
                message="未附加消息总线",
            )

        try:
            stats = self._bus.get_stats()
            queue_size = self._bus.get_queue_size()

            total_sent = getattr(stats, 'total_sent', 0)
            total_failed = getattr(stats, 'total_failed', 0)
            total_delivered = getattr(stats, 'total_delivered', 0)

            error_rate = total_failed / max(total_sent, 1)
            delivery_rate = total_delivered / max(total_sent, 1)

            metrics = {
                "queue_size": queue_size,
                "total_sent": total_sent,
                "total_delivered": total_delivered,
                "total_failed": total_failed,
                "error_rate": round(error_rate, 4),
                "delivery_rate": round(delivery_rate, 4),
            }

            if error_rate > self._max_error_rate:
                status = HealthStatus.UNHEALTHY
                message = f"错误率过高: {error_rate:.2%} (阈值: {self._max_error_rate:.2%})"
            elif queue_size > self._max_queue_size:
                status = HealthStatus.DEGRADED
                message = f"队列积压: {queue_size} (阈值: {self._max_queue_size})"
            elif error_rate > self._max_error_rate * 0.5:
                status = HealthStatus.DEGRADED
                message = f"错误率上升: {error_rate:.2%}"
            else:
                status = HealthStatus.HEALTHY
                message = f"消息总线正常, 投递率: {delivery_rate:.2%}"

            return ComponentHealth(
                name="message_bus",
                status=status,
                message=message,
                metrics=metrics,
            )
        except Exception as e:
            return ComponentHealth(
                name="message_bus",
                status=HealthStatus.UNHEALTHY,
                message=f"检查异常: {e}",
            )


class PoolLoadMonitor:
    """实例池负载监控器.

    监控实例池的负载情况和资源使用。
    """

    def __init__(
        self,
        max_load_ratio: float = 0.8,
        max_idle_ratio: float = 0.5,
    ) -> None:
        self._max_load_ratio = max_load_ratio
        self._max_idle_ratio = max_idle_ratio
        self._pool: Optional[Any] = None

    def attach(self, pool: Any) -> None:
        """附加到实例池."""
        self._pool = pool

    def check(self) -> ComponentHealth:
        """执行健康检查."""
        if self._pool is None:
            return ComponentHealth(
                name="agent_pool",
                status=HealthStatus.UNKNOWN,
                message="未附加实例池",
            )

        try:
            stats = self._pool.get_stats()
            total = getattr(stats, 'total_instances', 0)
            active = getattr(stats, 'active_instances', 0)
            idle = getattr(stats, 'idle_instances', 0)
            max_instances = getattr(self._pool, '_config', None)
            max_cap = max_instances.max_instances if max_instances else 100

            load_ratio = active / max(max_cap, 1)
            idle_ratio = idle / max(total, 1) if total > 0 else 0

            metrics = {
                "total_instances": total,
                "active_instances": active,
                "idle_instances": idle,
                "max_capacity": max_cap,
                "load_ratio": round(load_ratio, 4),
                "idle_ratio": round(idle_ratio, 4),
            }

            if load_ratio > self._max_load_ratio:
                status = HealthStatus.DEGRADED
                message = f"负载过高: {load_ratio:.1%} (阈值: {self._max_load_ratio:.1%})"
            elif idle_ratio > self._max_idle_ratio and total > 10:
                status = HealthStatus.DEGRADED
                message = f"空闲实例过多: {idle_ratio:.1%}"
            else:
                status = HealthStatus.HEALTHY
                message = f"实例池正常: {active}活跃/{total}总计"

            return ComponentHealth(
                name="agent_pool",
                status=status,
                message=message,
                metrics=metrics,
            )
        except Exception as e:
            return ComponentHealth(
                name="agent_pool",
                status=HealthStatus.UNHEALTHY,
                message=f"检查异常: {e}",
            )


class ConfigMonitor:
    """配置监控器.

    检测配置变更和配置有效性。
    """

    def __init__(self) -> None:
        self._last_config_hash: Optional[str] = None
        self._check_count = 0

    def _get_config_hash(self) -> str:
        """获取当前配置哈希（简化实现）."""
        try:
            from multi_agent_se.core.config import settings
            # 基于关键配置项生成简单哈希标识
            key = f"{settings.app_env}:{settings.log_level}:{getattr(settings, 'autogen_timeout', 60)}"
            return key
        except Exception:
            return "unknown"

    def check(self) -> ComponentHealth:
        """执行健康检查."""
        try:
            from multi_agent_se.core.config import settings

            current_hash = self._get_config_hash()
            changed = (self._last_config_hash is not None and
                      self._last_config_hash != current_hash)
            self._last_config_hash = current_hash
            self._check_count += 1

            # 基本有效性检查
            env = getattr(settings, 'app_env', 'unknown')
            log_level = getattr(settings, 'log_level', 'unknown')

            metrics = {
                "app_env": env,
                "log_level": log_level,
                "config_changed": changed,
                "check_count": self._check_count,
            }

            if env not in ('development', 'production', 'testing'):
                status = HealthStatus.UNHEALTHY
                message = f"无效的环境配置: {env}"
            elif log_level not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
                status = HealthStatus.DEGRADED
                message = f"非标准日志级别: {log_level}"
            elif changed:
                status = HealthStatus.DEGRADED
                message = "配置已变更，建议重启"
            else:
                status = HealthStatus.HEALTHY
                message = f"配置正常 ({env}, {log_level})"

            return ComponentHealth(
                name="configuration",
                status=status,
                message=message,
                metrics=metrics,
            )
        except Exception as e:
            return ComponentHealth(
                name="configuration",
                status=HealthStatus.UNHEALTHY,
                message=f"配置检查异常: {e}",
            )
