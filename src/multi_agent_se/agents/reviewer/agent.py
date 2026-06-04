"""Reviewer Agent - 第36阶段.

代码审查Agent - 负责代码审查、质量评估和最佳实践检查.

职责:
- 代码风格与规范检查
- 逻辑正确性审查
- 性能与安全风险识别
- 可维护性评估
- 生成结构化审查报告
- 审查历史追踪与统计
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
import re

from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
from multi_agent_se.agents.runtime.base_agent import BaseAgentImpl, AgentContext, TaskResult


class ReviewCategory(Enum):
    """审查类别."""
    STYLE = "style"                   # 代码风格
    LOGIC = "logic"                   # 逻辑正确性
    PERFORMANCE = "performance"       # 性能问题
    SECURITY = "security"             # 安全风险
    MAINTAINABILITY = "maintainability"  # 可维护性
    DOCUMENTATION = "documentation"   # 文档完整性
    TESTING = "testing"              # 测试覆盖
    ARCHITECTURE = "architecture"    # 架构合规


class IssueSeverity(Enum):
    """问题严重程度."""
    CRITICAL = "critical"     # 严重 - 必须修复
    MAJOR = "major"           # 重要 - 强烈建议修复
    MINOR = "minor"           # 次要 - 建议修复
    INFO = "info"             # 提示 - 信息性建议
    SUGGESTION = "suggestion" # 建议 - 改进建议


class ReviewDecision(Enum):
    """审查决策."""
    APPROVED = "approved"       # 通过
    CHANGES_REQUESTED = "changes_requested"  # 需要修改
    REJECTED = "rejected"       # 拒绝
    NEEDS_DISCUSSION = "needs_discussion"  # 需要讨论


@dataclass
class ReviewIssue:
    """审查发现的问题."""
    issue_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: ReviewCategory = ReviewCategory.STYLE
    severity: IssueSeverity = IssueSeverity.INFO
    message: str = ""
    
    # 位置信息
    file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    
    # 代码上下文
    code_snippet: str = ""
    
    # 修复建议
    suggestion: str = ""
    auto_fixable: bool = False
    
    # 规则引用
    rule_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message[:100],
            "file_path": self.file_path,
            "line_range": f"{self.line_start}-{self.line_end}",
            "suggestion": self.suggestion[:80],
            "auto_fixable": self.auto_fixable,
        }


@dataclass
class ReviewComment:
    """审查评论."""
    comment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    file_path: str = ""
    line_number: int = 0
    content: str = ""
    is_positive: bool = False  # 是否为正面评价
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "comment_id": self.comment_id,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "content": self.content[:100],
            "is_positive": self.is_positive,
        }


@dataclass
class QualityMetrics:
    """质量指标."""
    # 代码量
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # 复杂度
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    
    # 可维护性
    maintainability_index: float = 0.0  # 0-100
    
    # 重复度
    duplication_rate: float = 0.0  # 0-1
    
    # 文档覆盖
    doc_coverage: float = 0.0  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "comment_ratio": round(
                self.comment_lines / max(self.code_lines, 1), 2
            ),
            "cyclomatic_complexity": round(self.cyclomatic_complexity, 1),
            "maintainability_index": round(self.maintainability_index, 1),
            "duplication_rate": round(self.duplication_rate, 2),
            "doc_coverage": round(self.doc_coverage, 2),
        }


@dataclass
class ReviewReport:
    """审查报告."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 审查目标
    target_files: List[str] = field(default_factory=list)
    review_scope: str = ""  # full/partial/diff
    
    # 审查结果
    decision: ReviewDecision = ReviewDecision.APPROVED
    overall_score: float = 0.0  # 0-100
    
    # 问题统计
    issues: List[ReviewIssue] = field(default_factory=list)
    comments: List[ReviewComment] = field(default_factory=list)
    
    # 质量指标
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)
    
    # 分类统计
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    info_count: int = 0
    
    # 总结
    summary: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "target_files": self.target_files[:5],
            "decision": self.decision.value,
            "overall_score": round(self.overall_score, 1),
            "total_issues": len(self.issues),
            "issue_breakdown": {
                "critical": self.critical_count,
                "major": self.major_count,
                "minor": self.minor_count,
                "info": self.info_count,
            },
            "quality_metrics": self.quality_metrics.to_dict(),
            "summary": self.summary[:150],
            "strengths": self.strengths[:3],
            "weaknesses": self.weaknesses[:3],
        }


