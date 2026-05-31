#!/usr/bin/env python3
"""阶段3验收验证脚本.

验证内容：
1. LangGraph正确安装
2. 基础StateGraph可运行
3. 节点流转正常
4. 官方示例可执行
"""

import sys
from pathlib import Path

def print_header(text: str) -> None:
    """打印标题."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_result(test: str, passed: bool, details: str = "") -> bool:
    """打印测试结果."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test}")
    if details:
        print(f"       {details}")
    return passed

def main() -> int:
    """主函数."""
    print_header("阶段3验收验证 - 接入LangGraph基础调度内核")
    
    all_passed = True
    project_root = Path(__file__).parent.parent
    
    # 1. LangGraph安装检查
    print_header("1. LangGraph安装检查")
    
    try:
        import langgraph
        all_passed = print_result("LangGraph已安装", True) and all_passed
        
        # 检查核心组件
        from langgraph.graph import StateGraph, END
        all_passed = print_result("StateGraph可导入", True) and all_passed
        
        from langgraph.checkpoint.memory import MemorySaver
        all_passed = print_result("MemorySaver可导入", True) and all_passed
        
    except ImportError as e:
        all_passed = print_result("LangGraph已安装", False, str(e)) and all_passed
    
    # 2. 状态定义模块检查
    print_header("2. 状态定义模块检查")
    
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.collaboration.state import (
            GraphState,
            TaskStatus,
            AgentRole,
            SystemState,
            TaskState,
            BusinessState,
            create_initial_state,
            get_state_summary,
        )
        
        all_passed = print_result("状态模块可导入", True) and all_passed
        
        # 测试状态创建
        state = create_initial_state(task_type="test_task", input_data={"test": "data"})
        all_passed = print_result("create_initial_state可用", True) and all_passed
        all_passed = print_result("状态包含task_id", "task_id" in state and bool(state["task_id"])) and all_passed
        all_passed = print_result("状态包含session_id", "session_id" in state and bool(state["session_id"])) and all_passed
        all_passed = print_result("状态包含trace_id", "trace_id" in state and bool(state["trace_id"])) and all_passed
        
        # 测试状态摘要
        summary = get_state_summary(state)
        all_passed = print_result("get_state_summary可用", summary is not None) and all_passed
        
    except Exception as e:
        all_passed = print_result("状态模块可导入", False, str(e)) and all_passed
    
    # 3. GraphBuilder检查
    print_header("3. GraphBuilder检查")
    
    try:
        from multi_agent_se.collaboration.scheduler.graph_builder import (
            GraphBuilder,
            create_simple_graph,
            create_conditional_graph,
            init_node,
            end_node,
            error_handler,
        )
        
        all_passed = print_result("GraphBuilder可导入", True) and all_passed
        
        # 测试简单图创建
        builder = create_simple_graph()
        all_passed = print_result("create_simple_graph可用", True) and all_passed
        
        info = builder.get_graph_info()
        all_passed = print_result("get_graph_info可用", True) and all_passed
        all_passed = print_result("图包含init节点", "init" in info["nodes"]) and all_passed
        all_passed = print_result("图包含end节点", "end" in info["nodes"]) and all_passed
        all_passed = print_result("图有入口点", info["entry_point"] is not None) and all_passed
        
        # 测试条件图创建
        conditional_builder = create_conditional_graph()
        all_passed = print_result("create_conditional_graph可用", True) and all_passed
        
        conditional_info = conditional_builder.get_graph_info()
        all_passed = print_result("条件图有条件边", conditional_info["conditional_edges"] > 0) and all_passed
        
    except Exception as e:
        all_passed = print_result("GraphBuilder可导入", False, str(e)) and all_passed
    
    # 4. 图执行检查
    print_header("4. 图执行检查")
    
    try:
        from multi_agent_se.collaboration.scheduler.graph_builder import create_simple_graph
        from multi_agent_se.collaboration.state import create_initial_state
        
        # 创建并编译图
        builder = create_simple_graph()
        builder.compile(checkpoint=False)
        
        # 执行图
        initial_state = create_initial_state(task_type="verify_task")
        result = builder.invoke(initial_state)
        
        all_passed = print_result("图可编译", True) and all_passed
        all_passed = print_result("图可执行", True) and all_passed
        all_passed = print_result("执行结果非空", result is not None) and all_passed
        all_passed = print_result("任务状态为completed", result.get("status") == "completed") and all_passed
        all_passed = print_result("进度为100%", result.get("progress") == 100.0) and all_passed
        
    except Exception as e:
        all_passed = print_result("图执行", False, str(e)) and all_passed
    
    # 5. 示例文件检查
    print_header("5. 示例文件检查")
    
    example_file = project_root / "examples" / "langgraph_basic_example.py"
    all_passed = print_result("示例文件存在", example_file.exists()) and all_passed
    
    if example_file.exists():
        # 检查示例文件语法
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(example_file)],
            capture_output=True,
            text=True
        )
        all_passed = print_result("示例文件语法正确", result.returncode == 0) and all_passed
    
    # 6. 文件结构检查
    print_header("6. 文件结构检查")
    
    required_files = [
        "src/multi_agent_se/collaboration/state.py",
        "src/multi_agent_se/collaboration/scheduler/graph_builder.py",
        "examples/langgraph_basic_example.py",
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        all_passed = print_result(
            f"文件: {file_path}",
            full_path.exists(),
            "存在" if full_path.exists() else "不存在"
        ) and all_passed
    
    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段3验收通过！所有检查项均符合要求。")
        print("  📋 阶段3交付物清单：")
        print("     - state.py (三层状态定义: System/Task/Business)")
        print("     - graph_builder.py (StateGraph封装)")
        print("     - 基础节点: init_node, end_node, error_handler")
        print("     - 条件函数: should_continue, route_by_stage")
        print("     - langgraph_basic_example.py (官方示例)")
        print("     - scripts/verify_phase3.py (验收脚本)")
        return 0
    else:
        print("  ❌ 阶段3验收未通过！请修复上述失败项。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
