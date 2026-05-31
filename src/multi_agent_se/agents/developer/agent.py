"""Developer Agent - 第34阶段.

开发Agent - 负责代码实现、功能开发和单元测试编写.

职责:
- 根据架构设计实现功能代码
- 编写单元测试
- 遵循代码规范和最佳实践
- 生成代码文档
- 处理代码重构
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid
import re

from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
from multi_agent_se.agents.runtime.base_agent import BaseAgentImpl, AgentContext, TaskResult


class CodeLanguage(Enum):
    """编程语言."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    RUST = "rust"


class CodeTaskType(Enum):
    """代码任务类型."""
    IMPLEMENTATION = "implementation"   # 功能实现
    REFACTORING = "refactoring"         # 代码重构
    BUGFIX = "bugfix"                   # 缺陷修复
    OPTIMIZATION = "optimization"       # 性能优化
    TEST = "test"                       # 测试编写


@dataclass
class CodeFile:
    """代码文件."""
    file_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    file_path: str = ""
    language: CodeLanguage = CodeLanguage.PYTHON
    content: str = ""
    
    # 元数据
    lines_of_code: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # 质量指标
    complexity_score: float = 0.0
    has_tests: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_id": self.file_id,
            "file_path": self.file_path,
            "language": self.language.value,
            "lines_of_code": self.lines_of_code,
            "comment_lines": self.comment_lines,
            "has_tests": self.has_tests,
        }


@dataclass
class CodeChange:
    """代码变更."""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    change_type: str = ""  # add/modify/delete
    file_path: str = ""
    description: str = ""
    old_content: str = ""
    new_content: str = ""


@dataclass
class DevelopmentResult:
    """开发结果."""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_type: CodeTaskType = CodeTaskType.IMPLEMENTATION
    
    # 生成的文件
    files: List[CodeFile] = field(default_factory=list)
    
    # 变更记录
    changes: List[CodeChange] = field(default_factory=list)
    
    # 质量报告
    total_lines: int = 0
    test_coverage: float = 0.0
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "task_type": self.task_type.value,
            "files": [f.to_dict() for f in self.files],
            "total_lines": self.total_lines,
            "test_coverage": round(self.test_coverage, 2),
            "issues": self.issues,
        }


