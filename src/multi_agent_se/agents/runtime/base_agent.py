"""基础Agent实现 - 阶段20.

提供所有Agent的基类实现：
- 统一的execute接口
- 消息收发能力
- 任务处理能力
- 生命周期集成
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from multi_agent_se.agents.registry import (
    AgentRole,
    AgentStatus,
    AgentCapability,
    AgentMetadata,
    AgentCapabilityDeclaration,
)
from multi_agent_se.agents.communication import (
    Message,
    MessageType,
    MessagePriority,
    MessageBus,
    get_message_bus,
)
from multi_agent_se.agents.lifecycle import (
    LifecycleState,
    LifecycleEvent,
    LifecycleTransitionRecord,
)
from multi_agent_se.scheduler import (
    Task,
    TaskType,
    TaskResult,
    TaskStatus,
)


class AgentExecutionError(Exception):
    """Agent执行错误."""
    pass


@dataclass
class AgentContext:
    """Agent执行上下文."""
    task: Optional[Task] = None
    message: Optional[Message] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task.task_id if self.task else None,
            "message_id": self.message.message_id if self.message else None,
            "input_data": self.input_data,
            "metadata": self.metadata,
        }


class BaseAgentImpl(ABC):
    """基础Agent实现.
    
    所有8个正交角色的Agent都继承此类
    """
    
    # 子类必须定义
    AGENT_ROLE: AgentRole = AgentRole.CONTROLLER
    AGENT_CAPABILITIES: List[AgentCapability] = []
    AGENT_DESCRIPTION: str = ""
    
    def __init__(
        self,
        agent_id: str,
        name: str = "",
        message_bus: Optional[MessageBus] = None,
    ) -> None:
        """初始化Agent.
        
        Args:
            agent_id: Agent ID
            name: 名称
            message_bus: 消息总线
        """
        self._agent_id = agent_id
        self._name = name or f"{self.AGENT_ROLE.value.capitalize()}Agent"
        self._message_bus = message_bus or get_message_bus()
        
        # 状态
        self._status = AgentStatus.CREATED
        self._total_tasks = 0
        self._successful_tasks = 0
        self._failed_tasks = 0
        
        # 状态转换历史
        self._transition_history: List[LifecycleTransitionRecord] = []
        self._record_transition(AgentStatus.CREATED, AgentStatus.CREATED, "init")
        
        # 消息处理
        self._message_handlers: Dict[MessageType, Callable] = {}
        self._register_default_handlers()
    
    def _record_transition(self, from_status: AgentStatus, to_status: AgentStatus, reason: str = "", success: bool = True, error: Optional[str] = None) -> None:
        """记录状态转换."""
        record = LifecycleTransitionRecord(
            from_state=LifecycleState(from_status.value),
            to_state=LifecycleState(to_status.value),
            event=LifecycleEvent.RECOVER if to_status == AgentStatus.READY else LifecycleEvent.ERROR if to_status == AgentStatus.ERROR else LifecycleEvent.RUN,
            success=success,
            error=error,
            metadata={"reason": reason, "agent_id": self._agent_id},
        )
        self._transition_history.append(record)
    
    # ========== 属性 ==========
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def role(self) -> AgentRole:
        return self.AGENT_ROLE
    
    @property
    def status(self) -> AgentStatus:
        return self._status
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        return self.AGENT_CAPABILITIES
    
    @property
    def success_rate(self) -> float:
        if self._total_tasks == 0:
            return 0.0
        return self._successful_tasks / self._total_tasks
    
    @property
    def is_available(self) -> bool:
        return self._status in (AgentStatus.READY, AgentStatus.RUNNING)
    
    # ========== 生命周期 ==========
    
    def initialize(self) -> None:
        """初始化Agent."""
        old_status = self._status
        self._status = AgentStatus.READY
        self._record_transition(old_status, self._status, "initialize")
        self.on_initialize()
    
    def on_initialize(self) -> None:
        """初始化钩子（子类可覆盖）."""
        pass
    
    def start(self) -> None:
        """启动Agent."""
        if self._status not in (AgentStatus.READY, AgentStatus.PAUSED):
            raise AgentExecutionError(f"Cannot start agent in {self._status.value} state")
        old_status = self._status
        self._status = AgentStatus.RUNNING
        self._record_transition(old_status, self._status, "start")
        self.on_start()
    
    def on_start(self) -> None:
        """启动钩子（子类可覆盖）."""
        pass
    
    def pause(self) -> None:
        """暂停Agent."""
        if self._status != AgentStatus.RUNNING:
            return
        old_status = self._status
        self._status = AgentStatus.PAUSED
        self._record_transition(old_status, self._status, "pause")
        self.on_pause()
    
    def on_pause(self) -> None:
        """暂停钩子."""
        pass
    
    def resume(self) -> None:
        """恢复Agent."""
        if self._status != AgentStatus.PAUSED:
            return
        old_status = self._status
        self._status = AgentStatus.RUNNING
        self._record_transition(old_status, self._status, "resume")
        self.on_resume()
    
    def on_resume(self) -> None:
        """恢复钩子."""
        pass
    
    def stop(self) -> None:
        """停止Agent."""
        old_status = self._status
        self._status = AgentStatus.TERMINATED
        self._record_transition(old_status, self._status, "stop")
        self.on_stop()
    
    def on_stop(self) -> None:
        """停止钩子."""
        pass
    
    def terminate(self) -> None:
        """终止Agent."""
        self.stop()
    
    def get_transition_history(self) -> List[LifecycleTransitionRecord]:
        """获取状态转换历史."""
        return self._transition_history.copy()
    
    # ========== 核心执行 ==========
    
    def execute(self, context: AgentContext) -> TaskResult:
        """执行任务（统一入口）.
        
        增强：异常时自动记录状态转换，保持状态一致性。
        
        Args:
            context: 执行上下文
            
        Returns:
            TaskResult
        """
        if not self.is_available:
            return TaskResult(
                success=False,
                error_message=f"Agent {self._agent_id} is not available (status: {self._status.value})",
            )
        
        self._total_tasks += 1
        
        try:
            result = self.process(context)
            
            if result.success:
                self._successful_tasks += 1
            else:
                self._failed_tasks += 1
            
            return result
            
        except Exception as e:
            self._failed_tasks += 1
            # 记录异常状态转换
            old_status = self._status
            self._status = AgentStatus.ERROR
            self._record_transition(
                old_status, self._status,
                reason="execute_exception",
                success=False,
                error=str(e),
            )
            return TaskResult(
                success=False,
                error_message=f"Agent execution error: {e}",
            )
    
    @abstractmethod
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务（子类必须实现）.
        
        Args:
            context: 执行上下文
            
        Returns:
            TaskResult
        """
        pass
    
    # ========== 消息处理 ==========
    
    def _register_default_handlers(self) -> None:
        """注册默认消息处理器."""
        self._message_handlers[MessageType.TASK_ASSIGN] = self._handle_task_assign
        self._message_handlers[MessageType.STATUS_UPDATE] = self._handle_status_update
    
    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[Message], Optional[Message]],
    ) -> None:
        """注册消息处理器."""
        self._message_handlers[message_type] = handler
    
    def handle_message(self, message: Message) -> Optional[Message]:
        """处理消息.
        
        Args:
            message: 消息
            
        Returns:
            响应消息（可选）
        """
        handler = self._message_handlers.get(message.message_type)
        if handler:
            try:
                return handler(message)
            except Exception as e:
                return message.create_response(
                    payload={"error": str(e)},
                    sender_id=self._agent_id,
                )
        
        return message.create_response(
            payload={"error": f"No handler for {message.message_type.value}"},
            sender_id=self._agent_id,
        )
    
    def _handle_task_assign(self, message: Message) -> Optional[Message]:
        """处理任务分配消息."""
        context = AgentContext(
            input_data=message.payload or {},
            message=message,
        )
        
        result = self.execute(context)
        
        return message.create_response(
            payload=result.to_dict(),
            sender_id=self._agent_id,
        )
    
    def _handle_status_update(self, message: Message) -> Optional[Message]:
        """处理状态更新消息."""
        return message.create_response(
            payload={
                "agent_id": self._agent_id,
                "status": self._status.value,
                "total_tasks": self._total_tasks,
                "success_rate": self.success_rate,
            },
            sender_id=self._agent_id,
        )
    
    # ========== 消息发送 ==========
    
    def send_message(
        self,
        receiver_id: str,
        payload: Any,
        message_type: MessageType = MessageType.TEXT,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> bool:
        """发送消息."""
        message = Message.create(
            sender_id=self._agent_id,
            receiver_id=receiver_id,
            payload=payload,
            message_type=message_type,
            priority=priority,
        )
        return self._message_bus.send(message)
    
    def broadcast_message(
        self,
        payload: Any,
        receiver_role: Optional[str] = None,
        message_type: MessageType = MessageType.SYSTEM_EVENT,
    ) -> int:
        """广播消息."""
        message = Message.create_broadcast(
            sender_id=self._agent_id,
            payload=payload,
            receiver_role=receiver_role,
            message_type=message_type,
        )
        return self._message_bus.broadcast(message)
    
    # ========== 元数据 ==========
    
    def get_metadata(self) -> AgentMetadata:
        """获取Agent元数据."""
        capabilities = [
            AgentCapabilityDeclaration(capability=cap)
            for cap in self.AGENT_CAPABILITIES
        ]
        
        return AgentMetadata(
            agent_id=self._agent_id,
            name=self._name,
            role=self.AGENT_ROLE,
            description=self.AGENT_DESCRIPTION,
            capabilities=capabilities,
            status=self._status,
            module_path=self.__class__.__module__,
            class_name=self.__class__.__name__,
            total_tasks=self._total_tasks,
            successful_tasks=self._successful_tasks,
            failed_tasks=self._failed_tasks,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息."""
        return {
            "agent_id": self._agent_id,
            "name": self._name,
            "role": self.AGENT_ROLE.value,
            "status": self._status.value,
            "total_tasks": self._total_tasks,
            "successful_tasks": self._successful_tasks,
            "failed_tasks": self._failed_tasks,
            "success_rate": round(self.success_rate, 4),
            "is_available": self.is_available,
        }
