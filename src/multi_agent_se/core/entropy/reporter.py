"""规范文档生成器 - 阶段15.

自动生成规范文档：
- 熵值分析报告
- 合规检测报告
- 优化建议报告
- 架构规范文档
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from multi_agent_se.core.entropy.calculator import EntropyReport
from multi_agent_se.core.entropy.compliance import ComplianceResult
from multi_agent_se.core.entropy.optimizer import OptimizationPlan


class ReportFormat(Enum):
    """报告格式."""
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"


class ReportType(Enum):
    """报告类型."""
    ENTROPY = "entropy"              # 熵值报告
    COMPLIANCE = "compliance"        # 合规报告
    OPTIMIZATION = "optimization"    # 优化建议报告
    FULL = "full"                    # 完整报告


@dataclass
class ReportMetadata:
    """报告元数据."""
    title: str
    report_type: ReportType
    generated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    project_name: str = "Multi-Agent SE"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "report_type": self.report_type.value,
            "generated_at": self.generated_at.isoformat(),
            "version": self.version,
            "project_name": self.project_name,
        }


@dataclass
class GeneratedReport:
    """生成的报告."""
    metadata: ReportMetadata
    content: str
    format: ReportFormat
    
    def save(self, file_path: str) -> None:
        """保存报告到文件.
        
        Args:
            file_path: 文件路径
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.content, encoding="utf-8")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "format": self.format.value,
            "content_length": len(self.content),
        }


