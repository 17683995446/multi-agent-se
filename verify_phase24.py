#!/usr/bin/env python3
"""第24阶段验收脚本 - 文档生成器.

验证内容：
- 文档类型枚举
- 文档章节模型
- API文档条目
- 变更日志条目
- 完整文档生成
- AST文档提取
- README生成
- API文档生成
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from multi_agent_se.quality.docs import (
    DocType,
    DocFormat,
    ChangeType,
    DocSection,
    ParamInfo,
    APIEntry,
    ChangelogEntry,
    DocMetadata,
    Document,
    ASTDocExtractor,
    DocGenerator,
    create_section,
    create_api_entry,
    create_changelog,
    generate_readme,
    generate_api_doc,
    extract_docstring,
)


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name: str, passed: bool, message: str = "") -> None:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {test_name}")
    if message:
        print(f"         {message}")


def test_enums() -> bool:
    """测试枚举类型."""
    print_header("测试1: 枚举类型")

    doc_types = list(DocType)
    print(f"  DocType: {len(doc_types)}个 - {[d.value for d in doc_types]}")

    formats = list(DocFormat)
    print(f"  DocFormat: {len(formats)}个 - {[f.value for f in formats]}")

    changes = list(ChangeType)
    print(f"  ChangeType: {len(changes)}个 - {[c.value for c in changes]}")

    assert len(doc_types) == 8
    assert len(formats) == 4
    assert len(changes) == 7
    print_result("枚举类型", True, f"DocType={len(doc_types)}, DocFormat={len(formats)}, ChangeType={len(changes)}")
    return True


def test_doc_section() -> bool:
    """测试文档章节."""
    print_header("测试2: DocSection 文档章节")

    sec = create_section("安装指南", "使用pip安装", level=2)
    md = sec.to_markdown()
    assert "## 安装指南" in md
    assert "使用pip安装" in md
    print(f"  ✓ Markdown生成:\n    {md}")

    # 嵌套章节
    parent = create_section("第一章", "概述", level=1)
    child = create_section("第一节", "细节", level=2)
    parent.children.append(child)
    md = parent.to_markdown()
    assert "# 第一章" in md
    assert "## 第一节" in md
    print(f"  ✓ 嵌套章节正常")

    d = sec.to_dict()
    assert d["title"] == "安装指南"
    print(f"  ✓ to_dict() 正常")

    print_result("DocSection", True)
    return True


def test_param_info() -> bool:
    """测试参数信息."""
    print_header("测试3: ParamInfo 参数信息")

    p1 = ParamInfo(name="x", type_hint="int", description="数字", is_optional=False)
    md = p1.to_markdown()
    assert "**x**" in md and "int" in md
    print(f"  ✓ 必选参数: {md}")

    p2 = ParamInfo(name="name", type_hint="str", description="名称", default='""', is_optional=True)
    md = p2.to_markdown()
    assert "optional" in md
    print(f"  ✓ 可选参数: {md}")

    print_result("ParamInfo", True)
    return True


def test_api_entry() -> bool:
    """测试API文档条目."""
    print_header("测试4: APIEntry API文档条目")

    entry = create_api_entry(
        name="calculate",
        signature="def calculate(x: int, y: int) -> int",
        description="计算两个数的和",
        returns="int: 两数之和",
    )
    entry.params = [
        ParamInfo(name="x", type_hint="int", description="第一个数"),
        ParamInfo(name="y", type_hint="int", description="第二个数"),
    ]
    entry.examples = ["result = calculate(1, 2)  # returns 3"]

    md = entry.to_markdown()
    assert "### calculate" in md
    assert "def calculate" in md
    assert "**x**" in md
    assert "Returns:" in md
    assert "Examples:" in md
    print(f"  ✓ Markdown生成包含签名/参数/返回/示例")

    d = entry.to_dict()
    assert d["name"] == "calculate"
    assert len(d["params"]) == 2
    print(f"  ✓ to_dict() 正常")

    print_result("APIEntry", True)
    return True


def test_changelog_entry() -> bool:
    """测试变更日志条目."""
    print_header("测试5: ChangelogEntry 变更日志")

    entries = [
        create_changelog("1.0.0", ChangeType.ADDED, "初始版本发布"),
        create_changelog("1.0.1", ChangeType.FIXED, "修复计算错误"),
        create_changelog("1.1.0", ChangeType.CHANGED, "重构API接口"),
        create_changelog("2.0.0", ChangeType.BREAKING, "不兼容的API变更"),
    ]

    for entry in entries:
        md = entry.to_markdown()
        assert entry.change_type.value in md
        print(f"  ✓ {entry.version} [{entry.change_type.value}]: {entry.description[:30]}")

    print_result("ChangelogEntry", True)
    return True


def test_document() -> bool:
    """测试完整文档."""
    print_header("测试6: Document 完整文档")

    doc = Document(
        metadata=DocMetadata(
            title="测试项目",
            version="1.0.0",
            author="Team",
            description="一个测试项目",
            doc_type=DocType.README,
        ),
        sections=[
            create_section("简介", "这是项目简介", level=2),
            create_section("安装", "pip install test", level=2),
        ],
        api_entries=[
            create_api_entry("func_a", "def func_a():", "函数A说明"),
        ],
        changelog=[
            create_changelog("1.0.0", ChangeType.ADDED, "首次发布"),
        ],
    )

    md = doc.to_markdown()
    assert "# 测试项目" in md
    assert "一个测试项目" in md
    assert "## 简介" in md
    assert "### func_a" in md
    assert "变更日志" in md
    print(f"  ✓ 完整Markdown生成正常")

    assert doc.word_count > 0
    print(f"  ✓ 字数统计: {doc.word_count}")

    d = doc.to_dict()
    assert d["metadata"]["title"] == "测试项目"
    assert len(d["sections"]) == 2
    print(f"  ✓ to_dict() 正常")

    print_result("Document", True)
    return True


def test_ast_extractor() -> bool:
    """测试AST文档提取."""
    print_header("测试7: ASTDocExtractor AST提取")

    source = '''"""模块文档字符串.

