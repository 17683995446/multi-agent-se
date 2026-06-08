"""故障恢复管理器 - 第51阶段.

实现Agent异常自动重启、消息总线断线重连等恢复机制。
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class RecoveryStrategy(Enum):
    """恢复策略."""
    RESTART = "restart"           # 重启
    RECREATE = "recreate"         # 重新创建
    FAILOVER = "failover"         # 故障转移
    IGNORE = "ignore"             # 忽略
    ESCALATE = "escalate"         # 升级告警


@dataclass
class RecoveryResult:
    """恢复结果."""
    success: bool
    strategy: RecoveryStrategy
    target_id: str
    message: str
    attempts: int = 1
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RecoveryManager:
    """故障恢复管理器.

    统一管理所有组件的故障恢复：
    - Agent异常自动重启
    - 消息总线断线重连
    - 任务失败恢复
    - 级联故障隔离
    """

    def __init__(
        self,
        max_recovery_attempts: int = 3,
        recovery_cooldown_seconds: float = 5.0,
    ) -> None:
        self._max_attempts = max_recovery_attempts
        self._cooldown = recovery_cooldown_seconds

        # 恢复历史
        self._recovery_history: List[RecoveryResult] = []
        self._failure_counts: Dict[str, int] = {}
        self._last_recovery: Dict[str, datetime] = {}

        # 恢复处理器注册
        self._handlers: Dict[str, Callable[[str, RecoveryStrategy], RecoveryResult]] = {}

    def register_handler(
        self,
        component_type: str,
        handler: Callable[[str, RecoveryStrategy], RecoveryResult],
    ) -> None:
        """注册恢复处理器.

        Args:
            component_type: 组件类型（如 'agent', 'bus', 'task'）
            handler: 恢复处理函数(target_id, strategy) -> RecoveryResult
        """
        self._handlers[component_type] = handler

    def recover(
        self,
        component_type: str,
        target_id: str,
        strategy: Optional[RecoveryStrategy] = None,
    ) -> RecoveryResult:
        """执行故障恢复.

        Args:
            component_type: 组件类型
            target_id: 目标ID
            strategy: 恢复策略（None则自动选择）

        Returns:
            RecoveryResult
        """
        start = time.perf_counter()

        # 检查冷却期
        last = self._last_recovery.get(target_id)
        if last:
            elapsed = (datetime.now() - last).total_seconds()
            if elapsed < self._cooldown:
                return RecoveryResult(
                    success=False,
                    strategy=strategy or RecoveryStrategy.IGNORE,
                    target_id=target_id,
                    message=f"冷却期中，还需等待 {self._cooldown - elapsed:.1f} 秒",
                )

        # 检查重试次数
        failures = self._failure_counts.get(target_id, 0)
        if failures >= self._max_attempts:
            return RecoveryResult(
                success=False,
                strategy=RecoveryStrategy.ESCALATE,
                target_id=target_id,
                message=f"超过最大恢复次数 {self._max_attempts}，需要人工介入",
                attempts=failures,
            )

        # 自动选择策略
        if strategy is None:
            strategy = self._select_strategy(component_type, target_id)

        # 执行恢复
        handler = self._handlers.get(component_type)
        if handler:
            try:
                result = handler(target_id, strategy)
            except Exception as e:
                result = RecoveryResult(
                    success=False,
                    strategy=strategy,
                    target_id=target_id,
                    message=f"恢复处理异常: {e}",
                    attempts=failures + 1,
                )
        else:
            # 默认恢复逻辑
            result = self._default_recovery(component_type, target_id, strategy)

        result.duration_ms = (time.perf_counter() - start) * 1000
        result.attempts = failures + 1

        # 更新状态
        self._last_recovery[target_id] = datetime.now()
        if result.success:
            self._failure_counts[target_id] = 0
        else:
            self._failure_counts[target_id] = failures + 1

        self._recovery_history.append(result)
        return result

    def _select_strategy(self, component_type: str, target_id: str) -> RecoveryStrategy:
        """自动选择恢复策略."""
        failures = self._failure_counts.get(target_id, 0)

        if failures == 0:
            return RecoveryStrategy.RESTART
        elif failures == 1:
            return RecoveryStrategy.RECREATE
        elif failures == 2:
            return RecoveryStrategy.FAILOVER
        else:
            return RecoveryStrategy.ESCALATE

    def _default_recovery(
        self,
        component_type: str,
        target_id: str,
        strategy: RecoveryStrategy,
    ) -> RecoveryResult:
        """默认恢复逻辑."""
        if strategy == RecoveryStrategy.RESTART:
            return RecoveryResult(
                success=True,
                strategy=strategy,
                target_id=target_id,
                message=f"{component_type} {target_id} 已重启",
            )
        elif strategy == RecoveryStrategy.RECREATE:
            return RecoveryResult(
                success=True,
                strategy=strategy,
                target_id=target_id,
                message=f"{component_type} {target_id} 已重新创建",
            )
        elif strategy == RecoveryStrategy.FAILOVER:
            return RecoveryResult(
                success=True,
                strategy=strategy,
                target_id=target_id,
                message=f"{component_type} {target_id} 已故障转移",
            )
        elif strategy == RecoveryStrategy.IGNORE:
            return RecoveryResult(
                success=True,
                strategy=strategy,
                target_id=target_id,
                message=f"忽略 {component_type} {target_id} 的故障",
            )
        else:
            return RecoveryResult(
                success=False,
                strategy=strategy,
                target_id=target_id,
                message=f"无法处理 {component_type} {target_id} 的故障",
            )

    def record_failure(self, target_id: str) -> None:
        """记录故障（用于触发恢复）."""
        self._failure_counts[target_id] = self._failure_counts.get(target_id, 0) + 1

    def reset_failure_count(self, target_id: str) -> None:
        """重置故障计数."""
        self._failure_counts[target_id] = 0

    def get_failure_count(self, target_id: str) -> int:
        """获取故障计数."""
        return self._failure_counts.get(target_id, 0)

    def get_recovery_history(self, target_id: Optional[str] = None) -> List[RecoveryResult]:
        """获取恢复历史."""
        if target_id:
            return [r for r in self._recovery_history if r.target_id == target_id]
        return self._recovery_history.copy()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息."""
        total = len(self._recovery_history)
        successful = sum(1 for r in self._recovery_history if r.success)
        return {
            "total_recoveries": total,
            "successful_recoveries": successful,
            "failed_recoveries": total - successful,
            "active_failure_counts": dict(self._failure_counts),
        }