class EntropyReporter:
    """熵值报告生成器.
    
    生成各种格式的规范文档和报告
    """
    
    def __init__(self, project_name: str = "Multi-Agent SE") -> None:
        """初始化报告生成器.
        
        Args:
            project_name: 项目名称
        """
        self._project_name = project_name
    
    def generate_entropy_report(
        self,
        entropy_report: EntropyReport,
        format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> GeneratedReport:
        """生成熵值报告.
        
        Args:
            entropy_report: 熵值报告数据
            format: 输出格式
            
        Returns:
            GeneratedReport
        """
        metadata = ReportMetadata(
            title="系统熵值分析报告",
            report_type=ReportType.ENTROPY,
            project_name=self._project_name,
        )
        
        if format == ReportFormat.JSON:
            content = self._entropy_to_json(entropy_report)
        elif format == ReportFormat.MARKDOWN:
            content = self._entropy_to_markdown(entropy_report)
        elif format == ReportFormat.HTML:
            content = self._entropy_to_html(entropy_report)
        else:
            content = self._entropy_to_text(entropy_report)
        
        return GeneratedReport(
            metadata=metadata,
            content=content,
            format=format,
        )
    
    def generate_compliance_report(
        self,
        compliance_result: ComplianceResult,
        format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> GeneratedReport:
        """生成合规检测报告.
        
        Args:
            compliance_result: 合规检测结果
            format: 输出格式
            
        Returns:
            GeneratedReport
        """
        metadata = ReportMetadata(
            title="架构规范合规检测报告",
            report_type=ReportType.COMPLIANCE,
            project_name=self._project_name,
        )
        
        if format == ReportFormat.JSON:
            content = self._compliance_to_json(compliance_result)
        elif format == ReportFormat.MARKDOWN:
            content = self._compliance_to_markdown(compliance_result)
        elif format == ReportFormat.HTML:
            content = self._compliance_to_html(compliance_result)
        else:
            content = self._compliance_to_text(compliance_result)
        
        return GeneratedReport(
            metadata=metadata,
            content=content,
            format=format,
        )
    
    def generate_optimization_report(
        self,
        optimization_plan: OptimizationPlan,
        format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> GeneratedReport:
        """生成优化建议报告.
        
        Args:
            optimization_plan: 优化计划
            format: 输出格式
            
        Returns:
            GeneratedReport
        """
        metadata = ReportMetadata(
            title="熵减优化建议报告",
            report_type=ReportType.OPTIMIZATION,
            project_name=self._project_name,
        )
        
        if format == ReportFormat.JSON:
            content = self._optimization_to_json(optimization_plan)
        elif format == ReportFormat.MARKDOWN:
            content = self._optimization_to_markdown(optimization_plan)
        elif format == ReportFormat.HTML:
            content = self._optimization_to_html(optimization_plan)
        else:
            content = self._optimization_to_text(optimization_plan)
        
        return GeneratedReport(
            metadata=metadata,
            content=content,
            format=format,
        )
    
    def generate_full_report(
        self,
        entropy_report: EntropyReport,
        compliance_result: ComplianceResult,
        optimization_plan: OptimizationPlan,
        format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> GeneratedReport:
        """生成完整报告.
        
        Args:
            entropy_report: 熵值报告
            compliance_result: 合规检测结果
            optimization_plan: 优化计划
            format: 输出格式
            
        Returns:
            GeneratedReport
        """
        metadata = ReportMetadata(
            title="系统质量完整报告",
            report_type=ReportType.FULL,
            project_name=self._project_name,
        )
        
        if format == ReportFormat.JSON:
            content = json.dumps({
                "entropy": entropy_report.to_dict(),
                "compliance": compliance_result.to_dict(),
                "optimization": optimization_plan.to_dict(),
            }, indent=2, ensure_ascii=False)
        elif format == ReportFormat.MARKDOWN:
            content = self._generate_full_markdown(
                entropy_report,
                compliance_result,
                optimization_plan,
            )
        else:
            content = self._generate_full_text(
                entropy_report,
                compliance_result,
                optimization_plan,
            )
        
        return GeneratedReport(
            metadata=metadata,
            content=content,
            format=format,
        )
    
    # ========== JSON 格式 ==========
    
    def _entropy_to_json(self, report: EntropyReport) -> str:
        """熵值报告转JSON."""
        return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
    
    def _compliance_to_json(self, result: ComplianceResult) -> str:
        """合规报告转JSON."""
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
    
    def _optimization_to_json(self, plan: OptimizationPlan) -> str:
        """优化报告转JSON."""
        return json.dumps(plan.to_dict(), indent=2, ensure_ascii=False)
    
    # ========== Markdown 格式 ==========
    
    def _entropy_to_markdown(self, report: EntropyReport) -> str:
        """熵值报告转Markdown."""
        lines = [
            "# 系统熵值分析报告",
            "",
            f"**生成时间**: {datetime.now().isoformat()}",
            f"**项目**: {self._project_name}",
            "",
            "## 摘要",
            "",
            f"- **综合得分**: {report.total_score:.1f}/100",
            f"- **平均熵值**: {report.average_entropy:.1f}",
            f"- **最大熵值**: {report.max_entropy:.1f}",
            f"- **系统健康**: {'✅ 健康' if report.is_healthy else '⚠️ 需要关注'}",
            "",
            "## 详细指标",
            "",
        ]
        
        for metric in report.metrics:
            status = "✅" if metric.is_acceptable else "⚠️"
            lines.extend([
                f"### {metric.entropy_type.value} {status}",
                "",
                f"- **熵值**: {metric.value:.1f}/100",
                f"- **阈值**: {metric.threshold}",
                f"- **严重程度**: {metric.severity}",
                "",
                "**详情**:",
                "",
                "```json",
                json.dumps(metric.details, indent=2, ensure_ascii=False),
                "```",
                "",
            ])
        
        return "\n".join(lines)
    
    def _compliance_to_markdown(self, result: ComplianceResult) -> str:
        """合规报告转Markdown."""
        lines = [
            "# 架构规范合规检测报告",
            "",
            f"**生成时间**: {datetime.now().isoformat()}",
            f"**项目**: {self._project_name}",
            "",
            "## 摘要",
            "",
            f"- **合规率**: {result.compliance_rate:.1f}%",
            f"- **检查规则**: {result.checked_rules}",
            f"- **通过规则**: {result.passed_rules}",
            f"- **违规数**: {len(result.violations)}",
            f"- **强制违规**: {'⚠️ 存在' if result.has_mandatory_violations else '✅ 无'}",
            "",
        ]
        
        if result.violations:
            lines.extend([
                "## 违规详情",
                "",
                "| 规则ID | 规则名 | 级别 | 目标 | 建议修复 |",
                "|--------|--------|------|------|----------|",
            ])
            for v in result.violations:
                lines.append(
                    f"| {v.rule.rule_id} | {v.rule.name} | "
                    f"{v.rule.level.value} | {v.target} | {v.rule.fix_suggestion} |"
                )
            lines.append("")
        
        return "\n".join(lines)
    
    def _optimization_to_markdown(self, plan: OptimizationPlan) -> str:
        """优化报告转Markdown."""
        lines = [
            "# 熵减优化建议报告",
            "",
            f"**生成时间**: {datetime.now().isoformat()}",
            f"**项目**: {self._project_name}",
            "",
            "## 摘要",
            "",
            f"- **建议总数**: {plan.total_suggestions}",
            f"- **严重问题**: {plan.critical_count}",
            f"- **高优先级**: {plan.high_count}",
            f"- **可自动修复**: {plan.auto_fixable_count}",
            "",
        ]
        
        if plan.suggestions:
            lines.extend([
                "## 优化建议",
                "",
            ])
            
            for s in plan.suggestions:
                auto_fix = "🤖" if s.auto_fixable else ""
                lines.extend([
                    f"### [{s.priority.value.upper()}] {s.title} {auto_fix}",
                    "",
                    f"**类别**: {s.category.value}",
                    f"**描述**: {s.description}",
                    "",
                    "**当前状态**:",
                    f"> {s.current_state}",
                    "",
                    "**建议修改**:",
                    f"> {s.suggested_state}",
                    "",
                    f"**预期收益**: {s.expected_benefit}",
                    f"**预估工作量**: {s.estimated_effort}",
                    "",
                    "---",
                    "",
                ])
        
        return "\n".join(lines)
    
    def _generate_full_markdown(
        self,
        entropy: EntropyReport,
        compliance: ComplianceResult,
        optimization: OptimizationPlan,
    ) -> str:
        """生成完整Markdown报告."""
        entropy_report = self._entropy_to_markdown(entropy)
        compliance_report = self._compliance_to_markdown(compliance)
        optimization_report = self._optimization_to_markdown(optimization)
        
        return f"""# 系统质量完整报告

**生成时间**: {datetime.now().isoformat()}
**项目**: {self._project_name}

---

{entropy_report}

---

{compliance_report}

---

{optimization_report}
"""
    
    # ========== HTML 格式 ==========
    
    def _entropy_to_html(self, report: EntropyReport) -> str:
        """熵值报告转HTML."""
        health_class = "healthy" if report.is_healthy else "unhealthy"
        
        metrics_html = ""
        for metric in report.metrics:
            status_class = "pass" if metric.is_acceptable else "fail"
            metrics_html += f"""
            <div class="metric {status_class}">
                <h3>{metric.entropy_type.value}</h3>
                <p>熵值: {metric.value:.1f}/100</p>
                <p>严重程度: {metric.severity}</p>
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>系统熵值分析报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; }}
        .healthy {{ color: green; }}
        .unhealthy {{ color: red; }}
        .metric {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .pass {{ border-left: 4px solid green; }}
        .fail {{ border-left: 4px solid red; }}
    </style>
</head>
<body>
    <h1>系统熵值分析报告</h1>
    <div class="summary">
        <p>综合得分: {report.total_score:.1f}/100</p>
        <p class="{health_class}">系统健康: {'健康' if report.is_healthy else '需要关注'}</p>
    </div>
    <h2>详细指标</h2>
    {metrics_html}
</body>
</html>"""
    
    def _compliance_to_html(self, result: ComplianceResult) -> str:
        """合规报告转HTML."""
        violations_html = ""
        for v in result.violations:
            violations_html += f"""
            <tr>
                <td>{v.rule.rule_id}</td>
                <td>{v.rule.name}</td>
                <td>{v.rule.level.value}</td>
                <td>{v.target}</td>
            </tr>
            """
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>合规检测报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>架构规范合规检测报告</h1>
    <p>合规率: {result.compliance_rate:.1f}%</p>
    <p>违规数: {len(result.violations)}</p>
    <table>
        <tr><th>规则ID</th><th>规则名</th><th>级别</th><th>目标</th></tr>
        {violations_html}
    </table>
</body>
</html>"""
    
    def _optimization_to_html(self, plan: OptimizationPlan) -> str:
        """优化报告转HTML."""
        suggestions_html = ""
        for s in plan.suggestions:
            suggestions_html += f"""
            <div class="suggestion {s.priority.value}">
                <h3>[{s.priority.value.upper()}] {s.title}</h3>
                <p>{s.description}</p>
                <p><strong>建议:</strong> {s.suggested_state}</p>
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>优化建议报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .suggestion {{ border: 1px solid #ddd; padding: 15px; margin: 10px 0; }}
        .critical {{ border-left: 4px solid red; }}
        .high {{ border-left: 4px solid orange; }}
        .medium {{ border-left: 4px solid yellow; }}
        .low {{ border-left: 4px solid blue; }}
    </style>
</head>
<body>
    <h1>熵减优化建议报告</h1>
    <p>建议总数: {plan.total_suggestions}</p>
    <p>严重问题: {plan.critical_count}</p>
    {suggestions_html}
</body>
</html>"""
    
    # ========== Text 格式 ==========
    
    def _entropy_to_text(self, report: EntropyReport) -> str:
        """熵值报告转纯文本."""
        lines = [
            "=" * 50,
            "系统熵值分析报告",
            "=" * 50,
            f"综合得分: {report.total_score:.1f}/100",
            f"平均熵值: {report.average_entropy:.1f}",
            f"系统健康: {'健康' if report.is_healthy else '需要关注'}",
            "-" * 50,
        ]
        
        for metric in report.metrics:
            lines.extend([
                f"\n[{metric.entropy_type.value}]",
                f"  熵值: {metric.value:.1f}/100",
                f"  严重程度: {metric.severity}",
            ])
        
        return "\n".join(lines)
    
    def _compliance_to_text(self, result: ComplianceResult) -> str:
        """合规报告转纯文本."""
        lines = [
            "=" * 50,
            "架构规范合规检测报告",
            "=" * 50,
            f"合规率: {result.compliance_rate:.1f}%",
            f"违规数: {len(result.violations)}",
            "-" * 50,
        ]
        
        for v in result.violations:
            lines.extend([
                f"\n[{v.rule.rule_id}] {v.rule.name}",
                f"  级别: {v.rule.level.value}",
                f"  目标: {v.target}",
            ])
        
        return "\n".join(lines)
    
    def _optimization_to_text(self, plan: OptimizationPlan) -> str:
        """优化报告转纯文本."""
        lines = [
            "=" * 50,
            "熵减优化建议报告",
            "=" * 50,
            f"建议总数: {plan.total_suggestions}",
            f"严重问题: {plan.critical_count}",
            "-" * 50,
        ]
        
        for s in plan.suggestions:
            lines.extend([
                f"\n[{s.priority.value.upper()}] {s.title}",
                f"  类别: {s.category.value}",
                f"  描述: {s.description}",
                f"  建议: {s.suggested_state}",
            ])
        
        return "\n".join(lines)
    
    def _generate_full_text(
        self,
        entropy: EntropyReport,
        compliance: ComplianceResult,
        optimization: OptimizationPlan,
    ) -> str:
        """生成完整文本报告."""
        return "\n\n".join([
            self._entropy_to_text(entropy),
            self._compliance_to_text(compliance),
            self._optimization_to_text(optimization),
        ])


def create_reporter(project_name: str = "Multi-Agent SE") -> EntropyReporter:
    """工厂函数：创建报告生成器."""
    return EntropyReporter(project_name)