class DeveloperAgent(BaseAgentImpl):
    """开发Agent - 代码实现与开发.
    
    8大正交角色Agent之一，负责将架构设计转化为可运行的代码。
    """
    
    AGENT_ROLE = AgentRole.DEVELOPER
    AGENT_CAPABILITIES = [
        AgentCapability.CODE_GENERATION,
    ]
    AGENT_DESCRIPTION = "开发Agent - 负责代码实现、功能开发和单元测试编写"
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None) -> None:
        super().__init__(agent_id, config)
        self._development_history: List[DevelopmentResult] = []
        self._code_templates: Dict[str, str] = self._load_templates()
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理开发任务.
        
        Args:
            context: Agent执行上下文
            
        Returns:
            任务执行结果
        """
        input_data = context.input_data
        task_type_str = input_data.get("task_type", "implementation")
        task_type = CodeTaskType(task_type_str)
        
        requirement = input_data.get("requirement", "")
        module_name = input_data.get("module_name", "unnamed")
        
        if not requirement:
            return TaskResult(
                success=False,
                error_message="缺少开发需求",
            )
        
        # 创建开发结果
        result = DevelopmentResult(task_type=task_type)
        
        # 1. 生成代码
        if task_type == CodeTaskType.IMPLEMENTATION:
            self._generate_implementation(result, requirement, module_name)
        elif task_type == CodeTaskType.TEST:
            self._generate_tests(result, requirement, module_name)
        elif task_type == CodeTaskType.REFACTORING:
            self._perform_refactoring(result, input_data)
        else:
            self._generate_implementation(result, requirement, module_name)
        
        # 2. 分析代码质量
        self._analyze_quality(result)
        
        # 3. 保存结果
        self._development_history.append(result)
        
        return TaskResult(
            success=True,
            output=result.to_dict(),
            artifacts={
                "result": result,
            },
        )
    
    def _generate_implementation(
        self,
        result: DevelopmentResult,
        requirement: str,
        module_name: str,
    ) -> None:
        """生成功能实现代码."""
        # 解析需求，提取关键信息
        class_name = self._extract_class_name(requirement, module_name)
        methods = self._extract_methods(requirement)
        
        # 生成类代码
        code_content = self._generate_class_code(class_name, methods, requirement)
        
        file_path = f"{module_name}/{class_name.lower()}.py"
        
        code_file = CodeFile(
            file_path=file_path,
            language=CodeLanguage.PYTHON,
            content=code_content,
        )
        
        # 统计代码行数
        lines = code_content.splitlines()
        code_file.lines_of_code = len(lines)
        code_file.comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
        code_file.blank_lines = sum(1 for l in lines if not l.strip())
        
        result.files.append(code_file)
        result.total_lines = code_file.lines_of_code
        
        # 记录变更
        change = CodeChange(
            change_type="add",
            file_path=file_path,
            description=f"添加{class_name}类实现",
        )
        result.changes.append(change)
    
    def _generate_tests(
        self,
        result: DevelopmentResult,
        requirement: str,
        module_name: str,
    ) -> None:
        """生成测试代码."""
        class_name = self._extract_class_name(requirement, module_name)
        test_methods = self._generate_test_methods(class_name)
        
        test_content = f'''"""Tests for {class_name}."""

import pytest
from {module_name}.{class_name.lower()} import {class_name}


class Test{class_name}:
    """Test cases for {class_name}."""
    
{test_methods}
'''
        
        file_path = f"tests/test_{class_name.lower()}.py"
        
        code_file = CodeFile(
            file_path=file_path,
            language=CodeLanguage.PYTHON,
            content=test_content,
            has_tests=True,
        )
        
        lines = test_content.splitlines()
        code_file.lines_of_code = len(lines)
        
        result.files.append(code_file)
        result.total_lines = code_file.lines_of_code
        result.test_coverage = 0.8  # 模拟覆盖率
        
        change = CodeChange(
            change_type="add",
            file_path=file_path,
            description=f"添加{class_name}测试",
        )
        result.changes.append(change)
    
    def _perform_refactoring(
        self,
        result: DevelopmentResult,
        input_data: Dict[str, Any],
    ) -> None:
        """执行代码重构."""
        file_path = input_data.get("file_path", "")
        old_code = input_data.get("old_code", "")
        
        # 模拟重构：提取方法、重命名等
        refactored_code = self._apply_refactoring_patterns(old_code)
        
        code_file = CodeFile(
            file_path=file_path,
            content=refactored_code,
        )
        
        result.files.append(code_file)
        
        change = CodeChange(
            change_type="modify",
            file_path=file_path,
            description="代码重构",
            old_content=old_code[:100] + "..." if len(old_code) > 100 else old_code,
            new_content=refactored_code[:100] + "..." if len(refactored_code) > 100 else refactored_code,
        )
        result.changes.append(change)
    
    def _extract_class_name(self, requirement: str, default: str) -> str:
        """从需求中提取类名."""
        # 查找 "实现XXX类" 或 "XXX功能"
        patterns = [
            r'实现[一个]*(.+?)(?:类|功能|模块)',
            r'创建[一个]*(.+?)(?:类|功能|模块)',
            r'(.+?)(?:类|功能|模块)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, requirement)
            if match:
                name = match.group(1).strip()
                # 转换为驼峰命名
                words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', name)
                if words:
                    return ''.join(w.capitalize() for w in words[:2])
        
        return default.capitalize()
    
    def _extract_methods(self, requirement: str) -> List[Dict[str, Any]]:
        """从需求中提取方法."""
        methods = []
        
        # 查找动作描述
        action_patterns = [
            (r'支持(.+?)(?:功能|操作)', "支持"),
            (r'可以(.+?)', "可以"),
            (r'能够(.+?)', "能够"),
        ]
        
        for pattern, prefix in action_patterns:
            matches = re.finditer(pattern, requirement)
            for match in matches:
                action = match.group(1).strip()[:20]
                method_name = self._to_snake_case(action)
                methods.append({
                    "name": method_name,
                    "description": f"{prefix}{action}",
                })
        
        # 如果没有提取到方法，添加默认方法
        if not methods:
            methods.append({
                "name": "process",
                "description": "处理主要逻辑",
            })
        
        return methods[:3]  # 最多3个方法
    
    def _to_snake_case(self, text: str) -> str:
        """转换为蛇形命名."""
        # 移除特殊字符
        text = re.sub(r'[^\w\u4e00-\u9fa5]', '_', text)
        # 转换为小写
        return text.lower().replace('__', '_').strip('_')[:30]
    
    def _generate_class_code(
        self,
        class_name: str,
        methods: List[Dict[str, Any]],
        requirement: str,
    ) -> str:
        """生成类代码."""
        lines = [
            f'"""{class_name} - {requirement[:50]}."""',
            '',
            'from typing import Any, Dict, List, Optional',
            '',
            '',
            f'class {class_name}:',
            f'    """{requirement}."""',
            '',
            '    def __init__(self) -> None:',
            '        """初始化."""',
            '        pass',
            '',
        ]
        
        for method in methods:
            lines.extend([
                f'    def {method["name"]}(self, data: Any) -> Any:',
                f'        """{method["description"]}."""',
                '        # TODO: 实现逻辑',
                '        pass',
                '',
            ])
        
        return '\n'.join(lines)
    
    def _generate_test_methods(self, class_name: str) -> str:
        """生成测试方法."""
        methods = [
            f'    def test_{class_name.lower()}_creation(self):',
            f'        """测试{class_name}创建."""',
            f'        obj = {class_name}()',
            f'        assert obj is not None',
            '',
            f'    def test_{class_name.lower()}_process(self):',
            f'        """测试处理逻辑."""',
            f'        obj = {class_name}()',
            f'        result = obj.process({{"test": "data"}})',
            f'        assert result is not None',
            '',
        ]
        return '\n'.join(methods)
    
    def _apply_refactoring_patterns(self, code: str) -> str:
        """应用重构模式."""
        # 模拟重构：添加类型注解、改进命名等
        refactored = code
        
        # 添加类型注解
        if 'def ' in refactored and '->' not in refactored:
            refactored = re.sub(
                r'def (\w+)\(self\):',
                r'def \1(self) -> None:',
                refactored
            )
        
        return refactored
    
    def _analyze_quality(self, result: DevelopmentResult) -> None:
        """分析代码质量."""
        for file in result.files:
            # 检查代码规范
            if file.lines_of_code > 200:
                result.issues.append(f"{file.file_path}: 文件过长，建议拆分")
            
            if file.comment_lines / max(file.lines_of_code, 1) < 0.1:
                result.issues.append(f"{file.file_path}: 注释不足，建议添加文档字符串")
    
    def _load_templates(self) -> Dict[str, str]:
        """加载代码模板."""
        return {
            "class": "class {name}:\n    pass",
            "function": "def {name}():\n    pass",
        }
    
    def get_development_history(self) -> List[DevelopmentResult]:
        """获取开发历史."""
        return self._development_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        total_results = len(self._development_history)
        total_lines = sum(r.total_lines for r in self._development_history)
        total_files = sum(len(r.files) for r in self._development_history)
        
        return {
            "total_tasks": total_results,
            "total_lines_written": total_lines,
            "total_files_created": total_files,
            "avg_lines_per_task": total_lines / total_results if total_results > 0 else 0,
        }
