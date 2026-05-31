#!/usr/bin/env python3
"""阶段11验收验证脚本 - 落地系统四层架构."""
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
    print_header("阶段11验收验证 - 落地系统四层架构")
    all_passed = True
    project_root = Path(__file__).parent.parent

    # 1. ArchitectureLayer枚举检查
    print_header("1. ArchitectureLayer四层枚举")
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.core.architecture.layer_base import ArchitectureLayer

        all_passed = print_result("四层枚举完整", len(ArchitectureLayer) == 4) and all_passed
        all_passed = print_result("INPUT层", ArchitectureLayer.INPUT.level == 3) and all_passed
        all_passed = print_result("SCHEDULER层", ArchitectureLayer.SCHEDULER.level == 2) and all_passed
        all_passed = print_result("AGENT层", ArchitectureLayer.AGENT.level == 1) and all_passed
        all_passed = print_result("EXECUTOR层", ArchitectureLayer.EXECUTOR.level == 0) and all_passed

        # 层级标签
        all_passed = print_result("label属性", ArchitectureLayer.INPUT.label == "输入收敛层") and all_passed
        all_passed = print_result("description属性", len(ArchitectureLayer.SCHEDULER.description) > 0) and all_passed

        # 依赖方向
        all_passed = print_result(
            "INPUT可依赖SCHEDULER",
            ArchitectureLayer.INPUT.can_depend_on(ArchitectureLayer.SCHEDULER),
        ) and all_passed
        all_passed = print_result(
            "INPUT可依赖EXECUTOR",
            ArchitectureLayer.INPUT.can_depend_on(ArchitectureLayer.EXECUTOR),
        ) and all_passed
        all_passed = print_result(
            "EXECUTOR不可依赖INPUT",
            not ArchitectureLayer.EXECUTOR.can_depend_on(ArchitectureLayer.INPUT),
        ) and all_passed
        all_passed = print_result(
            "EXECUTOR不可依赖SCHEDULER",
            not ArchitectureLayer.EXECUTOR.can_depend_on(ArchitectureLayer.SCHEDULER),
        ) and all_passed
        all_passed = print_result(
            "同级可依赖",
            ArchitectureLayer.AGENT.can_depend_on(ArchitectureLayer.AGENT),
        ) and all_passed

        # 比较方法
        all_passed = print_result(
            "is_higher_than",
            ArchitectureLayer.INPUT.is_higher_than(ArchitectureLayer.EXECUTOR),
        ) and all_passed
        all_passed = print_result(
            "is_lower_than",
            ArchitectureLayer.EXECUTOR.is_lower_than(ArchitectureLayer.AGENT),
        ) and all_passed

    except Exception as e:
        all_passed = print_result("ArchitectureLayer", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 2. 四层接口实现检查
    print_header("2. 四层接口实现")
    try:
        from multi_agent_se.core.architecture.layer_base import (
            InputLayer, SchedulerLayer, AgentLayer, ExecutorLayer,
            LayerInterface, get_all_layers,
        )

        layers = get_all_layers()
        all_passed = print_result("get_all_layers返回4层", len(layers) == 4) and all_passed

        # 每层实现LayerInterface
        for layer_inst in layers:
            all_passed = print_result(
                f"{layer_inst.name}实现LayerInterface",
                isinstance(layer_inst, LayerInterface),
            ) and all_passed
            all_passed = print_result(
                f"{layer_inst.name}.layer正确",
                layer_inst.layer == ArchitectureLayer[layer_inst.layer.name],
            ) and all_passed

        # 上游/下游关系
        input_l = InputLayer()
        sched_l = SchedulerLayer()
        agent_l = AgentLayer()
        exec_l = ExecutorLayer()

        all_passed = print_result("InputLayer无上游", input_l.get_upstream_layers() == []) and all_passed
        all_passed = print_result("InputLayer下游=SCHEDULER", input_l.get_downstream_layers() == [ArchitectureLayer.SCHEDULER]) and all_passed
        all_passed = print_result("ExecutorLayer无下游", exec_l.get_downstream_layers() == []) and all_passed
        all_passed = print_result("ExecutorLayer上游=AGENT", exec_l.get_upstream_layers() == [ArchitectureLayer.AGENT]) and all_passed
        all_passed = print_result("SchedulerLayer双向", len(sched_l.get_upstream_layers()) == 1 and len(sched_l.get_downstream_layers()) == 1) and all_passed

        # 模块列表
        all_passed = print_result("AgentLayer含8个模块", len(agent_l.get_modules()) == 8) and all_passed
        all_passed = print_result("ExecutorLayer含15个模块", len(exec_l.get_modules()) == 15) and all_passed
        all_passed = print_result("SchedulerLayer含7个模块", len(sched_l.get_modules()) == 7) and all_passed

    except Exception as e:
        all_passed = print_result("四层接口", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 3. LayerRegistry注册表检查
    print_header("3. LayerRegistry注册表")
    try:
        from multi_agent_se.core.architecture.layer_base import (
            LayerRegistry, LayerModule, ArchitectureLayer,
        )

        reg = LayerRegistry()

        # 注册合法模块
        reg.register(LayerModule("core_config", ArchitectureLayer.EXECUTOR))
        reg.register(LayerModule("agent_dev", ArchitectureLayer.AGENT, dependencies={"core_config"}))
        reg.register(LayerModule("sched_graph", ArchitectureLayer.SCHEDULER, dependencies={"agent_dev"}))
        all_passed = print_result("合法注册成功", reg.total_modules == 3) and all_passed

        # 重复注册
        try:
            reg.register(LayerModule("core_config", ArchitectureLayer.EXECUTOR))
            all_passed = print_result("重复注册应报错", False) and all_passed
        except ValueError:
            all_passed = print_result("重复注册正确拒绝", True) and all_passed

        # 违规依赖
        try:
            reg.register(LayerModule("core_bad", ArchitectureLayer.EXECUTOR, dependencies={"sched_graph"}))
            all_passed = print_result("反向依赖应报错", False) and all_passed
        except ValueError:
            all_passed = print_result("反向依赖正确拒绝", True) and all_passed

        # 验证依赖
        violations = reg.validate_dependencies()
        all_passed = print_result("validate_dependencies无违规", len(violations) == 0) and all_passed

        # 层摘要
        summary = reg.get_layer_summary()
        all_passed = print_result("get_layer_summary", ArchitectureLayer.EXECUTOR in summary) and all_passed

        # 依赖图
        dep_graph = reg.get_dependency_graph()
        all_passed = print_result("get_dependency_graph", "agent_dev" in dep_graph) and all_passed

    except Exception as e:
        all_passed = print_result("LayerRegistry", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 4. 单向数据流验证检查
    print_header("4. 单向数据流验证")
    try:
        from multi_agent_se.core.architecture.data_flow import (
            DataFlowValidator, DataFlowEdge, DataFlowReport,
            FlowViolationType, FlowViolation,
            validate_unidirectional_flow,
            ArchitectureLayer,
        )
        from multi_agent_se.core.architecture.layer_base import LayerRegistry, LayerModule

        # 构建注册表
        reg = LayerRegistry()
        reg.register(LayerModule("m_exec", ArchitectureLayer.EXECUTOR))
        reg.register(LayerModule("m_agent", ArchitectureLayer.AGENT, dependencies={"m_exec"}))
        reg.register(LayerModule("m_sched", ArchitectureLayer.SCHEDULER, dependencies={"m_agent"}))

        validator = DataFlowValidator(reg)
        validator.add_edge("m_sched", "m_agent")  # 合法
        validator.add_edge("m_agent", "m_exec")  # 合法
        validator.add_edge("m_exec", "m_sched")  # 违规！

        report = validator.validate()
        all_passed = print_result("DataFlowReport生成", True) and all_passed
        all_passed = print_result("total_edges=3", report.total_edges == 3) and all_passed
        all_passed = print_result("valid_edges=2", report.valid_edges == 2) and all_passed
        all_passed = print_result("invalid_edges=1", report.invalid_edges == 1) and all_passed
        all_passed = print_result("is_valid=False", not report.is_valid) and all_passed
        all_passed = print_result("violations包含REVERSE", len(report.get_violations_by_type().get("REVERSE_FLOW", [])) == 1) and all_passed

        # DataFlowEdge
        edge = DataFlowEdge("a", ArchitectureLayer.AGENT, "b", ArchitectureLayer.EXECUTOR)
        all_passed = print_result("DataFlowEdge.is_valid", edge.is_valid) and all_passed
        all_passed = print_result("DataFlowEdge.to_dict", "source" in edge.to_dict()) and all_passed

        # validate_layer_flow
        all_passed = print_result(
            "validate_layer_flow(合法)",
            validator.validate_layer_flow(ArchitectureLayer.SCHEDULER, ArchitectureLayer.EXECUTOR),
        ) and all_passed
        all_passed = print_result(
            "validate_layer_flow(违规)",
            not validator.validate_layer_flow(ArchitectureLayer.EXECUTOR, ArchitectureLayer.SCHEDULER),
        ) and all_passed

        # 跨层/层内边
        cross = validator.get_cross_layer_edges()
        intra = validator.get_intra_layer_edges()
        all_passed = print_result("get_cross_layer_edges", len(cross) == 3) and all_passed
        all_passed = print_result("get_intra_layer_edges", len(intra) == 0) and all_passed

        # validate_unidirectional_flow
        report2 = validate_unidirectional_flow(reg)
        all_passed = print_result("validate_unidirectional_flow", report2.is_valid) and all_passed

    except Exception as e:
        all_passed = print_result("单向数据流验证", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 5. 耦合检测检查
    print_header("5. 层间耦合检测")
    try:
        from multi_agent_se.core.architecture.coupling_detector import (
            CouplingDetector, CouplingReport, CouplingRecord, ImportInfo,
        )

        detector = CouplingDetector(project_root=str(project_root))

        # 分析单个源码
        test_source = '''
from multi_agent_se.core.config import Settings
from multi_agent_se.agents.agent_base import BaseAgent
from multi_agent_se.collaboration.state import GraphState
import os
'''
        records = detector.analyze_source(test_source, "test.py", ArchitectureLayer.AGENT)
        all_passed = print_result("analyze_source可用", True) and all_passed
        all_passed = print_result("检测到3个内部import", len(records) == 3) and all_passed

        # 检查耦合方向：AGENT依赖CORE合法，但AGENT依赖SCHEDULER违规
        core_imports = [r for r in records if r.target_layer == ArchitectureLayer.EXECUTOR]
        sched_imports = [r for r in records if r.target_layer == ArchitectureLayer.SCHEDULER]
        all_passed = print_result("AGENT依赖CORE无违规", all(not r.is_violation for r in core_imports)) and all_passed
        all_passed = print_result("AGENT依赖SCHEDULER检测违规", any(r.is_violation for r in sched_imports)) and all_passed

        # 反向依赖检测
        bad_source = '''
from multi_agent_se.agents.agent_base import BaseAgent
'''
        bad_records = detector.analyze_source(bad_source, "bad.py", ArchitectureLayer.EXECUTOR)
        bad_violations = [r for r in bad_records if r.is_violation]
        all_passed = print_result("EXECUTOR依赖AGENT检测违规", len(bad_violations) == 1) and all_passed

        # 分析实际项目目录
        report = detector.analyze_directory(str(project_root / "src" / "multi_agent_se" / "core"))
        all_passed = print_result("analyze_directory可用", True) and all_passed
        all_passed = print_result("CouplingReport.coupling_score", report.coupling_score > 0) and all_passed
        all_passed = print_result("CouplingReport.to_dict", "is_healthy" in report.to_dict()) and all_passed

        # ImportInfo
        imp = ImportInfo(module="test", source_file="f.py", import_type="import", line=1)
        all_passed = print_result("ImportInfo.to_dict", "module" in imp.to_dict()) and all_passed

    except Exception as e:
        all_passed = print_result("耦合检测", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 6. 文件结构检查
    print_header("6. 文件结构检查")
    all_passed = print_result(
        "文件: core/architecture/layer_base.py",
        (project_root / "src/multi_agent_se/core/architecture/layer_base.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: core/architecture/data_flow.py",
        (project_root / "src/multi_agent_se/core/architecture/data_flow.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: core/architecture/coupling_detector.py",
        (project_root / "src/multi_agent_se/core/architecture/coupling_detector.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: core/architecture/__init__.py",
        (project_root / "src/multi_agent_se/core/architecture/__init__.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: scripts/verify_phase11.py",
        Path(__file__).exists(),
    ) and all_passed

    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段11验收通过！所有检查项均符合要求。")
        print("  📋 阶段11交付物清单：")
        print("     - layer_base.py (ArchitectureLayer枚举 + LayerInterface + 4层实现 + LayerRegistry)")
        print("     - data_flow.py (DataFlowValidator + DataFlowReport + 单向流验证)")
        print("     - coupling_detector.py (CouplingDetector + CouplingReport + AST静态分析)")
        print("     - 四层架构代码实现 ✓")
        print("     - 层间接口定义清晰 ✓")
        print("     - 单向数据流验证通过 ✓")
        print("     - 层间耦合度检测通过 ✓")
        return 0
    else:
        print("  ❌ 阶段11验收未通过！")
        return 1


if __name__ == "__main__":
    sys.exit(main())
