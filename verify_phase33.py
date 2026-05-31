"""第33阶段验收脚本: Architect Agent."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from multi_agent_se.agents.architect import (
    ArchitectAgent, ArchitectureStyle, ModuleType, ModuleDefinition,
    InterfaceDefinition, DataModel, ArchitectureDesign,
)
from multi_agent_se.agents.runtime.base_agent import AgentContext

def print_header(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")
def print_result(n, p): print(f"  {'[✓ PASS]' if p else '[✗ FAIL]'} {n}")

def test_enums():
    print_header("测试1: 枚举类型")
    assert len(list(ArchitectureStyle)) == 7
    assert len(list(ModuleType)) == 6
    print_result("枚举类型", True); return True

def test_module_definition():
    print_header("测试2: ModuleDefinition")
    mod = ModuleDefinition(name="core", description="核心模块", module_type=ModuleType.CORE)
    assert mod.name == "core"
    assert len(mod.module_id) == 8
    print_result("ModuleDefinition", True); return True

def test_architecture_design():
    print_header("测试3: ArchitectureDesign")
    design = ArchitectureDesign(name="测试架构", style=ArchitectureStyle.LAYERED)
    design.modules.append(ModuleDefinition(name="m1"))
    assert design.get_module("m1") is not None
    assert design.get_module("nonexistent") is None
    print_result("ArchitectureDesign", True); return True

def test_agent_creation():
    print_header("测试4: ArchitectAgent 创建")
    agent = ArchitectAgent(agent_id="arch-001")
    assert agent.agent_id == "arch-001"
    assert agent.AGENT_ROLE.value == "architect"
    print(f"  角色: {agent.AGENT_ROLE.value}")
    print_result("Agent创建", True); return True

def test_layered_architecture():
    print_header("测试5: 分层架构设计")
    agent = ArchitectAgent()
    context = AgentContext(input_data={
        "name": "用户管理系统",
        "requirements": [
            {"description": "用户登录功能"},
            {"description": "用户注册功能"},
        ],
        "style": "layered",
    })
    result = agent.process(context)
    assert result.success
    print(f"  模块数: {result.output['design']['module_count']}")
    print(f"  架构风格: {result.output['design']['style']}")
    assert result.output['design']['style'] == "layered"
    assert result.output['design']['module_count'] >= 3
    print_result("分层架构设计", True); return True

def test_modular_architecture():
    print_header("测试6: 模块化架构设计")
    agent = ArchitectAgent()
    context = AgentContext(input_data={
        "name": "插件系统",
        "requirements": [{"description": "支持插件扩展"}],
        "style": "modular",
    })
    result = agent.process(context)
    assert result.success
    print(f"  模块数: {result.output['design']['module_count']}")
    print(f"  架构风格: {result.output['design']['style']}")
    assert result.output['design']['style'] == "modular"
    print_result("模块化架构设计", True); return True

def test_quality_assessment():
    print_header("测试7: 架构质量评估")
    agent = ArchitectAgent()
    context = AgentContext(input_data={
        "name": "测试系统",
        "requirements": [{"description": "功能1"}, {"description": "功能2"}],
    })
    result = agent.process(context)
    scores = result.output['quality_assessment']
    print(f"  质量评分: {scores}")
    assert 0 <= scores['complexity'] <= 1
    assert 0 <= scores['coupling'] <= 1
    assert 0 <= scores['cohesion'] <= 1
    print_result("质量评估", True); return True

def test_tech_stack():
    print_header("测试8: 技术栈选择")
    agent = ArchitectAgent()
    context = AgentContext(input_data={
        "name": "Web服务",
        "requirements": [{"description": "API服务"}],
    })
    result = agent.process(context)
    stack = result.output['design']['tech_stack']
    print(f"  技术栈: {stack}")
    assert 'language' in stack
    assert 'database' in stack
    print_result("技术栈选择", True); return True

def test_error_handling():
    print_header("测试9: 错误处理")
    agent = ArchitectAgent()
    context = AgentContext(input_data={})
    result = agent.process(context)
    assert not result.success
    assert "缺少需求" in result.error_message
    print_result("错误处理", True); return True

def main():
    print("="*60 + "\n  第33阶段验收: Architect Agent\n" + "="*60)
    tests = [test_enums, test_module_definition, test_architecture_design,
             test_agent_creation, test_layered_architecture, test_modular_architecture,
             test_quality_assessment, test_tech_stack, test_error_handling]
    passed = sum(1 for t in tests if t())
    print(f"\n{'='*60}\n  验收结果: {passed}/{len(tests)} 通过\n{'='*60}")
    sys.exit(0 if passed == len(tests) else 1)

if __name__ == "__main__":
    main()
