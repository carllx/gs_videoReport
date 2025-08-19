# 批量处理功能 - 测试策略设计

## 概述

本文档定义批量处理功能的全面测试策略，包括单元测试、集成测试、性能测试、端到端测试和压力测试的详细规划。

## 测试框架和工具

### 测试技术栈
```python
# 测试依赖 (pyproject.toml)
[tool.poetry.group.test.dependencies]
pytest = "^7.4.0"                # 主要测试框架
pytest-asyncio = "^0.21.0"       # 异步测试支持
pytest-mock = "^3.11.0"          # Mock支持
pytest-cov = "^4.1.0"            # 覆盖率分析
pytest-benchmark = "^4.0.0"      # 性能基准测试
pytest-xdist = "^3.3.0"          # 并行测试
pytest-timeout = "^2.1.0"        # 测试超时控制

# 性能和监控
memory-profiler = "^0.61.0"      # 内存分析
psutil = "^5.9.0"                # 系统监控
aioresponses = "^0.7.0"          # HTTP Mock
fakeredis = "^2.18.0"            # Redis Mock

# 测试数据生成
factory-boy = "^3.3.0"           # 测试数据工厂
faker = "^19.3.0"                # 假数据生成
hypothesis = "^6.82.0"           # 属性测试
```

### 测试目录结构
```
tests/
├── unit/                        # 单元测试
│   ├── batch/
│   │   ├── test_data_models.py
│   │   ├── test_task_queue.py
│   │   ├── test_worker_pool.py
│   │   ├── test_processor.py
│   │   ├── test_progress_monitor.py
│   │   └── test_checkpoint_manager.py
│   └── test_batch_cli.py
├── integration/                 # 集成测试
│   ├── test_batch_workflow.py
│   ├── test_api_integration.py
│   ├── test_database_operations.py
│   └── test_file_operations.py
├── performance/                 # 性能测试
│   ├── test_throughput.py
│   ├── test_memory_usage.py
│   ├── test_concurrent_processing.py
│   └── test_scaling.py
├── e2e/                        # 端到端测试
│   ├── test_complete_workflow.py
│   ├── test_error_recovery.py
│   └── test_user_scenarios.py
├── stress/                     # 压力测试
│   ├── test_large_batches.py
│   ├── test_long_running.py
│   └── test_resource_limits.py
├── fixtures/                   # 测试数据
│   ├── videos/
│   ├── configs/
│   └── expected_outputs/
└── conftest.py                 # pytest配置
```

## 单元测试策略

### 1. 数据模型测试

#### test_data_models.py
```python
"""
数据模型单元测试
"""
import pytest
from datetime import datetime
from src.gs_video_report.batch.data_models import (
    VideoInput, VideoTask, TaskStatus, BatchStatus
)

class TestVideoInput:
    """VideoInput类测试"""
    
    def test_creation_with_required_fields(self):
        """测试必需字段创建"""
        input_data = VideoInput(
            source_type=InputType.FILE,
            source_path="./test.mp4",
            template="chinese_transcript",
            output_path="./output.md"
        )
        
        assert input_data.source_type == InputType.FILE
        assert input_data.source_path == "./test.mp4"
        assert input_data.priority == 50  # 默认值
    
    def test_serialization_roundtrip(self):
        """测试序列化往返"""
        original = VideoInput(
            source_type=InputType.YOUTUBE,
            source_path="https://youtube.com/watch?v=test",
            template="summary_report",
            output_path="./summary.md",
            file_size=1024000,
            metadata={"duration": 300}
        )
        
        # 序列化
        data_dict = original.to_dict()
        
        # 反序列化
        restored = VideoInput.from_dict(data_dict)
        
        assert restored.source_type == original.source_type
        assert restored.source_path == original.source_path
        assert restored.file_size == original.file_size
        assert restored.metadata == original.metadata
    
    @pytest.mark.parametrize("invalid_priority", [-1, 101, "invalid"])
    def test_invalid_priority_handling(self, invalid_priority):
        """测试无效优先级处理"""
        with pytest.raises(ValueError):
            VideoInput(
                source_type=InputType.FILE,
                source_path="./test.mp4",
                template="chinese_transcript",
                output_path="./output.md",
                priority=invalid_priority
            )

class TestVideoTask:
    """VideoTask类测试"""
    
    @pytest.fixture
    def sample_task(self):
        """样本任务数据"""
        input_data = VideoInput(
            source_type=InputType.FILE,
            source_path="./test.mp4",
            template="chinese_transcript",
            output_path="./output.md"
        )
        
        return VideoTask(
            task_id="task_001",
            batch_id="batch_001",
            input=input_data
        )
    
    def test_task_status_transitions(self, sample_task):
        """测试任务状态转换"""
        # 初始状态
        assert sample_task.status == TaskStatus.PENDING
        assert sample_task.started_at is None
        
        # 开始处理
        sample_task.status = TaskStatus.RUNNING
        sample_task.started_at = datetime.now()
        
        assert sample_task.status == TaskStatus.RUNNING
        assert sample_task.started_at is not None
        
        # 完成处理
        sample_task.status = TaskStatus.COMPLETED
        sample_task.completed_at = datetime.now()
        
        assert sample_task.status == TaskStatus.COMPLETED
        assert sample_task.completed_at is not None
    
    def test_retry_count_increment(self, sample_task):
        """测试重试计数"""
        assert sample_task.retry_count == 0
        
        sample_task.retry_count += 1
        assert sample_task.retry_count == 1
```

