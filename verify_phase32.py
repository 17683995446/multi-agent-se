"""第32阶段验收脚本: Requirement Agent."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from multi_agent_se.agents.requirement import (
    RequirementAgent, RequirementType, RequirementPriority, RequirementStatus,
    RequirementItem, RequirementAnalysis,
)
from multi_agent_se.agents.runtime.base_agent import AgentContext

def print_header(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")
def print_result(n, p): print(f"  {'[✓ PASS]' if p else '[✗ FAIL]'} {n}")

def test_enums():
    print_header("测试1: 枚举类型")
    assert len(list(RequirementType)) == 6
    assert len(list(RequirementPriority)) == 4
    assert len(list(RequirementStatus)) == 5
    print_result("枚举类型", True); return True

def test_requirement_item():
    print_header("测试2: RequirementItem")
    req = RequirementItem(title="测试需求", description="系统应该支持登录功能")
    assert req.req_type == RequirementType.FUNCTIONAL
    assert len(req.req_id) == 8
    print_result("RequirementItem", True); return True

def test_requirement_analysis():
    print_header("测试3: RequirementAnalysis")
    analysis = RequirementAnalysis(original_input="测试输入")
    analysis.requirements.append(RequirementItem(title="R1"))
    analysis.requirements.append(RequirementItem(title="R2", priority=RequirementPriority.MUST_HAVE))
    assert len(analysis.get_must_haves()) == 1
    print_result("RequirementAnalysis", True); return True

def test_agent_creation():
    print_header("测试4: RequirementAgent 创建")
    agent = RequirementAgent(agent_id="req-001")
    assert agent.agent_id == "req-001"
    assert agent.AGENT_ROLE.value == "requirement"
    print(f"  角色: {agent.AGENT_ROLE.value}")
    print_result("Agent创建", True); return True

def test_functional_extraction():
    print_header("测试5: 功能需求提取")
    agent = RequirementAgent()
    context = AgentContext(input_data={"requirement": "系统应该支持用户登录功能。用户必须能够输入用户名和密码。"})
    result = agent.process(context)
    assert result.success
    print(f"  提取需求数: {result.output['analysis']['total_requirements']}")
    print(f"  功能需求: {result.output['analysis']['functional']}")
    assert result.output['analysis']['functional'] > 0
    print_result("功能需求提取", True); return True

def test_non_functional_extraction():
    print_header("测试6: 非功能需求提取")
    agent = RequirementAgent()
    context = AgentContext(input_data={"requirement": "系统响应时间必须在2秒以内。数据需要加密存储。"})
    result = agent.process(context)
    assert result.success
    print(f"  非功能需求: {result.output['analysis']['non_functional']}")
    assert result.output['analysis']['non_functional'] > 0
    print_result("非功能需求提取", True); return True

def test_quality_evaluation():
    print_header("测试7: 质量评估")
    agent = RequirementAgent()
    context = AgentContext(input_data={"requirement": "系统应该支持100个并发用户，响应时间小于2秒。"})
    result = agent.process(context)
    scores = result.output['analysis']['quality_scores']
    print(f"  质量评分: {scores}")
    assert scores['clarity'] > 0
    print_result("质量评估", True); return True

def test_suggestions():
    print_header("测试8: 改进建议")
    agent = RequirementAgent()
    context = AgentContext(input_data={"requirement": "做一个系统"})  # 模糊需求
    result = agent.process(context)
    print(f"  建议数: {len(result.output['suggestions'])}")
    print(f"  建议: {result.output['suggestions'][:2]}")
    assert len(result.output['suggestions']) > 0
    print_result("改进建议", True); return True

def test_error_handling():
    print_header("测试9: 错误处理")
    agent = RequirementAgent()
    context = AgentContext(input_data={})
    result = agent.process(context)
    assert not result.success
    assert "缺少需求" in result.error_message
    print_result("错误处理", True); return True

def main():
    print("="*60 + "\n  第32阶段验收: Requirement Agent\n" + "="*60)
    tests = [test_enums, test_requirement_item, test_requirement_analysis, 
             test_agent_creation, test_functional_extraction, test_non_functional_extraction,
             test_quality_evaluation, test_suggestions, test_error_handling]
    passed = sum(1 for t in tests if t())
    print(f"\n{'='*60}\n  验收结果: {passed}/{len(tests)} 通过\n{'='*60}")
    sys.exit(0 if passed == len(tests) else 1)

if __name__ == "__main__":
    main()
