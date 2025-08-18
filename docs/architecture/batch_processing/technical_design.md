# 批量处理功能 - 技术设计规范

## 概述

本文档详细描述批量处理功能的技术实现设计，包括核心组件的内部架构、接口定义、算法设计和实现细节。

## 核心组件详细设计

### 1. BatchProcessor (批量处理器)

#### 1.1 组件职责
- 批量处理流程的主控制器
- 协调各子组件的工作
- 管理批量处理的生命周期
- 处理用户控制命令

#### 1.2 内部架构
```python
class BatchProcessor:
    """批量处理核心引擎"""
    
    def __init__(self, config: Config, options: BatchOptions):
        self.config = config
        self.options = options
        self.batch_id = self._generate_batch_id()
        
        # 核心组件初始化
        self.task_queue = TaskQueue(self.config)
        self.worker_pool = WorkerPool(
            max_workers=options.parallel,
            api_limiter=APILimiter(config.api_limits)
        )
        self.progress_monitor = ProgressMonitor()
        self.checkpoint_manager = CheckpointManager(
            checkpoint_dir=options.checkpoint_dir
        )
        
        # 状态管理
        self.batch_state = BatchState(
            batch_id=self.batch_id,
            status=BatchStatus.INITIALIZING,
            config=options
        )
        self._shutdown_event = asyncio.Event()
    
    async def process_batch(self, inputs: List[VideoInput]) -> BatchResult:
        """执行批量处理主流程"""
        try:
            # 1. 初始化阶段
            await self._initialize_batch(inputs)
            
            # 2. 执行处理阶段
            await self._execute_processing()
            
            # 3. 完成阶段
            return await self._finalize_batch()
            
        except Exception as e:
            await self._handle_batch_error(e)
            raise
    
    async def _initialize_batch(self, inputs: List[VideoInput]) -> None:
        """初始化批量处理"""
        # 创建任务队列
        tasks = [self._create_task(inp) for inp in inputs]
        await self.task_queue.add_tasks(tasks)
        
        # 初始化进度监控
        self.progress_monitor.start_monitoring(len(tasks))
        
        # 保存初始检查点
        await self.checkpoint_manager.save_checkpoint(self.batch_state)
        
        # 更新状态
        self.batch_state.status = BatchStatus.RUNNING
        self.batch_state.total_tasks = len(tasks)
    
    async def _execute_processing(self) -> None:
        """执行并发处理"""
        # 启动工作线程池
        await self.worker_pool.start_workers()
        
        # 启动监控任务
        monitor_task = asyncio.create_task(self._monitor_progress())
        checkpoint_task = asyncio.create_task(self._periodic_checkpoint())
        
        try:
            # 等待所有任务完成或收到停止信号
            await asyncio.wait_for(
                self._wait_for_completion(),
                timeout=self.options.timeout
            )
        finally:
            # 清理资源
            monitor_task.cancel()
            checkpoint_task.cancel()
            await self.worker_pool.stop_workers()
    
    async def _wait_for_completion(self) -> None:
        """等待批量处理完成"""
        while not self._shutdown_event.is_set():
            queue_status = await self.task_queue.get_status()
            
            if queue_status.pending_count == 0 and queue_status.running_count == 0:
                # 所有任务都已完成
                break
                
            await asyncio.sleep(1)  # 每秒检查一次
    
    def pause_processing(self) -> None:
        """暂停批量处理"""
        self.batch_state.status = BatchStatus.PAUSED
        self.worker_pool.pause_workers()
    
    def resume_processing(self) -> None:
        """恢复批量处理"""
        self.batch_state.status = BatchStatus.RUNNING
        self.worker_pool.resume_workers()
    
    def cancel_processing(self) -> None:
        """取消批量处理"""
        self.batch_state.status = BatchStatus.CANCELLED
        self._shutdown_event.set()
```

