"""第38阶段验收脚本 - Documenter Agent验证.

验证文档Agent的完整功能：
- 枚举定义
- 数据模型
- 文档生成（README/API/架构/变更日志/用户指南/开发者指南）
- 章节解析
- 文档历史追踪
"""

import sys
import traceback
from typing import Any, Dict, List

sys.path.insert(0, "/workspace/multi_agent_se/src")

from multi_agent_se.agents.documenter import (
    DocumenterAgent,
    DocType,
    DocFormat,
    DocStatus,
    DocSection,
    DocMetadata,
    GeneratedDoc,
    DocumentationResult,
)
from multi_agent_se.agents.runtime.base_agent import AgentContext
from multi_agent_se.scheduler.task import Task


def test_doc_type_enum():
    """测试: DocType枚举."""
    print("\n[TEST] DocType枚举")
    
    assert DocType.README.value == "readme"
    assert DocType.API.value == "api"
    assert DocType.ARCHITECTURE.value == "architecture"
    assert DocType.USER_GUIDE.value == "user_guide"
    assert DocType.DEVELOPER_GUIDE.value == "dev_guide"
    assert DocType.CHANGELOG.value == "changelog"
    assert DocType.LICENSE.value == "license"
    assert DocType.CONTRIBUTING.value == "contributing"
    assert DocType.CODE_OF_CONDUCT.value == "coc"
    assert DocType.DOCSTRING.value == "docstring"
    
    print("  ✓ DocType枚举定义正确（10种文档类型）")
    return True


def test_doc_format_enum():
    """测试: DocFormat枚举."""
    print("\n[TEST] DocFormat枚举")
    
    assert DocFormat.MARKDOWN.value == "markdown"
    assert DocFormat.RST.value == "rst"
    assert DocFormat.HTML.value == "html"
    assert DocFormat.PLAIN.value == "plain"
    assert DocFormat.YAML.value == "yaml"
    assert DocFormat.JSON.value == "json"
    
    print("  ✓ DocFormat枚举定义正确（6种格式）")
    return True


def test_doc_status_enum():
    """测试: DocStatus枚举."""
    print("\n[TEST] DocStatus枚举")
    
    assert DocStatus.DRAFT.value == "draft"
    assert DocStatus.REVIEW.value == "review"
    assert DocStatus.PUBLISHED.value == "published"
    assert DocStatus.OUTDATED.value == "outdated"
    assert DocStatus.DEPRECATED.value == "deprecated"
    
    print("  ✓ DocStatus枚举定义正确（5种状态）")
    return True


def test_doc_section():
    """测试: DocSection数据类."""
    print("\n[TEST] DocSection数据类")
    
    section = DocSection(
        title="快速开始",
        content="这里是快速开始的内容...",
        level=2,
        order=1,
    )
    
    assert section.title == "快速开始"
    assert section.level == 2
    assert section.order == 1
    
    data = section.to_dict()
    assert data["title"] == "快速开始"
    assert data["level"] == 2
    
    print("  ✓ DocSection数据类工作正常")
    return True


def test_doc_metadata():
    """测试: DocMetadata数据类."""
    print("\n[TEST] DocMetadata数据类")
    
    metadata = DocMetadata(
        title="项目文档",
        description="这是一个示例项目",
        author="Developer",
        version="1.0.0",
        tags=["python", "documentation"],
    )
    
    assert metadata.title == "项目文档"
    assert metadata.version == "1.0.0"
    assert len(metadata.tags) == 2
    
    data = metadata.to_dict()
    assert data["title"] == "项目文档"
    assert data["version"] == "1.0.0"
    
    print("  ✓ DocMetadata数据类工作正常")
    return True


def test_generated_doc():
    """测试: GeneratedDoc数据类."""
    print("\n[TEST] GeneratedDoc数据类")
    
    doc = GeneratedDoc(
        doc_type=DocType.README,
        doc_format=DocFormat.MARKDOWN,
        file_path="./",
        file_name="README.md",
        metadata=DocMetadata(title="Test Project"),
        content="# Test Project\n\nDescription here.",
        status=DocStatus.PUBLISHED,
        word_count=10,
        line_count=5,
    )
    
    assert doc.doc_type == DocType.README
    assert doc.file_name == "README.md"
    assert doc.status == DocStatus.PUBLISHED
    
    data = doc.to_dict()
    assert data["doc_type"] == "readme"
    assert data["file_name"] == "README.md"
    assert data["word_count"] == 10
    
    print("  ✓ GeneratedDoc数据类工作正常")
    return True


