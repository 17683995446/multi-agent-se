"""Agent生命周期状态机 - 阶段17.

定义Agent生命周期：
- 状态转换规则
- 生命周期事件
- 事件钩子机制
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Type


class LifecycleState(Enum):
    """生命周期状态."""
    CREATED = "created"           # 已创建（未初始化）
    INITIALIZING = "initializing" # 初始化中
    READY = "ready"              # 就绪（可执行任务）
    RUNNING = "running"          # 运行中（正在执行任务）
    PAUSED = "paused"            # 已暂停
    STOPPING = "stopping"        # 停止中
    STOPPED = "stopped"          # 已停止
    ERROR = "error"              # 错误状态
    TERMINATED = "terminated"     # 已终止（不可恢复）


class LifecycleEvent(Enum):
    """生命周期事件."""
    CREATE = "create"             # 创建
    INITIALIZE = "initialize"     # 初始化
    INITIALIZE_SUCCESS = "initialize_success"  # 初始化成功
    INITIALIZE_FAILURE = "initialize_failure"  # 初始化失败
    START = "start"               # 启动
    RUN = "run"                   # 运行
    PAUSE = "pause"               # 暂停
    RESUME = "resume"             # 恢复
    STOP = "stop"                 # 停止
    STOP_SUCCESS = "stop_success"  # 停止成功
    STOP_FAILURE = "stop_failure"  # 停止失败
    ERROR = "error"               # 错误
    RECOVER = "recover"           # 恢复
    TERMINATE = "terminate"       # 终止


class LifecycleTransition(Enum):
    """生命周期转换."""
    # 创建 -> 初始化
    CREATE_TO_INITIALIZING = (LifecycleState.CREATED, LifecycleState.INITIALIZING)
    # 初始化 -> 就绪
    INITIALIZING_TO_READY = (LifecycleState.INITIALIZING, LifecycleState.READY)
    # 初始化 -> 错误
    INITIALIZING_TO_ERROR = (LifecycleState.INITIALIZING, LifecycleState.ERROR)
    # 就绪 -> 运行
    READY_TO_RUNNING = (LifecycleState.READY, LifecycleState.RUNNING)
    # 运行 -> 就绪
    RUNNING_TO_READY = (LifecycleState.RUNNING, LifecycleState.READY)
    # 运行 -> 暂停
    RUNNING_TO_PAUSED = (LifecycleState.RUNNING, LifecycleState.PAUSED)
    # 暂停 -> 运行
    PAUSED_TO_RUNNING = (LifecycleState.PAUSED, LifecycleState.RUNNING)
    # 暂停 -> 停止中
    PAUSED_TO_STOPPING = (LifecycleState.PAUSED, LifecycleState.STOPPING)
    # 就绪 -> 停止中
    READY_TO_STOPPING = (LifecycleState.READY, LifecycleState.STOPPING)
    # 运行 -> 停止中
    RUNNING_TO_STOPPING = (LifecycleState.RUNNING, LifecycleState.STOPPING)
    # 停止中 -> 已停止
    STOPPING_TO_STOPPED = (LifecycleState.STOPPING, LifecycleState.STOPPED)
    # 停止中 -> 错误
    STOPPING_TO_ERROR = (LifecycleState.STOPPING, LifecycleState.ERROR)
    # 已停止 -> 终止
    STOPPED_TO_TERMINATED = (LifecycleState.STOPPED, LifecycleState.TERMINATED)
    # 错误 -> 就绪（恢复）
    ERROR_TO_READY = (LifecycleState.ERROR, LifecycleState.READY)
    # 错误 -> 终止
    ERROR_TO_TERMINATED = (LifecycleState.ERROR, LifecycleState.TERMINATED)
    
    @property
    def from_state(self) -> LifecycleState:
        return self.value[0]
    
    @property
    def to_state(self) -> LifecycleState:
        return self.value[1]


@dataclass
class LifecycleTransitionRecord:
    """生命周期转换记录."""
    from_state: LifecycleState
    to_state: LifecycleState
    event: LifecycleEvent
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "event": self.event.value,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }


class LifecycleStateMachine:
    """生命周期状态机.
    
    管理Agent的生命周期状态转换
    """
    
    # 合法转换映射
    VALID_TRANSITIONS: Dict[LifecycleState, Set[LifecycleState]] = {
        LifecycleState.CREATED: {
            LifecycleState.INITIALIZING,
            LifecycleState.TERMINATED,
        },
        LifecycleState.INITIALIZING: {
            LifecycleState.READY,
            LifecycleState.ERROR,
        },
        LifecycleState.READY: {
            LifecycleState.RUNNING,
            LifecycleState.STOPPING,
            LifecycleState.TERMINATED,
        },
        LifecycleState.RUNNING: {
            LifecycleState.READY,
            LifecycleState.PAUSED,
            LifecycleState.STOPPING,
            LifecycleState.ERROR,
        },
        LifecycleState.PAUSED: {
            LifecycleState.RUNNING,
            LifecycleState.STOPPING,
        },
        LifecycleState.STOPPING: {
            LifecycleState.STOPPED,
            LifecycleState.ERROR,
        },
        LifecycleState.STOPPED: {
            LifecycleState.TERMINATED,
        },
        LifecycleState.ERROR: {
            LifecycleState.READY,  # 恢复
            LifecycleState.TERMINATED,
        },
        LifecycleState.TERMINATED: set(),  # 终止状态不可转换
    }
    
    def __init__(self, initial_state: LifecycleState = LifecycleState.CREATED) -> None:
        """初始化状态机.
        
        Args:
            initial_state: 初始状态
        """
        self._state = initial_state
        self._history: List[LifecycleTransitionRecord] = []
        self._hooks: Dict[LifecycleEvent, List[Callable]] = {
            event: [] for event in LifecycleEvent
        }
    
    @property
    def state(self) -> LifecycleState:
        """当前状态."""
        return self._state
    
    @property
    def history(self) -> List[LifecycleTransitionRecord]:
        """转换历史."""
        return list(self._history)
    
    def can_transition_to(self, target: LifecycleState) -> bool:
        """检查是否可以转换到目标状态.
        
        Args:
            target: 目标状态
            
        Returns:
            是否可以转换
        """
        return target in self.VALID_TRANSITIONS.get(self._state, set())
    
    def transition(
        self,
        event: LifecycleEvent,
        target: Optional[LifecycleState] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LifecycleTransitionRecord:
        """执行状态转换.
        
        Args:
            event: 触发事件
            target: 目标状态（可选，由事件推断）
            metadata: 转换元数据
            
        Returns:
            LifecycleTransitionRecord
            
        Raises:
            ValueError: 如果转换不合法
        """
        # 推断目标状态
        if target is None:
            target = self._infer_target_state(event)
        
        # 验证转换
        if not self.can_transition_to(target):
            record = LifecycleTransitionRecord(
                from_state=self._state,
                to_state=target,
                event=event,
                success=False,
                error=f"Invalid transition: {self._state.value} -> {target.value}",
            )
            self._history.append(record)
            raise ValueError(record.error)
        
        # 执行钩子（转换前）
        self._execute_hooks(event, pre=True)
        
        # 记录转换
        old_state = self._state
        self._state = target
        
        record = LifecycleTransitionRecord(
            from_state=old_state,
            to_state=target,
            event=event,
            success=True,
            metadata=metadata or {},
        )
        self._history.append(record)
        
        # 执行钩子（转换后）
        self._execute_hooks(event, pre=False)
        
        return record
    
    def _infer_target_state(self, event: LifecycleEvent) -> LifecycleState:
        """根据事件推断目标状态."""
        event_to_state = {
            LifecycleEvent.CREATE: LifecycleState.CREATED,
            LifecycleEvent.INITIALIZE: LifecycleState.INITIALIZING,
            LifecycleEvent.INITIALIZE_SUCCESS: LifecycleState.READY,
            LifecycleEvent.INITIALIZE_FAILURE: LifecycleState.ERROR,
            LifecycleEvent.START: LifecycleState.RUNNING,
            LifecycleEvent.RUN: LifecycleState.RUNNING,
            LifecycleEvent.PAUSE: LifecycleState.PAUSED,
            LifecycleEvent.RESUME: LifecycleState.RUNNING,
            LifecycleEvent.STOP: LifecycleState.STOPPING,
            LifecycleEvent.STOP_SUCCESS: LifecycleState.STOPPED,
            LifecycleEvent.STOP_FAILURE: LifecycleState.ERROR,
            LifecycleEvent.ERROR: LifecycleState.ERROR,
            LifecycleEvent.RECOVER: LifecycleState.READY,
            LifecycleEvent.TERMINATE: LifecycleState.TERMINATED,
        }
        return event_to_state.get(event, self._state)
    
    def _execute_hooks(
        self,
        event: LifecycleEvent,
        pre: bool = True,
    ) -> None:
        """执行事件钩子."""
        hooks = self._hooks.get(event, [])
        for hook in hooks:
            try:
                hook(self._state, event, pre)
            except Exception:
                pass  # 钩子异常不影响转换
    
    def add_hook(
        self,
        event: LifecycleEvent,
        hook: Callable[[LifecycleState, LifecycleEvent, bool], None],
    ) -> None:
        """添加事件钩子.
        
        Args:
            event: 事件类型
            hook: 钩子函数 (state, event, is_pre) -> None
        """
        self._hooks[event].append(hook)
    
    def remove_hook(
        self,
        event: LifecycleEvent,
        hook: Callable,
    ) -> bool:
        """移除事件钩子."""
        try:
            self._hooks[event].remove(hook)
            return True
        except ValueError:
            return False
    
    # ========== 便捷方法 ==========
    
    def initialize(self) -> LifecycleTransitionRecord:
        """开始初始化."""
        return self.transition(LifecycleEvent.INITIALIZE)
    
    def initialize_success(self) -> LifecycleTransitionRecord:
        """初始化成功."""
        return self.transition(LifecycleEvent.INITIALIZE_SUCCESS)
    
    def initialize_failure(self, error: str) -> LifecycleTransitionRecord:
        """初始化失败."""
        return self.transition(
            LifecycleEvent.INITIALIZE_FAILURE,
            metadata={"error": error},
        )
    
    def start(self) -> LifecycleTransitionRecord:
        """启动（就绪->运行）."""
        return self.transition(LifecycleEvent.START)
    
    def pause(self) -> LifecycleTransitionRecord:
        """暂停."""
        return self.transition(LifecycleEvent.PAUSE)
    
    def resume(self) -> LifecycleTransitionRecord:
        """恢复."""
        return self.transition(LifecycleEvent.RESUME)
    
    def stop(self) -> LifecycleTransitionRecord:
        """停止."""
        return self.transition(LifecycleEvent.STOP)
    
    def stop_success(self) -> LifecycleTransitionRecord:
        """停止成功."""
        return self.transition(LifecycleEvent.STOP_SUCCESS)
    
    def terminate(self) -> LifecycleTransitionRecord:
        """终止."""
        return self.transition(LifecycleEvent.TERMINATE)
    
    def recover(self) -> LifecycleTransitionRecord:
        """从错误恢复."""
        return self.transition(LifecycleEvent.RECOVER)
    
    def error(self, error_msg: str) -> LifecycleTransitionRecord:
        """进入错误状态."""
        return self.transition(
            LifecycleEvent.ERROR,
            metadata={"error": error_msg},
        )
    
    # ========== 状态检查 ==========
    
    @property
    def is_created(self) -> bool:
        return self._state == LifecycleState.CREATED
    
    @property
    def is_ready(self) -> bool:
        return self._state == LifecycleState.READY
    
    @property
    def is_running(self) -> bool:
        return self._state == LifecycleState.RUNNING
    
    @property
    def is_paused(self) -> bool:
        return self._state == LifecycleState.PAUSED
    
    @property
    def is_stopped(self) -> bool:
        return self._state == LifecycleState.STOPPED
    
    @property
    def is_error(self) -> bool:
        return self._state == LifecycleState.ERROR
    
    @property
    def is_terminated(self) -> bool:
        return self._state == LifecycleState.TERMINATED
    
    @property
    def is_active(self) -> bool:
        """是否活跃（可以执行任务）."""
        return self._state in (LifecycleState.READY, LifecycleState.RUNNING)
    
    @property
    def is_recoverable(self) -> bool:
        """是否可恢复."""
        return self._state != LifecycleState.TERMINATED


# ========== 事件钩子接口 ==========

class LifecycleHook(ABC):
    """生命周期钩子接口."""
    
    @abstractmethod
    def on_event(
        self,
        state: LifecycleState,
        event: LifecycleEvent,
        is_pre: bool,
    ) -> None:
        """事件回调."""
        ...


class LoggingHook(LifecycleHook):
    """日志记录钩子."""
    
    def __init__(self, logger: Optional[Any] = None) -> None:
        self._logger = logger
    
    def on_event(
        self,
        state: LifecycleState,
        event: LifecycleEvent,
        is_pre: bool,
    ) -> None:
        phase = "PRE" if is_pre else "POST"
        msg = f"[{phase}] Lifecycle event: {event.value}, state: {state.value}"
        if self._logger:
            self._logger.info(msg)
        else:
            print(msg)


class MetricsHook(LifecycleHook):
    """指标收集钩子."""
    
    def __init__(self) -> None:
        self._event_counts: Dict[LifecycleEvent, int] = {
            event: 0 for event in LifecycleEvent
        }
    
    def on_event(
        self,
        state: LifecycleState,
        event: LifecycleEvent,
        is_pre: bool,
    ) -> None:
        if not is_pre:  # 只记录后置事件
            self._event_counts[event] += 1
    
    def get_counts(self) -> Dict[str, int]:
        return {e.value: c for e, c in self._event_counts.items()}
