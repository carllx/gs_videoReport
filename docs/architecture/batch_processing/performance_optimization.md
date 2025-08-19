# 批量处理功能 - 性能优化策略

## 概述

本文档详细描述批量处理功能的性能优化策略，包括并行处理优化、内存管理、I/O优化、API调用优化和系统资源管理等方面的具体方案。

## 性能目标设定

### 关键性能指标 (KPI)

#### 吞吐量指标
- **目标吞吐量**: 35-70 视频/小时 (依据并发数)
- **峰值吞吐量**: 80 视频/小时 (优化条件下)
- **最小吞吐量**: 20 视频/小时 (保底性能)

#### 资源使用指标
- **内存使用**: 峰值 < 2GB (8并发场景)
- **CPU使用**: 平均 60-80% (避免过载)
- **磁盘I/O**: < 100MB/s (避免瓶颈)
- **网络带宽**: < 50Mbps (API调用)

#### 响应时间指标
- **启动时间**: < 5秒 (包含恢复)
- **任务分配延迟**: < 100ms
- **进度更新延迟**: < 1秒
- **检查点保存时间**: < 3秒

#### 可靠性指标
- **错误恢复时间**: < 30秒
- **内存泄漏率**: 0% (长时间运行)
- **任务丢失率**: 0% (故障场景下)

## 并行处理优化

### 1. 动态并发调整算法

#### 自适应并发控制
```python
class AdaptiveConcurrencyController:
    """自适应并发控制器"""
    
    def __init__(self, initial_workers: int = 4):
        self.current_workers = initial_workers
        self.min_workers = 2
        self.max_workers = 8
        
        # 性能历史数据
        self.performance_window = deque(maxlen=20)
        self.adjustment_cooldown = 60  # 秒
        self.last_adjustment = 0
        
        # 性能阈值
        self.cpu_threshold_high = 0.85
        self.cpu_threshold_low = 0.40
        self.memory_threshold = 0.80
        self.error_rate_threshold = 0.10
        
    def should_adjust_workers(self, metrics: PerformanceMetrics) -> Optional[int]:
        """判断是否应该调整工作线程数"""
        
        # 冷却期检查
        if time.time() - self.last_adjustment < self.adjustment_cooldown:
            return None
            
        self.performance_window.append(metrics)
        
        if len(self.performance_window) < 5:
            return None  # 数据不足
            
        # 分析性能趋势
        recent_metrics = list(self.performance_window)[-5:]
        
        # 检查是否需要减少并发
        if self._should_decrease_workers(recent_metrics):
            new_workers = max(self.min_workers, self.current_workers - 1)
            return new_workers if new_workers != self.current_workers else None
            
        # 检查是否可以增加并发
        if self._should_increase_workers(recent_metrics):
            new_workers = min(self.max_workers, self.current_workers + 1)
            return new_workers if new_workers != self.current_workers else None
            
        return None
    
    def _should_decrease_workers(self, metrics_list: List[PerformanceMetrics]) -> bool:
        """判断是否应该减少工作线程"""
        avg_cpu = sum(m.cpu_usage for m in metrics_list) / len(metrics_list)
        avg_memory = sum(m.memory_usage for m in metrics_list) / len(metrics_list)
        avg_error_rate = sum(m.error_rate for m in metrics_list) / len(metrics_list)
        
        # CPU使用过高
        if avg_cpu > self.cpu_threshold_high:
            return True
            
        # 内存使用过高
        if avg_memory > self.memory_threshold:
            return True
            
        # 错误率过高
        if avg_error_rate > self.error_rate_threshold:
            return True
            
        # 吞吐量下降趋势
        if self._is_throughput_declining(metrics_list):
            return True
            
        return False
    
    def _should_increase_workers(self, metrics_list: List[PerformanceMetrics]) -> bool:
        """判断是否可以增加工作线程"""
        latest_metrics = metrics_list[-1]
        
        # 资源使用检查
        if (latest_metrics.cpu_usage < self.cpu_threshold_low and
            latest_metrics.memory_usage < self.memory_threshold * 0.7 and
            latest_metrics.error_rate < self.error_rate_threshold * 0.5):
            
            # 吞吐量改善空间检查
            if self._has_throughput_improvement_potential(metrics_list):
                return True
                
        return False
    
    def _is_throughput_declining(self, metrics_list: List[PerformanceMetrics]) -> bool:
        """检查吞吐量是否在下降"""
        if len(metrics_list) < 3:
            return False
            
        # 简单线性回归分析趋势
        throughputs = [m.throughput for m in metrics_list]
        x = list(range(len(throughputs)))
        
        # 计算斜率
        n = len(x)
        sum_xy = sum(x[i] * throughputs[i] for i in range(n))
        sum_x = sum(x)
        sum_y = sum(throughputs)
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        return slope < -0.1  # 负斜率表示下降趋势
```

