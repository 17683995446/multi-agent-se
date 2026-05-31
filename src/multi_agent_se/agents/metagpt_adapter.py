"""MetaGPT角色适配层 - 阶段5.

复用MetaGPT角色定义、Action体系、Team协作模型
遵循第一性原理：职责正交公理 + 开源复用原则

注意：MetaGPT的Role实例化需要真实LLM连接，
本适配层提供角色定义/配置/模板能力，实际LLM调用在后续阶段接入
"""

from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum

# MetaGPT核心类型（延迟导入，避免模块级初始化问题）
# from metagpt.roles import Role
# from metagpt.actions import Action
# from metagpt.schema import Message
# from metagpt.team import Team


class RoleProfile(Enum):
    """MetaGPT标准角色配置文件."""
    PRODUCT_MANAGER = "Product Manager"
    ARCHITECT = "Architect"
    PROJECT_MANAGER = "Project Manager"
    ENGINEER = "Engineer"
    QA_ENGINEER = "QA Engineer"
    DESIGNER = "UI Designer"
    DATA_SCIENTIST = "Data Scientist"
    RESEARCHER = "Researcher"


@dataclass
class RoleDefinition:
    """角色定义 - 复用MetaGPT角色模型.
    
    遵循职责正交公理：每个角色有唯一职责
    """
    name: str
    profile: str
    goal: str
    constraints: str = ""
    actions: List[str] = field(default_factory=list)
    watch_actions: List[str] = field(default_factory=list)
    config: Optional[Dict[str, Any]] = None
    meta_role: Optional[RoleProfile] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典."""
        return {
            "name": self.name,
            "profile": self.profile,
            "goal": self.goal,
            "constraints": self.constraints,
            "actions": self.actions,
            "watch_actions": self.watch_actions,
            "meta_role": self.meta_role.value if self.meta_role else None,
        }


@dataclass
class ActionDefinition:
    """Action定义 - 复用MetaGPT Action模型."""
    name: str
    description: str
    input_format: str = ""
    output_format: str = ""
    module: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "module": self.module,
        }


# ========== 8大正交角色定义（匹配系统设计）==========
ROLE_DEFINITIONS: Dict[str, RoleDefinition] = {
    "controller": RoleDefinition(
        name="Controller",
        profile="总控调度",
        goal="任务收口、优先级管控、全局协调、任务验收",
        constraints="不执行具体编码任务，只负责调度协调",
        actions=["dispatch_task", "check_status", "verify_result"],
        watch_actions=["all"],
    ),
    "requirement": RoleDefinition(
        name="RequirementAnalyst",
        profile="需求拆解",
        goal="需求转技术任务、层级拆分、影响范围分析",
        constraints="只做需求分析，不做架构设计",
        actions=["analyze_requirement", "decompose_task", "estimate_scope"],
        watch_actions=["controller"],
        meta_role=RoleProfile.PRODUCT_MANAGER,
    ),
    "architect": RoleDefinition(
        name="Architect",
        profile="架构设计",
        goal="模块边界划分、依赖梳理、重构方案制定",
        constraints="只做架构设计，不做编码实现",
        actions=["design_architecture", "analyze_dependency", "plan_refactor"],
        watch_actions=["requirement"],
        meta_role=RoleProfile.ARCHITECT,
    ),
    "developer": RoleDefinition(
        name="Developer",
        profile="开发编码",
        goal="原子化编码、代码重构、缺陷修改",
        constraints="只做编码实现，不做架构决策",
        actions=["write_code", "refactor_code", "fix_bug"],
        watch_actions=["architect"],
        meta_role=RoleProfile.ENGINEER,
    ),
    "bugfix": RoleDefinition(
        name="BugHunter",
        profile="缺陷排查",
        goal="报错根因定位、修复方案输出",
        constraints="只做问题定位，不做代码修改",
        actions=["analyze_error", "locate_bug", "suggest_fix"],
        watch_actions=["developer"],
        meta_role=RoleProfile.ENGINEER,
    ),
    "reviewer": RoleDefinition(
        name="CodeReviewer",
        profile="代码评审",
        goal="四级原子合规校验、性能安全规范检查",
        constraints="只做评审，不做修改",
        actions=["review_code", "check_compliance", "generate_report"],
        watch_actions=["developer"],
        meta_role=RoleProfile.QA_ENGINEER,
    ),
    "tester": RoleDefinition(
        name="Tester",
        profile="测试验证",
        goal="用例生成、回归测试、异常校验",
        constraints="只做测试，不做开发",
        actions=["generate_test", "run_test", "analyze_coverage"],
        watch_actions=["developer", "reviewer"],
        meta_role=RoleProfile.QA_ENGINEER,
    ),
    "documenter": RoleDefinition(
        name="Documenter",
        profile="文档归档",
        goal="资料同步、变更记录、成果归档",
        constraints="只做文档，不做开发或测试",
        actions=["generate_doc", "update_readme", "record_change"],
        watch_actions=["all"],
    ),
}

# ========== MetaGPT Action定义 ==========
ACTION_DEFINITIONS: Dict[str, ActionDefinition] = {
    "write_code": ActionDefinition(
        name="WriteCode",
        description="编写代码",
        input_format="需求描述/设计文档",
        output_format="代码文件",
        module="metagpt.actions.write_code",
    ),
    "write_test": ActionDefinition(
        name="WriteTest",
        description="编写测试",
        input_format="代码文件",
        output_format="测试文件",
        module="metagpt.actions.write_test",
    ),
    "run_code": ActionDefinition(
        name="RunCode",
        description="运行代码",
        input_format="代码文件",
        output_format="运行结果",
        module="metagpt.actions.run_code",
    ),
    "design_api": ActionDefinition(
        name="DesignAPI",
        description="设计API接口",
        input_format="需求描述",
        output_format="API设计文档",
        module="metagpt.actions.design_api",
    ),
    "write_doc": ActionDefinition(
        name="WriteDoc",
        description="编写文档",
        input_format="代码/需求",
        output_format="文档",
        module="metagpt.actions.write_doc",
    ),
    "requirement_analysis": ActionDefinition(
        name="WritePRD",
        description="需求分析",
        input_format="原始需求",
        output_format="PRD文档",
        module="metagpt.actions.write_prd",
    ),
}

# ========== 工程岗位流程模板 ==========
WORKFLOW_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "standard_pipeline": {
        "name": "标准工程流水线",
        "description": "需求→架构→开发→评审→测试→归档",
        "stages": [
            {"role": "requirement", "action": "requirement_analysis", "output": "PRD"},
            {"role": "architect", "action": "design_api", "output": "架构方案"},
            {"role": "developer", "action": "write_code", "output": "代码"},
            {"role": "reviewer", "action": "review_code", "output": "评审报告"},
            {"role": "tester", "action": "write_test", "output": "测试用例"},
            {"role": "tester", "action": "run_code", "output": "测试结果"},
            {"role": "documenter", "action": "write_doc", "output": "文档"},
        ],
    },
    "bug_fix_pipeline": {
        "name": "Bug修复流水线",
        "description": "定位→分析→修复→验证→归档",
        "stages": [
            {"role": "bugfix", "action": "analyze_error", "output": "根因分析"},
            {"role": "developer", "action": "write_code", "output": "修复代码"},
            {"role": "tester", "action": "write_test", "output": "回归测试"},
            {"role": "tester", "action": "run_code", "output": "测试结果"},
            {"role": "documenter", "action": "write_doc", "output": "修复记录"},
        ],
    },
    "refactor_pipeline": {
        "name": "重构流水线",
        "description": "分析→设计→重构→评审→测试→归档",
        "stages": [
            {"role": "architect", "action": "design_api", "output": "重构方案"},
            {"role": "developer", "action": "write_code", "output": "重构代码"},
            {"role": "reviewer", "action": "review_code", "output": "评审报告"},
            {"role": "tester", "action": "write_test", "output": "回归测试"},
            {"role": "tester", "action": "run_code", "output": "测试结果"},
            {"role": "documenter", "action": "write_doc", "output": "重构记录"},
        ],
    },
}


class MetaGPTAdapter:
    """MetaGPT适配器.
    
    复用MetaGPT角色定义与流程模板，提供统一接口
    """
    
    def __init__(self) -> None:
        self._roles: Dict[str, RoleDefinition] = dict(ROLE_DEFINITIONS)
        self._actions: Dict[str, ActionDefinition] = dict(ACTION_DEFINITIONS)
        self._workflows: Dict[str, Dict[str, Any]] = dict(WORKFLOW_TEMPLATES)
    
    def get_role(self, name: str) -> Optional[RoleDefinition]:
        """获取角色定义."""
        return self._roles.get(name)
    
    def get_all_roles(self) -> Dict[str, RoleDefinition]:
        """获取所有角色定义."""
        return dict(self._roles)
    
    def get_action(self, name: str) -> Optional[ActionDefinition]:
        """获取Action定义."""
        return self._actions.get(name)
    
    def get_all_actions(self) -> Dict[str, ActionDefinition]:
        """获取所有Action定义."""
        return dict(self._actions)
    
    def get_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        """获取流程模板."""
        return self._workflows.get(name)
    
    def get_all_workflows(self) -> Dict[str, Dict[str, Any]]:
        """获取所有流程模板."""
        return dict(self._workflows)
    
    def get_role_for_stage(self, workflow_name: str, stage_index: int) -> Optional[str]:
        """获取流程中指定阶段的角色."""
        workflow = self._workflows.get(workflow_name)
        if workflow and stage_index < len(workflow["stages"]):
            return workflow["stages"][stage_index]["role"]
        return None
    
    def register_role(self, name: str, definition: RoleDefinition) -> None:
        """注册自定义角色."""
        self._roles[name] = definition
    
    def register_workflow(self, name: str, workflow: Dict[str, Any]) -> None:
        """注册自定义流程."""
        self._workflows[name] = workflow
    
    def verify_orthogonality(self) -> Dict[str, Any]:
        """验证角色正交性（无重叠无空缺）.
        
        Returns:
            验证结果
        """
        roles = list(self._roles.values())
        goals = [r.goal for r in roles]
        actions = []
        for r in roles:
            actions.extend(r.actions)
        
        # 检查目标唯一性
        goal_duplicates = [g for g in goals if goals.count(g) > 1]
        
        # 检查Action覆盖
        unique_actions = set(actions)
        
        return {
            "total_roles": len(roles),
            "total_actions": len(unique_actions),
            "goal_duplicates": list(set(goal_duplicates)),
            "is_orthogonal": len(goal_duplicates) == 0,
            "roles": [r.name for r in roles],
        }


# 全局适配器实例
metagpt_adapter = MetaGPTAdapter()
