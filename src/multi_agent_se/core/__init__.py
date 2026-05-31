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

# 初始化日志系统
configure_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    log_file=settings.log_file,
)
logger = get_logger("mase")
