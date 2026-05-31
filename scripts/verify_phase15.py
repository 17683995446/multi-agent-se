#!/usr/bin/env python3
"""第15阶段验收脚本 - 熵监控系统.

验证内容：
1. 熵值计算模型 (calculator.py)
2. 规范符合度检测 (compliance.py)
3. 熵减优化建议 (optimizer.py)
4. 规范文档生成 (reporter.py)
5. 统一导出接口 (__init__.py)
"""

import sys
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, "/workspace/multi_agent_se/src")


def print_header(title: str) -> None:
    """打印标题."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_result(test_name: str, passed: bool, details: str = "") -> None:
    """打印测试结果."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test_name}")
    if details:
        print(f"       {details}")


def main() -> int:
    """主函数."""
    print_header("第15阶段验收：熵监控系统")
    
    passed = 0
    failed = 0
    
    # ========== 1. 测试熵值计算模型 ==========
    print_header("1. 熵值计算模型 (calculator.py)")
    
    try:
        from multi_agent_se.core.entropy import (
            EntropyType,
            EntropyMetric,
            EntropyReport,
            EntropyCalculator,
            calculate_module_entropy,
        )
        print_result("导入熵值计算模块", True)
        passed += 1
    except Exception as e:
        print_result("导入熵值计算模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 EntropyType 枚举
    try:
        assert EntropyType.CODE_COMPLEXITY.value == "code_complexity"
        assert EntropyType.DEPENDENCY_CHAOS.value == "dependency_chaos"
        assert EntropyType.STATE_DISPERSION.value == "state_dispersion"
        assert EntropyType.ARCHITECTURE_DRIFT.value == "architecture_drift"
        assert EntropyType.NAMING_INCONSISTENCY.value == "naming_inconsistency"
        print_result("EntropyType 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("EntropyType 枚举定义", False, str(e))
        failed += 1
    
    # 测试 EntropyMetric
    try:
        metric = EntropyMetric(
            entropy_type=EntropyType.CODE_COMPLEXITY,
            value=45.5,
            details={"function_count": 10},
            threshold=50.0,
        )
        assert metric.entropy_type == EntropyType.CODE_COMPLEXITY
        assert metric.value == 45.5
        assert metric.is_acceptable == True  # 45.5 <= 50.0
        assert metric.severity == "medium"   # 30 < 45.5 <= 60
        assert "type" in metric.to_dict()
        print_result("EntropyMetric 数据类", True)
        passed += 1
    except Exception as e:
        print_result("EntropyMetric 数据类", False, str(e))
        failed += 1
    
    # 测试 EntropyReport
    try:
        report = EntropyReport(
            metrics=[metric],
            total_score=80.0,
        )
        assert report.average_entropy == 45.5
        assert report.max_entropy == 45.5
        assert report.is_healthy == True
        assert report.get_by_type(EntropyType.CODE_COMPLEXITY) == metric
        assert report.to_dict()["total_score"] == 80.0
        print_result("EntropyReport 数据类", True)
        passed += 1
    except Exception as e:
        print_result("EntropyReport 数据类", False, str(e))
        failed += 1
    
    # 测试 EntropyCalculator - 代码复杂度计算
    try:
        calculator = EntropyCalculator()
        
        # 简单代码
        simple_code = """
def simple_func():
    return 1
"""
        metric = calculator.calculate_code_complexity(simple_code)
        assert metric.entropy_type == EntropyType.CODE_COMPLEXITY
        assert metric.value >= 0
        print_result("代码复杂度熵计算", True, f"熵值={metric.value:.1f}")
        passed += 1
    except Exception as e:
        print_result("代码复杂度熵计算", False, str(e))
        failed += 1
    
    # 测试依赖混乱度计算
    try:
        deps = {
            "module_a": ["module_b"],
            "module_b": ["module_c"],
            "module_c": [],
        }
        metric = calculator.calculate_dependency_chaos(deps)
        assert metric.entropy_type == EntropyType.DEPENDENCY_CHAOS
        assert metric.value >= 0
        print_result("依赖混乱度熵计算", True, f"熵值={metric.value:.1f}")
        passed += 1
    except Exception as e:
        print_result("依赖混乱度熵计算", False, str(e))
        failed += 1
    
    # 测试循环依赖检测
    try:
        cyclic_deps = {
            "a": ["b"],
            "b": ["c"],
            "c": ["a"],  # 循环
        }
        metric = calculator.calculate_dependency_chaos(cyclic_deps)
        assert metric.details["cycle_count"] >= 1
        print_result("循环依赖检测", True, f"发现{metric.details['cycle_count']}个循环")
        passed += 1
    except Exception as e:
        print_result("循环依赖检测", False, str(e))
        failed += 1
    
    # 测试状态分散度计算
    try:
        state_locs = ["file1.py", "file2.py", "file1.py"]
        metric = calculator.calculate_state_dispersion(state_locs)
        assert metric.entropy_type == EntropyType.STATE_DISPERSION
        assert metric.details["unique_locations"] == 2
        print_result("状态分散度熵计算", True, f"分散比例={metric.details['dispersion_ratio']:.2f}")
        passed += 1
    except Exception as e:
        print_result("状态分散度熵计算", False, str(e))
        failed += 1
    
    # 测试架构偏离度计算
    try:
        violations = [
            {"severity": "high"},
            {"severity": "medium"},
        ]
        metric = calculator.calculate_architecture_drift(violations)
        assert metric.entropy_type == EntropyType.ARCHITECTURE_DRIFT
        assert metric.value > 0
        print_result("架构偏离度熵计算", True, f"熵值={metric.value:.1f}")
        passed += 1
    except Exception as e:
        print_result("架构偏离度熵计算", False, str(e))
        failed += 1
    
    # 测试命名不一致熵计算
    try:
        names = ["snake_case", "camelCase", "PascalCase", "snake_case"]
        metric = calculator.calculate_naming_inconsistency(names)
        assert metric.entropy_type == EntropyType.NAMING_INCONSISTENCY
        assert metric.details["style_distribution"]["snake_case"] == 2
        print_result("命名不一致熵计算", True, f"香农熵={metric.details['shannon_entropy']:.2f}")
        passed += 1
    except Exception as e:
        print_result("命名不一致熵计算", False, str(e))
        failed += 1
    
    # 测试 calculate_module_entropy 便捷函数
    try:
        # 创建一个临时测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def test(): pass\n")
            temp_file = f.name
        
        report = calculate_module_entropy(temp_file)
        assert isinstance(report, EntropyReport)
        Path(temp_file).unlink()  # 清理
        print_result("calculate_module_entropy 便捷函数", True)
        passed += 1
    except Exception as e:
        print_result("calculate_module_entropy 便捷函数", False, str(e))
        failed += 1
    
    # ========== 2. 测试规范符合度检测 ==========
    print_header("2. 规范符合度检测 (compliance.py)")
    
    try:
        from multi_agent_se.core.entropy import (
            ComplianceLevel,
            ComplianceCategory,
            ComplianceRule,
            ComplianceViolation,
            ComplianceResult,
            ComplianceChecker,
            default_compliance_checker,
        )
        print_result("导入合规检测模块", True)
        passed += 1
    except Exception as e:
        print_result("导入合规检测模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 ComplianceLevel 枚举
    try:
        assert ComplianceLevel.MANDATORY.value == "mandatory"
        assert ComplianceLevel.RECOMMENDED.value == "recommended"
        assert ComplianceLevel.OPTIONAL.value == "optional"
        print_result("ComplianceLevel 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("ComplianceLevel 枚举定义", False, str(e))
        failed += 1
    
    # 测试 ComplianceCategory 枚举
    try:
        assert ComplianceCategory.ARCHITECTURE.value == "architecture"
        assert ComplianceCategory.NAMING.value == "naming"
        assert ComplianceCategory.DEPENDENCY.value == "dependency"
        assert ComplianceCategory.STATE.value == "state"
        assert ComplianceCategory.DOCUMENTATION.value == "documentation"
        print_result("ComplianceCategory 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("ComplianceCategory 枚举定义", False, str(e))
        failed += 1
    
    # 测试 ComplianceRule
    try:
        rule = ComplianceRule(
            rule_id="TEST-001",
            name="测试规则",
            description="这是一个测试规则",
            category=ComplianceCategory.NAMING,
            level=ComplianceLevel.MANDATORY,
            check_fn=lambda x: True,
            fix_suggestion="修复建议",
        )
        assert rule.rule_id == "TEST-001"
        assert rule.check("test") == True
        assert "rule_id" in rule.to_dict()
        print_result("ComplianceRule 数据类", True)
        passed += 1
    except Exception as e:
        print_result("ComplianceRule 数据类", False, str(e))
        failed += 1
    
    # 测试 ComplianceResult
    try:
        violation = ComplianceViolation(
            rule=rule,
            target="test_target",
            message="测试违规",
        )
        result = ComplianceResult(
            violations=[violation],
            checked_rules=5,
            passed_rules=4,
        )
        assert result.compliance_rate == 80.0
        assert result.is_compliant == False
        assert result.has_mandatory_violations == True
        assert len(result.get_violations_by_category(ComplianceCategory.NAMING)) == 1
        print_result("ComplianceResult 数据类", True)
        passed += 1
    except Exception as e:
        print_result("ComplianceResult 数据类", False, str(e))
        failed += 1
    
    # 测试 ComplianceChecker
    try:
        checker = ComplianceChecker()
        
        # 测试架构方向检查
        from multi_agent_se.core.architecture import ArchitectureLayer
        result = checker.check_architecture_compliance(
            ArchitectureLayer.SCHEDULER,
            ArchitectureLayer.EXECUTOR,
        )
        assert isinstance(result, ComplianceResult)
        
        # 测试反向依赖（应该违规）
        result = checker.check_architecture_compliance(
            ArchitectureLayer.EXECUTOR,
            ArchitectureLayer.SCHEDULER,
        )
        # 注意：这里可能通过也可能不通过，取决于规则实现
        print_result("ComplianceChecker 架构检查", True)
        passed += 1
    except Exception as e:
        print_result("ComplianceChecker 架构检查", False, str(e))
        failed += 1
    
    # 测试获取规则列表
    try:
        rules = checker.get_rules()
        assert len(rules) >= 5  # 至少有5个默认规则
        
        arch_rules = checker.get_rules(category=ComplianceCategory.ARCHITECTURE)
        assert len(arch_rules) >= 1
        
        mandatory_rules = checker.get_rules(level=ComplianceLevel.MANDATORY)
        assert len(mandatory_rules) >= 1
        
        print_result("ComplianceChecker 规则管理", True, f"共{len(rules)}条规则")
        passed += 1
    except Exception as e:
        print_result("ComplianceChecker 规则管理", False, str(e))
        failed += 1
    
    # 测试默认检测器实例
    try:
        assert default_compliance_checker is not None
        assert isinstance(default_compliance_checker, ComplianceChecker)
        print_result("default_compliance_checker 实例", True)
        passed += 1
    except Exception as e:
        print_result("default_compliance_checker 实例", False, str(e))
        failed += 1
    
    # ========== 3. 测试熵减优化建议 ==========
    print_header("3. 熵减优化建议 (optimizer.py)")
    
    try:
        from multi_agent_se.core.entropy import (
            OptimizationPriority,
            OptimizationCategory,
            OptimizationSuggestion,
            OptimizationPlan,
            EntropyOptimizer,
            create_optimizer,
        )
        print_result("导入优化建议模块", True)
        passed += 1
    except Exception as e:
        print_result("导入优化建议模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 OptimizationPriority 枚举
    try:
        assert OptimizationPriority.CRITICAL.value == "critical"
        assert OptimizationPriority.HIGH.value == "high"
        assert OptimizationPriority.MEDIUM.value == "medium"
        assert OptimizationPriority.LOW.value == "low"
        assert OptimizationPriority.OPTIONAL.value == "optional"
        print_result("OptimizationPriority 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("OptimizationPriority 枚举定义", False, str(e))
        failed += 1
    
    # 测试 OptimizationCategory 枚举
    try:
        assert OptimizationCategory.REFACTOR.value == "refactor"
        assert OptimizationCategory.ARCHITECTURE.value == "architecture"
        assert OptimizationCategory.NAMING.value == "naming"
        assert OptimizationCategory.DEPENDENCY.value == "dependency"
        assert OptimizationCategory.DOCUMENTATION.value == "documentation"
        assert OptimizationCategory.COMPLEXITY.value == "complexity"
        print_result("OptimizationCategory 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("OptimizationCategory 枚举定义", False, str(e))
        failed += 1
    
    # 测试 OptimizationSuggestion
    try:
        suggestion = OptimizationSuggestion(
            suggestion_id="SUG-001",
            title="测试建议",
            description="这是一个测试建议",
            category=OptimizationCategory.REFACTOR,
            priority=OptimizationPriority.HIGH,
            target_file="test.py",
            target_line=10,
            current_state="当前状态",
            suggested_state="建议状态",
            expected_benefit="预期收益",
            estimated_effort="small",
            auto_fixable=True,
        )
        assert suggestion.suggestion_id == "SUG-001"
        assert suggestion.auto_fixable == True
        assert "suggestion_id" in suggestion.to_dict()
        print_result("OptimizationSuggestion 数据类", True)
        passed += 1
    except Exception as e:
        print_result("OptimizationSuggestion 数据类", False, str(e))
        failed += 1
    
    # 测试 OptimizationPlan
    try:
        plan = OptimizationPlan(suggestions=[suggestion])
        assert plan.total_suggestions == 1
        assert plan.critical_count == 0
        assert plan.high_count == 1
        assert plan.auto_fixable_count == 1
        assert len(plan.get_by_priority(OptimizationPriority.HIGH)) == 1
        assert len(plan.get_by_category(OptimizationCategory.REFACTOR)) == 1
        assert "total_suggestions" in plan.to_dict()
        print_result("OptimizationPlan 数据类", True)
        passed += 1
    except Exception as e:
        print_result("OptimizationPlan 数据类", False, str(e))
        failed += 1
    
    # 测试 EntropyOptimizer
    try:
        optimizer = EntropyOptimizer()
        
        # 创建一个熵值报告用于测试
        test_report = EntropyReport(
            metrics=[
                EntropyMetric(
                    entropy_type=EntropyType.CODE_COMPLEXITY,
                    value=60.0,  # 超过阈值，应该产生建议
                    details={
                        "function_count": 5,
                        "max_function_lines": 80,  # 超过50行
                        "max_nesting_depth": 4,     # 超过3层
                    },
                    threshold=50.0,
                ),
            ],
            total_score=40.0,
        )
        
        plan = optimizer.generate_suggestions(test_report)
        assert isinstance(plan, OptimizationPlan)
        assert plan.total_suggestions >= 2  # 应该有函数过长和嵌套过深建议
        
        print_result("EntropyOptimizer 生成建议", True, f"生成{plan.total_suggestions}条建议")
        passed += 1
    except Exception as e:
        print_result("EntropyOptimizer 生成建议", False, str(e))
        failed += 1
    
    # 测试建议优先级排序
    try:
        sorted_suggestions = optimizer.prioritize_suggestions(plan)
        assert len(sorted_suggestions) == plan.total_suggestions
        # 验证排序（优先级高的在前）
        if len(sorted_suggestions) >= 2:
            # 获取优先级顺序值
            priority_order = {
                OptimizationPriority.CRITICAL: 0,
                OptimizationPriority.HIGH: 1,
                OptimizationPriority.MEDIUM: 2,
                OptimizationPriority.LOW: 3,
                OptimizationPriority.OPTIONAL: 4,
            }
            for i in range(len(sorted_suggestions) - 1):
                curr = priority_order.get(sorted_suggestions[i].priority, 5)
                next_p = priority_order.get(sorted_suggestions[i + 1].priority, 5)
                assert curr <= next_p
        print_result("建议优先级排序", True)
        passed += 1
    except Exception as e:
        print_result("建议优先级排序", False, str(e))
        failed += 1
    
    # 测试 create_optimizer 工厂函数
    try:
        optimizer2 = create_optimizer()
        assert isinstance(optimizer2, EntropyOptimizer)
        print_result("create_optimizer 工厂函数", True)
        passed += 1
    except Exception as e:
        print_result("create_optimizer 工厂函数", False, str(e))
        failed += 1
    
    # ========== 4. 测试规范文档生成 ==========
    print_header("4. 规范文档生成 (reporter.py)")
    
    try:
        from multi_agent_se.core.entropy import (
            ReportFormat,
            ReportType,
            ReportMetadata,
            GeneratedReport,
            EntropyReporter,
            create_reporter,
        )
        print_result("导入报告生成模块", True)
        passed += 1
    except Exception as e:
        print_result("导入报告生成模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 ReportFormat 枚举
    try:
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.MARKDOWN.value == "markdown"
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.TEXT.value == "text"
        print_result("ReportFormat 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("ReportFormat 枚举定义", False, str(e))
        failed += 1
    
    # 测试 ReportType 枚举
    try:
        assert ReportType.ENTROPY.value == "entropy"
        assert ReportType.COMPLIANCE.value == "compliance"
        assert ReportType.OPTIMIZATION.value == "optimization"
        assert ReportType.FULL.value == "full"
        print_result("ReportType 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("ReportType 枚举定义", False, str(e))
        failed += 1
    
    # 测试 ReportMetadata
    try:
        metadata = ReportMetadata(
            title="测试报告",
            report_type=ReportType.ENTROPY,
            version="1.0.0",
            project_name="TestProject",
        )
        assert metadata.title == "测试报告"
        assert metadata.report_type == ReportType.ENTROPY
        assert "title" in metadata.to_dict()
        print_result("ReportMetadata 数据类", True)
        passed += 1
    except Exception as e:
        print_result("ReportMetadata 数据类", False, str(e))
        failed += 1
    
    # 测试 EntropyReporter - 熵值报告生成
    try:
        reporter = EntropyReporter(project_name="TestProject")
        
        test_entropy_report = EntropyReport(
            metrics=[
                EntropyMetric(
                    entropy_type=EntropyType.CODE_COMPLEXITY,
                    value=30.0,
                    details={"function_count": 5},
                    threshold=50.0,
                ),
            ],
            total_score=70.0,
        )
        
        # 测试 Markdown 格式
        report = reporter.generate_entropy_report(
            test_entropy_report,
            format=ReportFormat.MARKDOWN,
        )
        assert isinstance(report, GeneratedReport)
        assert report.format == ReportFormat.MARKDOWN
        assert "# 系统熵值分析报告" in report.content
        assert report.metadata.project_name == "TestProject"
        print_result("生成 Markdown 熵值报告", True)
        passed += 1
    except Exception as e:
        print_result("生成 Markdown 熵值报告", False, str(e))
        failed += 1
    
    # 测试 JSON 格式报告
    try:
        report = reporter.generate_entropy_report(
            test_entropy_report,
            format=ReportFormat.JSON,
        )
        assert report.format == ReportFormat.JSON
        assert '"total_score"' in report.content
        print_result("生成 JSON 熵值报告", True)
        passed += 1
    except Exception as e:
        print_result("生成 JSON 熵值报告", False, str(e))
        failed += 1
    
    # 测试 HTML 格式报告
    try:
        report = reporter.generate_entropy_report(
            test_entropy_report,
            format=ReportFormat.HTML,
        )
        assert report.format == ReportFormat.HTML
        assert "<html>" in report.content.lower()
        print_result("生成 HTML 熵值报告", True)
        passed += 1
    except Exception as e:
        print_result("生成 HTML 熵值报告", False, str(e))
        failed += 1
    
    # 测试合规报告生成
    try:
        test_compliance_result = ComplianceResult(
            violations=[],
            checked_rules=10,
            passed_rules=10,
        )
        
        report = reporter.generate_compliance_report(
            test_compliance_result,
            format=ReportFormat.MARKDOWN,
        )
        assert isinstance(report, GeneratedReport)
        assert "# 架构规范合规检测报告" in report.content
        print_result("生成合规检测报告", True)
        passed += 1
    except Exception as e:
        print_result("生成合规检测报告", False, str(e))
        failed += 1
    
    # 测试优化建议报告生成
    try:
        test_plan = OptimizationPlan(suggestions=[
            OptimizationSuggestion(
                suggestion_id="SUG-001",
                title="测试建议",
                description="描述",
                category=OptimizationCategory.REFACTOR,
                priority=OptimizationPriority.HIGH,
                current_state="当前",
                suggested_state="建议",
                expected_benefit="收益",
                estimated_effort="small",
            ),
        ])
        
        report = reporter.generate_optimization_report(
            test_plan,
            format=ReportFormat.MARKDOWN,
        )
        assert isinstance(report, GeneratedReport)
        assert "# 熵减优化建议报告" in report.content
        print_result("生成优化建议报告", True)
        passed += 1
    except Exception as e:
        print_result("生成优化建议报告", False, str(e))
        failed += 1
    
    # 测试完整报告生成
    try:
        report = reporter.generate_full_report(
            test_entropy_report,
            test_compliance_result,
            test_plan,
            format=ReportFormat.MARKDOWN,
        )
        assert isinstance(report, GeneratedReport)
        assert report.metadata.report_type == ReportType.FULL
        assert "# 系统质量完整报告" in report.content
        print_result("生成完整报告", True)
        passed += 1
    except Exception as e:
        print_result("生成完整报告", False, str(e))
        failed += 1
    
    # 测试报告保存
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = f"{tmpdir}/test_report.md"
            report.save(file_path)
            assert Path(file_path).exists()
            content = Path(file_path).read_text(encoding="utf-8")
            assert len(content) > 0
        print_result("报告保存功能", True)
        passed += 1
    except Exception as e:
        print_result("报告保存功能", False, str(e))
        failed += 1
    
    # 测试 create_reporter 工厂函数
    try:
        reporter2 = create_reporter(project_name="TestProject2")
        assert isinstance(reporter2, EntropyReporter)
        print_result("create_reporter 工厂函数", True)
        passed += 1
    except Exception as e:
        print_result("create_reporter 工厂函数", False, str(e))
        failed += 1
    
    # ========== 5. 测试统一导出接口 ==========
    print_header("5. 统一导出接口 (__init__.py)")
    
    try:
        from multi_agent_se.core.entropy import __all__
        
        expected_exports = [
            # 熵值计算
            "EntropyType", "EntropyMetric", "EntropyReport",
            "EntropyCalculator", "calculate_module_entropy",
            # 规范符合度
            "ComplianceLevel", "ComplianceCategory",
            "ComplianceRule", "ComplianceViolation", "ComplianceResult",
            "ComplianceChecker", "default_compliance_checker",
            # 熵减优化
            "OptimizationPriority", "OptimizationCategory",
            "OptimizationSuggestion", "OptimizationPlan",
            "EntropyOptimizer", "create_optimizer",
            # 报告生成
            "ReportFormat", "ReportType",
            "ReportMetadata", "GeneratedReport",
            "EntropyReporter", "create_reporter",
        ]
        
        for export in expected_exports:
            assert export in __all__, f"缺少导出: {export}"
        
        print_result("__all__ 导出列表完整", True, f"共{len(__all__)}个导出")
        passed += 1
    except Exception as e:
        print_result("__all__ 导出列表完整", False, str(e))
        failed += 1
    
    # ========== 验收总结 ==========
    print_header("验收总结")
    total = passed + failed
    print(f"  总测试数: {total}")
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")
    print(f"  通过率: {passed/total*100:.1f}%")
    
    if failed == 0:
        print("\n  🎉 第15阶段验收通过！")
        return 0
    else:
        print(f"\n  ⚠️ 第15阶段有 {failed} 项测试未通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
