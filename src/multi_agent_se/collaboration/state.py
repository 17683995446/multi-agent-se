"""系统状态定义模块 - 阶段3.

遵循第一性原理：状态分离公理（业务/任务/系统三层隔离）
"""

from typing import Any, Dict, List, Optional, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
import operator


class TaskStatus(Enum):
    """任务状态枚举."""
    PENDING = "pending"           # 待处理
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class AgentRole(Enum):
    """Agent角色枚举."""
    CONTROLLER = "controller"     # 总控
    REQUIREMENT = "requirement"   # 需求拆解
    ARCHITECT = "architect"       # 架构
    DEVELOPER = "developer"       # 开发
    BUGFIX = "bugfix"             # 缺陷排查
    REVIEWER = "reviewer"         # 评审
    TESTER = "tester"             # 测试
    DOCUMENTER = "documenter"     # 文档


# ========== 三层状态定义 ==========

@dataclass
class SystemState:
    """系统层状态 - 全局运行时状态."""
    session_id: str = ""                          # 会话ID
    trace_id: str = ""                            # 链路追踪ID
    timestamp: str = ""                           # 时间戳
    env: str = "development"                      # 运行环境
    version: str = "0.1.0"                        # 系统版本


@dataclass
class TaskState:
    """任务层状态 - 任务执行状态."""
    task_id: str = ""                             # 任务ID
    task_type: str = ""                           # 任务类型
    status: TaskStatus = TaskStatus.PENDING       # 任务状态
    priority: int = 0                             # 优先级
    progress: float = 0.0                         # 进度(0-100)
    current_stage: str = ""                       # 当前阶段
    assigned_agent: Optional[AgentRole] = None    # 分配的Agent
    parent_task_id: Optional[str] = None          # 父任务ID
    sub_tasks: List[str] = field(default_factory=list)  # 子任务列表


@dataclass
class BusinessState:
    """业务层状态 - 业务数据状态."""
    input_data: Dict[str, Any] = field(default_factory=dict)    # 输入数据
    output_data: Dict[str, Any] = field(default_factory=dict)   # 输出数据
    context: Dict[str, Any] = field(default_factory=dict)       # 上下文
    artifacts: List[str] = field(default_factory=list)          # 产物列表
    metadata: Dict[str, Any] = field(default_factory=dict)      # 元数据


# ========== LangGraph状态定义 ==========

class GraphState(TypedDict):
    """LangGraph图状态 - 用于StateGraph.
    
    遵循状态分离公理，将三层状态扁平化存储
    """
    # 系统层
    session_id: str
    trace_id: str
    
    # 任务层
    task_id: str
    task_type: str
    status: str
    priority: int
    progress: float
    current_stage: str
    assigned_agent: Optional[str]
    
    # 业务层
    input_data: Annotated[Dict[str, Any], operator.or_]
    output_data: Annotated[Dict[str, Any], operator.or_]
    context: Annotated[Dict[str, Any], operator.or_]
    messages: Annotated[List[Dict[str, Any]], operator.add]  # 消息历史
    artifacts: Annotated[List[str], operator.add]
    
    # 控制流
    next_stage: Optional[str]
    should_continue: bool
    error: Optional[str]


def create_initial_state(
    task_type: str = "default",
    input_data: Optional[Dict[str, Any]] = None
) -> GraphState:
    """创建初始状态.
    
    Args:
        task_type: 任务类型
        input_data: 输入数据
        
    Returns:
        初始GraphState
    """
    import uuid
    from datetime import datetime
    
    return {
        # 系统层
        "session_id": str(uuid.uuid4()),
        "trace_id": str(uuid.uuid4()),
        
        # 任务层
        "task_id": str(uuid.uuid4()),
        "task_type": task_type,
        "status": TaskStatus.PENDING.value,
        "priority": 0,
        "progress": 0.0,
        "current_stage": "init",
        "assigned_agent": None,
        
        # 业务层
        "input_data": input_data or {},
        "output_data": {},
        "context": {},
        "messages": [],
        "artifacts": [],
        
        # 控制流
        "next_stage": None,
        "should_continue": True,
        "error": None,
    }


def update_state(
    state: GraphState,
    updates: Dict[str, Any]
) -> GraphState:
    """更新状态.
    
    Args:
        state: 当前状态
        updates: 更新内容
        
    Returns:
        更新后的状态
    """
    new_state = dict(state)
    new_state.update(updates)
    return new_state


def get_state_summary(state: GraphState) -> Dict[str, Any]:
    """获取状态摘要.
    
    Args:
        state: 当前状态
        
    Returns:
        状态摘要
    """
    return {
        "task_id": state["task_id"],
        "task_type": state["task_type"],
        "status": state["status"],
        "progress": state["progress"],
        "current_stage": state["current_stage"],
        "assigned_agent": state["assigned_agent"],
        "message_count": len(state["messages"]),
        "artifact_count": len(state["artifacts"]),
        "has_error": state["error"] is not None,
    }