class ReviewerAgent(BaseAgentImpl):
    """代码审查Agent - 质量评估与最佳实践检查.
    
    8大正交角色Agent之一，负责对代码进行全面审查，
    识别问题、评估质量并生成结构化审查报告。
    """
    
    AGENT_ROLE = AgentRole.REVIEWER
    AGENT_CAPABILITIES = [
        AgentCapability.CODE_REVIEW,
        AgentCapability.QUALITY_CHECK,
    ]
    AGENT_DESCRIPTION = "代码审查Agent - 负责代码审查、质量评估和最佳实践检查"
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None) -> None:
        super().__init__(agent_id, config)
        self._review_history: List[ReviewReport] = []
        self._review_rules: Dict[ReviewCategory, List[Dict]] = self._load_review_rules()
        self._quality_thresholds: Dict[str, float] = {
            "approve_min_score": 70.0,
            "critical_block_score": 30.0,
            "major_block_count": 5,
        }
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理代码审查任务.
        
        Args:
            context: Agent执行上下文
            
        Returns:
            任务执行结果
        """
        input_data = context.input_data
        
        # 输入类型验证
        if not isinstance(input_data, dict):
            return TaskResult(
                success=False,
                error_message=f"输入数据必须是字典类型，实际为 {type(input_data).__name__}",
            )
        
        code = input_data.get("code", "")
        files = input_data.get("files", [])
        review_scope = input_data.get("review_scope", "full")
        
        if not code and not files:
            return TaskResult(
                success=False,
                error_message="缺少代码或文件列表",
            )
        
        # 1. 创建审查报告
        report = ReviewReport(
            target_files=files if files else ["<inline_code>"],
            review_scope=review_scope,
        )
        
        # 2. 分析代码质量指标
        code_to_review = code or self._placeholder_code()
        report.quality_metrics = self._analyze_quality_metrics(code_to_review)
        
        # 3. 执行规则审查
        all_issues = self._run_rule_checks(code_to_review, files)
        report.issues = all_issues
        
        # 4. 生成评论
        report.comments = self._generate_comments(code_to_review)
        
        # 5. 统计问题
        self._count_issues(report)
        
        # 6. 计算总分
        report.overall_score = self._calculate_overall_score(report)
        
        # 7. 做出审查决策
        report.decision = self._make_decision(report)
        
        # 8. 生成总结
        report.summary = self._generate_summary(report)
        report.strengths = self._identify_strengths(report)
        report.weaknesses = self._identify_weaknesses(report)
        
        # 9. 保存历史
        self._review_history.append(report)
        
        return TaskResult(
            success=True,
            output=report.to_dict(),
            artifacts={
                "report": report,
                "issues": report.issues,
            },
        )
    
    def _placeholder_code(self) -> str:
        """占位代码（无代码输入时使用）."""
        return "# No code provided for review"
    
    def _analyze_quality_metrics(self, code: str) -> QualityMetrics:
        """分析代码质量指标."""
        metrics = QualityMetrics()
        
        if not code or code.startswith("# No code"):
            return metrics
        
        lines = code.splitlines()
        metrics.total_lines = len(lines)
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                metrics.blank_lines += 1
            elif stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                metrics.comment_lines += 1
            else:
                metrics.code_lines += 1
        
        # 圈复杂度估算（基于分支关键字）
        branch_keywords = ["if", "elif", "else", "for", "while", "except", "and", "or", "with"]
        metrics.cyclomatic_complexity = 1.0  # 基础复杂度
        for keyword in branch_keywords:
            metrics.cyclomatic_complexity += sum(
                1 for line in lines if re.match(rf'\b{keyword}\b', line.strip())
            )
        
        # 认知复杂度（嵌套加分）
        metrics.cognitive_complexity = metrics.cyclomatic_complexity * 1.2
        
        # 可维护性指数（简化计算）
        if metrics.code_lines > 0:
            comment_ratio = metrics.comment_lines / metrics.code_lines
            metrics.maintainability_index = min(
                100.0,
                50.0 + comment_ratio * 30.0 - (metrics.cyclomatic_complexity / max(metrics.code_lines, 1)) * 10.0
            )
        
        # 文档覆盖率
        doc_strings = len(re.findall(r'"""|\'\'\'', code))
        classes = max(len(re.findall(r'\bclass\b', code)), 1)
        functions = max(len(re.findall(r'\bdef\b', code)), 1)
        metrics.doc_coverage = min(1.0, doc_strings / (classes + functions))
        
        # 重复度（简化：检测相似行）
        metrics.duplication_rate = self._estimate_duplication(lines)
        
        return metrics
    
    def _estimate_duplication(self, lines: List[str]) -> float:
        """估算代码重复率."""
        if len(lines) < 4:
            return 0.0
        
        seen_blocks: Set[str] = set()
        duplicate_count = 0
        
        for i in range(len(lines) - 2):
            block = (lines[i].strip(), lines[i+1].strip(), lines[i+2].strip())
            block_key = "|".join(block)
            if block_key in seen_blocks and block[0]:
                duplicate_count += 1
            seen_blocks.add(block_key)
        
        return min(1.0, duplicate_count / max(len(lines), 1))
    
    def _run_rule_checks(
        self,
        code: str,
        files: List[str],
    ) -> List[ReviewIssue]:
        """执行规则检查."""
        issues: List[ReviewIssue] = []
        
        if not code or code.startswith("# No code"):
            return issues
        
        lines = code.splitlines()
        
        # 按类别检查
        for category, rules in self._review_rules.items():
            for rule in rules:
                rule_issues = self._apply_rule(rule, category, code, lines, files)
                issues.extend(rule_issues)
        
        return issues
    
    def _apply_rule(
        self,
        rule: Dict[str, Any],
        category: ReviewCategory,
        code: str,
        lines: List[str],
        files: List[str],
    ) -> List[ReviewIssue]:
        """应用单条规则."""
        issues: List[ReviewIssue] = []
        pattern = rule.get("pattern", "")
        severity = rule.get("severity", IssueSeverity.INFO)
        message = rule.get("message", "")
        suggestion = rule.get("suggestion", "")
        auto_fixable = rule.get("auto_fixable", False)
        
        if not pattern:
            return issues
        
        for i, line in enumerate(lines, start=1):
            if re.search(pattern, line):
                issues.append(ReviewIssue(
                    category=category,
                    severity=severity,
                    message=message,
                    file_path=files[0] if files else "unknown.py",
                    line_start=i,
                    line_end=i,
                    code_snippet=line.strip()[:80],
                    suggestion=suggestion,
                    auto_fixable=auto_fixable,
                    rule_id=rule.get("rule_id", ""),
                ))
        
        return issues
    
    def _generate_comments(self, code: str) -> List[ReviewComment]:
        """生成审查评论."""
        comments: List[ReviewComment] = []
        
        if not code or code.startswith("# No code"):
            return comments
        
        lines = code.splitlines()
        
        # 正面评论
        if any('"""' in line or "'''" in line for line in lines):
            comments.append(ReviewComment(
                content="代码包含文档字符串，文档化良好",
                is_positive=True,
            ))
        
        if any('from typing import' in line for line in lines):
            comments.append(ReviewComment(
                content="使用了类型注解，提高代码可读性",
                is_positive=True,
            ))
        
        # 改进建议
        if len(lines) > 100:
            comments.append(ReviewComment(
                content="文件较长，建议考虑模块拆分",
                is_positive=False,
            ))
        
        return comments
    
    def _count_issues(self, report: ReviewReport) -> None:
        """统计问题数量."""
        for issue in report.issues:
            if issue.severity == IssueSeverity.CRITICAL:
                report.critical_count += 1
            elif issue.severity == IssueSeverity.MAJOR:
                report.major_count += 1
            elif issue.severity == IssueSeverity.MINOR:
                report.minor_count += 1
            else:
                report.info_count += 1
    
    def _calculate_overall_score(self, report: ReviewReport) -> float:
        """计算总体评分."""
        # 基础分：可维护性指数
        score = report.quality_metrics.maintainability_index
        
        # 扣分：按严重程度
        deductions = {
            IssueSeverity.CRITICAL: 15.0,
            IssueSeverity.MAJOR: 8.0,
            IssueSeverity.MINOR: 3.0,
            IssueSeverity.INFO: 0.5,
            IssueSeverity.SUGGESTION: 0.0,
        }
        
        for issue in report.issues:
            score -= deductions.get(issue.severity, 0)
        
        # 加分：文档覆盖
        score += report.quality_metrics.doc_coverage * 10.0
        
        return max(0.0, min(100.0, score))
    
    def _make_decision(self, report: ReviewReport) -> ReviewDecision:
        """做出审查决策."""
        # 有严重问题直接拒绝
        if report.critical_count > 0:
            return ReviewDecision.CHANGES_REQUESTED
        
        # 分数过低
        if report.overall_score < self._quality_thresholds["critical_block_score"]:
            return ReviewDecision.REJECTED
        
        # 重大问题过多
        if report.major_count >= self._quality_thresholds["major_block_count"]:
            return ReviewDecision.CHANGES_REQUESTED
        
        # 分数达标
        if report.overall_score >= self._quality_thresholds["approve_min_score"]:
            return ReviewDecision.APPROVED
        
        return ReviewDecision.NEEDS_DISCUSSION
    
    def _generate_summary(self, report: ReviewReport) -> str:
        """生成审查总结."""
        total = len(report.issues)
        decision_map = {
            ReviewDecision.APPROVED: "代码审查通过",
            ReviewDecision.CHANGES_REQUESTED: "代码需要修改后重新提交",
            ReviewDecision.REJECTED: "代码未通过审查",
            ReviewDecision.NEEDS_DISCUSSION: "代码需要进一步讨论",
        }
        
        summary = decision_map.get(report.decision, "审查完成")
        summary += f"。总体评分: {report.overall_score:.1f}/100"
        summary += f"，共发现 {total} 个问题"
        
        if report.critical_count > 0:
            summary += f"（含 {report.critical_count} 个严重问题）"
        
        return summary
    
    def _identify_strengths(self, report: ReviewReport) -> List[str]:
        """识别代码优点."""
        strengths: List[str] = []
        
        if report.quality_metrics.doc_coverage > 0.5:
            strengths.append("文档覆盖良好")
        if report.quality_metrics.maintainability_index > 65:
            strengths.append("可维护性较高")
        if report.quality_metrics.duplication_rate < 0.05:
            strengths.append("代码重复率低")
        if report.quality_metrics.comment_lines / max(report.quality_metrics.code_lines, 1) > 0.15:
            strengths.append("注释比例合理")
        if report.critical_count == 0 and report.major_count == 0:
            strengths.append("无严重或重要问题")
        
        return strengths or ["代码基本符合规范"]
    
    def _identify_weaknesses(self, report: ReviewReport) -> List[str]:
        """识别代码不足."""
        weaknesses: List[str] = []
        
        if report.critical_count > 0:
            weaknesses.append(f"存在 {report.critical_count} 个严重问题需立即修复")
        if report.major_count > 0:
            weaknesses.append(f"存在 {report.major_count} 个重要问题建议修复")
        if report.quality_metrics.doc_coverage < 0.3:
            weaknesses.append("文档覆盖不足")
        if report.quality_metrics.maintainability_index < 50:
            weaknesses.append("可维护性偏低")
        if report.quality_metrics.duplication_rate > 0.1:
            weaknesses.append("存在代码重复")
        if report.quality_metrics.cyclomatic_complexity > 20:
            weaknesses.append("圈复杂度过高")
        
        return weaknesses or ["无明显不足"]
    
    def _load_review_rules(self) -> Dict[ReviewCategory, List[Dict]]:
        """加载审查规则."""
        return {
            ReviewCategory.STYLE: [
                {
                    "rule_id": "S001",
                    "pattern": r'\t',
                    "severity": IssueSeverity.MINOR,
                    "message": "使用了Tab缩进，建议使用空格",
                    "suggestion": "将Tab替换为4个空格",
                    "auto_fixable": True,
                },
                {
                    "rule_id": "S002",
                    "pattern": r'.{120,}',
                    "severity": IssueSeverity.INFO,
                    "message": "行过长（超过120字符）",
                    "suggestion": "将长行拆分为多行",
                    "auto_fixable": False,
                },
                {
                    "rule_id": "S003",
                    "pattern": r'except\s*:',
                    "severity": IssueSeverity.MAJOR,
                    "message": "使用了裸except，应指定具体异常类型",
                    "suggestion": "使用 except Exception 或具体异常类型",
                    "auto_fixable": False,
                },
            ],
            ReviewCategory.LOGIC: [
                {
                    "rule_id": "L001",
                    "pattern": r'==\s*True\b',
                    "severity": IssueSeverity.MINOR,
                    "message": "不建议使用 == True，应直接使用布尔值",
                    "suggestion": "if x: 替代 if x == True:",
                    "auto_fixable": True,
                },
                {
                    "rule_id": "L002",
                    "pattern": r'len\(.+\)\s*[!=]=\s*0',
                    "severity": IssueSeverity.INFO,
                    "message": "建议使用隐式布尔判断",
                    "suggestion": "if items: 替代 if len(items) != 0:",
                    "auto_fixable": False,
                },
            ],
            ReviewCategory.PERFORMANCE: [
                {
                    "rule_id": "P001",
                    "pattern": r'\+=\s*["\']',
                    "severity": IssueSeverity.MINOR,
                    "message": "循环中字符串拼接性能较差",
                    "suggestion": "使用 ''.join() 或 io.StringIO",
                    "auto_fixable": False,
                },
                {
                    "rule_id": "P002",
                    "pattern": r'import\s+\*',
                    "severity": IssueSeverity.MAJOR,
                    "message": "通配符导入影响性能和可读性",
                    "suggestion": "显式导入所需的名称",
                    "auto_fixable": False,
                },
            ],
            ReviewCategory.SECURITY: [
                {
                    "rule_id": "K001",
                    "pattern": r'eval\s*\(',
                    "severity": IssueSeverity.CRITICAL,
                    "message": "eval()存在代码注入风险",
                    "suggestion": "使用ast.literal_eval()或替代方案",
                    "auto_fixable": False,
                },
                {
                    "rule_id": "K002",
                    "pattern": r'exec\s*\(',
                    "severity": IssueSeverity.CRITICAL,
                    "message": "exec()存在代码注入风险",
                    "suggestion": "避免使用exec()",
                    "auto_fixable": False,
                },
                {
                    "rule_id": "K003",
                    "pattern": r'password\s*=\s*["\'][^"\']+["\']',
                    "severity": IssueSeverity.CRITICAL,
                    "message": "硬编码密码，存在安全风险",
                    "suggestion": "使用环境变量或配置管理",
                    "auto_fixable": False,
                },
            ],
            ReviewCategory.MAINTAINABILITY: [
                {
                    "rule_id": "M001",
                    "pattern": r'pass\s*$',
                    "severity": IssueSeverity.INFO,
                    "message": "空实现（pass），可能需要补充逻辑",
                    "suggestion": "添加TODO注释或实现逻辑",
                    "auto_fixable": False,
                },
            ],
            ReviewCategory.DOCUMENTATION: [
                {
                    "rule_id": "D001",
                    "pattern": r'^class\s+\w+.*:$',
                    "severity": IssueSeverity.MINOR,
                    "message": "类缺少文档字符串",
                    "suggestion": "为类添加docstring",
                    "auto_fixable": False,
                },
            ],
        }
    
    def get_review_history(self) -> List[ReviewReport]:
        """获取审查历史."""
        return self._review_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        total_reviews = len(self._review_history)
        if total_reviews == 0:
            return {
                "total_reviews": 0,
                "avg_score": 0.0,
                "approval_rate": 0.0,
            }
        
        approved = sum(
            1 for r in self._review_history
            if r.decision == ReviewDecision.APPROVED
        )
        avg_score = sum(r.overall_score for r in self._review_history) / total_reviews
        
        # 按类别统计问题
        category_counts: Dict[str, int] = {}
        for report in self._review_history:
            for issue in report.issues:
                cat = issue.category.value
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            "total_reviews": total_reviews,
            "approved_reviews": approved,
            "approval_rate": approved / total_reviews,
            "avg_score": round(avg_score, 1),
            "total_issues_found": sum(len(r.issues) for r in self._review_history),
            "issue_category_distribution": category_counts,
        }