### 2. 任务队列测试

#### test_task_queue.py
```python
"""
任务队列单元测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.gs_video_report.batch.task_queue import TaskQueue
from src.gs_video_report.batch.data_models import VideoTask, TaskStatus

class TestTaskQueue:
    """TaskQueue类测试"""
    
    @pytest.fixture
    async def task_queue(self, tmp_path):
        """创建测试用任务队列"""
        db_path = tmp_path / "test_tasks.db"
        queue = TaskQueue(str(db_path))
        yield queue
        # 清理
        await queue.close()
    
    @pytest.fixture
    def sample_tasks(self):
        """创建样本任务列表"""
        tasks = []
        for i in range(5):
            task = VideoTask(
                task_id=f"task_{i:03d}",
                batch_id="batch_001",
                input=VideoInput(
                    source_type=InputType.FILE,
                    source_path=f"./video_{i}.mp4",
                    template="chinese_transcript",
                    output_path=f"./output_{i}.md"
                )
            )
            tasks.append(task)
        return tasks
    
    async def test_add_tasks(self, task_queue, sample_tasks):
        """测试批量添加任务"""
        await task_queue.add_tasks(sample_tasks)
        
        # 验证任务计数
        status = await task_queue.get_status()
        assert status.total_tasks == 5
        assert status.pending_tasks == 5
        assert status.running_tasks == 0
    
    async def test_get_next_task_fifo_order(self, task_queue, sample_tasks):
        """测试FIFO顺序获取任务"""
        await task_queue.add_tasks(sample_tasks)
        
        # 获取第一个任务
        task = await task_queue.get_next_task()
        assert task is not None
        assert task.task_id == "task_000"
        assert task.status == TaskStatus.RUNNING
    
    async def test_priority_ordering(self, task_queue):
        """测试优先级排序"""
        # 创建不同优先级的任务
        high_priority_task = VideoTask(
            task_id="high_priority",
            batch_id="batch_001",
            input=VideoInput(
                source_type=InputType.FILE,
                source_path="./high.mp4",
                template="chinese_transcript",
                output_path="./high.md",
                priority=10  # 高优先级
            )
        )
        
        low_priority_task = VideoTask(
            task_id="low_priority",
            batch_id="batch_001",
            input=VideoInput(
                source_type=InputType.FILE,
                source_path="./low.mp4",
                template="chinese_transcript",
                output_path="./low.md",
                priority=90  # 低优先级
            )
        )
        
        # 先添加低优先级，再添加高优先级
        await task_queue.add_tasks([low_priority_task, high_priority_task])
        
        # 应该先获取高优先级任务
        task = await task_queue.get_next_task()
        assert task.task_id == "high_priority"
    
    async def test_concurrent_access(self, task_queue, sample_tasks):
        """测试并发访问安全性"""
        await task_queue.add_tasks(sample_tasks)
        
        # 创建多个并发获取任务的协程
        async def get_task():
            return await task_queue.get_next_task()
        
        # 并发获取任务
        tasks = await asyncio.gather(*[get_task() for _ in range(3)])
        
        # 验证获取的任务不重复
        task_ids = [task.task_id for task in tasks if task is not None]
        assert len(task_ids) == len(set(task_ids))  # 无重复
    
    async def test_task_persistence(self, task_queue, sample_tasks):
        """测试任务持久化"""
        await task_queue.add_tasks(sample_tasks)
        
        # 重新创建队列实例（模拟重启）
        new_queue = TaskQueue(task_queue.db_path)
        
        # 验证任务已恢复
        status = await new_queue.get_status()
        assert status.total_tasks == 5
        
        await new_queue.close()
```

