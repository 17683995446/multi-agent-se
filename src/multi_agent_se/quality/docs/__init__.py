"""文档生成器 - 阶段24.

从Python源码自动生成文档：
- AST解析提取函数/类/模块文档
- README生成
- API文档生成
- 变更日志生成
"""

from multi_agent_se.quality.docs.doc_models import (
    DocType,
    DocFormat,
    ChangeType,
    DocSection,
    ParamInfo,
    APIEntry,
    ChangelogEntry,
    DocMetadata,
    Document,
    create_section,
    create_api_entry,
    create_changelog,
)

from multi_agent_se.quality.docs.doc_generator import (
    ASTDocExtractor,
    DocGenerator,
    generate_readme,
    generate_api_doc,
    extract_docstring,
)

__all__ = [
    # 模型
    "DocType",
    "DocFormat",
    "ChangeType",
    "DocSection",
    "ParamInfo",
    "APIEntry",
    "ChangelogEntry",
    "DocMetadata",
    "Document",
    # 便捷函数
    "create_section",
    "create_api_entry",
    "create_changelog",
    # 生成器
    "ASTDocExtractor",
    "DocGenerator",
    "generate_readme",
    "generate_api_doc",
    "extract_docstring",
]
