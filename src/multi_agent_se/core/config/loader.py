"""配置加载器 - 阶段25.

提供分层配置管理能力：
- 多格式加载（YAML/TOML/JSON/ENV）
- 分层合并（系统→全局→项目→本地→环境→运行时）
- 配置验证
- 配置快照
- 配置变更监听
"""

import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from multi_agent_se.core.config.models import (
    ConfigField,
    ConfigFormat,
    ConfigLevel,
    ConfigSnapshot,
    ConfigSource,
    ValidationResult,
    ValidationSeverity,
    create_field,
)


# ========== 深度合并工具 ==========

def deep_merge(base: Dict, override: Dict) -> Dict:
    """深度合并两个字典，override覆盖base.

    Args:
        base: 基础字典
        override: 覆盖字典

    Returns:
        合并后的新字典
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if (key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """将嵌套字典展平为点号分隔的键.

    Args:
        d: 嵌套字典
        parent_key: 父键前缀
        sep: 分隔符

    Returns:
        展平后的字典
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """将展平的字典还原为嵌套字典.

    Args:
        d: 展平字典
        sep: 分隔符

    Returns:
        嵌套字典
    """
    result: Dict[str, Any] = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


# ========== 文件解析器 ==========

class ConfigParser:
    """配置文件解析器."""

    @staticmethod
    def parse_yaml(content: str) -> Dict[str, Any]:
        """解析YAML."""
        try:
            import yaml
            return yaml.safe_load(content) or {}
        except ImportError:
            raise RuntimeError("PyYAML未安装，请执行: pip install pyyaml")
        except Exception as e:
            raise ValueError(f"YAML解析失败: {e}")

    @staticmethod
    def parse_json(content: str) -> Dict[str, Any]:
        """解析JSON."""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {e}")

    @staticmethod
    def parse_toml(content: str) -> Dict[str, Any]:
        """解析TOML."""
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                raise RuntimeError("tomllib/tomli未安装")
        try:
            return tomllib.loads(content)
        except Exception as e:
            raise ValueError(f"TOML解析失败: {e}")

    @staticmethod
    def parse_env(content: str) -> Dict[str, Any]:
        """解析.env文件.

        支持: KEY=VALUE, KEY="VALUE", export KEY=VALUE
        """
        result: Dict[str, Any] = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # 去掉export前缀
            if line.startswith("export "):
                line = line[7:].strip()
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
            if match:
                key = match.group(1)
                value = match.group(2).strip()
                # 去掉引号
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                # 类型推断
                value = ConfigParser._infer_type(value)
                result[key] = value
        return result

    @staticmethod
    def _infer_type(value: str) -> Any:
        """推断值的类型."""
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        if value.lower() == "null" or value.lower() == "none":
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    @staticmethod
    def detect_format(file_path: str) -> Optional[ConfigFormat]:
        """根据文件扩展名检测格式."""
        path = Path(file_path)
        # .env 文件名本身就是扩展名
        if path.name == ".env" or path.suffix == ".env":
            return ConfigFormat.ENV
        ext = path.suffix.lower()
        format_map = {
            ".yaml": ConfigFormat.YAML,
            ".yml": ConfigFormat.YAML,
            ".json": ConfigFormat.JSON,
            ".toml": ConfigFormat.TOML,
        }
        return format_map.get(ext)

    @staticmethod
    def parse(content: str, fmt: ConfigFormat) -> Dict[str, Any]:
        """根据格式解析内容."""
        parsers = {
            ConfigFormat.YAML: ConfigParser.parse_yaml,
            ConfigFormat.JSON: ConfigParser.parse_json,
            ConfigFormat.TOML: ConfigParser.parse_toml,
            ConfigFormat.ENV: ConfigParser.parse_env,
        }
        parser = parsers.get(fmt)
        if parser is None:
            raise ValueError(f"不支持的配置格式: {fmt}")
        return parser(content)


# ========== 配置管理器 ==========

