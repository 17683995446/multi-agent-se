"""日志管理器 - 阶段28.

提供统一的日志记录接口：
- 多级日志记录
- 多处理器支持
- 上下文管理
- 便捷函数
"""

import sys
import threading
import traceback
from typing import Any, Dict, List, Optional

from multi_agent_se.core.logging.models import (
    ConsoleHandler,
    LogContext,
    LogFormat,
    LogHandler,
    LogLevel,
    LogRecord,
    MemoryHandler,
    create_record,
)


class Logger:
    """日志记录器.

    提供类似标准库logging的接口
    """

    def __init__(self, name: str = "") -> None:
        self.name = name
        self.level: LogLevel = LogLevel.INFO
        self.handlers: List[LogHandler] = []
        self.context: LogContext = LogContext()
        self._lock = threading.Lock()

    # ========== 配置 ==========

    def set_level(self, level: LogLevel) -> None:
        """设置日志级别."""
        self.level = level

    def add_handler(self, handler: LogHandler) -> None:
        """添加处理器."""
        with self._lock:
            self.handlers.append(handler)

    def remove_handler(self, handler: LogHandler) -> bool:
        """移除处理器."""
        with self._lock:
            if handler in self.handlers:
                self.handlers.remove(handler)
                return True
            return False

    def clear_handlers(self) -> None:
        """清空所有处理器."""
        with self._lock:
            self.handlers.clear()

    # ========== 日志记录 ==========

    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ) -> None:
        """内部日志记录方法."""
        if level.value < self.level.value:
            return

        # 构建记录
        record = create_record(
            message=message,
            level=level,
            logger_name=self.name,
            context={**self.context.copy(), **(context or {})},
        )

        # 添加异常信息
        if exc_info:
            record.exception_info = traceback.format_exc()

        # 添加调用信息
        try:
            import inspect
            frame = inspect.currentframe()
            if frame:
                caller = frame.f_back.f_back  # 跳过_log和调用者
                if caller:
                    record.source_file = caller.f_code.co_filename
                    record.source_line = caller.f_lineno
                    record.function_name = caller.f_code.co_name
        except Exception:
            pass

        # 分发到处理器
        with self._lock:
            for handler in self.handlers:
                try:
                    handler.handle(record)
                except Exception:
                    pass  # 处理器错误不应影响主流程

    # ========== 级别方法 ==========

    def debug(self, message: str, **kwargs) -> None:
        """记录DEBUG级别日志."""
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """记录INFO级别日志."""
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """记录WARNING级别日志."""
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """记录ERROR级别日志."""
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """记录CRITICAL级别日志."""
        self._log(LogLevel.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """记录异常信息."""
        self._log(LogLevel.ERROR, message, exc_info=True, **kwargs)

    # ========== 上下文管理 ==========

    def with_context(self, **context) -> "Logger":
        """创建带上下文的日志记录器（链式调用）."""
        for key, value in context.items():
            self.context.set(key, value)
        return self


class LogManager:
    """日志管理器.

    管理多个日志记录器实例
    """

    _instance: Optional["LogManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "LogManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._loggers: Dict[str, Logger] = {}
        self._default_level: LogLevel = LogLevel.INFO
        self._default_handlers: List[LogHandler] = [ConsoleHandler()]
        self._initialized = True

    # ========== 日志记录器管理 ==========

    def get_logger(self, name: str = "") -> Logger:
        """获取或创建日志记录器."""
        if name not in self._loggers:
            logger = Logger(name)
            logger.set_level(self._default_level)
            for handler in self._default_handlers:
                logger.add_handler(handler)
            self._loggers[name] = logger
        return self._loggers[name]

    def remove_logger(self, name: str) -> bool:
        """移除日志记录器."""
        if name in self._loggers:
            del self._loggers[name]
            return True
        return False

    def list_loggers(self) -> List[str]:
        """列出所有日志记录器名称."""
        return list(self._loggers.keys())

    # ========== 全局配置 ==========

    def set_default_level(self, level: LogLevel) -> None:
        """设置默认日志级别."""
        self._default_level = level
        for logger in self._loggers.values():
            logger.set_level(level)

    def add_default_handler(self, handler: LogHandler) -> None:
        """添加默认处理器."""
        self._default_handlers.append(handler)
        for logger in self._loggers.values():
            logger.add_handler(handler)

    def clear_default_handlers(self) -> None:
        """清空默认处理器."""
        self._default_handlers.clear()

    # ========== 便捷方法 ==========

    def debug(self, message: str, **kwargs) -> None:
        """使用根记录器记录DEBUG日志."""
        self.get_logger().debug(message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """使用根记录器记录INFO日志."""
        self.get_logger().info(message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """使用根记录器记录WARNING日志."""
        self.get_logger().warning(message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """使用根记录器记录ERROR日志."""
        self.get_logger().error(message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """使用根记录器记录CRITICAL日志."""
        self.get_logger().critical(message, **kwargs)


# ========== 全局实例 ==========

log_manager = LogManager()


def get_logger(name: str = "") -> Logger:
    """获取日志记录器的便捷函数."""
    return log_manager.get_logger(name)


def debug(message: str, **kwargs) -> None:
    """记录DEBUG日志的便捷函数."""
    log_manager.debug(message, **kwargs)


def info(message: str, **kwargs) -> None:
    """记录INFO日志的便捷函数."""
    log_manager.info(message, **kwargs)


def warning(message: str, **kwargs) -> None:
    """记录WARNING日志的便捷函数."""
    log_manager.warning(message, **kwargs)


def error(message: str, **kwargs) -> None:
    """记录ERROR日志的便捷函数."""
    log_manager.error(message, **kwargs)


def critical(message: str, **kwargs) -> None:
    """记录CRITICAL日志的便捷函数."""
    log_manager.critical(message, **kwargs)


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "console",
    log_file: Optional[str] = None,
) -> None:
    """配置日志系统.

    Args:
        log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        log_format: 日志格式 (console/json/structured)
        log_file: 日志文件路径 (可选)
    """
    # 解析日志级别
    level_map = {
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "WARNING": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL,
    }
    level = level_map.get(log_level.upper(), LogLevel.INFO)

    # 解析日志格式
    fmt_map = {
        "console": LogFormat.PLAIN,
        "plain": LogFormat.PLAIN,
        "json": LogFormat.JSON,
        "structured": LogFormat.STRUCTURED,
    }
    fmt = fmt_map.get(log_format.lower(), LogFormat.PLAIN)

    # 清空默认处理器
    log_manager.clear_default_handlers()

    # 添加控制台处理器
    console_handler = ConsoleHandler(formatter=fmt)
    log_manager.add_default_handler(console_handler)

    # 添加文件处理器（如果指定了日志文件）
    if log_file:
        file_handler = FileHandler(file_path=log_file, formatter=fmt)
        log_manager.add_default_handler(file_handler)

    # 设置默认日志级别
    log_manager.set_default_level(level)