### 2. 任务负载均衡

#### 智能任务分配
```python
class IntelligentTaskScheduler:
    """智能任务调度器"""
    
    def __init__(self):
        self.worker_performance = {}
        self.task_complexity_estimator = TaskComplexityEstimator()
        
    def assign_task_to_worker(self, task: VideoTask, 
                            available_workers: List[str]) -> str:
        """智能分配任务到最适合的工作线程"""
        
        # 计算任务复杂度
        task_complexity = self.task_complexity_estimator.estimate(task)
        
        # 评估每个工作线程的适配度
        worker_scores = {}
        for worker_id in available_workers:
            score = self._calculate_worker_score(worker_id, task_complexity)
            worker_scores[worker_id] = score
        
        # 选择得分最高的工作线程
        best_worker = max(worker_scores.items(), key=lambda x: x[1])[0]
        return best_worker
    
    def _calculate_worker_score(self, worker_id: str, 
                              task_complexity: float) -> float:
        """计算工作线程适配度得分"""
        if worker_id not in self.worker_performance:
            return 0.5  # 新工作线程默认得分
            
        perf = self.worker_performance[worker_id]
        
        # 基础性能得分 (0-1)
        base_score = perf.success_rate * 0.4 + (1 - perf.avg_processing_time / 600) * 0.3
        
        # 复杂度匹配得分
        complexity_match = 1 - abs(perf.avg_task_complexity - task_complexity)
        
        # 当前负载惩罚
        load_penalty = perf.current_load * 0.2
        
        return base_score + complexity_match * 0.3 - load_penalty

class TaskComplexityEstimator:
    """任务复杂度估算器"""
    
    def estimate(self, task: VideoTask) -> float:
        """估算任务复杂度 (0-1)"""
        complexity = 0.5  # 基础复杂度
        
        # 文件大小影响
        if hasattr(task.input, 'file_size'):
            size_gb = task.input.file_size / (1024 ** 3)
            complexity += min(0.3, size_gb * 0.1)
        
        # 视频时长影响
        if hasattr(task.input, 'estimated_duration'):
            duration_hours = task.input.estimated_duration / 3600
            complexity += min(0.2, duration_hours * 0.05)
        
        # 模板复杂度影响
        template_complexity = {
            'summary_report': 0.3,
            'chinese_transcript': 0.6,
            'comprehensive_lesson': 0.9
        }
        complexity += template_complexity.get(task.input.template, 0.5) * 0.2
        
        return min(1.0, complexity)
```

### 3. API调用优化

