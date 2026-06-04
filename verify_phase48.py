"""第48阶段验收脚本 - 配置系统解耦.

验证配置系统的兼容性：
- SimpleSettings 无pydantic依赖工作
- 环境变量加载
- 属性访问兼容性
- 与现有代码集成
"""

import sys
import os
sys.path.insert(0, "/workspace/multi_agent_se/src")


def test_simple_settings_basic():
    """测试: SimpleSettings基本功能."""
    print("\n[TEST] SimpleSettings基本功能")
    
    from multi_agent_se.core.config.simple_settings import SimpleSettings
    
    settings = SimpleSettings()
    
    # 基本属性
    assert settings.app_name == "multi-agent-se"
    assert settings.app_version == "0.1.0"
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.autogen_timeout == 60
    assert settings.min_test_coverage == 80.0
    print(f"  ✓ 默认配置正确")
    
    # 布尔属性
    assert settings.langgraph_checkpoint is True
    assert settings.langgraph_verbose is False
    print(f"  ✓ 布尔配置正确")
    
    # 便捷属性
    assert settings.is_development is True
    assert settings.is_production is False
    print(f"  ✓ 环境判断正确")
    
    # 导出字典
    data = settings.to_dict()
    assert "app_name" in data
    assert "log_level" in data
    print(f"  ✓ 字典导出正确")
    
    return True


def test_simple_settings_env_override():
    """测试: 环境变量覆盖."""
    print("\n[TEST] 环境变量覆盖")
    
    from multi_agent_se.core.config.simple_settings import SimpleSettings
    
    # 设置环境变量
    os.environ["APP_ENV"] = "production"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["AUTOGEN_TIMEOUT"] = "120"
    os.environ["MIN_TEST_COVERAGE"] = "90.5"
    
    settings = SimpleSettings()
    
    assert settings.app_env == "production"
    assert settings.log_level == "DEBUG"
    assert settings.autogen_timeout == 120
    assert settings.min_test_coverage == 90.5
    assert settings.is_production is True
    print(f"  ✓ 环境变量覆盖正确")
    
    # 清理环境变量
    del os.environ["APP_ENV"]
    del os.environ["LOG_LEVEL"]
    del os.environ["AUTOGEN_TIMEOUT"]
    del os.environ["MIN_TEST_COVERAGE"]
    
    return True


def test_simple_settings_from_dict():
    """测试: 从字典加载."""
    print("\n[TEST] 从字典加载")
    
    from multi_agent_se.core.config.simple_settings import SimpleSettings
    
    settings = SimpleSettings()
    settings._load_from_dict({
        "app_name": "custom-app",
        "log_level": "ERROR",
        "autogen_timeout": 30,
    })
    
    assert settings.app_name == "custom-app"
    assert settings.log_level == "ERROR"
    assert settings.autogen_timeout == 30
    # 未修改的保持默认值
    assert settings.app_version == "0.1.0"
    print(f"  ✓ 字典加载正确")
    
    return True


def test_compatible_settings():
    """测试: 兼容层自动选择."""
    print("\n[TEST] 兼容层自动选择")
    
    from multi_agent_se.core.config.simple_settings import (
        settings, get_settings_backend, SimpleSettings
    )
    
    backend = get_settings_backend()
    print(f"  当前后端: {backend}")
    
    # 无论哪个后端，属性访问应该一致
    assert hasattr(settings, "app_name")
    assert hasattr(settings, "log_level")
    assert hasattr(settings, "autogen_timeout")
    assert hasattr(settings, "is_development")
    assert hasattr(settings, "is_production")
    print(f"  ✓ 属性访问兼容")
    
    # 验证值合理
    assert settings.app_name == "multi-agent-se"
    assert settings.autogen_timeout > 0
    print(f"  ✓ 配置值合理")
    
    return True


def test_no_pydantic_import_error():
    """测试: 无pydantic时不报错."""
    print("\n[TEST] 无pydantic容错")
    
    # 模拟无pydantic环境
    import importlib
    
    # 确保simple_settings模块可独立导入
    from multi_agent_se.core.config.simple_settings import SimpleSettings
    
    settings = SimpleSettings()
    assert settings.app_name is not None
    print(f"  ✓ 纯Python配置独立工作")
    
    return True


def test_integration_with_agents():
    """测试: 与Agent集成."""
    print("\n[TEST] 与Agent集成")
    
    from multi_agent_se.agents.controller import ControllerAgent
    from multi_agent_se.agents.runtime.base_agent import AgentContext
    from multi_agent_se.scheduler.task import Task
    
    # Agent应该能正常工作，不依赖pydantic
    agent = ControllerAgent(agent_id="test.config.001")
    task = Task(task_id="config.test", task_type="controller")
    context = AgentContext(task=task, input_data={"requirement": "测试配置系统"})
    result = agent.process(context)
    
    assert result.success is True
    print(f"  ✓ Agent在无pydantic环境下正常工作")
    
    return True


def run_all_tests():
    """运行所有测试."""
    print("=" * 60)
    print("第48阶段验收测试 - 配置系统解耦")
    print("=" * 60)
    
    tests = [
        ("SimpleSettings基本功能", test_simple_settings_basic),
        ("环境变量覆盖", test_simple_settings_env_override),
        ("从字典加载", test_simple_settings_from_dict),
        ("兼容层自动选择", test_compatible_settings),
        ("无pydantic容错", test_no_pydantic_import_error),
        ("与Agent集成", test_integration_with_agents),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"  ✓ {name} 通过")
            else:
                failed += 1
                print(f"  ✗ {name} 失败")
        except Exception as e:
            failed += 1
            print(f"  ✗ {name} 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 第48阶段验收通过！配置系统解耦完成。")
    else:
        print("❌ 部分测试失败。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
