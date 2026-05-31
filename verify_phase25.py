#!/usr/bin/env python3
"""第25阶段验收脚本 - 配置管理器.

验证内容：
- 配置枚举类型
- 配置字段定义与验证
- 深度合并
- 字典展平/还原
- 文件解析器
- 配置管理器（分层加载/访问/验证/快照/监听）
"""

import json
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from multi_agent_se.core.config import (
    ConfigField,
    ConfigFormat,
    ConfigLevel,
    ConfigSnapshot,
    ConfigSource,
    ValidationResult,
    ValidationSeverity,
    ConfigManager,
    ConfigParser,
    deep_merge,
    flatten_dict,
    unflatten_dict,
    create_config,
    create_field,
)


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name: str, passed: bool, message: str = "") -> None:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {test_name}")
    if message:
        print(f"         {message}")


def test_enums() -> bool:
    """测试枚举类型."""
    print_header("测试1: 枚举类型")

    sources = list(ConfigSource)
    print(f"  ConfigSource: {[s.value for s in sources]}")
    assert len(sources) == 5

    formats = list(ConfigFormat)
    print(f"  ConfigFormat: {[f.value for f in formats]}")
    assert len(formats) == 5

    levels = list(ConfigLevel)
    print(f"  ConfigLevel: {[l.value for l in levels]}")
    assert len(levels) == 6

    print_result("枚举类型", True, f"Source={len(sources)}, Format={len(formats)}, Level={len(levels)}")
    return True


def test_config_field() -> bool:
    """测试配置字段定义."""
    print_header("测试2: ConfigField 配置字段")

    f1 = create_field("server.port", default=8080, field_type="int", description="服务端口")
    assert f1.key == "server.port"
    assert f1.value == 8080

    # 验证合法值
    errors = f1.validate(8080)
    assert len(errors) == 0
    print(f"  ✓ 合法值验证通过: port=8080")

    # 验证非法值
    errors = f1.validate("not_a_number")
    assert len(errors) > 0
    print(f"  ✓ 非法值检测: {errors[0]}")

    # 带范围限制
    f2 = ConfigField(key="timeout", value=30, field_type="int", min_value=1, max_value=300)
    errors = f2.validate(0)
    assert len(errors) > 0
    print(f"  ✓ 最小值限制: timeout=0 -> {errors[0]}")

    errors = f2.validate(500)
    assert len(errors) > 0
    print(f"  ✓ 最大值限制: timeout=500 -> {errors[0]}")

    # 带选择范围
    f3 = ConfigField(key="log_level", value="INFO", field_type="str", choices=["DEBUG", "INFO", "WARNING"])
    errors = f3.validate("TRACE")
    assert len(errors) > 0
    print(f"  ✓ 选择范围限制: TRACE -> {errors[0]}")

    # 正则匹配
    f4 = ConfigField(key="api_key", field_type="str", pattern=r"^[A-Za-z0-9]{16,}$")
    errors = f4.validate("short")
    assert len(errors) > 0
    print(f"  ✓ 正则匹配限制: 'short' -> {errors[0]}")

    errors = f4.validate("validapikey1234567890")
    assert len(errors) == 0
    print(f"  ✓ 正则匹配通过: 'validapikey1234567890'")

    print_result("ConfigField", True)
    return True


def test_validation_result() -> bool:
    """测试验证结果."""
    print_header("测试3: ValidationResult")

    vr = ValidationResult()
    assert vr.is_valid is True
    print(f"  ✓ 空验证通过")

    vr.add_error("key1", "必填项缺失")
    vr.add_warning("key2", "建议修改")
    assert vr.is_valid is False
    assert vr.error_count == 1
    assert vr.warning_count == 1
    print(f"  ✓ 错误+警告: {vr.format_summary()}")

    d = vr.to_dict()
    assert d["is_valid"] is False
    assert len(d["issues"]) == 2
    print(f"  ✓ to_dict() 正常")

    print_result("ValidationResult", True)
    return True


def test_deep_merge() -> bool:
    """测试深度合并."""
    print_header("测试4: deep_merge 深度合并")

    base = {"a": 1, "b": {"c": 2, "d": 3}}
    override = {"b": {"c": 99, "e": 4}, "f": 5}
    result = deep_merge(base, override)

    assert result["a"] == 1
    assert result["b"]["c"] == 99  # 被覆盖
    assert result["b"]["d"] == 3   # 保留
    assert result["b"]["e"] == 4   # 新增
    assert result["f"] == 5        # 新增
    print(f"  ✓ 合并结果: {result}")

    # 确保原字典不被修改
    assert base["b"]["c"] == 2
    print(f"  ✓ 原字典不被修改")

    print_result("deep_merge", True)
    return True


