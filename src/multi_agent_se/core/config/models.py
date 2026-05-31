"""配置模型定义 - 阶段25.

定义配置管理的数据结构：
- 配置源类型
- 配置层级
- 配置项定义
- 配置验证结果
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


class ConfigSource(Enum):
    """配置来源."""
    DEFAULT = "default"       # 默认值
    FILE = "file"             # 配置文件 (YAML/TOML/JSON)
    ENV = "env"               # 环境变量
    CLI = "cli"               # 命令行参数
    RUNTIME = "runtime"       # 运行时动态修改


class ConfigFormat(Enum):
    """配置文件格式."""
    YAML = "yaml"
    TOML = "toml"
    JSON = "json"
    ENV = "env"
    INI = "ini"


class ConfigLevel(Enum):
    """配置层级（优先级从低到高）."""
    SYSTEM = 0       # 系统级默认
    GLOBAL = 1       # 全局用户配置
    PROJECT = 2      # 项目级配置
    LOCAL = 3        # 本地覆盖
    ENVIRONMENT = 4  # 环境变量
    RUNTIME = 5      # 运行时覆盖


class ValidationSeverity(Enum):
    """验证严重程度."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# ========== 配置项定义 ==========

@dataclass
class ConfigField:
    """配置字段定义."""
    key: str = ""                       # 配置键（支持点号分隔，如 "server.port"）
    value: Any = None                   # 默认值
    field_type: str = "str"             # 类型标识
    description: str = ""               # 描述
    required: bool = False              # 是否必填
    choices: Optional[List[Any]] = None # 可选值列表
    min_value: Optional[float] = None   # 最小值
    max_value: Optional[float] = None   # 最大值
    pattern: Optional[str] = None       # 正则匹配
    source: ConfigSource = ConfigSource.DEFAULT
    level: ConfigLevel = ConfigLevel.SYSTEM

    def validate(self, value: Any) -> List[str]:
        """验证值是否合法，返回错误列表."""
        errors = []

        # 必填检查
        if self.required and value is None:
            errors.append(f"配置项 '{self.key}' 为必填项")
            return errors

        if value is None:
            return errors

        # 类型检查
        type_errors = self._check_type(value)
        errors.extend(type_errors)

        # 选择范围检查
        if self.choices is not None and value not in self.choices:
            errors.append(
                f"配置项 '{self.key}' 的值 '{value}' 不在允许范围 {self.choices} 内"
            )

        # 数值范围检查
        if isinstance(value, (int, float)):
            if self.min_value is not None and value < self.min_value:
                errors.append(f"配置项 '{self.key}' 的值 {value} 小于最小值 {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                errors.append(f"配置项 '{self.key}' 的值 {value} 大于最大值 {self.max_value}")

        # 正则匹配
        if self.pattern is not None and isinstance(value, str):
            import re
            if not re.match(self.pattern, value):
                errors.append(f"配置项 '{self.key}' 的值 '{value}' 不匹配模式 '{self.pattern}'")

        return errors

    def _check_type(self, value: Any) -> List[str]:
        """类型检查."""
        type_map = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "str_or_none": (str, type(None)),
        }
        expected = type_map.get(self.field_type)
        if expected and not isinstance(value, expected):
            return [f"配置项 '{self.key}' 期望类型 {self.field_type}，实际为 {type(value).__name__}"]
        return []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "type": self.field_type,
            "description": self.description,
            "required": self.required,
            "choices": self.choices,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "source": self.source.value,
            "level": self.level.value,
        }


# ========== 配置验证结果 ==========

@dataclass
class ValidationIssue:
    """验证问题."""
    key: str = ""
    message: str = ""
    severity: ValidationSeverity = ValidationSeverity.ERROR
    current_value: Any = None
    expected: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "message": self.message,
            "severity": self.severity.value,
            "current_value": repr(self.current_value),
            "expected": self.expected,
        }


@dataclass
class ValidationResult:
    """配置验证结果."""
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return all(i.severity != ValidationSeverity.ERROR for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)

    def add_error(self, key: str, message: str, current_value: Any = None) -> None:
        self.issues.append(ValidationIssue(
            key=key, message=message,
            severity=ValidationSeverity.ERROR,
            current_value=current_value,
        ))

    def add_warning(self, key: str, message: str, current_value: Any = None) -> None:
        self.issues.append(ValidationIssue(
            key=key, message=message,
            severity=ValidationSeverity.WARNING,
            current_value=current_value,
        ))

    def merge(self, other: "ValidationResult") -> None:
        self.issues.extend(other.issues)

    def format_summary(self) -> str:
        parts = [f"验证结果: {'通过' if self.is_valid else '失败'}"]
        if self.error_count:
            parts.append(f"错误: {self.error_count}")
        if self.warning_count:
            parts.append(f"警告: {self.warning_count}")
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
        }


# ========== 配置快照 ==========

@dataclass
class ConfigSnapshot:
    """配置快照 - 记录某时刻的配置状态."""
    name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    config: Dict[str, Any] = field(default_factory=dict)
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "config": self.config,
            "source": self.source,
        }


# ========== 便捷函数 ==========

def create_field(
    key: str,
    default: Any = None,
    field_type: str = "str",
    description: str = "",
    required: bool = False,
) -> ConfigField:
    """创建配置字段的便捷函数."""
    return ConfigField(
        key=key,
        value=default,
        field_type=field_type,
        description=description,
        required=required,
    )
