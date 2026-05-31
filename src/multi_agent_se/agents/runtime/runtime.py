"""Agent运行时核心 - 阶段20.

统一管理Agent的创建、注册、执行：
- AgentRuntime运行时
- Agent执行循环
- 统一入口
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from multi_agent_se.agents.registry import (
    AgentRole,
    AgentCapability,
    AgentRegistry,
    get_registry,
    reset_registry,
)
from multi_agent_se.agents.lifecycle import (
    LifecycleState,
    AgentFactory,
    AgentInstance,
    AgentPool,
    get_pool,
    reset_pool,
)
from multi_agent_se.agents.communication import (
    Message,
    MessageType,
    MessageBus,
    get_message_bus,
    reset_message_bus,
)
from multi_agent_se.agents.runtime.base_agent import (
    BaseAgentImpl,
    AgentContext,
    AgentExecutionError,
)
from multi_agent_se.agents.runtime.role_agents import (
    AGENT_CLASSES,
    create_agent_by_role,
    create_all_agents,
)
from multi_agent_se.scheduler import (
    Task,
    TaskType,
    TaskResult,
    Scheduler,
    CapabilityMatchingStrategy,
)


class RuntimeError(Exception):
    """运行时错误."""
    pass


@dataclass
class RuntimeStats:
    """运行时统计."""
    total_agents: int = 0
    active_agents: int = 0
    total_tasks_executed: int = 0
    total_tasks_succeeded: int = 0
    total_tasks_failed: int = 0
    uptime_seconds: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率."""
        if self.total_tasks_executed == 0:
            return 0.0
        return self.total_tasks_succeeded / self.total_tasks_executed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_agents": self.total_agents,
            "active_agents": self.active_agents,
            "total_tasks_executed": self.total_tasks_executed,
            "total_tasks_succeeded": self.total_tasks_succeeded,
            "total_tasks_failed": self.total_tasks_failed,
            "uptime_seconds": self.uptime_seconds,
            "success_rate": (
                self.total_tasks_succeeded / self.total_tasks_executed
                if self.total_tasks_executed > 0
                else 0.0
            ),
        }


