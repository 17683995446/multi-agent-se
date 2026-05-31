"""熵值计算模型 - 阶段15.

计算系统熵值指标：
- 代码复杂度熵
- 依赖混乱度熵
- 状态分散度熵
- 架构偏离度熵
"""

import ast
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class EntropyType(Enum):
    """熵值类型."""
    CODE_COMPLEXITY = "code_complexity"      # 代码复杂度熵
    DEPENDENCY_CHAOS = "dependency_chaos"    # 依赖混乱度熵
    STATE_DISPERSION = "state_dispersion"    # 状态分散度熵
    ARCHITECTURE_DRIFT = "architecture_drift"  # 架构偏离度熵
    NAMING_INCONSISTENCY = "naming_inconsistency"  # 命名不一致熵


@dataclass
class EntropyMetric:
    """熵值指标."""
    entropy_type: EntropyType
    value: float  # 0-100，越高越混乱
    details: Dict[str, Any] = field(default_factory=dict)
    threshold: float = 50.0  # 阈值
    
    @property
    def is_acceptable(self) -> bool:
        """是否在可接受范围."""
        return self.value <= self.threshold
    
    @property
    def severity(self) -> str:
        """严重程度."""
        if self.value <= 30:
            return "low"
        elif self.value <= 60:
            return "medium"
        elif self.value <= 80:
            return "high"
        else:
            return "critical"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.entropy_type.value,
            "value": round(self.value, 2),
            "threshold": self.threshold,
            "is_acceptable": self.is_acceptable,
            "severity": self.severity,
            "details": self.details,
        }


@dataclass
class EntropyReport:
    """熵值报告."""
    metrics: List[EntropyMetric] = field(default_factory=list)
    total_score: float = 0.0  # 综合得分(0-100)
    
    @property
    def average_entropy(self) -> float:
        """平均熵值."""
        if not self.metrics:
            return 0.0
        return sum(m.value for m in self.metrics) / len(self.metrics)
    
    @property
    def max_entropy(self) -> float:
        """最大熵值."""
        if not self.metrics:
            return 0.0
        return max(m.value for m in self.metrics)
    
    @property
    def critical_issues(self) -> List[EntropyMetric]:
        """严重问题."""
        return [m for m in self.metrics if m.severity == "critical"]
    
    @property
    def is_healthy(self) -> bool:
        """系统是否健康."""
        return all(m.is_acceptable for m in self.metrics)
    
    def get_by_type(self, entropy_type: EntropyType) -> Optional[EntropyMetric]:
        """按类型获取指标."""
        for m in self.metrics:
            if m.entropy_type == entropy_type:
                return m
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": round(self.total_score, 2),
            "average_entropy": round(self.average_entropy, 2),
            "max_entropy": round(self.max_entropy, 2),
            "is_healthy": self.is_healthy,
            "metrics": [m.to_dict() for m in self.metrics],
            "critical_count": len(self.critical_issues),
        }


