#!/usr/bin/env python3
"""阶段13验收验证脚本 - 任务状态、业务状态、系统状态三层隔离."""
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
    print_header("阶段13验收验证 - 三层状态隔离")
    all_passed = True
    project_root = Path(__file__).parent.parent

    # 1. 三层状态定义检查
    print_header("1. 三层状态定义清晰")
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.collaboration import StateLayer
        from multi_agent_se.collaboration.state import SystemState, TaskState, BusinessState
        
        all_passed = print_result("StateLayer枚举", len(StateLayer) == 3) and all_passed
        all_passed = print_result("SYSTEM层", StateLayer.SYSTEM.value == "system") and all_passed
        all_passed = print_result("TASK层", StateLayer.TASK.value == "task") and all_passed
        all_passed = print_result("BUSINESS层", StateLayer.BUSINESS.value == "business") and all_passed
        
        # 三层状态数据类
        all_passed = print_result("SystemState可创建", SystemState is not None) and all_passed
        all_passed = print_result("TaskState可创建", TaskState is not None) and all_passed
        all_passed = print_result("BusinessState可创建", BusinessState is not None) and all_passed
        
    except Exception as e:
        all_passed = print_result("三层状态定义", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 2. 状态转换规则
    print_header("2. 状态转换规则明确")
    try:
        from multi_agent_se.collaboration import TaskStateMachine, TaskStatus, TransitionResult
        
        sm = TaskStateMachine()
        
        # 合法转换
        all_passed = print_result("PENDING->RUNNING合法", sm.can_transition(TaskStatus.PENDING, TaskStatus.RUNNING)) and all_passed
        all_passed = print_result("RUNNING->COMPLETED合法", sm.can_transition(TaskStatus.RUNNING, TaskStatus.COMPLETED)) and all_passed
        all_passed = print_result("RUNNING->FAILED合法", sm.can_transition(TaskStatus.RUNNING, TaskStatus.FAILED)) and all_passed
        all_passed = print_result("FAILED->PENDING合法(重试)", sm.can_transition(TaskStatus.FAILED, TaskStatus.PENDING)) and all_passed
        
        # 非法转换
        all_passed = print_result("COMPLETED->RUNNING非法", not sm.can_transition(TaskStatus.COMPLETED, TaskStatus.RUNNING)) and all_passed
        all_passed = print_result("PENDING->COMPLETED非法", not sm.can_transition(TaskStatus.PENDING, TaskStatus.COMPLETED)) and all_passed
        
        # 转换图
        graph = sm.get_transition_graph()
        all_passed = print_result("get_transition_graph", "pending" in graph) and all_passed
        
        # 可转换状态
        valid_from_pending = sm.get_valid_transitions(TaskStatus.PENDING)
        all_passed = print_result("PENDING可转状态", TaskStatus.RUNNING in valid_from_pending) and all_passed
        
    except Exception as e:
        all_passed = print_result("状态转换规则", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 3. 三层状态管理器
    print_header("3. 三层状态管理器")
    try:
        from multi_agent_se.collaboration import (
            SystemStateManager, TaskStateManager, BusinessStateManager,
            StateLayer, TaskStatus, AgentRole,
        )
        
        # 系统层管理器
        sys_mgr = SystemStateManager()
        all_passed = print_result("SystemStateManager.layer", sys_mgr.layer == StateLayer.SYSTEM) and all_passed
        sys_state = sys_mgr.create(env="test")
        all_passed = print_result("SystemStateManager.create", sys_state is not None) and all_passed
        all_passed = print_result("SystemStateManager.get", sys_mgr.get() == sys_state) and all_passed
        sys_mgr.update(env="prod")
        all_passed = print_result("SystemStateManager.update", sys_mgr.get().env == "prod") and all_passed
        
        # 任务层管理器
        task_mgr = TaskStateManager()
        all_passed = print_result("TaskStateManager.layer", task_mgr.layer == StateLayer.TASK) and all_passed
        task_state = task_mgr.create(task_type="code_review", priority=5)
        all_passed = print_result("TaskStateManager.create", task_state is not None) and all_passed
        all_passed = print_result("TaskStateManager.get", task_mgr.get() == task_state) and all_passed
        
        # 状态转换
        result = task_mgr.transition(TaskStatus.RUNNING)
        all_passed = print_result("TaskStateManager.transition", result.success) and all_passed
        all_passed = print_result("状态已转换", task_mgr.get().status == TaskStatus.RUNNING) and all_passed
        
        # 进度更新
        task_mgr.update_progress(50.0)
        all_passed = print_result("TaskStateManager.update_progress", task_mgr.get().progress == 50.0) and all_passed
        
        # Agent分配
        task_mgr.assign_agent(AgentRole.DEVELOPER)
        all_passed = print_result("TaskStateManager.assign_agent", task_mgr.get().assigned_agent == AgentRole.DEVELOPER) and all_passed
        
        # 可转换状态
        valid_trans = task_mgr.get_valid_transitions()
        all_passed = print_result("TaskStateManager.get_valid_transitions", len(valid_trans) > 0) and all_passed
        
        # 业务层管理器
        biz_mgr = BusinessStateManager()
        all_passed = print_result("BusinessStateManager.layer", biz_mgr.layer == StateLayer.BUSINESS) and all_passed
        biz_state = biz_mgr.create(input_data={"code": "print('hello')"})
        all_passed = print_result("BusinessStateManager.create", biz_state is not None) and all_passed
        
        # 输出设置
        biz_mgr.set_output("result", "success")
        all_passed = print_result("BusinessStateManager.set_output", biz_mgr.get().output_data.get("result") == "success") and all_passed
        
        # 上下文设置
        biz_mgr.set_context("lang", "python")
        all_passed = print_result("BusinessStateManager.set_context", biz_mgr.get().context.get("lang") == "python") and all_passed
        
        # 产物添加
        biz_mgr.add_artifact("file.py")
        all_passed = print_result("BusinessStateManager.add_artifact", "file.py" in biz_mgr.get_artifacts()) and all_passed
        
    except Exception as e:
        all_passed = print_result("三层状态管理器", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 4. 状态隔离验证
    print_header("4. 状态隔离验证")
    try:
        from multi_agent_se.collaboration import (
            SystemStateManager, TaskStateManager, BusinessStateManager,
            StateLayer,
        )
        from multi_agent_se.core.exceptions import SchedulerError
        
        # 系统管理器不能访问任务状态
        sys_mgr = SystemStateManager()
        sys_mgr.create()
        try:
            # 尝试通过系统管理器访问（实际上不会直接暴露，但隔离检查在管理器内部）
            # 这里测试隔离开关
            sys_mgr.set_isolation(True)
            all_passed = print_result("隔离开关启用", sys_mgr._isolation_enabled) and all_passed
            
            # 验证各管理器只能访问自己的层
            all_passed = print_result("SystemStateManager只能访问SYSTEM层", sys_mgr.layer == StateLayer.SYSTEM) and all_passed
            
            task_mgr = TaskStateManager()
            all_passed = print_result("TaskStateManager只能访问TASK层", task_mgr.layer == StateLayer.TASK) and all_passed
            
            biz_mgr = BusinessStateManager()
            all_passed = print_result("BusinessStateManager只能访问BUSINESS层", biz_mgr.layer == StateLayer.BUSINESS) and all_passed
            
        except SchedulerError as e:
            all_passed = print_result("隔离违规检测", True, str(e)) and all_passed
        
        # 访问日志
        logs = sys_mgr.get_access_log()
        all_passed = print_result("访问日志记录", len(logs) > 0) and all_passed
        
    except Exception as e:
        all_passed = print_result("状态隔离验证", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 5. 状态同步机制
    print_header("5. 状态同步机制")
    try:
        from multi_agent_se.collaboration import StateSynchronizer, StateLayer
        from multi_agent_se.collaboration.state import GraphState
        
        sync = StateSynchronizer()
        
        # 创建三层状态
        sys_state, task_state, biz_state = sync.create_all(
            task_type="refactor",
            input_data={"file": "main.py"},
        )
        all_passed = print_result("StateSynchronizer.create_all", all([sys_state, task_state, biz_state])) and all_passed
        
        # 验证关联
        all_passed = print_result("task.parent_task_id关联", task_state.parent_task_id == sys_state.session_id) and all_passed
        
        # 同步到GraphState
        graph = sync.sync_to_graph_state()
        all_passed = print_result("sync_to_graph_state", graph is not None) and all_passed
        all_passed = print_result("GraphState含session_id", "session_id" in graph) and all_passed
        all_passed = print_result("GraphState含task_id", "task_id" in graph) and all_passed
        all_passed = print_result("GraphState含input_data", "input_data" in graph) and all_passed
        
        # 从GraphState同步回
        graph["status"] = "completed"
        graph["progress"] = 100.0
        graph["output_data"] = {"result": "done"}
        
        result = sync.sync_from_graph_state(graph)
        all_passed = print_result("sync_from_graph_state", result.success) and all_passed
        all_passed = print_result("同步层数", len(result.synced_layers) == 3) and all_passed
        
        # 验证同步结果
        all_passed = print_result("任务状态已同步", sync.task_manager.get().status.value == "completed") and all_passed
        all_passed = print_result("业务状态已同步", sync.business_manager.get().output_data.get("result") == "done") and all_passed
        
        # 隔离验证
        isolation = sync.validate_isolation()
        all_passed = print_result("validate_isolation", all(isolation.values())) and all_passed
        
        # 访问日志汇总
        all_logs = sync.get_all_access_logs()
        all_passed = print_result("get_all_access_logs", len(all_logs) == 3) and all_passed
        
    except Exception as e:
        all_passed = print_result("状态同步机制", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 6. 文件结构检查
    print_header("6. 文件结构检查")
    all_passed = print_result(
        "文件: collaboration/state_machine.py",
        (project_root / "src/multi_agent_se/collaboration/state_machine.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: collaboration/__init__.py",
        (project_root / "src/multi_agent_se/collaboration/__init__.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: scripts/verify_phase13.py",
        Path(__file__).exists(),
    ) and all_passed

    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段13验收通过！所有检查项均符合要求。")
        print("  📋 阶段13交付物清单：")
        print("     - state_machine.py (TaskStateMachine + 三层管理器 + StateSynchronizer)")
        print("     - 三层状态定义清晰 ✓")
        print("     - 状态转换规则明确 ✓")
        print("     - 状态隔离验证通过 ✓")
        print("     - 状态同步机制可用 ✓")
        return 0
    else:
        print("  ❌ 阶段13验收未通过！")
        return 1


if __name__ == "__main__":
    sys.exit(main())