#### 智能API限流器
```python
class IntelligentAPILimiter:
    """智能API限流器"""
    
    def __init__(self, initial_limits: APILimits):
        self.limits = initial_limits
        self.usage_tracker = APIUsageTracker()
        self.backoff_controller = BackoffController()
        
        # 动态限制调整
        self.dynamic_limits = DynamicLimits(initial_limits)
        
    async def acquire_permit(self, request_type: str = 'default') -> APIPermit:
        """获取API调用许可"""
        
        # 检查配额限制
        await self._check_quota_limits()
        
        # 应用动态限流
        await self._apply_dynamic_throttling()
        
        # 获取许可
        permit = APIPermit(
            permit_id=self._generate_permit_id(),
            acquired_at=time.time(),
            request_type=request_type
        )
        
        # 记录使用
        self.usage_tracker.record_acquisition(permit)
        
        return permit
    
    async def release_permit(self, permit: APIPermit, 
                           success: bool, response_time: float):
        """释放API调用许可"""
        
        # 记录结果
        self.usage_tracker.record_completion(permit, success, response_time)
        
        # 更新动态限制
        await self.dynamic_limits.update_based_on_performance(
            success, response_time
        )
        
        # 处理失败情况
        if not success:
            await self.backoff_controller.handle_failure(permit)
    
    async def _check_quota_limits(self):
        """检查配额限制"""
        daily_usage = self.usage_tracker.get_daily_usage()
        
        if daily_usage >= self.limits.daily_quota:
            raise APIQuotaExceededException(
                f"Daily quota {self.limits.daily_quota} exceeded"
            )
    
    async def _apply_dynamic_throttling(self):
        """应用动态限流"""
        current_load = self.usage_tracker.get_current_load()
        
        # 根据当前负载调整延迟
        if current_load > 0.8:
            delay = self.dynamic_limits.calculate_throttle_delay(current_load)
            await asyncio.sleep(delay)

class DynamicLimits:
    """动态限制调整器"""
    
    def __init__(self, base_limits: APILimits):
        self.base_limits = base_limits
        self.current_multiplier = 1.0
        self.adjustment_history = deque(maxlen=50)
        
    async def update_based_on_performance(self, success: bool, 
                                        response_time: float):
        """基于性能更新限制"""
        
        # 记录性能数据
        self.adjustment_history.append(PerformanceData(
            success=success,
            response_time=response_time,
            timestamp=time.time()
        ))
        
        if len(self.adjustment_history) < 10:
            return
            
        recent_data = list(self.adjustment_history)[-10:]
        
        # 计算成功率和平均响应时间
        success_rate = sum(1 for d in recent_data if d.success) / len(recent_data)
        avg_response_time = sum(d.response_time for d in recent_data) / len(recent_data)
        
        # 调整策略
        if success_rate < 0.8 or avg_response_time > 120:
            # 性能下降，降低限制
            self.current_multiplier = max(0.5, self.current_multiplier * 0.9)
        elif success_rate > 0.95 and avg_response_time < 60:
            # 性能良好，可以提高限制
            self.current_multiplier = min(2.0, self.current_multiplier * 1.1)
    
    def get_effective_concurrent_limit(self) -> int:
        """获取有效并发限制"""
        return int(self.base_limits.max_concurrent * self.current_multiplier)
    
    def calculate_throttle_delay(self, current_load: float) -> float:
        """计算限流延迟"""
        if current_load <= 0.8:
            return 0.0
            
        # 指数增长的延迟
        excess_load = current_load - 0.8
        delay = (excess_load / 0.2) ** 2 * 2.0  # 最大2秒延迟
        
        return min(delay, 5.0)
```

## 内存管理优化

### 1. 内存池管理

