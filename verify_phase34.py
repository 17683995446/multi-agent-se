"""第34阶段验收脚本: Developer Agent."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from multi_agent_se.agents.developer import (
    DeveloperAgent, CodeLanguage, CodeTaskType, CodeFile, CodeChange, DevelopmentResult,
)
from multi_agent_se.agents.runtime.base_agent import AgentContext

def print_header(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")
def print_result(n, p): print(f"  {'[✓ PASS]' if p else '[✗ FAIL]'} {n}")

def test_enums():
    print_header("测试1: 枚举类型")
    assert len(list(CodeLanguage)) == 6
    assert len(list(CodeTaskType)) == 5
    print_result("枚举类型", True); return True

def test_code_file():
    print_header("测试2: CodeFile")
    file = CodeFile(file_path="test.py", language=CodeLanguage.PYTHON, content="pass")
    assert file.file_path == "test.py"
    assert len(file.file_id) == 8
    print_result("CodeFile", True); return True

def test_development_result():
    print_header("测试3: DevelopmentResult")
    result = DevelopmentResult(task_type=CodeTaskType.IMPLEMENTATION)
    result.files.append(CodeFile(file_path="a.py"))
    assert len(result.files) == 1
    print_result("DevelopmentResult", True); return True

def test_agent_creation():
    print_header("测试4: DeveloperAgent 创建")
    agent = DeveloperAgent(agent_id="dev-001")
    assert agent.agent_id == "dev-001"
    assert agent.AGENT_ROLE.value == "developer"
    print(f"  角色: {agent.AGENT_ROLE.value}")
    print_result("Agent创建", True); return True

def test_implementation():
    print_header("测试5: 代码实现")
    agent = DeveloperAgent()
    context = AgentContext(input_data={
        "requirement": "实现一个用户管理类，支持添加用户和删除用户功能",
        "module_name": "user",
    })
    result = agent.process(context)
    assert result.success
    print(f"  生成文件数: {len(result.output['files'])}")
    print(f"  代码行数: {result.output['total_lines']}")
    assert len(result.output['files']) > 0
    assert result.output['total_lines'] > 0
    print_result("代码实现", True); return True

def test_test_generation():
    print_header("测试6: 测试代码生成")
    agent = DeveloperAgent()
    context = AgentContext(input_data={
        "requirement": "为用户类编写测试",
        "module_name": "user",
        "task_type": "test",
    })
    result = agent.process(context)
    assert result.success
    print(f"  测试覆盖率: {result.output['test_coverage']}")
    assert result.output['test_coverage'] > 0
    print_result("测试生成", True); return True

def test_code_quality():
    print_header("测试7: 代码质量检查")
    agent = DeveloperAgent()
    context = AgentContext(input_data={
        "requirement": "实现功能",
        "module_name": "test",
    })
    result = agent.process(context)
    print(f"  质量问题: {result.output['issues']}")
    print_result("代码质量检查", True); return True

def test_error_handling():
    print_header("测试8: 错误处理")
    agent = DeveloperAgent()
    context = AgentContext(input_data={})
    result = agent.process(context)
    assert not result.success
    assert "缺少开发需求" in result.error_message
    print_result("错误处理", True); return True

def main():
    print("="*60 + "\n  第34阶段验收: Developer Agent\n" + "="*60)
    tests = [test_enums, test_code_file, test_development_result, test_agent_creation,
             test_implementation, test_test_generation, test_code_quality, test_error_handling]
    passed = sum(1 for t in tests if t())
    print(f"\n{'='*60}\n  验收结果: {passed}/{len(tests)} 通过\n{'='*60}")
    sys.exit(0 if passed == len(tests) else 1)

if __name__ == "__main__":
    main()
