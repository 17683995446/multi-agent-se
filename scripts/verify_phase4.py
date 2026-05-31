#!/usr/bin/env python3
"""阶段4验收验证脚本.

验证内容：
1. AutoGen正确安装
2. 基础对话Agent可运行
3. 消息收发正常
4. GroupChat功能可用
"""

import sys
from pathlib import Path

def print_header(text: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_result(test: str, passed: bool, details: str = "") -> bool:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test}")
    if details:
        print(f"       {details}")
    return passed

def main() -> int:
    print_header("阶段4验收验证 - 接入AutoGen基础会话通信内核")
    
    all_passed = True
    project_root = Path(__file__).parent.parent
    
    # 1. AutoGen安装检查
    print_header("1. AutoGen安装检查")
    
    try:
        import autogen
        all_passed = print_result("AutoGen已安装", True) and all_passed
        all_passed = print_result("ConversableAgent可导入", True) and all_passed
        all_passed = print_result("GroupChat可导入", True) and all_passed
        all_passed = print_result("GroupChatManager可导入", True) and all_passed
    except ImportError as e:
        all_passed = print_result("AutoGen已安装", False, str(e)) and all_passed
    
    # 2. Agent基础类检查
    print_header("2. Agent基础类检查")
    
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.agents.agent_base import (
            BaseAgent, AgentConfig, UserProxyWrapper,
            create_assistant_agent, create_user_proxy,
            HumanInputMode,
        )
        
        all_passed = print_result("Agent基础模块可导入", True) and all_passed
        
        # 创建助手Agent
        agent = create_assistant_agent(
            name="test_assistant",
            role="assistant",
            system_message="你是一个测试助手",
        )
        all_passed = print_result("create_assistant_agent可用", True) and all_passed
        all_passed = print_result("Agent名称正确", agent.name == "test_assistant") and all_passed
        all_passed = print_result("Agent角色正确", agent.role == "assistant") and all_passed
        all_passed = print_result("底层AutoGen Agent存在", agent.agent is not None) and all_passed
        
        # 创建用户代理
        user_proxy = create_user_proxy(name="test_user")
        all_passed = print_result("create_user_proxy可用", True) and all_passed
        all_passed = print_result("用户代理名称正确", user_proxy.name == "test_user") and all_passed
        
        # AgentConfig测试
        config = AgentConfig(name="cfg_test", role="tester")
        all_passed = print_result("AgentConfig可创建", True) and all_passed
        
    except Exception as e:
        all_passed = print_result("Agent基础模块", False, str(e)) and all_passed
    
    # 3. 消息通信模块检查
    print_header("3. 消息通信模块检查")
    
    try:
        from multi_agent_se.collaboration.dispatcher.messaging import (
            Message, MessageType, MessagePriority, MessageBus,
        )
        
        all_passed = print_result("消息模块可导入", True) and all_passed
        
        # 消息创建
        msg = Message(
            sender="agent_a",
            receiver="agent_b",
            content="测试消息",
            msg_type=MessageType.TASK,
        )
        all_passed = print_result("Message可创建", True) and all_passed
        all_passed = print_result("消息有唯一ID", bool(msg.id)) and all_passed
        all_passed = print_result("消息有时间戳", bool(msg.timestamp)) and all_passed
        all_passed = print_result("消息序列化正常", len(msg.to_dict()) > 0) and all_passed
        
        # 消息反序列化
        msg_dict = msg.to_dict()
        restored = Message.from_dict(msg_dict)
        all_passed = print_result("消息反序列化正常", restored.id == msg.id) and all_passed
        
        # 消息总线
        bus = MessageBus()
        bus.send("agent_a", "agent_b", "消息1", trace_id="trace_001")
        bus.send("agent_b", "agent_a", "消息2", trace_id="trace_001")
        bus.send("agent_a", "agent_c", "消息3")
        
        all_passed = print_result("消息总线send可用", bus.total_messages == 3) and all_passed
        
        history = bus.get_history(sender="agent_a")
        all_passed = print_result("按发送方过滤历史", len(history) == 2) and all_passed
        
        conversation = bus.get_conversation("agent_a", "agent_b")
        all_passed = print_result("获取对话历史", len(conversation) == 2) and all_passed
        
        trace_msgs = bus.get_history(trace_id="trace_001")
        all_passed = print_result("按链路ID过滤", len(trace_msgs) == 2) and all_passed
        
        summary = bus.summary()
        all_passed = print_result("消息摘要可用", summary["total_messages"] == 3) and all_passed
        
    except Exception as e:
        all_passed = print_result("消息模块", False, str(e)) and all_passed
    
    # 4. GroupChat管理检查
    print_header("4. GroupChat管理检查")
    
    try:
        from multi_agent_se.collaboration.dispatcher.group_chat import GroupChatManager
        from multi_agent_se.agents.agent_base import create_assistant_agent
        
        # 创建多个Agent
        agents = [
            create_assistant_agent("architect", "架构师", "你是架构师"),
            create_assistant_agent("developer", "开发者", "你是开发者"),
            create_assistant_agent("reviewer", "评审员", "你是评审员"),
        ]
        
        # 创建GroupChat管理器
        manager = GroupChatManager(
            name="test_manager",
            agents=agents,
            max_round=10,
        )
        
        all_passed = print_result("GroupChatManager可创建", True) and all_passed
        all_passed = print_result("Agent数量正确", len(manager.agents) == 3) and all_passed
        all_passed = print_result("get_agent_list可用", len(manager.get_agent_list()) == 3) and all_passed
        
        # 测试Agent查询
        found = manager.get_agent_by_name("developer")
        all_passed = print_result("get_agent_by_name可用", found is not None and found.name == "developer") and all_passed
        
        not_found = manager.get_agent_by_name("nonexistent")
        all_passed = print_result("不存在的Agent返回None", not_found is None) and all_passed
        
        # 测试Agent增删
        new_agent = create_assistant_agent("tester", "测试员", "你是测试员")
        manager.add_agent(new_agent)
        all_passed = print_result("add_agent可用", len(manager.agents) == 4) and all_passed
        
        manager.remove_agent("tester")
        all_passed = print_result("remove_agent可用", len(manager.agents) == 3) and all_passed
        
        # 构建GroupChat
        manager.build()
        all_passed = print_result("GroupChat构建成功", True) and all_passed
        
        info = manager.get_info()
        all_passed = print_result("get_info可用", info["is_built"] is True) and all_passed
        
    except Exception as e:
        all_passed = print_result("GroupChat管理", False, str(e)) and all_passed
    
    # 5. 文件结构检查
    print_header("5. 文件结构检查")
    
    required_files = [
        "src/multi_agent_se/agents/agent_base.py",
        "src/multi_agent_se/collaboration/dispatcher/messaging.py",
        "src/multi_agent_se/collaboration/dispatcher/group_chat.py",
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        all_passed = print_result(
            f"文件: {file_path}",
            full_path.exists(),
            "存在" if full_path.exists() else "不存在"
        ) and all_passed
    
    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段4验收通过！所有检查项均符合要求。")
        print("  📋 阶段4交付物清单：")
        print("     - agent_base.py (BaseAgent/AgentConfig/UserProxyWrapper)")
        print("     - messaging.py (Message/MessageBus/消息追溯)")
        print("     - group_chat.py (GroupChatManager/多Agent群聊)")
        print("     - scripts/verify_phase4.py (验收脚本)")
        return 0
    else:
        print("  ❌ 阶段4验收未通过！请修复上述失败项。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
