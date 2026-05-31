"""Agent协作机制 - 第39阶段.

实现Agent间的协作能力：
- AgentCoordinator: 协调多个Agent完成复杂任务
- TaskOrchestrator: 任务编排和工作流定义
- CollaborationContext: 协作上下文
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid
from datetime import datetime

from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
from multi_agent_se.agents.communication.message import Message, MessageType


class CollaborationStatus(Enum):
    """协作状态."""
    PENDING = "pending"           # 待开始
    RUNNING = "running"           # 运行中
    PAUSED = "paused"             # 已暂停
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class TaskDependencyType(Enum):
    """任务依赖类型."""
    SEQUENTIAL = "sequential"     # 顺序执行
    PARALLEL = "parallel"         # 并行执行
    CONDITIONAL = "conditional"   # 条件执行


@dataclass
class AgentTask:
    """Agent任务."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    
    # 执行信息
    agent_role: AgentRole = AgentRole.CONTROLLER
    agent_id: Optional[str] = None
    
    # 输入输出
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    # 依赖
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    dependency_type: TaskDependencyType = TaskDependencyType.SEQUENTIAL
    
    # 条件
    condition: Optional[Callable[[Dict], bool]] = None
    
    # 状态
    status: CollaborationStatus = CollaborationStatus.PENDING
    error_message: str = ""
    
    # 时间
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "agent_role": self.agent_role.value,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "has_output": bool(self.output_data),
        }


@dataclass
class WorkflowDefinition:
    """工作流定义."""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    
    # 任务列表
    tasks: List[AgentTask] = field(default_factory=list)
    
    # 入口任务
    entry_task: Optional[str] = None
    
    # 元数据
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description[:100],
            "tasks_count": len(self.tasks),
            "entry_task": self.entry_task,
            "version": self.version,
        }


