"""统一路径管理."""

from multi_agent_se.core.paths.path_manager import (
    PathManager,
    path_manager,
    get_project_path,
    get_config_path,
    ensure_dir,
)

__all__ = [
    "PathManager",
    "path_manager",
    "get_project_path",
    "get_config_path",
    "ensure_dir",
]
