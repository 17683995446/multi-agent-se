#!/usr/bin/env python3
"""第28阶段验收脚本 - 日志系统.

验证内容：
- 日志级别枚举
- 日志记录创建与格式化
- 日志上下文
- 日志处理器（控制台/内存/文件）
- 日志记录器
- 日志管理器（单例/多记录器）
- 便捷函数
"""

import json
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from multi_agent_se.core.logging import (
    LogLevel,
    LogFormat,
    LogRecord,
    LogContext,
    ConsoleHandler,
    MemoryHandler,
    FileHandler,
    Logger,
    LogManager,
    log_manager,
    get_logger,
    debug,
    info,
    warning,
    error,
    critical,
    create_record,
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


def test_log_level() -> bool:
    """测试日志级别."""
    print_header("测试1: LogLevel 日志级别")

    levels = list(LogLevel)
    assert len(levels) == 5
    print(f"  级别: {[(l.name, l.value) for l in levels]}")

    # from_name
    assert LogLevel.from_name("debug") == LogLevel.DEBUG
    assert LogLevel.from_name("ERROR") == LogLevel.ERROR
    assert LogLevel.from_name("unknown") == LogLevel.INFO  # 默认
    print(f"  ✓ from_name() 正常")

    # from_value
    assert LogLevel.from_value(10) == LogLevel.DEBUG
    assert LogLevel.from_value(50) == LogLevel.CRITICAL
    print(f"  ✓ from_value() 正常")

    print_result("LogLevel", True)
    return True


def test_log_record() -> bool:
    """测试日志记录."""
    print_header("测试2: LogRecord 日志记录")

    record = create_record(
        message="测试消息",
        level=LogLevel.INFO,
        logger_name="test_logger",
        context={"key": "value"},
    )

    assert record.message == "测试消息"
    assert record.level == LogLevel.INFO
    assert record.logger_name == "test_logger"
    assert record.context["key"] == "value"
    assert len(record.record_id) > 0
    print(f"  ✓ 记录创建: {record.record_id}")

    # 格式化
    plain = record.format_plain()
    assert "测试消息" in plain
    assert "INFO" in plain
    print(f"  ✓ 纯文本格式: {plain[:50]}...")

    structured = record.format_structured()
    assert "level=INFO" in structured
    print(f"  ✓ 结构化格式: {structured[:60]}...")

    # JSON
    d = record.to_dict()
    assert d["message"] == "测试消息"
    print(f"  ✓ to_dict() 正常")

    print_result("LogRecord", True)
    return True


def test_log_context() -> bool:
    """测试日志上下文."""
    print_header("测试3: LogContext 日志上下文")

    ctx = LogContext()
    ctx.set("request_id", "req-123")
    ctx.set("user", "admin")

    assert ctx.get("request_id") == "req-123"
    assert ctx.get("missing", "default") == "default"
    print(f"  ✓ 上下文设置/获取正常")

    copied = ctx.copy()
    assert copied["user"] == "admin"
    print(f"  ✓ copy() 正常")

    ctx.remove("user")
    assert ctx.get("user") is None
    print(f"  ✓ remove() 正常")

    ctx.clear()
    assert len(ctx.copy()) == 0
    print(f"  ✓ clear() 正常")

    # 上下文管理器
    with LogContext() as c:
        c.set("temp", "value")
        assert c.get("temp") == "value"
    print(f"  ✓ 上下文管理器正常")

    print_result("LogContext", True)
    return True


def test_console_handler() -> bool:
    """测试控制台处理器."""
    print_header("测试4: ConsoleHandler 控制台处理器")

    handler = ConsoleHandler(name="console", level=LogLevel.INFO)
    record = create_record("控制台测试", level=LogLevel.INFO)

    assert handler.should_handle(record) is True
    print(f"  ✓ should_handle() 正常")

    formatted = handler.format_record(record)
    assert "控制台测试" in formatted
    print(f"  ✓ format_record() 正常")

    # emit会实际打印到控制台
    handler.emit(record)
    print(f"  ✓ emit() 已输出到控制台")

    print_result("ConsoleHandler", True)
    return True


def test_memory_handler() -> bool:
    """测试内存处理器."""
    print_header("测试5: MemoryHandler 内存处理器")

    handler = MemoryHandler(name="memory", max_records=10)

    # 记录多条日志
    for i in range(5):
        record = create_record(f"消息{i}", level=LogLevel.INFO if i % 2 == 0 else LogLevel.ERROR)
        handler.emit(record)

    assert len(handler.records) == 5
    print(f"  ✓ 存储记录数: {len(handler.records)}")

    # 按级别筛选
    errors = handler.get_records(LogLevel.ERROR)
    assert len(errors) == 2
    print(f"  ✓ ERROR级别记录: {len(errors)}条")

    # 清空
    handler.clear()
    assert len(handler.records) == 0
    print(f"  ✓ clear() 正常")

    print_result("MemoryHandler", True)
    return True


def test_file_handler() -> bool:
    """测试文件处理器."""
    print_header("测试6: FileHandler 文件处理器")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_path = f.name

    try:
        handler = FileHandler(name="file", file_path=log_path, formatter=LogFormat.PLAIN)
        record = create_record("文件测试消息", level=LogLevel.INFO, logger_name="test")

        handler.emit(record)

        # 读取文件验证
        with open(log_path, "r") as f:
            content = f.read()
        assert "文件测试消息" in content
        print(f"  ✓ 文件写入正常")

        # JSON格式
        handler2 = FileHandler(name="file2", file_path=log_path, formatter=LogFormat.JSON)
        record2 = create_record("JSON消息", level=LogLevel.WARNING)
        handler2.emit(record2)

        with open(log_path, "r") as f:
            lines = f.readlines()
        assert len(lines) == 2
        # 验证第二行是JSON
        json_data = json.loads(lines[1])
        assert json_data["message"] == "JSON消息"
        print(f"  ✓ JSON格式正常")

    finally:
        Path(log_path).unlink(missing_ok=True)

    print_result("FileHandler", True)
    return True


def test_logger() -> bool:
    """测试日志记录器."""
    print_header("测试7: Logger 日志记录器")

    logger = Logger(name="test_logger")
    logger.set_level(LogLevel.DEBUG)

    # 使用内存处理器捕获日志
    memory = MemoryHandler()
    logger.add_handler(memory)

    # 各级别日志
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    logger.critical("严重错误")

    assert len(memory.records) == 5
    assert memory.records[0].level == LogLevel.DEBUG
    assert memory.records[4].level == LogLevel.CRITICAL
    print(f"  ✓ 各级别日志记录: {len(memory.records)}条")

    # 级别过滤
    logger2 = Logger(name="filtered")
    logger2.set_level(LogLevel.WARNING)
    memory2 = MemoryHandler()
    logger2.add_handler(memory2)

    logger2.debug("被过滤")
    logger2.info("被过滤")
    logger2.warning("保留")
    logger2.error("保留")

    assert len(memory2.records) == 2
    print(f"  ✓ 级别过滤: 只保留WARNING及以上")

    # 上下文
    logger3 = Logger(name="context_test")
    memory3 = MemoryHandler()
    logger3.add_handler(memory3)
    logger3.with_context(request_id="req-456", user="tester")
    logger3.info("带上下文的日志")

    assert memory3.records[0].context["request_id"] == "req-456"
    print(f"  ✓ 上下文传递正常")

    print_result("Logger", True)
    return True


def test_log_manager_singleton() -> bool:
    """测试日志管理器单例."""
    print_header("测试8: LogManager 单例模式")

    manager1 = LogManager()
    manager2 = LogManager()

    assert manager1 is manager2
    print(f"  ✓ 单例模式正常")

    # 获取记录器
    logger_a = manager1.get_logger("logger_a")
    logger_b = manager1.get_logger("logger_b")
    logger_a2 = manager1.get_logger("logger_a")

    assert logger_a is logger_a2  # 相同名称返回相同实例
    assert logger_a is not logger_b
    print(f"  ✓ 记录器缓存正常")

    # 列表
    loggers = manager1.list_loggers()
    assert "logger_a" in loggers
    assert "logger_b" in loggers
    print(f"  ✓ list_loggers(): {loggers}")

    # 移除
    assert manager1.remove_logger("logger_a") is True
    assert manager1.remove_logger("nonexistent") is False
    print(f"  ✓ remove_logger() 正常")

    print_result("LogManager 单例", True)
    return True


def test_log_manager_global_config() -> bool:
    """测试日志管理器全局配置."""
    print_header("测试9: LogManager 全局配置")

    # 创建新管理器（单例，但我们可以重置）
    manager = LogManager()

    # 设置默认级别
    manager.set_default_level(LogLevel.ERROR)
    logger = manager.get_logger("level_test")
    memory = MemoryHandler()
    logger.clear_handlers()
    logger.add_handler(memory)

    logger.debug("被过滤")
    logger.info("被过滤")
    logger.error("保留")

    assert len(memory.records) == 1
    assert memory.records[0].message == "保留"
    print(f"  ✓ 默认级别生效")

    # 添加默认处理器
    manager.clear_default_handlers()
    manager.set_default_level(LogLevel.INFO)  # 重置默认级别为INFO
    memory2 = MemoryHandler()
    manager.add_default_handler(memory2)

    logger2 = manager.get_logger("handler_test")
    logger2.info("测试消息")

    assert len(memory2.records) == 1
    print(f"  ✓ 默认处理器生效")

    print_result("LogManager 全局配置", True)
    return True


def test_convenience_functions() -> bool:
    """测试便捷函数."""
    print_header("测试10: 便捷函数")

    # 使用内存处理器捕获
    memory = MemoryHandler()
    log_manager.add_default_handler(memory)

    # 清除之前的记录
    memory.clear()

    debug("调试消息")
    info("普通消息")
    warning("警告消息")
    error("错误消息")
    critical("严重消息")

    # 由于默认级别是ERROR（上一个测试设置的），只应捕获error和critical
    error_records = [r for r in memory.records if r.level.value >= LogLevel.ERROR.value]
    assert len(error_records) >= 2
    print(f"  ✓ 便捷函数记录: {len(error_records)}条ERROR及以上")

    # get_logger
    logger = get_logger("convenience_test")
    assert logger.name == "convenience_test"
    print(f"  ✓ get_logger() 正常")

    print_result("便捷函数", True)
    return True


def test_exception_logging() -> bool:
    """测试异常日志记录."""
    print_header("测试11: 异常日志记录")

    logger = Logger(name="exception_test")
    memory = MemoryHandler()
    logger.add_handler(memory)

    try:
        raise ValueError("测试异常")
    except Exception:
        logger.exception("捕获到异常")

    assert len(memory.records) == 1
    assert memory.records[0].level == LogLevel.ERROR
    assert "测试异常" in memory.records[0].exception_info
    print(f"  ✓ 异常信息记录: {memory.records[0].exception_info[:50]}...")

    print_result("异常日志记录", True)
    return True


def main() -> int:
    print("\n" + "="*60)
    print("  第28阶段验收: 日志系统 (Logging System)")
    print("="*60)

    tests = [
        test_log_level,
        test_log_record,
        test_log_context,
        test_console_handler,
        test_memory_handler,
        test_file_handler,
        test_logger,
        test_log_manager_singleton,
        test_log_manager_global_config,
        test_convenience_functions,
        test_exception_logging,
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
        print("\n  ✓ 第28阶段验收通过！")
        print("\n  实现功能:")
        print("    - LogLevel: 5级日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）")
        print("    - LogRecord: 日志记录（消息/级别/时间/上下文/异常信息）")
        print("    - LogFormat: 3种格式（纯文本/JSON/结构化键值对）")
        print("    - LogContext: 上下文管理（设置/获取/复制/清空/上下文管理器）")
        print("    - LogHandler: 处理器基类（级别过滤/格式化）")
        print("    - ConsoleHandler: 控制台输出（错误输出到stderr）")
        print("    - MemoryHandler: 内存存储（容量限制/按级别筛选）")
        print("    - FileHandler: 文件输出（自动创建目录/JSON格式）")
        print("    - Logger: 日志记录器（debug/info/warning/error/critical/exception）")
        print("    - LogManager: 单例管理器（多记录器/全局配置/默认处理器）")
        print("    - 便捷函数: get_logger/debug/info/warning/error/critical")
        print("="*60)
        return 0
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
