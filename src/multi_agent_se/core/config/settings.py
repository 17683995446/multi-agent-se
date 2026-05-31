"""全局配置管理模块 - 阶段10.

正交拆分后：本模块只负责Settings配置类定义
异常体系 → core.exceptions
日志管理 → core.logging
路径工具 → core.paths
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


# ========== 配置类 ==========
class Settings(BaseSettings):
    """系统配置类.

    基于pydantic-settings，支持.env文件和环境变量覆盖
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用信息
    app_name: str = "multi-agent-se"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development", alias="APP_ENV")

    # 日志配置
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="console", alias="LOG_FORMAT")
    log_file: Optional[str] = Field(default=None, alias="LOG_FILE")

    # LangGraph配置
    langgraph_checkpoint: bool = True
    langgraph_verbose: bool = False

    # AutoGen配置
    autogen_timeout: int = 60
    autogen_max_turns: int = 10

    # 代码解析配置
    tree_sitter_lib_path: Optional[str] = None

    # 质量门禁
    min_test_coverage: float = 80.0
    max_complexity: int = 10
    max_line_length: int = 100

    @property
    def is_development(self) -> bool:
        """是否为开发环境."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """是否为生产环境."""
        return self.app_env == "production"


# 全局配置实例
settings = Settings()


# ========== 向后兼容：从子模块重新导出 ==========
# test_config.py 等已有代码使用 from core.config import MASEError 等方式
from multi_agent_se.core.exceptions import (  # noqa: E402, F811
    MASEError,
    ConfigurationError,
    AgentError,
    format_error,
)
from multi_agent_se.core.paths import (  # noqa: E402, F811
    get_project_path,
    get_config_path,
    ensure_dir,
)
from multi_agent_se.core.logging import (  # noqa: E402, F811
    get_logger as _get_logger,
    configure_logging,
)

# 初始化日志
configure_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    log_file=settings.log_file,
)
logger = _get_logger("mase")
