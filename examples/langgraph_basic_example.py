#!/usr/bin/env python3
"""LangGraph基础示例 - 阶段3.

演示StateGraph的基本使用
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multi_agent_se.collaboration.scheduler.graph_builder import (
    create_simple_graph,
    create_conditional_graph,
    GraphBuilder,
    init_node,
    end_node,
)
from multi_agent_se.collaboration.state import create_initial_state, GraphState


def example_1_simple_graph():
    """示例1：简单流程图."""
    print("\n" + "="*60)
    print("示例1：简单流程图")
    print("="*60)
    
    # 创建图（不使用checkpoint）
    builder = create_simple_graph()
    builder.compile(checkpoint=False)
    
    # 查看图信息
    info = builder.get_graph_info()
    print(f"\n图信息: {info}")
    
    # 执行图
    initial_state = create_initial_state(
        task_type="simple_task",
        input_data={"message": "Hello, LangGraph!"}
    )
    
    print("\n开始执行...")
    result = builder.invoke(initial_state)
    
    print(f"\n执行结果:")
    print(f"  任务ID: {result['task_id']}")
    print(f"  任务类型: {result['task_type']}")
    print(f"  状态: {result['status']}")
    print(f"  当前阶段: {result['current_stage']}")
    print(f"  进度: {result['progress']}%")
    print(f"  消息数: {len(result['messages'])}")
    print(f"  消息内容:")
    for msg in result['messages']:
        print(f"    - [{msg['stage']}] {msg['role']}: {msg['content']}")
    
    return result


def example_2_conditional_graph():
    """示例2：条件流程图."""
    print("\n" + "="*60)
    print("示例2：条件流程图")
    print("="*60)
    
    # 创建图
    builder = create_conditional_graph()
    builder.compile(checkpoint=False)
    
    # 查看图信息
    info = builder.get_graph_info()
    print(f"\n图信息: {info}")
    
    # 执行图（正常流程）
    print("\n--- 正常流程 ---")
    initial_state = create_initial_state(
        task_type="conditional_task",
        input_data={"test": "normal"}
    )
    
    result = builder.invoke(initial_state)
    print(f"状态: {result['status']}")
    print(f"消息数: {len(result['messages'])}")
    
    return result


def main():
    """主函数."""
    print("\n" + "="*60)
    print("LangGraph基础示例 - 阶段3")
    print("="*60)
    
    try:
        # 运行示例
        example_1_simple_graph()
        example_2_conditional_graph()
        
        print("\n" + "="*60)
        print("✅ 所有示例执行成功！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
