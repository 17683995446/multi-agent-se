"""全链路日志追踪器 - 测试增强模块.

为系统所有关键操作提供详细的执行日志，便于：
1. 验证代码执行路径
2. 发现隐藏bug
3. 性能分析
4. 问题定位

使用方式:
    @trace_call
    def my_function():
        pass

    with TraceContext("operation_name", param1=value1):
        do_something()
"""

import functools
import inspect
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, TypeVar

from multi_agent_se.core.logging import get_logger, LogLevel

# 当前追踪上下文
_current_trace_id: ContextVar[str] = ContextVar("trace_id", default="")
_current_span_id: ContextVar[str] = ContextVar("span_id", default="")
_current_span_stack: ContextVar[List[str]] = ContextVar("span_stack", default=[])

logger = get_logger("tracer")


class TraceContext:
    """追踪上下文管理器.
    
    用于包裹一段代码，记录其执行时间、参数、返回值等信息。
    
    Example:
        with TraceContext("database_query", sql=query, timeout=30):
            result = db.execute(query)
    """
    
    def __init__(
        self,
        operation: str,
        level: LogLevel = LogLevel.DEBUG,
        log_args: bool = True,
        log_result: bool = True,
        log_exception: bool = True,
        **kwargs
    ):
        self.operation = operation
        self.level = level
        self.log_args = log_args
        self.log_result = log_result
        self.log_exception = log_exception
        self.extra = kwargs
        self.start_time: float = 0
        self.span_id: str = ""
        self.parent_span_id: str = ""
        
    def __enter__(self) -> "TraceContext":
        # 生成或复用trace_id
        trace_id = _current_trace_id.get()
        if not trace_id:
            trace_id = str(uuid.uuid4())[:8]
            _current_trace_id.set(trace_id)
        
        # 生成span_id
        self.span_id = str(uuid.uuid4())[:8]
        
        # 获取父span
        span_stack = _current_span_stack.get()
        self.parent_span_id = span_stack[-1] if span_stack else ""
        
        # 压入当前span
        span_stack.append(self.span_id)
        _current_span_stack.set(span_stack)
        _current_span_id.set(self.span_id)
        
        self.start_time = time.time()
        
        # 记录开始
        log_data = {
            "trace_id": trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation": self.operation,
            "event": "start",
        }
        if self.log_args and self.extra:
            # 安全地序列化参数
            safe_args = {}
            for k, v in self.extra.items():
                try:
                    safe_args[k] = _safe_repr(v)
                except Exception:
                    safe_args[k] = "<unserializable>"
            log_data["args"] = safe_args
            
        _log_at_level(self.level, f"[TRACE] {self.operation} START", log_data)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        duration = (time.time() - self.start_time) * 1000  # ms
        
        trace_id = _current_trace_id.get()
        
        log_data = {
            "trace_id": trace_id,
            "span_id": self.span_id,
            "operation": self.operation,
            "event": "end",
            "duration_ms": round(duration, 2),
        }
        
        if exc_type and self.log_exception:
            log_data["exception"] = f"{exc_type.__name__}: {exc_val}"
            _log_at_level(LogLevel.ERROR, f"[TRACE] {self.operation} FAILED", log_data)
        else:
            _log_at_level(self.level, f"[TRACE] {self.operation} END", log_data)
        
        # 弹出当前span
        span_stack = _current_span_stack.get()
        if span_stack and span_stack[-1] == self.span_id:
            span_stack.pop()
            _current_span_stack.set(span_stack)
            
        # 恢复父span
        if span_stack:
            _current_span_id.set(span_stack[-1])
        else:
            _current_span_id.set("")
            _current_trace_id.set("")


F = TypeVar("F", bound=Callable[..., Any])