这是一个示例模块，展示文档提取功能。
"""

import math
from typing import List


def add(x: int, y: int = 0) -> int:
    """计算两个数的和.

    Args:
        x: 第一个数
        y: 第二个数

    Returns:
        两数之和
    """
    return x + y


class Calculator:
    """计算器类.

    提供基本数学运算功能。
    """

    def multiply(self, a, b):
        """乘法运算."""
        return a * b
'''

    extractor = ASTDocExtractor()
    info = extractor.extract_module(source, "calculator.py")

    assert "示例模块" in info["docstring"]
    print(f"  ✓ 模块文档: {info['docstring'][:20]}...")

    assert len(info["functions"]) >= 1
    func = info["functions"][0]
    assert func.name == "add"
    assert "x" in [p.name for p in func.params]
    print(f"  ✓ 函数提取: {func.name}, 参数={[p.name for p in func.params]}")

    assert len(info["classes"]) >= 1
    cls = info["classes"][0]
    assert cls.name == "Calculator"
    assert "multiply" in cls.description
    print(f"  ✓ 类提取: {cls.name}")

    assert len(info["imports"]) >= 2
    print(f"  ✓ 导入提取: {len(info['imports'])}个")

    print_result("ASTDocExtractor", True)
    return True


def test_generate_readme() -> bool:
    """测试README生成."""
    print_header("测试8: README生成")

    gen = DocGenerator(project_name="MyProject", version="1.0.0")
    doc = gen.generate_readme(
        description="一个强大的Python工具库",
        features=["高性能", "易使用", "可扩展"],
        install_cmd="pip install myproject",
        usage_example="from myproject import tool\ntool.run()",
    )

    md = doc.to_markdown()
    assert "# MyProject" in md
    assert "强大的Python工具库" in md
    assert "高性能" in md
    assert "pip install" in md
    assert "from myproject" in md
    print(f"  ✓ README生成正常")

    # 便捷函数
    quick_md = generate_readme("Quick", description="快速测试")
    assert "# Quick" in quick_md
    print(f"  ✓ 便捷函数正常")

    print_result("README生成", True)
    return True


def test_generate_api_doc() -> bool:
    """测试API文档生成."""
    print_header("测试9: API文档生成")

    source = '''
def greet(name: str, greeting: str = "Hello") -> str:
    """生成问候语.

    Args:
        name: 名字
        greeting: 问候语
    """
    return f"{greeting}, {name}!"
'''

    gen = DocGenerator()
    doc = gen.generate_api_doc(source, "greeter.py")

    md = doc.to_markdown()
    assert "### greet" in md
    assert "def greet" in md
    assert "**name**" in md
    print(f"  ✓ API文档生成正常")

    # 便捷函数
    quick_md = generate_api_doc(source, "greeter.py")
    assert "### greet" in quick_md
    print(f"  ✓ 便捷函数正常")

    print_result("API文档生成", True)
    return True


def test_generate_changelog() -> bool:
    """测试变更日志生成."""
    print_header("测试10: 变更日志生成")

    gen = DocGenerator()
    doc = gen.generate_changelog([
        create_changelog("1.0.0", ChangeType.ADDED, "初始发布"),
        create_changelog("1.0.1", ChangeType.FIXED, "修复Bug"),
        create_changelog("1.1.0", ChangeType.ADDED, "新增功能"),
    ])

    md = doc.to_markdown()
    assert "## 变更日志" in md
    assert "added" in md.lower()
    assert "fixed" in md.lower()
    print(f"  ✓ 变更日志生成正常")

    print_result("变更日志生成", True)
    return True


def test_extract_docstring() -> bool:
    """测试文档字符串提取."""
    print_header("测试11: extract_docstring")

    source = '"""这是模块文档."""\n\ndef foo(): pass\n'
    result = extract_docstring(source)
    assert result == "这是模块文档."
    print(f"  ✓ 提取结果: {result}")

    source2 = "# 没有文档字符串\ndef bar(): pass\n"
    result2 = extract_docstring(source2)
    assert result2 == ""
    print(f"  ✓ 无文档字符串: '{result2}'")

    print_result("extract_docstring", True)
    return True


def main() -> int:
    print("\n" + "="*60)
    print("  第24阶段验收: 文档生成器 (Documentation Generator)")
    print("="*60)

    tests = [
        test_enums,
        test_doc_section,
        test_param_info,
        test_api_entry,
        test_changelog_entry,
        test_document,
        test_ast_extractor,
        test_generate_readme,
        test_generate_api_doc,
        test_generate_changelog,
        test_extract_docstring,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"  验收结果: {passed} 通过, {failed} 失败")
    print("="*60)

    if failed == 0:
        print("\n  ✓ 第24阶段验收通过！")
        print("\n  实现功能:")
        print("    - DocType: 8种文档类型")
        print("    - DocFormat: 4种文档格式")
        print("    - ChangeType: 7种变更类型")
        print("    - DocSection: 嵌套章节 + Markdown生成")
        print("    - ParamInfo: 参数信息（类型/默认值/可选）")
        print("    - APIEntry: API文档条目（签名/参数/返回/示例）")
        print("    - ChangelogEntry: 变更日志条目")
        print("    - Document: 完整文档（章节+API+变更日志+目录）")
        print("    - ASTDocExtractor: AST解析提取函数/类/模块文档")
        print("    - DocGenerator: README/API文档/变更日志/模块文档生成")
        print("="*60)
        return 0
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
