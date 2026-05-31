"""Pipeline编排器 - 阶段26.

DAG工作流调度执行引擎：
- 拓扑排序调度
- 依赖检查
- 重试机制
- 执行上下文传递
- Pipeline生命周期管理
"""

import copy
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from multi_agent_se.pipeline.models import (
    NodeStatus,
    PipelineDefinition,
    PipelineEdge,
    PipelineNode,
    PipelineResult,
    PipelineStatus,
    RetryPolicy,
    create_node,
    create_pipeline,
)


# ========== 执行上下文 ==========

class PipelineContext:
    """Pipeline执行上下文.

    在节点间传递数据的容器
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None) -> None:
        self._data: Dict[str, Any] = initial_data or {}
        self._node_outputs: Dict[str, Any] = {}  # 节点名 -> 输出结果
        self._metadata: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        """设置上下文数据."""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据."""
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def set_node_output(self, node_name: str, output: Any) -> None:
        """记录节点输出."""
        self._node_outputs[node_name] = output

    def get_node_output(self, node_name: str, default: Any = None) -> Any:
        """获取节点输出."""
        return self._node_outputs.get(node_name, default)

    def get_dependency_outputs(self, dependencies: List[str]) -> Dict[str, Any]:
        """获取所有依赖节点的输出."""
        return {
            dep: self._node_outputs.get(dep)
            for dep in dependencies
            if dep in self._node_outputs
        }

    def all_data(self) -> Dict[str, Any]:
        return copy.deepcopy(self._data)

    def all_node_outputs(self) -> Dict[str, Any]:
        return copy.deepcopy(self._node_outputs)


# ========== Pipeline编排器 ==========

