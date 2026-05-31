"""统一日志管理 - 阶段10.

正交拆分：日志管理独立于配置模块
基于structlog实现结构化日志，支持分级输出、JSON/Console格式、文件输出
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog


# ========== 日志级别常量 ==========
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.CRITICAL,
}


class LogManager:
    """日志管理器.

    统一管理structlog配置，支持：
    - 分级输出 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    - JSON格式 / Console格式
    - 文件输出 + 控制台输出
    - 上下文绑定 (trace_id, agent_name等)
    """

    _configured = False
    _log_level = logging.INFO
    _log_format = "console"  # "json" or "console"
    _log_file: Optional[Path] = None
    _extra_processors: List = []

    @classmethod
    def configure(
        cls,
        log_level: str = "INFO",
        log_format: str = "console",
        log_file: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """配置日志系统.

        Args:
            log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
            log_format: 输出格式 ("json" 或 "console")
            log_file: 日志文件路径 (None则仅输出到控制台)
            extra_context: 全局上下文字段
        """
        # 解析日志级别
        level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
        cls._log_level = level
        cls._log_format = log_format
        cls._log_file = Path(log_file) if log_file else None

        # 构建处理器链
        shared_processors: List[Any] = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
        ]

        # 添加额外处理器
        shared_processors.extend(cls._extra_processors)

        # 格式化处理器
        if log_format.lower() == "json":
            renderer = structlog.processors.JSONRenderer(ensure_ascii=False)
        else:
            renderer = structlog.dev.ConsoleRenderer(colors=True)

        # 配置标准库logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=level,
        )

        # 配置structlog
        structlog.configure(
            processors=shared_processors + [
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # 配置Formatter
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                renderer,
            ],
        )

        # 获取root handler并设置formatter
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.setFormatter(formatter)

        # 添加文件handler
        if cls._log_file:
            cls._log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                str(cls._log_file), encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        # 绑定全局上下文
        if extra_context:
            structlog.contextvars.bind_contextvars(**extra_context)

        cls._configured = True

    @classmethod
    def is_configured(cls) -> bool:
        """是否已配置."""
        return cls._configured

    @classmethod
    def get_logger(cls, name: str = "") -> structlog.stdlib.BoundLogger:
        """获取logger实例.

        Args:
            name: logger名称

        Returns:
            structlog BoundLogger
        """
        if not cls._configured:
            cls.configure()
        return structlog.get_logger(name)

    @classmethod
    def bind(cls, **kwargs: Any) -> None:
        """绑定上下文变量.

        Args:
            **kwargs: 上下文键值对
        """
        structlog.contextvars.bind_contextvars(**kwargs)

    @classmethod
    def unbind(cls, *keys: str) -> None:
        """解绑上下文变量.

        Args:
            *keys: 要解绑的键名
        """
        structlog.contextvars.unbind_contextvars(*keys)

    @classmethod
    def clear_context(cls) -> None:
        """清除所有上下文变量."""
        structlog.contextvars.clear_contextvars()

    @classmethod
    def new_context(cls, **kwargs: Any) -> Any:
        """创建新上下文 (contextmanager).

        Args:
            **kwargs: 上下文键值对

        Returns:
            contextvars上下文管理器
        """
        return structlog.contextvars.bind_contextvars(**kwargs)

    @classmethod
    def set_level(cls, level: str) -> None:
        """动态调整日志级别.

        Args:
            level: 日志级别字符串
        """
        new_level = LOG_LEVELS.get(level.upper(), logging.INFO)
        cls._log_level = new_level
        logging.getLogger().setLevel(new_level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(new_level)

    @classmethod
    def get_level(cls) -> str:
        """获取当前日志级别.

        Returns:
            日志级别字符串
        """
        for name, value in LOG_LEVELS.items():
            if value == cls._log_level:
                return name
        return "INFO"

    @classmethod
    def add_processor(cls, processor: Any) -> None:
        """添加自定义处理器（需在configure之前调用）.

        Args:
            processor: structlog处理器
        """
        cls._extra_processors.append(processor)


# ========== 便捷函数 ==========
def get_logger(name: str = "") -> structlog.stdlib.BoundLogger:
    """获取logger的便捷函数.

    Args:
        name: logger名称

    Returns:
        structlog BoundLogger
    """
    return LogManager.get_logger(name)


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "console",
    log_file: Optional[str] = None,
) -> None:
    """配置日志的便捷函数.

    Args:
        log_level: 日志级别
        log_format: 输出格式
        log_file: 日志文件路径
    """
    LogManager.configure(
        log_level=log_level,
        log_format=log_format,
        log_file=log_file,
    )
