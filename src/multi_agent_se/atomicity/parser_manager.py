"""Tree-sitter解析器管理模块 - 阶段6.

复用Tree-sitter开源内核，提供统一解析器创建/缓存接口
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter as ts
import tree_sitter_python as tspython


@dataclass
class ParseResult:
    """解析结果."""
    tree: ts.Tree
    source: bytes
    language: str
    root_node: ts.Node = field(init=False)
    
    def __post_init__(self) -> None:
        self.root_node = self.tree.root_node
    
    def get_source_text(self, node: ts.Node) -> str:
        """获取节点对应的源码文本."""
        return self.source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


@dataclass
class NodeInfo:
    """节点信息."""
    node_type: str
    text: str
    start_line: int
    start_col: int
    end_line: int
    end_col: int
    children_count: int
    parent_type: Optional[str] = None


class ParserManager:
    """解析器管理器.
    
    管理多语言解析器的创建与缓存
    """
    
    def __init__(self) -> None:
        self._languages: Dict[str, ts.Language] = {}
        self._parsers: Dict[str, ts.Parser] = {}
        self._register_builtin_languages()
    
    def _register_builtin_languages(self) -> None:
        """注册内置语言支持."""
        py_language = ts.Language(tspython.language())
        self._languages["python"] = py_language
        self._parsers["python"] = ts.Parser(py_language)
    
    def register_language(self, name: str, language: ts.Language) -> None:
        """注册新语言.
        
        Args:
            name: 语言名称
            language: Language对象
        """
        self._languages[name] = language
        self._parsers[name] = ts.Parser(language)
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表."""
        return list(self._languages.keys())
    
    def parse(self, source: str, language: str = "python") -> ParseResult:
        """解析源码.
        
        Args:
            source: 源码字符串
            language: 语言名称
            
        Returns:
            ParseResult
        """
        if language not in self._parsers:
            raise ValueError(f"不支持的语言: {language}，支持: {self.get_supported_languages()}")
        
        source_bytes = source.encode("utf-8")
        tree = self._parsers[language].parse(source_bytes)
        return ParseResult(tree=tree, source=source_bytes, language=language)
    
    def parse_file(self, file_path: str, language: Optional[str] = None) -> ParseResult:
        """解析文件.
        
        Args:
            file_path: 文件路径
            language: 语言名称（None则根据扩展名推断）
            
        Returns:
            ParseResult
        """
        path = Path(file_path)
        if language is None:
            language = self._detect_language(path)
        
        source = path.read_text(encoding="utf-8")
        return self.parse(source, language)
    
    def _detect_language(self, path: Path) -> str:
        """根据文件扩展名推断语言."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".c": "c",
            ".cpp": "cpp",
            ".java": "java",
        }
        return ext_map.get(path.suffix, "python")


# 全局解析器管理器实例
parser_manager = ParserManager()