#### 分层内存池
```python
class HierarchicalMemoryPool:
    """分层内存池管理器"""
    
    def __init__(self, total_memory_mb: int = 2048):
        self.total_memory_mb = total_memory_mb
        
        # 内存池分配
        self.pools = {
            'video_processing': MemoryPool(total_memory_mb * 0.6),  # 60%
            'api_responses': MemoryPool(total_memory_mb * 0.2),     # 20%
            'file_io': MemoryPool(total_memory_mb * 0.15),          # 15%
            'system_overhead': MemoryPool(total_memory_mb * 0.05)   # 5%
        }
        
        self.monitor = MemoryMonitor()
        self.gc_scheduler = GCScheduler()
    
    async def allocate_for_task(self, task_type: str, 
                               size_mb: float) -> MemoryAllocation:
        """为任务分配内存"""
        
        pool = self.pools.get(task_type, self.pools['system_overhead'])
        
        # 检查内存压力
        if await self._is_memory_pressure_high():
            await self._trigger_memory_cleanup()
        
        # 尝试分配
        allocation = await pool.allocate(size_mb)
        
        if allocation is None:
            # 分配失败，尝试垃圾回收
            await self.gc_scheduler.force_gc()
            allocation = await pool.allocate(size_mb)
        
        if allocation is None:
            # 仍然失败，减少其他池的使用
            await self._redistribute_memory(task_type, size_mb)
            allocation = await pool.allocate(size_mb)
        
        return allocation
    
    async def _is_memory_pressure_high(self) -> bool:
        """检查内存压力"""
        current_usage = self.monitor.get_current_usage_mb()
        return current_usage > self.total_memory_mb * 0.85
    
    async def _trigger_memory_cleanup(self):
        """触发内存清理"""
        # 清理不必要的缓存
        await self._cleanup_caches()
        
        # 强制垃圾回收
        await self.gc_scheduler.force_gc()
        
        # 压缩内存池
        for pool in self.pools.values():
            await pool.compress()

class MemoryPool:
    """单个内存池"""
    
    def __init__(self, max_size_mb: float):
        self.max_size_mb = max_size_mb
        self.allocated_mb = 0.0
        self.allocations = {}
        self._lock = asyncio.Lock()
    
    async def allocate(self, size_mb: float) -> Optional[MemoryAllocation]:
        """分配内存块"""
        async with self._lock:
            if self.allocated_mb + size_mb > self.max_size_mb:
                return None
            
            allocation_id = self._generate_allocation_id()
            allocation = MemoryAllocation(
                allocation_id=allocation_id,
                size_mb=size_mb,
                allocated_at=time.time()
            )
            
            self.allocations[allocation_id] = allocation
            self.allocated_mb += size_mb
            
            return allocation
    
    async def deallocate(self, allocation_id: str):
        """释放内存块"""
        async with self._lock:
            if allocation_id in self.allocations:
                allocation = self.allocations[allocation_id]
                self.allocated_mb -= allocation.size_mb
                del self.allocations[allocation_id]
```

### 2. 智能垃圾回收

#### 自适应GC调度
```python
class AdaptiveGCScheduler:
    """自适应垃圾回收调度器"""
    
    def __init__(self):
        self.gc_statistics = GCStatistics()
        self.memory_pressure_monitor = MemoryPressureMonitor()
        self.last_gc_time = 0
        self.adaptive_interval = 300  # 初始5分钟间隔
    
    async def schedule_gc_if_needed(self):
        """根据需要调度垃圾回收"""
        
        current_time = time.time()
        memory_pressure = self.memory_pressure_monitor.get_pressure_level()
        
        # 基于内存压力的紧急GC
        if memory_pressure > 0.9:
            await self._emergency_gc()
            return
        
        # 基于时间间隔的常规GC
        if current_time - self.last_gc_time > self.adaptive_interval:
            await self._scheduled_gc()
            return
        
        # 基于分配率的预测性GC
        if self._should_preemptive_gc():
            await self._preemptive_gc()
    
    async def _emergency_gc(self):
        """紧急垃圾回收"""
        logger.warning("Emergency GC triggered due to high memory pressure")
        
        start_time = time.time()
        initial_memory = psutil.Process().memory_info().rss
        
        # 执行全面垃圾回收
        gc.collect()
        
        # 记录统计信息
        final_memory = psutil.Process().memory_info().rss
        gc_time = time.time() - start_time
        
        self.gc_statistics.record_gc_event(
            gc_type='emergency',
            duration=gc_time,
            memory_freed=initial_memory - final_memory
        )
        
        self.last_gc_time = time.time()
    
    async def _scheduled_gc(self):
        """计划垃圾回收"""
        # 检查是否真的需要GC
        if not self._is_gc_beneficial():
            self._adjust_gc_interval(increase=True)
            return
        
        await self._perform_gc('scheduled')
        self._adjust_gc_interval(increase=False)
    
    def _adjust_gc_interval(self, increase: bool):
        """调整GC间隔"""
        if increase:
            self.adaptive_interval = min(600, self.adaptive_interval * 1.2)
        else:
            self.adaptive_interval = max(60, self.adaptive_interval * 0.8)
    
    def _is_gc_beneficial(self) -> bool:
        """判断GC是否有益"""
        # 基于历史数据判断GC效果
        recent_gcs = self.gc_statistics.get_recent_events(5)
        
        if not recent_gcs:
            return True
        
        avg_memory_freed = sum(gc.memory_freed for gc in recent_gcs) / len(recent_gcs)
        avg_gc_time = sum(gc.duration for gc in recent_gcs) / len(recent_gcs)
        
        # 如果释放内存量小且耗时长，则认为不必要
        return avg_memory_freed > 50 * 1024 * 1024 or avg_gc_time < 0.5  # 50MB或0.5秒
```