### 3. 工作线程池测试

#### test_worker_pool.py
```python
"""
工作线程池单元测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.gs_video_report.batch.worker_pool import WorkerPool
from src.gs_video_report.batch.api_limiter import APILimiter

class TestWorkerPool:
    """WorkerPool类测试"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock配置对象"""
        config = MagicMock()
        config.api_key = "test_api_key"
        config.model = "gemini-2.5-flash"
        return config
    
    @pytest.fixture
    def mock_api_limiter(self):
        """Mock API限流器"""
        limiter = AsyncMock(spec=APILimiter)
        limiter.acquire.return_value = None
        limiter.release.return_value = None
        return limiter
    
    @pytest.fixture
    async def worker_pool(self, mock_config, mock_api_limiter):
        """创建测试用工作线程池"""
        pool = WorkerPool(
            max_workers=2,
            config=mock_config,
            api_limiter=mock_api_limiter
        )
        yield pool
        await pool.stop_workers()
    
    async def test_worker_pool_initialization(self, worker_pool):
        """测试工作线程池初始化"""
        assert worker_pool.max_workers == 2
        assert len(worker_pool.workers) == 0  # 未启动
        assert not worker_pool.is_running
    
    async def test_start_stop_workers(self, worker_pool):
        """测试启动和停止工作线程"""
        # 启动工作线程
        await worker_pool.start_workers()
        
        assert worker_pool.is_running
        assert len(worker_pool.workers) == 2
        
        # 停止工作线程
        await worker_pool.stop_workers()
        
        assert not worker_pool.is_running
        assert len(worker_pool.workers) == 0
    
    @patch('src.gs_video_report.batch.worker_pool.GeminiService')
    @patch('src.gs_video_report.batch.worker_pool.LessonFormatter')
    @patch('src.gs_video_report.batch.worker_pool.FileWriter')
    async def test_task_execution_success(self, mock_file_writer, 
                                        mock_formatter, mock_gemini,
                                        worker_pool, sample_task):
        """测试任务执行成功流程"""
        # Mock服务返回值
        mock_gemini.return_value.analyze_video.return_value = AsyncMock()
        mock_formatter.return_value.format_lesson.return_value = "formatted content"
        mock_file_writer.return_value.write_lesson_plan.return_value = AsyncMock(
            file_path="./output.md",
            file_size=1024
        )
        
        # 执行任务
        result = await worker_pool.execute_task(sample_task)
        
        assert result.success
        assert result.task_id == sample_task.task_id
        assert result.output_path == "./output.md"
    
    async def test_task_execution_failure(self, worker_pool, sample_task):
        """测试任务执行失败流程"""
        # Mock API服务抛出异常
        with patch('src.gs_video_report.batch.worker_pool.GeminiService') as mock_gemini:
            mock_gemini.return_value.analyze_video.side_effect = Exception("API Error")
            
            result = await worker_pool.execute_task(sample_task)
            
            assert not result.success
            assert "API Error" in str(result.error)
    
    async def test_worker_load_balancing(self, worker_pool):
        """测试工作负载均衡"""
        await worker_pool.start_workers()
        
        # 创建多个任务
        tasks = [create_sample_task(f"task_{i}") for i in range(4)]
        
        # 模拟任务分配
        with patch.object(worker_pool, 'execute_task', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = TaskResult(success=True, task_id="test")
            
            # 并发执行任务
            results = await asyncio.gather(*[
                worker_pool.execute_task(task) for task in tasks
            ])
            
            # 验证所有任务都被执行
            assert len(results) == 4
            assert all(result.success for result in results)
```

## 集成测试策略

### 1. 批量工作流集成测试

