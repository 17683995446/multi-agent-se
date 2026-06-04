"""Documenter Agent - 第38阶段.

文档Agent - 负责文档生成、维护与更新.

职责:
- 生成项目README文档
- 生成API接口文档
- 生成架构设计文档
- 生成代码注释和文档字符串
- 维护变更日志
- 追踪文档版本历史
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid
import re
from datetime import datetime

from multi_agent_se.agents.registry.metadata import AgentRole, AgentCapability
from multi_agent_se.agents.runtime.base_agent import BaseAgentImpl, AgentContext, TaskResult


class DocType(Enum):
    """文档类型."""
    README = "readme"               # 项目README
    API = "api"                     # API文档
    ARCHITECTURE = "architecture"   # 架构文档
    USER_GUIDE = "user_guide"       # 用户指南
    DEVELOPER_GUIDE = "dev_guide"   # 开发者指南
    CHANGELOG = "changelog"         # 变更日志
    LICENSE = "license"             # 许可证
    CONTRIBUTING = "contributing"   # 贡献指南
    CODE_OF_CONDUCT = "coc"         # 行为准则
    DOCSTRING = "docstring"         # 文档字符串


class DocFormat(Enum):
    """文档格式."""
    MARKDOWN = "markdown"           # Markdown
    RST = "rst"                     # reStructuredText
    HTML = "html"                   # HTML
    PLAIN = "plain"                 # 纯文本
    YAML = "yaml"                   # YAML
    JSON = "json"                   # JSON


class DocStatus(Enum):
    """文档状态."""
    DRAFT = "draft"                 # 草稿
    REVIEW = "review"               # 审核中
    PUBLISHED = "published"         # 已发布
    OUTDATED = "outdated"           # 已过时
    DEPRECATED = "deprecated"       # 已弃用


@dataclass
class DocSection:
    """文档章节."""
    section_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    content: str = ""
    level: int = 1  # 标题级别 1-6
    order: int = 0  # 排序
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "level": self.level,
            "order": self.order,
            "content_length": len(self.content),
        }


@dataclass
class DocMetadata:
    """文档元数据."""
    title: str = ""
    description: str = ""
    author: str = ""
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description[:100],
            "author": self.author,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
        }


@dataclass
class GeneratedDoc:
    """生成的文档."""
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    doc_type: DocType = DocType.README
    doc_format: DocFormat = DocFormat.MARKDOWN
    
    # 文件信息
    file_path: str = ""
    file_name: str = ""
    
    # 内容
    metadata: DocMetadata = field(default_factory=DocMetadata)
    sections: List[DocSection] = field(default_factory=list)
    content: str = ""  # 完整内容
    
    # 状态
    status: DocStatus = DocStatus.DRAFT
    
    # 统计
    word_count: int = 0
    line_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type.value,
            "doc_format": self.doc_format.value,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "metadata": self.metadata.to_dict(),
            "sections_count": len(self.sections),
            "status": self.status.value,
            "word_count": self.word_count,
            "line_count": self.line_count,
        }


@dataclass
class DocumentationResult:
    """文档生成结果."""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # 生成的文档
    documents: List[GeneratedDoc] = field(default_factory=list)
    
    # 统计
    total_docs: int = 0
    total_words: int = 0
    total_lines: int = 0
    
    # 摘要
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "total_docs": len(self.documents),
            "total_words": self.total_words,
            "total_lines": self.total_lines,
            "documents": [d.to_dict() for d in self.documents],
            "summary": self.summary[:100],
        }


class DocumenterAgent(BaseAgentImpl):
    """文档Agent - 文档生成与维护.
    
    8大正交角色Agent之一，负责生成各类项目文档，
    包括README、API文档、架构文档等。
    """
    
    AGENT_ROLE = AgentRole.DOCUMENTER
    AGENT_CAPABILITIES = [
        AgentCapability.DOCUMENTATION,
        AgentCapability.FILE_OPERATION,
    ]
    AGENT_DESCRIPTION = "文档Agent - 负责文档生成、维护与更新"
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict] = None) -> None:
        super().__init__(agent_id, config)
        self._doc_history: List[DocumentationResult] = []
        self._doc_templates: Dict[DocType, str] = self._load_doc_templates()
        self._default_author: str = config.get("author", "Multi-Agent SE System") if config else "Multi-Agent SE System"
    
    def process(self, context: AgentContext) -> TaskResult:
        """处理文档生成任务.
        
        Args:
            context: Agent执行上下文
            
        Returns:
            任务执行结果
        """
        input_data = context.input_data
        
        # 输入类型验证
        if not isinstance(input_data, dict):
            return TaskResult(
                success=False,
                error_message=f"输入数据必须是字典类型，实际为 {type(input_data).__name__}",
            )
        
        # 获取参数
        doc_type_str = input_data.get("doc_type", "readme")
        doc_types = input_data.get("doc_types", [doc_type_str])
        target = input_data.get("target", "project")
        code = input_data.get("code", "")
        architecture = input_data.get("architecture", {})
        
        # 1. 创建结果
        result = DocumentationResult()
        
        # 2. 生成文档
        for dt_str in doc_types:
            try:
                doc_type = DocType(dt_str)
                doc = self._generate_document(doc_type, target, code, architecture)
                result.documents.append(doc)
            except ValueError:
                continue
        
        if not result.documents:
            return TaskResult(
                success=False,
                error_message="未生成任何文档",
            )
        
        # 3. 计算统计
        self._calculate_statistics(result)
        
        # 4. 生成总结
        result.summary = self._generate_summary(result)
        
        # 5. 保存历史
        self._doc_history.append(result)
        
        return TaskResult(
            success=True,
            output=result.to_dict(),
            artifacts={
                "result": result,
                "documents": result.documents,
            },
        )
    
    def _generate_document(
        self,
        doc_type: DocType,
        target: str,
        code: str,
        architecture: Dict[str, Any],
    ) -> GeneratedDoc:
        """生成单个文档."""
        doc = GeneratedDoc(
            doc_type=doc_type,
            file_path=self._get_file_path(doc_type),
            file_name=self._get_file_name(doc_type),
            metadata=DocMetadata(
                title=self._get_doc_title(doc_type, target),
                description=f"{target} 的{self._get_doc_type_name(doc_type)}",
                author=self._default_author,
            ),
        )
        
        # 根据文档类型生成内容
        generators = {
            DocType.README: self._generate_readme,
            DocType.API: self._generate_api_doc,
            DocType.ARCHITECTURE: self._generate_architecture_doc,
            DocType.CHANGELOG: self._generate_changelog,
            DocType.USER_GUIDE: self._generate_user_guide,
            DocType.DEVELOPER_GUIDE: self._generate_dev_guide,
        }
        
        generator = generators.get(doc_type, self._generate_generic_doc)
        doc.content = generator(target, code, architecture)
        doc.sections = self._parse_sections(doc.content)
        doc.word_count = len(doc.content.split())
        doc.line_count = len(doc.content.splitlines())
        doc.status = DocStatus.PUBLISHED
        
        return doc
    
    def _generate_readme(self, target: str, code: str, architecture: Dict) -> str:
        """生成README文档."""
        sections = [
            f"# {target}",
            "",
            f"{target} 项目说明文档。",
            "",
            "## 功能特性",
            "",
            self._extract_features(code),
            "",
            "## 安装",
            "",
            "```bash",
            f"pip install {target.lower().replace(' ', '-')}",
            "```",
            "",
            "## 快速开始",
            "",
            "```python",
            self._generate_quick_start(code),
            "```",
            "",
            "## 项目结构",
            "",
            self._generate_structure(architecture),
            "",
            "## 贡献指南",
            "",
            "欢迎提交Issue和Pull Request。",
            "",
            "## 许可证",
            "",
            "MIT License",
        ]
        return "\n".join(sections)
    
    def _generate_api_doc(self, target: str, code: str, architecture: Dict) -> str:
        """生成API文档."""
        sections = [
            f"# {target} API 文档",
            "",
            "## 概述",
            "",
            f"本文档描述 {target} 的 API 接口。",
            "",
            "## 类和方法",
            "",
        ]
        
        # 提取类和方法
        classes = self._extract_classes_from_code(code)
        for class_name, methods in classes.items():
            sections.extend([
                f"### {class_name}",
                "",
                f"**类 {class_name}**",
                "",
                "#### 方法",
                "",
            ])
            for method in methods:
                sections.extend([
                    f"- `{method}(**kwargs)`",
                    "",
                ])
            sections.append("")
        
        if not classes:
            sections.extend([
                "### 函数",
                "",
            ])
            functions = self._extract_functions_from_code(code)
            for func in functions:
                sections.append(f"- `{func}(**args)`")
        
        return "\n".join(sections)
    
    def _generate_architecture_doc(self, target: str, code: str, architecture: Dict) -> str:
        """生成架构文档."""
        sections = [
            f"# {target} 架构设计",
            "",
            "## 架构概述",
            "",
            f"{target} 采用分层架构设计，遵循高内聚低耦合原则。",
            "",
            "## 系统分层",
            "",
        ]
        
        layers = architecture.get("layers", ["输入层", "处理层", "输出层"])
        for i, layer in enumerate(layers, 1):
            sections.extend([
                f"### {i}. {layer}",
                "",
                f"负责{layer}相关功能。",
                "",
            ])
        
        sections.extend([
            "## 组件说明",
            "",
        ])
        
        components = architecture.get("components", [])
        for comp in components:
            name = comp.get("name", "Unknown")
            desc = comp.get("responsibility", "")
            sections.extend([
                f"### {name}",
                "",
                desc,
                "",
            ])
        
        sections.extend([
            "## 数据流",
            "",
            "```",
            "输入 -> 处理 -> 输出",
            "```",
            "",
        ])
        
        return "\n".join(sections)
    
    def _generate_changelog(self, target: str, code: str, architecture: Dict) -> str:
        """生成变更日志."""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"""# 变更日志