def test_documentation_result():
    """测试: DocumentationResult数据类."""
    print("\n[TEST] DocumentationResult数据类")
    
    docs = [
        GeneratedDoc(doc_type=DocType.README, word_count=100),
        GeneratedDoc(doc_type=DocType.API, word_count=200),
    ]
    
    result = DocumentationResult(
        documents=docs,
        total_docs=2,
        total_words=300,
        total_lines=50,
        summary="生成2个文档",
    )
    
    assert result.total_docs == 2
    assert result.total_words == 300
    
    data = result.to_dict()
    assert data["total_docs"] == 2
    assert data["total_words"] == 300
    
    print("  ✓ DocumentationResult数据类工作正常")
    return True


def test_agent_creation():
    """测试: DocumenterAgent创建."""
    print("\n[TEST] DocumenterAgent创建")
    
    from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
    
    agent = DocumenterAgent(agent_id="documenter.001")
    
    assert agent.agent_id == "documenter.001"
    assert agent.role == AgentRole.DOCUMENTER
    assert AgentCapability.DOCUMENTATION in agent.capabilities
    assert AgentCapability.FILE_OPERATION in agent.capabilities
    
    print(f"  ✓ DocumenterAgent创建成功: {agent.agent_id}")
    print(f"    - 角色: {agent.role.value}")
    print(f"    - 能力: {[c.value for c in agent.capabilities]}")
    return True


def test_readme_generation():
    """测试: README文档生成."""
    print("\n[TEST] README文档生成")
    
    agent = DocumenterAgent()
    
    code = '''
class DataProcessor:
    def process(self, data):
        return data.upper()
    
    def validate(self, data):
        return len(data) > 0

def helper_function():
    return "help"
'''
    
    readme = agent._generate_readme("MyProject", code, {})
    
    assert "# MyProject" in readme
    assert "## 功能特性" in readme
    assert "## 安装" in readme
    assert "## 快速开始" in readme
    assert "DataProcessor" in readme or "helper_function" in readme
    
    print("  ✓ README生成成功")
    print(f"    文档长度: {len(readme)} 字符")
    return True


def test_api_doc_generation():
    """测试: API文档生成."""
    print("\n[TEST] API文档生成")
    
    agent = DocumenterAgent()
    
    code = '''
class UserManager:
    def __init__(self):
        self.users = {}
    
    def add_user(self, name):
        self.users[name] = {"name": name}
        return self.users[name]
    
    def get_user(self, name):
        return self.users.get(name)

def process_data(data):
    return data.upper()
'''
    
    api_doc = agent._generate_api_doc("UserService", code, {})
    
    assert "# UserService API 文档" in api_doc
    assert "## 类和方法" in api_doc
    assert "UserManager" in api_doc
    assert "add_user" in api_doc or "get_user" in api_doc
    
    print("  ✓ API文档生成成功")
    return True


def test_architecture_doc_generation():
    """测试: 架构文档生成."""
    print("\n[TEST] 架构文档生成")
    
    agent = DocumenterAgent()
    
    architecture = {
        "layers": ["输入层", "处理层", "存储层", "输出层"],
        "components": [
            {"name": "InputParser", "responsibility": "解析输入数据"},
            {"name": "DataProcessor", "responsibility": "处理数据逻辑"},
        ],
    }
    
    arch_doc = agent._generate_architecture_doc("MySystem", "", architecture)
    
    assert "# MySystem 架构设计" in arch_doc
    assert "## 系统分层" in arch_doc
    assert "输入层" in arch_doc
    assert "处理层" in arch_doc
    assert "InputParser" in arch_doc
    assert "DataProcessor" in arch_doc
    
    print("  ✓ 架构文档生成成功")
    return True


def test_changelog_generation():
    """测试: 变更日志生成."""
    print("\n[TEST] 变更日志生成")
    
    agent = DocumenterAgent()
    
    changelog = agent._generate_changelog("MyProject", "", {})
    
    assert "# 变更日志" in changelog
    assert "## [1.0.0]" in changelog
    assert "### 新增" in changelog
    assert "初始版本发布" in changelog
    
    print("  ✓ 变更日志生成成功")
    return True


