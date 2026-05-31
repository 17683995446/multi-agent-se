"""代码质量问题定义 - 阶段22.

定义代码质量检查的结果封装：
- 问题严重程度
- 问题类型分类
- 代码位置信息
- 修复建议
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class Severity(Enum):
    """问题严重程度."""
    CRITICAL = "critical"      # 严重：可能导致系统崩溃或安全漏洞
    HIGH = "high"              # 高：明显缺陷，必须修复
    MEDIUM = "medium"          # 中：建议修复，影响代码质量
    LOW = "low"                # 低：轻微问题，可选修复
    INFO = "info"              # 信息：提示性建议


class IssueCategory(Enum):
    """问题类别."""
    SYNTAX = "syntax"                  # 语法错误
    STYLE = "style"                    # 代码风格
    COMPLEXITY = "complexity"          # 复杂度问题
    SECURITY = "security"              # 安全问题
    PERFORMANCE = "performance"        # 性能问题
    BUG_RISK = "bug_risk"              # 潜在Bug
    DOCUMENTATION = "documentation"    # 文档问题
    TYPE_CHECKING = "type_checking"    # 类型检查
    IMPORT = "import"                  # 导入问题
    COMPATIBILITY = "compatibility"    # 兼容性问题


class IssueSource(Enum):
    """问题来源."""
    RUFF = "ruff"                      # Ruff linter
    PYTEST = "pytest"                  # Pytest测试
    BANDIT = "bandit"                  # Bandit安全扫描
    MYPY = "mypy"                      # MyPy类型检查
    PYLINT = "pylint"                  # Pylint
    CUSTOM = "custom"                  # 自定义规则


@dataclass
class CodeLocation:
    """代码位置信息."""
    file_path: str = ""
    line_start: int = 0
    column_start: int = 0
    line_end: int = 0
    column_end: int = 0
    
    def __post_init__(self) -> None:
        """确保结束位置合理."""
        if self.line_end == 0:
            self.line_end = self.line_start
        if self.column_end == 0:
            self.column_end = self.column_start
    
    @property
    def line_range(self) -> str:
        """行范围字符串."""
        if self.line_start == self.line_end:
            return f"line {self.line_start}"
        return f"lines {self.line_start}-{self.line_end}"
    
    @property
    def position(self) -> str:
        """完整位置字符串."""
        if self.line_start == self.line_end and self.column_start == self.column_end:
            return f"{self.file_path}:{self.line_start}:{self.column_start}"
        return f"{self.file_path}:{self.line_start}:{self.column_start}-{self.line_end}:{self.column_end}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "file_path": self.file_path,
            "line_start": self.line_start,
            "column_start": self.column_start,
            "line_end": self.line_end,
            "column_end": self.column_end,
            "line_range": self.line_range,
            "position": self.position,
        }


@dataclass
class FixSuggestion:
    """修复建议."""
    description: str = ""                    # 修复描述
    replacement_code: Optional[str] = None   # 替换代码
    auto_fixable: bool = False               # 是否可自动修复
    confidence: float = 1.0                  # 修复置信度 (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "description": self.description,
            "replacement_code": self.replacement_code,
            "auto_fixable": self.auto_fixable,
            "confidence": self.confidence,
        }


@dataclass
class QualityIssue:
    """代码质量问题.
    
    统一的问题描述结构，整合各种检查工具的结果
    """
    # 基本信息
    rule_id: str = ""                        # 规则ID (如 E501, W0611)
    message: str = ""                        # 问题描述
    severity: Severity = Severity.LOW        # 严重程度
    category: IssueCategory = IssueCategory.STYLE  # 问题类别
    source: IssueSource = IssueSource.CUSTOM  # 来源工具
    
    # 位置信息
    location: CodeLocation = field(default_factory=CodeLocation)
    
    # 代码片段
    code_snippet: str = ""                   # 相关代码片段
    context_before: str = ""                 # 前文代码
    context_after: str = ""                  # 后文代码
    
    # 修复建议
    fix: Optional[FixSuggestion] = None
    
    # 元数据
    documentation_url: str = ""              # 规则文档链接
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理."""
        if self.fix is None:
            self.fix = FixSuggestion()
    
    @property
    def is_critical(self) -> bool:
        """是否严重问题."""
        return self.severity == Severity.CRITICAL
    
    @property
    def is_high_priority(self) -> bool:
        """是否高优先级."""
        return self.severity in (Severity.CRITICAL, Severity.HIGH)
    
    @property
    def is_auto_fixable(self) -> bool:
        """是否可自动修复."""
        return self.fix is not None and self.fix.auto_fixable

    @property
    def file_path(self) -> str:
        """文件路径（便捷访问）."""
        return self.location.file_path

    @property
    def full_message(self) -> str:
        """完整问题描述."""
        parts = [
            f"[{self.rule_id}]",
            f"{self.severity.value.upper()}: {self.message}",
            f"  at {self.location.position}",
        ]
        if self.code_snippet:
            parts.append(f"  code: {self.code_snippet[:50]}{'...' if len(self.code_snippet) > 50 else ''}")
        return "\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "source": self.source.value,
            "location": self.location.to_dict(),
            "code_snippet": self.code_snippet,
            "is_auto_fixable": self.is_auto_fixable,
            "fix": self.fix.to_dict() if self.fix else None,
            "documentation_url": self.documentation_url,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_ruff_issue(
        cls,
        code: str,
        message: str,
        file_path: str,
        line: int,
        col: int,
        end_line: int = 0,
        end_col: int = 0,
        fixable: bool = False,
    ) -> "QualityIssue":
        """从Ruff问题创建.
        
        Args:
            code: Ruff规则代码
            message: 问题消息
            file_path: 文件路径
            line: 起始行
            col: 起始列
            end_line: 结束行
            end_col: 结束列
            fixable: 是否可修复
            
        Returns:
            QualityIssue实例
        """
        # 映射Ruff代码到严重程度和类别
        severity, category = cls._map_ruff_code(code)
        
        location = CodeLocation(
            file_path=file_path,
            line_start=line,
            column_start=col,
            line_end=end_line or line,
            column_end=end_col or col,
        )
        
        fix = FixSuggestion(
            auto_fixable=fixable,
            description="Auto-fix available via ruff" if fixable else "",
        )
        
        return cls(
            rule_id=code,
            message=message,
            severity=severity,
            category=category,
            source=IssueSource.RUFF,
            location=location,
            fix=fix,
            documentation_url=f"https://docs.astral.sh/ruff/rules/{code}/",
        )
    
    @staticmethod
    def _map_ruff_code(code: str) -> tuple:
        """映射Ruff代码到严重程度和类别.
        
        Returns:
            (Severity, IssueCategory) 元组
        """
        # 错误代码前缀映射
        prefix_map = {
            "E": (Severity.HIGH, IssueCategory.BUG_RISK),      # pycodestyle errors
            "W": (Severity.MEDIUM, IssueCategory.STYLE),       # pycodestyle warnings
            "F": (Severity.HIGH, IssueCategory.BUG_RISK),      # Pyflakes
            "I": (Severity.LOW, IssueCategory.IMPORT),         # isort
            "N": (Severity.LOW, IssueCategory.STYLE),          # pep8-naming
            "D": (Severity.LOW, IssueCategory.DOCUMENTATION),  # pydocstyle
            "UP": (Severity.LOW, IssueCategory.COMPATIBILITY), # pyupgrade
            "B": (Severity.MEDIUM, IssueCategory.BUG_RISK),    # flake8-bugbear
            "C4": (Severity.LOW, IssueCategory.PERFORMANCE),   # flake8-comprehensions
            "SIM": (Severity.LOW, IssueCategory.COMPLEXITY),   # flake8-simplify
            "C90": (Severity.MEDIUM, IssueCategory.COMPLEXITY), # mccabe complexity
            "S": (Severity.CRITICAL, IssueCategory.SECURITY),  # flake8-bandit
        }
        
        # 提取前缀
        for prefix, (severity, category) in prefix_map.items():
            if code.startswith(prefix):
                return severity, category
        
        return Severity.LOW, IssueCategory.STYLE


