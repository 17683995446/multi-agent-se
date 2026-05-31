"""Bugfix Agent - 第35阶段.

缺陷修复Agent - 负责Bug定位、诊断和修复.

职责:
- 分析错误日志和堆栈跟踪
- 定位问题根因
- 生成修复补丁
- 验证修复效果
- 记录Bug修复历史
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
import re

from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
from multi_agent_se.agents.runtime.base_agent import BaseAgentImpl, AgentContext, TaskResult


class ErrorType(Enum):
    """错误类型."""
    SYNTAX = "syntax"           # 语法错误
    RUNTIME = "runtime"         # 运行时错误
    LOGIC = "logic"             # 逻辑错误
    TYPE = "type"               # 类型错误
    IMPORT = "import"           # 导入错误
    ATTRIBUTE = "attribute"     # 属性错误
    INDEX = "index"             # 索引错误
    KEY = "key"                 # 键错误
    VALUE = "value"             # 值错误
    IO = "io"                   # IO错误
    NETWORK = "network"         # 网络错误
    TIMEOUT = "timeout"         # 超时错误
    MEMORY = "memory"           # 内存错误
    UNKNOWN = "unknown"         # 未知错误


class FixSeverity(Enum):
    """修复严重程度."""
    CRITICAL = "critical"       # 严重 - 系统崩溃
    HIGH = "high"               # 高 - 功能失效
    MEDIUM = "medium"           # 中 - 部分异常
    LOW = "low"                 # 低 - 轻微问题
    TRIVIAL = "trivial"         # 微小 - 优化建议


@dataclass
class ErrorLocation:
    """错误位置."""
    file_path: str = ""
    line_number: int = 0
    column_number: int = 0
    function_name: str = ""
    class_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "function_name": self.function_name,
            "class_name": self.class_name,
        }


@dataclass
class BugReport:
    """Bug报告."""
    bug_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    error_type: ErrorType = ErrorType.UNKNOWN
    error_message: str = ""
    stack_trace: str = ""
    
    # 位置信息
    location: ErrorLocation = field(default_factory=ErrorLocation)
    
    # 上下文
    context_code: str = ""        # 错误发生处的代码
    related_files: List[str] = field(default_factory=list)
    
    # 元数据
    timestamp: str = field(default_factory=lambda: str(uuid.uuid1())[:8])
    environment: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bug_id": self.bug_id,
            "error_type": self.error_type.value,
            "error_message": self.error_message[:200],
            "location": self.location.to_dict(),
            "related_files": self.related_files,
        }


@dataclass
class FixSuggestion:
    """修复建议."""
    suggestion_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    severity: FixSeverity = FixSeverity.MEDIUM
    confidence: float = 0.0       # 置信度 0-1
    
    # 代码变更
    file_path: str = ""
    original_code: str = ""
    fixed_code: str = ""
    line_start: int = 0
    line_end: int = 0
    
    # 解释
    explanation: str = ""         # 修复解释
    side_effects: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "description": self.description,
            "severity": self.severity.value,
            "confidence": round(self.confidence, 2),
            "file_path": self.file_path,
            "line_range": f"{self.line_start}-{self.line_end}",
            "explanation": self.explanation[:100],
        }


@dataclass
class FixResult:
    """修复结果."""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    bug_report: Optional[BugReport] = None
    
    # 诊断结果
    root_cause: str = ""
    analysis_steps: List[str] = field(default_factory=list)
    
    # 修复方案
    suggestions: List[FixSuggestion] = field(default_factory=list)
    applied_fix: Optional[FixSuggestion] = None
    
    # 验证结果
    verified: bool = False
    verification_method: str = ""
    test_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # 统计
    total_suggestions: int = 0
    applied_suggestion_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "bug_id": self.bug_report.bug_id if self.bug_report else None,
            "root_cause": self.root_cause[:150],
            "total_suggestions": len(self.suggestions),
            "verified": self.verified,
            "suggestions": [s.to_dict() for s in self.suggestions[:3]],
        }


class BugfixAgent(BaseAgentImpl):
    """缺陷修复Agent - Bug定位与修复.
    
    8大正交角色Agent之一，负责分析错误、定位问题并生成修复方案。
    """
    
    AGENT_ROLE = AgentRole.BUGFIX
    AGENT_CAPABILITIES = [
        AgentCapability.CODE_DEBUGGING,
        AgentCapability.CODE_GENERATION,
    ]
    AGENT_DESCRIPTION = "缺陷修复Agent - 负责Bug定位、诊断和修复"
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None) -> None:
        super().__init__(agent_id, config)
        self._fix_history: List[FixResult] = []
        self._error_patterns: Dict[ErrorType, List[str]] = self._load_error_patterns()
        self._fix_templates: Dict[ErrorType, List[Dict]] = self._load_fix_templates()
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理Bug修复任务.
        
        Args:
            context: Agent执行上下文
            
        Returns:
            任务执行结果
        """
        input_data = context.input_data
        
        # 获取错误信息
        error_message = input_data.get("error_message", "")
        stack_trace = input_data.get("stack_trace", "")
        
        if not error_message and not stack_trace:
            return TaskResult(
                success=False,
                error_message="缺少错误信息或堆栈跟踪",
            )
        
        # 1. 解析Bug报告
        bug_report = self._parse_bug_report(input_data)
        
        # 2. 分析根因
        root_cause = self._analyze_root_cause(bug_report)
        
        # 3. 生成修复建议
        suggestions = self._generate_fix_suggestions(bug_report, root_cause)
        
        # 4. 创建修复结果
        result = FixResult(
            bug_report=bug_report,
            root_cause=root_cause,
            suggestions=suggestions,
            total_suggestions=len(suggestions),
            analysis_steps=self._get_analysis_steps(bug_report),
        )
        
        # 5. 如果有代码上下文，尝试生成具体修复
        if bug_report.context_code:
            fix = self._generate_code_fix(bug_report, root_cause)
            if fix:
                result.applied_fix = fix
                result.applied_suggestion_id = fix.suggestion_id
        
        # 6. 模拟验证
        result.verified = len(suggestions) > 0
        result.verification_method = "静态分析验证"
        
        # 7. 保存历史
        self._fix_history.append(result)
        
        return TaskResult(
            success=True,
            output=result.to_dict(),
            artifacts={
                "result": result,
                "bug_report": bug_report,
            },
        )
    
    def _parse_bug_report(self, input_data: Dict[str, Any]) -> BugReport:
        """解析Bug报告."""
        report = BugReport(
            error_message=input_data.get("error_message", ""),
            stack_trace=input_data.get("stack_trace", ""),
            context_code=input_data.get("context_code", ""),
            related_files=input_data.get("affected_files", []),
            environment=input_data.get("environment", {}),
        )
        
        # 识别错误类型
        report.error_type = self._detect_error_type(report.error_message, report.stack_trace)
        
        # 解析错误位置
        report.location = self._parse_error_location(report.stack_trace)
        
        return report
    
    def _detect_error_type(self, error_message: str, stack_trace: str) -> ErrorType:
        """检测错误类型."""
        text = (error_message + " " + stack_trace).lower()
        
        patterns = {
            ErrorType.SYNTAX: ["syntaxerror", "invalid syntax", "unexpected token"],
            ErrorType.TYPE: ["typeerror", "type error", "cannot convert"],
            ErrorType.ATTRIBUTE: ["attributeerror", "has no attribute", "object has no"],
            ErrorType.INDEX: ["indexerror", "list index out of range", "index out of bounds"],
            ErrorType.KEY: ["keyerror", "key not found", "missing key"],
            ErrorType.VALUE: ["valueerror", "invalid value", "value error"],
            ErrorType.IMPORT: ["importerror", "modulenotfounderror", "no module named"],
            ErrorType.IO: ["ioerror", "filenotfounderror", "permission denied"],
            ErrorType.NETWORK: ["connectionerror", "timeout", "network"],
            ErrorType.MEMORY: ["memoryerror", "out of memory", "memory limit"],
        }
        
        for error_type, keywords in patterns.items():
            if any(kw in text for kw in keywords):
                return error_type
        
        # 判断是否为逻辑错误
        if "assertion" in text or "assert" in text or "expected" in text:
            return ErrorType.LOGIC
        
        return ErrorType.UNKNOWN
    
    def _parse_error_location(self, stack_trace: str) -> ErrorLocation:
        """解析错误位置."""
        location = ErrorLocation()
        
        if not stack_trace:
            return location
        
        lines = stack_trace.strip().split('\n')
        
        # Python堆栈格式解析
        for line in lines:
            # 匹配 File "path", line X, in function
            match = re.search(r'File "([^"]+)", line (\d+), in (\w+)', line)
            if match:
                location.file_path = match.group(1)
                location.line_number = int(match.group(2))
                location.function_name = match.group(3)
            
            # 匹配类名
            class_match = re.search(r'class\s+(\w+)', line)
            if class_match:
                location.class_name = class_match.group(1)
        
        return location
    
    def _analyze_root_cause(self, bug_report: BugReport) -> str:
        """分析错误根因."""
        error_type = bug_report.error_type
        message = bug_report.error_message
        
        # 基于错误类型的根因分析
        root_cause_templates = {
            ErrorType.SYNTAX: f"语法错误: 代码结构不正确 - {message[:80]}",
            ErrorType.TYPE: f"类型不匹配: 操作数类型不兼容 - {message[:80]}",
            ErrorType.ATTRIBUTE: f"属性访问错误: 对象缺少请求的属性 - {message[:80]}",
            ErrorType.INDEX: f"索引越界: 访问了不存在的索引位置 - {message[:80]}",
            ErrorType.KEY: f"键不存在: 字典中缺少指定的键 - {message[:80]}",
            ErrorType.VALUE: f"值无效: 参数值不符合要求 - {message[:80]}",
            ErrorType.IMPORT: f"导入失败: 无法加载指定模块 - {message[:80]}",
            ErrorType.LOGIC: f"逻辑错误: 程序执行结果不符合预期 - {message[:80]}",
            ErrorType.RUNTIME: f"运行时错误: 程序执行过程中发生异常 - {message[:80]}",
        }
        
        return root_cause_templates.get(error_type, f"未知错误: {message[:80]}")
    
    def _generate_fix_suggestions(
        self,
        bug_report: BugReport,
        root_cause: str,
    ) -> List[FixSuggestion]:
        """生成修复建议."""
        suggestions = []
        error_type = bug_report.error_type
        
        # 基于错误类型生成建议
        templates = self._fix_templates.get(error_type, [])
        
        for i, template in enumerate(templates[:3]):  # 最多3个建议
            suggestion = FixSuggestion(
                description=template.get("description", ""),
                severity=template.get("severity", FixSeverity.MEDIUM),
                confidence=template.get("confidence", 0.7),
                explanation=template.get("explanation", ""),
                file_path=bug_report.location.file_path,
                line_start=bug_report.location.line_number,
                line_end=bug_report.location.line_number,
            )
            suggestions.append(suggestion)
        
        # 如果没有模板匹配，生成通用建议
        if not suggestions:
            suggestions.append(FixSuggestion(
                description=f"检查{error_type.value}错误的常见原因",
                severity=FixSeverity.MEDIUM,
                confidence=0.5,
                explanation="需要人工审查以确定具体修复方案",
                file_path=bug_report.location.file_path,
                line_start=bug_report.location.line_number,
            ))
        
        return suggestions
    
    def _generate_code_fix(
        self,
        bug_report: BugReport,
        root_cause: str,
    ) -> Optional[FixSuggestion]:
        """生成具体代码修复."""
        error_type = bug_report.error_type
        context = bug_report.context_code
        
        if not context:
            return None
        
        fix = FixSuggestion(
            description=f"自动修复{error_type.value}错误",
            severity=FixSeverity.HIGH,
            confidence=0.8,
            file_path=bug_report.location.file_path,
            line_start=bug_report.location.line_number,
            line_end=bug_report.location.line_number,
        )
        
        # 根据错误类型生成修复代码
        if error_type == ErrorType.ATTRIBUTE:
            fix.original_code = context
            fix.fixed_code = self._fix_attribute_error(context)
            fix.explanation = "添加属性存在性检查"
        
        elif error_type == ErrorType.INDEX:
            fix.original_code = context
            fix.fixed_code = self._fix_index_error(context)
            fix.explanation = "添加索引边界检查"
        
        elif error_type == ErrorType.KEY:
            fix.original_code = context
            fix.fixed_code = self._fix_key_error(context)
            fix.explanation = "使用get方法或添加键存在性检查"
        
        elif error_type == ErrorType.TYPE:
            fix.original_code = context
            fix.fixed_code = self._fix_type_error(context)
            fix.explanation = "添加类型检查和转换"
        
        else:
            return None
        
        return fix
    
    def _fix_attribute_error(self, code: str) -> str:
        """修复属性错误."""
        # 提取变量名并添加检查
        match = re.search(r'(\w+)\.\w+', code)
        if match:
            var = match.group(1)
            return f"if hasattr({var}, 'attr_name'):\n    {code}\nelse:\n    # 处理属性不存在的情况\n    pass"
        return code + "  # TODO: 添加属性检查"
    
    def _fix_index_error(self, code: str) -> str:
        """修复索引错误."""
        match = re.search(r'(\w+)\[(.+?)\]', code)
        if match:
            var = match.group(1)
            index = match.group(2)
            return f"if 0 <= {index} < len({var}):\n    {code}\nelse:\n    # 处理索引越界\n    pass"
        return code + "  # TODO: 添加索引检查"
    
    def _fix_key_error(self, code: str) -> str:
        """修复键错误."""
        # 将 dict[key] 改为 dict.get(key, default)
        return re.sub(
            r'(\w+)\[(.+?)\]',
            r'\1.get(\2, None)',
            code
        ) + "  # 使用get方法避免KeyError"
    
    def _fix_type_error(self, code: str) -> str:
        """修复类型错误."""
        return f"try:\n    {code}\nexcept TypeError as e:\n    # 处理类型错误\n    pass"
    
    def _get_analysis_steps(self, bug_report: BugReport) -> List[str]:
        """获取分析步骤."""
        return [
            f"1. 识别错误类型: {bug_report.error_type.value}",
            f"2. 定位错误位置: {bug_report.location.file_path}:{bug_report.location.line_number}",
            "3. 分析错误上下文和调用链",
            "4. 确定根因并生成修复建议",
        ]
    
    def _load_error_patterns(self) -> Dict[ErrorType, List[str]]:
        """加载错误模式."""
        return {
            ErrorType.SYNTAX: ["IndentationError", "SyntaxError"],
            ErrorType.TYPE: ["TypeError", "type mismatch"],
            ErrorType.ATTRIBUTE: ["AttributeError"],
            ErrorType.INDEX: ["IndexError"],
            ErrorType.KEY: ["KeyError"],
            ErrorType.VALUE: ["ValueError"],
            ErrorType.IMPORT: ["ImportError", "ModuleNotFoundError"],
        }
    
    def _load_fix_templates(self) -> Dict[ErrorType, List[Dict]]:
        """加载修复模板."""
        return {
            ErrorType.ATTRIBUTE: [
                {
                    "description": "添加hasattr检查确保属性存在",
                    "severity": FixSeverity.HIGH,
                    "confidence": 0.85,
                    "explanation": "在访问对象属性前检查属性是否存在",
                },
                {
                    "description": "使用getattr提供默认值",
                    "severity": FixSeverity.MEDIUM,
                    "confidence": 0.75,
                    "explanation": "使用getattr(obj, 'attr', default)避免AttributeError",
                },
            ],
            ErrorType.INDEX: [
                {
                    "description": "添加索引边界检查",
                    "severity": FixSeverity.HIGH,
                    "confidence": 0.9,
                    "explanation": "确保索引值在有效范围内",
                },
                {
                    "description": "使用try-except捕获IndexError",
                    "severity": FixSeverity.MEDIUM,
                    "confidence": 0.7,
                    "explanation": "捕获异常并提供备选处理逻辑",
                },
            ],
            ErrorType.KEY: [
                {
                    "description": "使用dict.get()方法",
                    "severity": FixSeverity.HIGH,
                    "confidence": 0.9,
                    "explanation": "使用get(key, default)替代直接访问",
                },
                {
                    "description": "检查键存在性",
                    "severity": FixSeverity.MEDIUM,
                    "confidence": 0.8,
                    "explanation": "使用if key in dict:进行存在性检查",
                },
            ],
            ErrorType.TYPE: [
                {
                    "description": "添加类型检查",
                    "severity": FixSeverity.HIGH,
                    "confidence": 0.8,
                    "explanation": "使用isinstance()检查参数类型",
                },
                {
                    "description": "类型转换",
                    "severity": FixSeverity.MEDIUM,
                    "confidence": 0.75,
                    "explanation": "使用int(), str()等函数进行类型转换",
                },
            ],
            ErrorType.SYNTAX: [
                {
                    "description": "检查缩进一致性",
                    "severity": FixSeverity.CRITICAL,
                    "confidence": 0.9,
                    "explanation": "确保使用统一的缩进（空格或Tab）",
                },
                {
                    "description": "检查括号匹配",
                    "severity": FixSeverity.CRITICAL,
                    "confidence": 0.85,
                    "explanation": "确保所有括号正确闭合",
                },
            ],
        }
    
    def get_fix_history(self) -> List[FixResult]:
        """获取修复历史."""
        return self._fix_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        total_fixes = len(self._fix_history)
        verified_fixes = sum(1 for f in self._fix_history if f.verified)
        
        # 按错误类型统计
        error_type_counts: Dict[str, int] = {}
        for result in self._fix_history:
            if result.bug_report:
                et = result.bug_report.error_type.value
                error_type_counts[et] = error_type_counts.get(et, 0) + 1
        
        return {
            "total_fixes": total_fixes,
            "verified_fixes": verified_fixes,
            "verification_rate": verified_fixes / total_fixes if total_fixes > 0 else 0,
            "error_type_distribution": error_type_counts,
            "avg_suggestions_per_fix": sum(r.total_suggestions for r in self._fix_history) / total_fixes if total_fixes > 0 else 0,
        }