#### test_batch_workflow.py
```python
"""
批量处理工作流集成测试
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from src.gs_video_report.batch.processor import BatchProcessor
from src.gs_video_report.config import Config

class TestBatchWorkflowIntegration:
    """批量处理工作流集成测试"""
    
    @pytest.fixture
    def test_environment(self):
        """创建测试环境"""
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())
        
        # 创建测试视频文件（空文件）
        video_dir = temp_dir / "videos"
        video_dir.mkdir()
        
        test_videos = []
        for i in range(3):
            video_file = video_dir / f"test_video_{i}.mp4"
            video_file.write_bytes(b"fake video content")
            test_videos.append(str(video_file))
        
        # 创建输出目录
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        # 创建检查点目录
        checkpoint_dir = temp_dir / "checkpoints"
        checkpoint_dir.mkdir()
        
        yield {
            'temp_dir': temp_dir,
            'video_dir': video_dir,
            'output_dir': output_dir,
            'checkpoint_dir': checkpoint_dir,
            'test_videos': test_videos
        }
        
        # 清理
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_config(self):
        """测试配置"""
        return Config({
            'google_api': {
                'api_key': 'test_api_key',
                'model': 'gemini-2.5-flash'
            },
            'templates': {
                'default_template': 'chinese_transcript'
            },
            'batch_processing': {
                'default_parallel': 2,
                'checkpoint_interval_minutes': 1
            }
        })
    
    async def test_complete_batch_workflow(self, test_environment, test_config):
        """测试完整批量处理工作流"""
        # 创建视频输入
        inputs = []
        for i, video_path in enumerate(test_environment['test_videos']):
            input_data = VideoInput(
                source_type=InputType.FILE,
                source_path=video_path,
                template="chinese_transcript",
                output_path=str(test_environment['output_dir'] / f"output_{i}.md")
            )
            inputs.append(input_data)
        
        # 创建批量处理选项
        options = BatchOptions(
            parallel=2,
            checkpoint_dir=str(test_environment['checkpoint_dir']),
            dry_run=False
        )
        
        # Mock外部服务
        with patch('src.gs_video_report.services.gemini_service.GeminiService') as mock_gemini:
            # Mock成功的API响应
            mock_gemini.return_value.analyze_video.return_value = AsyncMock(
                content="分析结果",
                metadata={'word_count': 100}
            )
            
            # 创建并执行批量处理器
            processor = BatchProcessor(test_config, options)
            result = await processor.process_batch(inputs)
            
            # 验证结果
            assert result.success_rate > 0.5  # 至少50%成功
            assert result.total_tasks == 3
            assert result.completed_tasks >= 1
    
    async def test_checkpoint_and_recovery(self, test_environment, test_config):
        """测试检查点保存和恢复"""
        inputs = [create_test_input(video) for video in test_environment['test_videos']]
        options = BatchOptions(
            parallel=1,
            checkpoint_dir=str(test_environment['checkpoint_dir'])
        )
        
        processor = BatchProcessor(test_config, options)
        
        # 模拟处理中断
        with patch.object(processor, '_execute_processing') as mock_execute:
            mock_execute.side_effect = KeyboardInterrupt("模拟中断")
            
            try:
                await processor.process_batch(inputs)
            except KeyboardInterrupt:
                pass
        
        # 验证检查点文件已创建
        checkpoint_files = list(test_environment['checkpoint_dir'].glob("*.json"))
        assert len(checkpoint_files) > 0
        
        # 测试恢复
        checkpoint_id = checkpoint_files[0].stem
        new_processor = BatchProcessor(test_config, options)
        
        recovered_state = await new_processor.checkpoint_manager.load_checkpoint(checkpoint_id)
        assert recovered_state is not None
        assert recovered_state.batch_id == processor.batch_id
    
    async def test_error_handling_and_retry(self, test_environment, test_config):
        """测试错误处理和重试机制"""
        inputs = [create_test_input(test_environment['test_videos'][0])]
        options = BatchOptions(parallel=1, max_retries=2)
        
        processor = BatchProcessor(test_config, options)
        
        # Mock API服务，前两次失败，第三次成功
        call_count = 0
        async def mock_analyze_video(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("网络错误")
            return AsyncMock(content="成功结果", metadata={})
        
        with patch('src.gs_video_report.services.gemini_service.GeminiService') as mock_gemini:
            mock_gemini.return_value.analyze_video = mock_analyze_video
            
            result = await processor.process_batch(inputs)
            
            # 验证重试成功
            assert result.completed_tasks == 1
            assert call_count == 3  # 重试了2次后成功
```

## 性能测试策略

### 1. 吞吐量测试

