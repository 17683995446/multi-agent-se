"""统一异常体系 - 阶段10.

正交拆分：异常捕获机制独立于配置模块
遵循第一性原理 — 每个异常类单一职责，错误码分层管理
"""

from typing import Any, Dict, Optional


# ========== 基础异常 ==========
class MASEError(Exception):
    """MASE系统基础异常.

    所有自定义异常的根类，提供统一的错误码和详情字段
    """

    def __init__(
        self,
        message: str,
        error_code: str = "MASE_001",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ========== 配置层异常 (CFG) ==========
class ConfigurationError(MASEError):
    """配置错误.

    配置文件加载、解析、验证失败时抛出
    """

    def __init__(
        self,
        message: str,
        config_key: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="MASE_CFG_001", details=details)
        self.config_key = config_key


class ConfigurationNotFoundError(ConfigurationError):
    """配置文件未找到."""

    def __init__(
        self,
        config_path: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            f"配置文件未找到: {config_path}",
            config_key=config_path,
            details=details,
        )
        self.config_path = config_path


# ========== Agent层异常 (AGENT) ==========
class AgentError(MASEError):
    """Agent执行错误.

    Agent初始化、执行、通信失败时抛出
    """

    def __init__(
        self,
        message: str,
        agent_name: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="MASE_AGENT_001", details=details)
        self.agent_name = agent_name


class AgentTimeoutError(AgentError):
    """Agent执行超时."""

    def __init__(
        self,
        agent_name: str,
        timeout: float = 0.0,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            f"Agent '{agent_name}' 执行超时 ({timeout}s)",
            agent_name=agent_name,
            details=details,
        )
        self.timeout = timeout


class AgentCommunicationError(AgentError):
    """Agent通信错误."""

    def __init__(
        self,
        sender: str = "",
        receiver: str = "",
        message: str = "Agent通信失败",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            agent_name=sender,
            details=details,
        )
        self.sender = sender
        self.receiver = receiver


# ========== 调度层异常 (SCHED) ==========
class SchedulerError(MASEError):
    """调度器错误.

    任务调度、DAG验证、状态转换失败时抛出
    """

    def __init__(
        self,
        message: str,
        task_id: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="MASE_SCHED_001", details=details)
        self.task_id = task_id


class CyclicDependencyError(SchedulerError):
    """循环依赖错误."""

    def __init__(
        self,
        cycle: Optional[list] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        cycle_str = " -> ".join(cycle) if cycle else "unknown"
        super().__init__(
            f"检测到循环依赖: {cycle_str}",
            details=details or {"cycle": cycle},
        )
        self.cycle = cycle or []


# ========== 代码质量异常 (QUALITY) ==========
class QualityError(MASEError):
    """代码质量错误.

    Lint检查、格式化、覆盖率不达标时抛出
    """

    def __init__(
        self,
        message: str,
        rule_code: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="MASE_QUALITY_001", details=details)
        self.rule_code = rule_code


class CoverageThresholdError(QualityError):
    """覆盖率不达标."""

    def __init__(
        self,
        actual: float,
        required: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            f"覆盖率不达标: {actual:.1f}% < {required:.1f}%",
            rule_code="COVERAGE",
            details=details or {"actual": actual, "required": required},
        )
        self.actual = actual
        self.required = required


# ========== 解析层异常 (PARSE) ==========
class ParseError(MASEError):
    """代码解析错误.

    AST解析、Tree-sitter解析失败时抛出
    """

    def __init__(
        self,
        message: str,
        file_path: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code="MASE_PARSE_001", details=details)
        self.file_path = file_path


class UnsupportedLanguageError(ParseError):
    """不支持的语言."""

    def __init__(
        self,
        language: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            f"不支持的语言: {language}",
            details=details or {"language": language},
        )
        self.language = language


# ========== 工具函数 ==========
def get_error_hierarchy() -> Dict[str, list]:
    """获取异常层级结构.

    Returns:
        异常层级字典，键为基类名，值为子类名列表
    """
    import inspect

    hierarchy: Dict[str, list] = {}
    all_exceptions = [
        MASEError,
        ConfigurationError, ConfigurationNotFoundError,
        AgentError, AgentTimeoutError, AgentCommunicationError,
        SchedulerError, CyclicDependencyError,
        QualityError, CoverageThresholdError,
        ParseError, UnsupportedLanguageError,
    ]

    for exc_class in all_exceptions:
        bases = [b.__name__ for b in exc_class.__bases__ if b is not Exception]
        for base_name in bases:
            if base_name not in hierarchy:
                hierarchy[base_name] = []
            hierarchy[base_name].append(exc_class.__name__)

    return hierarchy


def format_error(error: Exception) -> str:
    """格式化异常信息.

    Args:
        error: 异常实例

    Returns:
        格式化的错误字符串
    """
    if isinstance(error, MASEError):
        return str(error)
    return f"{type(error).__name__}: {error}"
