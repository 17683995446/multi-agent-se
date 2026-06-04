"""配置管理器 - 阶段25.

分层配置管理：
- 多格式加载（YAML/TOML/JSON/ENV）
- 分层合并（系统→全局→项目→本地→环境→运行时）
- 配置验证
- 配置快照
- 配置变更监听

向后兼容：
- Settings / settings 从 settings.py 导出
"""

from multi_agent_se.core.config.models import (
    ConfigField,
    ConfigFormat,
    ConfigLevel,
    ConfigSnapshot,
    ConfigSource,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    create_field,
)

from multi_agent_se.core.config.loader import (
    ConfigManager,
    ConfigParser,
    deep_merge,
    flatten_dict,
    unflatten_dict,
    create_config,
)

# 向后兼容：优先从 settings.py 导出 Settings，pydantic 不可用时从 simple_settings 回退
try:
    from multi_agent_se.core.config.settings import Settings, settings  # noqa: E402
except ImportError:
    from multi_agent_se.core.config.simple_settings import SimpleSettings as Settings, settings  # noqa: E402

__all__ = [
    # 模型
    "ConfigField",
    "ConfigFormat",
    "ConfigLevel",
    "ConfigSnapshot",
    "ConfigSource",
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
    "create_field",
    # 加载器
    "ConfigManager",
    "ConfigParser",
    "deep_merge",
    "flatten_dict",
    "unflatten_dict",
    "create_config",
    # 向后兼容
    "Settings",
    "settings",
]