#### test_throughput.py
```python
"""
吞吐量性能测试
"""
import pytest
import time
import asyncio
from src.gs_video_report.batch.processor import BatchProcessor

class TestThroughputPerformance:
    """吞吐量性能测试"""
    
    @pytest.mark.benchmark
    async def test_small_batch_throughput(self, benchmark, test_config):
        """测试小批量处理吞吐量"""
        inputs = [create_test_input(f"video_{i}.mp4") for i in range(10)]
        options = BatchOptions(parallel=4)
        
        async def process_batch():
            processor = BatchProcessor(test_config, options)
            with mock_successful_processing():
                return await processor.process_batch(inputs)
        
        result = await benchmark.pedantic(process_batch, rounds=3, iterations=1)
        
        # 验证性能指标
        assert result.average_processing_time < 300  # 5分钟内完成
        assert result.success_rate > 0.9  # 90%以上成功率
    
    @pytest.mark.benchmark
    async def test_concurrent_throughput_scaling(self, test_config):
        """测试并发数扩展的吞吐量影响"""
        inputs = [create_test_input(f"video_{i}.mp4") for i in range(20)]
        
        throughput_results = {}
        
        for parallel_count in [2, 4, 6, 8]:
            options = BatchOptions(parallel=parallel_count)
            processor = BatchProcessor(test_config, options)
            
            start_time = time.time()
            
            with mock_successful_processing():
                result = await processor.process_batch(inputs)
            
            end_time = time.time()
            duration = end_time - start_time
            throughput = len(inputs) / duration * 3600  # videos/hour
            
            throughput_results[parallel_count] = {
                'throughput': throughput,
                'duration': duration,
                'success_rate': result.success_rate
            }
        
        # 验证并发扩展效果
        assert throughput_results[4]['throughput'] > throughput_results[2]['throughput']
        
        # 记录基准数据
        for parallel, metrics in throughput_results.items():
            print(f"并发数 {parallel}: {metrics['throughput']:.1f} videos/hour")
    
    @pytest.mark.performance
    async def test_memory_usage_under_load(self, test_config):
        """测试负载下的内存使用"""
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        inputs = [create_test_input(f"video_{i}.mp4") for i in range(50)]
        options = BatchOptions(parallel=8)
        
        processor = BatchProcessor(test_config, options)
        
        # 监控内存使用
        memory_samples = []
        
        async def memory_monitor():
            while True:
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append(memory_mb)
                await asyncio.sleep(1)
        
        monitor_task = asyncio.create_task(memory_monitor())
        
        try:
            with mock_successful_processing():
                await processor.process_batch(inputs)
        finally:
            monitor_task.cancel()
        
        peak_memory = max(memory_samples)
        avg_memory = sum(memory_samples) / len(memory_samples)
        
        print(f"初始内存: {initial_memory:.1f} MB")
        print(f"峰值内存: {peak_memory:.1f} MB")
        print(f"平均内存: {avg_memory:.1f} MB")
        
        # 验证内存使用在合理范围内
        assert peak_memory < 2048  # 小于2GB
        assert peak_memory - initial_memory < 1024  # 增长小于1GB
```

### 2. 并发性能测试

#### test_concurrent_processing.py
```python
"""
并发处理性能测试
"""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestConcurrentPerformance:
    """并发处理性能测试"""
    
    @pytest.mark.performance
    async def test_api_limiter_performance(self, test_config):
        """测试API限流器性能"""
        from src.gs_video_report.batch.api_limiter import APILimiter
        
        limits = APILimits(
            max_concurrent=5,
            requests_per_minute=60,
            daily_quota=1000
        )
        
        limiter = APILimiter(limits)
        
        # 测试并发获取许可
        async def acquire_permit():
            permit = await limiter.acquire_permit()
            await asyncio.sleep(0.1)  # 模拟API调用
            await limiter.release_permit(permit, success=True, response_time=0.1)
        
        start_time = time.time()
        
        # 并发执行100个请求
        await asyncio.gather(*[acquire_permit() for _ in range(100)])
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 验证限流效果
        expected_min_duration = 100 / 60  # 基于每分钟60请求的限制
        assert duration >= expected_min_duration * 0.8  # 允许20%误差
        
        print(f"100个请求耗时: {duration:.2f}秒")
        print(f"实际吞吐量: {100/duration:.1f} 请求/秒")
    
    @pytest.mark.performance
    async def test_task_queue_concurrent_access(self):
        """测试任务队列并发访问性能"""
        from src.gs_video_report.batch.task_queue import TaskQueue
        
        queue = TaskQueue(":memory:")  # 使用内存数据库
        
        # 创建大量任务
        tasks = [create_test_task(f"task_{i}") for i in range(1000)]
        
        # 测试并发添加
        start_time = time.time()
        await queue.add_tasks(tasks)
        add_duration = time.time() - start_time
        
        # 测试并发获取
        async def get_tasks():
            retrieved_tasks = []
            for _ in range(100):
                task = await queue.get_next_task()
                if task:
                    retrieved_tasks.append(task)
            return retrieved_tasks
        
        start_time = time.time()
        results = await asyncio.gather(*[get_tasks() for _ in range(10)])
        get_duration = time.time() - start_time
        
        total_retrieved = sum(len(result) for result in results)
        
        print(f"添加1000个任务耗时: {add_duration:.3f}秒")
        print(f"并发获取{total_retrieved}个任务耗时: {get_duration:.3f}秒")
        
        # 验证性能指标
        assert add_duration < 1.0  # 添加1000个任务应在1秒内
        assert get_duration < 2.0  # 获取任务应在2秒内
        
        await queue.close()
    
    @pytest.mark.performance
    async def test_worker_pool_scalability(self, test_config):
        """测试工作线程池扩展性"""
        from src.gs_video_report.batch.worker_pool import WorkerPool
        
        scalability_results = {}
        
        # 测试不同工作线程数的性能
        for worker_count in [1, 2, 4, 8]:
            pool = WorkerPool(max_workers=worker_count, config=test_config)
            
            await pool.start_workers()
            
            # 创建任务并测试处理时间
            tasks = [create_test_task(f"task_{i}") for i in range(20)]
            
            start_time = time.time()
            
            with mock_successful_processing():
                results = await asyncio.gather(*[
                    pool.execute_task(task) for task in tasks
                ])
            
            end_time = time.time()
            duration = end_time - start_time
            
            await pool.stop_workers()
            
            scalability_results[worker_count] = {
                'duration': duration,
                'throughput': len(tasks) / duration,
                'success_rate': sum(1 for r in results if r.success) / len(results)
            }
        
        # 分析扩展性
        for workers, metrics in scalability_results.items():
            print(f"工作线程数 {workers}: {metrics['throughput']:.1f} tasks/sec")
        
        # 验证扩展效果
        assert scalability_results[4]['throughput'] > scalability_results[2]['throughput']
```

