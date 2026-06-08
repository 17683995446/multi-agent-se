"""重试策略 - 第51阶段.

实现任务失败自动重试策略：
- 指数退避
- 熔断器模式
- 自定义重试策略
"""

import time
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, Tuple


class CircuitState(Enum):
    """熔断器状态."""
    CLOSED = "closed"       # 关闭（正常通过）
    OPEN = "open"           # 打开（拒绝请求）
    HALF_OPEN = "half_open" # 半开（试探性通过）


@dataclass
class RetryPolicy:
    """重试策略配置."""
    max_retries: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = field(default_factory=lambda: (Exception,))

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """判断是否应重试."""
        if attempt >= self.max_retries:
            return False
        return isinstance(exception, self.retryable_exceptions)

    def get_delay(self, attempt: int) -> float:
        """获取第attempt次重试的延迟."""
        delay = self.base_delay_seconds * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay_seconds)
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)
        return delay


class ExponentialBackoff:
    """指数退避执行器.

    包装函数调用，失败时自动重试。
    """

    def __init__(self, policy: Optional[RetryPolicy] = None) -> None:
        self._policy = policy or RetryPolicy()
        self._attempt_history: Dict[str, int] = {}

    def execute(
        self,
        func: Callable[..., Any],
        *args,
        task_id: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """执行函数，失败时自动重试.

        Args:
            func: 要执行的函数
            *args: 位置参数
            task_id: 任务ID（用于追踪）
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            最后一次异常
        """
        task_key = task_id or f"{func.__name__}_{id(func)}"
        last_exception: Optional[Exception] = None

        for attempt in range(self._policy.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                # 成功则重置计数
                self._attempt_history[task_key] = 0
                return result
            except Exception as e:
                last_exception = e
                if not self._policy.should_retry(e, attempt):
                    break

                if attempt < self._policy.max_retries:
                    delay = self._policy.get_delay(attempt)
                    time.sleep(delay)

        # 全部失败
        self._attempt_history[task_key] = self._attempt_history.get(task_key, 0) + 1
        raise last_exception

    def get_attempt_count(self, task_id: str) -> int:
        """获取任务尝试次数."""
        return self._attempt_history.get(task_id, 0)


class CircuitBreaker:
    """熔断器.

    防止故障扩散，当失败率达到阈值时拒绝请求。
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        half_open_max_calls: int = 3,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        self._half_open_max = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """当前状态."""
        if self._state == CircuitState.OPEN:
            # 检查是否已过恢复期
            if self._last_failure_time:
                elapsed = datetime.now() - self._last_failure_time
                if elapsed > self._recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
        return self._state

    def can_execute(self) -> bool:
        """检查是否可以执行请求."""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.OPEN:
            return False
        elif state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self._half_open_max
        return False

    def record_success(self) -> None:
        """记录成功."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self._half_open_max:
                self._reset()
        else:
            self._failure_count = 0

    def record_failure(self) -> None:
        """记录失败."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
        elif self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN

    def execute(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """执行函数（带熔断保护）.

        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数

        Returns:
            函数返回值

        Raises:
            CircuitBreakerOpenError: 熔断器打开
            原函数异常
        """
        if not self.can_execute():
            raise CircuitBreakerOpenError("熔断器打开，请求被拒绝")

        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise

    def _reset(self) -> None:
        """重置熔断器."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息."""
        return {
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self._failure_threshold,
            "recovery_timeout_seconds": self._recovery_timeout.total_seconds(),
        }


class CircuitBreakerOpenError(Exception):
    """熔断器打开错误."""
    pass