class ConfigManager:
    """配置管理器.

    分层配置管理：
    1. 加载默认配置
    2. 加载配置文件（按层级合并）
    3. 加载环境变量
    4. 运行时覆盖
    """

    def __init__(self, app_name: str = "multi-agent-se") -> None:
        self.app_name = app_name
        self._layers: Dict[ConfigLevel, Dict[str, Any]] = {}
        self._fields: Dict[str, ConfigField] = {}
        self._snapshots: List[ConfigSnapshot] = []
        self._watchers: Dict[str, List[Callable]] = {}
        self._resolved: Optional[Dict[str, Any]] = None

    # ========== 配置注册 ==========

    def register_field(self, field: ConfigField) -> None:
        """注册配置字段定义."""
        self._fields[field.key] = field
        self._invalidate_cache()

    def register_fields(self, fields: List[ConfigField]) -> None:
        """批量注册配置字段."""
        for f in fields:
            self.register_field(f)

    def register_schema(self, schema: Dict[str, Any]) -> None:
        """从字典注册配置schema.

        Args:
            schema: 格式为 {"key": {"default": ..., "type": ..., "description": ...}}
        """
        for key, definition in schema.items():
            self.register_field(ConfigField(
                key=key,
                value=definition.get("default"),
                field_type=definition.get("type", "str"),
                description=definition.get("description", ""),
                required=definition.get("required", False),
                choices=definition.get("choices"),
                min_value=definition.get("min"),
                max_value=definition.get("max"),
                pattern=definition.get("pattern"),
            ))

    # ========== 配置加载 ==========

    def load_defaults(self, defaults: Dict[str, Any]) -> None:
        """加载默认配置."""
        self._layers[ConfigLevel.SYSTEM] = copy.deepcopy(defaults)
        self._invalidate_cache()

    def load_file(
        self,
        file_path: Union[str, Path],
        level: ConfigLevel = ConfigLevel.PROJECT,
    ) -> None:
        """从文件加载配置.

        Args:
            file_path: 文件路径
            level: 配置层级
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return

        content = file_path.read_text(encoding="utf-8")
        fmt = ConfigParser.detect_format(str(file_path))
        if fmt is None:
            return

        data = ConfigParser.parse(content, fmt)
        self._layers[level] = deep_merge(self._layers.get(level, {}), data)
        self._invalidate_cache()

    def load_dict(
        self,
        data: Dict[str, Any],
        level: ConfigLevel = ConfigLevel.RUNTIME,
    ) -> None:
        """从字典加载配置."""
        self._layers[level] = deep_merge(self._layers.get(level, {}), data)
        self._invalidate_cache()

    def load_env_vars(
        self,
        prefix: str = "",
        mapping: Optional[Dict[str, str]] = None,
    ) -> None:
        """从环境变量加载配置.

        Args:
            prefix: 环境变量前缀（如 "MASE_"）
            mapping: 环境变量名到配置键的映射
        """
        env_data: Dict[str, Any] = {}

        if mapping:
            for env_key, config_key in mapping.items():
                value = os.environ.get(env_key)
                if value is not None:
                    env_data[config_key] = ConfigParser._infer_type(value)
        else:
            pfx = prefix.upper()
            for key, value in os.environ.items():
                if pfx and not key.startswith(pfx):
                    continue
                # MASE_SERVER_PORT -> server.port
                config_key = key.lower()
                if pfx:
                    config_key = config_key[len(pfx):].lstrip("_")
                config_key = config_key.replace("__", ".").replace("_", ".")
                env_data[config_key] = ConfigParser._infer_type(value)

        if env_data:
            self._layers[ConfigLevel.ENVIRONMENT] = deep_merge(
                self._layers.get(ConfigLevel.ENVIRONMENT, {}), env_data
            )
            self._invalidate_cache()

    # ========== 配置访问 ==========

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的嵌套键）.

        Args:
            key: 配置键（如 "server.port"）
            default: 默认值
        """
        resolved = self._resolve()
        return self._get_nested(resolved, key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值（运行时覆盖）.

        Args:
            key: 配置键
            value: 值
        """
        old_value = self.get(key)
        nested = unflatten_dict({key: value})
        self._layers[ConfigLevel.RUNTIME] = deep_merge(
            self._layers.get(ConfigLevel.RUNTIME, {}), nested
        )
        self._invalidate_cache()

        # 触发变更监听
        if old_value != value:
            self._notify_watchers(key, old_value, value)

    def has(self, key: str) -> bool:
        """检查配置键是否存在."""
        resolved = self._resolve()
        return self._has_nested(resolved, key)

    def keys(self, prefix: str = "") -> List[str]:
        """获取配置键列表."""
        resolved = self._resolve()
        flat = flatten_dict(resolved)
        if prefix:
            return [k for k in flat if k.startswith(prefix)]
        return list(flat.keys())

    def all(self) -> Dict[str, Any]:
        """获取所有配置（合并后）."""
        return copy.deepcopy(self._resolve())

    # ========== 配置验证 ==========

    def validate(self) -> ValidationResult:
        """验证所有已注册的配置字段."""
        result = ValidationResult()
        resolved = self._resolve()
        flat = flatten_dict(resolved)

        for key, field_def in self._fields.items():
            value = flat.get(key)
            errors = field_def.validate(value)
            for err in errors:
                result.add_error(key, err, value)

        return result

    # ========== 快照管理 ==========

    def snapshot(self, name: str = "") -> ConfigSnapshot:
        """创建配置快照."""
        snap = ConfigSnapshot(
            name=name or f"snapshot_{len(self._snapshots)}",
            config=copy.deepcopy(self._resolve()),
            source="current",
        )
        self._snapshots.append(snap)
        return snap

    def restore(self, snapshot: ConfigSnapshot) -> None:
        """从快照恢复配置."""
        self._layers[ConfigLevel.RUNTIME] = copy.deepcopy(snapshot.config)
        self._invalidate_cache()

    def get_snapshots(self) -> List[ConfigSnapshot]:
        """获取所有快照."""
        return list(self._snapshots)

    # ========== 变更监听 ==========

    def watch(self, key: str, callback: Callable[[str, Any, Any], None]) -> None:
        """监听配置变更.

        Args:
            key: 配置键
            callback: 回调函数 (key, old_value, new_value)
        """
        if key not in self._watchers:
            self._watchers[key] = []
        self._watchers[key].append(callback)

    def unwatch(self, key: str, callback: Optional[Callable] = None) -> None:
        """取消监听."""
        if key not in self._watchers:
            return
        if callback is None:
            self._watchers[key] = []
        else:
            self._watchers[key] = [cb for cb in self._watchers[key] if cb != callback]

    def _notify_watchers(self, key: str, old_value: Any, new_value: Any) -> None:
        """通知监听器."""
        for cb in self._watchers.get(key, []):
            try:
                cb(key, old_value, new_value)
            except Exception:
                pass

    # ========== 内部方法 ==========

    def _resolve(self) -> Dict[str, Any]:
        """按层级合并所有配置."""
        if self._resolved is not None:
            return self._resolved

        result: Dict[str, Any] = {}
        for level in sorted(ConfigLevel, key=lambda l: l.value):
            if level in self._layers:
                result = deep_merge(result, self._layers[level])

        self._resolved = result
        return result

    def _invalidate_cache(self) -> None:
        """使缓存失效."""
        self._resolved = None

    @staticmethod
    def _get_nested(d: Dict, key: str, default: Any = None) -> Any:
        """获取嵌套字典的值."""
        parts = key.split(".")
        current = d
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    @staticmethod
    def _has_nested(d: Dict, key: str) -> bool:
        """检查嵌套键是否存在."""
        parts = key.split(".")
        current = d
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        return True


# ========== 便捷函数 ==========

def create_config(
    defaults: Optional[Dict[str, Any]] = None,
    app_name: str = "multi-agent-se",
) -> ConfigManager:
    """创建配置管理器的便捷函数."""
    mgr = ConfigManager(app_name=app_name)
    if defaults:
        mgr.load_defaults(defaults)
    return mgr
