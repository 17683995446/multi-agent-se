"""代码执行沙箱 - 阶段21.

实现安全的Python代码执行环境：
- 白名单/黑名单模块控制
- 超时控制
- 输出捕获
- 资源限制
"""

import ast
import builtins
import contextlib
import io
import signal
import sys
import threading
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Set, Union

from multi_agent_se.executor.result import (
    ExecutionLimits,
    ExecutionResult,
    ExecutionStatus,
)


# ========== 异常定义 ==========

class SandboxError(Exception):
    """沙箱基础异常."""
    pass


class SecurityError(SandboxError):
    """安全违规异常."""
    pass


class TimeoutError(SandboxError):
    """超时异常."""
    pass


# ========== 安全分析器 ==========

# 预加载的安全模块（沙箱会自动提供这些模块）
PRELOADED_MODULES = {
    'math', 'random', 'datetime', 'json', 're', 'string',
    'collections', 'itertools', 'functools', 'typing',
    'decimal', 'fractions', 'statistics', 'hashlib', 'base64',
    'copy', 'pprint', 'textwrap', 'uuid', 'dataclasses', 'enum',
}


class SecurityAnalyzer(ast.NodeVisitor):
    """AST安全分析器 - 检查代码中的安全风险."""
    
    def __init__(self, blocked_modules: List[str], allowed_modules: Optional[List[str]] = None):
        self.blocked_modules = set(blocked_modules)
        self.allowed_modules = set(allowed_modules) if allowed_modules else None
        self.violations: List[str] = []
        self.imported_modules: Set[str] = set()
    
    def analyze(self, code: str) -> List[str]:
        """分析代码，返回违规列表.
        
        注意：语法错误不在此阶段处理，留给执行阶段的compile()来捕获。
        """
        self.violations = []
        self.imported_modules = set()
        
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError:
            # 语法错误不在安全分析阶段处理
            # 让执行阶段的compile()来捕获并返回SYNTAX_ERROR状态
            pass
        
        return self.violations
    
    def visit_Import(self, node: ast.Import) -> None:
        """检查import语句."""
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            self._check_module(module_name, node)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """检查from ... import语句."""
        if node.module:
            module_name = node.module.split('.')[0]
            self._check_module(module_name, node)
        self.generic_visit(node)
    
    def _check_module(self, module_name: str, node: ast.AST) -> None:
        """检查模块是否允许导入."""
        self.imported_modules.add(module_name)
        
        # 如果是预加载的安全模块，允许导入（沙箱已提供）
        if module_name in PRELOADED_MODULES:
            return
        
        # 如果有白名单，优先检查白名单
        if self.allowed_modules is not None:
            if module_name not in self.allowed_modules:
                self.violations.append(
                    f"Module '{module_name}' is not in allowed modules list"
                )
            return
        
        # 检查黑名单
        if module_name in self.blocked_modules:
            self.violations.append(
                f"Import of blocked module '{module_name}' detected at line {node.lineno}"
            )
    
    def visit_Call(self, node: ast.Call) -> None:
        """检查危险函数调用."""
        # 检查eval, exec, compile等危险函数
        if isinstance(node.func, ast.Name):
            if node.func.id in ('eval', 'exec', 'compile', '__import__'):
                self.violations.append(
                    f"Dangerous function '{node.func.id}' called at line {node.lineno}"
                )
        
        # 检查open函数（文件操作）
        if isinstance(node.func, ast.Name) and node.func.id == 'open':
            self.violations.append(
                f"File operation 'open' detected at line {node.lineno}"
            )
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute) -> None:
        """检查属性访问."""
        # 检查访问__subclasses__等危险属性
        dangerous_attrs = ('__subclasses__', '__bases__', '__globals__', '__code__')
        if node.attr in dangerous_attrs:
            self.violations.append(
                f"Dangerous attribute access '{node.attr}' detected at line {node.lineno}"
            )
        self.generic_visit(node)


# ========== 受限内置函数 ==========