#### 1.3 错误处理策略
```python
class BatchErrorHandler:
    """批量处理错误处理器"""
    
    ERROR_RETRY_STRATEGIES = {
        NetworkError: RetryStrategy(max_retries=3, backoff_factor=2),
        APIQuotaError: RetryStrategy(max_retries=1, delay=3600),  # 1小时后重试
        FileNotFoundError: RetryStrategy(max_retries=0),  # 不重试
        PermissionError: RetryStrategy(max_retries=0),   # 不重试
    }
    
    @classmethod
    async def handle_task_error(cls, task: VideoTask, error: Exception) -> ErrorAction:
        """处理单个任务错误"""
        error_type = type(error)
        
        if error_type in cls.ERROR_RETRY_STRATEGIES:
            strategy = cls.ERROR_RETRY_STRATEGIES[error_type]
            
            if task.retry_count < strategy.max_retries:
                await asyncio.sleep(strategy.get_delay(task.retry_count))
                return ErrorAction.RETRY
            else:
                return ErrorAction.FAIL
        else:
            # 未知错误，记录并失败
            logger.error(f"Unknown error in task {task.task_id}: {error}")
            return ErrorAction.FAIL
```

### 2. TaskQueue (任务队列)

#### 2.1 组件设计
```python
class TaskQueue:
    """高性能任务队列实现"""
    
    def __init__(self, config: Config):
        self.config = config
        self._queue = asyncio.PriorityQueue()
        self._tasks_map = {}  # task_id -> VideoTask
        self._status_counters = {
            TaskStatus.PENDING: 0,
            TaskStatus.RUNNING: 0,
            TaskStatus.COMPLETED: 0,
            TaskStatus.FAILED: 0,
            TaskStatus.CANCELLED: 0
        }
        self._lock = asyncio.Lock()
    
    async def add_tasks(self, tasks: List[VideoTask]) -> None:
        """批量添加任务"""
        async with self._lock:
            for task in tasks:
                priority = self._calculate_priority(task)
                await self._queue.put((priority, task.created_at, task))
                self._tasks_map[task.task_id] = task
                self._status_counters[TaskStatus.PENDING] += 1
    
    async def get_next_task(self) -> Optional[VideoTask]:
        """获取下一个待处理任务"""
        try:
            _, _, task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            
            async with self._lock:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                self._status_counters[TaskStatus.PENDING] -= 1
                self._status_counters[TaskStatus.RUNNING] += 1
                
            return task
        except asyncio.TimeoutError:
            return None
    
    async def mark_completed(self, task_id: str, result: TaskResult) -> None:
        """标记任务完成"""
        async with self._lock:
            if task_id in self._tasks_map:
                task = self._tasks_map[task_id]
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                
                self._status_counters[TaskStatus.RUNNING] -= 1
                self._status_counters[TaskStatus.COMPLETED] += 1
    
    def _calculate_priority(self, task: VideoTask) -> int:
        """计算任务优先级"""
        # 基础优先级
        priority = 50
        
        # 文件大小影响 (小文件优先)
        if hasattr(task.input, 'file_size'):
            if task.input.file_size < 100 * 1024 * 1024:  # < 100MB
                priority -= 10
            elif task.input.file_size > 500 * 1024 * 1024:  # > 500MB
                priority += 10
        
        # 重试任务优先级降低
        priority += task.retry_count * 20
        
        return priority
```

#### 2.2 持久化设计
```python
class TaskQueuePersistence:
    """任务队列持久化管理"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL,
                    input_data TEXT NOT NULL,  -- JSON序列化的VideoInput
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    result_data TEXT  -- JSON序列化的TaskResult
                );
                
                CREATE INDEX IF NOT EXISTS idx_batch_status 
                ON tasks(batch_id, status);
                
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON tasks(created_at);
            """)
    
    async def save_tasks(self, tasks: List[VideoTask]) -> None:
        """保存任务到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            for task in tasks:
                conn.execute("""
                    INSERT OR REPLACE INTO tasks 
                    (task_id, batch_id, input_data, status, created_at, 
                     started_at, completed_at, retry_count, error_message, result_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.task_id, task.batch_id, 
                    json.dumps(task.input.__dict__),
                    task.status.value,
                    task.created_at, task.started_at, task.completed_at,
                    task.retry_count, task.error_message,
                    json.dumps(task.result.__dict__) if task.result else None
                ))
            conn.commit()
```

