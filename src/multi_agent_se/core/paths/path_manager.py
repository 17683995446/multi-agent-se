"""统一路径管理 - 阶段10.

正交拆分：路径工具独立于配置模块
提供跨平台兼容的路径操作工具
"""

import os
import platform
import shutil
from pathlib import Path
from typing import List, Optional, Union


class PathManager:
    """路径管理器.

    统一管理项目路径，提供跨平台兼容的路径操作：
    - 标准化目录结构 (src/config/logs/data/tests/artifacts)
    - 跨平台路径拼接与转换
    - 目录创建与清理
    - 文件查找与遍历
    """

    def __init__(self, project_root: Optional[Union[str, Path]] = None) -> None:
        """初始化路径管理器.

        Args:
            project_root: 项目根目录 (默认自动检测)
        """
        if project_root:
            self._root = Path(project_root).resolve()
        else:
            self._root = Path(__file__).parent.parent.parent.parent.resolve()

        # 标准化目录
        self.src_dir = self._root / "src"
        self.config_dir = self._root / "config"
        self.logs_dir = self._root / "logs"
        self.data_dir = self._root / "data"
        self.tests_dir = self._root / "tests"
        self.artifacts_dir = self._root / "artifacts"
        self.scripts_dir = self._root / "scripts"

        # 确保必要目录存在
        self._ensure_core_dirs()

    def _ensure_core_dirs(self) -> None:
        """确保核心目录存在."""
        for d in [self.logs_dir, self.data_dir, self.artifacts_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ========== 属性 ==========
    @property
    def root(self) -> Path:
        """项目根目录."""
        return self._root

    @property
    def platform_name(self) -> str:
        """当前平台名称."""
        return platform.system()

    @property
    def is_windows(self) -> bool:
        """是否Windows."""
        return os.name == "nt"

    @property
    def is_posix(self) -> bool:
        """是否POSIX系统."""
        return os.name == "posix"

    # ========== 路径构建 ==========
    def resolve(self, *parts: str) -> Path:
        """构建并解析路径.

        Args:
            *parts: 路径组成部分

        Returns:
            解析后的绝对路径
        """
        return self._root.joinpath(*parts).resolve()

    def relative_to_root(self, path: Union[str, Path]) -> Path:
        """获取相对于项目根目录的路径.

        Args:
            path: 绝对路径

        Returns:
            相对路径
        """
        abs_path = Path(path).resolve()
        try:
            return abs_path.relative_to(self._root)
        except ValueError:
            return abs_path

    def to_posix(self, path: Union[str, Path]) -> str:
        """转换为POSIX路径格式 (使用/分隔符).

        Args:
            path: 路径

        Returns:
            POSIX格式路径字符串
        """
        return str(Path(path)).replace("\\", "/")

    def to_native(self, path: Union[str, Path]) -> str:
        """转换为当前平台原生路径格式.

        Args:
            path: 路径

        Returns:
            原生格式路径字符串
        """
        return str(Path(path))

    # ========== 目录操作 ==========
    def ensure_dir(self, path: Union[str, Path]) -> Path:
        """确保目录存在.

        Args:
            path: 目录路径

        Returns:
            目录路径
        """
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def ensure_file_dir(self, file_path: Union[str, Path]) -> Path:
        """确保文件所在目录存在.

        Args:
            file_path: 文件路径

        Returns:
            文件所在目录路径
        """
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p.parent

    def clean_dir(self, path: Union[str, Path]) -> None:
        """清空目录内容 (保留目录本身).

        Args:
            path: 目录路径
        """
        p = Path(path)
        if p.exists() and p.is_dir():
            for item in p.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)

    def remove_dir(self, path: Union[str, Path]) -> bool:
        """删除目录.

        Args:
            path: 目录路径

        Returns:
            是否成功删除
        """
        p = Path(path)
        if p.exists() and p.is_dir():
            shutil.rmtree(p)
            return True
        return False

    # ========== 文件查找 ==========
    def find_files(
        self,
        directory: Union[str, Path],
        pattern: str = "*",
        recursive: bool = True,
    ) -> List[Path]:
        """查找文件.

        Args:
            directory: 搜索目录
            pattern: 文件匹配模式 (glob格式)
            recursive: 是否递归搜索

        Returns:
            匹配的文件路径列表
        """
        d = Path(directory)
        if not d.exists():
            return []

        if recursive:
            return sorted(d.rglob(pattern))
        return sorted(d.glob(pattern))

    def find_python_files(self, directory: Union[str, Path]) -> List[Path]:
        """查找Python文件.

        Args:
            directory: 搜索目录

        Returns:
            .py文件路径列表
        """
        return self.find_files(directory, pattern="*.py", recursive=True)

    # ========== 路径信息 ==========
    def get_dir_tree(
        self,
        directory: Union[str, Path],
        max_depth: int = 3,
        exclude: Optional[List[str]] = None,
    ) -> str:
        """获取目录树字符串.

        Args:
            directory: 目录路径
            max_depth: 最大深度
            exclude: 排除的目录名列表

        Returns:
            目录树字符串
        """
        exclude = exclude or ["__pycache__", ".git", "node_modules", ".pytest_cache", "htmlcov"]
        lines = []
        d = Path(directory)

        def _walk(current: Path, prefix: str, depth: int) -> None:
            if depth > max_depth:
                return
            try:
                items = sorted(current.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            except PermissionError:
                return
            for i, item in enumerate(items):
                if item.name in exclude or item.name.startswith("."):
                    continue
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{item.name}")
                if item.is_dir():
                    extension = "    " if is_last else "│   "
                    _walk(item, prefix + extension, depth + 1)

        lines.append(str(d.name) + "/")
        _walk(d, "", 0)
        return "\n".join(lines)

    def get_path_info(self, path: Union[str, Path]) -> dict:
        """获取路径详细信息.

        Args:
            path: 文件或目录路径

        Returns:
            路径信息字典
        """
        p = Path(path).resolve()
        info = {
            "path": str(p),
            "name": p.name,
            "suffix": p.suffix,
            "stem": p.stem,
            "exists": p.exists(),
            "is_file": p.is_file() if p.exists() else False,
            "is_dir": p.is_dir() if p.exists() else False,
            "parent": str(p.parent),
        }
        if p.exists():
            stat = p.stat()
            info["size"] = stat.st_size
            info["size_human"] = self._format_size(stat.st_size)
        return info

    @staticmethod
    def _format_size(size: int) -> str:
        """格式化文件大小."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"


# ========== 全局路径管理器实例 ==========
path_manager = PathManager()


# ========== 便捷函数 ==========
def get_project_path(*parts: str) -> Path:
    """获取项目路径."""
    return path_manager.resolve(*parts)


def get_config_path(filename: str) -> Path:
    """获取配置文件路径."""
    return path_manager.config_dir / filename


def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在."""
    return path_manager.ensure_dir(path)