## 端到端测试策略

### 1. 完整用户场景测试

#### test_user_scenarios.py
```python
"""
端到端用户场景测试
"""
import pytest
import subprocess
import tempfile
import json
from pathlib import Path

class TestEndToEndScenarios:
    """端到端用户场景测试"""
    
    @pytest.fixture
    def cli_environment(self):
        """CLI测试环境"""
        temp_dir = Path(tempfile.mkdtemp())
        
        # 创建测试配置
        config_file = temp_dir / "test_config.yaml"
        config_content = """
google_api:
  api_key: "test_api_key"
  model: "gemini-2.5-flash"

templates:
  default_template: "chinese_transcript"

batch_processing:
  default_parallel: 2
"""
        config_file.write_text(config_content)
        
        # 创建测试视频目录
        video_dir = temp_dir / "videos"
        video_dir.mkdir()
        
        for i in range(3):
            video_file = video_dir / f"test_{i}.mp4"
            video_file.write_bytes(b"fake video content")
        
        # 创建输出目录
        output_dir = temp_dir / "output"
        output_dir.mkdir()
        
        yield {
            'temp_dir': temp_dir,
            'config_file': config_file,
            'video_dir': video_dir,
            'output_dir': output_dir
        }
        
        # 清理
        shutil.rmtree(temp_dir)
    
    def test_cli_batch_directory_processing(self, cli_environment):
        """测试CLI目录批量处理"""
        cmd = [
            "python", "-m", "src.gs_video_report.cli", "batch",
            "--input-dir", str(cli_environment['video_dir']),
            "--output", str(cli_environment['output_dir']),
            "--config", str(cli_environment['config_file']),
            "--parallel", "2",
            "--dry-run"  # 使用dry-run避免真实API调用
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 验证CLI执行成功
        assert result.returncode == 0
        assert "3 videos found" in result.stdout
        assert "dry-run" in result.stdout.lower()
    
    def test_cli_file_list_processing(self, cli_environment):
        """测试CLI文件列表处理"""
        # 创建文件列表
        file_list = cli_environment['temp_dir'] / "video_list.txt"
        video_files = list(cli_environment['video_dir'].glob("*.mp4"))
        file_list.write_text("\n".join(str(f) for f in video_files))
        
        cmd = [
            "python", "-m", "src.gs_video_report.cli", "batch",
            "--file-list", str(file_list),
            "--output", str(cli_environment['output_dir']),
            "--config", str(cli_environment['config_file']),
            "--template", "summary_report",
            "--dry-run"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "summary_report" in result.stdout
    
    def test_cli_progress_monitoring(self, cli_environment):
        """测试CLI进度监控功能"""
        progress_file = cli_environment['temp_dir'] / "progress.json"
        
        cmd = [
            "python", "-m", "src.gs_video_report.cli", "batch",
            "--input-dir", str(cli_environment['video_dir']),
            "--output", str(cli_environment['output_dir']),
            "--config", str(cli_environment['config_file']),
            "--progress-file", str(progress_file),
            "--dry-run"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        
        # 验证进度文件创建
        if progress_file.exists():
            progress_data = json.loads(progress_file.read_text())
            assert 'batch_id' in progress_data
            assert 'progress' in progress_data
    
    def test_cli_error_handling(self, cli_environment):
        """测试CLI错误处理"""
        # 测试无效输入目录
        cmd = [
            "python", "-m", "src.gs_video_report.cli", "batch",
            "--input-dir", "/nonexistent/directory",
            "--output", str(cli_environment['output_dir']),
            "--config", str(cli_environment['config_file'])
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 应该返回错误
        assert result.returncode != 0
        assert "does not exist" in result.stderr.lower()
    
    def test_cli_help_and_documentation(self):
        """测试CLI帮助信息"""
        cmd = ["python", "-m", "src.gs_video_report.cli", "batch", "--help"]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "--input-dir" in result.stdout
        assert "--parallel" in result.stdout
        assert "--template" in result.stdout
        assert "批量处理" in result.stdout or "batch" in result.stdout.lower()
```