### 3. WorkerPool (工作线程池)

#### 3.1 并发控制设计
```python
class WorkerPool:
    """高效并发工作线程池"""
    
    def __init__(self, max_workers: int, api_limiter: APILimiter):
        self.max_workers = max_workers
        self.api_limiter = api_limiter
        self.workers = []
        self.is_running = False
        self.is_paused = False
        
        # 工作线程状态追踪
        self.worker_status = {}
        
        # 重用现有服务组件
        self.gemini_service = None
        self.lesson_formatter = None
        self.file_writer = None
    
    async def start_workers(self) -> None:
        """启动工作线程池"""
        self.is_running = True
        
        # 初始化服务组件
        await self._init_services()
        
        # 创建工作线程
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(f"worker_{i}"))
            self.workers.append(worker)
            self.worker_status[f"worker_{i}"] = WorkerStatus.IDLE
    
    async def _worker_loop(self, worker_id: str) -> None:
        """单个工作线程的主循环"""
        while self.is_running:
            try:
                # 检查暂停状态
                await self._check_pause_state()
                
                # 从队列获取任务
                task = await self.task_queue.get_next_task()
                if not task:
                    await asyncio.sleep(0.1)
                    continue
                
                # 执行任务
                self.worker_status[worker_id] = WorkerStatus.WORKING
                result = await self._execute_task(task)
                
                # 处理结果
                if result.success:
                    await self.task_queue.mark_completed(task.task_id, result)
                else:
                    await self._handle_task_failure(task, result.error)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)  # 错误后短暂休息
            finally:
                self.worker_status[worker_id] = WorkerStatus.IDLE
    
    async def _execute_task(self, task: VideoTask) -> TaskResult:
        """执行单个视频处理任务"""
        try:
            # API限流控制
            await self.api_limiter.acquire()
            
            # 复用现有处理流程
            analysis_result = await self.gemini_service.analyze_video(
                task.input.source_path, 
                task.input.template
            )
            
            formatted_content = self.lesson_formatter.format_lesson(
                analysis_result.to_lesson_plan_data()
            )
            
            write_result = await self.file_writer.write_lesson_plan(
                formatted_content,
                task.input.output_path
            )
            
            return TaskResult(
                success=True,
                task_id=task.task_id,
                output_path=write_result.file_path,
                processing_time=time.time() - task.started_at.timestamp(),
                metadata={
                    'word_count': analysis_result.word_count,
                    'file_size': write_result.file_size
                }
            )
            
        except Exception as e:
            return TaskResult(
                success=False,
                task_id=task.task_id,
                error=e,
                processing_time=time.time() - task.started_at.timestamp()
            )
        finally:
            self.api_limiter.release()
```

#### 3.2 API限流器设计
```python
class APILimiter:
    """智能API调用限流器"""
    
    def __init__(self, limits: APILimits):
        self.limits = limits
        
        # 令牌桶算法实现
        self.concurrent_semaphore = asyncio.Semaphore(limits.max_concurrent)
        self.rate_limiter = TokenBucket(
            capacity=limits.requests_per_minute,
            refill_rate=limits.requests_per_minute / 60.0
        )
        
        # 配额追踪
        self.daily_usage = DailyUsageTracker()
        
        # 自适应调整
        self.adaptive_controller = AdaptiveController()
    
    async def acquire(self) -> None:
        """获取API调用许可"""
        # 并发限制
        await self.concurrent_semaphore.acquire()
        
        # 频率限制
        await self.rate_limiter.consume(1)
        
        # 配额检查
        if not await self.daily_usage.check_quota_available():
            raise APIQuotaExceededException("Daily quota exceeded")
        
        # 记录使用
        await self.daily_usage.record_usage()
    
    def release(self) -> None:
        """释放API调用许可"""
        self.concurrent_semaphore.release()

class TokenBucket:
    """令牌桶算法实现"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int) -> None:
        """消费令牌"""
        async with self._lock:
            await self._refill_tokens()
            
            while self.tokens < tokens:
                # 等待令牌补充
                wait_time = tokens / self.refill_rate
                await asyncio.sleep(min(wait_time, 1.0))
                await self._refill_tokens()
            
            self.tokens -= tokens
    
    async def _refill_tokens(self) -> None:
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
```