@dataclass
class QualityReport:
    """代码质量报告.
    
    汇总单次检查的所有问题
    """
    file_path: str = ""
    issues: List[QualityIssue] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.now)
    source: IssueSource = IssueSource.CUSTOM
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_issues(self) -> int:
        """问题总数."""
        return len(self.issues)
    
    @property
    def critical_count(self) -> int:
        """严重问题数."""
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)
    
    @property
    def high_count(self) -> int:
        """高优先级问题数."""
        return sum(1 for i in self.issues if i.severity == Severity.HIGH)
    
    @property
    def medium_count(self) -> int:
        """中优先级问题数."""
        return sum(1 for i in self.issues if i.severity == Severity.MEDIUM)
    
    @property
    def low_count(self) -> int:
        """低优先级问题数."""
        return sum(1 for i in self.issues if i.severity == Severity.LOW)
    
    @property
    def info_count(self) -> int:
        """信息性问题数."""
        return sum(1 for i in self.issues if i.severity == Severity.INFO)
    
    @property
    def auto_fixable_count(self) -> int:
        """可自动修复的问题数."""
        return sum(1 for i in self.issues if i.is_auto_fixable)
    
    @property
    def has_critical_issues(self) -> bool:
        """是否有严重问题."""
        return self.critical_count > 0
    
    @property
    def is_clean(self) -> bool:
        """是否无问题."""
        return len(self.issues) == 0
    
    def get_issues_by_severity(self, severity: Severity) -> List[QualityIssue]:
        """按严重程度获取问题."""
        return [i for i in self.issues if i.severity == severity]
    
    def get_issues_by_category(self, category: IssueCategory) -> List[QualityIssue]:
        """按类别获取问题."""
        return [i for i in self.issues if i.category == category]
    
    def get_auto_fixable_issues(self) -> List[QualityIssue]:
        """获取可自动修复的问题."""
        return [i for i in self.issues if i.is_auto_fixable]
    
    def merge(self, other: "QualityReport") -> "QualityReport":
        """合并另一个报告."""
        merged = QualityReport(
            file_path=self.file_path or other.file_path,
            issues=self.issues + other.issues,
            checked_at=datetime.now(),
            metadata={**self.metadata, **other.metadata},
        )
        return merged
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "file_path": self.file_path,
            "total_issues": self.total_issues,
            "severity_counts": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
            },
            "auto_fixable": self.auto_fixable_count,
            "is_clean": self.is_clean,
            "checked_at": self.checked_at.isoformat(),
            "source": self.source.value,
            "issues": [i.to_dict() for i in self.issues],
        }
    
    def format_summary(self) -> str:
        """格式化摘要."""
        lines = [
            f"Quality Report for: {self.file_path}",
            f"  Total Issues: {self.total_issues}",
            f"    Critical: {self.critical_count}",
            f"    High: {self.high_count}",
            f"    Medium: {self.medium_count}",
            f"    Low: {self.low_count}",
            f"    Info: {self.info_count}",
            f"  Auto-fixable: {self.auto_fixable_count}",
        ]
        return "\n".join(lines)


# ========== 便捷函数 ==========

def create_issue(
    rule_id: str,
    message: str,
    file_path: str,
    line: int = 1,
    severity: Severity = Severity.LOW,
    category: IssueCategory = IssueCategory.STYLE,
) -> QualityIssue:
    """创建问题的便捷函数.
    
    Args:
        rule_id: 规则ID
        message: 问题消息
        file_path: 文件路径
        line: 行号
        severity: 严重程度
        category: 问题类别
        
    Returns:
        QualityIssue实例
    """
    return QualityIssue(
        rule_id=rule_id,
        message=message,
        severity=severity,
        category=category,
        location=CodeLocation(file_path=file_path, line_start=line),
    )