## 压力测试策略

### 1. 大规模批处理测试

#### test_large_batches.py
```python
"""
大规模批处理压力测试
"""
import pytest
import asyncio
import psutil
from src.gs_video_report.batch.processor import BatchProcessor

class TestLargeBatchStress:
    """大规模批处理压力测试"""
    
    @pytest.mark.stress
    @pytest.mark.slow
    async def test_large_batch_processing(self, test_config):
        """测试大批量处理能力"""
        # 创建1000个任务
        inputs = [create_test_input(f"video_{i}.mp4") for i in range(1000)]
        
        options = BatchOptions(
            parallel=8,
            checkpoint_interval_minutes=1,
            max_retries=1
        )
        
        processor = BatchProcessor(test_config, options)
        
        # 监控系统资源
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_samples = []
        cpu_samples = []
        
        async def resource_monitor():
            while True:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                
                memory_samples.append(memory_mb)
                cpu_samples.append(cpu_percent)
                
                await asyncio.sleep(5)
        
        monitor_task = asyncio.create_task(resource_monitor())
        
        try:
            with mock_successful_processing():
                result = await processor.process_batch(inputs)
        finally:
            monitor_task.cancel()
        
        # 分析结果
        peak_memory = max(memory_samples) if memory_samples else initial_memory
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        
        print(f"处理任务数: {result.total_tasks}")
        print(f"成功率: {result.success_rate:.1%}")
        print(f"峰值内存: {peak_memory:.1f} MB")
        print(f"平均CPU: {avg_cpu:.1f}%")
        print(f"总处理时间: {result.total_processing_time:.1f}秒")
        
        # 验证压力测试通过标准
        assert result.success_rate > 0.95  # 95%以上成功率
        assert peak_memory < 3072  # 内存使用小于3GB
        assert avg_cpu < 90  # 平均CPU使用率小于90%
    
    @pytest.mark.stress
    async def test_memory_pressure_handling(self, test_config):
        """测试内存压力处理"""
        # 创建大量任务以产生内存压力
        inputs = [create_large_test_input(f"large_video_{i}.mp4") for i in range(100)]
        
        options = BatchOptions(
            parallel=4,
            memory_limit_mb=1024  # 限制内存使用
        )
        
        processor = BatchProcessor(test_config, options)
        
        # 监控内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        with mock_memory_intensive_processing():
            result = await processor.process_batch(inputs)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory
        
        print(f"内存增长: {memory_growth:.1f} MB")
        print(f"处理成功率: {result.success_rate:.1%}")
        
        # 验证内存控制有效
        assert memory_growth < 1536  # 内存增长控制在1.5GB内
        assert result.success_rate > 0.8  # 在内存压力下仍保持80%成功率
    
    @pytest.mark.stress
    async def test_long_running_stability(self, test_config):
        """测试长时间运行稳定性"""
        # 模拟长时间运行场景
        batch_count = 10
        tasks_per_batch = 50
        
        total_processed = 0
        total_errors = 0
        memory_samples = []
        
        for batch_num in range(batch_count):
            inputs = [create_test_input(f"batch_{batch_num}_video_{i}.mp4") 
                     for i in range(tasks_per_batch)]
            
            options = BatchOptions(parallel=4)
            processor = BatchProcessor(test_config, options)
            
            # 监控内存
            memory_before = psutil.Process().memory_info().rss / 1024 / 1024
            
            with mock_successful_processing():
                result = await processor.process_batch(inputs)
            
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples.append(memory_after)
            
            total_processed += result.completed_tasks
            total_errors += result.failed_tasks
            
            print(f"批次 {batch_num + 1}/{batch_count} 完成, "
                  f"成功: {result.completed_tasks}, "
                  f"失败: {result.failed_tasks}, "
                  f"内存: {memory_after:.1f} MB")
            
            # 短暂休息
            await asyncio.sleep(1)
        
        # 分析长期稳定性
        memory_trend = memory_samples[-1] - memory_samples[0]
        error_rate = total_errors / (total_processed + total_errors)
        
        print(f"总处理任务: {total_processed}")
        print(f"总错误数: {total_errors}")
        print(f"错误率: {error_rate:.1%}")
        print(f"内存趋势: {memory_trend:.1f} MB")
        
        # 验证长期稳定性
        assert error_rate < 0.05  # 错误率小于5%
        assert memory_trend < 500  # 内存增长小于500MB（可能的内存泄漏检测）
```

