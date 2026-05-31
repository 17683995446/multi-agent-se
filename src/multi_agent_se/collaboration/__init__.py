"""协作模块 - 状态、调度、消息、协商."""

from multi_agent_se.collaboration.state import (
    SystemState, TaskState, BusinessState,
    TaskStatus, AgentRole, GraphState,
    create_initial_state, update_state,
)

from multi_agent_se.collaboration.state_machine import (
    StateLayer,
    StateTransition,
    TransitionResult,
    TaskStateMachine,
    StateAccessRecord,
    LayerStateManager,
    SystemStateManager,
    TaskStateManager,
    BusinessStateManager,
    SyncResult,
    StateSynchronizer,
)

__all__ = [
    # 状态定义
    "SystemState", "TaskState", "BusinessState",
    "TaskStatus", "AgentRole", "GraphState",
    "create_initial_state", "update_state",
    # 状态机
    "StateLayer",
    "StateTransition",
    "TransitionResult",
    "TaskStateMachine",
    "StateAccessRecord",
    "LayerStateManager",
    "SystemStateManager",
    "TaskStateManager",
    "BusinessStateManager",
    "SyncResult",
    "StateSynchronizer",
]
