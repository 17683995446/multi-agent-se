"""Controller Agent - 第31阶段.

控制器Agent - 负责任务分解、分配和整体调度。

职责:
- 接收用户输入的需求/任务
- 将大任务分解为可管理的子任务
- 分析子任务间的依赖关系
- 调度子任务分配给合适的Agent
- 监控任务执行状态
- 处理异常和重试
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
import uuid
import time

from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
from multi_agent_se.agents.runtime.base_agent import BaseAgentImpl, AgentContext, TaskResult


class TaskPriority(Enum):
    """任务优先级."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class TaskStatus(Enum):
    """任务状态."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SubTask:
    """子任务."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    task_type: str = ""  # requirement/architect/developer/reviewer/tester/bugfix/documenter
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    
    # 依赖关系
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID列表
    dependent_tasks: List[str] = field(default_factory=list)  # 依赖此任务的任务ID列表
    
    # 执行信息
    assigned_agent: Optional[str] = None
    result: Optional[Any] = None
    error_message: str = ""
    
    # 时间戳
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    def can_execute(self, completed_task_ids: Set[str]) -> bool:
        """检查任务是否可以执行（所有依赖已完成）."""
        return all(dep in completed_task_ids for dep in self.dependencies)
    
    @property
    def execution_time(self) -> Optional[float]:
        """获取执行时间（秒）."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class TaskDecomposition:
    """任务分解结果."""
    original_requirement: str = ""
    sub_tasks: List[SubTask] = field(default_factory=list)
    strategy: str = "default"
    
    def get_execution_order(self) -> List[SubTask]:
        """获取按依赖排序的执行顺序."""
        # 拓扑排序
        completed: Set[str] = set()
        order: List[SubTask] = []
        remaining = list(self.sub_tasks)
        
        while remaining:
            # 找到可以执行的任务
            executable = [t for t in remaining if t.can_execute(completed)]
            if not executable:
                # 有循环依赖，按优先级排序
                executable = sorted(remaining, key=lambda t: t.priority.value)
            
            for task in executable:
                order.append(task)
                completed.add(task.task_id)
                remaining.remove(task)
        
        return order
    
    def get_parallel_groups(self) -> List[List[SubTask]]:
        """获取可以并行执行的组."""
        completed: Set[str] = set()
        remaining = list(self.sub_tasks)
        groups: List[List[SubTask]] = []
        
        while remaining:
            # 找到当前可以并行执行的所有任务
            group = [t for t in remaining if t.can_execute(completed)]
            if not group:
                break
            
            groups.append(group)
            for task in group:
                completed.add(task.task_id)
                remaining.remove(task)
        
        return groups


class ControllerAgent(BaseAgentImpl):
    """控制器Agent - 任务分解与调度中心.
    
    这是8大正交角色Agent中的核心，负责协调其他Agent的工作。
    """
    
    AGENT_ROLE = AgentRole.CONTROLLER
    AGENT_CAPABILITIES = [
        AgentCapability.TASK_DECOMPOSITION,
        AgentCapability.TASK_SCHEDULING,
    ]
    AGENT_DESCRIPTION = "控制器Agent - 负责任务分解、分配和整体调度"
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None) -> None:
        super().__init__(agent_id, config)
        self._decomposition_history: List[TaskDecomposition] = []
        self._task_callbacks: Dict[str, Callable] = {}
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务：分解输入需求并调度执行.
        
        Args:
            context: Agent执行上下文
            
        Returns:
            任务执行结果
        """
        input_data = context.input_data
        
        # 输入类型验证
        if not isinstance(input_data, dict):
            return TaskResult(
                success=False,
                error_message=f"输入数据必须是字典类型，实际为 {type(input_data).__name__}",
            )
        
        requirement = input_data.get("requirement", "")
        
        if not requirement:
            return TaskResult(
                success=False,
                error_message="缺少需求描述",
            )
        
        # 1. 任务分解
        decomposition = self._decompose_task(requirement, input_data)
        self._decomposition_history.append(decomposition)
        
        # 2. 分析依赖关系
        parallel_groups = decomposition.get_parallel_groups()
        execution_order = decomposition.get_execution_order()
        
        # 3. 构建执行计划
        execution_plan = {
            "total_tasks": len(decomposition.sub_tasks),
            "parallel_groups": len(parallel_groups),
            "execution_order": [t.name for t in execution_order],
        }
        
        # 4. 如果需要实际执行
        if input_data.get("execute", False):
            return self._execute_decomposition(decomposition, context)
        
        return TaskResult(
            success=True,
            output={
                "requirement": requirement,
                "decomposition": {
                    "sub_tasks": [
                        {
                            "task_id": t.task_id,
                            "name": t.name,
                            "type": t.task_type,
                            "priority": t.priority.value,
                            "dependencies": t.dependencies,
                        }
                        for t in decomposition.sub_tasks
                    ],
                    "execution_plan": execution_plan,
                    "parallel_groups": [
                        [t.name for t in group]
                        for group in parallel_groups
                    ],
                },
                "strategy": decomposition.strategy,
            },
            artifacts={
                "decomposition": decomposition,
                "execution_order": execution_order,
            },
        )
    
    def _decompose_task(
        self,
        requirement: str,
        input_data: Dict[str, Any],
    ) -> TaskDecomposition:
        """分解任务为子任务.
        
        Args:
            requirement: 原始需求
            input_data: 输入数据
            
        Returns:
            任务分解结果
        """
        strategy = input_data.get("strategy", "default")
        
        if strategy == "simple":
            return self._simple_decomposition(requirement)
        elif strategy == "agile":
            return self._agile_decomposition(requirement)
        else:
            return self._default_decomposition(requirement)
    
    def _default_decomposition(self, requirement: str) -> TaskDecomposition:
        """默认任务分解策略.
        
        标准软件工程流程：需求 -> 架构 -> 开发 -> 审查 -> 测试 -> 文档
        """
        decomposition = TaskDecomposition(
            original_requirement=requirement,
            strategy="default",
        )
        
        # 1. 需求分析
        req_task = SubTask(
            name="需求分析",
            description=f"分析需求: {requirement[:100]}",
            task_type="requirement",
            priority=TaskPriority.HIGH,
        )
        decomposition.sub_tasks.append(req_task)
        
        # 2. 架构设计
        arch_task = SubTask(
            name="架构设计",
            description="设计系统架构和模块划分",
            task_type="architect",
            priority=TaskPriority.HIGH,
            dependencies=[req_task.task_id],
        )
        decomposition.sub_tasks.append(arch_task)
        req_task.dependent_tasks.append(arch_task.task_id)
        
        # 3. 代码开发
        dev_task = SubTask(
            name="代码开发",
            description="实现功能代码",
            task_type="developer",
            priority=TaskPriority.NORMAL,
            dependencies=[arch_task.task_id],
        )
        decomposition.sub_tasks.append(dev_task)
        arch_task.dependent_tasks.append(dev_task.task_id)
        
        # 4. 代码审查
        review_task = SubTask(
            name="代码审查",
            description="审查代码质量和规范性",
            task_type="reviewer",
            priority=TaskPriority.NORMAL,
            dependencies=[dev_task.task_id],
        )
        decomposition.sub_tasks.append(review_task)
        dev_task.dependent_tasks.append(review_task.task_id)
        
        # 5. 测试验证
        test_task = SubTask(
            name="测试验证",
            description="编写和执行测试用例",
            task_type="tester",
            priority=TaskPriority.NORMAL,
            dependencies=[dev_task.task_id],
        )
        decomposition.sub_tasks.append(test_task)
        dev_task.dependent_tasks.append(test_task.task_id)
        
        # 6. 文档编写
        doc_task = SubTask(
            name="文档编写",
            description="编写技术文档和使用说明",
            task_type="documenter",
            priority=TaskPriority.LOW,
            dependencies=[dev_task.task_id],
        )
        decomposition.sub_tasks.append(doc_task)
        dev_task.dependent_tasks.append(doc_task.task_id)
        
        return decomposition
    
    def _simple_decomposition(self, requirement: str) -> TaskDecomposition:
        """简单任务分解策略.
        
        最小化流程：开发 -> 测试
        """
        decomposition = TaskDecomposition(
            original_requirement=requirement,
            strategy="simple",
        )
        
        dev_task = SubTask(
            name="代码开发",
            description=f"实现: {requirement[:100]}",
            task_type="developer",
            priority=TaskPriority.NORMAL,
        )
        decomposition.sub_tasks.append(dev_task)
        
        test_task = SubTask(
            name="测试验证",
            description="验证功能正确性",
            task_type="tester",
            priority=TaskPriority.NORMAL,
            dependencies=[dev_task.task_id],
        )
        decomposition.sub_tasks.append(test_task)
        dev_task.dependent_tasks.append(test_task.task_id)
        
        return decomposition
    
    def _agile_decomposition(self, requirement: str) -> TaskDecomposition:
        """敏捷任务分解策略.
        
        迭代式开发：需求 -> 开发 -> 测试 -> 审查（循环）
        """
        decomposition = TaskDecomposition(
            original_requirement=requirement,
            strategy="agile",
        )
        
        # 迭代1: MVP
        req_task = SubTask(
            name="需求分析(MVP)",
            description=f"MVP需求: {requirement[:80]}",
            task_type="requirement",
            priority=TaskPriority.HIGH,
        )
        decomposition.sub_tasks.append(req_task)
        
        dev_task = SubTask(
            name="MVP开发",
            description="开发最小可行产品",
            task_type="developer",
            priority=TaskPriority.HIGH,
            dependencies=[req_task.task_id],
        )
        decomposition.sub_tasks.append(dev_task)
        
        test_task = SubTask(
            name="MVP测试",
            description="验证MVP功能",
            task_type="tester",
            priority=TaskPriority.HIGH,
            dependencies=[dev_task.task_id],
        )
        decomposition.sub_tasks.append(test_task)
        
        return decomposition
    
    def _execute_decomposition(
        self,
        decomposition: TaskDecomposition,
        context: AgentContext,
    ) -> TaskResult:
        """执行分解后的任务.
        
        Args:
            decomposition: 任务分解结果
            context: 执行上下文
            
        Returns:
            执行结果
        """
        # 获取执行顺序
        execution_order = decomposition.get_execution_order()
        
        completed_tasks: List[SubTask] = []
        failed_tasks: List[SubTask] = []
        
        for task in execution_order:
            # 更新状态
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()
            
            try:
                # 模拟执行（实际应该调用对应的Agent）
                task.result = self._simulate_task_execution(task, context)
                task.status = TaskStatus.COMPLETED
                completed_tasks.append(task)
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                failed_tasks.append(task)
            
            task.completed_at = time.time()
        
        return TaskResult(
            success=len(failed_tasks) == 0,
            output={
                "total_tasks": len(decomposition.sub_tasks),
                "completed": len(completed_tasks),
                "failed": len(failed_tasks),
                "execution_time": sum(
                    t.execution_time or 0 for t in execution_order
                ),
            },
            artifacts={
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
            },
        )
    
    def _simulate_task_execution(
        self,
        task: SubTask,
        context: AgentContext,
    ) -> Dict[str, Any]:
        """模拟任务执行.
        
        实际实现中，这里应该调用对应的Agent来执行任务。
        
        Args:
            task: 要执行的子任务
            context: 执行上下文
            
        Returns:
            模拟执行结果
        """
        return {
            "task_id": task.task_id,
            "task_name": task.name,
            "task_type": task.task_type,
            "status": "completed",
            "simulated": True,
        }
    
    def get_decomposition_history(self) -> List[TaskDecomposition]:
        """获取任务分解历史."""
        return self._decomposition_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        total_decompositions = len(self._decomposition_history)
        total_tasks = sum(
            len(d.sub_tasks) for d in self._decomposition_history
        )
        
        return {
            "total_decompositions": total_decompositions,
            "total_tasks_generated": total_tasks,
            "avg_tasks_per_decomposition": (
                total_tasks / total_decompositions if total_decompositions > 0 else 0
            ),
        }
