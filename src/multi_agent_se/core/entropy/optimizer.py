"""熵减优化建议 - 阶段15.

基于熵值计算结果生成优化建议：
- 代码重构建议
- 架构调整建议
- 命名规范化建议
- 依赖优化建议
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

from multi_agent_se.core.entropy.calculator import (
    EntropyCalculator,
    EntropyMetric,
    EntropyReport,
    EntropyType,
)
from multi_agent_se.core.entropy.compliance import (
    ComplianceChecker,
    ComplianceResult,
    ComplianceViolation,
)


class OptimizationPriority(Enum):
    """优化优先级."""
    CRITICAL = "critical"    # 必须立即修复
    HIGH = "high"            # 高优先级
    MEDIUM = "medium"        # 中等优先级
    LOW = "low"              # 低优先级
    OPTIONAL = "optional"    # 可选优化


class OptimizationCategory(Enum):
    """优化类别."""
    REFACTOR = "refactor"        # 代码重构
    ARCHITECTURE = "architecture"  # 架构调整
    NAMING = "naming"            # 命名规范
    DEPENDENCY = "dependency"    # 依赖优化
    DOCUMENTATION = "documentation"  # 文档完善
    COMPLEXITY = "complexity"    # 复杂度降低


@dataclass
class OptimizationSuggestion:
    """优化建议."""
    suggestion_id: str
    title: str
    description: str
    category: OptimizationCategory
    priority: OptimizationPriority
    target_file: str = ""
    target_line: int = 0
    current_state: str = ""
    suggested_state: str = ""
    expected_benefit: str = ""
    estimated_effort: str = ""  # 预估工作量：small/medium/large
    auto_fixable: bool = False
    fix_code: str = ""  # 自动修复代码（如适用）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.value,
            "target_file": self.target_file,
            "target_line": self.target_line,
            "current_state": self.current_state,
            "suggested_state": self.suggested_state,
            "expected_benefit": self.expected_benefit,
            "estimated_effort": self.estimated_effort,
            "auto_fixable": self.auto_fixable,
        }


@dataclass
class OptimizationPlan:
    """优化计划."""
    suggestions: List[OptimizationSuggestion] = field(default_factory=list)
    
    @property
    def total_suggestions(self) -> int:
        """建议总数."""
        return len(self.suggestions)
    
    @property
    def critical_count(self) -> int:
        """严重问题数."""
        return sum(
            1 for s in self.suggestions
            if s.priority == OptimizationPriority.CRITICAL
        )
    
    @property
    def high_count(self) -> int:
        """高优先级数."""
        return sum(
            1 for s in self.suggestions
            if s.priority == OptimizationPriority.HIGH
        )
    
    @property
    def auto_fixable_count(self) -> int:
        """可自动修复数."""
        return sum(1 for s in self.suggestions if s.auto_fixable)
    
    def get_by_priority(
        self,
        priority: OptimizationPriority,
    ) -> List[OptimizationSuggestion]:
        """按优先级获取建议."""
        return [s for s in self.suggestions if s.priority == priority]
    
    def get_by_category(
        self,
        category: OptimizationCategory,
    ) -> List[OptimizationSuggestion]:
        """按类别获取建议."""
        return [s for s in self.suggestions if s.category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_suggestions": self.total_suggestions,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "auto_fixable_count": self.auto_fixable_count,
            "suggestions": [s.to_dict() for s in self.suggestions],
        }


class EntropyOptimizer:
    """熵减优化器.
    
    基于熵值报告和合规检测结果生成优化建议
    """
    
    def __init__(self) -> None:
        """初始化优化器."""
        self._calculator = EntropyCalculator()
        self._compliance_checker = ComplianceChecker()
    
    def generate_suggestions(
        self,
        entropy_report: EntropyReport,
        compliance_result: Optional[ComplianceResult] = None,
    ) -> OptimizationPlan:
        """生成优化建议.
        
        Args:
            entropy_report: 熵值报告
            compliance_result: 合规检测结果（可选）
            
        Returns:
            OptimizationPlan
        """
        suggestions: List[OptimizationSuggestion] = []
        
        # 基于熵值指标生成建议
        for metric in entropy_report.metrics:
            metric_suggestions = self._suggestions_for_metric(metric)
            suggestions.extend(metric_suggestions)
        
        # 基于合规检测结果生成建议
        if compliance_result:
            compliance_suggestions = self._suggestions_for_compliance(
                compliance_result
            )
            suggestions.extend(compliance_suggestions)
        
        # 去重（基于suggestion_id）
        seen_ids: Set[str] = set()
        unique_suggestions: List[OptimizationSuggestion] = []
        for s in suggestions:
            if s.suggestion_id not in seen_ids:
                seen_ids.add(s.suggestion_id)
                unique_suggestions.append(s)
        
        return OptimizationPlan(suggestions=unique_suggestions)
    
    def _suggestions_for_metric(
        self,
        metric: EntropyMetric,
    ) -> List[OptimizationSuggestion]:
        """为单个熵值指标生成建议."""
        suggestions: List[OptimizationSuggestion] = []
        
        if metric.entropy_type == EntropyType.CODE_COMPLEXITY:
            suggestions.extend(self._complexity_suggestions(metric))
        elif metric.entropy_type == EntropyType.DEPENDENCY_CHAOS:
            suggestions.extend(self._dependency_suggestions(metric))
        elif metric.entropy_type == EntropyType.STATE_DISPERSION:
            suggestions.extend(self._state_suggestions(metric))
        elif metric.entropy_type == EntropyType.ARCHITECTURE_DRIFT:
            suggestions.extend(self._architecture_suggestions(metric))
        elif metric.entropy_type == EntropyType.NAMING_INCONSISTENCY:
            suggestions.extend(self._naming_suggestions(metric))
        
        return suggestions
    
    def _complexity_suggestions(
        self,
        metric: EntropyMetric,
    ) -> List[OptimizationSuggestion]:
        """复杂度优化建议."""
        suggestions: List[OptimizationSuggestion] = []
        details = metric.details
        
        # 函数过长建议
        max_lines = details.get("max_function_lines", 0)
        if max_lines > 50:
            suggestions.append(OptimizationSuggestion(
                suggestion_id="COMP-001",
                title="函数过长需要拆分",
                description=f"发现函数长度为{max_lines}行，超过推荐的50行",
                category=OptimizationCategory.COMPLEXITY,
                priority=OptimizationPriority.HIGH if max_lines > 100 else OptimizationPriority.MEDIUM,
                current_state=f"函数长度: {max_lines}行",
                suggested_state="拆分为多个小函数，每个函数不超过50行",
                expected_benefit="提高可读性，降低维护成本",
                estimated_effort="medium",
            ))
        
        # 嵌套深度建议
        max_depth = details.get("max_nesting_depth", 0)
        if max_depth > 3:
            suggestions.append(OptimizationSuggestion(
                suggestion_id="COMP-002",
                title="嵌套深度过大",
                description=f"最大嵌套深度为{max_depth}层，建议不超过3层",
                category=OptimizationCategory.COMPLEXITY,
                priority=OptimizationPriority.MEDIUM,
                current_state=f"嵌套深度: {max_depth}层",
                suggested_state="使用卫语句或提前返回减少嵌套",
                expected_benefit="提高代码可读性",
                estimated_effort="small",
            ))
        
        # 圈复杂度建议
        avg_complexity = details.get("avg_complexity", 0)
        if avg_complexity > 10:
            suggestions.append(OptimizationSuggestion(
                suggestion_id="COMP-003",
                title="圈复杂度过高",
                description=f"平均圈复杂度为{avg_complexity:.1f}，建议不超过10",
                category=OptimizationCategory.COMPLEXITY,
                priority=OptimizationPriority.HIGH,
                current_state=f"平均圈复杂度: {avg_complexity:.1f}",
                suggested_state="提取复杂逻辑为独立函数，使用策略模式",
                expected_benefit="降低测试难度，提高可维护性",
                estimated_effort="large",
            ))
        
        return suggestions
    
    def _dependency_suggestions(
        self,
        metric: EntropyMetric,
    ) -> List[OptimizationSuggestion]:
        """依赖优化建议."""
        suggestions: List[OptimizationSuggestion] = []
        details = metric.details
        
        # 循环依赖建议
        cycles = details.get("cycles", [])
        if cycles:
            suggestions.append(OptimizationSuggestion(
                suggestion_id="DEP-001",
                title="存在循环依赖",
                description=f"发现{len(cycles)}个循环依赖",
                category=OptimizationCategory.DEPENDENCY,
                priority=OptimizationPriority.CRITICAL,
                current_state=f"循环依赖: {cycles[:3]}",
                suggested_state="提取共享接口，使用依赖注入打破循环",
                expected_benefit="消除耦合，提高模块独立性",
                estimated_effort="large",
            ))
        
        # 依赖密度建议
        avg_deps = details.get("avg_dependencies", 0)
        if avg_deps > 10:
            suggestions.append(OptimizationSuggestion(
                suggestion_id="DEP-002",
                title="模块依赖过多",
                description=f"平均每个模块依赖{avg_deps:.1f}个其他模块",
                category=OptimizationCategory.DEPENDENCY,
                priority=OptimizationPriority.MEDIUM,
                current_state=f"平均依赖数: {avg_deps:.1f}",
                suggested_state="应用依赖倒置原则，减少直接依赖",
                expected_benefit="降低耦合度，提高可测试性",
                estimated_effort="medium",
            ))
        
        return suggestions
    
    def _state_suggestions(
        self,
        metric: EntropyMetric,
    ) -> List[OptimizationSuggestion]:
        """状态管理优化建议."""
        suggestions: List[OptimizationSuggestion] = []
        details = metric.details
        
        dispersion_ratio = details.get("dispersion_ratio", 0)
        if dispersion_ratio > 0.5:
            suggestions.append(OptimizationSuggestion(
                suggestion_id="STATE-001",
                title="状态分散度过高",
                description=f"状态分散比例为{dispersion_ratio:.2f}，建议集中管理",
                category=OptimizationCategory.ARCHITECTURE,
                priority=OptimizationPriority.HIGH,
                current_state=f"分散比例: {dispersion_ratio:.2f}",
                suggested_state="使用统一的状态管理器（如StateRegistry）",
                expected_benefit="提高状态可追溯性，减少bug",
                estimated_effort="medium",
            ))
        
        return suggestions
    
    def _architecture_suggestions(
        self,
        metric: EntropyMetric,
    ) -> List[OptimizationSuggestion]:
        """架构优化建议."""
        suggestions: List[OptimizationSuggestion] = []
        details = metric.details
        
        violation_count = details.get("violation_count", 0)
        if violation_count > 0:
            by_severity = details.get("by_severity", {})
            critical_count = by_severity.get("critical", 0)
            
            priority = OptimizationPriority.CRITICAL if critical_count > 0 else OptimizationPriority.HIGH
            
            suggestions.append(OptimizationSuggestion(
                suggestion_id="ARCH-001",
                title="架构规范违规",
                description=f"发现{violation_count}个架构违规（严重{critical_count}个）",
                category=OptimizationCategory.ARCHITECTURE,
                priority=priority,
                current_state=f"违规数: {violation_count}",
                suggested_state="修复架构违规，确保依赖方向正确",
                expected_benefit="维护架构完整性，防止技术债务累积",
                estimated_effort="large",
            ))
        
        return suggestions
    
    def _naming_suggestions(
        self,
        metric: EntropyMetric,
    ) -> List[OptimizationSuggestion]:
        """命名优化建议."""
        suggestions: List[OptimizationSuggestion] = []
        details = metric.details
        
        styles = details.get("style_distribution", {})
        dominant_style = max(styles, key=styles.get) if styles else ""
        
        if metric.value > 50:
            suggestions.append(OptimizationSuggestion(
                suggestion_id="NAME-001",
                title="命名风格不一致",
                description=f"检测到多种命名风格混杂，熵值{metric.value:.1f}",
                category=OptimizationCategory.NAMING,
                priority=OptimizationPriority.MEDIUM,
                current_state=f"风格分布: {styles}",
                suggested_state=f"统一使用{dominant_style}风格",
                expected_benefit="提高代码一致性，降低认知负担",
                estimated_effort="small",
                auto_fixable=True,
            ))
        
        return suggestions
    
    def _suggestions_for_compliance(
        self,
        result: ComplianceResult,
    ) -> List[OptimizationSuggestion]:
        """基于合规检测结果生成建议."""
        suggestions: List[OptimizationSuggestion] = []
        
        for violation in result.violations:
            rule = violation.rule
            
            # 映射优先级
            if rule.level.value == "mandatory":
                priority = OptimizationPriority.CRITICAL
            elif rule.level.value == "recommended":
                priority = OptimizationPriority.HIGH
            else:
                priority = OptimizationPriority.MEDIUM
            
            # 映射类别
            category_map = {
                "architecture": OptimizationCategory.ARCHITECTURE,
                "naming": OptimizationCategory.NAMING,
                "dependency": OptimizationCategory.DEPENDENCY,
                "state": OptimizationCategory.ARCHITECTURE,
                "documentation": OptimizationCategory.DOCUMENTATION,
            }
            category = category_map.get(
                rule.category.value,
                OptimizationCategory.REFACTOR,
            )
            
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"COMP-{rule.rule_id}",
                title=f"规范违规: {rule.name}",
                description=rule.description,
                category=category,
                priority=priority,
                target_file=violation.file_path,
                target_line=violation.line_number,
                current_state=violation.message,
                suggested_state=rule.fix_suggestion,
                expected_benefit=f"符合{rule.category.value}规范",
                estimated_effort="small",
            ))
        
        return suggestions
    
    def prioritize_suggestions(
        self,
        plan: OptimizationPlan,
    ) -> List[OptimizationSuggestion]:
        """对建议进行优先级排序.
        
        排序规则：
        1. 优先级（CRITICAL > HIGH > MEDIUM > LOW > OPTIONAL）
        2. 工作量（small < medium < large）
        3. 是否可自动修复（可自动修复优先）
        
        Args:
            plan: 优化计划
            
        Returns:
            排序后的建议列表
        """
        priority_order = {
            OptimizationPriority.CRITICAL: 0,
            OptimizationPriority.HIGH: 1,
            OptimizationPriority.MEDIUM: 2,
            OptimizationPriority.LOW: 3,
            OptimizationPriority.OPTIONAL: 4,
        }
        
        effort_order = {
            "small": 0,
            "medium": 1,
            "large": 2,
        }
        
        return sorted(
            plan.suggestions,
            key=lambda s: (
                priority_order.get(s.priority, 5),
                effort_order.get(s.estimated_effort, 3),
                -int(s.auto_fixable),  # 可自动修复的排在前面
            ),
        )


def create_optimizer() -> EntropyOptimizer:
    """工厂函数：创建优化器实例."""
    return EntropyOptimizer()