def test_flatten_unflatten() -> bool:
    """测试字典展平与还原."""
    print_header("测试5: flatten_dict / unflatten_dict")

    nested = {"server": {"port": 8080, "host": "localhost"}, "debug": True}
    flat = flatten_dict(nested)

    assert flat["server.port"] == 8080
    assert flat["server.host"] == "localhost"
    assert flat["debug"] is True
    print(f"  ✓ 展平: {flat}")

    restored = unflatten_dict(flat)
    assert restored["server"]["port"] == 8080
    assert restored["server"]["host"] == "localhost"
    assert restored["debug"] is True
    print(f"  ✓ 还原: {restored}")

    print_result("flatten/unflatten", True)
    return True


def test_config_parser() -> bool:
    """测试配置文件解析."""
    print_header("测试6: ConfigParser 文件解析")

    # JSON
    json_str = '{"server": {"port": 8080}, "debug": true}'
    data = ConfigParser.parse(json_str, ConfigFormat.JSON)
    assert data["server"]["port"] == 8080
    assert data["debug"] is True
    print(f"  ✓ JSON解析: port={data['server']['port']}")

    # ENV
    env_str = "APP_NAME=test\nDEBUG=true\nPORT=3000\n"
    data = ConfigParser.parse(env_str, ConfigFormat.ENV)
    assert data["APP_NAME"] == "test"
    assert data["DEBUG"] is True
    assert data["PORT"] == 3000
    print(f"  ✓ ENV解析: {data}")

    # 格式检测
    assert ConfigParser.detect_format("config.json") == ConfigFormat.JSON
    assert ConfigParser.detect_format("config.yaml") == ConfigFormat.YAML
    assert ConfigParser.detect_format("config.toml") == ConfigFormat.TOML
    assert ConfigParser.detect_format(".env") == ConfigFormat.ENV
    assert ConfigParser.detect_format("config.env") == ConfigFormat.ENV
    print(f"  ✓ 格式检测正常")

    print_result("ConfigParser", True)
    return True


def test_config_manager_basic() -> bool:
    """测试配置管理器基本功能."""
    print_header("测试7: ConfigManager 基本功能")

    mgr = ConfigManager()
    mgr.load_defaults({
        "server": {"host": "localhost", "port": 8080},
        "debug": False,
        "log_level": "INFO",
    })

    # get
    assert mgr.get("server.host") == "localhost"
    assert mgr.get("server.port") == 8080
    assert mgr.get("debug") is False
    assert mgr.get("missing", "default") == "default"
    print(f"  ✓ get() 正常")

    # has
    assert mgr.has("server.host") is True
    assert mgr.has("missing") is False
    print(f"  ✓ has() 正常")

    # keys
    keys = mgr.keys()
    assert "server.host" in keys
    assert "server.port" in keys
    print(f"  ✓ keys(): {keys}")

    # all
    all_cfg = mgr.all()
    assert all_cfg["server"]["host"] == "localhost"
    print(f"  ✓ all() 正常")

    print_result("ConfigManager 基本功能", True)
    return True


def test_config_manager_layers() -> bool:
    """测试分层配置合并."""
    print_header("测试8: ConfigManager 分层合并")

    mgr = ConfigManager()
    mgr.load_defaults({"server": {"host": "localhost", "port": 8080}, "debug": False})

    # 项目级覆盖
    mgr.load_dict({"server": {"port": 9090}}, level=ConfigLevel.PROJECT)
    assert mgr.get("server.port") == 9090
    assert mgr.get("server.host") == "localhost"  # 保留
    print(f"  ✓ 项目级覆盖: port=9090, host=localhost")

    # 运行时覆盖（最高优先级）
    mgr.set("server.port", 3000)
    assert mgr.get("server.port") == 3000
    print(f"  ✓ 运行时覆盖: port=3000")

    print_result("ConfigManager 分层合并", True)
    return True


def test_config_manager_file() -> bool:
    """测试文件加载."""
    print_header("测试9: ConfigManager 文件加载")

    # 创建临时JSON配置文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"server": {"host": "0.0.0.0", "port": 5000}, "verbose": True}, f)
        json_path = f.name

    try:
        mgr = ConfigManager()
        mgr.load_defaults({"server": {"host": "localhost", "port": 8080}})
        mgr.load_file(json_path, level=ConfigLevel.PROJECT)

        assert mgr.get("server.host") == "0.0.0.0"
        assert mgr.get("server.port") == 5000
        assert mgr.get("verbose") is True
        print(f"  ✓ JSON文件加载正常")

    finally:
        Path(json_path).unlink(missing_ok=True)

    # 创建临时ENV文件
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("APP_NAME=test_app\nDEBUG=true\n")
        env_path = f.name

    try:
        mgr2 = ConfigManager()
        mgr2.load_file(env_path, level=ConfigLevel.LOCAL)
        assert mgr2.get("APP_NAME") == "test_app"
        assert mgr2.get("DEBUG") is True
        print(f"  ✓ ENV文件加载正常")

    finally:
        Path(env_path).unlink(missing_ok=True)

    print_result("ConfigManager 文件加载", True)
    return True


