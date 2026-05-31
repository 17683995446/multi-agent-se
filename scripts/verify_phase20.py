#!/usr/bin/env python3
"""第20阶段验收脚本 - Agent运行时集成.

验证内容：
1. BaseAgentImpl基础实现 (base_agent.py)
2. 8个正交角色Agent (role_agents.py)
3. AgentRuntime运行时核心 (runtime.py)
4. 统一导出接口 (__init__.py)
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, "/workspace/multi_agent_se/src")


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test_name}")
    if details:
        print(f"       {details}")


def main() -> int:
    print_header("第20阶段验收：Agent运行时集成")
    
    passed = 0
    failed = 0
    
    # ========== 1. 测试BaseAgentImpl ==========
    print_header("1. BaseAgentImpl基础实现 (base_agent.py)")
    
    try:
        from multi_agent_se.agents.runtime import (
            AgentExecutionError,
            AgentContext,
            BaseAgentImpl,
        )
        print_result("导入基础模块", True)
        passed += 1
    except Exception as e:
        print_result("导入基础模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 AgentContext
    try:
        ctx = AgentContext(
            input_data={"key": "value"},
            metadata={"source": "test"},
        )
        assert ctx.input_data == {"key": "value"}
        assert "input_data" in ctx.to_dict()
        print_result("AgentContext 数据类", True)
        passed += 1
    except Exception as e:
        print_result("AgentContext 数据类", False, str(e))
        failed += 1
    
    # 测试 BaseAgentImpl 子类化
    try:
        from multi_agent_se.agents.registry import AgentRole, AgentCapability, AgentStatus
        
        class TestAgent(BaseAgentImpl):
            AGENT_ROLE = AgentRole.DEVELOPER
            AGENT_CAPABILITIES = [AgentCapability.CODE_GENERATION]
            AGENT_DESCRIPTION = "测试Agent"
            
            def process(self, context):
                return TaskResult(success=True, output={"processed": True})
        
        from multi_agent_se.scheduler import TaskResult
        
        agent = TestAgent(agent_id="test.agent")
        assert agent.agent_id == "test.agent"
        assert agent.role == AgentRole.DEVELOPER
        assert agent.status == AgentStatus.CREATED
        assert agent.is_available == False
        
        print_result("BaseAgentImpl 子类化", True)
        passed += 1
    except Exception as e:
        print_result("BaseAgentImpl 子类化", False, str(e))
        failed += 1
    
    # 测试生命周期
    try:
        agent = TestAgent(agent_id="lifecycle.test")
        
        agent.initialize()
        assert agent.status == AgentStatus.READY
        assert agent.is_available == True
        
        agent.start()
        assert agent.status == AgentStatus.RUNNING
        
        agent.pause()
        assert agent.status == AgentStatus.PAUSED
        
        agent.resume()
        assert agent.status == AgentStatus.RUNNING
        
        agent.stop()
        assert agent.status == AgentStatus.TERMINATED
        
        print_result("Agent生命周期", True, "CREATED->READY->RUNNING->PAUSED->RUNNING->TERMINATED")
        passed += 1
    except Exception as e:
        print_result("Agent生命周期", False, str(e))
        failed += 1
    
    # 测试任务执行
    try:
        agent = TestAgent(agent_id="exec.test")
        agent.initialize()
        
        ctx = AgentContext(input_data={"test": True})
        result = agent.execute(ctx)
        
        assert result.success == True
        assert result.output == {"processed": True}
        assert agent._total_tasks == 1
        assert agent._successful_tasks == 1
        
        print_result("Agent任务执行", True)
        passed += 1
    except Exception as e:
        print_result("Agent任务执行", False, str(e))
        failed += 1
    
    # 测试消息处理
    try:
        from multi_agent_se.agents.communication import Message, MessageType, reset_message_bus
        from multi_agent_se.agents.registry import reset_registry, discover_agents
        
        reset_message_bus()
        reset_registry()
        discover_agents(include_builtin=True)
        
        agent = TestAgent(agent_id="msg.test")
        agent.initialize()
        
        # 发送任务分配消息
        msg = Message.create(
            sender_id="sender",
            receiver_id="msg.test",
            payload={"key": "value"},
            message_type=MessageType.TASK_ASSIGN,
        )
        
        response = agent.handle_message(msg)
        assert response is not None
        assert response.header.correlation_id == msg.message_id
        
        print_result("Agent消息处理", True)
        passed += 1
    except Exception as e:
        print_result("Agent消息处理", False, str(e))
        failed += 1
    
    # 测试获取元数据
    try:
        agent = TestAgent(agent_id="meta.test")
        agent.initialize()
        
        metadata = agent.get_metadata()
        assert metadata.agent_id == "meta.test"
        assert metadata.role == AgentRole.DEVELOPER
        assert len(metadata.capabilities) == 1
        
        stats = agent.get_stats()
        assert stats["agent_id"] == "meta.test"
        assert stats["role"] == "developer"
        
        print_result("Agent元数据与统计", True)
        passed += 1
    except Exception as e:
        print_result("Agent元数据与统计", False, str(e))
        failed += 1
    
    # ========== 2. 测试8个正交角色Agent ==========
    print_header("2. 8个正交角色Agent (role_agents.py)")
    
    try:
        from multi_agent_se.agents.runtime import (
            ControllerAgent,
            RequirementAgent,
            ArchitectAgent,
            DeveloperAgent,
            BugfixAgent,
            ReviewerAgent,
            TesterAgent,
            DocumenterAgent,
            AGENT_CLASSES,
            create_agent_by_role,
            create_all_agents,
        )
        print_result("导入角色Agent模块", True)
        passed += 1
    except Exception as e:
        print_result("导入角色Agent模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 AGENT_CLASSES 映射
    try:
        assert len(AGENT_CLASSES) == 8
        assert AgentRole.CONTROLLER in AGENT_CLASSES
        assert AgentRole.DEVELOPER in AGENT_CLASSES
        assert AgentRole.TESTER in AGENT_CLASSES
        
        print_result("AGENT_CLASSES 映射", True, f"共{len(AGENT_CLASSES)}个角色")
        passed += 1
    except Exception as e:
        print_result("AGENT_CLASSES 映射", False, str(e))
        failed += 1
    
    # 测试每个角色Agent的创建和执行
    role_tests = [
        (AgentRole.CONTROLLER, ControllerAgent, {"requirement": "实现用户登录功能"}),
        (AgentRole.REQUIREMENT, RequirementAgent, {"requirement": "用户需要能够注册和登录"}),
        (AgentRole.ARCHITECT, ArchitectAgent, {"requirement_analysis": {}}),
        (AgentRole.DEVELOPER, DeveloperAgent, {"task_description": "实现登录API", "language": "python"}),
        (AgentRole.BUGFIX, BugfixAgent, {"error_message": "NullPointerException", "error_type": "runtime"}),
        (AgentRole.REVIEWER, ReviewerAgent, {"code": "def login(): pass", "files": ["auth.py"]}),
        (AgentRole.TESTER, TesterAgent, {"target_files": ["auth.py"], "test_type": "unit"}),
        (AgentRole.DOCUMENTER, DocumenterAgent, {"doc_type": "readme", "target": "登录系统"}),
    ]
    
    for role, cls, input_data in role_tests:
        try:
            agent = cls(agent_id=f"test.{role.value}")
            agent.initialize()
            
            ctx = AgentContext(input_data=input_data)
            result = agent.execute(ctx)
            
            assert result.success == True, f"{role.value} 执行失败: {result.error_message}"
            assert result.output is not None
            
            print_result(f"{role.value} Agent执行", True)
            passed += 1
        except Exception as e:
            print_result(f"{role.value} Agent执行", False, str(e))
            failed += 1
    
    # 测试 create_agent_by_role
    try:
        agent = create_agent_by_role(AgentRole.DEVELOPER, agent_id="factory.test")
        assert isinstance(agent, DeveloperAgent)
        assert agent.agent_id == "factory.test"
        
        print_result("create_agent_by_role 工厂函数", True)
        passed += 1
    except Exception as e:
        print_result("create_agent_by_role 工厂函数", False, str(e))
        failed += 1
    
    # 测试 create_all_agents
    try:
        all_agents = create_all_agents()
        assert len(all_agents) == 8
        
        for role, agent in all_agents.items():
            assert isinstance(agent, BaseAgentImpl)
        
        print_result("create_all_agents 创建全部Agent", True, f"共{len(all_agents)}个")
        passed += 1
    except Exception as e:
        print_result("create_all_agents", False, str(e))
        failed += 1
    
    # ========== 3. 测试AgentRuntime ==========
    print_header("3. AgentRuntime运行时核心 (runtime.py)")
    
    try:
        from multi_agent_se.agents.runtime import (
            RuntimeError,
            RuntimeStats,
            AgentRuntime,
            get_runtime,
            reset_runtime,
        )
        print_result("导入运行时模块", True)
        passed += 1
    except Exception as e:
        print_result("导入运行时模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 RuntimeStats
    try:
        stats = RuntimeStats(
            total_agents=8,
            active_agents=8,
            total_tasks_executed=10,
            total_tasks_succeeded=9,
        )
        assert stats.total_agents == 8
        assert stats.success_rate == 0.9
        assert "success_rate" in stats.to_dict()
        
        print_result("RuntimeStats 数据类", True)
        passed += 1
    except Exception as e:
        print_result("RuntimeStats 数据类", False, str(e))
        failed += 1
    
    # 测试 AgentRuntime 初始化
    try:
        reset_runtime()
        runtime = AgentRuntime()
        runtime.initialize(include_builtin=True)
        
        assert runtime.get_stats().total_agents == 8
        
        print_result("AgentRuntime 初始化", True, f"注册{runtime.get_stats().total_agents}个Agent")
        passed += 1
    except Exception as e:
        print_result("AgentRuntime 初始化", False, str(e))
        failed += 1
    
    # 测试获取Agent
    try:
        agent = runtime.get_agent_by_role(AgentRole.DEVELOPER)
        assert agent is not None
        assert isinstance(agent, DeveloperAgent)
        
        all_agents = runtime.get_all_agents()
        assert len(all_agents) == 8
        
        active = runtime.get_active_agents()
        assert len(active) == 8  # 所有都已初始化
        
        print_result("AgentRuntime 获取Agent", True)
        passed += 1
    except Exception as e:
        print_result("AgentRuntime 获取Agent", False, str(e))
        failed += 1
    
    # 测试 execute_task
    try:
        result = runtime.execute_task(
            role=AgentRole.DEVELOPER,
            input_data={"task_description": "实现API", "language": "python"},
        )
        
        assert result.success == True
        assert result.output is not None
        
        stats = runtime.get_stats()
        assert stats.total_tasks_executed == 1
        assert stats.total_tasks_succeeded == 1
        
        print_result("AgentRuntime execute_task", True)
        passed += 1
    except Exception as e:
        print_result("AgentRuntime execute_task", False, str(e))
        failed += 1
    
    # 测试 execute_pipeline
    try:
        reset_runtime()
        runtime = AgentRuntime()
        runtime.initialize(include_builtin=True)
        
        pipeline_results = runtime.execute_pipeline(
            input_data={"requirement": "实现用户登录"},
        )
        
        assert len(pipeline_results) >= 1
        assert pipeline_results[0]["role"] == "requirement"
        
        # 检查每个阶段都有结果
        for r in pipeline_results:
            assert "role" in r
            assert "success" in r
        
        print_result("AgentRuntime execute_pipeline", True, f"执行{len(pipeline_results)}个阶段")
        passed += 1
    except Exception as e:
        print_result("AgentRuntime execute_pipeline", False, str(e))
        failed += 1
    
    # 测试消息路由
    try:
        from multi_agent_se.agents.communication import Message, MessageType
        
        msg = Message.create(
            sender_id="external",
            receiver_id="runtime.developer",
            payload={"task": "write_code"},
            message_type=MessageType.TASK_ASSIGN,
        )
        
        response = runtime.route_message(msg)
        assert response is not None
        
        print_result("AgentRuntime 消息路由", True)
        passed += 1
    except Exception as e:
        print_result("AgentRuntime 消息路由", False, str(e))
        failed += 1
    
    # 测试 shutdown
    try:
        runtime.shutdown()
        stats = runtime.get_stats()
        assert stats.total_agents == 0
        
        print_result("AgentRuntime shutdown", True)
        passed += 1
    except Exception as e:
        print_result("AgentRuntime shutdown", False, str(e))
        failed += 1
    
    # 测试全局运行时
    try:
        reset_runtime()
        rt1 = get_runtime()
        rt2 = get_runtime()
        assert rt1 is rt2
        
        print_result("全局运行时", True)
        passed += 1
    except Exception as e:
        print_result("全局运行时", False, str(e))
        failed += 1
    
    # ========== 4. 测试统一导出接口 ==========
    print_header("4. 统一导出接口 (__init__.py)")
    
    try:
        from multi_agent_se.agents.runtime import __all__
        
        expected_exports = [
            "AgentExecutionError", "AgentContext", "BaseAgentImpl",
            "ControllerAgent", "RequirementAgent", "ArchitectAgent",
            "DeveloperAgent", "BugfixAgent", "ReviewerAgent",
            "TesterAgent", "DocumenterAgent",
            "AGENT_CLASSES", "create_agent_by_role", "create_all_agents",
            "RuntimeError", "RuntimeStats", "AgentRuntime",
            "get_runtime", "reset_runtime",
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
        print("\n  🎉 第20阶段验收通过！")
        return 0
    else:
        print(f"\n  ⚠️ 第20阶段有 {failed} 项测试未通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
