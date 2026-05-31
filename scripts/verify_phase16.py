#!/usr/bin/env python3
"""第16阶段验收脚本 - Agent注册中心.

验证内容：
1. Agent元数据管理 (metadata.py)
2. Agent注册表 (agent_registry.py)
3. 动态发现机制 (discovery.py)
4. 统一导出接口 (__init__.py)
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, "/workspace/multi_agent_se/src")


def print_header(title: str) -> None:
    """打印标题."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    """打印测试结果."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test_name}")
    if details:
        print(f"       {details}")


def main() -> int:
    """主函数."""
    print_header("第16阶段验收：Agent注册中心")
    
    passed = 0
    failed = 0
    
    # ========== 1. 测试Agent元数据管理 ==========
    print_header("1. Agent元数据管理 (metadata.py)")
    
    try:
        from multi_agent_se.agents.registry import (
            AgentRole,
            AgentStatus,
            AgentCapability,
            AgentCapabilityDeclaration,
            AgentMetadata,
            AgentRegistrationInfo,
        )
        print_result("导入元数据模块", True)
        passed += 1
    except Exception as e:
        print_result("导入元数据模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 AgentRole 枚举
    try:
        assert AgentRole.CONTROLLER.value == "controller"
        assert AgentRole.REQUIREMENT.value == "requirement"
        assert AgentRole.ARCHITECT.value == "architect"
        assert AgentRole.DEVELOPER.value == "developer"
        assert AgentRole.BUGFIX.value == "bugfix"
        assert AgentRole.REVIEWER.value == "reviewer"
        assert AgentRole.TESTER.value == "tester"
        assert AgentRole.DOCUMENTER.value == "documenter"
        assert len(AgentRole) == 8  # 8个正交角色
        print_result("AgentRole 枚举定义（8个正交角色）", True)
        passed += 1
    except Exception as e:
        print_result("AgentRole 枚举定义", False, str(e))
        failed += 1
    
    # 测试 AgentStatus 枚举
    try:
        assert AgentStatus.CREATED.value == "created"
        assert AgentStatus.READY.value == "ready"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.PAUSED.value == "paused"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.TERMINATED.value == "terminated"
        print_result("AgentStatus 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("AgentStatus 枚举定义", False, str(e))
        failed += 1
    
    # 测试 AgentCapability 枚举
    try:
        assert AgentCapability.CODE_GENERATION.value == "code_generation"
        assert AgentCapability.CODE_REVIEW.value == "code_review"
        assert AgentCapability.CODE_TESTING.value == "code_testing"
        assert AgentCapability.TASK_DECOMPOSITION.value == "task_decomposition"
        assert len(AgentCapability) >= 10  # 至少10种能力
        print_result("AgentCapability 枚举定义", True, f"共{len(AgentCapability)}种能力")
        passed += 1
    except Exception as e:
        print_result("AgentCapability 枚举定义", False, str(e))
        failed += 1
    
    # 测试 AgentCapabilityDeclaration
    try:
        cap_decl = AgentCapabilityDeclaration(
            capability=AgentCapability.CODE_GENERATION,
            proficiency=0.8,
            constraints={"max_lines": 100},
        )
        assert cap_decl.capability == AgentCapability.CODE_GENERATION
        assert cap_decl.proficiency == 0.8
        assert cap_decl.constraints["max_lines"] == 100
        assert "capability" in cap_decl.to_dict()
        print_result("AgentCapabilityDeclaration 数据类", True)
        passed += 1
    except Exception as e:
        print_result("AgentCapabilityDeclaration 数据类", False, str(e))
        failed += 1
    
    # 测试 AgentMetadata
    try:
        metadata = AgentMetadata(
            agent_id="test.agent",
            name="TestAgent",
            role=AgentRole.DEVELOPER,
            description="测试Agent",
            tags={"test", "demo"},
        )
        assert metadata.agent_id == "test.agent"
        assert metadata.role == AgentRole.DEVELOPER
        assert metadata.status == AgentStatus.CREATED
        assert "test" in metadata.tags
        assert metadata.success_rate == 0.0
        assert metadata.is_available == False  # CREATED状态不可用
        print_result("AgentMetadata 基本属性", True)
        passed += 1
    except Exception as e:
        print_result("AgentMetadata 基本属性", False, str(e))
        failed += 1
    
    # 测试 AgentMetadata 能力管理
    try:
        metadata.add_capability(AgentCapability.CODE_GENERATION, proficiency=0.9)
        metadata.add_capability(AgentCapability.CODE_REVIEW, proficiency=0.7)
        
        assert metadata.has_capability(AgentCapability.CODE_GENERATION)
        assert metadata.has_capability(AgentCapability.CODE_REVIEW)
        assert not metadata.has_capability(AgentCapability.CODE_TESTING)
        assert metadata.get_capability_proficiency(AgentCapability.CODE_GENERATION) == 0.9
        assert len(metadata.capability_types) == 2
        print_result("AgentMetadata 能力管理", True, f"添加了{len(metadata.capabilities)}个能力")
        passed += 1
    except Exception as e:
        print_result("AgentMetadata 能力管理", False, str(e))
        failed += 1
    
    # 测试 AgentMetadata 状态更新
    try:
        metadata.update_status(AgentStatus.READY)
        assert metadata.status == AgentStatus.READY
        assert metadata.is_available == True
        
        metadata.record_task(success=True)
        metadata.record_task(success=True)
        metadata.record_task(success=False)
        assert metadata.total_tasks == 3
        assert metadata.successful_tasks == 2
        assert metadata.failed_tasks == 1
        assert abs(metadata.success_rate - 2/3) < 0.001
        print_result("AgentMetadata 状态与统计", True, f"成功率={metadata.success_rate:.2%}")
        passed += 1
    except Exception as e:
        print_result("AgentMetadata 状态与统计", False, str(e))
        failed += 1
    
    # 测试 AgentMetadata 序列化
    try:
        data = metadata.to_dict()
        assert data["agent_id"] == "test.agent"
        assert data["role"] == "developer"
        assert data["status"] == "ready"
        
        # 反序列化
        restored = AgentMetadata.from_dict(data)
        assert restored.agent_id == metadata.agent_id
        assert restored.role == metadata.role
        assert restored.total_tasks == metadata.total_tasks
        print_result("AgentMetadata 序列化/反序列化", True)
        passed += 1
    except Exception as e:
        print_result("AgentMetadata 序列化/反序列化", False, str(e))
        failed += 1
    
    # 测试 AgentRegistrationInfo
    try:
        reg_info = AgentRegistrationInfo(
            metadata=metadata,
            agent_class=None,
            factory=None,
            instance=None,
        )
        assert reg_info.metadata.agent_id == "test.agent"
        assert reg_info.has_class == False
        assert "metadata" in reg_info.to_dict()
        print_result("AgentRegistrationInfo 数据类", True)
        passed += 1
    except Exception as e:
        print_result("AgentRegistrationInfo 数据类", False, str(e))
        failed += 1
    
    # ========== 2. 测试Agent注册表 ==========
    print_header("2. Agent注册表 (agent_registry.py)")
    
    try:
        from multi_agent_se.agents.registry import (
            AgentRegistry,
            AgentRegistryError,
            AgentNotFoundError,
            AgentAlreadyRegisteredError,
            RegistryStats,
            get_registry,
            reset_registry,
        )
        print_result("导入注册表模块", True)
        passed += 1
    except Exception as e:
        print_result("导入注册表模块", False, str(e))
        failed += 1
        return 1
    
    # 测试创建注册表
    try:
        registry = AgentRegistry()
        assert registry.total_agents == 0
        print_result("创建AgentRegistry实例", True)
        passed += 1
    except Exception as e:
        print_result("创建AgentRegistry实例", False, str(e))
        failed += 1
    
    # 测试注册Agent
    try:
        meta1 = AgentMetadata(
            agent_id="agent.controller",
            name="ControllerAgent",
            role=AgentRole.CONTROLLER,
        )
        meta1.add_capability(AgentCapability.TASK_DECOMPOSITION)
        meta1.update_status(AgentStatus.READY)
        
        agent_id = registry.register(metadata=meta1)
        assert agent_id == "agent.controller"
        assert registry.total_agents == 1
        assert registry.has_agent("agent.controller")
        print_result("注册Agent", True, f"ID={agent_id}")
        passed += 1
    except Exception as e:
        print_result("注册Agent", False, str(e))
        failed += 1
    
    # 测试重复注册
    try:
        try:
            registry.register(metadata=meta1)
            print_result("重复注册检测", False, "应该抛出异常")
            failed += 1
        except AgentAlreadyRegisteredError:
            print_result("重复注册检测", True, "正确抛出AgentAlreadyRegisteredError")
            passed += 1
    except Exception as e:
        print_result("重复注册检测", False, str(e))
        failed += 1
    
    # 测试注册多个Agent
    try:
        meta2 = AgentMetadata(
            agent_id="agent.developer",
            name="DeveloperAgent",
            role=AgentRole.DEVELOPER,
        )
        meta2.add_capability(AgentCapability.CODE_GENERATION, proficiency=0.9)
        meta2.add_capability(AgentCapability.CODE_REFACTORING, proficiency=0.7)
        meta2.update_status(AgentStatus.READY)
        
        meta3 = AgentMetadata(
            agent_id="agent.reviewer",
            name="ReviewerAgent",
            role=AgentRole.REVIEWER,
        )
        meta3.add_capability(AgentCapability.CODE_REVIEW, proficiency=0.85)
        meta3.update_status(AgentStatus.READY)
        
        registry.register(metadata=meta2)
        registry.register(metadata=meta3)
        
        assert registry.total_agents == 3
        print_result("注册多个Agent", True, f"共{registry.total_agents}个")
        passed += 1
    except Exception as e:
        print_result("注册多个Agent", False, str(e))
        failed += 1
    
    # 测试获取Agent
    try:
        info = registry.get("agent.controller")
        assert info.metadata.name == "ControllerAgent"
        
        meta = registry.get_metadata("agent.developer")
        assert meta.role == AgentRole.DEVELOPER
        
        print_result("获取Agent信息", True)
        passed += 1
    except Exception as e:
        print_result("获取Agent信息", False, str(e))
        failed += 1
    
    # 测试按角色查询
    try:
        controllers = registry.get_by_role(AgentRole.CONTROLLER)
        assert len(controllers) == 1
        assert controllers[0].metadata.agent_id == "agent.controller"
        
        developers = registry.get_by_role(AgentRole.DEVELOPER)
        assert len(developers) == 1
        
        print_result("按角色查询Agent", True, f"CONTROLLER={len(controllers)}, DEVELOPER={len(developers)}")
        passed += 1
    except Exception as e:
        print_result("按角色查询Agent", False, str(e))
        failed += 1
    
    # 测试按能力查询
    try:
        code_gen_agents = registry.get_by_capability(AgentCapability.CODE_GENERATION)
        assert len(code_gen_agents) == 1
        assert code_gen_agents[0].metadata.agent_id == "agent.developer"
        
        # 测试熟练度过滤
        high_proficiency = registry.get_by_capability(
            AgentCapability.CODE_GENERATION,
            min_proficiency=0.95,
        )
        assert len(high_proficiency) == 0  # 最高0.9
        
        print_result("按能力查询Agent", True, f"CODE_GENERATION={len(code_gen_agents)}")
        passed += 1
    except Exception as e:
        print_result("按能力查询Agent", False, str(e))
        failed += 1
    
    # 测试按状态查询
    try:
        ready_agents = registry.get_by_status(AgentStatus.READY)
        assert len(ready_agents) == 3
        
        available = registry.get_available()
        assert len(available) == 3
        
        print_result("按状态查询Agent", True, f"READY={len(ready_agents)}")
        passed += 1
    except Exception as e:
        print_result("按状态查询Agent", False, str(e))
        failed += 1
    
    # 测试查找最佳Agent
    try:
        best = registry.find_best_for_capability(AgentCapability.CODE_GENERATION)
        assert best is not None
        assert best.metadata.agent_id == "agent.developer"
        
        best_reviewer = registry.find_best_for_capability(AgentCapability.CODE_REVIEW)
        assert best_reviewer.metadata.agent_id == "agent.reviewer"
        
        print_result("查找最佳Agent", True, f"CODE_GENERATION最佳={best.metadata.agent_id}")
        passed += 1
    except Exception as e:
        print_result("查找最佳Agent", False, str(e))
        failed += 1
    
    # 测试更新状态
    try:
        registry.update_agent_status("agent.controller", AgentStatus.RUNNING)
        meta = registry.get_metadata("agent.controller")
        assert meta.status == AgentStatus.RUNNING
        
        print_result("更新Agent状态", True)
        passed += 1
    except Exception as e:
        print_result("更新Agent状态", False, str(e))
        failed += 1
    
    # 测试统计
    try:
        stats = registry.get_stats()
        assert stats.total_agents == 3
        assert stats.by_role["controller"] == 1
        assert stats.by_role["developer"] == 1
        assert stats.by_status["running"] == 1
        assert stats.by_status["ready"] == 2
        
        print_result("注册表统计", True, f"总数={stats.total_agents}")
        passed += 1
    except Exception as e:
        print_result("注册表统计", False, str(e))
        failed += 1
    
    # 测试注销
    try:
        result = registry.unregister("agent.controller")
        assert result == True
        assert registry.total_agents == 2
        assert not registry.has_agent("agent.controller")
        
        # 注销不存在的Agent
        result = registry.unregister("nonexistent")
        assert result == False
        
        print_result("注销Agent", True)
        passed += 1
    except Exception as e:
        print_result("注销Agent", False, str(e))
        failed += 1
    
    # 测试全局注册表
    try:
        reset_registry()
        global_registry = get_registry()
        assert global_registry.total_agents == 0
        
        # 再次获取应该是同一个实例
        same_registry = get_registry()
        assert same_registry is global_registry
        
        print_result("全局注册表", True)
        passed += 1
    except Exception as e:
        print_result("全局注册表", False, str(e))
        failed += 1
    
    # ========== 3. 测试动态发现机制 ==========
    print_header("3. 动态发现机制 (discovery.py)")
    
    try:
        from multi_agent_se.agents.registry import (
            DiscoveryResult,
            AgentDiscovery,
            discover_agents,
        )
        print_result("导入发现模块", True)
        passed += 1
    except Exception as e:
        print_result("导入发现模块", False, str(e))
        failed += 1
        return 1
    
    # 测试发现内置Agent
    try:
        reset_registry()
        discovery = AgentDiscovery()
        result = discovery.discover_builtin_agents()
        
        assert result.total_discovered == 8  # 8个正交角色
        assert result.total_registered == 8
        assert result.total_failed == 0
        
        registry = get_registry()
        assert registry.total_agents == 8
        
        print_result("发现内置Agent", True, f"发现{result.total_discovered}个，注册{result.total_registered}个")
        passed += 1
    except Exception as e:
        print_result("发现内置Agent", False, str(e))
        failed += 1
    
    # 测试验证内置Agent角色
    try:
        registry = get_registry()
        
        # 验证每个角色都有对应的Agent
        for role in AgentRole:
            agents = registry.get_by_role(role)
            assert len(agents) >= 1, f"角色{role.value}没有Agent"
        
        print_result("验证8个正交角色都有Agent", True)
        passed += 1
    except Exception as e:
        print_result("验证8个正交角色都有Agent", False, str(e))
        failed += 1
    
    # 测试能力覆盖
    try:
        registry = get_registry()
        
        # 验证关键能力都有Agent
        key_capabilities = [
            AgentCapability.CODE_GENERATION,
            AgentCapability.CODE_REVIEW,
            AgentCapability.CODE_TESTING,
            AgentCapability.TASK_DECOMPOSITION,
        ]
        
        for cap in key_capabilities:
            assert registry.has_capability(cap), f"能力{cap.value}没有Agent"
            agents = registry.get_by_capability(cap)
            assert len(agents) >= 1
        
        print_result("验证关键能力覆盖", True)
        passed += 1
    except Exception as e:
        print_result("验证关键能力覆盖", False, str(e))
        failed += 1
    
    # 测试DiscoveryResult
    try:
        result = DiscoveryResult(
            discovered=["a", "b"],
            registered=["a"],
            failed=[{"agent": "b", "error": "test"}],
            skipped=["c"],
        )
        assert result.total_discovered == 2
        assert result.total_registered == 1
        assert result.total_failed == 1
        assert "discovered" in result.to_dict()
        
        print_result("DiscoveryResult 数据类", True)
        passed += 1
    except Exception as e:
        print_result("DiscoveryResult 数据类", False, str(e))
        failed += 1
    
    # 测试便捷函数
    try:
        reset_registry()
        result = discover_agents(include_builtin=True)
        
        assert result.total_registered == 8
        
        print_result("discover_agents 便捷函数", True)
        passed += 1
    except Exception as e:
        print_result("discover_agents 便捷函数", False, str(e))
        failed += 1
    
    # ========== 4. 测试统一导出接口 ==========
    print_header("4. 统一导出接口 (__init__.py)")
    
    try:
        from multi_agent_se.agents.registry import __all__
        
        expected_exports = [
            # 元数据
            "AgentRole", "AgentStatus", "AgentCapability",
            "AgentCapabilityDeclaration", "AgentMetadata", "AgentRegistrationInfo",
            # 注册表
            "AgentRegistry", "AgentRegistryError", "AgentNotFoundError",
            "AgentAlreadyRegisteredError", "RegistryStats",
            "get_registry", "reset_registry",
            # 发现
            "DiscoveryResult", "AgentDiscovery", "discover_agents",
        ]
        
        for export in expected_exports:
            assert export in __all__, f"缺少导出: {export}"
        
        print_result("__all__ 导出列表完整", True, f"共{len(__all__)}个导出")
        passed += 1
    except Exception as e:
        print_result("__all__ 导出列表完整", False, str(e))
        failed += 1
    
    # ========== 验收总结 ==========
    print_header("验收总结")
    total = passed + failed
    print(f"  总测试数: {total}")
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")
    print(f"  通过率: {passed/total*100:.1f}%")
    
    if failed == 0:
        print("\n  🎉 第16阶段验收通过！")
        return 0
    else:
        print(f"\n  ⚠️ 第16阶段有 {failed} 项测试未通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
