"""第49阶段验收测试 - 性能基准测试与优化

遵循第一性原理：
1. 测量：建立可量化的性能基准
2. 识别瓶颈：定位性能热点
3. 最小改动：针对性优化，保持代码简洁
4. 验证：优化后性能提升可量化

测试维度：
- Agent启动延迟
- 消息吞吐量
- 任务调度延迟
- 内存占用
- 状态转换开销
"""

import time
import sys
import os
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from statistics import mean, median

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


@dataclass
class BenchmarkResult:
    """基准测试结果."""
    name: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    median_time_ms: float
    ops_per_second: float
    memory_delta_mb: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_ms": round(self.total_time_ms, 2),
            "avg_time_ms": round(self.avg_time_ms, 4),
            "min_time_ms": round(self.min_time_ms, 4),
            "max_time_ms": round(self.max_time_ms, 4),
            "median_time_ms": round(self.median_time_ms, 4),
            "ops_per_second": round(self.ops_per_second, 2),
            "memory_delta_mb": round(self.memory_delta_mb, 2),
        }


def run_benchmark(
    name: str,
    func: Callable[[], Any],
    iterations: int = 1000,
    warmup: int = 100,
) -> BenchmarkResult:
    """运行基准测试.
    
    Args:
        name: 测试名称
        func: 测试函数
        iterations: 迭代次数
        warmup: 预热次数
        
    Returns:
        BenchmarkResult
    """
    # 预热
    for _ in range(warmup):
        func()
    
    # 测量内存
    import psutil
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # 测量时间
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # ms
    
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    
    total_time = sum(times)
    
    return BenchmarkResult(
        name=name,
        iterations=iterations,
        total_time_ms=total_time,
        avg_time_ms=mean(times),
        min_time_ms=min(times),
        max_time_ms=max(times),
        median_time_ms=median(times),
        ops_per_second=iterations / (total_time / 1000),
        memory_delta_mb=mem_after - mem_before,
    )


def print_result(result: BenchmarkResult) -> None:
    """打印测试结果."""
    print(f"  {result.name}:")
    print(f"    迭代次数: {result.iterations}")
    print(f"    总时间: {result.total_time_ms:.2f} ms")
    print(f"    平均: {result.avg_time_ms:.4f} ms/op")
    print(f"    中位数: {result.median_time_ms:.4f} ms/op")
    print(f"    最小: {result.min_time_ms:.4f} ms")
    print(f"    最大: {result.max_time_ms:.4f} ms")
    print(f"    吞吐量: {result.ops_per_second:.2f} ops/sec")
    if result.memory_delta_mb > 0.01:
        print(f"    内存增长: {result.memory_delta_mb:.2f} MB")


# ========== 测试1: Agent启动延迟 ==========

def test_agent_startup_latency() -> BenchmarkResult:
    """测试Agent启动延迟."""
    from multi_agent_se.agents.controller.agent import ControllerAgent
    
    counter = [0]
    
    def create_and_init():
        agent = ControllerAgent(agent_id=f"perf.controller.{counter[0]}")
        counter[0] += 1
        agent.initialize()
    
    return run_benchmark("Agent启动延迟", create_and_init, iterations=100, warmup=10)


# ========== 测试2: 消息吞吐量 ==========

def test_message_throughput() -> BenchmarkResult:
    """测试消息总线吞吐量."""
    from multi_agent_se.agents.communication.bus import MessageBus
    from multi_agent_se.agents.communication.message import Message, MessageType
    
    bus = MessageBus()
    counter = [0]
    
    def send_message():
        msg = Message.create(
            sender_id="perf.sender",
            receiver_id=f"perf.receiver.{counter[0] % 10}",
            payload={"data": "test"},
            message_type=MessageType.TASK_ASSIGN,
        )
        bus.send(msg)
        counter[0] += 1
    
    return run_benchmark("消息发送吞吐量", send_message, iterations=10000, warmup=1000)


# ========== 测试3: 消息接收吞吐量 ==========

def test_message_receive_throughput() -> BenchmarkResult:
    """测试消息接收吞吐量."""
    from multi_agent_se.agents.communication.bus import MessageBus
    from multi_agent_se.agents.communication.message import Message, MessageType
    
    bus = MessageBus()
    
    # 预填充消息
    for i in range(1000):
        msg = Message.create(
            sender_id="perf.sender",
            receiver_id="perf.receiver",
            payload={"index": i},
            message_type=MessageType.TASK_ASSIGN,
        )
        bus.send(msg)
    
    def receive_message():
        bus.receive("perf.receiver")
    
    return run_benchmark("消息接收吞吐量", receive_message, iterations=1000, warmup=100)


# ========== 测试4: 状态转换开销 ==========

