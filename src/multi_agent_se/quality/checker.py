"""统一代码质量检查器 - 阶段22.

整合多种代码质量工具：
- Ruff: 静态代码检查
- 支持扩展其他工具（Bandit, MyPy等）

提供统一的检查接口和质量报告。
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from multi_agent_se.quality.issue import (
    CodeLocation,
    FixSuggestion,
    IssueCategory,
    IssueSource,
    QualityIssue,
    QualityReport,
    Severity,
    create_issue,
)


class QualityChecker:
    """统一代码质量检查器.
    
    整合多种检查工具，提供统一的检查接口
    """
    
    def __init__(
        self,
        ruff_config: Optional[str] = None,
        min_severity: Severity = Severity.LOW,
    ) -> None:
        """初始化检查器.
        
        Args:
            ruff_config: Ruff配置文件路径
            min_severity: 最小报告严重程度
        """
        self.ruff_config = ruff_config
        self.min_severity = min_severity
        self._enabled_sources: List[IssueSource] = [
            IssueSource.RUFF,
        ]
    
    def check_file(
        self,
        file_path: Union[str, Path],
        select_rules: Optional[List[str]] = None,
        ignore_rules: Optional[List[str]] = None,
    ) -> QualityReport:
        """检查单个文件.
        
        Args:
            file_path: 文件路径
            select_rules: 只检查指定规则
            ignore_rules: 忽略指定规则
            
        Returns:
            QualityReport: 质量报告
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return QualityReport(
                file_path=str(file_path),
                issues=[
                    create_issue(
                        rule_id="FILE_NOT_FOUND",
                        message=f"File not found: {file_path}",
                        file_path=str(file_path),
                        severity=Severity.CRITICAL,
                        category=IssueCategory.BUG_RISK,
                    )
                ],
            )
        
        # 读取文件内容
        try:
            source = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return QualityReport(
                file_path=str(file_path),
                issues=[
                    create_issue(
                        rule_id="FILE_READ_ERROR",
                        message=f"Cannot read file: {e}",
                        file_path=str(file_path),
                        severity=Severity.CRITICAL,
                        category=IssueCategory.BUG_RISK,
                    )
                ],
            )
        
        return self.check_source(
            source=source,
            file_path=str(file_path),
            select_rules=select_rules,
            ignore_rules=ignore_rules,
        )
    
    def check_source(
        self,
        source: str,
        file_path: str = "<stdin>",
        select_rules: Optional[List[str]] = None,
        ignore_rules: Optional[List[str]] = None,
    ) -> QualityReport:
        """检查源代码字符串.
        
        Args:
            source: 源代码
            file_path: 文件路径（用于报告）
            select_rules: 只检查指定规则
            ignore_rules: 忽略指定规则
            
        Returns:
            QualityReport: 质量报告
        """
        all_issues: List[QualityIssue] = []
        
        # 运行Ruff检查
        if IssueSource.RUFF in self._enabled_sources:
            ruff_issues = self._run_ruff_check(
                source, file_path, select_rules, ignore_rules
            )
            all_issues.extend(ruff_issues)
        
        # 过滤严重程度
        filtered_issues = [
            i for i in all_issues
            if self._severity_rank(i.severity) >= self._severity_rank(self.min_severity)
        ]
        
        return QualityReport(
            file_path=file_path,
            issues=filtered_issues,
            source=IssueSource.RUFF,
        )
    
    def check_files(
        self,
        file_paths: List[Union[str, Path]],
        select_rules: Optional[List[str]] = None,
    ) -> QualityReport:
        """批量检查多个文件.
        
        Args:
            file_paths: 文件路径列表
            select_rules: 只检查指定规则
            
        Returns:
            QualityReport: 合并后的质量报告
        """
        merged_report = QualityReport()
        
        for file_path in file_paths:
            report = self.check_file(file_path, select_rules)
            merged_report = merged_report.merge(report)
        
        return merged_report
    
    def format_code(self, source: str) -> str:
        """格式化代码.
        
        Args:
            source: 源代码
            
        Returns:
            格式化后的代码
        """
        try:
            result = subprocess.run(
                ["ruff", "format", "-"],
                capture_output=True,
                text=True,
                input=source,
                timeout=30,
            )
            return result.stdout if result.returncode == 0 else source
        except Exception:
            return source
    
    def fix_issues(
        self,
        file_path: Union[str, Path],
        select_rules: Optional[List[str]] = None,
    ) -> bool:
        """自动修复文件中的问题.
        
        Args:
            file_path: 文件路径
            select_rules: 只修复指定规则
            
        Returns:
            是否成功修复
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        try:
            args = ["ruff", "check", "--fix", str(file_path)]
            
            if select_rules:
                args.extend(["--select", ",".join(select_rules)])
            
            if self.ruff_config:
                args.extend(["--config", self.ruff_config])
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            return result.returncode in (0, 1)  # 0=无问题, 1=有问题但已修复
        except Exception:
            return False
    
    def _run_ruff_check(
        self,
        source: str,
        file_path: str,
        select_rules: Optional[List[str]] = None,
        ignore_rules: Optional[List[str]] = None,
    ) -> List[QualityIssue]:
        """运行Ruff检查.
        
        Args:
            source: 源代码
            file_path: 文件路径
            select_rules: 只检查指定规则
            ignore_rules: 忽略指定规则
            
        Returns:
            QualityIssue列表
        """
        try:
            # 构建命令
            args = ["ruff", "check", "-", "--output-format=json"]
            
            if select_rules:
                args.extend(["--select", ",".join(select_rules)])
            
            if ignore_rules:
                args.extend(["--ignore", ",".join(ignore_rules)])
            
            if self.ruff_config:
                args.extend(["--config", self.ruff_config])
            
            # 运行检查
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                input=source,
                timeout=30,
            )
            
            # 解析结果
            return self._parse_ruff_output(result.stdout, file_path)
            
        except subprocess.TimeoutExpired:
            return [
                create_issue(
                    rule_id="RUFF_TIMEOUT",
                    message="Ruff check timed out",
                    file_path=file_path,
                    severity=Severity.HIGH,
                    category=IssueCategory.BUG_RISK,
                )
            ]
        except Exception as e:
            return [
                create_issue(
                    rule_id="RUFF_ERROR",
                    message=f"Ruff check failed: {e}",
                    file_path=file_path,
                    severity=Severity.HIGH,
                    category=IssueCategory.BUG_RISK,
                )
            ]
    
    def _parse_ruff_output(
        self,
        output: str,
        file_path: str,
    ) -> List[QualityIssue]:
        """解析Ruff输出.
        
        Args:
            output: Ruff JSON输出
            file_path: 文件路径
            
        Returns:
            QualityIssue列表
        """
        issues = []
        
        if not output.strip():
            return issues
        
        try:
            data = json.loads(output)
            
            for item in data:
                code = item.get("code", "")
                message = item.get("message", "")
                location = item.get("location", {})
                end_location = item.get("end_location", {})
                fix_data = item.get("fix")
                
                # 创建QualityIssue
                issue = QualityIssue.from_ruff_issue(
                    code=code,
                    message=message,
                    file_path=file_path,
                    line=location.get("row", 0),
                    col=location.get("column", 0),
                    end_line=end_location.get("row", 0),
                    end_col=end_location.get("column", 0),
                    fixable=fix_data is not None and fix_data.get("applicability") == "safe",
                )
                
                # 添加修复建议详情
                if fix_data and isinstance(fix_data, dict):
                    issue.fix = FixSuggestion(
                        auto_fixable=fix_data.get("applicability") == "safe",
                        description=fix_data.get("message", ""),
                        replacement_code=fix_data.get("content"),
                    )
                
                issues.append(issue)
                
        except json.JSONDecodeError:
            pass
        
        return issues
    
    def _severity_rank(self, severity: Severity) -> int:
        """获取严重程度排序值.
        
        Args:
            severity: 严重程度
            
        Returns:
            排序值（越大越严重）
        """
        ranks = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        return ranks.get(severity, 0)
    
    def enable_source(self, source: IssueSource) -> None:
        """启用检查源.
        
        Args:
            source: 检查源
        """
        if source not in self._enabled_sources:
            self._enabled_sources.append(source)
    
    def disable_source(self, source: IssueSource) -> None:
        """禁用检查源.
        
        Args:
            source: 检查源
        """
        if source in self._enabled_sources:
            self._enabled_sources.remove(source)


# ========== 便捷函数 ==========

def check_code(
    source: str,
    file_path: str = "<stdin>",
    min_severity: Severity = Severity.LOW,
) -> QualityReport:
    """快速检查代码的便捷函数.
    
    Args:
        source: 源代码
        file_path: 文件路径
        min_severity: 最小报告严重程度
        
    Returns:
        QualityReport: 质量报告
    """
    checker = QualityChecker(min_severity=min_severity)
    return checker.check_source(source, file_path)


def check_file(
    file_path: Union[str, Path],
    min_severity: Severity = Severity.LOW,
) -> QualityReport:
    """快速检查文件的便捷函数.
    
    Args:
        file_path: 文件路径
        min_severity: 最小报告严重程度
        
    Returns:
        QualityReport: 质量报告
    """
    checker = QualityChecker(min_severity=min_severity)
    return checker.check_file(file_path)


def format_code(source: str) -> str:
    """快速格式化代码的便捷函数.
    
    Args:
        source: 源代码
        
    Returns:
        格式化后的代码
    """
    checker = QualityChecker()
    return checker.format_code(source)
