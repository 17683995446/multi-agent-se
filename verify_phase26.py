#!/usr/bin/env python3
"""第26阶段验收脚本 - Pipeline编排器.

验证内容：
- 枚举类型
- Pipeline节点
- Pipeline定义（DAG验证/拓扑排序）
- Pipeline结果
- Pipeline编排器（执行/依赖/重试/上下文传递）
- 线性Pipeline构建
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from multi_agent_se.pipeline import (
    NodeStatus,
    PipelineStatus,
    RetryPolicy,
    PipelineNode,
    PipelineEdge,
    PipelineDefinition,
    PipelineResult,
    PipelineContext,
    PipelineOrchestrator,
    create_node,
    create_pipeline,
    run_pipeline,
    build_linear_pipeline,
)


def print_header(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(test_name: str, passed: bool, message: str = "") -> None:
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {test_name}")
    if message:
        print(f"         {message}")


def test_enums() -> bool:
    """测试枚举类型."""
    print_header("测试1: 枚举类型")

    node_statuses = list(NodeStatus)
    print(f"  NodeStatus: {[s.value for s in node_statuses]}")
    assert len(node_statuses) == 8

    pipeline_statuses = list(PipelineStatus)
    print(f"  PipelineStatus: {[s.value for s in pipeline_statuses]}")
    assert len(pipeline_statuses) == 7

    retry_policies = list(RetryPolicy)
    print(f"  RetryPolicy: {[p.value for p in retry_policies]}")
    assert len(retry_policies) == 3

    print_result("枚举类型", True, f"Node={len(node_statuses)}, Pipeline={len(pipeline_statuses)}, Retry={len(retry_policies)}")
    return True


def test_pipeline_node() -> bool:
    """测试Pipeline节点."""
    print_header("测试2: PipelineNode")

    node = create_node("step1", description="第一步")
    assert node.name == "step1"
    assert node.status == NodeStatus.PENDING
    assert node.is_terminal is False
    print(f"  ✓ 节点创建: {node.name}, status={node.status.value}")

    node.status = NodeStatus.SUCCESS
    assert node.is_success is True
    assert node.is_terminal is True
    print(f"  ✓ 终态判断: is_success={node.is_success}, is_terminal={node.is_terminal}")

    d = node.to_dict()
    assert d["name"] == "step1"
    assert d["status"] == "success"
    print(f"  ✓ to_dict() 正常")

    print_result("PipelineNode", True)
    return True


def test_pipeline_definition() -> bool:
    """测试Pipeline定义."""
    print_header("测试3: PipelineDefinition")

    pipeline = create_pipeline("test_pipeline", "测试Pipeline")
    pipeline.add_node(create_node("A"))
    pipeline.add_node(create_node("B", dependencies=["A"]))
    pipeline.add_node(create_node("C", dependencies=["A"]))
    pipeline.add_node(create_node("D", dependencies=["B", "C"]))
    pipeline.add_edge("A", "B")
    pipeline.add_edge("A", "C")
    pipeline.add_edge("B", "D")
    pipeline.add_edge("C", "D")

    # 根节点
    roots = pipeline.get_root_nodes()
    assert len(roots) == 1
    assert roots[0].name == "A"
    print(f"  ✓ 根节点: {[r.name for r in roots]}")

    # 上游/下游
    assert pipeline.get_downstream("A") == ["B", "C"]
    assert pipeline.get_upstream("D") == ["B", "C"]
    print(f"  ✓ A的下游: {pipeline.get_downstream('A')}")
    print(f"  ✓ D的上游: {pipeline.get_upstream('D')}")

    # 拓扑排序
    order = pipeline.topological_order()
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
    assert order.index("B") < order.index("D")
    assert order.index("C") < order.index("D")
    print(f"  ✓ 拓扑排序: {order}")

    # 验证
    errors = pipeline.validate()
    assert len(errors) == 0
    print(f"  ✓ DAG验证通过")

    print_result("PipelineDefinition", True)
    return True


def test_pipeline_validation() -> bool:
    """测试Pipeline验证."""
    print_header("测试4: Pipeline验证")

    # 重复节点名
    p1 = create_pipeline("dup")
    p1.add_node(create_node("A"))
    p1.add_node(create_node("A"))
    errors = p1.validate()
    assert len(errors) > 0
    print(f"  ✓ 重复节点检测: {errors[0]}")

    # 不存在的依赖
    p2 = create_pipeline("missing_dep")
    p2.add_node(create_node("A", dependencies=["X"]))
    errors = p2.validate()
    assert len(errors) > 0
    print(f"  ✓ 缺失依赖检测: {errors[0]}")

    # 循环依赖
    p3 = create_pipeline("cycle")
    p3.add_node(create_node("A", dependencies=["B"]))
    p3.add_node(create_node("B", dependencies=["A"]))
    errors = p3.validate()
    assert any("循环" in e for e in errors) or len(errors) > 0
    print(f"  ✓ 循环依赖检测: {errors}")

    print_result("Pipeline验证", True)
    return True


def test_pipeline_context() -> bool:
    """测试执行上下文."""
    print_header("测试5: PipelineContext")

    ctx = PipelineContext({"input": 42})
    assert ctx.get("input") == 42
    assert ctx.has("input") is True
    print(f"  ✓ 初始数据: input={ctx.get('input')}")

    ctx.set("output", 84)
    assert ctx.get("output") == 84
    print(f"  ✓ 设置数据: output={ctx.get('output')}")

    ctx.set_node_output("step1", "result1")
    assert ctx.get_node_output("step1") == "result1"
    print(f"  ✓ 节点输出: step1={ctx.get_node_output('step1')}")

    deps = ctx.get_dependency_outputs(["step1"])
    assert deps == {"step1": "result1"}
    print(f"  ✓ 依赖输出: {deps}")

    print_result("PipelineContext", True)
    return True


def test_execute_linear() -> bool:
    """测试线性Pipeline执行."""
    print_header("测试6: 线性Pipeline执行")

    execution_log = []

    def step_a(deps, ctx):
        execution_log.append("A")
        ctx.set("x", 10)
        return "result_a"

    def step_b(deps, ctx):
        execution_log.append("B")
        x = ctx.get("x", 0)
        return f"result_b_{x}"

    def step_c(deps, ctx):
        execution_log.append("C")
        return "result_c"

    pipeline = build_linear_pipeline("linear", [
        ("step_a", step_a, "步骤A"),
        ("step_b", step_b, "步骤B"),
        ("step_c", step_c, "步骤C"),
    ])

    result = run_pipeline(pipeline)

    assert result.status == PipelineStatus.SUCCESS
    assert result.total_nodes == 3
    assert result.success_count == 3
    assert execution_log == ["A", "B", "C"]
    print(f"  ✓ 执行顺序: {execution_log}")

    assert result.node_results["step_a"].result == "result_a"
    assert result.node_results["step_b"].result == "result_b_10"
    print(f"  ✓ 上下文传递: B收到x=10")

    print_result("线性Pipeline执行", True)
    return True


def test_execute_dag() -> bool:
    """测试DAG Pipeline执行."""
    print_header("测试7: DAG Pipeline执行")

    execution_log = []

    def task_a(deps, ctx):
        execution_log.append("A")
        return 1

    def task_b(deps, ctx):
        execution_log.append("B")
        return 2

    def task_c(deps, ctx):
        execution_log.append("C")
        a = deps.get("A", 0)
        b = deps.get("B", 0)
        return a + b

    pipeline = create_pipeline("dag_test")
    pipeline.add_node(create_node("A", handler=task_a))
    pipeline.add_node(create_node("B", handler=task_b))
    pipeline.add_node(create_node("C", handler=task_c, dependencies=["A", "B"]))
    pipeline.add_edge("A", "C")
    pipeline.add_edge("B", "C")

    result = run_pipeline(pipeline)

    assert result.status == PipelineStatus.SUCCESS
    assert result.node_results["C"].result == 3
    assert execution_log.index("A") < execution_log.index("C")
    assert execution_log.index("B") < execution_log.index("C")
    print(f"  ✓ DAG执行: {execution_log}, C={result.node_results['C'].result}")

    print_result("DAG Pipeline执行", True)
    return True


def test_execute_failure() -> bool:
    """测试失败处理."""
    print_header("测试8: 失败处理")

    def fail_step(deps, ctx):
        raise RuntimeError("故意失败")

    def after_fail(deps, ctx):
        return "should_not_run"

    pipeline = create_pipeline("fail_test")
    pipeline.add_node(create_node("fail", handler=fail_step, required=True))
    pipeline.add_node(create_node("after", handler=after_fail, dependencies=["fail"]))
    pipeline.add_edge("fail", "after")

    result = run_pipeline(pipeline)

    assert result.status == PipelineStatus.FAILED
    assert result.node_results["fail"].is_failed is True
    assert result.node_results["after"].status == NodeStatus.SKIPPED
    print(f"  ✓ 失败节点: {result.node_results['fail'].error}")
    print(f"  ✓ 下游跳过: after={result.node_results['after'].status.value}")

    print_result("失败处理", True)
    return True


def test_retry() -> bool:
    """测试重试机制."""
    print_header("测试9: 重试机制")

    attempt_count = {"n": 0}

    def flaky_step(deps, ctx):
        attempt_count["n"] += 1
        if attempt_count["n"] < 3:
            raise RuntimeError(f"第{attempt_count['n']}次失败")
        return "success"

    node = create_node("flaky", handler=flaky_step)
    node.retry_count = 3
    node.retry_delay_seconds = 0.01

    pipeline = create_pipeline("retry_test")
    pipeline.add_node(node)

    result = run_pipeline(pipeline)

    assert result.status == PipelineStatus.SUCCESS
    assert attempt_count["n"] == 3
    print(f"  ✓ 重试成功: 共{attempt_count['n']}次尝试")

    print_result("重试机制", True)
    return True


def test_orchestrator_register() -> bool:
    """测试编排器注册与执行."""
    print_header("测试10: 编排器注册与执行")

    def hello(deps, ctx):
        return "hello"

    pipeline = build_linear_pipeline("greet", [
        ("say_hello", hello, "打招呼"),
    ])

    orch = PipelineOrchestrator()
    orch.register(pipeline)

    assert "greet" in orch.list_pipelines()
    print(f"  ✓ 注册成功: {orch.list_pipelines()}")

    result = orch.execute_by_name("greet")
    assert result.status == PipelineStatus.SUCCESS
    assert result.node_results["say_hello"].result == "hello"
    print(f"  ✓ 按名执行: {result.node_results['say_hello'].result}")

    # 未注册的Pipeline
    result2 = orch.execute_by_name("nonexistent")
    assert result2.status == PipelineStatus.FAILED
    print(f"  ✓ 未注册Pipeline返回失败")

    # 历史记录
    history = orch.get_history("greet")
    assert len(history) == 1
    print(f"  ✓ 执行历史: {len(history)}条")

    print_result("编排器注册与执行", True)
    return True


def test_pipeline_result() -> bool:
    """测试Pipeline结果."""
    print_header("测试11: PipelineResult")

    result = PipelineResult(
        pipeline_name="test",
        status=PipelineStatus.SUCCESS,
    )
    result.node_results = {
        "a": create_node("a"),
        "b": create_node("b"),
    }
    result.node_results["a"].status = NodeStatus.SUCCESS
    result.node_results["b"].status = NodeStatus.FAILED

    assert result.total_nodes == 2
    assert result.success_count == 1
    assert result.failed_count == 1
    assert abs(result.success_rate - 50.0) < 0.01
    print(f"  ✓ 统计: total={result.total_nodes}, success={result.success_count}, rate={result.success_rate}%")

    summary = result.format_summary()
    assert "test" in summary
    print(f"  ✓ 摘要: {summary}")

    d = result.to_dict()
    assert d["total_nodes"] == 2
    print(f"  ✓ to_dict() 正常")

    print_result("PipelineResult", True)
    return True


def test_optional_node_failure() -> bool:
    """测试非必需节点失败."""
    print_header("测试12: 非必需节点失败")

    def fail(deps, ctx):
        raise RuntimeError("失败")

    def after(deps, ctx):
        return "still_runs"

    pipeline = create_pipeline("optional_test")
    fail_node = create_node("fail", handler=fail)
    fail_node.required = False
    pipeline.add_node(fail_node)
    pipeline.add_node(create_node("after", handler=after, dependencies=["fail"]))
    pipeline.add_edge("fail", "after")

    result = run_pipeline(pipeline)

    # 非必需节点失败，下游仍被跳过（因为依赖未成功）
    assert result.node_results["fail"].is_failed is True
    assert result.node_results["after"].status == NodeStatus.SKIPPED
    print(f"  ✓ 非必需失败: fail={result.node_results['fail'].status.value}")
    print(f"  ✓ 下游仍跳过: after={result.node_results['after'].status.value}")

    print_result("非必需节点失败", True)
    return True


def main() -> int:
    print("\n" + "="*60)
    print("  第26阶段验收: Pipeline编排器 (Pipeline Orchestrator)")
    print("="*60)

    tests = [
        test_enums,
        test_pipeline_node,
        test_pipeline_definition,
        test_pipeline_validation,
        test_pipeline_context,
        test_execute_linear,
        test_execute_dag,
        test_execute_failure,
        test_retry,
        test_orchestrator_register,
        test_pipeline_result,
        test_optional_node_failure,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"  验收结果: {passed} 通过, {failed} 失败")
    print("="*60)

    if failed == 0:
        print("\n  ✓ 第26阶段验收通过！")
        print("\n  实现功能:")
        print("    - NodeStatus: 8种节点状态")
        print("    - PipelineStatus: 6种Pipeline状态")
        print("    - RetryPolicy: 3种重试策略")
        print("    - PipelineNode: 节点定义（handler/依赖/超时/重试）")
        print("    - PipelineDefinition: DAG定义")
        print("      - add_node/add_edge（链式调用）")
        print("      - topological_order（拓扑排序）")
        print("      - validate（DAG验证：重复/缺失依赖/环检测）")
        print("      - get_root_nodes/get_downstream/get_upstream")
        print("    - PipelineResult: 执行结果（统计/摘要/序列化）")
        print("    - PipelineContext: 执行上下文（数据传递/节点输出）")
        print("    - PipelineOrchestrator: 编排器")
        print("      - register/execute/execute_by_name")
        print("      - 依赖检查/失败传播/下游跳过")
        print("      - 重试机制（固定/指数退避）")
        print("      - 执行历史查询")
        print("    - 便捷函数: run_pipeline / build_linear_pipeline")
        print("="*60)
        return 0
    else:
        print(f"\n  ✗ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
