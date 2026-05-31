#!/usr/bin/env python3
"""阶段12验收验证脚本 - 全局DAG单向依赖校验机制."""
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
    print_header("阶段12验收验证 - 全局DAG单向依赖校验机制")
    all_passed = True
    project_root = Path(__file__).parent.parent

    # 1. 模块导入检查
    print_header("1. 模块导入检查")
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.core.dag import (
            DAGValidator, dag_validator,
            ViolationType, Violation, DAGValidationResult,
        )
        from multi_agent_se.core.architecture.layer_base import ArchitectureLayer
        from multi_agent_se.core.exceptions import CyclicDependencyError, SchedulerError
        all_passed = print_result("dag模块可导入", True) and all_passed
        all_passed = print_result("全局dag_validator实例", dag_validator is not None) and all_passed
    except Exception as e:
        all_passed = print_result("模块导入", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()
        return 1

    # 2. DAG检测算法
    print_header("2. DAG检测算法")
    try:
        v = DAGValidator()

        # 空图是DAG
        all_passed = print_result("空图是DAG", v.is_dag()) and all_passed

        # 构建合法DAG
        v.add_dependency("A", "B")
        v.add_dependency("A", "C")
        v.add_dependency("B", "D")
        v.add_dependency("C", "D")
        all_passed = print_result("合法DAG构建", v.is_dag()) and all_passed
        all_passed = print_result("节点数=4", v.node_count == 4) and all_passed
        all_passed = print_result("边数=4", v.edge_count == 4) and all_passed

        # 拓扑排序
        topo = v.topological_sort()
        all_passed = print_result("拓扑排序可用", len(topo) == 4) and all_passed
        # D必须在B和C之后
        all_passed = print_result("拓扑顺序正确", topo.index("D") > topo.index("B") and topo.index("D") > topo.index("C")) and all_passed

        # 循环检测
        v2 = DAGValidator(block_on_violation=False)
        v2.add_dependency("X", "Y")
        v2.add_dependency("Y", "Z")
        v2.add_dependency("Z", "X")
        all_passed = print_result("循环图非DAG", not v2.is_dag()) and all_passed

        cycles = v2.find_cycles()
        all_passed = print_result("找到循环", len(cycles) > 0) and all_passed
        all_passed = print_result("循环路径含X,Y,Z", all("X" in c and "Y" in c and "Z" in c for c in cycles)) and all_passed

        # 拓扑排序应失败
        try:
            v2.topological_sort()
            all_passed = print_result("循环图拓扑排序应失败", False) and all_passed
        except ValueError:
            all_passed = print_result("循环图拓扑排序正确报错", True) and all_passed

    except Exception as e:
        all_passed = print_result("DAG检测算法", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 3. 循环依赖自动识别
    print_header("3. 循环依赖自动识别")
    try:
        # 预判循环（不实际添加）
        v3 = DAGValidator(block_on_violation=False)
        v3.add_dependency("P", "Q")
        v3.add_dependency("Q", "R")
        result = v3.add_dependency("R", "P")
        all_passed = print_result("循环检测返回违规", not result.is_valid) and all_passed
        all_passed = print_result("违规类型=CYCLIC", result.has_cycles) and all_passed
        all_passed = print_result("循环路径记录", len(result.violations) > 0 and result.violations[0].cycle_path) and all_passed

        # 自循环
        v4 = DAGValidator(block_on_violation=False)
        result_self = v4.add_dependency("S", "S")
        all_passed = print_result("自循环检测", not result_self.is_valid) and all_passed

        # 多条独立链路（不构成循环）
        v5 = DAGValidator()
        v5.add_dependency("M", "N")
        v5.add_dependency("M", "O")
        v5.add_dependency("N", "P")
        v5.add_dependency("O", "P")
        all_passed = print_result("菱形依赖是DAG", v5.is_dag()) and all_passed

    except Exception as e:
        all_passed = print_result("循环依赖识别", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 4. 循环依赖阻断机制
    print_header("4. 循环依赖阻断机制")
    try:
        # 阻断模式
        v_block = DAGValidator(block_on_violation=True)
        v_block.add_dependency("A1", "B1")
        v_block.add_dependency("B1", "C1")
        try:
            v_block.add_dependency("C1", "A1")
            all_passed = print_result("阻断模式应抛异常", False) and all_passed
        except CyclicDependencyError as e:
            all_passed = print_result("阻断抛出CyclicDependencyError", True) and all_passed
            all_passed = print_result("异常含cycle信息", len(e.cycle) > 0) and all_passed

        # 阻断后边未被添加
        all_passed = print_result("阻断后边未添加", v_block.edge_count == 2) and all_passed
        all_passed = print_result("阻断后仍为DAG", v_block.is_dag()) and all_passed

        # 非阻断模式
        v_noblock = DAGValidator(block_on_violation=False)
        v_noblock.add_dependency("A2", "B2")
        v_noblock.add_dependency("B2", "C2")
        result = v_noblock.add_dependency("C2", "A2")
        all_passed = print_result("非阻断模式不抛异常", True) and all_passed
        all_passed = print_result("非阻断返回违规结果", not result.is_valid) and all_passed

    except Exception as e:
        all_passed = print_result("阻断机制", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 5. 依赖方向强制校验
    print_header("5. 依赖方向强制校验")
    try:
        # 合法方向：AGENT依赖EXECUTOR
        v_dir = DAGValidator(enforce_direction=True, block_on_violation=True)
        v_dir.add_dependency("agent_dev", "core_config", layer=ArchitectureLayer.AGENT)
        all_passed = print_result("AGENT→EXECUTOR合法", v_dir.edge_count == 1) and all_passed

        v_dir.add_dependency("agent_dev", "agent_ctrl", layer=ArchitectureLayer.AGENT)
        all_passed = print_result("AGENT→AGENT同级合法", v_dir.edge_count == 2) and all_passed

        # 违规方向：EXECUTOR依赖AGENT
        try:
            v_dir.add_dependency("core_config", "agent_ctrl", layer=ArchitectureLayer.EXECUTOR)
            all_passed = print_result("EXECUTOR→AGENT应阻断", False) and all_passed
        except SchedulerError:
            all_passed = print_result("EXECUTOR→AGENT阻断成功", True) and all_passed

        # 非阻断模式
        v_dir2 = DAGValidator(enforce_direction=True, block_on_violation=False)
        result = v_dir2.add_dependency("core_log", "agent_ctrl", layer=ArchitectureLayer.EXECUTOR)
        all_passed = print_result("方向违规返回结果", not result.is_valid) and all_passed
        all_passed = print_result("方向违规类型正确", result.has_direction_violations) and all_passed

        # validate_direction批量校验
        v_dir3 = DAGValidator(enforce_direction=True, block_on_violation=False)
        v_dir3.add_dependency("core_a", "agent_x", layer=ArchitectureLayer.EXECUTOR)
        v_dir3.add_dependency("core_b", "agent_y", layer=ArchitectureLayer.EXECUTOR)
        dir_violations = v_dir3.validate_direction()
        all_passed = print_result("批量方向校验", len(dir_violations) == 2) and all_passed

    except Exception as e:
        all_passed = print_result("方向校验", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 6. 完整校验报告
    print_header("6. 完整校验报告")
    try:
        v_full = DAGValidator(enforce_direction=True, block_on_violation=False)
        v_full.add_dependency("sched", "agent", layer=ArchitectureLayer.SCHEDULER)
        v_full.add_dependency("agent", "core", layer=ArchitectureLayer.AGENT)
        v_full.add_dependency("core", "sched", layer=ArchitectureLayer.EXECUTOR)  # 循环+方向违规

        report = v_full.full_validation()
        all_passed = print_result("full_validation可用", True) and all_passed
        all_passed = print_result("报告is_valid=False", not report.is_valid) and all_passed
        all_passed = print_result("报告is_dag=False", not report.is_dag) and all_passed
        all_passed = print_result("报告has_cycles", report.has_cycles) and all_passed
        all_passed = print_result("报告to_dict", "is_valid" in report.to_dict()) and all_passed

        # 合法DAG的完整报告
        v_ok = DAGValidator(enforce_direction=True)
        v_ok.add_dependency("agent", "core", layer=ArchitectureLayer.AGENT)
        v_ok.add_dependency("sched", "agent", layer=ArchitectureLayer.SCHEDULER)
        report_ok = v_ok.full_validation()
        all_passed = print_result("合法DAG报告is_valid", report_ok.is_valid) and all_passed
        all_passed = print_result("合法DAG拓扑排序", len(report_ok.topological_order) == 3) and all_passed

    except Exception as e:
        all_passed = print_result("完整校验", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 7. 查询功能
    print_header("7. 查询功能")
    try:
        v_q = DAGValidator()
        v_q.add_dependency("A", "B")
        v_q.add_dependency("A", "C")
        v_q.add_dependency("B", "D")
        v_q.add_dependency("C", "D")
        v_q.add_dependency("D", "E")

        # 直接依赖
        deps = v_q.get_dependencies("A")
        all_passed = print_result("get_dependencies(A)={B,C}", deps == {"B", "C"}) and all_passed

        # 递归依赖
        all_deps = v_q.get_dependencies("A", recursive=True)
        all_passed = print_result("递归依赖(A)={B,C,D,E}", all_deps == {"B", "C", "D", "E"}) and all_passed

        # 反向查询
        dependents = v_q.get_dependents("D")
        all_passed = print_result("get_dependents(D)={B,C}", dependents == {"B", "C"}) and all_passed

        # 最短路径
        path = v_q.get_shortest_path("A", "E")
        all_passed = print_result("最短路径A→E", path is not None and path[0] == "A" and path[-1] == "E") and all_passed

        # 不存在的路径
        no_path = v_q.get_shortest_path("E", "A")
        all_passed = print_result("反向不可达", no_path is None) and all_passed

        # 移除边
        removed = v_q.remove_dependency("A", "C")
        all_passed = print_result("remove_dependency", removed) and all_passed
        all_passed = print_result("移除后边数=4", v_q.edge_count == 4) and all_passed

        # 移除节点
        removed_node = v_q.remove_node("D")
        all_passed = print_result("remove_node", removed_node) and all_passed
        all_passed = print_result("移除后节点数=4", v_q.node_count == 4) and all_passed

        # 统计
        stats = v_q.get_stats()
        all_passed = print_result("get_stats", "node_count" in stats and "is_dag" in stats) and all_passed

    except Exception as e:
        all_passed = print_result("查询功能", False, str(e)) and all_passed
        import traceback
        traceback.print_exc()

    # 8. 文件结构检查
    print_header("8. 文件结构检查")
    all_passed = print_result(
        "文件: core/dag/dag_validator.py",
        (project_root / "src/multi_agent_se/core/dag/dag_validator.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: core/dag/__init__.py",
        (project_root / "src/multi_agent_se/core/dag/__init__.py").exists(),
    ) and all_passed
    all_passed = print_result(
        "文件: scripts/verify_phase12.py",
        Path(__file__).exists(),
    ) and all_passed

    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段12验收通过！所有检查项均符合要求。")
        print("  📋 阶段12交付物清单：")
        print("     - dag_validator.py (DAGValidator + DAGValidationResult + Violation)")
        print("     - DAG检测算法实现 ✓")
        print("     - 循环依赖自动识别 ✓")
        print("     - 依赖方向强制校验 ✓")
        print("     - 违规阻断机制可用 ✓")
        return 0
    else:
        print("  ❌ 阶段12验收未通过！")
        return 1


if __name__ == "__main__":
    sys.exit(main())
