"""综合集成测试 - 复杂场景验证.

测试目标：
1. 验证系统在复杂、大规模、高并发场景下的稳定性
2. 发现隐藏bug和边界问题
3. 验证各模块协同工作是否正常

测试场景：
- 场景1: 多Agent并发协作
- 场景2: 大规模代码原子化分析
- 场景3: 复杂Pipeline编排
- 场景4: 异常和边界条件
- 场景5: 长时间运行稳定性
"""

import sys
import os
import time
import threading
import concurrent.futures
from typing import List, Dict, Any
from pathlib import Path

# 确保项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from multi_agent_se.core.logging.tracer import trace_call, TraceContext, trace_block
from multi_agent_se.core.logging import configure_logging, LogLevel

# 配置详细日志
configure_logging(
    log_level="DEBUG",
    log_format="structured",
)


class ComprehensiveTestRunner:
    """综合测试运行器."""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.errors: List[Exception] = []
        
    @trace_call(operation="run_all_tests", level=LogLevel.INFO)
    def run_all_tests(self) -> bool:
        """运行所有测试场景."""
        print("=" * 80)
        print("  综合集成测试 - 复杂场景验证")
        print("=" * 80)
        
        tests = [
            ("场景1: 多Agent并发协作", self.test_multi_agent_concurrency),
            ("场景2: 大规模代码原子化分析", self.test_large_scale_atomicity),
            ("场景3: 复杂Pipeline编排", self.test_complex_pipeline),
            ("场景4: 异常和边界条件", self.test_edge_cases),
            ("场景5: 长时间运行稳定性", self.test_long_running_stability),
        ]
        
        all_passed = True
        for name, test_func in tests:
            print(f"\n{'='*80}")
            print(f"  {name}")
            print(f"{'='*80}")
            try:
                with TraceContext(name, level=LogLevel.INFO):
                    result = test_func()
                    self.test_results.append({
                        "name": name,
                        "passed": result,
                        "error": None,
                    })
                    if not result:
                        all_passed = False
                        print(f"  ✗ {name} 失败")
                    else:
                        print(f"  ✓ {name} 通过")
            except Exception as e:
                all_passed = False
                self.errors.append(e)
                self.test_results.append({
                    "name": name,
                    "passed": False,
                    "error": str(e),
                })
                print(f"  ✗ {name} 异常: {e}")
        
        return all_passed
    
    # ========== 场景1: 多Agent并发协作 ==========
    
    @trace_call(operation="test_multi_agent_concurrency")
    def test_multi_agent_concurrency(self) -> bool:
        """测试多Agent并发协作场景."""
        print("  测试多Agent并发协作...")
        
        # 模拟10个并发任务
        num_tasks = 10
        results = []
        
        def worker_task(task_id: int) -> Dict[str, Any]:
            with TraceContext(f"worker_task_{task_id}"):
                # 模拟Agent处理
                time.sleep(0.01)  # 10ms处理时间
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "timestamp": time.time(),
                }
        
        # 使用线程池并发执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_tasks)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"    任务异常: {e}")
                    return False
        
        # 验证所有任务完成
        if len(results) != num_tasks:
            print(f"    任务数量不匹配: 期望{num_tasks}, 实际{len(results)}")
            return False
        
        print(f"    ✓ {num_tasks}个并发任务全部完成")
        return True
    
    # ========== 场景2: 大规模代码原子化分析 ==========
    
    @trace_call(operation="test_large_scale_atomicity")
    def test_large_scale_atomicity(self) -> bool:
        """测试大规模代码原子化分析."""
        print("  测试大规模代码原子化分析...")
        
        # 生成大规模测试代码
        large_code = self._generate_large_code(100)  # 100个函数
        
        try:
            from multi_agent_se.atomicity.variable.extractor import VariableExtractor
            from multi_agent_se.atomicity.method.extractor import MethodExtractor
            
            # 变量提取
            with TraceContext("variable_extraction"):
                var_extractor = VariableExtractor(large_code, file_path="large_test.py")
                variables = var_extractor.extract()
                print(f"    提取变量数: {len(variables)}")
            
            # 方法提取
            with TraceContext("method_extraction"):
                method_extractor = MethodExtractor(large_code, file_path="large_test.py")
                methods = method_extractor.extract()
                print(f"    提取方法数: {len(methods)}")
            
            # 验证结果
            if len(methods) < 100:
                print(f"    方法数量不足: 期望>=100, 实际{len(methods)}")
                return False
            
            print(f"    ✓ 大规模代码分析完成")
            return True
            
        except Exception as e:
            print(f"    分析异常: {e}")
            return False
    
    def _generate_large_code(self, num_functions: int) -> str:
        """生成大规模测试代码."""
        code_lines = [
            '"""大规模测试模块."""',
            "from typing import List, Dict, Optional",
            "",
            "GLOBAL_CONSTANT = 100",
            "",
        ]
        
        for i in range(num_functions):
            code_lines.extend([
                f"",
                f"def process_data_{i}(data: List[int], multiplier: float = 1.0) -> Dict[str, Any]:",
                f'    """处理数据函数 {i}."""',
                f"    result = {{}}",
                f"    total = 0",
                f"    for item in data:",
                f"        if item > 0:",
                f"            total += item * multiplier",
                f"    result['total'] = total",
                f"    result['count'] = len(data)",
                f"    return result",
            ])
        
        return "\n".join(code_lines)
    
    # ========== 场景3: 复杂Pipeline编排 ==========
    
    @trace_call(operation="test_complex_pipeline")
    def test_complex_pipeline(self) -> bool:
        """测试复杂Pipeline编排."""
        print("  测试复杂Pipeline编排...")
        
        try:
            from multi_agent_se.pipeline.models import (
                PipelineDefinition, PipelineNode, RetryPolicy, NodeStatus
            )
            from multi_agent_se.pipeline.orchestrator import PipelineOrchestrator
            
            # 创建复杂DAG Pipeline
            with TraceContext("create_pipeline"):
                # 使用正确的PipelineNode模型（name作为id，dependencies表示依赖）
                nodes = [
                    PipelineNode(
                        name="start",
                        description="开始节点",
                        handler=lambda: print("Start"),
                    ),
                    PipelineNode(
                        name="parse",
                        description="解析",
                        handler=lambda: print("Parse"),
                        dependencies=["start"],
                        retry_count=3,
                        retry_policy=RetryPolicy.FIXED,
                    ),
                    PipelineNode(
                        name="validate",
                        description="验证",
                        handler=lambda: print("Validate"),
                        dependencies=["start"],
                        retry_count=3,
                        retry_policy=RetryPolicy.FIXED,
                    ),
                    PipelineNode(
                        name="transform",
                        description="转换",
                        handler=lambda: print("Transform"),
                        dependencies=["parse", "validate"],
                    ),
                    PipelineNode(
                        name="save",
                        description="保存",
                        handler=lambda: print("Save"),
                        dependencies=["transform"],
                    ),
                    PipelineNode(
                        name="notify",
                        description="通知",
                        handler=lambda: print("Notify"),
                        dependencies=["save"],
                    ),
                ]
                
                pipeline = PipelineDefinition(
                    name="复杂数据处理Pipeline",
                    description="包含并行处理和依赖的复杂Pipeline",
                    nodes=nodes,
                )
                
                # 验证Pipeline
                errors = pipeline.validate()
                if errors:
                    print(f"    Pipeline验证失败: {errors}")
                    return False
            
            print(f"    ✓ Pipeline创建和验证成功")
            print(f"    节点数: {len(nodes)}")
            print(f"    拓扑顺序: {pipeline.topological_order}")
            
            return True
            
        except Exception as e:
            print(f"    Pipeline测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ========== 场景4: 异常和边界条件 ==========
    
    @trace_call(operation="test_edge_cases")
    def test_edge_cases(self) -> bool:
        """测试异常和边界条件."""
        print("  测试异常和边界条件...")
        
        all_passed = True
        
        # 测试1: 空代码
        print("    测试1: 空代码处理...")
        try:
            from multi_agent_se.atomicity.variable.extractor import VariableExtractor
            extractor = VariableExtractor("", file_path="empty.py")
            variables = extractor.extract()
            print(f"      ✓ 空代码处理正常，变量数: {len(variables)}")
        except Exception as e:
            print(f"      ✗ 空代码处理异常: {e}")
            all_passed = False
        
        # 测试2: 语法错误代码
        print("    测试2: 语法错误处理...")
        try:
            bad_code = "def broken(:\n    pass"
            from multi_agent_se.atomicity.variable.extractor import VariableExtractor
            extractor = VariableExtractor(bad_code, file_path="bad.py")
            variables = extractor.extract()
            print(f"      ✗ 应该抛出异常但没有")
            all_passed = False
        except SyntaxError:
            print(f"      ✓ 语法错误正确捕获")
        except Exception as e:
            print(f"      ✗ 异常类型不正确: {e}")
            all_passed = False
        
        # 测试3: 超大输入
        print("    测试3: 超大输入处理...")
        try:
            huge_code = "x = 1\n" * 10000  # 10000行代码
            from multi_agent_se.atomicity.variable.extractor import VariableExtractor
            extractor = VariableExtractor(huge_code, file_path="huge.py")
            variables = extractor.extract()
            print(f"      ✓ 超大输入处理正常，变量数: {len(variables)}")
        except Exception as e:
            print(f"      ✗ 超大输入处理异常: {e}")
            all_passed = False
        
        # 测试4: 特殊字符
        print("    测试4: 特殊字符处理...")
        try:
            special_code = '''
# 中文注释
变量 = "中文"
emoji = "🎉"
unicode_var = "café"
'''
            from multi_agent_se.atomicity.variable.extractor import VariableExtractor
            extractor = VariableExtractor(special_code, file_path="special.py")
            variables = extractor.extract()
            print(f"      ✓ 特殊字符处理正常，变量数: {len(variables)}")
        except Exception as e:
            print(f"      ✗ 特殊字符处理异常: {e}")
            all_passed = False
        
        return all_passed
    
    # ========== 场景5: 长时间运行稳定性 ==========
    
    @trace_call(operation="test_long_running_stability")
    def test_long_running_stability(self) -> bool:
        """测试长时间运行稳定性."""
        print("  测试长时间运行稳定性...")
        
        iterations = 100
        errors = 0
        
        from multi_agent_se.atomicity.variable.extractor import VariableExtractor
        
        test_code = '''
def process(x: int) -> int:
    result = x * 2
    return result
'''
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                with TraceContext(f"stability_iteration_{i}", level=LogLevel.DEBUG):
                    extractor = VariableExtractor(test_code, file_path="stability.py")
                    variables = extractor.extract()
                    if len(variables) != 2:  # x, result
                        errors += 1
                        print(f"    迭代{i}: 变量数量不匹配")
            except Exception as e:
                errors += 1
                print(f"    迭代{i}: 异常 - {e}")
        
        duration = time.time() - start_time
        
        print(f"    迭代次数: {iterations}")
        print(f"    错误次数: {errors}")
        print(f"    总耗时: {duration:.2f}s")
        print(f"    平均每次: {duration/iterations*1000:.2f}ms")
        
        if errors > 0:
            print(f"    ✗ 稳定性测试失败")
            return False
        
        print(f"    ✓ 稳定性测试通过")
        return True
    
    def print_summary(self) -> None:
        """打印测试摘要."""
        print(f"\n{'='*80}")
        print("  测试摘要")
        print(f"{'='*80}")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        
        print(f"  总测试数: {total}")
        print(f"  通过: {passed}")
        print(f"  失败: {failed}")
        
        if self.errors:
            print(f"\n  异常列表:")
            for i, e in enumerate(self.errors, 1):
                print(f"    {i}. {e}")
        
        print(f"{'='*80}")


def main():
    """主函数."""
    runner = ComprehensiveTestRunner()
    success = runner.run_all_tests()
    runner.print_summary()
    
    if success:
        print("\n  ✓ 所有测试通过！")
        return 0
    else:
        print("\n  ✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
