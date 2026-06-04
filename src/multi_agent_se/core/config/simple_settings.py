"""纯Python配置管理 - 第48阶段.

无pydantic依赖的配置系统，作为fallback使用。
遵循第一性原理：最小依赖、最大兼容。
"""

import os
from typing import Any, Dict, Optional


class SimpleSettings:
    """纯Python配置类.
    
    功能等价于pydantic-based Settings，但无外部依赖。
    """
    
    # 应用信息
    app_name: str = "multi-agent-se"
    app_version: str = "0.1.0"
    app_env: str = "development"
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "console"
    log_file: Optional[str] = None
    
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
    
    def __init__(self) -> None:
        """初始化并从环境变量加载."""
        self._load_from_env()
    
    def _load_from_env(self) -> None:
        """从环境变量加载配置."""
        env_mappings = {
            "app_env": "APP_ENV",
            "log_level": "LOG_LEVEL",
            "log_format": "LOG_FORMAT",
            "log_file": "LOG_FILE",
            "autogen_timeout": "AUTOGEN_TIMEOUT",
            "autogen_max_turns": "AUTOGEN_MAX_TURNS",
            "min_test_coverage": "MIN_TEST_COVERAGE",
            "max_complexity": "MAX_COMPLEXITY",
            "max_line_length": "MAX_LINE_LENGTH",
        }
        
        for attr_name, env_name in env_mappings.items():
            env_value = os.environ.get(env_name)
            if env_value is not None:
                # 类型转换
                current_value = getattr(self, attr_name)
                if isinstance(current_value, bool):
                    setattr(self, attr_name, env_value.lower() in ("true", "1", "yes"))
                elif isinstance(current_value, int):
                    try:
                        setattr(self, attr_name, int(env_value))
                    except ValueError:
                        pass
                elif isinstance(current_value, float):
                    try:
                        setattr(self, attr_name, float(env_value))
                    except ValueError:
                        pass
                else:
                    setattr(self, attr_name, env_value)
    
    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """从字典加载配置."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_development(self) -> bool:
        """是否为开发环境."""
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        """是否为生产环境."""
        return self.app_env == "production"
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典."""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "app_env": self.app_env,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "log_file": self.log_file,
            "langgraph_checkpoint": self.langgraph_checkpoint,
            "langgraph_verbose": self.langgraph_verbose,
            "autogen_timeout": self.autogen_timeout,
            "autogen_max_turns": self.autogen_max_turns,
            "tree_sitter_lib_path": self.tree_sitter_lib_path,
            "min_test_coverage": self.min_test_coverage,
            "max_complexity": self.max_complexity,
            "max_line_length": self.max_line_length,
        }
    
    def __repr__(self) -> str:
        return f"SimpleSettings(env={self.app_env}, log_level={self.log_level})"


# 尝试使用pydantic Settings，失败则使用SimpleSettings
try:
    from multi_agent_se.core.config.settings import Settings as _PydanticSettings
    
    class CompatibleSettings(_PydanticSettings):
        """兼容层：优先使用pydantic Settings."""
        pass
    
    settings = CompatibleSettings()
    _SETTINGS_BACKEND = "pydantic"
    
except ImportError:
    # pydantic不可用，使用纯Python实现
    settings = SimpleSettings()
    _SETTINGS_BACKEND = "simple"


def get_settings_backend() -> str:
    """获取当前配置后端."""
    return _SETTINGS_BACKEND
