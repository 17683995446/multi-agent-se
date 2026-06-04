"""Requirement Agent - 第32阶段.

需求Agent - 负责需求分析、澄清和规范化.

职责:
- 接收原始需求描述
- 分析需求类型（功能/非功能/技术约束）
- 提取关键需求点
- 识别需求间的依赖和冲突
- 生成规范化的需求文档
- 评估需求可行性和风险
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid
import re

from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
from multi_agent_se.agents.runtime.base_agent import BaseAgentImpl, AgentContext, TaskResult


class RequirementType(Enum):
    """需求类型."""
    FUNCTIONAL = "functional"           # 功能需求
    NON_FUNCTIONAL = "non_functional"   # 非功能需求（性能、安全等）
    TECHNICAL = "technical"             # 技术约束
    BUSINESS = "business"               # 业务规则
    USER_STORY = "user_story"           # 用户故事
    EPIC = "epic"                       # 史诗


class RequirementPriority(Enum):
    """需求优先级."""
    MUST_HAVE = "must_have"             # 必须有
    SHOULD_HAVE = "should_have"         # 应该有
    COULD_HAVE = "could_have"           # 可以有
    WONT_HAVE = "wont_have"             # 暂不需要


class RequirementStatus(Enum):
    """需求状态."""
    DRAFT = "draft"                     # 草稿
    ANALYZED = "analyzed"               # 已分析
    APPROVED = "approved"               # 已批准
    REJECTED = "rejected"               # 已拒绝
    IMPLEMENTED = "implemented"         # 已实现


@dataclass
class RequirementItem:
    """需求项."""
    req_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    req_type: RequirementType = RequirementType.FUNCTIONAL
    priority: RequirementPriority = RequirementPriority.SHOULD_HAVE
    status: RequirementStatus = RequirementStatus.DRAFT
    
    # 元数据
    acceptance_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # 依赖的其他需求ID
    conflicts_with: List[str] = field(default_factory=list)  # 冲突的需求ID
    
    # 分析结果
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)  # 提取的实体（名词）
    actions: List[str] = field(default_factory=list)   # 提取的动作（动词）
    
    # 评估
    complexity: str = "medium"          # low/medium/high
    risk_level: str = "low"             # low/medium/high
    estimated_effort: str = ""          # 估算工作量
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "req_id": self.req_id,
            "title": self.title,
            "description": self.description[:100] if self.description else "",
            "type": self.req_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "acceptance_criteria": self.acceptance_criteria,
            "complexity": self.complexity,
            "risk_level": self.risk_level,
        }


@dataclass
class RequirementAnalysis:
    """需求分析结果."""
    original_input: str = ""
    requirements: List[RequirementItem] = field(default_factory=list)
    
    # 分析摘要
    total_count: int = 0
    functional_count: int = 0
    non_functional_count: int = 0
    
    # 质量评估
    clarity_score: float = 0.0          # 清晰度评分 (0-1)
    completeness_score: float = 0.0     # 完整性评分 (0-1)
    consistency_score: float = 0.0      # 一致性评分 (0-1)
    
    # 建议
    suggestions: List[str] = field(default_factory=list)
    missing_info: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    def get_by_type(self, req_type: RequirementType) -> List[RequirementItem]:
        """按类型获取需求."""
        return [r for r in self.requirements if r.req_type == req_type]
    
    def get_by_priority(self, priority: RequirementPriority) -> List[RequirementItem]:
        """按优先级获取需求."""
        return [r for r in self.requirements if r.priority == priority]
    
    def get_must_haves(self) -> List[RequirementItem]:
        """获取必须有需求."""
        return self.get_by_priority(RequirementPriority.MUST_HAVE)


class RequirementAgent(BaseAgentImpl):
    """需求Agent - 需求分析与规范化.
    
    8大正交角色Agent之一，负责将原始需求转化为结构化、可执行的需求规格。
    """
    
    AGENT_ROLE = AgentRole.REQUIREMENT
    AGENT_CAPABILITIES = [
        AgentCapability.REQUIREMENT_ANALYSIS,
    ]
    AGENT_DESCRIPTION = "需求Agent - 负责需求分析、澄清和规范化"
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None) -> None:
        super().__init__(agent_id, config)
        self._analysis_history: List[RequirementAnalysis] = []
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理需求分析任务.
        
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
        
        raw_requirement = input_data.get("requirement", "")
        
        if not raw_requirement:
            return TaskResult(
                success=False,
                error_message="缺少需求描述",
            )
        
        # 1. 需求解析
        analysis = self._analyze_requirement(raw_requirement)
        self._analysis_history.append(analysis)
        
        # 2. 质量评估
        self._evaluate_quality(analysis)
        
        # 3. 生成建议
        self._generate_suggestions(analysis)
        
        # 4. 构建输出
        output = {
            "original": raw_requirement[:200],
            "analysis": {
                "total_requirements": analysis.total_count,
                "functional": analysis.functional_count,
                "non_functional": analysis.non_functional_count,
                "quality_scores": {
                    "clarity": round(analysis.clarity_score, 2),
                    "completeness": round(analysis.completeness_score, 2),
                    "consistency": round(analysis.consistency_score, 2),
                },
            },
            "requirements": [r.to_dict() for r in analysis.requirements],
            "must_haves": [r.to_dict() for r in analysis.get_must_haves()],
            "suggestions": analysis.suggestions,
            "missing_info": analysis.missing_info,
            "risks": analysis.risks,
        }
        
        return TaskResult(
            success=True,
            output=output,
            artifacts={
                "analysis": analysis,
            },
        )
    
    def _analyze_requirement(self, raw_input: str) -> RequirementAnalysis:
        """分析原始需求.
        
        Args:
            raw_input: 原始需求文本
            
        Returns:
            需求分析结果
        """
        analysis = RequirementAnalysis(original_input=raw_input)
        
        # 1. 提取功能需求
        functional_reqs = self._extract_functional_requirements(raw_input)
        analysis.requirements.extend(functional_reqs)
        
        # 2. 提取非功能需求
        non_func_reqs = self._extract_non_functional_requirements(raw_input)
        analysis.requirements.extend(non_func_reqs)
        
        # 3. 提取用户故事
        user_stories = self._extract_user_stories(raw_input)
        analysis.requirements.extend(user_stories)
        
        # 4. 更新统计
        analysis.total_count = len(analysis.requirements)
        analysis.functional_count = len(analysis.get_by_type(RequirementType.FUNCTIONAL))
        analysis.non_functional_count = len(analysis.get_by_type(RequirementType.NON_FUNCTIONAL))
        
        # 5. 分析依赖关系
        self._analyze_dependencies(analysis)
        
        return analysis
    
    def _extract_functional_requirements(self, text: str) -> List[RequirementItem]:
        """提取功能需求.
        
        识别文本中的功能描述，如：
        - "系统应该..."
        - "用户可以..."
        - "支持...功能"
        """
        requirements = []
        
        # 按句子分割
        sentences = re.split(r'[。；\n]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 功能需求模式匹配
            patterns = [
                r'(系统|用户|管理员).*?(应该|需要|可以|必须|能够)(.*)',
                r'支持(.*)(功能|操作)',
                r'实现(.*)',
                r'提供(.*)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, sentence)
                if match:
                    req = RequirementItem(
                        title=sentence[:50] + "..." if len(sentence) > 50 else sentence,
                        description=sentence,
                        req_type=RequirementType.FUNCTIONAL,
                    )
                    
                    # 提取关键词
                    req.keywords = self._extract_keywords(sentence)
                    req.entities = self._extract_entities(sentence)
                    req.actions = self._extract_actions(sentence)
                    
                    # 判断优先级
                    if any(kw in sentence for kw in ["必须", "一定", "关键", "核心"]):
                        req.priority = RequirementPriority.MUST_HAVE
                    elif any(kw in sentence for kw in ["可以", "可选", "最好"]):
                        req.priority = RequirementPriority.COULD_HAVE
                    
                    # 生成验收标准
                    req.acceptance_criteria = self._generate_acceptance_criteria(req)
                    
                    requirements.append(req)
                    break
        
        return requirements
    
    def _extract_non_functional_requirements(self, text: str) -> List[RequirementItem]:
        """提取非功能需求.
        
        识别性能、安全、可用性等非功能需求。
        """
        requirements = []
        
        # 非功能需求关键词
        nfr_patterns = {
            "performance": ["性能", "响应时间", "吞吐量", "并发", "速度", "快"],
            "security": ["安全", "加密", "认证", "授权", "权限", "保护"],
            "availability": ["可用性", "稳定性", "可靠性", "容错", "备份"],
            "usability": ["易用性", "用户体验", "界面", "友好", "简单"],
            "scalability": ["可扩展", "扩展性", "伸缩", "扩容"],
            "maintainability": ["可维护", "维护性", "代码质量", "文档"],
        }
        
        sentences = re.split(r'[。；\n]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            for category, keywords in nfr_patterns.items():
                if any(kw in sentence for kw in keywords):
                    req = RequirementItem(
                        title=f"[{category.upper()}] {sentence[:40]}...",
                        description=sentence,
                        req_type=RequirementType.NON_FUNCTIONAL,
                        priority=RequirementPriority.SHOULD_HAVE,
                    )
                    
                    # 根据类别设置复杂度
                    complexity_map = {
                        "performance": "high",
                        "security": "high",
                        "scalability": "medium",
                    }
                    req.complexity = complexity_map.get(category, "medium")
                    
                    requirements.append(req)
                    break
        
        return requirements
    
    def _extract_user_stories(self, text: str) -> List[RequirementItem]:
        """提取用户故事.
        
        识别 "作为...我想要...以便..." 格式的用户故事。
        """
        requirements = []
        
        # 用户故事模式
        pattern = r'作为[一个]*(.+?)[，,]?我[想要|希望|需要](.+?)[，,]?(?:以便|从而|为了)(.+)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            role = match.group(1).strip()
            action = match.group(2).strip()
            benefit = match.group(3).strip()
            
            req = RequirementItem(
                title=f"作为{role}，{action}",
                description=f"作为{role}，我想要{action}，以便{benefit}",
                req_type=RequirementType.USER_STORY,
                priority=RequirementPriority.SHOULD_HAVE,
            )
            
            req.acceptance_criteria = [
                f"{role}能够{action}",
                f"实现{benefit}",
            ]
            
            requirements.append(req)
        
        return requirements
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词."""
        # 简单的关键词提取：名词和动词
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z_]+', text)
        # 过滤常见停用词
        stopwords = {"一个", "这个", "那个", "需要", "应该", "可以", "进行", "完成"}
        return list(set(w for w in words if w not in stopwords and len(w) >= 2))[:10]
    
    def _extract_entities(self, text: str) -> List[str]:
        """提取实体（名词）."""
        # 识别大写名词或特定模式
        entities = re.findall(r'[\u4e00-\u9fa5]{2,}(?:系统|模块|功能|数据|用户|角色)', text)
        return list(set(entities))[:5]
    
    def _extract_actions(self, text: str) -> List[str]:
        """提取动作（动词）."""
        action_patterns = ["创建", "读取", "更新", "删除", "查询", "导入", "导出", 
                          "验证", "发送", "接收", "处理", "管理"]
        actions = [a for a in action_patterns if a in text]
        return actions
    
    def _generate_acceptance_criteria(self, req: RequirementItem) -> List[str]:
        """生成验收标准."""
        criteria = []
        
        # 基于动作生成标准
        for action in req.actions:
            criteria.append(f"能够成功{action}")
        
        # 基于实体生成标准
        for entity in req.entities:
            criteria.append(f"{entity}状态正确更新")
        
        # 默认标准
        if not criteria:
            criteria.append("功能按描述正确实现")
            criteria.append("通过相关测试用例")
        
        return criteria[:3]
    
    def _analyze_dependencies(self, analysis: RequirementAnalysis) -> None:
        """分析需求间的依赖关系."""
        reqs = analysis.requirements
        
        for i, req in enumerate(reqs):
            # 检查与其他需求的依赖
            for other in reqs[i+1:]:
                # 共享实体可能表示依赖
                shared_entities = set(req.entities) & set(other.entities)
                if shared_entities and req.req_id != other.req_id:
                    # 简单的依赖推断：如果一个是基础功能，另一个是高级功能
                    if req.priority == RequirementPriority.MUST_HAVE and \
                       other.priority == RequirementPriority.SHOULD_HAVE:
                        other.dependencies.append(req.req_id)
    
    def _evaluate_quality(self, analysis: RequirementAnalysis) -> None:
        """评估需求质量."""
        text = analysis.original_input
        
        # 清晰度评分
        clarity_factors = {
            "has_specific_numbers": bool(re.search(r'\d+', text)),  # 有具体数字
            "has_clear_subjects": len(analysis.requirements) > 0,  # 有明确主体
            "reasonable_length": 20 < len(text) < 2000,  # 合理长度
        }
        analysis.clarity_score = sum(clarity_factors.values()) / len(clarity_factors)
        
        # 完整性评分
        completeness_factors = {
            "has_functional": analysis.functional_count > 0,
            "has_acceptance_criteria": all(r.acceptance_criteria for r in analysis.requirements),
            "has_priorities": len(analysis.get_must_haves()) > 0,
        }
        analysis.completeness_score = sum(completeness_factors.values()) / len(completeness_factors)
        
        # 一致性评分
        consistency_factors = {
            "no_direct_conflicts": len([r for r in analysis.requirements if r.conflicts_with]) == 0,
            "reasonable_count": analysis.total_count <= 20,  # 需求数量合理
        }
        analysis.consistency_score = sum(consistency_factors.values()) / len(consistency_factors)
    
    def _generate_suggestions(self, analysis: RequirementAnalysis) -> None:
        """生成改进建议."""
        # 清晰度建议
        if analysis.clarity_score < 0.5:
            analysis.suggestions.append("需求描述不够清晰，建议添加更多具体细节")
        
        if not re.search(r'\d+', analysis.original_input):
            analysis.suggestions.append("建议添加量化指标（如响应时间、并发数等）")
        
        # 完整性建议
        if analysis.functional_count == 0:
            analysis.suggestions.append("未识别到功能需求，请明确系统需要实现的功能")
        
        if analysis.non_functional_count == 0:
            analysis.suggestions.append("建议补充非功能需求（性能、安全、可用性等）")
        
        if not any(r.acceptance_criteria for r in analysis.requirements):
            analysis.suggestions.append("建议为每个需求添加验收标准")
        
        # 优先级建议
        if len(analysis.get_must_haves()) == 0:
            analysis.suggestions.append("建议标记必须有（Must Have）的核心需求")
        
        if len(analysis.get_must_haves()) > analysis.total_count * 0.7:
            analysis.suggestions.append("必须有需求过多，建议重新评估优先级")
        
        # 缺失信息
        if "用户" not in analysis.original_input:
            analysis.missing_info.append("目标用户群体")
        
        if "时间" not in analysis.original_input and "日期" not in analysis.original_input:
            analysis.missing_info.append("时间约束或里程碑")
        
        # 风险识别
        high_complexity = [r for r in analysis.requirements if r.complexity == "high"]
        if len(high_complexity) > 3:
            analysis.risks.append(f"存在{len(high_complexity)}个高复杂度需求，可能影响进度")
        
        if analysis.total_count > 20:
            analysis.risks.append("需求数量较多，建议分阶段实现")
    
    def get_analysis_history(self) -> List[RequirementAnalysis]:
        """获取分析历史."""
        return self._analysis_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        total_analyses = len(self._analysis_history)
        total_requirements = sum(a.total_count for a in self._analysis_history)
        
        return {
            "total_analyses": total_analyses,
            "total_requirements_extracted": total_requirements,
            "avg_requirements_per_analysis": (
                total_requirements / total_analyses if total_analyses > 0 else 0
            ),
        }
