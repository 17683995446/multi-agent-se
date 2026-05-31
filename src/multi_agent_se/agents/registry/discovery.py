"""Agent动态发现机制 - 阶段16.

实现Agent的动态发现与加载：
- 模块扫描
- 自动注册
- 配置驱动发现
"""

import importlib
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union

from multi_agent_se.agents.registry.metadata import (
    AgentRole,
    AgentStatus,
    AgentCapability,
    AgentMetadata,
    AgentCapabilityDeclaration,
)
from multi_agent_se.agents.registry.agent_registry import (
    AgentRegistry,
    get_registry,
    AgentRegistryError,
)


@dataclass
class DiscoveryResult:
    """发现结果."""
    discovered: List[str] = field(default_factory=list)  # 发现的Agent ID
    registered: List[str] = field(default_factory=list)  # 成功注册的Agent ID
    failed: List[Dict[str, Any]] = field(default_factory=list)  # 失败信息
    skipped: List[str] = field(default_factory=list)  # 跳过的
    
    @property
    def total_discovered(self) -> int:
        return len(self.discovered)
    
    @property
    def total_registered(self) -> int:
        return len(self.registered)
    
    @property
    def total_failed(self) -> int:
        return len(self.failed)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "discovered": self.discovered,
            "registered": self.registered,
            "failed": self.failed,
            "skipped": self.skipped,
            "total_discovered": self.total_discovered,
            "total_registered": self.total_registered,
            "total_failed": self.total_failed,
        }


