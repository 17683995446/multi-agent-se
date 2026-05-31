"""状态机与三层状态管理 - 阶段13.

实现任务状态、业务状态、系统状态三层隔离：
1. 状态转换规则明确（状态机）
2. 三层状态定义清晰（SystemState/TaskState/BusinessState）
3. 状态隔离验证通过（LayerStateManager隔离检查）
4. 状态同步机制可用（StateSynchronizer同步协调）
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from datetime import datetime
import uuid

from multi_agent_se.collaboration.state import (
    SystemState, TaskState, BusinessState,
    TaskStatus, AgentRole, GraphState,
    create_initial_state, update_state,
)
from multi_agent_se.core.exceptions import SchedulerError


# ========== 状态层类型 ==========
class StateLayer(Enum):
    """状态层级."""
    SYSTEM = "system"      # 系统层 - 全局运行时状态
    TASK = "task"          # 任务层 - 任务执行状态
    BUSINESS = "business"  # 业务层 - 业务数据状态


# ========== 状态转换规则 ==========
class StateTransition(Enum):
    """任务状态转换规则."""
    # 正常流程
    START = (TaskStatus.PENDING, TaskStatus.RUNNING)
    COMPLETE = (TaskStatus.RUNNING, TaskStatus.COMPLETED)
    FAIL = (TaskStatus.RUNNING, TaskStatus.FAILED)
    CANCEL = (TaskStatus.PENDING, TaskStatus.CANCELLED)
    CANCEL_RUNNING = (TaskStatus.RUNNING, TaskStatus.CANCELLED)
    
    # 重试流程
    RETRY = (TaskStatus.FAILED, TaskStatus.PENDING)
    
    def __init__(self, from_status: TaskStatus, to_status: TaskStatus) -> None:
        self.from_status = from_status
        self.to_status = to_status


# 有效转换映射
VALID_TRANSITIONS: Dict[TaskStatus, Set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
    TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
    TaskStatus.COMPLETED: set(),  # 终态
    TaskStatus.FAILED: {TaskStatus.PENDING},  # 可重试
    TaskStatus.CANCELLED: set(),  # 终态
}


@dataclass
class TransitionResult:
    """状态转换结果."""
    success: bool
    from_status: TaskStatus
    to_status: TaskStatus
    message: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "from_status": self.from_status.value,
            "to_status": self.to_status.value,
            "message": self.message,
            "timestamp": self.timestamp,
        }


class TaskStateMachine:
    """任务状态机.
    
    管理任务状态的转换规则与验证
    """
    
    def __init__(self) -> None:
        """初始化状态机."""
        self._transitions: Dict[Tuple[TaskStatus, TaskStatus], str] = {
            (TaskStatus.PENDING, TaskStatus.RUNNING): "start",
            (TaskStatus.RUNNING, TaskStatus.COMPLETED): "complete",
            (TaskStatus.RUNNING, TaskStatus.FAILED): "fail",
            (TaskStatus.PENDING, TaskStatus.CANCELLED): "cancel",
            (TaskStatus.RUNNING, TaskStatus.CANCELLED): "cancel_running",
            (TaskStatus.FAILED, TaskStatus.PENDING): "retry",
        }
        self._hooks: Dict[TaskStatus, List[Callable[[TaskState], None]]] = {
            status: [] for status in TaskStatus
        }
    
    def can_transition(self, from_status: TaskStatus, to_status: TaskStatus) -> bool:
        """检查转换是否合法.
        
        Args:
            from_status: 源状态
            to_status: 目标状态
            
        Returns:
            True如果转换合法
        """
        if from_status == to_status:
            return True  # 允许自转换
        return to_status in VALID_TRANSITIONS.get(from_status, set())
    
    def transition(
        self,
        task_state: TaskState,
        to_status: TaskStatus,
        validate: bool = True,
    ) -> TransitionResult:
        """执行状态转换.
        
        Args:
            task_state: 任务状态
            to_status: 目标状态
            validate: 是否验证转换合法性
            
        Returns:
            TransitionResult
        """
        from_status = task_state.status
        
        if validate and not self.can_transition(from_status, to_status):
            return TransitionResult(
                success=False,
                from_status=from_status,
                to_status=to_status,
                message=f"非法状态转换: {from_status.value} -> {to_status.value}",
            )
        
        # 执行转换
        task_state.status = to_status
        
        # 执行钩子
        for hook in self._hooks.get(to_status, []):
            hook(task_state)
        
        return TransitionResult(
            success=True,
            from_status=from_status,
            to_status=to_status,
            message=f"状态转换成功: {from_status.value} -> {to_status.value}",
        )
    
    def register_hook(
        self,
        status: TaskStatus,
        hook: Callable[[TaskState], None],
    ) -> None:
        """注册状态进入钩子.
        
        Args:
            status: 目标状态
            hook: 钩子函数
        """
        self._hooks[status].append(hook)
    
    def get_valid_transitions(self, status: TaskStatus) -> Set[TaskStatus]:
        """获取从当前状态可转换的所有状态.
        
        Args:
            status: 当前状态
            
        Returns:
            可转换状态集合
        """
        return VALID_TRANSITIONS.get(status, set()).copy()
    
    def get_transition_graph(self) -> Dict[str, List[str]]:
        """获取状态转换图.
        
        Returns:
            {状态名: [可转换状态名列表]}
        """
        return {
            status.value: [s.value for s in targets]
            for status, targets in VALID_TRANSITIONS.items()
        }


# ========== 三层状态管理器 ==========
@dataclass
class StateAccessRecord:
    """状态访问记录."""
    layer: StateLayer
    operation: str  # read / write
    field: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    caller: str = ""


class LayerStateManager:
    """分层状态管理器基类.
    
    实现三层状态隔离：
    - 系统层管理器：只管理系统状态
    - 任务层管理器：只管理任务状态
    - 业务层管理器：只管理业务状态
    """
    
    def __init__(self, layer: StateLayer) -> None:
        """初始化管理器.
        
        Args:
            layer: 管理的层级
        """
        self._layer = layer
        self._access_log: List[StateAccessRecord] = []
        self._isolation_enabled = True
    
    @property
    def layer(self) -> StateLayer:
        """获取管理的层级."""
        return self._layer
    
    def _check_isolation(self, target_layer: StateLayer, operation: str) -> None:
        """检查隔离规则.
        
        Args:
            target_layer: 目标层级
            operation: 操作类型
            
        Raises:
            SchedulerError: 违反隔离规则
        """
        if self._isolation_enabled and target_layer != self._layer:
            raise SchedulerError(
                message=f"状态隔离违规: {self._layer.value}层管理器不能{operation}{target_layer.value}层状态",
                details={
                    "manager_layer": self._layer.value,
                    "target_layer": target_layer.value,
                    "operation": operation,
                },
            )
    
    def _log_access(self, field: str, operation: str, caller: str = "") -> None:
        """记录访问日志."""
        self._access_log.append(StateAccessRecord(
            layer=self._layer,
            operation=operation,
            field=field,
            caller=caller,
        ))
    
    def get_access_log(self) -> List[StateAccessRecord]:
        """获取访问日志."""
        return list(self._access_log)
    
    def clear_access_log(self) -> None:
        """清空访问日志."""
        self._access_log.clear()
    
    def set_isolation(self, enabled: bool) -> None:
        """设置隔离开关.
        
        Args:
            enabled: 是否启用隔离
        """
        self._isolation_enabled = enabled


class SystemStateManager(LayerStateManager):
    """系统状态管理器."""
    
    def __init__(self) -> None:
        """初始化系统状态管理器."""
        super().__init__(StateLayer.SYSTEM)
        self._state: Optional[SystemState] = None
    
    def create(self, session_id: Optional[str] = None, env: str = "development") -> SystemState:
        """创建系统状态.
        
        Args:
            session_id: 会话ID（None则自动生成）
            env: 运行环境
            
        Returns:
            SystemState
        """
        self._check_isolation(StateLayer.SYSTEM, "创建")
        self._state = SystemState(
            session_id=session_id or str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            env=env,
        )
        self._log_access("system_state", "write", "create")
        return self._state
    
    def get(self) -> Optional[SystemState]:
        """获取系统状态."""
        self._check_isolation(StateLayer.SYSTEM, "读取")
        self._log_access("system_state", "read", "get")
        return self._state
    
    def update(self, **kwargs: Any) -> SystemState:
        """更新系统状态.
        
        Args:
            **kwargs: 更新字段
            
        Returns:
            更新后的状态
            
        Raises:
            SchedulerError: 状态未创建
        """
        self._check_isolation(StateLayer.SYSTEM, "更新")
        if self._state is None:
            raise SchedulerError(message="系统状态未创建")
        
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
                self._log_access(key, "write", "update")
        
        return self._state


class TaskStateManager(LayerStateManager):
    """任务状态管理器."""
    
    def __init__(self) -> None:
        """初始化任务状态管理器."""
        super().__init__(StateLayer.TASK)
        self._state: Optional[TaskState] = None
        self._state_machine = TaskStateMachine()
    
    def create(
        self,
        task_type: str = "default",
        priority: int = 0,
    ) -> TaskState:
        """创建任务状态.
        
        Args:
            task_type: 任务类型
            priority: 优先级
            
        Returns:
            TaskState
        """
        self._check_isolation(StateLayer.TASK, "创建")
        self._state = TaskState(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            status=TaskStatus.PENDING,
            priority=priority,
        )
        self._log_access("task_state", "write", "create")
        return self._state
    
    def get(self) -> Optional[TaskState]:
        """获取任务状态."""
        self._check_isolation(StateLayer.TASK, "读取")
        self._log_access("task_state", "read", "get")
        return self._state
    
    def transition(self, to_status: TaskStatus) -> TransitionResult:
        """执行状态转换.
        
        Args:
            to_status: 目标状态
            
        Returns:
            TransitionResult
        """
        self._check_isolation(StateLayer.TASK, "更新")
        if self._state is None:
            return TransitionResult(
                success=False,
                from_status=TaskStatus.PENDING,
                to_status=to_status,
                message="任务状态未创建",
            )
        
        result = self._state_machine.transition(self._state, to_status)
        if result.success:
            self._log_access("status", "write", f"transition_to_{to_status.value}")
        return result
    
    def update_progress(self, progress: float) -> None:
        """更新进度.
        
        Args:
            progress: 进度(0-100)
        """
        self._check_isolation(StateLayer.TASK, "更新")
        if self._state is None:
            raise SchedulerError(message="任务状态未创建")
        
        self._state.progress = max(0.0, min(100.0, progress))
        self._log_access("progress", "write", "update_progress")
    
    def assign_agent(self, agent: AgentRole) -> None:
        """分配Agent.
        
        Args:
            agent: Agent角色
        """
        self._check_isolation(StateLayer.TASK, "更新")
        if self._state is None:
            raise SchedulerError(message="任务状态未创建")
        
        self._state.assigned_agent = agent
        self._log_access("assigned_agent", "write", "assign_agent")
    
    def get_valid_transitions(self) -> Set[TaskStatus]:
        """获取可转换状态."""
        if self._state is None:
            return set()
        return self._state_machine.get_valid_transitions(self._state.status)


class BusinessStateManager(LayerStateManager):
    """业务状态管理器."""
    
    def __init__(self) -> None:
        """初始化业务状态管理器."""
        super().__init__(StateLayer.BUSINESS)
        self._state: Optional[BusinessState] = None
    
    def create(self, input_data: Optional[Dict[str, Any]] = None) -> BusinessState:
        """创建业务状态.
        
        Args:
            input_data: 输入数据
            
        Returns:
            BusinessState
        """
        self._check_isolation(StateLayer.BUSINESS, "创建")
        self._state = BusinessState(
            input_data=input_data or {},
        )
        self._log_access("business_state", "write", "create")
        return self._state
    
    def get(self) -> Optional[BusinessState]:
        """获取业务状态."""
        self._check_isolation(StateLayer.BUSINESS, "读取")
        self._log_access("business_state", "read", "get")
        return self._state
    
    def set_output(self, key: str, value: Any) -> None:
        """设置输出数据.
        
        Args:
            key: 键
            value: 值
        """
        self._check_isolation(StateLayer.BUSINESS, "更新")
        if self._state is None:
            raise SchedulerError(message="业务状态未创建")
        
        self._state.output_data[key] = value
        self._log_access(f"output_data.{key}", "write", "set_output")
    
    def set_context(self, key: str, value: Any) -> None:
        """设置上下文.
        
        Args:
            key: 键
            value: 值
        """
        self._check_isolation(StateLayer.BUSINESS, "更新")
        if self._state is None:
            raise SchedulerError(message="业务状态未创建")
        
        self._state.context[key] = value
        self._log_access(f"context.{key}", "write", "set_context")
    
    def add_artifact(self, artifact: str) -> None:
        """添加产物.
        
        Args:
            artifact: 产物标识
        """
        self._check_isolation(StateLayer.BUSINESS, "更新")
        if self._state is None:
            raise SchedulerError(message="业务状态未创建")
        
        self._state.artifacts.append(artifact)
        self._log_access("artifacts", "write", "add_artifact")
    
    def get_artifacts(self) -> List[str]:
        """获取产物列表."""
        self._check_isolation(StateLayer.BUSINESS, "读取")
        if self._state is None:
            return []
        return list(self._state.artifacts)


# ========== 状态同步器 ==========
@dataclass
class SyncResult:
    """同步结果."""
    success: bool
    synced_layers: List[StateLayer]
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class StateSynchronizer:
    """状态同步器.
    
    协调三层状态间的同步与一致性
    """
    
    def __init__(
        self,
        system_manager: Optional[SystemStateManager] = None,
        task_manager: Optional[TaskStateManager] = None,
        business_manager: Optional[BusinessStateManager] = None,
    ) -> None:
        """初始化同步器.
        
        Args:
            system_manager: 系统状态管理器
            task_manager: 任务状态管理器
            business_manager: 业务状态管理器
        """
        self._system = system_manager or SystemStateManager()
        self._task = task_manager or TaskStateManager()
        self._business = business_manager or BusinessStateManager()
        self._sync_hooks: List[Callable[[StateLayer, str], None]] = []
    
    @property
    def system_manager(self) -> SystemStateManager:
        """获取系统状态管理器."""
        return self._system
    
    @property
    def task_manager(self) -> TaskStateManager:
        """获取任务状态管理器."""
        return self._task
    
    @property
    def business_manager(self) -> BusinessStateManager:
        """获取业务状态管理器."""
        return self._business
    
    def create_all(
        self,
        task_type: str = "default",
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[SystemState, TaskState, BusinessState]:
        """创建三层状态.
        
        Args:
            task_type: 任务类型
            input_data: 输入数据
            
        Returns:
            (SystemState, TaskState, BusinessState)
        """
        system = self._system.create()
        task = self._task.create(task_type=task_type)
        business = self._business.create(input_data=input_data)
        
        # 建立关联
        task.parent_task_id = system.session_id
        
        return system, task, business
    
    def sync_to_graph_state(self) -> GraphState:
        """同步到GraphState（用于LangGraph）.
        
        Returns:
            GraphState
        """
        system = self._system.get()
        task = self._task.get()
        business = self._business.get()
        
        if system is None or task is None or business is None:
            raise SchedulerError(message="三层状态未完全创建")
        
        return {
            # 系统层
            "session_id": system.session_id,
            "trace_id": system.trace_id,
            
            # 任务层
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status.value,
            "priority": task.priority,
            "progress": task.progress,
            "current_stage": task.current_stage,
            "assigned_agent": task.assigned_agent.value if task.assigned_agent else None,
            
            # 业务层
            "input_data": business.input_data,
            "output_data": business.output_data,
            "context": business.context,
            "messages": [],
            "artifacts": business.artifacts,
            
            # 控制流
            "next_stage": None,
            "should_continue": True,
            "error": None,
        }
    
    def sync_from_graph_state(self, graph_state: GraphState) -> SyncResult:
        """从GraphState同步回三层状态.
        
        Args:
            graph_state: LangGraph状态
            
        Returns:
            SyncResult
        """
        errors = []
        synced = []
        
        try:
            # 同步系统层
            system = self._system.get()
            if system:
                system.session_id = graph_state.get("session_id", system.session_id)
                system.trace_id = graph_state.get("trace_id", system.trace_id)
                synced.append(StateLayer.SYSTEM)
        except Exception as e:
            errors.append(f"系统层同步失败: {e}")
        
        try:
            # 同步任务层
            task = self._task.get()
            if task:
                status_str = graph_state.get("status")
                if status_str:
                    task.status = TaskStatus(status_str)
                task.progress = graph_state.get("progress", task.progress)
                task.current_stage = graph_state.get("current_stage", task.current_stage)
                synced.append(StateLayer.TASK)
        except Exception as e:
            errors.append(f"任务层同步失败: {e}")
        
        try:
            # 同步业务层
            business = self._business.get()
            if business:
                business.output_data = graph_state.get("output_data", business.output_data)
                business.context = graph_state.get("context", business.context)
                synced.append(StateLayer.BUSINESS)
        except Exception as e:
            errors.append(f"业务层同步失败: {e}")
        
        return SyncResult(
            success=len(errors) == 0,
            synced_layers=synced,
            errors=errors,
        )
    
    def validate_isolation(self) -> Dict[str, bool]:
        """验证三层状态隔离.
        
        Returns:
            {层名: 是否隔离}
        """
        return {
            "system": self._system.layer == StateLayer.SYSTEM,
            "task": self._task.layer == StateLayer.TASK,
            "business": self._business.layer == StateLayer.BUSINESS,
        }
    
    def get_all_access_logs(self) -> Dict[str, List[StateAccessRecord]]:
        """获取所有层的访问日志.
        
        Returns:
            {层名: 访问日志列表}
        """
        return {
            "system": self._system.get_access_log(),
            "task": self._task.get_access_log(),
            "business": self._business.get_access_log(),
        }
    
    def register_sync_hook(self, hook: Callable[[StateLayer, str], None]) -> None:
        """注册同步钩子.
        
        Args:
            hook: 钩子函数(layer, operation)
        """
        self._sync_hooks.append(hook)
    
    def _notify_sync(self, layer: StateLayer, operation: str) -> None:
        """通知同步钩子."""
        for hook in self._sync_hooks:
            try:
                hook(layer, operation)
            except Exception:
                pass  # 忽略钩子错误