### 3. 流式处理优化

#### 流式数据处理
```python
class StreamingDataProcessor:
    """流式数据处理器"""
    
    def __init__(self, chunk_size_mb: int = 10):
        self.chunk_size_mb = chunk_size_mb
        self.processing_pipeline = ProcessingPipeline()
        
    async def process_large_video_streaming(self, video_path: str) -> AsyncIterator[ProcessingChunk]:
        """流式处理大视频文件"""
        
        file_size = os.path.getsize(video_path)
        chunk_size_bytes = self.chunk_size_mb * 1024 * 1024
        
        async with aiofiles.open(video_path, 'rb') as f:
            chunk_index = 0
            
            while True:
                chunk_data = await f.read(chunk_size_bytes)
                if not chunk_data:
                    break
                
                # 流式处理块
                processed_chunk = await self.processing_pipeline.process_chunk(
                    chunk_data, chunk_index, file_size
                )
                
                yield processed_chunk
                
                # 及时释放内存
                del chunk_data
                if chunk_index % 5 == 0:  # 每5个块强制GC
                    gc.collect()
                
                chunk_index += 1
    
    async def aggregate_streaming_results(self, 
                                        chunk_stream: AsyncIterator[ProcessingChunk]) -> FinalResult:
        """聚合流式处理结果"""
        
        aggregator = ResultAggregator()
        
        async for chunk in chunk_stream:
            await aggregator.add_chunk(chunk)
            
            # 定期保存中间结果
            if aggregator.should_save_intermediate():
                await aggregator.save_checkpoint()
        
        return await aggregator.finalize()
```

## I/O性能优化

### 1. 异步I/O优化

