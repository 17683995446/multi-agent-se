"""配置模块单元测试."""

import pytest
from pathlib import Path

from multi_agent_se.core.config import (
    Settings,
    MASEError,
    ConfigurationError,
    AgentError,
    get_project_path,
    get_config_path,
    ensure_dir,
    settings,
    logger,
)


class TestSettings:
    """测试配置类."""
    
    def test_default_settings(self):
        """测试默认配置."""
        assert settings.app_name == "multi-agent-se"
        assert settings.app_version == "0.1.0"
        assert settings.log_level == "INFO"
        assert settings.min_test_coverage == 80.0
    
    def test_environment_detection(self):
        """测试环境检测."""
        assert settings.is_development == True
        assert settings.is_production == False


class TestExceptions:
    """测试异常类."""
    
    def test_base_error(self):
        """测试基础异常."""
        error = MASEError("测试错误", error_code="TEST_001", details={"key": "value"})
        assert error.message == "测试错误"
        assert error.error_code == "TEST_001"
        assert error.details == {"key": "value"}
    
    def test_configuration_error(self):
        """测试配置错误."""
        error = ConfigurationError("配置错误")
        assert error.error_code == "MASE_CFG_001"
    
    def test_agent_error(self):
        """测试Agent错误."""
        error = AgentError("Agent错误", agent_name="TestAgent")
        assert error.error_code == "MASE_AGENT_001"
        assert error.agent_name == "TestAgent"


class TestPathUtils:
    """测试路径工具."""
    
    def test_get_project_path(self):
        """测试获取项目路径."""
        path = get_project_path("test", "file.txt")
        assert isinstance(path, Path)
        assert "test" in str(path)
        assert "file.txt" in str(path)
    
    def test_get_config_path(self):
        """测试获取配置路径."""
        path = get_config_path("settings.yaml")
        assert isinstance(path, Path)
        assert path.name == "settings.yaml"
    
    def test_ensure_dir(self, tmp_path):
        """测试确保目录存在."""
        test_dir = tmp_path / "test_dir"
        result = ensure_dir(test_dir)
        assert result.exists()
        assert result.is_dir()


class TestLogger:
    """测试日志."""
    
    def test_logger_exists(self):
        """测试logger存在."""
        assert logger is not None
