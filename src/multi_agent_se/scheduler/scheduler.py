"""任务调度器 - 阶段19.

实现任务调度核心逻辑：
- 任务分配策略
- 调度循环
- 任务执行管理
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from multi_agent_se.scheduler.task import Task, TaskPriority, TaskStatus, TaskType, TaskResult
from multi_agent_se.scheduler.queue import TaskQueue, QueueStats
from multi_agent_se.agents.registry import AgentRegistry, get_registry, AgentCapability
from multi_agent_se.agents.lifecycle import AgentPool, get_pool


class SchedulingStrategy(ABC):
    """调度策略接口."""
    
    @abstractmethod
    def select_agent(self, task: Task, available_agents: List[Any]) -> Optional[str]:
        """选择执行任务的Agent.
        
        Args:
            task: 任务
            available_agents: 可用Agent列表
            
        Returns:
            选中的Agent ID或None
        """
        pass


class CapabilityMatchingStrategy(SchedulingStrategy):
    """能力匹配策略.
    
    选择最匹配任务需求的Agent
    """
    
    def select_agent(self, task: Task, available_agents: List[Any]) -> Optional[str]:
        """选择Agent.
        
        评分规则：
        1. 能力匹配度（必需能力占比）
        2. 熟练度
        3. 当前负载（越低越好）
        """
        if not available_agents:
            return None
        
        best_agent = None
        best_score = -1
        
        required_caps = task.requirements.required_capabilities
        required_roles = task.requirements.required_roles
        
        for agent_info in available_agents:
            metadata = agent_info.metadata
            
            # 检查角色要求
            if required_roles and metadata.role.value not in required_roles:
                continue
            
            score = 0.0
            
            # 能力匹配度
            if required_caps:
                matched = 0
                total_proficiency = 0.0
                for cap in required_caps:
                    if metadata.has_capability(AgentCapability(cap)):
                        matched += 1
                        total_proficiency += metadata.get_capability_proficiency(
                            AgentCapability(cap)
                        )
                
                if matched == 0:
                    continue  # 必需能力不匹配
                
                cap_score = (matched / len(required_caps)) * 0.5
                prof_score = (total_proficiency / len(required_caps)) * 0.3
                score += cap_score + prof_score
            else:
                score += 0.4  # 无特殊能力要求
            
            # 当前负载（任务数越少越好）
            load_score = max(0, 1.0 - metadata.total_tasks * 0.1) * 0.2
            score += load_score
            
            if score > best_score:
                best_score = score
                best_agent = metadata.agent_id
        
        return best_agent


class RoundRobinStrategy(SchedulingStrategy):
    """轮询策略.
    
    轮流选择Agent，实现负载均衡
    """
    
    def __init__(self) -> None:
        self._last_index = 0
    
    def select_agent(self, task: Task, available_agents: List[Any]) -> Optional[str]:
        if not available_agents:
            return None
        
        # 简单轮询
        agent = available_agents[self._last_index % len(available_agents)]
        self._last_index += 1
        return agent.metadata.agent_id


class PriorityBasedStrategy(SchedulingStrategy):
    """优先级策略.
    
    优先选择高熟练度的Agent
    """
    
    def select_agent(self, task: Task, available_agents: List[Any]) -> Optional[str]:
        if not available_agents:
            return None
        
        best_agent = None
        best_proficiency = -1
        
        required_caps = task.requirements.required_capabilities
        
        for agent_info in available_agents:
            metadata = agent_info.metadata
            
            # 计算平均熟练度
            if required_caps:
                proficiencies = [
                    metadata.get_capability_proficiency(AgentCapability(cap))
                    for cap in required_caps
                ]
                avg_proficiency = sum(proficiencies) / len(proficiencies)
            else:
                avg_proficiency = 0.5
            
            if avg_proficiency > best_proficiency:
                best_proficiency = avg_proficiency
                best_agent = metadata.agent_id
        
        return best_agent


@dataclass
class SchedulerStats:
    """调度器统计."""
    total_scheduled: int = 0
    total_completed: int = 0
    total_failed: int = 0
    total_cancelled: int = 0
    
    by_type: Dict[str, int] = field(default_factory=dict)
    by_priority: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_scheduled": self.total_scheduled,
            "total_completed": self.total_completed,
            "total_failed": self.total_failed,
            "total_cancelled": self.total_cancelled,
            "by_type": self.by_type,
            "by_priority": self.by_priority,
        }


class Scheduler:
    """任务调度器.
    
    负责任务的调度、分配和执行管理
    """
    
    def __init__(
        self,
        strategy: Optional[SchedulingStrategy] = None,
        registry: Optional[AgentRegistry] = None,
        agent_pool: Optional[AgentPool] = None,
    ) -> None:
        """初始化调度器.
        
        Args:
            strategy: 调度策略
            registry: Agent注册表
            agent_pool: Agent实例池
        """
        self._strategy = strategy or CapabilityMatchingStrategy()
        self._registry = registry or get_registry()
        self._agent_pool = agent_pool or get_pool()
        
        # 任务队列
        self._queue = TaskQueue()
        
        # 运行中的任务
        self._running_tasks: Dict[str, Task] = {}
        
        # 完成的任务
        self._completed_tasks: Dict[str, Task] = {}
        
        # 统计
        self._stats = SchedulerStats()
        
        # 回调
        self._on_task_completed: List[Callable[[Task], None]] = []
        self._on_task_failed: List[Callable[[Task], None]] = []
    
    # ========== 任务提交 ==========
    
    def submit(self, task: Task) -> bool:
        """提交任务.
        
        Args:
            task: 任务
            
        Returns:
            是否成功提交
        """
        # 检查依赖是否完成
        for dep_id in task.dependencies:
            if dep_id in self._running_tasks:
                # 依赖还在运行，不能入队
                return False
            if dep_id not in self._completed_tasks:
                # 依赖不存在或未完成
                if not self._queue.has(dep_id):
                    return False
        
        # 入队
        if self._queue.enqueue(task):
            # 更新统计
            self._stats.total_scheduled += 1
            type_name = task.task_type.value
            self._stats.by_type[type_name] = self._stats.by_type.get(type_name, 0) + 1
            priority_name = task.priority.name
            self._stats.by_priority[priority_name] = self._stats.by_priority.get(priority_name, 0) + 1
            return True
        
        return False
    
    def submit_batch(self, tasks: List[Task]) -> int:
        """批量提交任务.
        
        Args:
            tasks: 任务列表
            
        Returns:
            成功提交的数量
        """
        count = 0
        for task in tasks:
            if self.submit(task):
                count += 1
        return count
    
    # ========== 任务调度 ==========
    
    def schedule_once(self) -> Optional[Task]:
        """执行一次调度.
        
        Returns:
            分配的任务或None
        """
        # 获取就绪的任务
        ready_task = self._queue.dequeue()
        if not ready_task:
            return None
        
        # 获取可用Agent
        available_agents = self._agent_pool.get_active()
        if not available_agents:
            # 没有可用Agent，放回队列
            self._queue.enqueue(ready_task)
            return None
        
        # 选择Agent
        agent_id = self._strategy.select_agent(ready_task, available_agents)
        if not agent_id:
            # 没有合适的Agent，放回队列
            self._queue.enqueue(ready_task)
            return None
        
        # 分配任务
        ready_task.mark_assigned(agent_id)
        self._running_tasks[ready_task.task_id] = ready_task
        
        return ready_task
    
    def schedule_all(self) -> List[Task]:
        """调度所有就绪任务.
        
        Returns:
            分配的任务列表
        """
        assigned = []
        while True:
            task = self.schedule_once()
            if not task:
                break
            assigned.append(task)
        return assigned
    
    # ========== 任务完成处理 ==========
    
    def complete_task(self, task_id: str, result: TaskResult) -> bool:
        """完成任务.
        
        Args:
            task_id: 任务ID
            result: 执行结果
            
        Returns:
            是否成功
        """
        if task_id not in self._running_tasks:
            return False
        
        task = self._running_tasks[task_id]
        task.mark_completed(result)
        
        # 移动到完成列表
        del self._running_tasks[task_id]
        self._completed_tasks[task_id] = task
        
        # 更新统计
        self._stats.total_completed += 1
        
        # 触发回调
        for callback in self._on_task_completed:
            try:
                callback(task)
            except Exception:
                pass
        
        # 更新依赖该任务的其他任务
        self._update_dependent_tasks(task_id)
        
        return True
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """标记任务失败.
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            
        Returns:
            是否成功
        """
        if task_id not in self._running_tasks:
            return False
        
        task = self._running_tasks[task_id]
        task.mark_failed(error_message)
        
        # 移动到完成列表
        del self._running_tasks[task_id]
        self._completed_tasks[task_id] = task
        
        # 更新统计
        self._stats.total_failed += 1
        
        # 触发回调
        for callback in self._on_task_failed:
            try:
                callback(task)
            except Exception:
                pass
        
        # 检查是否需要重试
        if task.can_retry:
            task.retry()
            self.submit(task)
        
        return True
    
    def cancel_task(self, task_id: str, reason: str = "") -> bool:
        """取消任务.
        
        Args:
            task_id: 任务ID
            reason: 取消原因
            
        Returns:
            是否成功
        """
        # 检查运行中的任务
        if task_id in self._running_tasks:
            task = self._running_tasks[task_id]
            task.mark_cancelled(reason)
            del self._running_tasks[task_id]
            self._completed_tasks[task_id] = task
            self._stats.total_cancelled += 1
            return True
        
        # 检查队列中的任务
        task = self._queue.get(task_id)
        if task:
            task.mark_cancelled(reason)
            self._queue.remove(task_id)
            self._completed_tasks[task_id] = task
            self._stats.total_cancelled += 1
            return True
        
        return False
    
    def _update_dependent_tasks(self, completed_task_id: str) -> None:
        """更新依赖已完成任务的其他任务.
        
        Args:
            completed_task_id: 已完成的任务ID
        """
        # 检查队列中的任务
        for task in self._queue.get_all():
            if completed_task_id in task.dependencies:
                task.remove_dependency(completed_task_id)
    
    # ========== 查询 ==========
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务或None
        """
        # 检查运行中
        if task_id in self._running_tasks:
            return self._running_tasks[task_id]
        
        # 检查已完成
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        
        # 检查队列
        return self._queue.get(task_id)
    
    def get_running_tasks(self) -> List[Task]:
        """获取运行中的任务."""
        return list(self._running_tasks.values())
    
    def get_completed_tasks(self) -> List[Task]:
        """获取已完成的任务."""
        return list(self._completed_tasks.values())
    
    def get_pending_tasks(self) -> List[Task]:
        """获取待处理的任务."""
        return self._queue.get_all()
    
    def get_ready_tasks(self) -> List[Task]:
        """获取就绪的任务."""
        return self._queue.get_ready_tasks()
    
    # ========== 统计 ==========
    
    def get_stats(self) -> SchedulerStats:
        """获取调度器统计."""
        return self._stats
    
    def get_queue_stats(self) -> QueueStats:
        """获取队列统计."""
        return self._queue.get_stats()
    
    # ========== 回调注册 ==========
    
    def on_task_completed(self, callback: Callable[[Task], None]) -> None:
        """注册任务完成回调."""
        self._on_task_completed.append(callback)
    
    def on_task_failed(self, callback: Callable[[Task], None]) -> None:
        """注册任务失败回调."""
        self._on_task_failed.append(callback)
    
    # ========== 清理 ==========
    
    def clear(self) -> None:
        """清空所有任务."""
        self._queue.clear()
        self._running_tasks.clear()
        self._completed_tasks.clear()
        self._stats = SchedulerStats()
