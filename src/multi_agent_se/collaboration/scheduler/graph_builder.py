"""LangGraph状态图构建器 - 阶段3.

复用LangGraph开源内核，实现基础调度能力
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar
from functools import wraps

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from multi_agent_se.collaboration.state import GraphState, TaskStatus, create_initial_state


# 节点函数类型
NodeFunction = Callable[[GraphState], GraphState]


class GraphBuilder:
    """状态图构建器.
    
    封装LangGraph StateGraph，提供简化的API
    """
    
    def __init__(self, name: str = "default") -> None:
        """初始化图构建器.
        
        Args:
            name: 图名称
        """
        self.name = name
        self._graph = StateGraph(GraphState)
        self._nodes: Dict[str, NodeFunction] = {}
        self._edges: List[tuple] = []
        self._conditional_edges: List[tuple] = []
        self._entry_point: Optional[str] = None
        self._compiled = False
        self._compiled_graph = None
    
    def add_node(self, name: str, func: NodeFunction) -> "GraphBuilder":
        """添加节点.
        
        Args:
            name: 节点名称
            func: 节点处理函数
            
        Returns:
            self，支持链式调用
        """
        self._nodes[name] = func
        self._graph.add_node(name, func)
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> "GraphBuilder":
        """添加边.
        
        Args:
            from_node: 起始节点
            to_node: 目标节点
            
        Returns:
            self，支持链式调用
        """
        self._edges.append((from_node, to_node))
        self._graph.add_edge(from_node, to_node)
        return self
    
    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable[[GraphState], str],
        to_nodes: Dict[str, str]
    ) -> "GraphBuilder":
        """添加条件边.
        
        Args:
            from_node: 起始节点
            condition: 条件函数，返回目标节点名称
            to_nodes: 条件映射 {返回值: 目标节点}
            
        Returns:
            self，支持链式调用
        """
        self._conditional_edges.append((from_node, condition, to_nodes))
        self._graph.add_conditional_edges(from_node, condition, to_nodes)
        return self
    
    def set_entry_point(self, node_name: str) -> "GraphBuilder":
        """设置入口点.
        
        Args:
            node_name: 入口节点名称
            
        Returns:
            self，支持链式调用
        """
        self._entry_point = node_name
        self._graph.set_entry_point(node_name)
        return self
    
    def compile(self, checkpoint: bool = True) -> "GraphBuilder":
        """编译图.
        
        Args:
            checkpoint: 是否启用检查点
            
        Returns:
            self，支持链式调用
        """
        if checkpoint:
            memory = MemorySaver()
            self._compiled_graph = self._graph.compile(checkpointer=memory)
        else:
            self._compiled_graph = self._graph.compile()
        self._compiled = True
        return self
    
    def invoke(
        self,
        input_state: Optional[GraphState] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> GraphState:
        """执行图.
        
        Args:
            input_state: 输入状态
            config: 运行配置
            
        Returns:
            最终状态
        """
        if not self._compiled:
            self.compile()
        
        if input_state is None:
            input_state = create_initial_state()
        
        return self._compiled_graph.invoke(input_state, config=config)
    
    def stream(
        self,
        input_state: Optional[GraphState] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """流式执行图.
        
        Args:
            input_state: 输入状态
            config: 运行配置
            
        Yields:
            状态更新
        """
        if not self._compiled:
            self.compile()
        
        if input_state is None:
            input_state = create_initial_state()
        
        yield from self._compiled_graph.stream(input_state, config=config)
    
    def get_graph_info(self) -> Dict[str, Any]:
        """获取图信息.
        
        Returns:
            图信息字典
        """
        return {
            "name": self.name,
            "nodes": list(self._nodes.keys()),
            "edges": self._edges,
            "conditional_edges": len(self._conditional_edges),
            "entry_point": self._entry_point,
            "compiled": self._compiled,
        }


# ========== 预定义节点 ==========

def init_node(state: GraphState) -> GraphState:
    """初始化节点.
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    state["status"] = TaskStatus.RUNNING.value
    state["current_stage"] = "init"
    state["messages"].append({
        "role": "system",
        "content": "任务初始化完成",
        "stage": "init"
    })
    return state


def end_node(state: GraphState) -> GraphState:
    """结束节点.
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    if state["error"]:
        state["status"] = TaskStatus.FAILED.value
    else:
        state["status"] = TaskStatus.COMPLETED.value
        state["progress"] = 100.0
    
    state["current_stage"] = "end"
    state["should_continue"] = False
    state["messages"].append({
        "role": "system",
        "content": f"任务结束，状态: {state['status']}",
        "stage": "end"
    })
    return state


def error_handler(state: GraphState) -> GraphState:
    """错误处理节点.
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    state["status"] = TaskStatus.FAILED.value
    state["should_continue"] = False
    state["messages"].append({
        "role": "system",
        "content": f"错误处理: {state.get('error', '未知错误')}",
        "stage": "error"
    })
    return state


# ========== 条件函数 ==========

def should_continue(state: GraphState) -> str:
    """判断是否继续执行.
    
    Args:
        state: 当前状态
        
    Returns:
        下一个节点名称
    """
    if state.get("error"):
        return "error"
    if not state.get("should_continue", True):
        return "end"
    return "continue"


def route_by_stage(state: GraphState) -> str:
    """根据当前阶段路由.
    
    Args:
        state: 当前状态
        
    Returns:
        下一个节点名称
    """
    return state.get("next_stage", "end")


# ========== 快捷构建函数 ==========

def create_simple_graph() -> GraphBuilder:
    """创建简单流程图.
    
    Returns:
        图构建器
    """
    builder = GraphBuilder("simple")
    
    # 添加节点
    builder.add_node("init", init_node)
    builder.add_node("end", end_node)
    builder.add_node("error", error_handler)
    
    # 设置入口
    builder.set_entry_point("init")
    
    # 添加边
    builder.add_edge("init", "end")
    
    return builder


def create_conditional_graph() -> GraphBuilder:
    """创建条件流程图.
    
    Returns:
        图构建器
    """
    builder = GraphBuilder("conditional")
    
    # 添加节点
    builder.add_node("init", init_node)
    builder.add_node("end", end_node)
    builder.add_node("error", error_handler)
    
    # 设置入口
    builder.set_entry_point("init")
    
    # 添加条件边
    builder.add_conditional_edge(
        "init",
        should_continue,
        {
            "continue": "end",
            "error": "error",
            "end": "end"
        }
    )
    
    # 错误处理到结束
    builder.add_edge("error", "end")
    
    return builder
