"""Ruff静态代码检查封装模块 - 阶段8.

复用Ruff开源内核，提供统一检查/格式化接口
"""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RuffIssue:
    """Ruff检查问题."""
    code: str
    message: str
    file: str
    line: int
    col: int
    end_line: int
    end_col: int
    fixable: bool = False
    rule_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "col": self.col,
            "end_line": self.end_line,
            "end_col": self.end_col,
            "fixable": self.fixable,
        }


@dataclass
class RuffResult:
    """Ruff检查结果."""
    issues: List[RuffIssue] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    fixable_count: int = 0
    
    @property
    def total(self) -> int:
        return len(self.issues)
    
    @property
    def has_errors(self) -> bool:
        return self.error_count > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "fixable": self.fixable_count,
            "issues": [i.to_dict() for i in self.issues],
        }


class RuffChecker:
    """Ruff检查器.
    
    封装Ruff CLI，提供Python接口
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """初始化检查器.
        
        Args:
            config_path: 配置文件路径
        """
        self._config_path = config_path
    
    def _build_args(
        self,
        action: str,
        paths: List[str],
        select: Optional[List[str]] = None,
        ignore: Optional[List[str]] = None,
        fix: bool = False,
    ) -> List[str]:
        """构建命令行参数."""
        args = ["ruff", action]
        
        if self._config_path:
            args.extend(["--config", self._config_path])
        
        if select:
            args.extend(["--select", ",".join(select)])
        if ignore:
            args.extend(["--ignore", ",".join(ignore)])
        if fix:
            args.append("--fix")
        
        args.extend(paths)
        return args
    
    def check(
        self,
        source: Optional[str] = None,
        file_path: Optional[str] = None,
        select: Optional[List[str]] = None,
        ignore: Optional[List[str]] = None,
    ) -> RuffResult:
        """执行代码检查.
        
        Args:
            source: 源码字符串
            file_path: 文件路径
            select: 选择的规则
            ignore: 忽略的规则
            
        Returns:
            RuffResult
        """
        if source is not None:
            result = subprocess.run(
                ["ruff", "check", "-", "--output-format=json"] +
                (["--select", ",".join(select)] if select else []) +
                (["--ignore", ",".join(ignore)] if ignore else []),
                capture_output=True, text=True, input=source,
            )
        elif file_path is not None:
            args = self._build_args("check", [file_path], select, ignore)
            result = subprocess.run(args, capture_output=True, text=True)
        else:
            return RuffResult()
        
        issues = []
        if result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                issues = self._parse_issues(data, file_path or "<stdin>")
            except json.JSONDecodeError:
                pass
        
        return RuffResult(
            issues=issues,
            error_count=sum(1 for i in issues if i.code.startswith("E")),
            warning_count=sum(1 for i in issues if i.code.startswith("W")),
            fixable_count=sum(1 for i in issues if i.fixable),
        )
    
    def check_file(
        self,
        file_path: str,
        select: Optional[List[str]] = None,
    ) -> RuffResult:
        """检查文件."""
        return self.check(file_path=file_path, select=select)
    
    def format_code(self, source: str) -> str:
        """格式化代码.
        
        Args:
            source: 源码字符串
            
        Returns:
            格式化后的代码
        """
        result = subprocess.run(
            ["ruff", "format", "-"],
            capture_output=True, text=True, input=source,
        )
        return result.stdout if result.returncode == 0 else source
    
    def format_diff(self, source: str) -> str:
        """获取格式化差异.
        
        Args:
            source: 源码字符串
            
        Returns:
            diff字符串
        """
        result = subprocess.run(
            ["ruff", "format", "-", "--diff"],
            capture_output=True, text=True, input=source,
        )
        return result.stdout
    
    def _parse_issues(self, data: Any, file_path: str) -> List[RuffIssue]:
        """解析检查结果."""
        issues = []
        for item in data:
            loc = item.get("location", {})
            end_loc = item.get("end_location", {})
            issues.append(RuffIssue(
                code=item.get("code", ""),
                message=item.get("message", ""),
                file=file_path,
                line=loc.get("row", 0),
                col=loc.get("column", 0),
                end_line=end_loc.get("row", 0),
                end_col=end_loc.get("column", 0),
                fixable=item.get("fix", {}).get("availability") == "safe"
                    if isinstance(item.get("fix"), dict) else False,
            ))
        return issues


# 全局检查器实例
ruff_checker = RuffChecker()
