"""文档模型定义 - 阶段24.

定义文档生成的数据结构：
- 文档类型
- 文档章节
- 文档元数据
- API文档条目
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DocType(Enum):
    """文档类型."""
    README = "readme"              # 项目说明
    API = "api"                    # API文档
    CHANGELOG = "changelog"        # 变更日志
    ARCHITECTURE = "architecture"  # 架构文档
    GUIDE = "guide"                # 使用指南
    MODULE = "module"              # 模块文档
    CLASS = "class"                # 类文档
    FUNCTION = "function"          # 函数文档


class DocFormat(Enum):
    """文档格式."""
    MARKDOWN = "markdown"
    RST = "rst"
    HTML = "html"
    JSON = "json"


class ChangeType(Enum):
    """变更类型."""
    ADDED = "added"
    CHANGED = "changed"
    FIXED = "fixed"
    DEPRECATED = "deprecated"
    REMOVED = "removed"
    SECURITY = "security"
    BREAKING = "breaking"


# ========== 文档章节 ==========

@dataclass
class DocSection:
    """文档章节."""
    title: str = ""
    level: int = 1              # 标题层级 (1-6)
    content: str = ""            # 正文内容（Markdown格式）
    order: int = 0               # 排序序号
    children: List["DocSection"] = field(default_factory=list)

    def to_markdown(self) -> str:
        """转换为Markdown."""
        prefix = "#" * self.level
        parts = [f"{prefix} {self.title}"]
        if self.content:
            parts.append(self.content)
        for child in self.children:
            parts.append(child.to_markdown())
        return "\n\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "level": self.level,
            "content": self.content,
            "order": self.order,
            "children": [c.to_dict() for c in self.children],
        }


# ========== API文档条目 ==========

@dataclass
class ParamInfo:
    """函数/方法参数信息."""
    name: str = ""
    type_hint: str = ""
    description: str = ""
    default: str = ""
    is_optional: bool = False

    def to_markdown(self) -> str:
        opt = ", optional" if self.is_optional else ""
        default = f" (default: {self.default})" if self.default else ""
        return f"- **{self.name}** ({self.type_hint}{opt}){default}: {self.description}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type_hint": self.type_hint,
            "description": self.description,
            "default": self.default,
            "is_optional": self.is_optional,
        }


@dataclass
class APIEntry:
    """API文档条目."""
    name: str = ""
    doc_type: DocType = DocType.FUNCTION
    signature: str = ""          # 函数签名
    description: str = ""         # 简要描述
    params: List[ParamInfo] = field(default_factory=list)
    returns: str = ""             # 返回值说明
    raises: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    module: str = ""              # 所属模块
    since: str = ""               # 从哪个版本开始
    deprecated: bool = False
    deprecation_note: str = ""

    def to_markdown(self) -> str:
        """转换为Markdown."""
        parts = []
        parts.append(f"### {self.name}\n")
        if self.signature:
            parts.append(f"```python\n{self.signature}\n```\n")
        if self.deprecated:
            note = self.deprecation_note or "This API is deprecated."
            parts.append(f"> **Deprecated**: {note}\n")
        if self.description:
            parts.append(f"{self.description}\n")
        if self.params:
            parts.append("**Parameters:**\n")
            for p in self.params:
                parts.append(p.to_markdown())
            parts.append("")
        if self.returns:
            parts.append(f"**Returns:** {self.returns}\n")
        if self.raises:
            parts.append(f"**Raises:** {', '.join(self.raises)}\n")
        if self.examples:
            parts.append("**Examples:**\n")
            for ex in self.examples:
                parts.append(f"```python\n{ex}\n```\n")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "doc_type": self.doc_type.value,
            "signature": self.signature,
            "description": self.description,
            "params": [p.to_dict() for p in self.params],
            "returns": self.returns,
            "raises": self.raises,
            "examples": self.examples,
            "module": self.module,
            "since": self.since,
            "deprecated": self.deprecated,
        }


# ========== 变更日志条目 ==========

@dataclass
class ChangelogEntry:
    """变更日志条目."""
    version: str = ""
    date: str = ""
    change_type: ChangeType = ChangeType.ADDED
    description: str = ""
    details: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        emoji_map = {
            ChangeType.ADDED: "✨",
            ChangeType.CHANGED: "🔄",
            ChangeType.FIXED: "🐛",
            ChangeType.DEPRECATED: "⚠️",
            ChangeType.REMOVED: "🗑️",
            ChangeType.SECURITY: "🔒",
            ChangeType.BREAKING: "💥",
        }
        emoji = emoji_map.get(self.change_type, "")
        parts = [f"- {emoji} **{self.change_type.value}**: {self.description}"]
        for detail in self.details:
            parts.append(f"  - {detail}")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "date": self.date,
            "change_type": self.change_type.value,
            "description": self.description,
            "details": self.details,
        }


# ========== 文档元数据 ==========

@dataclass
class DocMetadata:
    """文档元数据."""
    title: str = ""
    version: str = ""
    author: str = ""
    date: str = ""
    project_name: str = ""
    description: str = ""
    doc_type: DocType = DocType.README
    format: DocFormat = DocFormat.MARKDOWN
    keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "version": self.version,
            "author": self.author,
            "date": self.date,
            "project_name": self.project_name,
            "description": self.description,
            "doc_type": self.doc_type.value,
            "format": self.format.value,
            "keywords": self.keywords,
        }


# ========== 完整文档 ==========

@dataclass
class Document:
    """完整文档."""
    metadata: DocMetadata = field(default_factory=DocMetadata)
    sections: List[DocSection] = field(default_factory=list)
    api_entries: List[APIEntry] = field(default_factory=list)
    changelog: List[ChangelogEntry] = field(default_factory=list)
    raw_content: str = ""

    def to_markdown(self) -> str:
        """生成完整Markdown文档."""
        parts = []

        # 标题
        if self.metadata.title:
            parts.append(f"# {self.metadata.title}\n")

        # 元信息
        meta = self.metadata
        if meta.description:
            parts.append(f"{meta.description}\n")
        if meta.version or meta.date or meta.author:
            info_items = []
            if meta.version:
                info_items.append(f"Version: {meta.version}")
            if meta.date:
                info_items.append(f"Date: {meta.date}")
            if meta.author:
                info_items.append(f"Author: {meta.author}")
            parts.append(" | ".join(info_items) + "\n")

        # 目录（仅当有多个章节时）
        if len(self.sections) > 1:
            parts.append("## 目录\n")
            for sec in self.sections:
                indent = "  " * (sec.level - 1)
                parts.append(f"{indent}- [{sec.title}](#{sec.title.lower().replace(' ', '-')})")
            parts.append("")

        # 章节
        for sec in self.sections:
            parts.append(sec.to_markdown())

        # API文档
        if self.api_entries:
            parts.append("## API 参考\n")
            for entry in self.api_entries:
                parts.append(entry.to_markdown())

        # 变更日志
        if self.changelog:
            parts.append("## 变更日志\n")
            for entry in self.changelog:
                parts.append(entry.to_markdown())
            parts.append("")

        return "\n\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "sections": [s.to_dict() for s in self.sections],
            "api_entries": [a.to_dict() for a in self.api_entries],
            "changelog": [c.to_dict() for c in self.changelog],
        }

    @property
    def word_count(self) -> int:
        """文档字数估算."""
        text = self.to_markdown()
        return len(text.split())


# ========== 便捷函数 ==========

def create_section(title: str, content: str = "", level: int = 2) -> DocSection:
    """创建章节的便捷函数."""
    return DocSection(title=title, content=content, level=level)


def create_api_entry(
    name: str,
    signature: str = "",
    description: str = "",
    returns: str = "",
) -> APIEntry:
    """创建API条目的便捷函数."""
    return APIEntry(
        name=name,
        signature=signature,
        description=description,
        returns=returns,
    )


def create_changelog(
    version: str,
    change_type: ChangeType,
    description: str,
) -> ChangelogEntry:
    """创建变更日志条目的便捷函数."""
    return ChangelogEntry(
        version=version,
        change_type=change_type,
        description=description,
        date=datetime.now().strftime("%Y-%m-%d"),
    )