所有重要变更都将记录在此文件中。

## [1.0.0] - {today}

### 新增
- 初始版本发布
- 核心功能实现

### 变更
- 无

### 修复
- 无

## [0.1.0] - {today}

### 新增
- 项目初始化
- 基础架构搭建
"""
    
    def _generate_user_guide(self, target: str, code: str, architecture: Dict) -> str:
        """生成用户指南."""
        return f"""# {target} 用户指南

## 简介

欢迎使用 {target}！本指南将帮助您快速上手。

## 安装

### 环境要求

- Python 3.8+
- pip

### 安装步骤

```bash
pip install {target.lower().replace(' ', '-')}
```

## 基本使用

### 导入模块

```python
import {target.lower().replace(' ', '_')}
```

### 第一个示例

```python
# 创建实例
obj = {target.title().replace(' ', '')}()

# 使用功能
result = obj.process()
```

## 常见问题

### Q: 如何获取帮助？

A: 请参考API文档或提交Issue。

## 获取支持

如有问题，请联系支持团队。
"""
    
    def _generate_dev_guide(self, target: str, code: str, architecture: Dict) -> str:
        """生成开发者指南."""
        return f"""# {target} 开发者指南

## 开发环境搭建

### 克隆仓库

```bash
git clone https://github.com/example/{target.lower().replace(' ', '-')}.git
cd {target.lower().replace(' ', '-')}
```