class AgentRuntime:
    """Agent运行时.
    
    统一管理所有Agent的创建、注册、执行
    """
    
    def __init__(
        self,
        registry: Optional[AgentRegistry] = None,
        message_bus: Optional[MessageBus] = None,
        pool: Optional[AgentPool] = None,
    ) -> None:
        """初始化运行时.
        
        Args:
            registry: Agent注册表
            message_bus: 消息总线
            pool: Agent实例池
        """
        self._registry = registry or get_registry()
        self._message_bus = message_bus or get_message_bus()
        self._pool = pool or get_pool()
        self._scheduler = Scheduler(
            strategy=CapabilityMatchingStrategy(),
            registry=self._registry,
            agent_pool=self._pool,
        )
        
        # Agent实例存储
        self._agents: Dict[str, BaseAgentImpl] = {}
        
        # 统计
        self._stats = RuntimeStats()
        self._started_at: Optional[datetime] = None
        
        # 回调
        self._on_task_complete: List[Callable] = []
    
    # ========== 初始化 ==========
    
    def initialize(self, include_builtin: bool = True) -> None:
        """初始化运行时.
        
        Args:
            include_builtin: 是否包含内置Agent
        """
        self._started_at = datetime.now()
        
        if include_builtin:
            self._register_builtin_agents()
    
    def _register_builtin_agents(self) -> None:
        """注册内置Agent."""
        for role, agent_class in AGENT_CLASSES.items():
            agent_id = f"runtime.{role.value}"
            agent = agent_class(agent_id=agent_id, message_bus=self._message_bus)
            
            # 初始化Agent
            agent.initialize()
            
            # 注册到运行时
            self._agents[agent_id] = agent
            
            # 注册到注册表
            metadata = agent.get_metadata()
            self._registry.register(
                metadata=metadata,
                agent_class=agent_class,
                instance=agent,
            )
        
        self._stats.total_agents = len(self._agents)
    
    # ========== Agent管理 ==========
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgentImpl]:
        """获取Agent."""
        return self._agents.get(agent_id)
    
    def get_agent_by_role(self, role: AgentRole) -> Optional[BaseAgentImpl]:
        """按角色获取Agent."""
        agent_id = f"runtime.{role.value}"
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, BaseAgentImpl]:
        """获取所有Agent."""
        return dict(self._agents)
    
    def get_active_agents(self) -> List[BaseAgentImpl]:
        """获取活跃Agent."""
        return [a for a in self._agents.values() if a.is_available]
    
    def register_agent(self, agent: BaseAgentImpl) -> str:
        """注册自定义Agent."""
        agent.initialize()
        self._agents[agent.agent_id] = agent
        
        metadata = agent.get_metadata()
        self._registry.register(
            metadata=metadata,
            agent_class=type(agent),
            instance=agent,
        )
        
        self._stats.total_agents = len(self._agents)
        return agent.agent_id
    
    # ========== 任务执行 ==========
    
    def execute_task(
        self,
        role: AgentRole,
        input_data: Dict[str, Any],
        task_name: str = "",
    ) -> TaskResult:
        """执行任务.
        
        Args:
            role: 目标角色
            input_data: 输入数据
            task_name: 任务名称
            
        Returns:
            TaskResult
        """
        agent = self.get_agent_by_role(role)
        if not agent:
            return TaskResult(
                success=False,
                error_message=f"Agent for role '{role.value}' not found",
            )
        
        context = AgentContext(
            input_data=input_data,
            metadata={"task_name": task_name},
        )
        
        result = agent.execute(context)
        
        # 更新统计
        self._stats.total_tasks_executed += 1
        if result.success:
            self._stats.total_tasks_succeeded += 1
        else:
            self._stats.total_tasks_failed += 1
        
        # 触发回调
        for callback in self._on_task_complete:
            try:
                callback(role, result)
            except Exception:
                pass
        
        return result
    
    def execute_pipeline(
        self,
        input_data: Dict[str, Any],
        pipeline: Optional[List[AgentRole]] = None,
    ) -> List[Dict[str, Any]]:
        """执行流水线.
        
        Args:
            input_data: 输入数据
            pipeline: 流水线角色列表（默认使用标准流水线）
            
        Returns:
            每个阶段的执行结果
        """
        if pipeline is None:
            pipeline = [
                AgentRole.REQUIREMENT,
                AgentRole.ARCHITECT,
                AgentRole.DEVELOPER,
                AgentRole.REVIEWER,
                AgentRole.TESTER,
                AgentRole.DOCUMENTER,
            ]
        
        results = []
        current_data = dict(input_data)
        
        for role in pipeline:
            result = self.execute_task(role, current_data)
            
            results.append({
                "role": role.value,
                "success": result.success,
                "output": result.output,
                "error": result.error_message,
            })
            
            if result.success and result.output:
                # 将输出传递给下一阶段
                if isinstance(result.output, dict):
                    current_data.update(result.output)
            
            # 如果某阶段失败，停止流水线
            if not result.success:
                break
        
        return results
    
    # ========== 消息路由 ==========
    
    def route_message(self, message: Message) -> Optional[Message]:
        """路由消息到目标Agent.
        
        Args:
            message: 消息
            
        Returns:
            响应消息
        """
        if message.is_broadcast:
            # 广播给所有活跃Agent
            for agent in self.get_active_agents():
                agent.handle_message(message)
            return None
        
        receiver_id = message.receiver_id
        if not receiver_id:
            return None
        
        agent = self._agents.get(receiver_id)
        if not agent:
            return message.create_response(
                payload={"error": f"Agent '{receiver_id}' not found"},
                sender_id="runtime",
            )
        
        return agent.handle_message(message)
    
    # ========== 统计 ==========
    
    def get_stats(self) -> RuntimeStats:
        """获取运行时统计."""
        if self._started_at:
            self._stats.uptime_seconds = (datetime.now() - self._started_at).total_seconds()
        
        self._stats.active_agents = len(self.get_active_agents())
        return self._stats
    
    def get_agent_stats(self) -> List[Dict[str, Any]]:
        """获取所有Agent的统计."""
        return [agent.get_stats() for agent in self._agents.values()]
    
    # ========== 回调 ==========
    
    def on_task_complete(self, callback: Callable) -> None:
        """注册任务完成回调."""
        self._on_task_complete.append(callback)
    
    # ========== 清理 ==========
    
    def shutdown(self) -> None:
        """关闭运行时."""
        for agent in self._agents.values():
            try:
                agent.stop()
            except Exception:
                pass
        
        self._agents.clear()
        self._stats.total_agents = 0


# ========== 全局运行时 ==========

_global_runtime: Optional[AgentRuntime] = None


def get_runtime() -> AgentRuntime:
    """获取全局运行时."""
    global _global_runtime
    if _global_runtime is None:
        _global_runtime = AgentRuntime()
    return _global_runtime


def reset_runtime() -> None:
    """重置全局运行时."""
    global _global_runtime
    reset_registry()
    reset_message_bus()
    reset_pool()
    if _global_runtime is not None:
        _global_runtime.shutdown()
    _global_runtime = AgentRuntime()