### 4. ProgressMonitor (进度监控)

#### 4.1 实时监控设计
```python
class ProgressMonitor:
    """实时进度监控和ETA估算"""
    
    def __init__(self):
        self.start_time = None
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        
        # 性能统计
        self.processing_times = deque(maxlen=100)  # 最近100个任务的处理时间
        self.throughput_samples = deque(maxlen=10)  # 最近10分钟的吞吐量样本
        
        # 事件处理
        self.event_queue = asyncio.Queue()
        self.subscribers = []
    
    def start_monitoring(self, total_tasks: int) -> None:
        """开始监控"""
        self.start_time = datetime.now()
        self.total_tasks = total_tasks
        self._start_background_tasks()
    
    async def update_progress(self, event: ProgressEvent) -> None:
        """更新进度信息"""
        await self.event_queue.put(event)
    
    async def _process_events(self) -> None:
        """处理进度事件"""
        while True:
            try:
                event = await self.event_queue.get()
                await self._handle_event(event)
                
                # 通知订阅者
                for subscriber in self.subscribers:
                    await subscriber.on_progress_update(self.get_current_progress())
                    
            except Exception as e:
                logger.error(f"Progress monitor error: {e}")
    
    async def _handle_event(self, event: ProgressEvent) -> None:
        """处理单个进度事件"""
        if event.type == ProgressEventType.TASK_COMPLETED:
            self.completed_tasks += 1
            self.processing_times.append(event.processing_time)
            
        elif event.type == ProgressEventType.TASK_FAILED:
            self.failed_tasks += 1
            
        # 更新吞吐量统计
        self._update_throughput_stats()
    
    def get_current_progress(self) -> Progress:
        """获取当前进度信息"""
        completed_ratio = self.completed_tasks / self.total_tasks if self.total_tasks > 0 else 0
        
        return Progress(
            total_tasks=self.total_tasks,
            completed_tasks=self.completed_tasks,
            failed_tasks=self.failed_tasks,
            pending_tasks=self.total_tasks - self.completed_tasks - self.failed_tasks,
            completion_ratio=completed_ratio,
            eta=self._calculate_eta(),
            average_processing_time=self._get_average_processing_time(),
            current_throughput=self._get_current_throughput()
        )
    
    def _calculate_eta(self) -> Optional[datetime]:
        """计算预计完成时间"""
        if not self.processing_times or self.completed_tasks == 0:
            return None
        
        remaining_tasks = self.total_tasks - self.completed_tasks - self.failed_tasks
        if remaining_tasks <= 0:
            return datetime.now()
        
        avg_time = statistics.mean(self.processing_times)
        eta_seconds = remaining_tasks * avg_time
        
        return datetime.now() + timedelta(seconds=eta_seconds)
```

#### 4.2 Rich UI集成
```python
class RichProgressDisplay:
    """Rich库集成的进度显示"""
    
    def __init__(self, progress_monitor: ProgressMonitor):
        self.progress_monitor = progress_monitor
        self.console = Console()
        self.progress_table = None
        self.live_display = None
    
    async def start_display(self) -> None:
        """启动实时进度显示"""
        with Live(self._create_progress_layout(), console=self.console, refresh_per_second=2) as live:
            self.live_display = live
            
            # 订阅进度更新
            self.progress_monitor.subscribe(self._update_display)
            
            # 保持显示直到完成
            while not self._is_complete():
                await asyncio.sleep(0.5)
    
    def _create_progress_layout(self) -> Layout:
        """创建进度显示布局"""
        layout = Layout()
        
        layout.split_column(
            Layout(self._create_summary_panel(), name="summary"),
            Layout(self._create_progress_bar(), name="progress"),
            Layout(self._create_status_table(), name="status")
        )
        
        return layout
    
    def _create_summary_panel(self) -> Panel:
        """创建摘要面板"""
        progress = self.progress_monitor.get_current_progress()
        
        summary_text = f"""
        Total Tasks: {progress.total_tasks}
        Completed: {progress.completed_tasks} ({progress.completion_ratio:.1%})
        Failed: {progress.failed_tasks}
        Remaining: {progress.pending_tasks}
        
        ETA: {progress.eta.strftime('%H:%M:%S') if progress.eta else 'Calculating...'}
        Avg Time/Task: {progress.average_processing_time:.1f}s
        Current Throughput: {progress.current_throughput:.2f} tasks/min
        """
        
        return Panel(summary_text, title="Batch Processing Status")
```

