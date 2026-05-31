"""代码执行结果定义 - 阶段21.

定义代码执行的结果封装：
- 执行状态
- 输出捕获
- 错误处理
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union


class ExecutionStatus(Enum):
    """执行状态."""
    PENDING = "pending"           # 待执行
    RUNNING = "running"           # 执行中
    SUCCESS = "success"           # 成功完成
    ERROR = "error"              # 执行错误
    TIMEOUT = "timeout"          # 超时
    MEMORY_LIMIT = "memory_limit"  # 内存超限
    SECURITY_VIOLATION = "security_violation"  # 安全违规
    IMPORT_ERROR = "import_error"  # 导入错误
    SYNTAX_ERROR = "syntax_error"  # 语法错误


@dataclass
class ExecutionLimits:
    """执行限制配置."""
    max_execution_time_seconds: float = 30.0  # 最大执行时间
    max_memory_mb: int = 512                   # 最大内存(MB)
    max_output_size_bytes: int = 1024 * 1024   # 最大输出(1MB)
    max_cpu_percent: Optional[float] = None    # 最大CPU使用率
    allow_network: bool = False                # 是否允许网络
    allow_file_write: bool = False             # 是否允许文件写入
    allowed_modules: Optional[List[str]] = None  # 允许导入的模块
    blocked_modules: List[str] = field(default_factory=lambda: [
        "os", "sys", "subprocess", "socket", "urllib", "http",
        "ftplib", "telnetlib", "pickle", "marshal", "ctypes",
    ])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_execution_time_seconds": self.max_execution_time_seconds,
            "max_memory_mb": self.max_memory_mb,
            "max_output_size_bytes": self.max_output_size_bytes,
            "max_cpu_percent": self.max_cpu_percent,
            "allow_network": self.allow_network,
            "allow_file_write": self.allow_file_write,
            "allowed_modules": self.allowed_modules,
            "blocked_modules": self.blocked_modules,
        }


@dataclass
class ExecutionResult:
    """代码执行结果.
    
    封装代码执行的完整结果
    """
    # 基本信息
    status: ExecutionStatus = ExecutionStatus.PENDING
    exit_code: int = 0
    
    # 输出
    stdout: str = ""
    stderr: str = ""
    
    # 执行信息
    execution_time_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    
    # 错误信息
    error_message: str = ""
    error_type: Optional[str] = None
    traceback: str = ""
    
    # 返回值（如果是函数调用）
    return_value: Any = None
    
    # 元数据
    executed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理."""
        # 根据状态设置退出码
        if self.status == ExecutionStatus.SUCCESS:
            self.exit_code = 0
        elif self.status in (ExecutionStatus.ERROR, ExecutionStatus.SYNTAX_ERROR):
            self.exit_code = 1
        elif self.status == ExecutionStatus.TIMEOUT:
            self.exit_code = 124  # 标准超时退出码
        elif self.status == ExecutionStatus.MEMORY_LIMIT:
            self.exit_code = 137  # 标准内存超限退出码
        elif self.status == ExecutionStatus.SECURITY_VIOLATION:
            self.exit_code = 126
    
    @property
    def is_success(self) -> bool:
        """是否执行成功."""
        return self.status == ExecutionStatus.SUCCESS
    
    @property
    def has_error(self) -> bool:
        """是否有错误."""
        return self.status in (
            ExecutionStatus.ERROR,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.MEMORY_LIMIT,
            ExecutionStatus.SECURITY_VIOLATION,
            ExecutionStatus.IMPORT_ERROR,
            ExecutionStatus.SYNTAX_ERROR,
        )
    
    @property
    def combined_output(self) -> str:
        """合并的标准输出和错误输出."""
        output = self.stdout
        if self.stderr:
            if output:
                output += "\n"
            output += f"[STDERR]\n{self.stderr}"
        return output
    
    @property
    def truncated_stdout(self, max_length: int = 1000) -> str:
        """截断的标准输出."""
        if len(self.stdout) <= max_length:
            return self.stdout
        return self.stdout[:max_length] + f"\n... ({len(self.stdout) - max_length} more chars)"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "status": self.status.value,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "combined_output": self.combined_output,
            "execution_time_seconds": self.execution_time_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "traceback": self.traceback,
            "return_value": str(self.return_value) if self.return_value is not None else None,
            "executed_at": self.executed_at.isoformat(),
            "is_success": self.is_success,
            "has_error": self.has_error,
            "metadata": self.metadata,
        }
    
    @classmethod
    def success(
        cls,
        stdout: str = "",
        return_value: Any = None,
        execution_time: float = 0.0,
    ) -> "ExecutionResult":
        """工厂方法：创建成功结果."""
        return cls(
            status=ExecutionStatus.SUCCESS,
            stdout=stdout,
            return_value=return_value,
            execution_time_seconds=execution_time,
        )
    
    @classmethod
    def error(
        cls,
        error_message: str,
        error_type: Optional[str] = None,
        traceback: str = "",
        stderr: str = "",
    ) -> "ExecutionResult":
        """工厂方法：创建错误结果."""
        return cls(
            status=ExecutionStatus.ERROR,
            error_message=error_message,
            error_type=error_type,
            traceback=traceback,
            stderr=stderr,
        )
    
    @classmethod
    def timeout(
        cls,
        limit_seconds: float,
        partial_stdout: str = "",
    ) -> "ExecutionResult":
        """工厂方法：创建超时结果."""
        return cls(
            status=ExecutionStatus.TIMEOUT,
            error_message=f"Execution timed out after {limit_seconds} seconds",
            stdout=partial_stdout,
        )
    
    @classmethod
    def security_violation(
        cls,
        violation: str,
    ) -> "ExecutionResult":
        """工厂方法：创建安全违规结果."""
        return cls(
            status=ExecutionStatus.SECURITY_VIOLATION,
            error_message=f"Security violation: {violation}",
            error_type="SecurityError",
        )


# ========== 便捷函数 ==========

def format_execution_result(result: ExecutionResult, verbose: bool = False) -> str:
    """格式化执行结果.
    
    Args:
        result: 执行结果
        verbose: 是否详细输出
        
    Returns:
        格式化字符串
    """
    lines = [
        f"Status: {result.status.value}",
        f"Exit Code: {result.exit_code}",
        f"Execution Time: {result.execution_time_seconds:.3f}s",
    ]
    
    if result.memory_usage_mb > 0:
        lines.append(f"Memory Usage: {result.memory_usage_mb:.2f} MB")
    
    if result.stdout:
        lines.append(f"\nSTDOUT:\n{result.stdout}")
    
    if result.stderr:
        lines.append(f"\nSTDERR:\n{result.stderr}")
    
    if result.has_error and result.error_message:
        lines.append(f"\nError: {result.error_message}")
    
    if verbose and result.traceback:
        lines.append(f"\nTraceback:\n{result.traceback}")
    
    return "\n".join(lines)
