#!/usr/bin/env python3
"""阶段14验收验证脚本 - 全局信息显式化机制（消灭隐式状态）."""
import sys
from pathlib import Path


def print_header(text: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_result(test: str, passed: bool, details: str = "") -> bool:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test}")
    if details:
        print(f"       {details}")
    return passed


def main() -> int:
    print_header("阶段14验收验证 - 全局信息显式化机制")
    all_passed = True
    project_root = Path(__file__).parent.parent

    # 1. 隐式状态扫描工具
    print_header("1. 隐式状态扫描工具")
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.core.explicitness import (
            StateScanner, ImplicitStateType, ScanResult, scan_module,
        )
        
        scanner = StateScanner()
        
        # 扫描测试代码
        test_code = '''
# 模块级可变全局变量（隐式状态）
_cache = {}
_config = []

# 类级可变变量
class MyClass:
    shared_data = {}
    _instance = None
    
    def method(self, items=[]):
        pass
'''
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        issues = scanner.scan_file(temp_file)
        import os
        os.unlink(temp_file)
        
        all_passed = print_result("扫描发现隐式状态", len(issues) > 0, f"发现{len(issues)}个问题") and all_passed
        
        # 检查类型
        module_globals = [i for i in issues if i.state_type == ImplicitStateType.MODULE_GLOBAL]
        class_vars = [i for i in issues if i.state_type == ImplicitStateType.CLASS_VARIABLE]
        singletons = [i for i in issues if i.state_type == ImplicitStateType.SINGLETON_STATE]
        mutable_defaults = [i for i in issues if i.state_type == ImplicitStateType.MUTABLE_DEFAULT]
        
        all_passed = print_result("MODULE_GLOBAL检测", len(module_globals) >= 2) and all_passed
        all_passed = print_result("CLASS_VARIABLE检测", len(class_vars) >= 1) and all_passed
        all_passed = print_result("SINGLETON_STATE检测", len(singletons) >= 1) and all_passed
        all_passed = print_result("MUTABLE_DEFAULT检测", len(mutable_defaults) >= 1) and all_passed
        
        # ScanResult
        result = ScanResult(implicit_states=issues, scanned_files=1, scanned_lines=15)
        all_passed = print_result("ScanResult.total_issues", result.total_issues > 0) and all_passed
        all_passed = print_result("ScanResult.issues_by_type", len(result.issues_by_type) > 0) and all_passed
        all_passed = print_result("ScanResult.to_dict", "total_issues" in result.to_dict()) and all_passed
        
        # 扫描实际项目
        scanner2 = StateScanner()
        scan_result = scanner2.scan_directory(str(project_root / "src" / "multi_agent_se" / "core"))
        all_passed = print_result("扫描项目目录", scan_result.scanned_files > 0, f"扫描了{scan_result.scanned_files}个文件") and all_passed
        
    except Exception as e:
        all_passed = print_result("隐式状态扫描", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 2. 全局状态注册表
    print_header("2. 全局状态注册表")
    try:
        from multi_agent_se.core.explicitness import (
            StateRegistry, global_state_registry, StateScope, ExplicitState,
        )
        
        reg = StateRegistry()
        
        # 注册状态
        state1 = reg.register(
            name="app_config",
            value={"debug": True, "port": 8080},
            scope=StateScope.GLOBAL,
            description="应用配置",
            owner="system",
        )
        all_passed = print_result("register返回ExplicitState", isinstance(state1, ExplicitState)) and all_passed
        all_passed = print_result("state_id自动生成", len(state1.state_id) > 0) and all_passed
        
        # 不同作用域
        state2 = reg.register("session_data", {"user": "admin"}, scope=StateScope.SESSION)
        state3 = reg.register("task_progress", 50, scope=StateScope.TASK)
        all_passed = print_result("多作用域注册", len(reg.get_all_names()) == 3) and all_passed
        
        # 获取状态
        val = reg.get("app_config")
        all_passed = print_result("get返回值", val == {"debug": True, "port": 8080}) and all_passed
        
        # 获取完整记录
        full_state = reg.get_state("app_config")
        all_passed = print_result("get_state返回完整记录", full_state.name == "app_config") and all_passed
        all_passed = print_result("access_count增加", full_state.access_count > 0) and all_passed
        
        # 更新状态
        updated = reg.update("app_config", {"debug": False, "port": 8080})
        all_passed = print_result("update成功", updated) and all_passed
        all_passed = print_result("值已更新", reg.get("app_config")["debug"] == False) and all_passed
        
        # 依赖关系
        reg.register("db_config", {"host": "localhost"}, dependencies={"app_config"})
        deps = reg.get_dependencies("db_config")
        all_passed = print_result("dependencies记录", len(deps) == 1 and deps[0].name == "app_config") and all_passed
        
        dependents = reg.get_dependents("app_config")
        all_passed = print_result("dependents查询", len(dependents) == 1 and dependents[0].name == "db_config") and all_passed
        
        # 按作用域查询
        global_states = reg.get_by_scope(StateScope.GLOBAL)
        all_passed = print_result("get_by_scope", len(global_states) == 2) and all_passed
        
        # 按所有者查询
        system_states = reg.get_by_owner("system")
        all_passed = print_result("get_by_owner", len(system_states) == 1) and all_passed
        
        # 存在检查
        all_passed = print_result("exists(存在的)", reg.exists("app_config")) and all_passed
        all_passed = print_result("exists(不存在的)", not reg.exists("not_exist")) and all_passed
        
        # 重复注册
        try:
            reg.register("app_config", {})
            all_passed = print_result("重复注册应报错", False) and all_passed
        except ValueError:
            all_passed = print_result("重复注册正确拒绝", True) and all_passed
        
        # 注销
        unregistered = reg.unregister("session_data")
        all_passed = print_result("unregister成功", unregistered) and all_passed
        all_passed = print_result("注销后不存在", not reg.exists("session_data")) and all_passed
        
        # 统计（4个注册 - 1个注销 = 3个）
        stats = reg.get_stats()
        all_passed = print_result("get_stats", stats.total_states == 3) and all_passed
        all_passed = print_result("stats.by_scope", "global" in stats.by_scope) and all_passed
        
        # 全局实例
        all_passed = print_result("global_state_registry可用", global_state_registry is not None) and all_passed
        
    except Exception as e:
        all_passed = print_result("全局状态注册表", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 3. 状态可追溯验证
    print_header("3. 状态可追溯验证")
    try:
        from multi_agent_se.core.explicitness import (
            StateTracer, global_state_tracer, ChangeType, StateChange, TraceQuery,
        )
        
        tracer = StateTracer()
        
        # 记录变更
        change1 = tracer.record(
            state_name="config",
            change_type=ChangeType.CREATE,
            new_value={"debug": True},
            actor="admin",
            reason="初始化配置",
        )
        all_passed = print_result("record返回StateChange", isinstance(change1, StateChange)) and all_passed
        all_passed = print_result("change_id自动生成", len(change1.change_id) > 0) and all_passed
        
        # 更多变更
        tracer.record("config", ChangeType.UPDATE, {"debug": True}, {"debug": False}, "admin", "关闭调试")
        tracer.record("config", ChangeType.READ, actor="user1")
        tracer.record("db", ChangeType.CREATE, new_value={"host": "localhost"}, actor="admin")
        
        all_passed = print_result("变更记录总数", tracer.get_change_count() == 4) and all_passed
        
        # 查询历史
        config_history = tracer.get_history("config")
        all_passed = print_result("get_history", len(config_history) == 3) and all_passed
        
        # 最后变更
        last = tracer.get_last_change("config")
        all_passed = print_result("get_last_change", last.change_type == ChangeType.READ) and all_passed
        
        # 条件查询
        query = TraceQuery(state_name="config", change_type=ChangeType.UPDATE)
        updates = tracer.query(query)
        all_passed = print_result("query(UPDATE)", len(updates) == 1) and all_passed
        
        # 所有追踪的状态
        unique_states = tracer.get_unique_states()
        all_passed = print_result("get_unique_states", set(unique_states) == {"config", "db"}) and all_passed
        
        # 审计报告
        report = tracer.get_audit_report("config")
        all_passed = print_result("get_audit_report", report["total_changes"] == 3) and all_passed
        all_passed = print_result("report.changes_by_type", "create" in report["changes_by_type"]) and all_passed
        
        # 全局报告
        global_report = tracer.get_audit_report()
        all_passed = print_result("全局audit_report", global_report["total_changes"] == 4) and all_passed
        
        # 全局实例
        all_passed = print_result("global_state_tracer可用", global_state_tracer is not None) and all_passed
        
    except Exception as e:
        all_passed = print_result("状态可追溯验证", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 4. 文件结构检查
    print_header("4. 文件结构检查")
    all_passed = print_result(
        "文件: core/explicitness/scanner.py",
        (project_root / "src/multi_agent_se/core/explicitness/scanner.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: core/explicitness/registry.py",
        (project_root / "src/multi_agent_se/core/explicitness/registry.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: core/explicitness/tracer.py",
        (project_root / "src/multi_agent_se/core/explicitness/tracer.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: core/explicitness/__init__.py",
        (project_root / "src/multi_agent_se/core/explicitness/__init__.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: scripts/verify_phase14.py",
        Path(__file__).exists(),
    ) and all_passed

    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段14验收通过！所有检查项均符合要求。")
        print("  📋 阶段14交付物清单：")
        print("     - scanner.py (StateScanner - 隐式状态扫描)")
        print("     - registry.py (StateRegistry - 全局状态注册)")
        print("     - tracer.py (StateTracer - 状态变更追踪)")
        print("     - 隐式状态扫描工具 ✓")
        print("     - 显式化转换规则 ✓")
        print("     - 全局状态注册表 ✓")
        print("     - 状态可追溯验证 ✓")
        return 0
    else:
        print("  ❌ 阶段14验收未通过！")
        return 1


if __name__ == "__main__":
    sys.exit(main())