#### 并发文件操作
```python
class OptimizedFileIO:
    """优化的文件I/O操作"""
    
    def __init__(self, max_concurrent_io: int = 10):
        self.io_semaphore = asyncio.Semaphore(max_concurrent_io)
        self.read_cache = LRUCache(maxsize=100)
        self.write_buffer = WriteBuffer()
        
    async def batch_read_files(self, file_paths: List[str]) -> Dict[str, bytes]:
        """批量读取文件"""
        
        # 创建并发读取任务
        tasks = []
        for file_path in file_paths:
            task = asyncio.create_task(self._read_file_with_cache(file_path))
            tasks.append(task)
        
        # 等待所有读取完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        file_contents = {}
        for file_path, result in zip(file_paths, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to read {file_path}: {result}")
                continue
            file_contents[file_path] = result
        
        return file_contents
    
    async def _read_file_with_cache(self, file_path: str) -> bytes:
        """带缓存的文件读取"""
        
        # 检查缓存
        if file_path in self.read_cache:
            return self.read_cache[file_path]
        
        async with self.io_semaphore:
            try:
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
                
                # 缓存小文件
                if len(content) < 10 * 1024 * 1024:  # < 10MB
                    self.read_cache[file_path] = content
                
                return content
                
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                raise
    
    async def batch_write_files(self, write_operations: List[WriteOperation]):
        """批量写入文件"""
        
        # 按目录分组，减少目录锁竞争
        operations_by_dir = defaultdict(list)
        for op in write_operations:
            dir_path = os.path.dirname(op.file_path)
            operations_by_dir[dir_path].append(op)
        
        # 并发处理每个目录
        tasks = []
        for dir_path, ops in operations_by_dir.items():
            task = asyncio.create_task(self._write_files_in_directory(ops))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)

class WriteBuffer:
    """写入缓冲区"""
    
    def __init__(self, buffer_size_mb: int = 50):
        self.buffer_size_bytes = buffer_size_mb * 1024 * 1024
        self.buffer = {}
        self.current_size = 0
        self._lock = asyncio.Lock()
    
    async def add_write(self, file_path: str, content: bytes):
        """添加写入操作到缓冲区"""
        async with self._lock:
            self.buffer[file_path] = content
            self.current_size += len(content)
            
            # 检查是否需要刷新缓冲区
            if self.current_size > self.buffer_size_bytes:
                await self._flush_buffer()
    
    async def _flush_buffer(self):
        """刷新缓冲区"""
        if not self.buffer:
            return
        
        # 并发写入所有缓冲的文件
        write_tasks = []
        for file_path, content in self.buffer.items():
            task = asyncio.create_task(self._write_file(file_path, content))
            write_tasks.append(task)
        
        await asyncio.gather(*write_tasks, return_exceptions=True)
        
        # 清空缓冲区
        self.buffer.clear()
        self.current_size = 0
```

### 2. 磁盘I/O优化

#### 智能磁盘调度
```python
class DiskIOScheduler:
    """磁盘I/O调度器"""
    
    def __init__(self):
        self.pending_reads = deque()
        self.pending_writes = deque()
        self.io_stats = IOStatistics()
        
    def schedule_read(self, file_path: str, priority: int = 5) -> Future:
        """调度读取操作"""
        operation = IOOperation(
            operation_type='read',
            file_path=file_path,
            priority=priority,
            scheduled_at=time.time()
        )
        
        # 按优先级插入队列
        bisect.insort(self.pending_reads, operation)
        
        return operation.future
    
    def schedule_write(self, file_path: str, content: bytes, 
                      priority: int = 5) -> Future:
        """调度写入操作"""
        operation = IOOperation(
            operation_type='write',
            file_path=file_path,
            content=content,
            priority=priority,
            scheduled_at=time.time()
        )
        
        bisect.insort(self.pending_writes, operation)
        return operation.future
    
    async def process_io_queue(self):
        """处理I/O队列"""
        while True:
            try:
                # 优先处理读取操作（通常更紧急）
                if self.pending_reads:
                    operation = self.pending_reads.popleft()
                    await self._execute_read(operation)
                elif self.pending_writes:
                    operation = self.pending_writes.popleft()
                    await self._execute_write(operation)
                else:
                    await asyncio.sleep(0.1)  # 队列为空，短暂等待
                    
            except Exception as e:
                logger.error(f"IO operation failed: {e}")
    
    async def _execute_read(self, operation: IOOperation):
        """执行读取操作"""
        start_time = time.time()
        
        try:
            async with aiofiles.open(operation.file_path, 'rb') as f:
                content = await f.read()
            
            operation.future.set_result(content)
            
        except Exception as e:
            operation.future.set_exception(e)
        finally:
            # 记录I/O统计
            duration = time.time() - start_time
            self.io_stats.record_operation('read', duration, True)
```

## 系统资源监控

### 1. 实时资源监控