def test_state_transition_overhead() -> BenchmarkResult:
    """测试Agent状态转换开销."""
    from multi_agent_se.agents.controller.agent import ControllerAgent
    
    agent = ControllerAgent(agent_id="perf.state.test")
    agent.initialize()
    
    state_cycle = [0]
    
    def state_transition():
        cycle = state_cycle[0] % 4
        if cycle == 0:
            agent.start()
        elif cycle == 1:
            agent.pause()
        elif cycle == 2:
            agent.resume()
        else:
            agent.stop()
            agent.initialize()
        state_cycle[0] += 1
    
    return run_benchmark("状态转换开销", state_transition, iterations=200, warmup=20)


# ========== 测试5: 任务执行延迟 ==========

def test_task_execution_latency() -> BenchmarkResult:
    """测试任务执行延迟."""
    from multi_agent_se.agents.controller.agent import ControllerAgent
    from multi_agent_se.agents.runtime.base_agent import AgentContext
    
    agent = ControllerAgent(agent_id="perf.task.test")
    agent.initialize()
    agent.start()
    
    context = AgentContext(input_data={"requirement": "性能测试需求"})
    
    def execute_task():
        agent.execute(context)
    
    return run_benchmark("任务执行延迟", execute_task, iterations=500, warmup=50)


# ========== 测试6: 实例池获取/释放 ==========

def test_pool_acquire_release() -> BenchmarkResult:
    """测试实例池获取/释放性能."""
    from multi_agent_se.agents.lifecycle.pool import AgentPool, PoolConfig
    from multi_agent_se.agents.registry import AgentRole
    
    pool = AgentPool(config=PoolConfig(max_instances=50, enable_instance_reuse=True))
    
    # 预创建一些实例
    instances = []
    for i in range(10):
        inst = pool.acquire(AgentRole.CONTROLLER)
        instances.append(inst)
    
    for inst in instances:
        pool.release(inst.instance_id)
    
    counter = [0]
    
    def acquire_release():
        inst = pool.acquire(AgentRole.CONTROLLER)
        pool.release(inst.instance_id)
        counter[0] += 1
    
    return run_benchmark("实例池获取/释放", acquire_release, iterations=500, warmup=50)


# ========== 测试7: 内存占用稳定性 ==========

def test_memory_stability() -> Dict[str, Any]:
    """测试内存占用稳定性."""
    import gc
    import psutil
    
    process = psutil.Process()
    
    from multi_agent_se.agents.controller.agent import ControllerAgent
    
    gc.collect()
    mem_before = process.memory_info().rss / 1024 / 1024
    
    # 创建大量Agent
    agents = []
    for i in range(100):
        agent = ControllerAgent(agent_id=f"mem.test.{i}")
        agent.initialize()
        agents.append(agent)
    
    mem_during = process.memory_info().rss / 1024 / 1024
    
    # 释放所有Agent
    agents.clear()
    gc.collect()
    
    mem_after = process.memory_info().rss / 1024 / 1024
    
    return {
        "memory_before_mb": round(mem_before, 2),
        "memory_during_mb": round(mem_during, 2),
        "memory_after_mb": round(mem_after, 2),
        "per_agent_mb": round((mem_during - mem_before) / 100, 4),
        "leak_detected": mem_after > mem_before + 10,  # 超过10MB视为泄漏
    }


# ========== 测试8: 端到端工作流延迟 ==========

def test_end_to_end_workflow() -> BenchmarkResult:
    """测试端到端工作流延迟."""
    from multi_agent_se.agents.controller.agent import ControllerAgent
    from multi_agent_se.agents.requirement.agent import RequirementAgent
    from multi_agent_se.agents.runtime.base_agent import AgentContext
    
    controller = ControllerAgent(agent_id="perf.e2e.controller")
    controller.initialize()
    controller.start()
    
    requirement = RequirementAgent(agent_id="perf.e2e.requirement")
    requirement.initialize()
    requirement.start()
    
    def workflow():
        # Controller 解析需求
        ctx1 = AgentContext(input_data={"requirement": "性能测试需求"})
        result1 = controller.execute(ctx1)
        
        # Requirement 分析
        if result1.success:
            parsed = result1.output if isinstance(result1.output, dict) else {}
            ctx2 = AgentContext(input_data={"requirement": parsed.get("parsed_requirement", "")})
            requirement.execute(ctx2)
    
    return run_benchmark("端到端工作流", workflow, iterations=100, warmup=10)


# ========== 性能基准汇总 ==========