## 测试数据管理

### 测试数据工厂

#### conftest.py
```python
"""
pytest配置和测试数据工厂
"""
import pytest
from factory import Factory, Faker, SubFactory
from src.gs_video_report.batch.data_models import VideoInput, VideoTask, InputType

class VideoInputFactory(Factory):
    """VideoInput工厂"""
    class Meta:
        model = VideoInput
    
    source_type = InputType.FILE
    source_path = Faker('file_path', extension='mp4')
    template = "chinese_transcript"
    output_path = Faker('file_path', extension='md')
    file_size = Faker('random_int', min=1024000, max=1024000000)  # 1MB-1GB
    priority = Faker('random_int', min=1, max=100)

class VideoTaskFactory(Factory):
    """VideoTask工厂"""
    class Meta:
        model = VideoTask
    
    task_id = Faker('uuid4')
    batch_id = Faker('uuid4')
    input = SubFactory(VideoInputFactory)

@pytest.fixture
def sample_video_input():
    """样本视频输入"""
    return VideoInputFactory()

@pytest.fixture
def sample_video_task():
    """样本视频任务"""
    return VideoTaskFactory()

@pytest.fixture
def batch_of_tasks():
    """批量任务数据"""
    return VideoTaskFactory.create_batch(10)

# Mock配置
@pytest.fixture
def mock_successful_processing():
    """Mock成功处理的上下文管理器"""
    from unittest.mock import patch, AsyncMock
    
    def _mock_context():
        return patch.multiple(
            'src.gs_video_report.services.gemini_service.GeminiService',
            analyze_video=AsyncMock(return_value=AsyncMock(
                content="Mock analysis result",
                metadata={'word_count': 100}
            ))
        )
    
    return _mock_context
```

## 持续集成测试

### GitHub Actions配置

#### .github/workflows/batch-processing-tests.yml
```yaml
name: Batch Processing Tests

on:
  pull_request:
    paths:
      - 'src/gs_video_report/batch/**'
      - 'tests/batch/**'
  push:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install --with test
    
    - name: Run unit tests
      run: |
        poetry run pytest tests/unit/batch/ -v --cov=src/gs_video_report/batch --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install --with test
    
    - name: Run integration tests
      run: |
        poetry run pytest tests/integration/ -v --timeout=300
    
    - name: Run performance tests
      run: |
        poetry run pytest tests/performance/ -v -m "not stress" --benchmark-only

  stress-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install poetry
        poetry install --with test
    
    - name: Run stress tests
      run: |
        poetry run pytest tests/stress/ -v --timeout=1800
```

## 测试报告和指标

### 测试覆盖率目标
- **单元测试覆盖率**: > 85%
- **集成测试覆盖率**: > 70%
- **关键路径覆盖率**: 100%

### 性能基准指标
- **小批量吞吐量**: > 30 videos/hour (10个视频，4并发)
- **大批量吞吐量**: > 60 videos/hour (100个视频，8并发)
- **内存使用效率**: < 20MB per concurrent task
- **启动时间**: < 5秒
- **检查点保存时间**: < 3秒

### 质量门禁标准
- 所有单元测试必须通过
- 集成测试通过率 > 95%
- 性能测试基准达标
- 内存泄漏测试通过
- 代码覆盖率达标

---

*文档版本: v1.0*  
*创建日期: 2025-08-18*  
*负责人: 架构师@qa.mdc*  
*状态: 测试策略设计完成*
