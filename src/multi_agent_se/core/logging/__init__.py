"""日志系统 - 阶段28.

结构化日志记录：
- 多级日志（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- 多格式输出（纯文本/JSON/结构化）
- 多处理器（控制台/内存/文件）
- 上下文管理
"""

from multi_agent_se.core.logging.models import (
    LogLevel,
    LogFormat,
    LogRecord,
    LogContext,
    LogHandler,
    ConsoleHandler,
    MemoryHandler,
    FileHandler,
    create_record,
)

from multi_agent_se.core.logging.manager import (
    Logger,
    LogManager,
    log_manager,
    get_logger,
    debug,
    info,
    warning,
    error,
    critical,
    configure_logging,
)

__all__ = [
    # 模型
    "LogLevel",
    "LogFormat",
    "LogRecord",
    "LogContext",
    "LogHandler",
    "ConsoleHandler",
    "MemoryHandler",
    "FileHandler",
    "create_record",
    # 管理器
    "Logger",
    "LogManager",
    "log_manager",
    # 便捷函数
    "get_logger",
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "configure_logging",
]
