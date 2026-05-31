"""代码执行器 - 阶段21.

实现安全代码执行环境
"""

from multi_agent_se.executor.result import (
    ExecutionStatus,
    ExecutionResult,
    ExecutionLimits,
)

from multi_agent_se.executor.sandbox import (
    SandboxError,
    SecurityError,
    TimeoutError,
    CodeSandbox,
    create_sandbox,
    quick_execute,
)

__all__ = [
    # 执行结果
    "ExecutionStatus",
    "ExecutionResult",
    "ExecutionLimits",
    # 沙箱
    "SandboxError",
    "SecurityError",
    "TimeoutError",
    "CodeSandbox",
    "create_sandbox",
    "quick_execute",
]