class AgentDiscovery:
    """Agent动态发现器.
    
    扫描指定路径，发现并注册Agent
    """
    
    # Agent类需要实现的接口方法
    REQUIRED_INTERFACE = {
        "execute",  # 执行方法
    }
    
    # 可选接口方法
    OPTIONAL_INTERFACE = {
        "initialize",
        "shutdown",
        "pause",
        "resume",
        "get_status",
    }
    
    def __init__(self, registry: Optional[AgentRegistry] = None) -> None:
        """初始化发现器.
        
        Args:
            registry: 注册表（默认使用全局注册表）
        """
        self._registry = registry or get_registry()
        self._discovered_modules: Set[str] = set()
    
    def discover_in_path(
        self,
        path: Union[str, Path],
        recursive: bool = True,
        auto_register: bool = True,
    ) -> DiscoveryResult:
        """在指定路径发现Agent.
        
        Args:
            path: 搜索路径
            recursive: 是否递归搜索
            auto_register: 是否自动注册
            
        Returns:
            DiscoveryResult
        """
        result = DiscoveryResult()
        search_path = Path(path)
        
        if not search_path.exists():
            return result
        
        # 获取所有Python文件
        if recursive:
            py_files = list(search_path.rglob("*.py"))
        else:
            py_files = list(search_path.glob("*.py"))
        
        # 排除__init__.py和__pycache__
        py_files = [
            f for f in py_files
            if f.name != "__init__.py" and "__pycache__" not in str(f)
        ]
        
        for py_file in py_files:
            try:
                module_result = self._discover_in_file(py_file, auto_register)
                result.discovered.extend(module_result.discovered)
                result.registered.extend(module_result.registered)
                result.failed.extend(module_result.failed)
                result.skipped.extend(module_result.skipped)
            except Exception as e:
                result.failed.append({
                    "file": str(py_file),
                    "error": str(e),
                })
        
        return result
    
    def _discover_in_file(
        self,
        file_path: Path,
        auto_register: bool,
    ) -> DiscoveryResult:
        """在单个文件中发现Agent."""
        result = DiscoveryResult()
        
        # 构建模块名
        # 从src目录开始计算相对路径
        try:
            # 尝试找到src目录
            parts = file_path.parts
            if "src" in parts:
                src_idx = parts.index("src")
                module_parts = parts[src_idx + 1:]
                # 移除.py后缀
                if module_parts[-1].endswith(".py"):
                    module_parts = list(module_parts[:-1]) + [module_parts[-1][:-3]]
                module_name = ".".join(module_parts)
            else:
                # 直接使用文件名
                module_name = file_path.stem
        except Exception:
            module_name = file_path.stem
        
        # 避免重复发现
        if module_name in self._discovered_modules:
            result.skipped.append(module_name)
            return result
        
        try:
            # 导入模块
            module = importlib.import_module(module_name)
            self._discovered_modules.add(module_name)
            
            # 查找Agent类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # 跳过导入的类
                if obj.__module__ != module_name:
                    continue
                
                # 检查是否是Agent类
                if self._is_agent_class(obj):
                    agent_id = f"{module_name}.{name}"
                    result.discovered.append(agent_id)
                    
                    if auto_register:
                        try:
                            metadata = self._create_metadata(obj, agent_id, name)
                            self._registry.register(
                                metadata=metadata,
                                agent_class=obj,
                            )
                            result.registered.append(agent_id)
                        except Exception as e:
                            result.failed.append({
                                "agent": agent_id,
                                "error": str(e),
                            })
        
        except ImportError as e:
            result.failed.append({
                "module": module_name,
                "error": f"ImportError: {e}",
            })
        
        return result
    
    def _is_agent_class(self, cls: Type) -> bool:
        """检查类是否是Agent类.
        
        判断标准：
        1. 类名以Agent结尾
        2. 或实现了execute方法
        3. 或有AGENT_ROLE属性
        """
        # 检查类名
        if cls.__name__.endswith("Agent"):
            return True
        
        # 检查方法
        if hasattr(cls, "execute") and callable(getattr(cls, "execute")):
            return True
        
        # 检查标记属性
        if hasattr(cls, "AGENT_ROLE"):
            return True
        
        return False
    
    def _create_metadata(
        self,
        cls: Type,
        agent_id: str,
        name: str,
    ) -> AgentMetadata:
        """从类创建元数据."""
        # 获取角色
        if hasattr(cls, "AGENT_ROLE"):
            role_value = getattr(cls, "AGENT_ROLE")
            if isinstance(role_value, str):
                role = AgentRole(role_value)
            else:
                role = role_value
        elif "controller" in name.lower():
            role = AgentRole.CONTROLLER
        elif "requirement" in name.lower():
            role = AgentRole.REQUIREMENT
        elif "architect" in name.lower():
            role = AgentRole.ARCHITECT
        elif "developer" in name.lower():
            role = AgentRole.DEVELOPER
        elif "bugfix" in name.lower():
            role = AgentRole.BUGFIX
        elif "reviewer" in name.lower():
            role = AgentRole.REVIEWER
        elif "tester" in name.lower():
            role = AgentRole.TESTER
        elif "documenter" in name.lower():
            role = AgentRole.DOCUMENTER
        else:
            role = AgentRole.CONTROLLER  # 默认
        
        # 获取能力
        capabilities = []
        if hasattr(cls, "AGENT_CAPABILITIES"):
            caps = getattr(cls, "AGENT_CAPABILITIES")
            if isinstance(caps, list):
                for cap in caps:
                    if isinstance(cap, str):
                        capabilities.append(AgentCapabilityDeclaration(
                            capability=AgentCapability(cap),
                        ))
                    elif isinstance(cap, AgentCapability):
                        capabilities.append(AgentCapabilityDeclaration(
                            capability=cap,
                        ))
        
        # 获取描述
        description = ""
        if cls.__doc__:
            description = cls.__doc__.strip().split("\n")[0]
        
        # 获取模块路径
        module_path = cls.__module__
        
        return AgentMetadata(
            agent_id=agent_id,
            name=name,
            role=role,
            description=description,
            capabilities=capabilities,
            module_path=module_path,
            class_name=cls.__name__,
        )
    
    def discover_builtin_agents(self) -> DiscoveryResult:
        """发现内置Agent（8个正交角色）."""
        result = DiscoveryResult()
        
        # 内置Agent定义
        builtin_agents = [
            {
                "agent_id": "builtin.controller",
                "name": "ControllerAgent",
                "role": AgentRole.CONTROLLER,
                "description": "控制器Agent - 任务分解与调度",
                "capabilities": [
                    AgentCapability.TASK_DECOMPOSITION,
                    AgentCapability.TASK_SCHEDULING,
                ],
            },
            {
                "agent_id": "builtin.requirement",
                "name": "RequirementAgent",
                "role": AgentRole.REQUIREMENT,
                "description": "需求分析Agent - 需求解析与验证",
                "capabilities": [
                    AgentCapability.REQUIREMENT_ANALYSIS,
                    AgentCapability.DOCUMENTATION,
                ],
            },
            {
                "agent_id": "builtin.architect",
                "name": "ArchitectAgent",
                "role": AgentRole.ARCHITECT,
                "description": "架构设计Agent - 架构设计与评审",
                "capabilities": [
                    AgentCapability.ARCHITECTURE_DESIGN,
                    AgentCapability.CODE_REVIEW,
                ],
            },
            {
                "agent_id": "builtin.developer",
                "name": "DeveloperAgent",
                "role": AgentRole.DEVELOPER,
                "description": "开发Agent - 代码生成与实现",
                "capabilities": [
                    AgentCapability.CODE_GENERATION,
                    AgentCapability.CODE_REFACTORING,
                ],
            },
            {
                "agent_id": "builtin.bugfix",
                "name": "BugfixAgent",
                "role": AgentRole.BUGFIX,
                "description": "修复Agent - Bug定位与修复",
                "capabilities": [
                    AgentCapability.CODE_DEBUGGING,
                    AgentCapability.CODE_GENERATION,
                ],
            },
            {
                "agent_id": "builtin.reviewer",
                "name": "ReviewerAgent",
                "role": AgentRole.REVIEWER,
                "description": "审查Agent - 代码审查与质量检查",
                "capabilities": [
                    AgentCapability.CODE_REVIEW,
                    AgentCapability.QUALITY_CHECK,
                ],
            },
            {
                "agent_id": "builtin.tester",
                "name": "TesterAgent",
                "role": AgentRole.TESTER,
                "description": "测试Agent - 测试用例生成与执行",
                "capabilities": [
                    AgentCapability.CODE_TESTING,
                    AgentCapability.QUALITY_CHECK,
                ],
            },
            {
                "agent_id": "builtin.documenter",
                "name": "DocumenterAgent",
                "role": AgentRole.DOCUMENTER,
                "description": "文档Agent - 文档生成与维护",
                "capabilities": [
                    AgentCapability.DOCUMENTATION,
                    AgentCapability.FILE_OPERATION,
                ],
            },
        ]
        
        for agent_def in builtin_agents:
            result.discovered.append(agent_def["agent_id"])
            
            try:
                capabilities = [
                    AgentCapabilityDeclaration(capability=cap)
                    for cap in agent_def["capabilities"]
                ]
                
                metadata = AgentMetadata(
                    agent_id=agent_def["agent_id"],
                    name=agent_def["name"],
                    role=agent_def["role"],
                    description=agent_def["description"],
                    capabilities=capabilities,
                )
                
                self._registry.register(metadata=metadata)
                result.registered.append(agent_def["agent_id"])
                
            except Exception as e:
                result.failed.append({
                    "agent": agent_def["agent_id"],
                    "error": str(e),
                })
        
        return result
    
    def clear_discovered(self) -> None:
        """清除已发现记录."""
        self._discovered_modules.clear()


def discover_agents(
    path: Optional[Union[str, Path]] = None,
    include_builtin: bool = True,
) -> DiscoveryResult:
    """便捷函数：发现并注册Agent.
    
    Args:
        path: 搜索路径（可选）
        include_builtin: 是否包含内置Agent
        
    Returns:
        DiscoveryResult
    """
    discovery = AgentDiscovery()
    result = DiscoveryResult()
    
    # 发现内置Agent
    if include_builtin:
        builtin_result = discovery.discover_builtin_agents()
        result.discovered.extend(builtin_result.discovered)
        result.registered.extend(builtin_result.registered)
        result.failed.extend(builtin_result.failed)
    
    # 在指定路径发现
    if path:
        path_result = discovery.discover_in_path(path)
        result.discovered.extend(path_result.discovered)
        result.registered.extend(path_result.registered)
        result.failed.extend(path_result.failed)
        result.skipped.extend(path_result.skipped)
    
    return result
