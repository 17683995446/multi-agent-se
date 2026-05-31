#!/usr/bin/env python3
"""阶段2验收验证脚本.

验证内容：
1. 项目目录符合四级原子化结构
2. 无循环导入风险
3. 目录层级≤4层
4. README说明目录用途
5. 单向依赖图（DAG）验证
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
    print_header("阶段2验收验证 - 初始化项目目录架构")
    
    all_passed = True
    project_root = Path(__file__).parent.parent
    
    # 1. 四级原子化目录结构检查
    print_header("1. 四级原子化目录结构检查")
    
    required_dirs = {
        # 核心层
        "src/multi_agent_se/core": "核心底座",
        "src/multi_agent_se/core/config": "配置管理",
        "src/multi_agent_se/core/logging": "日志管理",
        "src/multi_agent_se/core/exceptions": "异常处理",
        "src/multi_agent_se/core/paths": "路径管理",
        
        # Agent层（8大Agent）
        "src/multi_agent_se/agents": "Agent层",
        "src/multi_agent_se/agents/controller": "总控Agent",
        "src/multi_agent_se/agents/requirement": "需求拆解Agent",
        "src/multi_agent_se/agents/architect": "架构Agent",
        "src/multi_agent_se/agents/developer": "开发Agent",
        "src/multi_agent_se/agents/bugfix": "缺陷排查Agent",
        "src/multi_agent_se/agents/reviewer": "评审Agent",
        "src/multi_agent_se/agents/tester": "测试Agent",
        "src/multi_agent_se/agents/documenter": "文档Agent",
        
        # 原子化层（四级）
        "src/multi_agent_se/atomicity": "原子化层",
        "src/multi_agent_se/atomicity/variable": "变量原子",
        "src/multi_agent_se/atomicity/method": "方法原子",
        "src/multi_agent_se/atomicity/class_atom": "类原子",
        "src/multi_agent_se/atomicity/module_atom": "模块原子",
        
        # 协作层
        "src/multi_agent_se/collaboration": "协作层",
        "src/multi_agent_se/collaboration/scheduler": "调度器",
        "src/multi_agent_se/collaboration/dispatcher": "分发器",
        "src/multi_agent_se/collaboration/negotiator": "协商器",
        "src/multi_agent_se/collaboration/algorithm": "协作算法",
        
        # 流水线层
        "src/multi_agent_se/pipeline": "流水线层",
        "src/multi_agent_se/pipeline/stages": "流水线阶段",
        "src/multi_agent_se/pipeline/branches": "流水线分支",
        "src/multi_agent_se/pipeline/workflow": "工作流",
        
        # 质量层
        "src/multi_agent_se/quality": "质量层",
        "src/multi_agent_se/quality/linter": "代码检查",
        "src/multi_agent_se/quality/security": "安全扫描",
        "src/multi_agent_se/quality/coverage": "覆盖率分析",
        "src/multi_agent_se/quality/metrics": "质量指标",
        
        # 工具层
        "src/multi_agent_se/utils": "工具层",
        "src/multi_agent_se/utils/helpers": "辅助函数",
        "src/multi_agent_se/utils/validators": "验证器",
        "src/multi_agent_se/utils/converters": "转换器",
        
        # 测试目录
        "tests/unit": "单元测试",
        "tests/integration": "集成测试",
        
        # 配置目录
        "config": "配置目录",
        "docs": "文档目录",
        "scripts": "脚本目录",
    }
    
    for dir_path, desc in required_dirs.items():
        full_path = project_root / dir_path
        all_passed &= print_result(
            f"{desc}: {dir_path}",
            full_path.exists(),
            "存在" if full_path.exists() else "不存在"
        )
    
    # 2. 目录层级检查
    print_header("2. 目录层级检查（≤4层）")
    
    src_dir = project_root / "src"
    max_depth = 0
    deep_paths = []
    
    for file_path in src_dir.rglob("*"):
        rel_path = file_path.relative_to(src_dir)
        depth = len(rel_path.parts)
        if depth > max_depth:
            max_depth = depth
        if depth > 4:
            deep_paths.append(str(rel_path))
    
    all_passed &= print_result(
        "最大目录层级 ≤ 4",
        max_depth <= 4,
        f"当前最大层级: {max_depth}"
    )
    
    if deep_paths:
        print(f"  ⚠️ 超过4层的路径: {deep_paths}")
    
    # 3. __init__.py文件检查
    print_header("3. 模块初始化文件检查")
    
    init_count = 0
    missing_init = []
    
    for dir_path in src_dir.rglob("*"):
        if dir_path.is_dir():
            init_file = dir_path / "__init__.py"
            if init_file.exists():
                init_count += 1
            else:
                # 检查目录是否包含.py文件
                has_py = list(dir_path.glob("*.py"))
                if has_py:
                    missing_init.append(str(dir_path.relative_to(project_root)))
    
    all_passed &= print_result(
        "所有模块包含__init__.py",
        len(missing_init) == 0,
        f"已创建: {init_count}个"
    )
    
    if missing_init:
        print(f"  ⚠️ 缺少__init__.py: {missing_init[:5]}...")
    
    # 4. 单向依赖图验证
    print_header("4. 单向依赖图（DAG）验证")
    
    try:
        sys.path.insert(0, str(project_root / "src"))
        from multi_agent_se.core.dependency_graph import (
            dependency_graph,
            LayerType,
            MODULE_DEPENDENCIES
        )
        
        # 检查是否为DAG
        is_dag = dependency_graph.is_dag()
        all_passed &= print_result("依赖图为DAG（无环）", is_dag)
        
        # 检查循环依赖
        cycles = dependency_graph.find_cycles()
        all_passed &= print_result("无循环依赖", len(cycles) == 0, f"发现循环: {len(cycles)}个")
        
        if cycles:
            print(f"  ⚠️ 循环依赖: {cycles}")
        
        # 检查依赖方向
        valid_direction, violations = dependency_graph.validate_dependency_direction()
        all_passed &= print_result(
            "依赖方向正确（上层依赖下层）",
            valid_direction,
            f"违规: {len(violations)}个"
        )
        
        if violations:
            print(f"  ⚠️ 依赖方向违规: {violations[:3]}...")
        
        # 拓扑排序验证
        try:
            topo_order = dependency_graph.topological_sort()
            all_passed &= print_result(
                "拓扑排序成功",
                True,
                f"模块数: {len(topo_order)}"
            )
        except ValueError as e:
            all_passed &= print_result("拓扑排序成功", False, str(e))
        
        # 层级模块统计
        print("\n  📊 各层级模块统计:")
        for layer in [LayerType.EXECUTOR, LayerType.AGENT, LayerType.SCHEDULER, LayerType.INPUT]:
            modules = dependency_graph.get_layer_modules(layer)
            print(f"     - {layer.value}: {len(modules)}个模块")
        
    except Exception as e:
        all_passed &= print_result("依赖图模块加载", False, str(e))
    
    # 5. README检查
    print_header("5. README文档检查")
    
    readme = project_root / "README.md"
    if readme.exists():
        content = readme.read_text()
        all_passed &= print_result("README.md存在", True)
        all_passed &= print_result("包含项目结构说明", "项目结构" in content or "四级原子化" in content)
        all_passed &= print_result("包含依赖关系说明", "依赖" in content or "DAG" in content)
        all_passed &= print_result("包含安装说明", "安装" in content or "install" in content.lower())
    else:
        all_passed &= print_result("README.md存在", False)
    
    # 总结
    print_header("验收结果总结")
    if all_passed:
        print("  ✅ 阶段2验收通过！所有检查项均符合要求。")
        print("  📋 阶段2交付物清单：")
        print("     - 四级原子化目录结构（core/agents/atomicity/collaboration/pipeline/quality/utils）")
        print("     - 8大Agent目录（controller/requirement/architect/developer/bugfix/reviewer/tester/documenter）")
        print("     - 四级原子化目录（variable/method/class_atom/module_atom）")
        print("     - dependency_graph.py 单向依赖图（DAG验证通过）")
        print("     - README.md 目录结构说明")
        print("     - scripts/verify_phase2.py 验收脚本")
        return 0
    else:
        print("  ❌ 阶段2验收未通过！请修复上述失败项。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