### 安装依赖

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 项目结构

```
{target.lower().replace(' ', '_')}/
├── src/           # 源代码
├── tests/         # 测试代码
├── docs/          # 文档
└── README.md      # 项目说明
```

## 开发流程

1. 创建功能分支
2. 编写代码和测试
3. 运行测试确保通过
4. 提交Pull Request

## 代码规范

- 遵循PEP 8
- 使用类型注解
- 编写文档字符串

## 测试

```bash
pytest tests/
```

## 提交规范

- feat: 新功能
- fix: 修复
- docs: 文档
- test: 测试
"""
    
    def _generate_generic_doc(self, target: str, code: str, architecture: Dict) -> str:
        """生成通用文档."""
        return f"""# {target} 文档

## 概述

这是 {target} 的文档。

## 内容

文档内容待补充。

---

生成时间: {datetime.now().isoformat()}
"""
    
    def _extract_features(self, code: str) -> str:
        """提取功能特性."""
        features = []
        
        # 从代码中提取类名作为功能
        classes = re.findall(r'class\s+(\w+)', code)
        for cls in classes[:3]:
            features.append(f"- 支持 {cls} 功能")
        
        # 从代码中提取函数作为功能
        functions = re.findall(r'def\s+(\w+)\s*\(', code)
        for func in functions[:3]:
            if not func.startswith('_'):
                features.append(f"- 提供 {func} 功能")
        
        return "\n".join(features) if features else "- 核心功能实现\n- 模块化设计\n- 易于扩展"
    
    def _generate_quick_start(self, code: str) -> str:
        """生成快速开始示例."""
        classes = re.findall(r'class\s+(\w+)', code)
        if classes:
            cls = classes[0]
            return f"""from mymodule import {cls}