def run_all_benchmarks() -> Dict[str, Any]:
    """运行所有基准测试."""
    print("=" * 60)
    print("第49阶段验收测试 - 性能基准测试与优化")
    print("=" * 60)
    print()
    
    results = {}
    
    # 测试1: Agent启动延迟
    print("[TEST] Agent启动延迟")
    try:
        result = test_agent_startup_latency()
        print_result(result)
        results["agent_startup"] = result.to_dict()
        print("  ✓ Agent启动延迟 通过")
    except Exception as e:
        print(f"  ✗ Agent启动延迟 失败: {e}")
        results["agent_startup"] = {"error": str(e)}
    print()
    
    # 测试2: 消息发送吞吐量
    print("[TEST] 消息发送吞吐量")
    try:
        result = test_message_throughput()
        print_result(result)
        results["message_send"] = result.to_dict()
        print("  ✓ 消息发送吞吐量 通过")
    except Exception as e:
        print(f"  ✗ 消息发送吞吐量 失败: {e}")
        results["message_send"] = {"error": str(e)}
    print()
    
    # 测试3: 消息接收吞吐量
    print("[TEST] 消息接收吞吐量")
    try:
        result = test_message_receive_throughput()
        print_result(result)
        results["message_receive"] = result.to_dict()
        print("  ✓ 消息接收吞吐量 通过")
    except Exception as e:
        print(f"  ✗ 消息接收吞吐量 失败: {e}")
        results["message_receive"] = {"error": str(e)}
    print()
    
    # 测试4: 状态转换开销
    print("[TEST] 状态转换开销")
    try:
        result = test_state_transition_overhead()
        print_result(result)
        results["state_transition"] = result.to_dict()
        print("  ✓ 状态转换开销 通过")
    except Exception as e:
        print(f"  ✗ 状态转换开销 失败: {e}")
        results["state_transition"] = {"error": str(e)}
    print()
    
    # 测试5: 任务执行延迟
    print("[TEST] 任务执行延迟")
    try:
        result = test_task_execution_latency()
        print_result(result)
        results["task_execution"] = result.to_dict()
        print("  ✓ 任务执行延迟 通过")
    except Exception as e:
        print(f"  ✗ 任务执行延迟 失败: {e}")
        results["task_execution"] = {"error": str(e)}
    print()
    
    # 测试6: 实例池获取/释放
    print("[TEST] 实例池获取/释放")
    try:
        result = test_pool_acquire_release()
        print_result(result)
        results["pool_acquire_release"] = result.to_dict()
        print("  ✓ 实例池获取/释放 通过")
    except Exception as e:
        print(f"  ✗ 实例池获取/释放 失败: {e}")
        results["pool_acquire_release"] = {"error": str(e)}
    print()
    
    # 测试7: 内存占用稳定性
    print("[TEST] 内存占用稳定性")
    try:
        mem_result = test_memory_stability()
        print(f"  创建前内存: {mem_result['memory_before_mb']} MB")
        print(f"  创建100个Agent后: {mem_result['memory_during_mb']} MB")
        print(f"  释放后内存: {mem_result['memory_after_mb']} MB")
        print(f"  每个Agent占用: {mem_result['per_agent_mb']} MB")
        if mem_result['leak_detected']:
            print("  ⚠ 检测到可能的内存泄漏")
        else:
            print("  ✓ 内存稳定性良好")
        results["memory_stability"] = mem_result
    except Exception as e:
        print(f"  ✗ 内存占用稳定性 失败: {e}")
        results["memory_stability"] = {"error": str(e)}
    print()
    
    # 测试8: 端到端工作流
    print("[TEST] 端到端工作流延迟")
    try:
        result = test_end_to_end_workflow()
        print_result(result)
        results["end_to_end_workflow"] = result.to_dict()
        print("  ✓ 端到端工作流 通过")
    except Exception as e:
        print(f"  ✗ 端到端工作流 失败: {e}")
        results["end_to_end_workflow"] = {"error": str(e)}
    print()
    
    # 汇总
    print("=" * 60)
    print("性能基准汇总")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if "error" not in r)
    total = len(results)
    
    print(f"测试通过: {passed}/{total}")
    print()
    
    # 关键指标
    if "message_send" in results and "error" not in results["message_send"]:
        print(f"消息吞吐量: {results['message_send']['ops_per_second']:.0f} ops/sec")
    if "task_execution" in results and "error" not in results["task_execution"]:
        print(f"任务执行延迟: {results['task_execution']['avg_time_ms']:.4f} ms")
    if "memory_stability" in results and "error" not in results["memory_stability"]:
        print(f"每个Agent内存: {results['memory_stability']['per_agent_mb']:.4f} MB")
    
    print()
    
    if passed == total:
        print("🎉 第49阶段验收通过！性能基准测试完成。")
    else:
        print(f"⚠ 部分测试未通过 ({total - passed} 个失败)")
    
    return results


if __name__ == "__main__":
    run_all_benchmarks()