### 5. CheckpointManager (检查点管理)

#### 5.1 检查点策略
```python
class CheckpointManager:
    """智能检查点管理"""
    
    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查点策略配置
        self.auto_save_interval = 300  # 5分钟
        self.auto_save_task_count = 10  # 每10个任务
        self.max_checkpoints = 10       # 最多保留10个检查点
        
        self._last_save_time = time.time()
        self._last_save_task_count = 0
    
    async def save_checkpoint(self, batch_state: BatchState) -> str:
        """保存检查点"""
        checkpoint_id = f"{batch_state.batch_id}_{int(time.time())}"
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        checkpoint_data = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'batch_state': batch_state.to_dict(),
            'task_states': await self._collect_task_states(batch_state),
            'metadata': {
                'python_version': sys.version,
                'gs_videoreport_version': get_version(),
                'config_hash': self._calculate_config_hash(batch_state.config)
            }
        }
        
        # 原子写入
        temp_file = checkpoint_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        
        temp_file.rename(checkpoint_file)
        
        # 清理旧检查点
        await self._cleanup_old_checkpoints(batch_state.batch_id)
        
        return checkpoint_id
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[BatchState]:
        """加载检查点"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            # 版本兼容性检查
            if not self._is_compatible_version(checkpoint_data.get('version')):
                logger.warning(f"Checkpoint version incompatible: {checkpoint_data.get('version')}")
                return None
            
            # 恢复批量状态
            batch_state = BatchState.from_dict(checkpoint_data['batch_state'])
            
            # 恢复任务状态
            await self._restore_task_states(checkpoint_data['task_states'])
            
            return batch_state
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None
    
    def should_save_checkpoint(self, current_task_count: int) -> bool:
        """判断是否应该保存检查点"""
        now = time.time()
        
        # 基于时间的触发
        if now - self._last_save_time >= self.auto_save_interval:
            return True
        
        # 基于任务数量的触发
        if current_task_count - self._last_save_task_count >= self.auto_save_task_count:
            return True
        
        return False
```

## 算法设计

### 1. 动态并发调整算法
```python
class AdaptiveController:
    """自适应并发控制算法"""
    
    def __init__(self, initial_workers: int = 4):
        self.current_workers = initial_workers
        self.min_workers = 2
        self.max_workers = 8
        
        # 性能历史
        self.performance_history = deque(maxlen=20)
        self.adjustment_cooldown = 60  # 60秒调整间隔
        self.last_adjustment = 0
    
    def suggest_worker_adjustment(self, metrics: PerformanceMetrics) -> int:
        """建议工作线程数调整"""
        if time.time() - self.last_adjustment < self.adjustment_cooldown:
            return self.current_workers
        
        self.performance_history.append(metrics)
        
        if len(self.performance_history) < 5:
            return self.current_workers  # 数据不足，不调整
        
        # 分析性能趋势
        recent_throughput = [m.throughput for m in list(self.performance_history)[-5:]]
        
        if self._is_performance_declining(recent_throughput):
            # 性能下降，减少并发
            new_workers = max(self.min_workers, self.current_workers - 1)
        elif self._can_increase_concurrency(metrics):
            # 可以增加并发
            new_workers = min(self.max_workers, self.current_workers + 1)
        else:
            new_workers = self.current_workers
        
        if new_workers != self.current_workers:
            self.last_adjustment = time.time()
            self.current_workers = new_workers
        
        return new_workers
    
    def _is_performance_declining(self, throughput_history: List[float]) -> bool:
        """判断性能是否在下降"""
        if len(throughput_history) < 3:
            return False
        
        # 简单的线性回归判断趋势
        x = list(range(len(throughput_history)))
        slope = self._calculate_slope(x, throughput_history)
        
        return slope < -0.1  # 吞吐量显著下降
    
    def _can_increase_concurrency(self, metrics: PerformanceMetrics) -> bool:
        """判断是否可以增加并发"""
        # CPU使用率不超过80%
        if metrics.cpu_usage > 0.8:
            return False
        
        # 内存使用率不超过75%
        if metrics.memory_usage > 0.75:
            return False
        
        # API错误率不超过5%
        if metrics.api_error_rate > 0.05:
            return False
        
        # 平均响应时间不超过阈值
        if metrics.avg_response_time > 300:  # 5分钟
            return False
        
        return True
```

