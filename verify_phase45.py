"""第45阶段验收脚本 - 全系统输入验证标准化.

验证所有8个Agent对非法输入类型的正确处理。
"""

import sys
sys.path.insert(0, "/workspace/multi_agent_se/src")

from multi_agent_se.agents.controller import ControllerAgent
from multi_agent_se.agents.requirement import RequirementAgent
from multi_agent_se.agents.architect import ArchitectAgent
from multi_agent_se.agents.developer import DeveloperAgent
from multi_agent_se.agents.bugfix import BugfixAgent
from multi_agent_se.agents.reviewer import ReviewerAgent
from multi_agent_se.agents.tester import TesterAgent
from multi_agent_se.agents.documenter import DocumenterAgent
from multi_agent_se.agents.runtime.base_agent import AgentContext
from multi_agent_se.scheduler.task import Task


def test_all_agents_non_dict_input():
    """测试: 所有Agent对非字典输入的拒绝."""
    print("\n[TEST] 所有Agent非字典输入验证")
    
    agents = [
        ("Controller", ControllerAgent()),
        ("Requirement", RequirementAgent()),
        ("Architect", ArchitectAgent()),
        ("Developer", DeveloperAgent()),
        ("Bugfix", BugfixAgent()),
        ("Reviewer", ReviewerAgent()),
        ("Tester", TesterAgent()),
        ("Documenter", DocumenterAgent()),
    ]
    
    bad_inputs = [
        "string_input",
        12345,
        ["list", "input"],
        None,
        {"nested": "dict"},  # 嵌套字典作为顶层（某些Agent可能接受）
    ]
    
    passed = 0
    total = 0
    
    for name, agent in agents:
        for bad_input in bad_inputs:
            total += 1
            try:
                task = Task(task_id=f"val.{name}", task_type=name.lower())
                context = AgentContext(task=task, input_data=bad_input)
                result = agent.process(context)
                
                if not isinstance(bad_input, dict):
                    # 非字典输入应该被拒绝
                    if not result.success and ("字典" in result.error_message or "dict" in result.error_message.lower()):
                        passed += 1
                    else:
                        print(f"  ✗ {name} 未拒绝非字典输入 {type(bad_input).__name__}: {result.error_message}")
                else:
                    # 字典输入（即使是嵌套的）应该被接受或正常处理
                    passed += 1
                    
            except Exception as e:
                print(f"  ✗ {name} 处理 {type(bad_input).__name__} 时抛出异常: {e}")
    
    print(f"  结果: {passed}/{total} 通过")
    return passed == total


def test_input_validator_module():
    """测试: 输入验证器模块."""
    print("\n[TEST] 输入验证器模块")
    
    from multi_agent_se.utils.input_validator import InputValidator
    
    # 测试 validate_dict
    assert InputValidator.validate_dict({}) == (True, None)
    assert InputValidator.validate_dict("bad")[0] == False
    assert InputValidator.validate_dict(123)[0] == False
    print("  ✓ validate_dict")
    
    # 测试 validate_string
    assert InputValidator.validate_string("hello", "field") == (True, None)
    assert InputValidator.validate_string(123, "field")[0] == False
    assert InputValidator.validate_string(None, "field", allow_none=True) == (True, None)
    print("  ✓ validate_string")
    
    # 测试 validate_list
    assert InputValidator.validate_list([1, 2], "field") == (True, None)
    assert InputValidator.validate_list("bad", "field")[0] == False
    assert InputValidator.validate_list([], "field", allow_empty=False)[0] == False
    print("  ✓ validate_list")
    
    # 测试 validate_int
    assert InputValidator.validate_int(42, "field") == (True, None)
    assert InputValidator.validate_int("bad", "field")[0] == False
    assert InputValidator.validate_int(5, "field", min_value=10)[0] == False
    assert InputValidator.validate_int(True, "field")[0] == False  # bool不是int
    print("  ✓ validate_int")
    
    # 测试 validate_agent_input
    assert InputValidator.validate_agent_input(
        {"name": "test"},
        required_fields={"name": "str"}
    )[0] == True
    assert InputValidator.validate_agent_input(
        {},
        required_fields={"name": "str"}
    )[0] == False
    assert InputValidator.validate_agent_input(
        {"name": 123},
        required_fields={"name": "str"}
    )[0] == False
    print("  ✓ validate_agent_input")
    
    return True


def test_specific_type_validation():
    """测试: 特定字段类型验证."""
    print("\n[TEST] 特定字段类型验证")
    
    # BugfixAgent: error_message 必须是字符串
    agent = BugfixAgent()
    task = Task(task_id="type.bugfix", task_type="bugfix")
    
    # 字典类型的 error_message 应该被拒绝
    context = AgentContext(task=task, input_data={
        "error_message": {"nested": "dict"},
    })
    result = agent.process(context)
    assert not result.success and "字符串" in result.error_message
    print("  ✓ BugfixAgent 拒绝字典类型的 error_message")
    
    # 列表类型的 stack_trace 应该被拒绝
    context = AgentContext(task=task, input_data={
        "error_message": "error",
        "stack_trace": ["line1", "line2"],
    })
    result = agent.process(context)
    assert not result.success and "字符串" in result.error_message
    print("  ✓ BugfixAgent 拒绝列表类型的 stack_trace")
    
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第45阶段验收测试 - 全系统输入验证标准化")
    print("=" * 60)
    
    tests = [
        ("输入验证器模块", test_input_validator_module),
        ("特定字段类型验证", test_specific_type_validation),
        ("所有Agent非字典输入", test_all_agents_non_dict_input),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"  ✓ {name} 通过")
            else:
                failed += 1
                print(f"  ✗ {name} 失败")
        except Exception as e:
            failed += 1
            print(f"  ✗ {name} 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 第45阶段验收通过！全系统输入验证标准化完成。")
    else:
        print("❌ 部分测试失败。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