class EntropyCalculator:
    """熵值计算器.
    
    计算系统各维度的熵值指标
    """
    
    def __init__(self) -> None:
        """初始化计算器."""
        self._metrics: List[EntropyMetric] = []
    
    def calculate_code_complexity(
        self,
        source_code: str,
        file_path: str = "",
    ) -> EntropyMetric:
        """计算代码复杂度熵.
        
        基于：圈复杂度、函数长度、嵌套深度
        
        Args:
            source_code: 源代码
            file_path: 文件路径
            
        Returns:
            EntropyMetric
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return EntropyMetric(
                entropy_type=EntropyType.CODE_COMPLEXITY,
                value=0.0,
                details={"error": "parse_error"},
            )
        
        total_complexity = 0
        function_count = 0
        max_function_lines = 0
        max_nesting_depth = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_count += 1
                func_lines = node.end_lineno - node.lineno if node.end_lineno else 1
                max_function_lines = max(max_function_lines, func_lines)
                
                # 简单圈复杂度：分支数量
                complexity = 1  # 基础复杂度
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                        complexity += 1
                    elif isinstance(child, ast.ExceptHandler):
                        complexity += 1
                
                total_complexity += complexity
                
                # 计算嵌套深度
                depth = self._calculate_nesting_depth(node)
                max_nesting_depth = max(max_nesting_depth, depth)
        
        # 归一化到0-100
        avg_complexity = total_complexity / max(function_count, 1)
        entropy_value = min(100, avg_complexity * 10 + max_function_lines / 5 + max_nesting_depth * 5)
        
        return EntropyMetric(
            entropy_type=EntropyType.CODE_COMPLEXITY,
            value=entropy_value,
            details={
                "function_count": function_count,
                "avg_complexity": round(avg_complexity, 2),
                "max_function_lines": max_function_lines,
                "max_nesting_depth": max_nesting_depth,
            },
            threshold=50.0,
        )
    
    def _calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """计算嵌套深度."""
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, depth)
            else:
                depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, depth)
        return max_depth
    
    def calculate_dependency_chaos(
        self,
        dependencies: Dict[str, List[str]],
    ) -> EntropyMetric:
        """计算依赖混乱度熵.
        
        基于：循环依赖数量、跨层依赖数量、依赖深度
        
        Args:
            dependencies: 依赖图 {模块: [依赖列表]}
            
        Returns:
            EntropyMetric
        """
        if not dependencies:
            return EntropyMetric(
                entropy_type=EntropyType.DEPENDENCY_CHAOS,
                value=0.0,
                details={},
            )
        
        # 计算依赖统计
        total_deps = sum(len(deps) for deps in dependencies.values())
        module_count = len(dependencies)
        avg_deps = total_deps / max(module_count, 1)
        
        # 检测循环依赖（简化版）
        cycles = self._detect_cycles(dependencies)
        
        # 计算熵值
        cycle_penalty = len(cycles) * 20
        density_penalty = avg_deps * 5
        entropy_value = min(100, cycle_penalty + density_penalty)
        
        return EntropyMetric(
            entropy_type=EntropyType.DEPENDENCY_CHAOS,
            value=entropy_value,
            details={
                "module_count": module_count,
                "total_dependencies": total_deps,
                "avg_dependencies": round(avg_deps, 2),
                "cycle_count": len(cycles),
                "cycles": cycles[:5],  # 最多显示5个
            },
            threshold=40.0,
        )
    
    def _detect_cycles(
        self,
        dependencies: Dict[str, List[str]],
    ) -> List[List[str]]:
        """检测循环依赖."""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependencies.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # 发现循环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            path.pop()
            rec_stack.discard(node)
        
        for node in dependencies:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    def calculate_state_dispersion(
        self,
        state_locations: List[str],
    ) -> EntropyMetric:
        """计算状态分散度熵.
        
        基于：状态分散的文件数量、重复定义数量
        
        Args:
            state_locations: 状态定义位置列表
            
        Returns:
            EntropyMetric
        """
        if not state_locations:
            return EntropyMetric(
                entropy_type=EntropyType.STATE_DISPERSION,
                value=0.0,
                details={},
            )
        
        # 统计不同位置
        unique_locations = len(set(state_locations))
        total_states = len(state_locations)
        
        # 计算分散度
        dispersion_ratio = unique_locations / max(total_states, 1)
        entropy_value = min(100, dispersion_ratio * 100)
        
        return EntropyMetric(
            entropy_type=EntropyType.STATE_DISPERSION,
            value=entropy_value,
            details={
                "total_states": total_states,
                "unique_locations": unique_locations,
                "dispersion_ratio": round(dispersion_ratio, 2),
            },
            threshold=60.0,
        )
    
    def calculate_architecture_drift(
        self,
        violations: List[Dict[str, Any]],
    ) -> EntropyMetric:
        """计算架构偏离度熵.
        
        基于：架构违规数量、严重程度
        
        Args:
            violations: 架构违规列表
            
        Returns:
            EntropyMetric
        """
        if not violations:
            return EntropyMetric(
                entropy_type=EntropyType.ARCHITECTURE_DRIFT,
                value=0.0,
                details={"violation_count": 0},
            )
        
        # 按严重程度统计
        severity_weights = {
            "critical": 10,
            "high": 5,
            "medium": 2,
            "low": 1,
        }
        
        total_weight = sum(
            severity_weights.get(v.get("severity", "low"), 1)
            for v in violations
        )
        
        entropy_value = min(100, total_weight * 2)
        
        return EntropyMetric(
            entropy_type=EntropyType.ARCHITECTURE_DRIFT,
            value=entropy_value,
            details={
                "violation_count": len(violations),
                "total_weight": total_weight,
                "by_severity": {
                    sev: sum(1 for v in violations if v.get("severity") == sev)
                    for sev in severity_weights.keys()
                },
            },
            threshold=30.0,
        )
    
    def calculate_naming_inconsistency(
        self,
        names: List[str],
    ) -> EntropyMetric:
        """计算命名不一致熵.
        
        基于：命名风格混杂程度
        
        Args:
            names: 名称列表
            
        Returns:
            EntropyMetric
        """
        if not names:
            return EntropyMetric(
                entropy_type=EntropyType.NAMING_INCONSISTENCY,
                value=0.0,
                details={},
            )
        
        # 统计命名风格
        styles = {
            "snake_case": 0,
            "camelCase": 0,
            "PascalCase": 0,
            "UPPER_CASE": 0,
            "mixed": 0,
        }
        
        for name in names:
            style = self._detect_naming_style(name)
            styles[style] += 1
        
        # 计算不一致度（使用香农熵）
        total = len(names)
        entropy = 0.0
        for count in styles.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # 归一化到0-100
        max_entropy = math.log2(len(styles))
        normalized_entropy = (entropy / max_entropy) * 100 if max_entropy > 0 else 0
        
        return EntropyMetric(
            entropy_type=EntropyType.NAMING_INCONSISTENCY,
            value=normalized_entropy,
            details={
                "total_names": total,
                "style_distribution": styles,
                "shannon_entropy": round(entropy, 2),
            },
            threshold=50.0,
        )
    
    def _detect_naming_style(self, name: str) -> str:
        """检测命名风格."""
        if name.isupper():
            return "UPPER_CASE"
        elif name[0].isupper():
            return "PascalCase"
        elif "_" in name:
            return "snake_case"
        elif any(c.isupper() for c in name[1:]):
            return "camelCase"
        else:
            return "mixed"
    
    def calculate_file(self, file_path: str) -> EntropyReport:
        """计算单个文件的熵值报告.
        
        Args:
            file_path: 文件路径
            
        Returns:
            EntropyReport
        """
        path = Path(file_path)
        if not path.exists():
            return EntropyReport(metrics=[], total_score=0.0)
        
        source = path.read_text(encoding="utf-8")
        
        metrics = [
            self.calculate_code_complexity(source, file_path),
        ]
        
        # 计算综合得分
        total_score = 100 - sum(m.value for m in metrics) / max(len(metrics), 1)
        
        return EntropyReport(
            metrics=metrics,
            total_score=max(0, total_score),
        )
    
    def calculate_directory(
        self,
        directory: str,
        pattern: str = "*.py",
    ) -> EntropyReport:
        """计算目录的熵值报告.
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            
        Returns:
            EntropyReport
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return EntropyReport()
        
        all_metrics: List[EntropyMetric] = []
        all_names: List[str] = []
        
        for py_file in sorted(dir_path.rglob(pattern)):
            report = self.calculate_file(str(py_file))
            all_metrics.extend(report.metrics)
            
            # 收集名称用于命名一致性计算
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        all_names.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        all_names.append(node.name)
            except Exception:
                pass
        
        # 添加命名一致性指标
        if all_names:
            naming_metric = self.calculate_naming_inconsistency(all_names)
            all_metrics.append(naming_metric)
        
        # 计算综合得分
        avg_entropy = sum(m.value for m in all_metrics) / max(len(all_metrics), 1)
        total_score = max(0, 100 - avg_entropy)
        
        return EntropyReport(
            metrics=all_metrics,
            total_score=total_score,
        )


def calculate_module_entropy(module_path: str) -> EntropyReport:
    """便捷函数：计算模块熵值.
    
    Args:
        module_path: 模块路径（文件或目录）
        
    Returns:
        EntropyReport
    """
    calculator = EntropyCalculator()
    path = Path(module_path)
    
    if path.is_file():
        return calculator.calculate_file(module_path)
    else:
        return calculator.calculate_directory(module_path)
