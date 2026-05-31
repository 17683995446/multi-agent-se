"""全局信息显式化机制 - 阶段14.

消灭隐式状态，建立显式化机制：
- 隐式状态扫描
- 显式化转换
- 全局状态注册
- 状态变更追踪
"""

from multi_agent_se.core.explicitness.scanner import (
    ImplicitStateType,
    ImplicitState,
    ScanResult,
    StateScanner,
    scan_module,
)

from multi_agent_se.core.explicitness.registry import (
    StateScope,
    ExplicitState,
    StateRegistry,
    global_state_registry,
)

from multi_agent_se.core.explicitness.tracer import (
    ChangeType,
    StateChange,
    StateTracer,
    TraceQuery,
    global_state_tracer,
)

__all__ = [
    # 扫描器
    "ImplicitStateType",
    "ImplicitState",
    "ScanResult",
    "StateScanner",
    "scan_module",
    # 注册表
    "StateScope",
    "ExplicitState",
    "StateRegistry",
    "global_state_registry",
    # 追踪器
    "ChangeType",
    "StateChange",
    "StateTracer",
    "TraceQuery",
    "global_state_tracer",
]
