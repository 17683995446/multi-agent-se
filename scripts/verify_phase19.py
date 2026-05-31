#!/usr/bin/env python3
"""第19阶段验收脚本 - 任务调度器核心.

验证内容：
1. 任务定义 (task.py)
2. 任务队列 (queue.py)
3. 调度器实现 (scheduler.py)
4. 统一导出接口 (__init__.py)
"""

import sys
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
    print_header("第19阶段验收：任务调度器核心")
    
    passed = 0
    failed = 0
    
    # ========== 1. 测试任务定义 ==========
    print_header("1. 任务定义 (task.py)")
    
    try:
        from multi_agent_se.scheduler import (
            TaskType,
            TaskPriority,
            TaskStatus,
            TaskRequirements,
            TaskResult,
            Task,
            TaskFilter,
        )
        print_result("导入任务模块", True)
        passed += 1
    except Exception as e:
        print_result("导入任务模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 TaskType 枚举
    try:
        assert TaskType.CODE_GENERATION.value == "code_generation"
        assert TaskType.CODE_REVIEW.value == "code_review"
        assert TaskType.REQUIREMENT_ANALYSIS.value == "requirement_analysis"
        assert TaskType.BUG_FIXING.value == "bug_fixing"
        assert TaskType.DOCUMENTATION.value == "documentation"
        assert len(TaskType) >= 15  # 至少15种任务类型
        print_result("TaskType 枚举定义", True, f"共{len(TaskType)}种类型")
        passed += 1
    except Exception as e:
        print_result("TaskType 枚举定义", False, str(e))
        failed += 1
    
    # 测试 TaskPriority 枚举
    try:
        assert TaskPriority.CRITICAL.value == 0
        assert TaskPriority.HIGH.value == 1
        assert TaskPriority.NORMAL.value == 2
        assert TaskPriority.LOW.value == 3
        assert TaskPriority.BACKGROUND.value == 4
        assert len(TaskPriority) == 5
        print_result("TaskPriority 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("TaskPriority 枚举定义", False, str(e))
        failed += 1
    
    # 测试 TaskStatus 枚举
    try:
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.QUEUED.value == "queued"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.CANCELLED.value == "cancelled"
        print_result("TaskStatus 枚举定义", True)
        passed += 1
    except Exception as e:
        print_result("TaskStatus 枚举定义", False, str(e))
        failed += 1
    
    # 测试 TaskRequirements
    try:
        reqs = TaskRequirements(
            required_capabilities={"code_generation"},
            required_roles={"developer"},
            estimated_duration_seconds=120,
            max_retries=5,
        )
        assert "code_generation" in reqs.required_capabilities
        assert "developer" in reqs.required_roles
        assert reqs.max_retries == 5
        print_result("TaskRequirements 数据类", True)
        passed += 1
    except Exception as e:
        print_result("TaskRequirements 数据类", False, str(e))
        failed += 1
    
    # 测试 TaskResult
    try:
        result = TaskResult(
            success=True,
            output="code",
            artifacts={"file": "test.py"},
        )
        assert result.success == True
        assert result.output == "code"
        assert "file" in result.artifacts
        print_result("TaskResult 数据类", True)
        passed += 1
    except Exception as e:
        print_result("TaskResult 数据类", False, str(e))
        failed += 1
    
    # 测试 Task 创建
    try:
        task = Task.create(
            name="TestTask",
            task_type=TaskType.CODE_GENERATION,
            input_data={"prompt": "write hello world"},
            priority=TaskPriority.HIGH,
            required_capabilities={"code_generation"},
        )
        
        assert task.name == "TestTask"
        assert task.task_type == TaskType.CODE_GENERATION
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert task.is_ready == True  # 无依赖
        
        print_result("Task.create 工厂方法", True, f"ID={task.task_id[:8]}")
        passed += 1
    except Exception as e:
        print_result("Task.create 工厂方法", False, str(e))
        failed += 1
    
    # 测试任务状态转换
    try:
        task = Task.create(
            name="StateTest",
            task_type=TaskType.CODE_REVIEW,
            input_data={},
        )
        
        assert task.status == TaskStatus.PENDING
        
        task.mark_queued()
        assert task.status == TaskStatus.QUEUED
        
        task.mark_assigned("agent.dev")
        assert task.status == TaskStatus.ASSIGNED
        assert task.assigned_agent_id == "agent.dev"
        
        task.mark_running()
        assert task.status == TaskStatus.RUNNING
        
        result = TaskResult(success=True, output="done")
        task.mark_completed(result)
        assert task.status == TaskStatus.COMPLETED
        assert task.is_completed == True
        assert task.is_terminal == True
        
        print_result("任务状态转换", True, "PENDING->QUEUED->ASSIGNED->RUNNING->COMPLETED")
        passed += 1
    except Exception as e:
        print_result("任务状态转换", False, str(e))
        failed += 1
    
    # 测试任务失败和重试
    try:
        task = Task.create(
            name="RetryTest",
            task_type=TaskType.CODE_GENERATION,
            input_data={},
        )
        task.requirements.max_retries = 3
        
        task.mark_running()
        task.mark_failed("error")
        
        assert task.status == TaskStatus.FAILED
        assert task.is_failed == True
        assert task.can_retry == True
        assert task.retry_count == 0
        
        # 重试
        task.retry()
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 1
        
        print_result("任务失败和重试", True)
        passed += 1
    except Exception as e:
        print_result("任务失败和重试", False, str(e))
        failed += 1
    
    # 测试任务依赖
    try:
        task1 = Task.create(name="Task1", task_type=TaskType.CODE_GENERATION, input_data={})
        task2 = Task.create(
            name="Task2",
            task_type=TaskType.CODE_REVIEW,
            input_data={},
            dependencies={task1.task_id},
        )
        
        assert task2.has_dependency(task1.task_id) == True
        assert task2.is_ready == False  # 有依赖，未就绪
        
        task2.remove_dependency(task1.task_id)
        assert task2.is_ready == True  # 依赖移除，已就绪
        
        print_result("任务依赖管理", True)
        passed += 1
    except Exception as e:
        print_result("任务依赖管理", False, str(e))
        failed += 1
    
    # 测试 TaskFilter
    try:
        filter = TaskFilter(
            task_types={TaskType.CODE_GENERATION},
            min_priority=TaskPriority.NORMAL,
        )
        
        task1 = Task.create(
            name="T1",
            task_type=TaskType.CODE_GENERATION,
            input_data={},
            priority=TaskPriority.HIGH,
        )
        
        task2 = Task.create(
            name="T2",
            task_type=TaskType.CODE_REVIEW,  # 不匹配
            input_data={},
            priority=TaskPriority.HIGH,
        )
        
        assert filter.match(task1) == True
        assert filter.match(task2) == False
        
        print_result("TaskFilter 过滤器", True)
        passed += 1
    except Exception as e:
        print_result("TaskFilter 过滤器", False, str(e))
        failed += 1
    
    # ========== 2. 测试任务队列 ==========
    print_header("2. 任务队列 (queue.py)")
    
    try:
        from multi_agent_se.scheduler import QueueStats, TaskQueue
        print_result("导入队列模块", True)
        passed += 1
    except Exception as e:
        print_result("导入队列模块", False, str(e))
        failed += 1
        return 1
    
    # 测试 TaskQueue 创建
    try:
        queue = TaskQueue(max_size=100)
        assert queue.size == 0
        assert queue.is_empty == True
        assert queue.is_full == False
        
        print_result("TaskQueue 创建", True)
        passed += 1
    except Exception as e:
        print_result("TaskQueue 创建", False, str(e))
        failed += 1
    
    # 测试入队/出队
    try:
        queue = TaskQueue()
        
        task1 = Task.create(name="T1", task_type=TaskType.CODE_GENERATION, input_data={})
        task2 = Task.create(name="T2", task_type=TaskType.CODE_REVIEW, input_data={})
        
        assert queue.enqueue(task1) == True
        assert queue.enqueue(task2) == True
        assert queue.size == 2
        
        # 出队
        dequeued = queue.dequeue()
        assert dequeued is not None
        assert queue.size == 1
        
        print_result("入队/出队", True)
        passed += 1
    except Exception as e:
        print_result("入队/出队", False, str(e))
        failed += 1
    
    # 测试优先级排序
    try:
        queue = TaskQueue()
        
        task_low = Task.create(
            name="Low",
            task_type=TaskType.CODE_GENERATION,
            input_data={},
            priority=TaskPriority.LOW,
        )
        task_high = Task.create(
            name="High",
            task_type=TaskType.CODE_GENERATION,
            input_data={},
            priority=TaskPriority.HIGH,
        )
        task_critical = Task.create(
            name="Critical",
            task_type=TaskType.CODE_GENERATION,
            input_data={},
            priority=TaskPriority.CRITICAL,
        )
        
        # 按低->高->关键的顺序入队
        queue.enqueue(task_low)
        queue.enqueue(task_high)
        queue.enqueue(task_critical)
        
        # 应该按优先级出队
        first = queue.dequeue()
        second = queue.dequeue()
        third = queue.dequeue()
        
        assert first.priority == TaskPriority.CRITICAL
        assert second.priority == TaskPriority.HIGH
        assert third.priority == TaskPriority.LOW
        
        print_result("优先级排序", True, "CRITICAL->HIGH->LOW")
        passed += 1
    except Exception as e:
        print_result("优先级排序", False, str(e))
        failed += 1
    
    # 测试队列统计
    try:
        queue = TaskQueue()
        
        queue.enqueue(Task.create(name="T1", task_type=TaskType.CODE_GENERATION, input_data={}, priority=TaskPriority.HIGH))
        queue.enqueue(Task.create(name="T2", task_type=TaskType.CODE_REVIEW, input_data={}, priority=TaskPriority.NORMAL))
        queue.enqueue(Task.create(name="T3", task_type=TaskType.CODE_GENERATION, input_data={}, priority=TaskPriority.HIGH))
        
        stats = queue.get_stats()
        assert stats.total_tasks == 3
        assert stats.by_priority.get("HIGH", 0) == 2
        assert stats.by_priority.get("NORMAL", 0) == 1
        
        print_result("队列统计", True)
        passed += 1
    except Exception as e:
        print_result("队列统计", False, str(e))
        failed += 1
    
    # ========== 3. 测试调度器 ==========
    print_header("3. 调度器实现 (scheduler.py)")
    
    try:
        from multi_agent_se.scheduler import (
            SchedulingStrategy,
            CapabilityMatchingStrategy,
            RoundRobinStrategy,
            PriorityBasedStrategy,
            SchedulerStats,
            Scheduler,
        )
        from multi_agent_se.agents.registry import reset_registry, discover_agents
        from multi_agent_se.agents.lifecycle import reset_pool
        print_result("导入调度器模块", True)
        passed += 1
    except Exception as e:
        print_result("导入调度器模块", False, str(e))
        failed += 1
        return 1
    
    # 测试调度策略
    try:
        strategy = CapabilityMatchingStrategy()
        assert isinstance(strategy, SchedulingStrategy)
        
        round_robin = RoundRobinStrategy()
        assert isinstance(round_robin, SchedulingStrategy)
        
        priority_strategy = PriorityBasedStrategy()
        assert isinstance(priority_strategy, SchedulingStrategy)
        
        print_result("调度策略类", True, "3种策略")
        passed += 1
    except Exception as e:
        print_result("调度策略类", False, str(e))
        failed += 1
    
    # 测试 Scheduler 创建
    try:
        reset_registry()
        reset_pool()
        discover_agents(include_builtin=True)
        
        scheduler = Scheduler()
        assert scheduler is not None
        
        print_result("Scheduler 创建", True)
        passed += 1
    except Exception as e:
        print_result("Scheduler 创建", False, str(e))
        failed += 1
    
    # 测试任务提交
    try:
        scheduler = Scheduler()
        
        task = Task.create(
            name="SubmitTest",
            task_type=TaskType.CODE_GENERATION,
            input_data={"prompt": "test"},
        )
        
        result = scheduler.submit(task)
        assert result == True
        
        stats = scheduler.get_stats()
        assert stats.total_scheduled == 1
        
        print_result("任务提交", True)
        passed += 1
    except Exception as e:
        print_result("任务提交", False, str(e))
        failed += 1
    
    # 测试批量提交
    try:
        scheduler = Scheduler()
        
        tasks = [
            Task.create(name=f"Batch{i}", task_type=TaskType.CODE_GENERATION, input_data={})
            for i in range(5)
        ]
        
        count = scheduler.submit_batch(tasks)
        assert count == 5
        
        stats = scheduler.get_stats()
        assert stats.total_scheduled == 5
        
        print_result("批量提交", True, f"提交{count}个任务")
        passed += 1
    except Exception as e:
        print_result("批量提交", False, str(e))
        failed += 1
    
    # 测试任务完成
    try:
        scheduler = Scheduler()
        
        task = Task.create(name="CompleteTest", task_type=TaskType.CODE_GENERATION, input_data={})
        task.mark_running()
        scheduler._running_tasks[task.task_id] = task
        
        result = TaskResult(success=True, output="done")
        scheduler.complete_task(task.task_id, result)
        
        assert task.is_completed == True
        stats = scheduler.get_stats()
        assert stats.total_completed == 1
        
        print_result("任务完成", True)
        passed += 1
    except Exception as e:
        print_result("任务完成", False, str(e))
        failed += 1
    
    # 测试任务失败（设置max_retries=0，避免重试）
    try:
        scheduler = Scheduler()
        
        task = Task.create(name="FailTest", task_type=TaskType.CODE_GENERATION, input_data={})
        task.requirements.max_retries = 0  # 禁止重试
        task.mark_running()
        scheduler._running_tasks[task.task_id] = task
        
        scheduler.fail_task(task.task_id, "error message")
        
        assert task.is_failed == True
        stats = scheduler.get_stats()
        assert stats.total_failed == 1
        
        print_result("任务失败", True)
        passed += 1
    except Exception as e:
        print_result("任务失败", False, str(e))
        failed += 1
    
    # 测试任务取消
    try:
        scheduler = Scheduler()
        
        task = Task.create(name="CancelTest", task_type=TaskType.CODE_GENERATION, input_data={})
        scheduler.submit(task)
        
        result = scheduler.cancel_task(task.task_id, "test cancel")
        assert result == True
        
        stats = scheduler.get_stats()
        assert stats.total_cancelled == 1
        
        print_result("任务取消", True)
        passed += 1
    except Exception as e:
        print_result("任务取消", False, str(e))
        failed += 1
    
    # 测试任务查询
    try:
        scheduler = Scheduler()
        
        task = Task.create(name="QueryTest", task_type=TaskType.CODE_GENERATION, input_data={})
        scheduler.submit(task)
        
        # 查询待处理任务
        pending = scheduler.get_pending_tasks()
        assert len(pending) == 1
        
        # 通过ID查询
        found = scheduler.get_task(task.task_id)
        assert found is not None
        assert found.name == "QueryTest"
        
        print_result("任务查询", True)
        passed += 1
    except Exception as e:
        print_result("任务查询", False, str(e))
        failed += 1
    
    # ========== 4. 测试统一导出接口 ==========
    print_header("4. 统一导出接口 (__init__.py)")
    
    try:
        from multi_agent_se.scheduler import __all__
        
        expected_exports = [
            # 任务定义
            "TaskType", "TaskPriority", "TaskStatus",
            "TaskRequirements", "TaskResult", "Task", "TaskFilter",
            # 任务队列
            "QueueStats", "TaskQueue",
            # 调度器
            "SchedulingStrategy", "CapabilityMatchingStrategy",
            "RoundRobinStrategy", "PriorityBasedStrategy",
            "SchedulerStats", "Scheduler",
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
        print("\n  🎉 第19阶段验收通过！")
        return 0
    else:
        print(f"\n  ⚠️ 第19阶段有 {failed} 项测试未通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
