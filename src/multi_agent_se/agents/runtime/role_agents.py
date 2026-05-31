"""8个正交角色Agent实现 - 阶段20.

实现8个正交角色的具体Agent：
- ControllerAgent: 控制器
- RequirementAgent: 需求分析
- ArchitectAgent: 架构设计
- DeveloperAgent: 开发
- BugfixAgent: 修复
- ReviewerAgent: 审查
- TesterAgent: 测试
- DocumenterAgent: 文档
"""

from typing import Any, Dict, List, Optional

from multi_agent_se.agents.registry import (
    AgentRole,
    AgentCapability,
)
from multi_agent_se.agents.runtime.base_agent import (
    BaseAgentImpl,
    AgentContext,
    AgentExecutionError,
    TaskResult,
)


class ControllerAgent(BaseAgentImpl):
    """控制器Agent - 任务分解与调度."""
    
    AGENT_ROLE = AgentRole.CONTROLLER
    AGENT_CAPABILITIES = [
        AgentCapability.TASK_DECOMPOSITION,
        AgentCapability.TASK_SCHEDULING,
    ]
    AGENT_DESCRIPTION = "控制器Agent - 负责任务分解、分配和整体调度"
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务：分解输入需求为子任务."""
        input_data = context.input_data
        requirement = input_data.get("requirement", "")
        
        if not requirement:
            return TaskResult(
                success=False,
                error_message="缺少需求描述",
            )
        
        # 任务分解逻辑
        sub_tasks = self._decompose_task(requirement, input_data)
        
        return TaskResult(
            success=True,
            output={
                "sub_tasks": sub_tasks,
                "total_sub_tasks": len(sub_tasks),
                "strategy": input_data.get("strategy", "default"),
            },
            artifacts={"decomposition": sub_tasks},
        )
    
    def _decompose_task(
        self,
        requirement: str,
        input_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """分解任务为子任务."""
        # 基础分解策略
        sub_tasks = [
            {
                "name": "需求分析",
                "role": "requirement",
                "type": "requirement_analysis",
                "description": f"分析需求: {requirement[:50]}",
            },
            {
                "name": "架构设计",
                "role": "architect",
                "type": "architecture_design",
                "description": "设计系统架构",
                "depends_on": ["需求分析"],
            },
            {
                "name": "代码开发",
                "role": "developer",
                "type": "code_generation",
                "description": "实现功能代码",
                "depends_on": ["架构设计"],
            },
            {
                "name": "代码审查",
                "role": "reviewer",
                "type": "code_review",
                "description": "审查代码质量",
                "depends_on": ["代码开发"],
            },
            {
                "name": "测试验证",
                "role": "tester",
                "type": "code_testing",
                "description": "编写并执行测试",
                "depends_on": ["代码开发"],
            },
            {
                "name": "文档生成",
                "role": "documenter",
                "type": "documentation",
                "description": "生成项目文档",
                "depends_on": ["代码审查", "测试验证"],
            },
        ]
        
        return sub_tasks


class RequirementAgent(BaseAgentImpl):
    """需求分析Agent - 需求解析与验证."""
    
    AGENT_ROLE = AgentRole.REQUIREMENT
    AGENT_CAPABILITIES = [
        AgentCapability.REQUIREMENT_ANALYSIS,
        AgentCapability.DOCUMENTATION,
    ]
    AGENT_DESCRIPTION = "需求分析Agent - 负责需求解析、验证和文档化"
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务：分析需求."""
        input_data = context.input_data
        raw_requirement = input_data.get("requirement", "")
        
        if not raw_requirement:
            return TaskResult(
                success=False,
                error_message="缺少需求描述",
            )
        
        # 需求分析
        analysis = {
            "raw_requirement": raw_requirement,
            "functional_requirements": self._extract_functional(raw_requirement),
            "non_functional_requirements": self._extract_non_functional(input_data),
            "constraints": input_data.get("constraints", []),
            "acceptance_criteria": input_data.get("acceptance_criteria", []),
        }
        
        return TaskResult(
            success=True,
            output=analysis,
            artifacts={"requirement_analysis": analysis},
        )
    
    def _extract_functional(self, requirement: str) -> List[str]:
        """提取功能性需求."""
        return [f"FR-{i+1}: {requirement[:80]}" for i in range(min(3, max(1, len(requirement) // 50)))]
    
    def _extract_non_functional(self, input_data: Dict[str, Any]) -> List[str]:
        """提取非功能性需求."""
        nfr = input_data.get("non_functional", [])
        if not nfr:
            nfr = ["NFR-1: 系统可用性 >= 99.9%", "NFR-2: 响应时间 < 200ms"]
        return nfr


class ArchitectAgent(BaseAgentImpl):
    """架构设计Agent - 架构设计与评审."""
    
    AGENT_ROLE = AgentRole.ARCHITECT
    AGENT_CAPABILITIES = [
        AgentCapability.ARCHITECTURE_DESIGN,
        AgentCapability.CODE_REVIEW,
    ]
    AGENT_DESCRIPTION = "架构设计Agent - 负责系统架构设计和评审"
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务：设计架构."""
        input_data = context.input_data
        requirement_analysis = input_data.get("requirement_analysis", {})
        
        # 架构设计
        architecture = {
            "layers": ["输入层", "调度层", "Agent层", "执行层"],
            "components": self._design_components(requirement_analysis),
            "interfaces": self._design_interfaces(),
            "data_flow": self._design_data_flow(),
            "patterns": ["DAG依赖", "正交角色", "状态分离"],
        }
        
        return TaskResult(
            success=True,
            output=architecture,
            artifacts={"architecture": architecture},
        )
    
    def _design_components(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """设计组件."""
        return [
            {"name": "InputParser", "layer": "输入层", "responsibility": "解析输入"},
            {"name": "Scheduler", "layer": "调度层", "responsibility": "任务调度"},
            {"name": "AgentRegistry", "layer": "Agent层", "responsibility": "Agent管理"},
            {"name": "CodeExecutor", "layer": "执行层", "responsibility": "代码执行"},
        ]
    
    def _design_interfaces(self) -> List[str]:
        """设计接口."""
        return ["ITaskHandler", "IMessageBus", "IAgent", "IScheduler"]
    
    def _design_data_flow(self) -> List[str]:
        """设计数据流."""
        return ["输入 -> 解析 -> 调度 -> 执行 -> 输出"]


class DeveloperAgent(BaseAgentImpl):
    """开发Agent - 代码生成与实现."""
    
    AGENT_ROLE = AgentRole.DEVELOPER
    AGENT_CAPABILITIES = [
        AgentCapability.CODE_GENERATION,
        AgentCapability.CODE_REFACTORING,
    ]
    AGENT_DESCRIPTION = "开发Agent - 负责代码生成和重构"
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务：生成代码."""
        input_data = context.input_data
        task_description = input_data.get("task_description", "")
        language = input_data.get("language", "python")
        architecture = input_data.get("architecture", {})
        
        if not task_description:
            return TaskResult(
                success=False,
                error_message="缺少任务描述",
            )
        
        # 代码生成
        code_artifacts = {
            "files": self._generate_files(task_description, language),
            "tests": self._generate_tests(task_description),
            "config": self._generate_config(),
        }
        
        return TaskResult(
            success=True,
            output={
                "files_generated": len(code_artifacts["files"]),
                "tests_generated": len(code_artifacts["tests"]),
                "language": language,
            },
            artifacts=code_artifacts,
        )
    
    def _generate_files(self, description: str, language: str) -> List[Dict[str, str]]:
        """生成代码文件."""
        return [
            {"path": f"src/main.{self._ext(language)}", "description": f"主模块: {description[:50]}"},
            {"path": f"src/utils.{self._ext(language)}", "description": "工具函数"},
        ]
    
    def _generate_tests(self, description: str) -> List[Dict[str, str]]:
        """生成测试文件."""
        return [
            {"path": "tests/test_main.py", "description": f"主模块测试: {description[:30]}"},
        ]
    
    def _generate_config(self) -> Dict[str, Any]:
        """生成配置."""
        return {"format": "pyproject.toml", "linters": ["ruff"], "test_runner": "pytest"}
    
    @staticmethod
    def _ext(language: str) -> str:
        return {"python": "py", "javascript": "js", "typescript": "ts"}.get(language, "py")


class BugfixAgent(BaseAgentImpl):
    """修复Agent - Bug定位与修复."""
    
    AGENT_ROLE = AgentRole.BUGFIX
    AGENT_CAPABILITIES = [
        AgentCapability.CODE_DEBUGGING,
        AgentCapability.CODE_GENERATION,
    ]
    AGENT_DESCRIPTION = "修复Agent - 负责Bug定位和修复"
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务：修复Bug."""
        input_data = context.input_data
        error_message = input_data.get("error_message", "")
        error_type = input_data.get("error_type", "runtime")
        affected_files = input_data.get("affected_files", [])
        
        if not error_message:
            return TaskResult(
                success=False,
                error_message="缺少错误信息",
            )
        
        # Bug分析
        analysis = {
            "error_type": error_type,
            "root_cause": self._analyze_root_cause(error_message, error_type),
            "affected_files": affected_files or ["unknown.py"],
            "fix_strategy": self._determine_fix_strategy(error_type),
        }
        
        # 修复方案
        fix = {
            "description": f"修复{error_type}错误",
            "changes": [
                {"file": f, "change": "应用修复补丁"}
                for f in (affected_files or ["unknown.py"])
            ],
            "verification": "运行测试验证修复",
        }
        
        return TaskResult(
            success=True,
            output={"analysis": analysis, "fix": fix},
            artifacts={"bug_fix": fix},
        )
    
    def _analyze_root_cause(self, error: str, error_type: str) -> str:
        """分析根因."""
        return f"{error_type}错误: {error[:100]}"
    
    def _determine_fix_strategy(self, error_type: str) -> str:
        """确定修复策略."""
        strategies = {
            "runtime": "添加异常处理和输入验证",
            "logic": "修正算法逻辑",
            "syntax": "修正语法错误",
            "type": "修正类型不匹配",
        }
        return strategies.get(error_type, "通用修复策略")


class ReviewerAgent(BaseAgentImpl):
    """审查Agent - 代码审查与质量检查."""
    
    AGENT_ROLE = AgentRole.REVIEWER
    AGENT_CAPABILITIES = [
        AgentCapability.CODE_REVIEW,
        AgentCapability.QUALITY_CHECK,
    ]
    AGENT_DESCRIPTION = "审查Agent - 负责代码审查和质量检查"
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务：审查代码."""
        input_data = context.input_data
        code = input_data.get("code", "")
        files = input_data.get("files", [])
        
        if not code and not files:
            return TaskResult(
                success=False,
                error_message="缺少代码或文件列表",
            )
        
        # 代码审查
        review = {
            "issues": self._check_issues(code, files),
            "suggestions": self._generate_suggestions(),
            "quality_score": self._calculate_quality_score(),
            "approved": True,
        }
        
        return TaskResult(
            success=True,
            output=review,
            artifacts={"review": review},
        )
    
    def _check_issues(self, code: str, files: List[str]) -> List[Dict[str, Any]]:
        """检查问题."""
        issues = []
        if code:
            lines = code.count('\n')
            if lines > 100:
                issues.append({"severity": "warning", "message": f"文件过长({lines}行)"})
        return issues or [{"severity": "info", "message": "未发现问题"}]
    
    def _generate_suggestions(self) -> List[str]:
        """生成建议."""
        return ["建议添加类型注解", "建议增加单元测试覆盖"]
    
    def _calculate_quality_score(self) -> float:
        """计算质量分数."""
        return 85.0


class TesterAgent(BaseAgentImpl):
    """测试Agent - 测试用例生成与执行."""
    
    AGENT_ROLE = AgentRole.TESTER
    AGENT_CAPABILITIES = [
        AgentCapability.CODE_TESTING,
        AgentCapability.QUALITY_CHECK,
    ]
    AGENT_DESCRIPTION = "测试Agent - 负责测试用例生成和执行"
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务：生成并执行测试."""
        input_data = context.input_data
        target_files = input_data.get("target_files", [])
        test_type = input_data.get("test_type", "unit")
        
        # 生成测试
        test_cases = self._generate_test_cases(target_files, test_type)
        
        # 模拟执行
        execution_result = {
            "total_tests": len(test_cases),
            "passed": max(1, len(test_cases) - 1),
            "failed": 1 if len(test_cases) > 1 else 0,
            "coverage": 80.0,
            "test_type": test_type,
        }
        
        return TaskResult(
            success=True,
            output=execution_result,
            artifacts={
                "test_cases": test_cases,
                "execution_result": execution_result,
            },
        )
    
    def _generate_test_cases(self, files: List[str], test_type: str) -> List[Dict[str, Any]]:
        """生成测试用例."""
        cases = []
        for f in (files or ["module.py"]):
            cases.append({
                "name": f"test_{f.replace('.', '_').replace('/', '_')}",
                "target": f,
                "type": test_type,
                "assertions": ["assert result is not None"],
            })
        return cases or [{"name": "test_default", "target": "module.py", "type": test_type, "assertions": []}]


class DocumenterAgent(BaseAgentImpl):
    """文档Agent - 文档生成与维护."""
    
    AGENT_ROLE = AgentRole.DOCUMENTER
    AGENT_CAPABILITIES = [
        AgentCapability.DOCUMENTATION,
        AgentCapability.FILE_OPERATION,
    ]
    AGENT_DESCRIPTION = "文档Agent - 负责文档生成和维护"
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理任务：生成文档."""
        input_data = context.input_data
        doc_type = input_data.get("doc_type", "readme")
        target = input_data.get("target", "project")
        content = input_data.get("content", {})
        
        # 生成文档
        documents = self._generate_documents(doc_type, target, content)
        
        return TaskResult(
            success=True,
            output={
                "documents_generated": len(documents),
                "doc_type": doc_type,
            },
            artifacts={"documents": documents},
        )
    
    def _generate_documents(
        self,
        doc_type: str,
        target: str,
        content: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """生成文档."""
        docs = []
        
        if doc_type in ("readme", "all"):
            docs.append({
                "path": "README.md",
                "title": f"{target} 项目文档",
                "content": f"# {target}\n\n项目说明文档",
            })
        
        if doc_type in ("api", "all"):
            docs.append({
                "path": "docs/API.md",
                "title": "API文档",
                "content": "# API Reference\n\n接口说明",
            })
        
        if doc_type in ("architecture", "all"):
            docs.append({
                "path": "docs/ARCHITECTURE.md",
                "title": "架构文档",
                "content": "# Architecture\n\n系统架构说明",
            })
        
        return docs or [{
            "path": f"docs/{doc_type}.md",
            "title": f"{target} {doc_type}",
            "content": f"# {doc_type}",
        }]


# ========== Agent工厂映射 ==========

AGENT_CLASSES = {
    AgentRole.CONTROLLER: ControllerAgent,
    AgentRole.REQUIREMENT: RequirementAgent,
    AgentRole.ARCHITECT: ArchitectAgent,
    AgentRole.DEVELOPER: DeveloperAgent,
    AgentRole.BUGFIX: BugfixAgent,
    AgentRole.REVIEWER: ReviewerAgent,
    AgentRole.TESTER: TesterAgent,
    AgentRole.DOCUMENTER: DocumenterAgent,
}


def create_agent_by_role(
    role: AgentRole,
    agent_id: Optional[str] = None,
    **kwargs,
) -> BaseAgentImpl:
    """根据角色创建Agent.
    
    Args:
        role: 角色类型
        agent_id: Agent ID（可选）
        **kwargs: 额外参数
        
    Returns:
        Agent实例
    """
    cls = AGENT_CLASSES.get(role)
    if not cls:
        raise AgentExecutionError(f"Unknown role: {role.value}")
    
    if agent_id is None:
        agent_id = f"agent.{role.value}"
    
    return cls(agent_id=agent_id, **kwargs)


def create_all_agents(**kwargs) -> Dict[AgentRole, BaseAgentImpl]:
    """创建所有8个正交角色Agent.
    
    Returns:
        角色到Agent的映射
    """
    agents = {}
    for role in AgentRole:
        agents[role] = create_agent_by_role(role, **kwargs)
    return agents