@dataclass
class CollaborationContext:
    """协作上下文."""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 工作流
    workflow: Optional[WorkflowDefinition] = None
    
    # 状态
    status: CollaborationStatus = CollaborationStatus.PENDING
    
    # 执行跟踪
    completed_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    running_task: Optional[str] = None
    
    # 共享数据
    shared_data: Dict[str, Any] = field(default_factory=dict)
    
    # 结果
    results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 错误
    errors: List[Tuple[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "status": self.status.value,
            "completed_count": len(self.completed_tasks),
            "pending_count": len(self.pending_tasks),
            "running_task": self.running_task,
            "has_errors": len(self.errors) > 0,
        }


class TaskOrchestrator:
    """任务编排器.
    
    负责定义和管理任务工作流。
    """
    
    def __init__(self) -> None:
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._templates: Dict[str, WorkflowDefinition] = self._load_templates()
    
    def create_workflow(self, name: str, description: str = "") -> WorkflowDefinition:
        """创建工作流.
        
        Args:
            name: 工作流名称
            description: 描述
            
        Returns:
            工作流定义
        """
        workflow = WorkflowDefinition(name=name, description=description)
        self._workflows[workflow.workflow_id] = workflow
        return workflow
    
    def add_task(
        self,
        workflow: WorkflowDefinition,
        name: str,
        agent_role: AgentRole,
        input_data: Optional[Dict] = None,
        dependencies: Optional[List[str]] = None,
        dependency_type: TaskDependencyType = TaskDependencyType.SEQUENTIAL,
        condition: Optional[Callable] = None,
    ) -> AgentTask:
        """添加任务到工作流.
        
        Args:
            workflow: 工作流
            name: 任务名称
            agent_role: 执行的Agent角色
            input_data: 输入数据
            dependencies: 依赖任务ID
            dependency_type: 依赖类型
            condition: 条件函数
            
        Returns:
            创建的任务
        """
        task = AgentTask(
            name=name,
            agent_role=agent_role,
            input_data=input_data or {},
            dependencies=dependencies or [],
            dependency_type=dependency_type,
            condition=condition,
        )
        
        workflow.tasks.append(task)
        
        # 设置入口任务
        if workflow.entry_task is None and not task.dependencies:
            workflow.entry_task = task.task_id
        
        return task
    
    def get_task(self, workflow: WorkflowDefinition, task_id: str) -> Optional[AgentTask]:
        """获取任务.
        
        Args:
            workflow: 工作流
            task_id: 任务ID
            
        Returns:
            任务或None
        """
        for task in workflow.tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def get_ready_tasks(
        self,
        workflow: WorkflowDefinition,
        completed_tasks: Set[str],
    ) -> List[AgentTask]:
        """获取可执行的任务.
        
        Args:
            workflow: 工作流
            completed_tasks: 已完成的任务ID集合
            
        Returns:
            可执行的任务列表
        """
        ready = []
        
        for task in workflow.tasks:
            if task.status != CollaborationStatus.PENDING:
                continue
            
            # 检查依赖
            if task.dependencies:
                if not all(dep in completed_tasks for dep in task.dependencies):
                    continue
            
            # 检查条件
            if task.condition and not task.condition({"completed": list(completed_tasks)}):
                continue
            
            ready.append(task)
        
        return ready
    
    def validate_workflow(self, workflow: WorkflowDefinition) -> Tuple[bool, List[str]]:
        """验证工作流.
        
        Args:
            workflow: 工作流
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 检查是否有任务
        if not workflow.tasks:
            errors.append("工作流没有任务")
            return False, errors
        
        # 检查入口任务
        if workflow.entry_task is None:
            errors.append("工作流没有入口任务")
        
        # 检查循环依赖
        task_ids = {t.task_id for t in workflow.tasks}
        for task in workflow.tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    errors.append(f"任务 {task.task_id} 依赖不存在的任务 {dep}")
        
        # 检查循环依赖（简化检测）
        visited: Set[str] = set()
        for task in workflow.tasks:
            if self._has_cycle(task, workflow, visited, set()):
                errors.append(f"检测到循环依赖")
                break
        
        return len(errors) == 0, errors
    
    def _has_cycle(
        self,
        task: AgentTask,
        workflow: WorkflowDefinition,
        visited: Set[str],
        path: Set[str],
    ) -> bool:
        """检测循环依赖."""
        if task.task_id in path:
            return True
        
        if task.task_id in visited:
            return False
        
        visited.add(task.task_id)
        path.add(task.task_id)
        
        for dep_id in task.dependencies:
            dep_task = self.get_task(workflow, dep_id)
            if dep_task and self._has_cycle(dep_task, workflow, visited, path):
                return True
        
        path.remove(task.task_id)
        return False
    
    def _load_templates(self) -> Dict[str, WorkflowDefinition]:
        """加载工作流模板."""
        templates = {}
        
        # 软件开发工作流模板
        dev_workflow = self.create_workflow(
            name="software_development",
            description="软件开发标准工作流",
        )
        
        # 添加任务
        req_task = self.add_task(
            dev_workflow,
            name="需求分析",
            agent_role=AgentRole.REQUIREMENT,
        )
        
        arch_task = self.add_task(
            dev_workflow,
            name="架构设计",
            agent_role=AgentRole.ARCHITECT,
            dependencies=[req_task.task_id],
        )
        
        dev_task = self.add_task(
            dev_workflow,
            name="代码开发",
            agent_role=AgentRole.DEVELOPER,
            dependencies=[arch_task.task_id],
        )
        
        test_task = self.add_task(
            dev_workflow,
            name="测试",
            agent_role=AgentRole.TESTER,
            dependencies=[dev_task.task_id],
        )
        
        review_task = self.add_task(
            dev_workflow,
            name="代码审查",
            agent_role=AgentRole.REVIEWER,
            dependencies=[dev_task.task_id],
        )
        
        doc_task = self.add_task(
            dev_workflow,
            name="文档生成",
            agent_role=AgentRole.DOCUMENTER,
            dependencies=[test_task.task_id, review_task.task_id],
        )
        
        templates["software_development"] = dev_workflow
        
        # Bug修复工作流模板
        bugfix_workflow = self.create_workflow(
            name="bugfix",
            description="Bug修复工作流",
        )
        
        fix_task = self.add_task(
            bugfix_workflow,
            name="Bug修复",
            agent_role=AgentRole.BUGFIX,
        )
        
        test_task2 = self.add_task(
            bugfix_workflow,
            name="测试验证",
            agent_role=AgentRole.TESTER,
            dependencies=[fix_task.task_id],
        )
        
        self.add_task(
            bugfix_workflow,
            name="文档更新",
            agent_role=AgentRole.DOCUMENTER,
            dependencies=[test_task2.task_id],
        )
        
        templates["bugfix"] = bugfix_workflow
        
        return templates
    
    def get_template(self, name: str) -> Optional[WorkflowDefinition]:
        """获取工作流模板.
        
        Args:
            name: 模板名称
            
        Returns:
            工作流模板或None
        """
        return self._templates.get(name)


class AgentCoordinator:
    """Agent协作器.
    
    协调多个Agent完成复杂任务。
    """
    
    def __init__(self, orchestrator: Optional[TaskOrchestrator] = None) -> None:
        self._orchestrator = orchestrator or TaskOrchestrator()
        self._contexts: Dict[str, CollaborationContext] = {}
        self._agent_instances: Dict[AgentRole, Any] = {}
    
    def register_agent(self, role: AgentRole, agent_instance: Any) -> None:
        """注册Agent实例.
        
        Args:
            role: Agent角色
            agent_instance: Agent实例
        """
        self._agent_instances[role] = agent_instance
    
    def start_workflow(
        self,
        workflow: WorkflowDefinition,
        initial_data: Optional[Dict] = None,
    ) -> CollaborationContext:
        """启动工作流.
        
        Args:
            workflow: 工作流定义
            initial_data: 初始数据
            
        Returns:
            协作上下文
        """
        # 验证工作流
        valid, errors = self._orchestrator.validate_workflow(workflow)
        if not valid:
            context = CollaborationContext(
                workflow=workflow,
                status=CollaborationStatus.FAILED,
            )
            context.errors = [("validation", str(errors))]
            return context
        
        # 创建上下文
        context = CollaborationContext(
            workflow=workflow,
            status=CollaborationStatus.RUNNING,
            shared_data=initial_data or {},
        )
        
        # 初始化待执行任务
        context.pending_tasks = [t.task_id for t in workflow.tasks]
        
        self._contexts[context.context_id] = context
        
        return context
    
    def execute_next(self, context: CollaborationContext) -> Optional[AgentTask]:
        """执行下一个任务.
        
        Args:
            context: 协作上下文
            
        Returns:
            执行的任务或None
        """
        if context.status != CollaborationStatus.RUNNING:
            return None
        
        workflow = context.workflow
        if not workflow:
            return None
        
        # 获取可执行任务
        completed = set(context.completed_tasks)
        ready_tasks = self._orchestrator.get_ready_tasks(workflow, completed)
        
        if not ready_tasks:
            # 检查是否全部完成
            if not context.pending_tasks:
                context.status = CollaborationStatus.COMPLETED
            return None
        
        # 选择第一个可执行任务
        task = ready_tasks[0]
        
        # 更新状态
        task.status = CollaborationStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        context.running_task = task.task_id
        context.pending_tasks.remove(task.task_id)
        
        # 执行任务
        try:
            result = self._execute_task(task, context)
            task.output_data = result
            task.status = CollaborationStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()
            context.results[task.task_id] = result
            context.completed_tasks.append(task.task_id)
        except Exception as e:
            task.status = CollaborationStatus.FAILED
            task.error_message = str(e)
            context.errors.append((task.task_id, str(e)))
        
        context.running_task = None
        
        return task
    
    def _execute_task(
        self,
        task: AgentTask,
        context: CollaborationContext,
    ) -> Dict[str, Any]:
        """执行单个任务.
        
        Args:
            task: 任务
            context: 上下文
            
        Returns:
            执行结果
        """
        # 获取Agent实例
        agent = self._agent_instances.get(task.agent_role)
        
        # 准备输入数据
        input_data = {**task.input_data}
        
        # 添加依赖任务的输出
        for dep_id in task.dependencies:
            if dep_id in context.results:
                input_data[f"dep_{dep_id}"] = context.results[dep_id]
        
        # 添加共享数据
        input_data["shared"] = context.shared_data
        
        if agent and hasattr(agent, 'process'):
            # 使用真实Agent执行
            from multi_agent_se.agents.runtime.base_agent import AgentContext
            from multi_agent_se.scheduler.task import Task
            
            agent_task = Task(
                task_id=task.task_id,
                task_type=task.agent_role.value,
                description=task.name,
            )
            
            agent_context = AgentContext(
                task=agent_task,
                input_data=input_data,
            )
            
            result = agent.process(agent_context)
            
            if result.success:
                return result.output or {}
            else:
                raise Exception(result.error_message or "Agent执行失败")
        else:
            # 模拟执行
            return {
                "task": task.name,
                "role": task.agent_role.value,
                "status": "simulated",
                "input_keys": list(input_data.keys()),
            }
    
    def execute_all(self, context: CollaborationContext) -> Dict[str, Any]:
        """执行所有任务.
        
        Args:
            context: 协作上下文
            
        Returns:
            执行结果
        """
        while context.status == CollaborationStatus.RUNNING:
            task = self.execute_next(context)
            if task is None:
                break
        
        return {
            "status": context.status.value,
            "completed_tasks": len(context.completed_tasks),
            "total_tasks": len(context.workflow.tasks) if context.workflow else 0,
            "results": context.results,
            "errors": context.errors,
        }
    
    def pause(self, context: CollaborationContext) -> bool:
        """暂停工作流.
        
        Args:
            context: 协作上下文
            
        Returns:
            是否成功
        """
        if context.status == CollaborationStatus.RUNNING:
            context.status = CollaborationStatus.PAUSED
            return True
        return False
    
    def resume(self, context: CollaborationContext) -> bool:
        """恢复工作流.
        
        Args:
            context: 协作上下文
            
        Returns:
            是否成功
        """
        if context.status == CollaborationStatus.PAUSED:
            context.status = CollaborationStatus.RUNNING
            return True
        return False
    
    def cancel(self, context: CollaborationContext) -> bool:
        """取消工作流.
        
        Args:
            context: 协作上下文
            
        Returns:
            是否成功
        """
        if context.status in (CollaborationStatus.RUNNING, CollaborationStatus.PAUSED):
            context.status = CollaborationStatus.CANCELLED
            return True
        return False
    
    def get_context(self, context_id: str) -> Optional[CollaborationContext]:
        """获取协作上下文.
        
        Args:
            context_id: 上下文ID
            
        Returns:
            上下文或None
        """
        return self._contexts.get(context_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        total = len(self._contexts)
        by_status: Dict[str, int] = {}
        
        for ctx in self._contexts.values():
            status = ctx.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            "total_workflows": total,
            "by_status": by_status,
            "registered_agents": [r.value for r in self._agent_instances.keys()],
        }