### 2. 智能重试算法
```python
class IntelligentRetryStrategy:
    """智能重试策略"""
    
    def __init__(self):
        self.error_patterns = self._load_error_patterns()
        self.success_rates = defaultdict(lambda: 0.5)  # 初始成功率50%
    
    def should_retry(self, task: VideoTask, error: Exception) -> bool:
        """判断是否应该重试"""
        error_type = type(error).__name__
        
        # 基于错误类型的基础策略
        base_strategy = self._get_base_retry_strategy(error_type)
        if not base_strategy.should_retry(task.retry_count):
            return False
        
        # 基于历史成功率的动态调整
        success_rate = self.success_rates[error_type]
        if success_rate < 0.1 and task.retry_count > 0:
            return False  # 成功率太低，不再重试
        
        # 基于错误消息模式匹配
        if self._is_permanent_error(str(error)):
            return False
        
        return True
    
    def calculate_retry_delay(self, task: VideoTask, error: Exception) -> float:
        """计算重试延迟时间"""
        base_delay = 2 ** task.retry_count  # 指数退避
        
        # 基于错误类型调整
        error_type = type(error).__name__
        if error_type in ['APIQuotaError', 'RateLimitError']:
            base_delay *= 10  # API限制错误需要更长等待
        elif error_type in ['NetworkError', 'ConnectionError']:
            base_delay *= 2   # 网络错误适度等待
        
        # 添加随机抖动，避免同时重试
        jitter = random.uniform(0.5, 1.5)
        
        return base_delay * jitter
    
    def update_success_rate(self, error_type: str, success: bool) -> None:
        """更新错误类型的历史成功率"""
        current_rate = self.success_rates[error_type]
        # 使用指数移动平均更新
        alpha = 0.1
        new_rate = current_rate * (1 - alpha) + (1.0 if success else 0.0) * alpha
        self.success_rates[error_type] = new_rate
```

## 数据结构定义

### 1. 配置数据结构
```python
@dataclass
class BatchOptions:
    """批量处理选项配置"""
    parallel: int = 4                    # 并发数
    timeout: Optional[int] = None        # 超时时间(秒)
    checkpoint_dir: str = "./checkpoints"  # 检查点目录
    checkpoint_interval: int = 300       # 检查点间隔(秒)
    retry_failed: bool = True           # 是否重试失败任务
    max_retries: int = 3                # 最大重试次数
    dry_run: bool = False               # 是否干运行
    skip_existing: bool = False         # 是否跳过已存在文件
    output_pattern: str = "{title}_{timestamp}.md"  # 输出文件名模式
    progress_file: Optional[str] = None  # 进度文件路径
    webhook_url: Optional[str] = None    # 完成通知Webhook
    cost_limit: Optional[float] = None   # 成本限制

@dataclass
class APILimits:
    """API限制配置"""
    max_concurrent: int = 5              # 最大并发请求数
    requests_per_minute: int = 60        # 每分钟请求数
    requests_per_day: int = 1000         # 每日请求数
    max_file_size_mb: int = 2048         # 最大文件大小
    timeout_seconds: int = 300           # 请求超时时间
```