def trace_call(
    operation: Optional[str] = None,
    level: LogLevel = LogLevel.DEBUG,
    log_args: bool = True,
    log_result: bool = True,
    log_exception: bool = True,
    max_arg_length: int = 200,
) -> Callable[[F], F]:
    """函数调用追踪装饰器.
    
    自动记录函数的调用、参数、返回值、执行时间和异常。
    
    Args:
        operation: 操作名称（默认使用函数名）
        level: 日志级别
        log_args: 是否记录参数
        log_result: 是否记录返回值
        log_exception: 是否记录异常
        max_arg_length: 参数值最大长度
        
    Example:
        @trace_call()
        def process_data(data: dict) -> dict:
            return transform(data)
            
        @trace_call(operation="custom_name", level=LogLevel.INFO)
        def important_function():
            pass
    """
    def decorator(func: F) -> F:
        op_name = operation or func.__qualname__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成或复用trace_id
            trace_id = _current_trace_id.get()
            if not trace_id:
                trace_id = str(uuid.uuid4())[:8]
                _current_trace_id.set(trace_id)
            
            span_id = str(uuid.uuid4())[:8]
            span_stack = _current_span_stack.get()
            parent_span_id = span_stack[-1] if span_stack else ""
            span_stack.append(span_id)
            _current_span_stack.set(span_stack)
            _current_span_id.set(span_id)
            
            start_time = time.time()
            
            # 记录调用
            log_data = {
                "trace_id": trace_id,
                "span_id": span_id,
                "parent_span_id": parent_span_id,
                "operation": op_name,
                "function": func.__qualname__,
                "module": func.__module__,
                "event": "call",
            }
            
            if log_args:
                # 安全地记录参数
                try:
                    bound = inspect.signature(func).bind(*args, **kwargs)
                    bound.apply_defaults()
                    safe_args = {}
                    for name, value in bound.arguments.items():
                        try:
                            repr_str = _safe_repr(value)
                            if len(repr_str) > max_arg_length:
                                repr_str = repr_str[:max_arg_length] + "..."
                            safe_args[name] = repr_str
                        except Exception:
                            safe_args[name] = "<unserializable>"
                    log_data["args"] = safe_args
                except Exception as e:
                    log_data["args_error"] = str(e)
            
            _log_at_level(level, f"[TRACE] {op_name} CALL", log_data)
            
            try:
                result = func(*args, **kwargs)
                
                duration = (time.time() - start_time) * 1000
                
                # 记录返回
                result_log = {
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "operation": op_name,
                    "event": "return",
                    "duration_ms": round(duration, 2),
                }
                
                if log_result:
                    try:
                        result_str = _safe_repr(result)
                        if len(result_str) > max_arg_length:
                            result_str = result_str[:max_arg_length] + "..."
                        result_log["result"] = result_str
                    except Exception:
                        result_log["result"] = "<unserializable>"
                
                _log_at_level(level, f"[TRACE] {op_name} RETURN", result_log)
                
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                if log_exception:
                    error_log = {
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "operation": op_name,
                        "event": "exception",
                        "duration_ms": round(duration, 2),
                        "exception_type": type(e).__name__,
                        "exception_msg": str(e),
                    }
                    logger.error(f"[TRACE] {op_name} EXCEPTION", extra=error_log)
                
                raise
                
            finally:
                # 弹出span
                span_stack = _current_span_stack.get()
                if span_stack and span_stack[-1] == span_id:
                    span_stack.pop()
                    _current_span_stack.set(span_stack)
                    if span_stack:
                        _current_span_id.set(span_stack[-1])
                    else:
                        _current_span_id.set("")
                        _current_trace_id.set("")
        
        return wrapper  # type: ignore
    
    return decorator


def get_current_trace_id() -> str:
    """获取当前追踪ID."""
    return _current_trace_id.get()


def get_current_span_id() -> str:
    """获取当前Span ID."""
    return _current_span_id.get()


def _safe_repr(obj: Any) -> str:
    """安全地获取对象字符串表示."""
    try:
        if isinstance(obj, (str, int, float, bool, type(None))):
            return repr(obj)
        if isinstance(obj, (list, tuple)):
            items = [_safe_repr(x) for x in obj[:5]]
            if len(obj) > 5:
                items.append(f"...({len(obj)-5} more)")
            return f"[{', '.join(items)}]"
        if isinstance(obj, dict):
            items = []
            for i, (k, v) in enumerate(obj.items()):
                if i >= 5:
                    items.append(f"...({len(obj)-5} more)")
                    break
                items.append(f"{_safe_repr(k)}: {_safe_repr(v)}")
            return "{" + ", ".join(items) + "}"
        if hasattr(obj, "__class__"):
            return f"<{obj.__class__.__name__}>"
        return repr(obj)
    except Exception:
        return "<repr_error>"


def _log_at_level(level: LogLevel, msg: str, data: Dict[str, Any]) -> None:
    """根据级别记录日志."""
    # 将数据序列化为消息的一部分
    import json
    try:
        data_str = json.dumps(data, ensure_ascii=False, default=str)
        full_msg = f"{msg} | {data_str}"
    except Exception:
        full_msg = msg
    
    if level == LogLevel.DEBUG:
        logger.debug(full_msg)
    elif level == LogLevel.INFO:
        logger.info(full_msg)
    elif level == LogLevel.WARNING:
        logger.warning(full_msg)
    elif level == LogLevel.ERROR:
        logger.error(full_msg)
    elif level == LogLevel.CRITICAL:
        logger.critical(full_msg)


# 便捷函数
@contextmanager
def trace_block(operation: str, **kwargs):
    """追踪代码块的便捷上下文管理器."""
    with TraceContext(operation, **kwargs):
        yield


def trace_method(level: LogLevel = LogLevel.DEBUG):
    """类方法追踪装饰器的便捷版本."""
    return trace_call(level=level)
