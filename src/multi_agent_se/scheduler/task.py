"""任务定义 - 阶段19.

定义任务的数据结构和状态管理：
- 任务类型与优先级
- 任务状态机
- 任务依赖关系
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Callable
import uuid


class TaskType(Enum):
    """任务类型."""
    # 开发任务
    CODE_GENERATION = "code_generation"       # 代码生成
    CODE_REVIEW = "code_review"              # 代码审查
    CODE_TESTING = "code_testing"            # 代码测试
    CODE_REFACTORING = "code_refactoring"    # 代码重构
    
    # 分析任务
    REQUIREMENT_ANALYSIS = "requirement_analysis"  # 需求分析
    ARCHITECTURE_DESIGN = "architecture_design"    # 架构设计
    
    # 修复任务
    BUG_FIXING = "bug_fixing"                # Bug修复
    ERROR_HANDLING = "error_handling"        # 错误处理
    
    # 文档任务
    DOCUMENTATION = "documentation"          # 文档生成
    COMMENT_GENERATION = "comment_generation"  # 注释生成
    
    # 管理任务
    TASK_DECOMPOSITION = "task_decomposition"  # 任务分解
    TASK_MERGING = "task_merging"            # 任务合并
    QUALITY_CHECK = "quality_check"          # 质量检查
    
    # 系统任务
    SYSTEM_INITIALIZATION = "system_init"    # 系统初始化
    SYSTEM_SHUTDOWN = "system_shutdown"      # 系统关闭
    HEALTH_CHECK = "health_check"            # 健康检查


class TaskPriority(Enum):
    """任务优先级."""
    CRITICAL = 0     # 关键（阻塞性）
    HIGH = 1         # 高优先级
    NORMAL = 2       # 普通
    LOW = 3          # 低优先级
    BACKGROUND = 4   # 后台任务


class TaskStatus(Enum):
    """任务状态."""
    PENDING = "pending"           # 待处理
    QUEUED = "queued"             # 已入队
    ASSIGNED = "assigned"         # 已分配
    RUNNING = "running"           # 执行中
    PAUSED = "paused"             # 已暂停
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消
    TIMEOUT = "timeout"           # 超时


@dataclass
class TaskRequirements:
    """任务需求."""
    required_capabilities: Set[str] = field(default_factory=set)  # 所需能力
    required_roles: Set[str] = field(default_factory=set)        # 所需角色
    min_agent_proficiency: float = 0.0                           # 最低熟练度
    
    # 资源需求
    estimated_duration_seconds: int = 60  # 预估执行时间
    max_retries: int = 3                  # 最大重试次数
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "required_capabilities": list(self.required_capabilities),
            "required_roles": list(self.required_roles),
            "min_agent_proficiency": self.min_agent_proficiency,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "max_retries": self.max_retries,
        }


@dataclass
class TaskResult:
    """任务结果."""
    success: bool = False
    output: Any = None
    error_message: str = ""
    artifacts: Dict[str, Any] = field(default_factory=dict)  # 产出物
    
    # 执行信息
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """执行时长."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error_message": self.error_message,
            "artifacts": self.artifacts,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class Task:
    """任务.
    
    调度器的基本工作单元
    """
    # 基本信息
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    task_type: TaskType = TaskType.CODE_GENERATION
    priority: TaskPriority = TaskPriority.NORMAL
    
    # 输入数据
    input_data: Dict[str, Any] = field(default_factory=dict)
    
    # 需求和约束
    requirements: TaskRequirements = field(default_factory=TaskRequirements)
    
    # 依赖关系
    dependencies: Set[str] = field(default_factory=set)  # 依赖的任务ID
    
    # 状态
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent_id: Optional[str] = None
    
    # 结果
    result: Optional[TaskResult] = None
    retry_count: int = 0
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    queued_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    
    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"Task-{self.task_id[:8]}"
    
    @property
    def is_ready(self) -> bool:
        """是否就绪（可以执行）."""
        return self.status == TaskStatus.PENDING and len(self.dependencies) == 0
    
    @property
    def is_running(self) -> bool:
        """是否正在执行."""
        return self.status == TaskStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """是否已完成."""
        return self.status == TaskStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """是否失败."""
        return self.status == TaskStatus.FAILED
    
    @property
    def is_terminal(self) -> bool:
        """是否处于终止状态."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        )
    
    @property
    def can_retry(self) -> bool:
        """是否可以重试."""
        if self.is_terminal and self.result:
            return self.retry_count < self.requirements.max_retries
        return False
    
    @property
    def wait_time_seconds(self) -> float:
        """等待时间."""
        if self.started_at:
            return (self.started_at - self.created_at).total_seconds()
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def execution_time_seconds(self) -> float:
        """执行时间."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return 0.0
    
    # ========== 状态转换方法 ==========
    
    def mark_queued(self) -> None:
        """标记为已入队."""
        self.status = TaskStatus.QUEUED
        self.queued_at = datetime.now()
    
    def mark_assigned(self, agent_id: str) -> None:
        """标记为已分配."""
        self.status = TaskStatus.ASSIGNED
        self.assigned_agent_id = agent_id
        self.assigned_at = datetime.now()
    
    def mark_running(self) -> None:
        """标记为执行中."""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        if self.result:
            self.result.started_at = self.started_at
    
    def mark_completed(self, result: TaskResult) -> None:
        """标记为已完成."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.result = result
        self.result.completed_at = self.completed_at
        if not self.result.started_at and self.started_at:
            self.result.started_at = self.started_at
    
    def mark_failed(self, error_message: str) -> None:
        """标记为失败."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.result = TaskResult(
            success=False,
            error_message=error_message,
            completed_at=self.completed_at,
        )
    
    def mark_cancelled(self, reason: str = "") -> None:
        """标记为已取消."""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
        self.metadata["cancel_reason"] = reason
    
    def mark_paused(self) -> None:
        """标记为暂停."""
        if self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.PAUSED
    
    def mark_resumed(self) -> None:
        """标记为恢复."""
        if self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.RUNNING
    
    def retry(self) -> bool:
        """重试任务.
        
        Returns:
            是否成功重置
        """
        if not self.can_retry:
            return False
        
        self.retry_count += 1
        self.status = TaskStatus.PENDING
        self.assigned_agent_id = None
        self.queued_at = None
        self.assigned_at = None
        self.started_at = None
        self.completed_at = None
        self.result = None
        
        return True
    
    # ========== 依赖管理 ==========
    
    def add_dependency(self, task_id: str) -> None:
        """添加依赖."""
        self.dependencies.add(task_id)
    
    def remove_dependency(self, task_id: str) -> None:
        """移除依赖."""
        self.dependencies.discard(task_id)
    
    def has_dependency(self, task_id: str) -> bool:
        """检查是否有依赖."""
        return task_id in self.dependencies
    
    # ========== 序列化 ==========
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "priority": self.priority.value,
            "input_data": self.input_data,
            "requirements": self.requirements.to_dict(),
            "dependencies": list(self.dependencies),
            "status": self.status.value,
            "assigned_agent_id": self.assigned_agent_id,
            "result": self.result.to_dict() if self.result else None,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "wait_time_seconds": self.wait_time_seconds,
            "execution_time_seconds": self.execution_time_seconds,
            "is_ready": self.is_ready,
            "is_terminal": self.is_terminal,
            "can_retry": self.can_retry,
            "metadata": self.metadata,
            "tags": list(self.tags),
        }
    
    @classmethod
    def create(
        cls,
        name: str,
        task_type: TaskType,
        input_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        description: str = "",
        dependencies: Optional[Set[str]] = None,
        required_capabilities: Optional[Set[str]] = None,
        required_roles: Optional[Set[str]] = None,
    ) -> "Task":
        """工厂方法：创建任务.
        
        Args:
            name: 任务名称
            task_type: 任务类型
            input_data: 输入数据
            priority: 优先级
            description: 描述
            dependencies: 依赖任务ID
            required_capabilities: 所需能力
            required_roles: 所需角色
            
        Returns:
            Task实例
        """
        requirements = TaskRequirements(
            required_capabilities=required_capabilities or set(),
            required_roles=required_roles or set(),
        )
        
        return cls(
            name=name,
            task_type=task_type,
            priority=priority,
            description=description,
            input_data=input_data,
            requirements=requirements,
            dependencies=dependencies or set(),
        )


# ========== 任务过滤器 ==========

class TaskFilter:
    """任务过滤器."""
    
    def __init__(
        self,
        task_types: Optional[Set[TaskType]] = None,
        priorities: Optional[Set[TaskPriority]] = None,
        statuses: Optional[Set[TaskStatus]] = None,
        min_priority: Optional[TaskPriority] = None,
        tags: Optional[Set[str]] = None,
    ) -> None:
        self.task_types = task_types
        self.priorities = priorities
        self.statuses = statuses
        self.min_priority = min_priority
        self.tags = tags
    
    def match(self, task: Task) -> bool:
        """检查任务是否匹配过滤器."""
        if self.task_types and task.task_type not in self.task_types:
            return False
        
        if self.priorities and task.priority not in self.priorities:
            return False
        
        if self.statuses and task.status not in self.statuses:
            return False
        
        if self.min_priority and task.priority.value > self.min_priority.value:
            return False
        
        if self.tags and not self.tags.intersection(task.tags):
            return False
        
        return True