# 创建实例
obj = {cls}()

# 使用功能
result = obj.process()
print(result)"""
        
        functions = re.findall(r'def\s+(\w+)\s*\(', code)
        if functions and not functions[0].startswith('_'):
            return f"""from mymodule import {functions[0]}

# 调用函数
result = {functions[0]}()
print(result)"""
        
        return "# 示例代码\nprint('Hello World')"
    
    def _generate_structure(self, architecture: Dict) -> str:
        """生成项目结构."""
        components = architecture.get("components", [])
        if not components:
            return """```
project/
├── src/
├── tests/
└── docs/
```"""
        
        lines = ["```", "project/"]
        for comp in components:
            name = comp.get("name", "unknown")
            lines.append(f"├── {name.lower()}/")
        lines.append("```")
        return "\n".join(lines)
    
    def _extract_classes_from_code(self, code: str) -> Dict[str, List[str]]:
        """从代码中提取类和方法."""
        classes: Dict[str, List[str]] = {}
        current_class = None
        
        for line in code.splitlines():
            class_match = re.match(r'class\s+(\w+)', line)
            if class_match:
                current_class = class_match.group(1)
                classes[current_class] = []
            
            method_match = re.match(r'\s+def\s+(\w+)\s*\(', line)
            if method_match and current_class:
                method_name = method_match.group(1)
                if not method_name.startswith('_') or method_name == '__init__':
                    classes[current_class].append(method_name)
        
        return classes
    
    def _extract_functions_from_code(self, code: str) -> List[str]:
        """从代码中提取独立函数."""
        functions = []
        in_class = False
        
        for line in code.splitlines():
            if line.strip().startswith('class '):
                in_class = True
            elif in_class and line.strip() and not line.startswith(' '):
                in_class = False
            
            if not in_class:
                func_match = re.match(r'def\s+(\w+)\s*\(', line.strip())
                if func_match:
                    func_name = func_match.group(1)
                    if not func_name.startswith('_'):
                        functions.append(func_name)
        
        return functions
    
    def _parse_sections(self, content: str) -> List[DocSection]:
        """解析文档章节."""
        sections: List[DocSection] = []
        lines = content.splitlines()
        current_content: List[str] = []
        current_title = ""
        current_level = 1
        order = 0
        
        for line in lines:
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                # 保存上一个章节
                if current_title:
                    sections.append(DocSection(
                        title=current_title,
                        content="\n".join(current_content).strip(),
                        level=current_level,
                        order=order,
                    ))
                    order += 1
                
                current_level = len(header_match.group(1))
                current_title = header_match.group(2)
                current_content = []
            else:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_title:
            sections.append(DocSection(
                title=current_title,
                content="\n".join(current_content).strip(),
                level=current_level,
                order=order,
            ))
        
        return sections
    
    def _get_file_path(self, doc_type: DocType) -> str:
        """获取文档文件路径."""
        paths = {
            DocType.README: "./",
            DocType.API: "docs/",
            DocType.ARCHITECTURE: "docs/",
            DocType.CHANGELOG: "./",
            DocType.USER_GUIDE: "docs/",
            DocType.DEVELOPER_GUIDE: "docs/",
        }
        return paths.get(doc_type, "docs/")
    
    def _get_file_name(self, doc_type: DocType) -> str:
        """获取文档文件名."""
        names = {
            DocType.README: "README.md",
            DocType.API: "API.md",
            DocType.ARCHITECTURE: "ARCHITECTURE.md",
            DocType.CHANGELOG: "CHANGELOG.md",
            DocType.USER_GUIDE: "USER_GUIDE.md",
            DocType.DEVELOPER_GUIDE: "DEVELOPER_GUIDE.md",
        }
        return names.get(doc_type, f"{doc_type.value.upper()}.md")
    
    def _get_doc_title(self, doc_type: DocType, target: str) -> str:
        """获取文档标题."""
        titles = {
            DocType.README: f"{target}",
            DocType.API: f"{target} API Documentation",
            DocType.ARCHITECTURE: f"{target} Architecture",
            DocType.CHANGELOG: "Changelog",
            DocType.USER_GUIDE: f"{target} User Guide",
            DocType.DEVELOPER_GUIDE: f"{target} Developer Guide",
        }
        return titles.get(doc_type, f"{target} Documentation")
    
    def _get_doc_type_name(self, doc_type: DocType) -> str:
        """获取文档类型名称."""
        names = {
            DocType.README: "项目说明文档",
            DocType.API: "API接口文档",
            DocType.ARCHITECTURE: "架构设计文档",
            DocType.CHANGELOG: "变更日志",
            DocType.USER_GUIDE: "用户指南",
            DocType.DEVELOPER_GUIDE: "开发者指南",
        }
        return names.get(doc_type, "文档")
    
    def _calculate_statistics(self, result: DocumentationResult) -> None:
        """计算统计信息."""
        result.total_docs = len(result.documents)
        result.total_words = sum(d.word_count for d in result.documents)
        result.total_lines = sum(d.line_count for d in result.documents)
    
    def _generate_summary(self, result: DocumentationResult) -> str:
        """生成总结."""
        doc_types = [d.doc_type.value for d in result.documents]
        return (
            f"成功生成 {result.total_docs} 个文档 "
            f"({', '.join(doc_types)}), "
            f"共 {result.total_words} 词, {result.total_lines} 行"
        )
    
    def _load_doc_templates(self) -> Dict[DocType, str]:
        """加载文档模板."""
        return {
            DocType.README: "standard",
            DocType.API: "openapi",
            DocType.ARCHITECTURE: "c4",
        }
    
    def get_doc_history(self) -> List[DocumentationResult]:
        """获取文档生成历史."""
        return self._doc_history.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息."""
        total_runs = len(self._doc_history)
        if total_runs == 0:
            return {
                "total_runs": 0,
                "total_docs_generated": 0,
                "avg_docs_per_run": 0.0,
            }
        
        total_docs = sum(r.total_docs for r in self._doc_history)
        
        # 按类型统计
        type_counts: Dict[str, int] = {}
        for result in self._doc_history:
            for doc in result.documents:
                dt = doc.doc_type.value
                type_counts[dt] = type_counts.get(dt, 0) + 1
        
        return {
            "total_runs": total_runs,
            "total_docs_generated": total_docs,
            "avg_docs_per_run": total_docs / total_runs,
            "total_words_generated": sum(r.total_words for r in self._doc_history),
            "doc_type_distribution": type_counts,
        }