#### 综合资源监控器
```python
class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.metrics_history = deque(maxlen=300)  # 5分钟历史
        self.alert_thresholds = AlertThresholds()
        self.is_monitoring = False
        
    async def start_monitoring(self):
        """开始资源监控"""
        self.is_monitoring = True
        await asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """监控主循环"""
        while self.is_monitoring:
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # 检查告警条件
                await self._check_alerts(metrics)
                
                # 自适应调整
                await self._adaptive_adjustments(metrics)
                
                await asyncio.sleep(self.sampling_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)  # 错误时等待更长时间
    
    async def _collect_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        process = psutil.Process()
        
        # CPU指标
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count()
        
        # 内存指标
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        # 磁盘I/O指标
        disk_io = psutil.disk_io_counters()
        
        # 网络I/O指标
        network_io = psutil.net_io_counters()
        
        return SystemMetrics(
            timestamp=time.time(),
            
            # CPU
            cpu_usage_percent=cpu_percent,
            cpu_count=cpu_count,
            
            # 内存
            process_memory_mb=memory_info.rss / 1024 / 1024,
            system_memory_total_mb=system_memory.total / 1024 / 1024,
            system_memory_available_mb=system_memory.available / 1024 / 1024,
            memory_usage_percent=system_memory.percent,
            
            # 磁盘I/O
            disk_read_mb_per_sec=self._calculate_rate(disk_io.read_bytes, 'disk_read'),
            disk_write_mb_per_sec=self._calculate_rate(disk_io.write_bytes, 'disk_write'),
            
            # 网络I/O
            network_sent_mb_per_sec=self._calculate_rate(network_io.bytes_sent, 'net_sent'),
            network_recv_mb_per_sec=self._calculate_rate(network_io.bytes_recv, 'net_recv'),
        )
    
    async def _check_alerts(self, metrics: SystemMetrics):
        """检查告警条件"""
        alerts = []
        
        # CPU使用率告警
        if metrics.cpu_usage_percent > self.alert_thresholds.cpu_high:
            alerts.append(Alert(
                type='cpu_high',
                severity='warning',
                message=f"High CPU usage: {metrics.cpu_usage_percent:.1f}%"
            ))
        
        # 内存使用率告警
        if metrics.memory_usage_percent > self.alert_thresholds.memory_high:
            alerts.append(Alert(
                type='memory_high',
                severity='warning',
                message=f"High memory usage: {metrics.memory_usage_percent:.1f}%"
            ))
        
        # 磁盘I/O告警
        if metrics.disk_write_mb_per_sec > self.alert_thresholds.disk_io_high:
            alerts.append(Alert(
                type='disk_io_high',
                severity='info',
                message=f"High disk I/O: {metrics.disk_write_mb_per_sec:.1f} MB/s"
            ))
        
        # 发送告警
        for alert in alerts:
            await self._send_alert(alert)
```

### 2. 自动性能调优

