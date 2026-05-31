"""日志模型定义 - 阶段28.

定义日志系统的数据结构：
- 日志级别
- 日志记录
- 日志上下文
- 日志格式化
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class LogLevel(Enum):
    """日志级别."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    @classmethod
    def from_name(cls, name: str) -> "LogLevel":
        """从名称获取级别."""
        mapping = {
            "debug": cls.DEBUG,
            "info": cls.INFO,
            "warning": cls.WARNING,
            "error": cls.ERROR,
            "critical": cls.CRITICAL,
        }
        return mapping.get(name.lower(), cls.INFO)

    @classmethod
    def from_value(cls, value: int) -> "LogLevel":
        """从数值获取级别."""
        for level in cls:
            if level.value == value:
                return level
        return cls.INFO


class LogFormat(Enum):
    """日志格式."""
    PLAIN = "plain"          # 纯文本
    JSON = "json"            # JSON格式
    STRUCTURED = "structured"  # 结构化键值对


# ========== 日志记录 ==========

@dataclass
class LogRecord:
    """日志记录."""
    message: str = ""
    level: LogLevel = LogLevel.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    logger_name: str = ""
    source_file: str = ""
    source_line: int = 0
    function_name: str = ""
    thread_id: int = 0
    process_id: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    exception_info: str = ""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def level_name(self) -> str:
        return self.level.name

    @property
    def is_error(self) -> bool:
        return self.level.value >= LogLevel.ERROR.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level_name,
            "level_value": self.level.value,
            "logger_name": self.logger_name,
            "message": self.message,
            "source_file": self.source_file,
            "source_line": self.source_line,
            "function_name": self.function_name,
            "thread_id": self.thread_id,
            "process_id": self.process_id,
            "context": self.context,
            "exception_info": self.exception_info,
        }

    def format_plain(self) -> str:
        """格式化为纯文本."""
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        parts = [f"[{ts}]", f"[{self.level_name:8}]"]
        if self.logger_name:
            parts.append(f"[{self.logger_name}]")
        parts.append(self.message)
        if self.exception_info:
            parts.append(f"\n{self.exception_info}")
        return " ".join(parts)

    def format_structured(self) -> str:
        """格式化为结构化文本."""
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        parts = [
            f"timestamp={ts}",
            f"level={self.level_name}",
            f"logger={self.logger_name}",
            f"message={repr(self.message)}",
        ]
        if self.context:
            for key, value in self.context.items():
                parts.append(f"{key}={repr(value)}")
        return " ".join(parts)


# ========== 日志上下文 ==========

class LogContext:
    """日志上下文.

    用于在日志记录中添加统一的上下文信息
    """

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """设置上下文值."""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文值."""
        return self._data.get(key, default)

    def remove(self, key: str) -> None:
        """移除上下文值."""
        self._data.pop(key, None)

    def clear(self) -> None:
        """清空上下文."""
        self._data.clear()

    def copy(self) -> Dict[str, Any]:
        """复制当前上下文."""
        return dict(self._data)

    def __enter__(self) -> "LogContext":
        return self

    def __exit__(self, *args) -> None:
        self.clear()


# ========== 日志处理器 ==========

@dataclass
class LogHandler:
    """日志处理器基类."""
    name: str = ""
    level: LogLevel = LogLevel.DEBUG
    formatter: LogFormat = LogFormat.PLAIN
    enabled: bool = True

    def should_handle(self, record: LogRecord) -> bool:
        """判断是否应处理该记录."""
        return self.enabled and record.level.value >= self.level.value

    def format_record(self, record: LogRecord) -> str:
        """格式化记录."""
        if self.formatter == LogFormat.JSON:
            import json
            return json.dumps(record.to_dict(), ensure_ascii=False)
        elif self.formatter == LogFormat.STRUCTURED:
            return record.format_structured()
        return record.format_plain()

    def emit(self, record: LogRecord) -> None:
        """输出日志记录（子类实现）."""
        raise NotImplementedError

    def handle(self, record: LogRecord) -> None:
        """处理日志记录."""
        if self.should_handle(record):
            self.emit(record)


@dataclass
class ConsoleHandler(LogHandler):
    """控制台日志处理器."""
    use_stderr_for_errors: bool = True

    def emit(self, record: LogRecord) -> None:
        """输出到控制台."""
        import sys
        formatted = self.format_record(record)
        if self.use_stderr_for_errors and record.is_error:
            print(formatted, file=sys.stderr)
        else:
            print(formatted)


@dataclass
class MemoryHandler(LogHandler):
    """内存日志处理器（用于测试和调试）."""
    max_records: int = 1000
    records: List[LogRecord] = field(default_factory=list)

    def emit(self, record: LogRecord) -> None:
        """存储到内存."""
        self.records.append(record)
        if len(self.records) > self.max_records:
            self.records.pop(0)

    def clear(self) -> None:
        """清空记录."""
        self.records.clear()

    def get_records(self, level: Optional[LogLevel] = None) -> List[LogRecord]:
        """获取记录."""
        if level is None:
            return list(self.records)
        return [r for r in self.records if r.level.value >= level.value]


@dataclass
class FileHandler(LogHandler):
    """文件日志处理器."""
    file_path: str = ""
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    def emit(self, record: LogRecord) -> None:
        """输出到文件."""
        from pathlib import Path
        formatted = self.format_record(record)
        path = Path(self.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")


# ========== 便捷函数 ==========

def create_record(
    message: str,
    level: LogLevel = LogLevel.INFO,
    logger_name: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> LogRecord:
    """创建日志记录的便捷函数."""
    return LogRecord(
        message=message,
        level=level,
        logger_name=logger_name,
        context=context or {},
    )
