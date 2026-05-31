"""任务队列 - 阶段19.

实现任务队列管理：
- 优先级队列
- 任务排序
- 队列统计
"""

import heapq
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List, Optional, Set

from multi_agent_se.scheduler.task import Task, TaskPriority, TaskStatus, TaskFilter


@dataclass
class QueueStats:
    """队列统计."""
    total_tasks: int = 0
    pending_tasks: int = 0
    queued_tasks: int = 0
    by_priority: Dict[str, int] = field(default_factory=dict)
    by_type: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tasks": self.total_tasks,
            "pending_tasks": self.pending_tasks,
            "queued_tasks": self.queued_tasks,
            "by_priority": self.by_priority,
            "by_type": self.by_type,
        }


class TaskQueue:
    """任务队列.
    
    管理任务的排队和调度
    """
    
    def __init__(self, max_size: int = 1000) -> None:
        """初始化任务队列.
        
        Args:
            max_size: 最大队列大小
        """
        self._max_size = max_size
        
        # 优先级队列 (priority, created_at, task_id, task)
        # 使用创建时间作为次级排序，确保FIFO
        self._queue: List[tuple] = []
        
        # 任务索引
        self._tasks: Dict[str, Task] = {}
        
        # 锁
        self._lock = Lock()
        
        # 统计
        self._stats = QueueStats()
    
    def enqueue(self, task: Task) -> bool:
        """将任务加入队列.
        
        Args:
            task: 任务
            
        Returns:
            是否成功入队
        """
        with self._lock:
            if len(self._queue) >= self._max_size:
                return False
            
            if task.task_id in self._tasks:
                return False
            
            # 更新任务状态
            task.mark_queued()
            
            # 入队 (priority_value, created_at, task_id, task)
            heapq.heappush(
                self._queue,
                (task.priority.value, task.created_at, task.task_id, task)
            )
            
            # 索引
            self._tasks[task.task_id] = task
            
            return True
    
    def dequeue(self, filter: Optional[TaskFilter] = None) -> Optional[Task]:
        """从队列取出任务.
        
        Args:
            filter: 任务过滤器
            
        Returns:
            任务或None
        """
        with self._lock:
            while self._queue:
                _, _, task_id, task = heapq.heappop(self._queue)
                
                # 检查是否仍在索引中（可能被移除）
                if task_id not in self._tasks:
                    continue
                
                # 检查过滤器
                if filter and not filter.match(task):
                    # 不匹配，放回队列
                    heapq.heappush(
                        self._queue,
                        (task.priority.value, task.created_at, task_id, task)
                    )
                    continue
                
                # 从索引移除
                del self._tasks[task_id]
                
                return task
            
            return None
    
    def peek(self, filter: Optional[TaskFilter] = None) -> Optional[Task]:
        """查看队列头部任务（不取出）.
        
        Args:
            filter: 任务过滤器
            
        Returns:
            任务或None
        """
        with self._lock:
            for priority, created_at, task_id, task in self._queue:
                if task_id not in self._tasks:
                    continue
                
                if filter and not filter.match(task):
                    continue
                
                return task
            
            return None
    
    def remove(self, task_id: str) -> bool:
        """从队列移除任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功移除
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            del self._tasks[task_id]
            return True
    
    def get(self, task_id: str) -> Optional[Task]:
        """获取任务（不移除）.
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务或None
        """
        return self._tasks.get(task_id)
    
    def has(self, task_id: str) -> bool:
        """检查队列中是否有任务.
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否存在
        """
        return task_id in self._tasks
    
    def get_all(self) -> List[Task]:
        """获取所有任务.
        
        Returns:
            任务列表
        """
        with self._lock:
            return list(self._tasks.values())
    
    def get_by_priority(self, priority: TaskPriority) -> List[Task]:
        """按优先级获取任务.
        
        Args:
            priority: 优先级
            
        Returns:
            任务列表
        """
        with self._lock:
            return [
                task for task in self._tasks.values()
                if task.priority == priority
            ]
    
    def get_by_status(self, status: TaskStatus) -> List[Task]:
        """按状态获取任务.
        
        Args:
            status: 状态
            
        Returns:
            任务列表
        """
        with self._lock:
            return [
                task for task in self._tasks.values()
                if task.status == status
            ]
    
    def get_ready_tasks(self) -> List[Task]:
        """获取就绪的任务（无依赖）.
        
        Returns:
            任务列表
        """
        with self._lock:
            return [
                task for task in self._tasks.values()
                if task.is_ready
            ]
    
    def clear(self) -> int:
        """清空队列.
        
        Returns:
            清空的任务数
        """
        with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._tasks.clear()
            return count
    
    def get_stats(self) -> QueueStats:
        """获取队列统计."""
        with self._lock:
            by_priority: Dict[str, int] = {}
            by_type: Dict[str, int] = {}
            
            for task in self._tasks.values():
                priority_name = task.priority.name
                by_priority[priority_name] = by_priority.get(priority_name, 0) + 1
                
                type_name = task.task_type.value
                by_type[type_name] = by_type.get(type_name, 0) + 1
            
            return QueueStats(
                total_tasks=len(self._tasks),
                pending_tasks=len([t for t in self._tasks.values() if t.status == TaskStatus.PENDING]),
                queued_tasks=len([t for t in self._tasks.values() if t.status == TaskStatus.QUEUED]),
                by_priority=by_priority,
                by_type=by_type,
            )
    
    @property
    def size(self) -> int:
        """队列大小."""
        return len(self._tasks)
    
    @property
    def is_empty(self) -> bool:
        """是否为空."""
        return len(self._tasks) == 0
    
    @property
    def is_full(self) -> bool:
        """是否已满."""
        return len(self._tasks) >= self._max_size
