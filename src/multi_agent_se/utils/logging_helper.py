"""日志辅助模块 - 第42阶段.

为系统提供统一的结构化日志能力，支持运行时追踪和调试。
"""

import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional


class LogLevel:
    """日志级别."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class StructuredLogger:
    """结构化日志器.
    
    为每个模块提供带上下文信息的日志输出。
    """
    
    _enabled = True
    _min_level = LogLevel.DEBUG
    _level_priority = {
        LogLevel.DEBUG: 0,
        LogLevel.INFO: 1,
        LogLevel.WARN: 2,
        LogLevel.ERROR: 3,
        LogLevel.FATAL: 4,
    }
    
    def __init__(self, module_name: str, agent_id: Optional[str] = None) -> None:
        self.module_name = module_name
        self.agent_id = agent_id
        self._context: Dict[str, Any] = {}
    
    def with_context(self, **kwargs) -> "StructuredLogger":
        """添加上下文."""
        self._context.update(kwargs)
        return self
    
    def _should_log(self, level: str) -> bool:
        """判断是否应记录该级别日志."""
        if not self._enabled:
            return False
        return self._level_priority.get(level, 0) >= self._level_priority.get(self._min_level, 0)
    
    def _format(self, level: str, message: str, **extra) -> str:
        """格式化日志."""
        timestamp = datetime.now().isoformat()
        parts = [
            f"[{timestamp}]",
            f"[{level:5s}]",
            f"[{self.module_name}]",
        ]
        
        if self.agent_id:
            parts.append(f"[agent={self.agent_id}]")
        
        # 添加上下文
        ctx_items = []
        for k, v in {**self._context, **extra}.items():
            if isinstance(v, str) and len(v) > 50:
                v = v[:50] + "..."
            ctx_items.append(f"{k}={v}")
        
        if ctx_items:
            parts.append(f"({' | '.join(ctx_items)})")
        
        parts.append(f"-> {message}")
        return " ".join(parts)
    
    def debug(self, message: str, **extra) -> None:
        """调试日志."""
        if self._should_log(LogLevel.DEBUG):
            print(self._format(LogLevel.DEBUG, message, **extra), file=sys.stderr)
    
    def info(self, message: str, **extra) -> None:
        """信息日志."""
        if self._should_log(LogLevel.INFO):
            print(self._format(LogLevel.INFO, message, **extra), file=sys.stderr)
    
    def warn(self, message: str, **extra) -> None:
        """警告日志."""
        if self._should_log(LogLevel.WARN):
            print(self._format(LogLevel.WARN, message, **extra), file=sys.stderr)
    
    def error(self, message: str, exc: Optional[Exception] = None, **extra) -> None:
        """错误日志."""
        if self._should_log(LogLevel.ERROR):
            print(self._format(LogLevel.ERROR, message, **extra), file=sys.stderr)
            if exc:
                traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
    
    def fatal(self, message: str, exc: Optional[Exception] = None, **extra) -> None:
        """致命日志."""
        print(self._format(LogLevel.FATAL, message, **extra), file=sys.stderr)
        if exc:
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
    
    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        """设置全局日志开关."""
        cls._enabled = enabled
    
    @classmethod
    def set_min_level(cls, level: str) -> None:
        """设置最小日志级别."""
        cls._min_level = level


def get_logger(module_name: str, agent_id: Optional[str] = None) -> StructuredLogger:
    """获取日志器."""
    return StructuredLogger(module_name, agent_id)