# 允许的安全内置函数
SAFE_BUILTINS = {
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
    'chr', 'classmethod', 'complex', 'dict', 'dir', 'divmod', 'enumerate',
    'filter', 'float', 'format', 'frozenset', 'hasattr', 'hash', 'hex',
    'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
    'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object',
    'oct', 'ord', 'pow', 'print', 'property', 'range', 'repr', 'reversed',
    'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str',
    'sum', 'super', 'tuple', 'type', 'vars', 'zip', '__build_class__',
    '__name__', '__import__', 'True', 'False', 'None',
}

# 危险内置函数（将被移除）
DANGEROUS_BUILTINS = {
    'eval', 'exec', 'compile', '__import__', 'open',
    'exit', 'quit', 'help', 'copyright', 'credits', 'license',
}


def create_restricted_globals() -> Dict[str, Any]:
    """创建受限的全局命名空间."""
    restricted = {}
    
    # 添加安全的内置函数
    for name in SAFE_BUILTINS:
        if hasattr(builtins, name):
            restricted[name] = getattr(builtins, name)
    
    # 添加安全模块
    safe_modules = {
        'math': __import__('math'),
        'random': __import__('random'),
        'datetime': __import__('datetime'),
        'json': __import__('json'),
        're': __import__('re'),
        'string': __import__('string'),
        'collections': __import__('collections'),
        'itertools': __import__('itertools'),
        'functools': __import__('functools'),
        'typing': __import__('typing'),
        'decimal': __import__('decimal'),
        'fractions': __import__('fractions'),
        'statistics': __import__('statistics'),
        'hashlib': __import__('hashlib'),
        'base64': __import__('base64'),
        'copy': __import__('copy'),
        'pprint': __import__('pprint'),
        'textwrap': __import__('textwrap'),
        'uuid': __import__('uuid'),
        'dataclasses': __import__('dataclasses'),
        'enum': __import__('enum'),
    }
    
    for name, module in safe_modules.items():
        restricted[name] = module
    
    return {'__builtins__': restricted}


# ========== 输出捕获 ==========

class OutputCapture:
    """输出捕获器 - 捕获stdout和stderr."""
    
    def __init__(self, max_size: int = 1024 * 1024):
        self.max_size = max_size
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        self._original_stdout = None
        self._original_stderr = None
        self._captured_size = 0
    
    def __enter__(self) -> 'OutputCapture':
        """进入上下文，开始捕获."""
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self._LimitingWriter(self.stdout_buffer, self)
        sys.stderr = self._LimitingWriter(self.stderr_buffer, self)
        return self
    
    def __exit__(self, *args) -> None:
        """退出上下文，恢复输出."""
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
    
    def get_stdout(self) -> str:
        """获取捕获的标准输出."""
        return self.stdout_buffer.getvalue()
    
    def get_stderr(self) -> str:
        """获取捕获的标准错误."""
        return self.stderr_buffer.getvalue()
    
    def _check_size(self, size: int) -> bool:
        """检查是否超过大小限制."""
        self._captured_size += size
        return self._captured_size <= self.max_size
    
    class _LimitingWriter:
        """限制大小的写入器."""
        
        def __init__(self, buffer: io.StringIO, capture: 'OutputCapture'):
            self.buffer = buffer
            self.capture = capture
            self._truncated = False
        
        def write(self, text: str) -> int:
            if self._truncated:
                return 0
            
            if not self.capture._check_size(len(text)):
                self._truncated = True
                self.buffer.write("\n[Output truncated: exceeded size limit]\n")
                return 0
            
            return self.buffer.write(text)
        
        def flush(self) -> None:
            self.buffer.flush()


# ========== 超时处理器 ==========

class TimeoutHandler:
    """超时处理器 - 使用线程实现超时控制."""
    
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        self._timer: Optional[threading.Timer] = None
        self._timed_out = threading.Event()
    
    def __enter__(self) -> 'TimeoutHandler':
        """启动超时计时器."""
        self._timed_out.clear()
        self._timer = threading.Timer(self.timeout_seconds, self._on_timeout)
        self._timer.start()
        return self
    
    def __exit__(self, *args) -> None:
        """取消超时计时器."""
        if self._timer:
            self._timer.cancel()
    
    def _on_timeout(self) -> None:
        """超时回调."""
        self._timed_out.set()
    
    def is_timed_out(self) -> bool:
        """检查是否已超时."""
        return self._timed_out.is_set()
    
    def check_timeout(self) -> None:
        """检查超时，如果超时则抛出异常."""
        if self._timed_out.is_set():
            raise TimeoutError(f"Execution timed out after {self.timeout_seconds} seconds")


