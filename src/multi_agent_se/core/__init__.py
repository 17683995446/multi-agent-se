"""MASE核心模块 - 阶段10.

统一导出入口，正交拆分：
- config: Settings配置类
- exceptions: 异常体系
- logging: 日志管理
- paths: 路径工具
- dependency_graph: 依赖关系图
"""

# 配置
from multi_agent_se.core.config import Settings, settings

# 异常
from multi_agent_se.core.exceptions import (
    MASEError,
    ConfigurationError,
    ConfigurationNotFoundError,
    AgentError,
    AgentTimeoutError,
    AgentCommunicationError,
    SchedulerError,
    CyclicDependencyError,
    QualityError,
    CoverageThresholdError,
    ParseError,
    UnsupportedLanguageError,
    format_error,
    get_error_hierarchy,
)

# 日志
from multi_agent_se.core.logging import (
    LogManager,
    get_logger,
    configure_logging,
)

# 路径
from multi_agent_se.core.paths import (
    PathManager,
    path_manager,
    get_project_path,
    get_config_path,
    ensure_dir,
)

__all__ = [
    # 配置
    "Settings",
    "settings",
    # 异常
    "MASEError",
    "ConfigurationError",
    "ConfigurationNotFoundError",
    "AgentError",
    "AgentTimeoutError",
    "AgentCommunicationError",
    "SchedulerError",
    "CyclicDependencyError",
    "QualityError",
    "CoverageThresholdError",
    "ParseError",
    "UnsupportedLanguageError",
    "format_error",
    "get_error_hierarchy",
    # 日志
    "LogManager",
    "get_logger",
    "configure_logging",
    "logger",
    # 路径
    "PathManager",
    "path_manager",
    "get_project_path",
    "get_config_path",
    "ensure_dir",
]

# 延迟初始化日志系统，避免在导入阶段强制加载配置（支持无pydantic环境）
_logger_initialized = False
logger = None


def _ensure_logging_initialized():
    """确保日志系统已初始化（惰性加载）."""
    global _logger_initialized, logger
    if not _logger_initialized:
        try:
            configure_logging(
                log_level=settings.log_level,
                log_format=getattr(settings, "log_format", "console"),
                log_file=getattr(settings, "log_file", None),
            )
            logger = get_logger("mase")
        except Exception:
            # 即使日志初始化失败也不应阻断系统启动
            logger = None
        _logger_initialized = True
    return logger


# 首次访问时触发初始化（保持向后兼容）
_ensure_logging_initialized()