class PipelineOrchestrator:
    """Pipeline编排器.

    负责执行PipelineDefinition中定义的DAG工作流
    """

    def __init__(self) -> None:
        self._pipelines: Dict[str, PipelineDefinition] = {}
        self._history: List[PipelineResult] = []

    # ========== Pipeline注册 ==========

    def register(self, pipeline: PipelineDefinition) -> None:
        """注册Pipeline定义."""
        errors = pipeline.validate()
        if errors:
            raise ValueError(f"Pipeline定义无效: {'; '.join(errors)}")
        self._pipelines[pipeline.name] = pipeline

    def get_pipeline(self, name: str) -> Optional[PipelineDefinition]:
        """获取已注册的Pipeline."""
        return self._pipelines.get(name)

    def list_pipelines(self) -> List[str]:
        """列出所有已注册的Pipeline."""
        return list(self._pipelines.keys())

    # ========== 执行 ==========

    def execute(
        self,
        pipeline: PipelineDefinition,
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """执行Pipeline.

        Args:
            pipeline: Pipeline定义
            initial_data: 初始上下文数据

        Returns:
            PipelineResult
        """
        # 验证
        errors = pipeline.validate()
        if errors:
            return PipelineResult(
                pipeline_name=pipeline.name,
                status=PipelineStatus.FAILED,
                error=f"Pipeline定义无效: {'; '.join(errors)}",
            )

        # 初始化
        context = PipelineContext(initial_data)
        result = PipelineResult(
            pipeline_name=pipeline.name,
            status=PipelineStatus.RUNNING,
            started_at=datetime.now(),
        )

        # 深拷贝节点（避免修改原定义）
        node_map: Dict[str, PipelineNode] = {
            n.name: copy.deepcopy(n) for n in pipeline.nodes
        }

        # 获取拓扑顺序
        execution_order = pipeline.topological_order()

        # 逐节点执行
        for node_name in execution_order:
            node = node_map[node_name]

            # 检查依赖状态
            deps_satisfied, skip_reason = self._check_dependencies(node, node_map)
            if not deps_satisfied:
                node.status = NodeStatus.SKIPPED
                node.error = skip_reason
                result.node_results[node_name] = node
                continue

            # 标记为就绪
            node.status = NodeStatus.READY

            # 执行节点
            self._execute_node(node, context)

            # 记录结果
            result.node_results[node_name] = node

            # 检查是否需要终止Pipeline
            if node.is_failed and node.required:
                # 必需节点失败，标记下游为跳过
                self._mark_downstream_skipped(node_name, pipeline, node_map, result)
                result.status = PipelineStatus.FAILED
                result.error = f"必需节点 '{node_name}' 执行失败: {node.error}"
                break

        # 确定最终状态
        if result.status == PipelineStatus.RUNNING:
            all_terminal = all(n.is_terminal for n in result.node_results.values())
            if all_terminal and result.failed_count == 0:
                result.status = PipelineStatus.SUCCESS
            elif result.failed_count > 0:
                result.status = PipelineStatus.PARTIAL

        result.finished_at = datetime.now()
        if result.started_at:
            result.duration_seconds = (result.finished_at - result.started_at).total_seconds()

        self._history.append(result)
        return result

    def execute_by_name(
        self,
        name: str,
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """按名称执行已注册的Pipeline."""
        pipeline = self._pipelines.get(name)
        if pipeline is None:
            return PipelineResult(
                pipeline_name=name,
                status=PipelineStatus.FAILED,
                error=f"Pipeline '{name}' 未注册",
            )
        return self.execute(pipeline, initial_data)

    # ========== 内部方法 ==========

    def _check_dependencies(
        self,
        node: PipelineNode,
        node_map: Dict[str, PipelineNode],
    ) -> tuple:
        """检查依赖是否满足.

        Returns:
            (是否满足, 跳过原因)
        """
        for dep_name in node.dependencies:
            dep_node = node_map.get(dep_name)
            if dep_node is None:
                return False, f"依赖节点 '{dep_name}' 不存在"
            if dep_node.is_failed:
                return False, f"依赖节点 '{dep_name}' 执行失败"
            if dep_node.status == NodeStatus.SKIPPED:
                return False, f"依赖节点 '{dep_name}' 被跳过"
            if not dep_node.is_terminal:
                return False, f"依赖节点 '{dep_name}' 尚未完成"
        return True, ""

    def _execute_node(
        self,
        node: PipelineNode,
        context: PipelineContext,
    ) -> None:
        """执行单个节点（含重试）."""
        if node.handler is None:
            node.status = NodeStatus.SUCCESS
            node.result = None
            context.set_node_output(node.name, None)
            return

        max_attempts = 1 + node.retry_count

        for attempt in range(max_attempts):
            node.attempt = attempt + 1
            node.status = NodeStatus.RUNNING
            node.started_at = datetime.now()

            try:
                # 准备输入：依赖节点的输出
                dep_outputs = context.get_dependency_outputs(node.dependencies)
                # 调用handler
                output = node.handler(dep_outputs, context)
                # 记录结果
                node.status = NodeStatus.SUCCESS
                node.result = output
                node.error = None
                context.set_node_output(node.name, output)
                return

            except Exception as e:
                node.error = str(e)
                node.finished_at = datetime.now()
                if node.started_at:
                    node.duration_seconds = (node.finished_at - node.started_at).total_seconds()

                # 最后一次尝试失败
                if attempt == max_attempts - 1:
                    node.status = NodeStatus.FAILED
                    return

                # 等待后重试
                node.status = NodeStatus.RETRYING
                delay = self._calculate_retry_delay(node, attempt)
                time.sleep(delay)

    def _calculate_retry_delay(self, node: PipelineNode, attempt: int) -> float:
        """计算重试延迟."""
        if node.retry_policy == RetryPolicy.EXPONENTIAL:
            return node.retry_delay_seconds * (2 ** attempt)
        return node.retry_delay_seconds

    def _mark_downstream_skipped(
        self,
        failed_node: str,
        pipeline: PipelineDefinition,
        node_map: Dict[str, PipelineNode],
        result: PipelineResult,
    ) -> None:
        """标记所有下游节点为跳过."""
        visited: set = set()
        queue = [failed_node]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            for downstream in pipeline.get_downstream(current):
                if downstream not in result.node_results:
                    node = node_map[downstream]
                    node.status = NodeStatus.SKIPPED
                    node.error = f"上游节点 '{failed_node}' 失败"
                    result.node_results[downstream] = node
                    queue.append(downstream)

    # ========== 历史查询 ==========

    def get_history(self, pipeline_name: str = "") -> List[PipelineResult]:
        """获取执行历史."""
        if pipeline_name:
            return [r for r in self._history if r.pipeline_name == pipeline_name]
        return list(self._history)

    def get_last_result(self, pipeline_name: str) -> Optional[PipelineResult]:
        """获取最近一次执行结果."""
        for r in reversed(self._history):
            if r.pipeline_name == pipeline_name:
                return r
        return None


# ========== 便捷函数 ==========

def run_pipeline(
    pipeline: PipelineDefinition,
    initial_data: Optional[Dict[str, Any]] = None,
) -> PipelineResult:
    """快速执行Pipeline的便捷函数."""
    orchestrator = PipelineOrchestrator()
    return orchestrator.execute(pipeline, initial_data)


def build_linear_pipeline(
    name: str,
    steps: List[tuple],
    description: str = "",
) -> PipelineDefinition:
    """构建线性Pipeline的便捷函数.

    Args:
        name: Pipeline名称
        steps: 步骤列表，每项为 (name, handler, description)
        description: Pipeline描述

    Returns:
        PipelineDefinition
    """
    pipeline = create_pipeline(name, description)

    prev_name = None
    for step_name, handler, desc in steps:
        deps = [prev_name] if prev_name else []
        node = create_node(step_name, handler=handler, dependencies=deps, description=desc)
        pipeline.add_node(node)
        if prev_name:
            pipeline.add_edge(prev_name, step_name)
        prev_name = step_name

    return pipeline