def test_section_parsing():
    """测试: 文档章节解析."""
    print("\n[TEST] 文档章节解析")
    
    agent = DocumenterAgent()
    
    content = '''# 主标题

这是介绍。

## 第一节

第一节内容。

### 子节

子节内容。

## 第二节

第二节内容。
'''
    
    sections = agent._parse_sections(content)
    
    assert len(sections) >= 2
    assert sections[0].title == "主标题"
    assert sections[0].level == 1
    assert any(s.title == "第一节" for s in sections)
    assert any(s.level == 2 for s in sections)
    
    print(f"  ✓ 章节解析成功，共 {len(sections)} 个章节")
    for s in sections[:3]:
        print(f"    - {'#' * s.level} {s.title}")
    return True


def test_agent_full_process():
    """测试: Agent完整处理流程."""
    print("\n[TEST] Agent完整处理流程")
    
    agent = DocumenterAgent(agent_id="documenter.test")
    
    code = '''
class StringProcessor:
    def reverse(self, text):
        return text[::-1]
    
    def capitalize(self, text):
        return text.capitalize()
'''
    
    architecture = {
        "layers": ["输入层", "处理层"],
        "components": [
            {"name": "StringProcessor", "responsibility": "字符串处理"},
        ],
    }
    
    task = Task(
        task_id="task.doc.001",
        task_type="documentation",
        description="生成项目文档",
    )
    
    context = AgentContext(
        task=task,
        input_data={
            "doc_types": ["readme", "api", "architecture"],
            "target": "StringProcessor",
            "code": code,
            "architecture": architecture,
        },
    )
    
    result = agent.process(context)
    
    assert result.success is True
    assert result.output is not None
    assert "result_id" in result.output
    assert "total_docs" in result.output
    assert result.output["total_docs"] == 3
    assert "documents" in result.output
    assert "summary" in result.output
    
    print(f"  ✓ Agent处理成功:")
    print(f"    - 结果ID: {result.output['result_id']}")
    print(f"    - 生成文档数: {result.output['total_docs']}")
    print(f"    - 总词数: {result.output['total_words']}")
    print(f"    - 总行数: {result.output['total_lines']}")
    print(f"    - 摘要: {result.output['summary'][:60]}...")
    return True


def test_doc_history():
    """测试: 文档历史追踪."""
    print("\n[TEST] 文档历史追踪")
    
    agent = DocumenterAgent()
    
    # 执行多次文档生成
    for i in range(3):
        task = Task(task_id=f"task.doc.{i}")
        context = AgentContext(
            task=task,
            input_data={
                "doc_type": "readme",
                "target": f"Project{i}",
            },
        )
        agent.process(context)
    
    history = agent.get_doc_history()
    stats = agent.get_statistics()
    
    assert len(history) == 3
    assert stats["total_runs"] == 3
    assert stats["total_docs_generated"] == 3
    
    print(f"  ✓ 历史追踪正常:")
    print(f"    - 总运行数: {stats['total_runs']}")
    print(f"    - 总文档数: {stats['total_docs_generated']}")
    print(f"    - 平均每次文档数: {stats['avg_docs_per_run']:.1f}")
    print(f"    - 总词数: {stats['total_words_generated']}")
    return True


def test_error_handling():
    """测试: 错误处理."""
    print("\n[TEST] 错误处理")
    
    agent = DocumenterAgent()
    
    task = Task(task_id="task.empty")
    context = AgentContext(
        task=task,
        input_data={
            "doc_types": [],  # 空文档类型列表
        },
    )
    
    result = agent.process(context)
    
    assert result.success is False
    assert "未生成任何文档" in result.error_message
    
    print(f"  ✓ 错误处理正确: {result.error_message}")
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第38阶段验收测试 - Documenter Agent")
    print("=" * 60)
    
    tests = [
        ("DocType枚举", test_doc_type_enum),
        ("DocFormat枚举", test_doc_format_enum),
        ("DocStatus枚举", test_doc_status_enum),
        ("DocSection数据类", test_doc_section),
        ("DocMetadata数据类", test_doc_metadata),
        ("GeneratedDoc数据类", test_generated_doc),
        ("DocumentationResult数据类", test_documentation_result),
        ("Agent创建", test_agent_creation),
        ("README生成", test_readme_generation),
        ("API文档生成", test_api_doc_generation),
        ("架构文档生成", test_architecture_doc_generation),
        ("变更日志生成", test_changelog_generation),
        ("章节解析", test_section_parsing),
        ("Agent完整处理流程", test_agent_full_process),
        ("文档历史追踪", test_doc_history),
        ("错误处理", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n  ✗ {name} 失败: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 第38阶段验收通过！Documenter Agent实现完成。")
        print("\n✨ 8大正交角色Agent全部完成！")
    else:
        print("❌ 部分测试失败，请检查实现。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