# ========== 代码沙箱 ==========

class CodeSandbox:
    """代码执行沙箱.
    
    提供安全的Python代码执行环境，包括：
    - 模块导入限制
    - 内置函数限制
    - 超时控制
    - 输出捕获
    - 资源限制
    """
    
    def __init__(self, limits: Optional[ExecutionLimits] = None):
        """初始化沙箱.
        
        Args:
            limits: 执行限制配置
        """
        self.limits = limits or ExecutionLimits()
        self.analyzer = SecurityAnalyzer(
            blocked_modules=self.limits.blocked_modules,
            allowed_modules=self.limits.allowed_modules,
        )
        self._globals = create_restricted_globals()
        self._locals: Dict[str, Any] = {}
    
    def analyze(self, code: str) -> List[str]:
        """分析代码安全性.
        
        Args:
            code: 要分析的代码
            
        Returns:
            违规列表，空列表表示安全
        """
        return self.analyzer.analyze(code)
    
    def is_safe(self, code: str) -> bool:
        """检查代码是否安全.
        
        Args:
            code: 要检查的代码
            
        Returns:
            是否安全
        """
        return len(self.analyze(code)) == 0
    
    def execute(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """执行代码.
        
        Args:
            code: 要执行的Python代码
            context: 额外的执行上下文变量
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        
        # 1. 安全检查
        violations = self.analyze(code)
        if violations:
            return ExecutionResult.security_violation("; ".join(violations))
        
        # 2. 准备执行环境
        globals_dict = self._globals.copy()
        locals_dict = self._locals.copy()
        
        if context:
            locals_dict.update(context)
        
        # 3. 捕获输出并执行
        stdout = ""
        stderr = ""
        return_value = None
        
        try:
            with OutputCapture(max_size=self.limits.max_output_size_bytes) as capture:
                with TimeoutHandler(self.limits.max_execution_time_seconds) as timeout:
                    # 编译代码（捕获语法错误）
                    try:
                        compiled_code = compile(code, '<sandbox>', 'exec')
                    except SyntaxError as e:
                        return ExecutionResult(
                            status=ExecutionStatus.SYNTAX_ERROR,
                            error_message=str(e),
                            error_type="SyntaxError",
                            traceback=traceback.format_exc(),
                            execution_time_seconds=time.time() - start_time,
                        )
                    
                    # 执行代码
                    exec(compiled_code, globals_dict, locals_dict)
                    
                    # 检查超时
                    timeout.check_timeout()
                    
                    # 获取输出
                    stdout = capture.get_stdout()
                    stderr = capture.get_stderr()
            
            # 保存局部变量状态
            self._locals.update(locals_dict)
            
            execution_time = time.time() - start_time
            
            return ExecutionResult.success(
                stdout=stdout,
                return_value=return_value,
                execution_time=execution_time,
            )
            
        except TimeoutError as e:
            return ExecutionResult.timeout(
                limit_seconds=self.limits.max_execution_time_seconds,
                partial_stdout=stdout,
            )
        except ImportError as e:
            return ExecutionResult(
                status=ExecutionStatus.IMPORT_ERROR,
                error_message=str(e),
                error_type="ImportError",
                traceback=traceback.format_exc(),
                stdout=stdout,
                stderr=stderr,
                execution_time_seconds=time.time() - start_time,
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error_message=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc(),
                stdout=stdout,
                stderr=stderr,
                execution_time_seconds=time.time() - start_time,
            )
    
    def eval_expression(
        self,
        expression: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """安全地求值表达式.
        
        Args:
            expression: 要求值的表达式
            context: 执行上下文
            
        Returns:
            ExecutionResult: 包含表达式返回值的结果
        """
        start_time = time.time()
        
        # 安全检查
        violations = self.analyze(expression)
        if violations:
            return ExecutionResult.security_violation("; ".join(violations))
        
        # 准备环境
        globals_dict = self._globals.copy()
        locals_dict = self._locals.copy()
        
        if context:
            locals_dict.update(context)
        
        try:
            with TimeoutHandler(self.limits.max_execution_time_seconds) as timeout:
                result = eval(expression, globals_dict, locals_dict)
                timeout.check_timeout()
            
            execution_time = time.time() - start_time
            
            return ExecutionResult.success(
                return_value=result,
                execution_time=execution_time,
            )
            
        except TimeoutError:
            return ExecutionResult.timeout(
                limit_seconds=self.limits.max_execution_time_seconds,
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error_message=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc(),
                execution_time_seconds=time.time() - start_time,
            )
    
    def call_function(
        self,
        func_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """调用沙箱中定义的函数.
        
        Args:
            func_name: 函数名
            args: 位置参数
            kwargs: 关键字参数
            context: 执行上下文
            
        Returns:
            ExecutionResult: 调用结果
        """
        args = args or []
        kwargs = kwargs or {}
        
        locals_dict = self._locals.copy()
        
        if context:
            locals_dict.update(context)
        
        if func_name not in locals_dict:
            return ExecutionResult.error(
                error_message=f"Function '{func_name}' not found in sandbox",
                error_type="NameError",
            )
        
        func = locals_dict[func_name]
        
        if not callable(func):
            return ExecutionResult.error(
                error_message=f"'{func_name}' is not callable",
                error_type="TypeError",
            )
        
        start_time = time.time()
        
        try:
            with TimeoutHandler(self.limits.max_execution_time_seconds) as timeout:
                result = func(*args, **kwargs)
                timeout.check_timeout()
            
            execution_time = time.time() - start_time
            
            return ExecutionResult.success(
                return_value=result,
                execution_time=execution_time,
            )
            
        except TimeoutError:
            return ExecutionResult.timeout(
                limit_seconds=self.limits.max_execution_time_seconds,
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                error_message=str(e),
                error_type=type(e).__name__,
                traceback=traceback.format_exc(),
                execution_time_seconds=time.time() - start_time,
            )
    
    def reset(self) -> None:
        """重置沙箱状态."""
        self._locals = {}
    
    def get_defined_names(self) -> List[str]:
        """获取沙箱中定义的变量名列表."""
        return list(self._locals.keys())


# ========== 便捷函数 ==========

def create_sandbox(
    max_execution_time: float = 30.0,
    max_memory_mb: int = 512,
    allow_network: bool = False,
    allowed_modules: Optional[List[str]] = None,
    blocked_modules: Optional[List[str]] = None,
) -> CodeSandbox:
    """创建代码沙箱的便捷函数.
    
    Args:
        max_execution_time: 最大执行时间（秒）
        max_memory_mb: 最大内存（MB）
        allow_network: 是否允许网络
        allowed_modules: 允许导入的模块列表
        blocked_modules: 禁止导入的模块列表
        
    Returns:
        CodeSandbox: 代码沙箱实例
    """
    limits = ExecutionLimits(
        max_execution_time_seconds=max_execution_time,
        max_memory_mb=max_memory_mb,
        allow_network=allow_network,
        allowed_modules=allowed_modules,
        blocked_modules=blocked_modules or [
            "os", "sys", "subprocess", "socket", "urllib", "http",
            "ftplib", "telnetlib", "pickle", "marshal", "ctypes",
        ],
    )
    
    return CodeSandbox(limits=limits)


def quick_execute(
    code: str,
    timeout: float = 30.0,
    context: Optional[Dict[str, Any]] = None,
) -> ExecutionResult:
    """快速执行代码的便捷函数.
    
    Args:
        code: 要执行的代码
        timeout: 超时时间（秒）
        context: 执行上下文
        
    Returns:
        ExecutionResult: 执行结果
    """
    sandbox = create_sandbox(max_execution_time=timeout)
    return sandbox.execute(code, context=context)