### 2. 结果数据结构
```python
@dataclass
class TaskResult:
    """单个任务处理结果"""
    success: bool
    task_id: str
    output_path: Optional[str] = None
    processing_time: float = 0
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BatchResult:
    """批量处理最终结果"""
    batch_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    total_processing_time: float
    start_time: datetime
    end_time: datetime
    output_directory: str
    task_results: List[TaskResult]
    summary_report: str
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks
    
    @property
    def average_processing_time(self) -> float:
        """计算平均处理时间"""
        if self.completed_tasks == 0:
            return 0.0
        total_time = sum(r.processing_time for r in self.task_results if r.success)
        return total_time / self.completed_tasks
```

## 性能优化策略

### 1. 内存优化
```python
class MemoryOptimizer:
    """内存使用优化器"""
    
    def __init__(self, max_memory_mb: int = 2048):
        self.max_memory_mb = max_memory_mb
        self.current_memory_mb = 0
        self.memory_monitor = MemoryMonitor()
    
    async def optimize_batch_size(self, available_tasks: int) -> int:
        """根据内存限制优化批处理大小"""
        # 估算单任务内存使用
        estimated_memory_per_task = self._estimate_memory_per_task()
        
        # 计算最大并发任务数
        max_concurrent = int(self.max_memory_mb / estimated_memory_per_task)
        
        # 考虑系统保留内存
        safe_concurrent = max(1, int(max_concurrent * 0.8))
        
        return min(available_tasks, safe_concurrent)
    
    def _estimate_memory_per_task(self) -> float:
        """估算单任务内存使用量"""
        # 基于历史数据和文件大小估算
        base_memory = 100  # MB，基础内存使用
        
        # 根据处理类型调整
        processing_overhead = 50  # MB，处理过程额外内存
        
        return base_memory + processing_overhead

class MemoryMonitor:
    """内存使用监控"""
    
    def __init__(self):
        self.peak_usage = 0
        self.usage_history = deque(maxlen=100)
    
    def get_current_usage(self) -> float:
        """获取当前内存使用量(MB)"""
        process = psutil.Process()
        memory_info = process.memory_info()
        usage_mb = memory_info.rss / 1024 / 1024
        
        self.usage_history.append(usage_mb)
        self.peak_usage = max(self.peak_usage, usage_mb)
        
        return usage_mb
    
    def get_memory_pressure(self) -> float:
        """获取内存压力指标(0-1)"""
        if not self.usage_history:
            return 0.0
        
        current = self.usage_history[-1]
        recent_avg = sum(list(self.usage_history)[-10:]) / min(10, len(self.usage_history))
        
        # 基于增长率计算压力
        if recent_avg == 0:
            return 0.0
        
        growth_rate = (current - recent_avg) / recent_avg
        pressure = min(1.0, max(0.0, growth_rate * 10))
        
        return pressure
```

### 2. I/O优化
```python
class IOOptimizer:
    """I/O操作优化器"""
    
    def __init__(self):
        self.file_cache = LRUCache(maxsize=100)
        self.read_buffer_size = 64 * 1024  # 64KB
        self.write_buffer_size = 64 * 1024  # 64KB
    
    async def optimized_file_read(self, file_path: str) -> bytes:
        """优化的文件读取"""
        # 检查缓存
        if file_path in self.file_cache:
            return self.file_cache[file_path]
        
        # 异步读取
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
        
        # 缓存小文件
        if len(content) < 10 * 1024 * 1024:  # < 10MB
            self.file_cache[file_path] = content
        
        return content
    
    async def batch_file_operations(self, operations: List[FileOperation]) -> List[FileResult]:
        """批量文件操作"""
        # 按操作类型分组
        read_ops = [op for op in operations if op.type == 'read']
        write_ops = [op for op in operations if op.type == 'write']
        
        # 并发执行同类操作
        results = []
        
        if read_ops:
            read_results = await asyncio.gather(*[
                self.optimized_file_read(op.path) for op in read_ops
            ])
            results.extend(read_results)
        
        if write_ops:
            write_results = await asyncio.gather(*[
                self.optimized_file_write(op.path, op.content) for op in write_ops
            ])
            results.extend(write_results)
        
        return results
```

---

*文档版本: v1.0*  
*创建日期: 2025-08-18*  
*负责人: 架构师@qa.mdc*  
*状态: 技术设计完成*