def test_config_manager_validation() -> bool:
    """测试配置验证."""
    print_header("测试10: ConfigManager 配置验证")

    mgr = ConfigManager()
    mgr.load_defaults({"server": {"port": 8080}, "timeout": 30})

    # 注册字段定义
    mgr.register_field(ConfigField(
        key="server.port", field_type="int", min_value=1, max_value=65535,
    ))
    mgr.register_field(ConfigField(
        key="timeout", field_type="int", min_value=1, max_value=300,
    ))
    mgr.register_field(ConfigField(
        key="api_key", field_type="str", required=True,
    ))

    # 合法配置
    result = mgr.validate()
    assert not result.is_valid  # api_key缺失
    assert result.error_count >= 1
    print(f"  ✓ 缺失必填项检测: {result.format_summary()}")

    # 修复后验证
    mgr.set("api_key", "valid_key_12345678")
    result = mgr.validate()
    assert result.is_valid
    print(f"  ✓ 修复后验证通过: {result.format_summary()}")

    print_result("ConfigManager 配置验证", True)
    return True


def test_config_manager_snapshot() -> bool:
    """测试配置快照."""
    print_header("测试11: ConfigManager 快照")

    mgr = ConfigManager()
    mgr.load_defaults({"version": "1.0", "mode": "dev"})

    # 创建快照
    snap = mgr.snapshot("initial")
    assert snap.name == "initial"
    assert snap.config["version"] == "1.0"
    print(f"  ✓ 快照创建: {snap.name}")

    # 修改配置
    mgr.set("version", "2.0")
    mgr.set("mode", "prod")
    assert mgr.get("version") == "2.0"
    print(f"  ✓ 配置已修改: version=2.0")

    # 从快照恢复
    mgr.restore(snap)
    assert mgr.get("version") == "1.0"
    assert mgr.get("mode") == "dev"
    print(f"  ✓ 从快照恢复: version=1.0")

    # 快照列表
    snaps = mgr.get_snapshots()
    assert len(snaps) == 1
    print(f"  ✓ 快照列表: {len(snaps)}个")

    print_result("ConfigManager 快照", True)
    return True


def test_config_manager_watch() -> bool:
    """测试配置变更监听."""
    print_header("测试12: ConfigManager 变更监听")

    mgr = ConfigManager()
    mgr.load_defaults({"theme": "light"})

    changes = []

    def on_change(key, old_val, new_val):
        changes.append((key, old_val, new_val))

    mgr.watch("theme", on_change)
    mgr.set("theme", "dark")

    assert len(changes) == 1
    assert changes[0] == ("theme", "light", "dark")
    print(f"  ✓ 变更监听触发: {changes[0]}")

    # 相同值不触发
    mgr.set("theme", "dark")
    assert len(changes) == 1
    print(f"  ✓ 相同值不触发")

    # 取消监听
    mgr.unwatch("theme")
    mgr.set("theme", "blue")
    assert len(changes) == 1
    print(f"  ✓ 取消监听后不触发")

    print_result("ConfigManager 变更监听", True)
    return True


def test_create_config_convenience() -> bool:
    """测试便捷函数."""
    print_header("测试13: create_config 便捷函数")

    mgr = create_config(
        defaults={"app": "test", "version": "1.0"},
        app_name="test-app",
    )
    assert mgr.get("app") == "test"
    assert mgr.app_name == "test-app"
    print(f"  ✓ 便捷函数正常")

    print_result("create_config 便捷函数", True)
    return True


def main() -> int:
    print("\n" + "="*60)
    print("  第25阶段验收: 配置管理器 (Configuration Manager)")
    print("="*60)

    tests = [
        test_enums,
        test_config_field,
        test_validation_result,
        test_deep_merge,
        test_flatten_unflatten,
        test_config_parser,
        test_config_manager_basic,
        test_config_manager_layers,
        test_config_manager_file,
        test_config_manager_validation,
        test_config_manager_snapshot,
        test_config_manager_watch,
        test_create_config_convenience,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"  验收结果: {passed} 通过, {failed} 失败")
    print("="*60)

    if failed == 0:
        print("\n  ✓ 第25阶段验收通过！")
        print("\n  实现功能:")
        print("    - ConfigSource: 5种配置来源")
        print("    - ConfigFormat: 5种文件格式")
        print("    - ConfigLevel: 6级配置层级")
        print("    - ConfigField: 字段定义（类型/范围/选择/正则/必填）")
        print("    - ValidationResult: 验证结果（错误/警告）")
        print("    - deep_merge: 深度字典合并")
        print("    - flatten/unflatten: 字典展平与还原")
        print("    - ConfigParser: 多格式解析（JSON/ENV/YAML/TOML）")
        print("    - ConfigManager: 分层配置管理")
        print("      - get/set/has/keys/all")
        print("      - load_defaults/load_file/load_dict/load_env_vars")
        print("      - validate（基于字段定义）")
        print("      - snapshot/restore（配置快照）")
        print("      - watch/unwatch（变更监听）")
        print("="*60)
        return 0
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