#### 自适应性能调优器
```python
class AdaptivePerformanceTuner:
    """自适应性能调优器"""
    
    def __init__(self, batch_processor):
        self.batch_processor = batch_processor
        self.tuning_history = deque(maxlen=50)
        self.current_config = PerformanceConfig()
        
    async def continuous_tuning(self):
        """持续性能调优"""
        while True:
            try:
                # 收集性能数据
                perf_data = await self._collect_performance_data()
                
                # 分析性能趋势
                tuning_suggestions = await self._analyze_performance(perf_data)
                
                # 应用调优建议
                await self._apply_tuning_suggestions(tuning_suggestions)
                
                # 等待调优效果显现
                await asyncio.sleep(120)  # 2分钟间隔
                
            except Exception as e:
                logger.error(f"Performance tuning error: {e}")
                await asyncio.sleep(300)  # 错误时等待更长时间
    
    async def _analyze_performance(self, perf_data: PerformanceData) -> List[TuningSuggestion]:
        """分析性能数据并生成调优建议"""
        suggestions = []
        
        # 分析吞吐量趋势
        if self._is_throughput_declining():
            if perf_data.cpu_usage > 0.85:
                suggestions.append(TuningSuggestion(
                    type='reduce_concurrency',
                    reason='High CPU usage causing throughput decline',
                    target_value=max(2, self.current_config.worker_count - 1)
                ))
            elif perf_data.memory_usage > 0.80:
                suggestions.append(TuningSuggestion(
                    type='enable_memory_optimization',
                    reason='High memory usage affecting performance'
                ))
        
        # 分析资源利用率
        elif (perf_data.cpu_usage < 0.60 and 
              perf_data.memory_usage < 0.70 and 
              perf_data.error_rate < 0.05):
            suggestions.append(TuningSuggestion(
                type='increase_concurrency',
                reason='Resources underutilized, can increase parallelism',
                target_value=min(8, self.current_config.worker_count + 1)
            ))
        
        # 分析API性能
        if perf_data.avg_api_response_time > 180:  # 3分钟
            suggestions.append(TuningSuggestion(
                type='adjust_api_limits',
                reason='High API response time, reduce request frequency'
            ))
        
        return suggestions
    
    async def _apply_tuning_suggestions(self, suggestions: List[TuningSuggestion]):
        """应用调优建议"""
        for suggestion in suggestions:
            try:
                await self._apply_single_suggestion(suggestion)
                
                # 记录调优历史
                self.tuning_history.append(TuningRecord(
                    timestamp=time.time(),
                    suggestion=suggestion,
                    applied=True
                ))
                
            except Exception as e:
                logger.error(f"Failed to apply tuning suggestion {suggestion.type}: {e}")
    
    async def _apply_single_suggestion(self, suggestion: TuningSuggestion):
        """应用单个调优建议"""
        if suggestion.type == 'reduce_concurrency':
            await self.batch_processor.adjust_worker_count(suggestion.target_value)
            self.current_config.worker_count = suggestion.target_value
            
        elif suggestion.type == 'increase_concurrency':
            await self.batch_processor.adjust_worker_count(suggestion.target_value)
            self.current_config.worker_count = suggestion.target_value
            
        elif suggestion.type == 'enable_memory_optimization':
            await self.batch_processor.enable_memory_optimization()
            self.current_config.memory_optimization_enabled = True
            
        elif suggestion.type == 'adjust_api_limits':
            await self.batch_processor.adjust_api_limits(reduce_by=0.2)
            
        logger.info(f"Applied tuning suggestion: {suggestion.type}")
```

## 性能基准测试

### 基准测试套件
```python
class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self):
        self.benchmark_results = {}
        
    async def run_comprehensive_benchmark(self) -> BenchmarkReport:
        """运行综合性能基准测试"""
        
        benchmarks = [
            ('small_batch', self._benchmark_small_batch),
            ('medium_batch', self._benchmark_medium_batch),
            ('large_batch', self._benchmark_large_batch),
            ('memory_stress', self._benchmark_memory_stress),
            ('api_throughput', self._benchmark_api_throughput),
            ('io_performance', self._benchmark_io_performance)
        ]
        
        results = {}
        for name, benchmark_func in benchmarks:
            logger.info(f"Running benchmark: {name}")
            result = await benchmark_func()
            results[name] = result
            
            # 恢复系统状态
            await self._reset_system_state()
            await asyncio.sleep(30)  # 冷却时间
        
        return BenchmarkReport(results)
    
    async def _benchmark_small_batch(self) -> BenchmarkResult:
        """小批量处理基准测试"""
        video_count = 10
        parallel_workers = 4
        
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss
        
        # 模拟小批量处理
        result = await self._simulate_batch_processing(
            video_count=video_count,
            avg_video_size_mb=50,
            parallel_workers=parallel_workers
        )
        
        end_time = time.time()
        memory_after = psutil.Process().memory_info().rss
        
        return BenchmarkResult(
            name='small_batch',
            duration=end_time - start_time,
            throughput=video_count / (end_time - start_time) * 3600,  # videos/hour
            memory_used_mb=(memory_after - memory_before) / 1024 / 1024,
            success_rate=result.success_rate,
            metadata={
                'video_count': video_count,
                'parallel_workers': parallel_workers,
                'avg_video_size_mb': 50
            }
        )
```

---

*文档版本: v1.0*  
*创建日期: 2025-08-18*  
*负责人: 架构师@qa.mdc*  
*状态: 性能优化策略完成*
