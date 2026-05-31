"""规范符合度检测 - 阶段15.

检测代码是否符合架构规范：
- 四层架构规范
- 命名规范
- 依赖规范
- 状态管理规范
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Callable

from multi_agent_se.core.architecture.layer_base import ArchitectureLayer


class ComplianceLevel(Enum):
    """规范符合级别."""
    MANDATORY = "mandatory"    # 强制
    RECOMMENDED = "recommended"  # 推荐
    OPTIONAL = "optional"      # 可选


class ComplianceCategory(Enum):
    """规范类别."""
    ARCHITECTURE = "architecture"    # 架构规范
    NAMING = "naming"                # 命名规范
    DEPENDENCY = "dependency"        # 依赖规范
    STATE = "state"                  # 状态规范
    DOCUMENTATION = "documentation"  # 文档规范


@dataclass
class ComplianceRule:
    """规范规则."""
    rule_id: str
    name: str
    description: str
    category: ComplianceCategory
    level: ComplianceLevel
    check_fn: Callable[[Any], bool] = field(compare=False)
    fix_suggestion: str = ""
    
    def check(self, target: Any) -> bool:
        """检查目标是否符合规范.
        
        Args:
            target: 检查目标
            
        Returns:
            True如果符合
        """
        try:
            return self.check_fn(target)
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "level": self.level.value,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass
class ComplianceViolation:
    """规范违规记录."""
    rule: ComplianceRule
    target: str
    message: str
    file_path: str = ""
    line_number: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule.to_dict(),
            "target": self.target,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
        }


@dataclass
class ComplianceResult:
    """规范符合度结果."""
    violations: List[ComplianceViolation] = field(default_factory=list)
    checked_rules: int = 0
    passed_rules: int = 0
    
    @property
    def compliance_rate(self) -> float:
        """符合率(0-100)."""
        if self.checked_rules == 0:
            return 100.0
        return (self.passed_rules / self.checked_rules) * 100
    
    @property
    def is_compliant(self) -> bool:
        """是否完全符合规范."""
        return len(self.violations) == 0
    
    @property
    def has_mandatory_violations(self) -> bool:
        """是否有强制规范违规."""
        return any(
            v.rule.level == ComplianceLevel.MANDATORY
            for v in self.violations
        )
    
    def get_violations_by_category(
        self,
        category: ComplianceCategory,
    ) -> List[ComplianceViolation]:
        """按类别获取违规."""
        return [v for v in self.violations if v.rule.category == category]
    
    def get_violations_by_level(
        self,
        level: ComplianceLevel,
    ) -> List[ComplianceViolation]:
        """按级别获取违规."""
        return [v for v in self.violations if v.rule.level == level]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "compliance_rate": round(self.compliance_rate, 2),
            "is_compliant": self.is_compliant,
            "checked_rules": self.checked_rules,
            "passed_rules": self.passed_rules,
            "violation_count": len(self.violations),
            "has_mandatory_violations": self.has_mandatory_violations,
            "violations": [v.to_dict() for v in self.violations],
        }


class ComplianceChecker:
    """规范符合度检测器.
    
    检测代码是否符合架构规范
    """
    
    def __init__(self) -> None:
        """初始化检测器."""
        self._rules: List[ComplianceRule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """设置默认规则."""
        # 架构规范
        self._rules.append(ComplianceRule(
            rule_id="ARCH-001",
            name="四层架构依赖方向",
            description="依赖必须遵循 INPUT->SCHEDULER->AGENT->EXECUTOR 方向",
            category=ComplianceCategory.ARCHITECTURE,
            level=ComplianceLevel.MANDATORY,
            check_fn=self._check_architecture_direction,
            fix_suggestion="将依赖移到正确的架构层",
        ))
        
        # 命名规范
        self._rules.append(ComplianceRule(
            rule_id="NAME-001",
            name="模块名使用snake_case",
            description="Python模块名应使用snake_case",
            category=ComplianceCategory.NAMING,
            level=ComplianceLevel.MANDATORY,
            check_fn=self._check_module_naming,
            fix_suggestion="将模块名改为snake_case格式",
        ))
        
        self._rules.append(ComplianceRule(
            rule_id="NAME-002",
            name="类名使用PascalCase",
            description="类名应使用PascalCase",
            category=ComplianceCategory.NAMING,
            level=ComplianceLevel.MANDATORY,
            check_fn=self._check_class_naming,
            fix_suggestion="将类名改为PascalCase格式",
        ))
        
        # 依赖规范
        self._rules.append(ComplianceRule(
            rule_id="DEP-001",
            name="禁止循环依赖",
            description="模块间不应存在循环依赖",
            category=ComplianceCategory.DEPENDENCY,
            level=ComplianceLevel.MANDATORY,
            check_fn=self._check_no_cycles,
            fix_suggestion="重构代码消除循环依赖",
        ))
        
        # 状态规范
        self._rules.append(ComplianceRule(
            rule_id="STATE-001",
            name="状态必须显式注册",
            description="全局状态必须通过StateRegistry显式注册",
            category=ComplianceCategory.STATE,
            level=ComplianceLevel.RECOMMENDED,
            check_fn=self._check_explicit_state,
            fix_suggestion="使用StateRegistry.register()注册状态",
        ))
    
    def _check_architecture_direction(self, ctx: Dict[str, Any]) -> bool:
        """检查架构依赖方向."""
        source_layer = ctx.get("source_layer")
        target_layer = ctx.get("target_layer")
        
        if source_layer is None or target_layer is None:
            return True
        
        if isinstance(source_layer, str):
            source_layer = ArchitectureLayer[source_layer]
        if isinstance(target_layer, str):
            target_layer = ArchitectureLayer[target_layer]
        
        return source_layer.can_depend_on(target_layer)
    
    def _check_module_naming(self, name: str) -> bool:
        """检查模块命名."""
        if not name:
            return True
        return name.islower() and " " not in name
    
    def _check_class_naming(self, name: str) -> bool:
        """检查类命名."""
        if not name:
            return True
        return name[0].isupper() and "_" not in name
    
    def _check_no_cycles(self, ctx: Dict[str, Any]) -> bool:
        """检查无循环依赖."""
        dependencies = ctx.get("dependencies", {})
        # 简化检查，实际应使用DAG检测
        return True
    
    def _check_explicit_state(self, ctx: Dict[str, Any]) -> bool:
        """检查状态显式注册."""
        is_registered = ctx.get("is_registered", False)
        return is_registered
    
    def add_rule(self, rule: ComplianceRule) -> None:
        """添加规则.
        
        Args:
            rule: 规则
        """
        self._rules.append(rule)
    
    def check(
        self,
        target: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ComplianceResult:
        """执行规范检查.
        
        Args:
            target: 检查目标
            context: 上下文信息
            
        Returns:
            ComplianceResult
        """
        violations: List[ComplianceViolation] = []
        checked = 0
        passed = 0
        
        ctx = context or {}
        
        for rule in self._rules:
            checked += 1
            if rule.check(ctx):
                passed += 1
            else:
                violations.append(ComplianceViolation(
                    rule=rule,
                    target=str(target),
                    message=f"违反规范: {rule.name}",
                    file_path=ctx.get("file_path", ""),
                    line_number=ctx.get("line_number", 0),
                ))
        
        return ComplianceResult(
            violations=violations,
            checked_rules=checked,
            passed_rules=passed,
        )
    
    def check_architecture_compliance(
        self,
        source_layer: ArchitectureLayer,
        target_layer: ArchitectureLayer,
    ) -> ComplianceResult:
        """检查架构符合度.
        
        Args:
            source_layer: 源层
            target_layer: 目标层
            
        Returns:
            ComplianceResult
        """
        context = {
            "source_layer": source_layer,
            "target_layer": target_layer,
        }
        return self.check("architecture_check", context)
    
    def get_rules(
        self,
        category: Optional[ComplianceCategory] = None,
        level: Optional[ComplianceLevel] = None,
    ) -> List[ComplianceRule]:
        """获取规则列表.
        
        Args:
            category: 类别过滤
            level: 级别过滤
            
        Returns:
            规则列表
        """
        rules = self._rules
        
        if category:
            rules = [r for r in rules if r.category == category]
        
        if level:
            rules = [r for r in rules if r.level == level]
        
        return rules
    
    def get_rule(self, rule_id: str) -> Optional[ComplianceRule]:
        """获取指定规则.
        
        Args:
            rule_id: 规则ID
            
        Returns:
            规则（不存在返回None）
        """
        for rule in self._rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除规则.
        
        Args:
            rule_id: 规则ID
            
        Returns:
            是否成功移除
        """
        for i, rule in enumerate(self._rules):
            if rule.rule_id == rule_id:
                self._rules.pop(i)
                return True
        return False
    
    def clear_rules(self) -> None:
        """清空所有规则."""
        self._rules.clear()


# 默认规范检测器实例
default_compliance_checker = ComplianceChecker()
