"""最小熵全局规范体系 - 阶段15.

实现系统熵值计算、规范符合度检测、熵减优化建议、规范文档生成
"""

from multi_agent_se.core.entropy.calculator import (
    EntropyType,
    EntropyMetric,
    EntropyReport,
    EntropyCalculator,
    calculate_module_entropy,
)

from multi_agent_se.core.entropy.compliance import (
    ComplianceLevel,
    ComplianceCategory,
    ComplianceRule,
    ComplianceViolation,
    ComplianceResult,
    ComplianceChecker,
    default_compliance_checker,
)

from multi_agent_se.core.entropy.optimizer import (
    OptimizationPriority,
    OptimizationCategory,
    OptimizationSuggestion,
    OptimizationPlan,
    EntropyOptimizer,
    create_optimizer,
)

from multi_agent_se.core.entropy.reporter import (
    ReportFormat,
    ReportType,
    ReportMetadata,
    GeneratedReport,
    EntropyReporter,
    create_reporter,
)

__all__ = [
    # 熵值计算
    "EntropyType",
    "EntropyMetric",
    "EntropyReport",
    "EntropyCalculator",
    "calculate_module_entropy",
    # 规范符合度
    "ComplianceLevel",
    "ComplianceCategory",
    "ComplianceRule",
    "ComplianceViolation",
    "ComplianceResult",
    "ComplianceChecker",
    "default_compliance_checker",
    # 熵减优化
    "OptimizationPriority",
    "OptimizationCategory",
    "OptimizationSuggestion",
    "OptimizationPlan",
    "EntropyOptimizer",
    "create_optimizer",
    # 报告生成
    "ReportFormat",
    "ReportType",
    "ReportMetadata",
    "GeneratedReport",
    "EntropyReporter",
    "create_reporter",
]
