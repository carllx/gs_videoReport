# 批量处理功能 - 实现指南

## 概述

本文档为开发团队提供批量处理功能的详细实现指南，包括开发任务分解、代码结构设计、实现优先级和开发计划。

## 实现路线图

### Phase 1: 基础架构 (Week 1-2)
- [ ] 核心数据结构定义
- [ ] 基础CLI命令框架
- [ ] 任务队列系统
- [ ] 状态持久化机制

### Phase 2: 核心功能 (Week 3-4)
- [ ] 批量处理引擎
- [ ] 并发工作线程池
- [ ] 进度监控系统
- [ ] 错误处理机制

### Phase 3: 优化和扩展 (Week 5-6)
- [ ] 性能优化实现
- [ ] 检查点和恢复
- [ ] 高级配置选项
- [ ] 通知和报告系统

### Phase 4: 测试和文档 (Week 7-8)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试
- [ ] 用户文档

## 代码结构设计

### 目录结构
```
src/gs_video_report/
├── batch/                          # 批量处理模块
│   ├── __init__.py
│   ├── processor.py                # BatchProcessor主类
│   ├── task_queue.py              # 任务队列管理
│   ├── worker_pool.py             # 工作线程池
│   ├── progress_monitor.py        # 进度监控
│   ├── checkpoint_manager.py      # 检查点管理
│   ├── api_limiter.py             # API限流控制
│   ├── data_models.py             # 数据模型定义
│   └── utils.py                   # 工具函数
├── batch_cli.py                   # 批量处理CLI扩展
├── cli.py                         # 现有CLI (需要扩展)
└── ...                           # 现有模块
```

### 核心模块设计

#### 1. 数据模型模块 (data_models.py)

```python
# src/gs_video_report/batch/data_models.py
"""
批量处理核心数据模型定义
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
import json

class InputType(Enum):
    """输入类型枚举"""
    FILE = "file"
    URL = "url"
    YOUTUBE = "youtube"

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class BatchStatus(Enum):
    """批量状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class VideoInput:
    """视频输入数据结构"""
    source_type: InputType
    source_path: str
    template: str
    output_path: str
    estimated_duration: Optional[int] = None
    file_size: Optional[int] = None
    priority: int = 50
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'source_type': self.source_type.value,
            'source_path': self.source_path,
            'template': self.template,
            'output_path': self.output_path,
            'estimated_duration': self.estimated_duration,
            'file_size': self.file_size,
            'priority': self.priority,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoInput':
        """从字典反序列化"""
        return cls(
            source_type=InputType(data['source_type']),
            source_path=data['source_path'],
            template=data['template'],
            output_path=data['output_path'],
            estimated_duration=data.get('estimated_duration'),
            file_size=data.get('file_size'),
            priority=data.get('priority', 50),
            metadata=data.get('metadata', {})
        )

@dataclass
class VideoTask:
    """视频处理任务"""
    task_id: str
    batch_id: str
    input: VideoInput
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    worker_id: Optional[str] = None
    error_message: Optional[str] = None
    result: Optional['TaskResult'] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'task_id': self.task_id,
            'batch_id': self.batch_id,
            'input': self.input.to_dict(),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'worker_id': self.worker_id,
            'error_message': self.error_message,
            'result': self.result.to_dict() if self.result else None
        }

# 实现任务: 完成所有数据模型类的定义
# 预估时间: 1天
# 依赖: 无
```

#### 2. 任务队列模块 (task_queue.py)

```python
# src/gs_video_report/batch/task_queue.py
"""
任务队列管理模块
"""
import asyncio
import sqlite3
import json
from collections import deque
from typing import Optional, List, Dict, Any
from .data_models import VideoTask, TaskStatus

class TaskQueue:
    """高性能任务队列"""
    
    def __init__(self, db_path: str = "./batch_tasks.db"):
        self.db_path = db_path
        self._memory_queue = asyncio.PriorityQueue()
        self._tasks_map = {}  # task_id -> VideoTask
        self._status_counters = {status: 0 for status in TaskStatus}
        self._lock = asyncio.Lock()
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_data TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    priority INTEGER DEFAULT 50,
                    worker_id TEXT,
                    error_message TEXT,
                    result_data TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_batch_status 
                ON tasks(batch_id, status);
                
                CREATE INDEX IF NOT EXISTS idx_priority 
                ON tasks(priority, created_at);
            """)
    
    async def add_tasks(self, tasks: List[VideoTask]) -> None:
        """批量添加任务"""
        async with self._lock:
            for task in tasks:
                # 添加到内存队列
                priority = self._calculate_priority(task)
                await self._memory_queue.put((priority, task.created_at, task))
                
                # 更新映射表
                self._tasks_map[task.task_id] = task
                self._status_counters[task.status] += 1
                
                # 持久化到数据库
                await self._persist_task(task)
    
    async def get_next_task(self) -> Optional[VideoTask]:
        """获取下一个待处理任务"""
        try:
            _, _, task = await asyncio.wait_for(
                self._memory_queue.get(), timeout=1.0
            )
            
            async with self._lock:
                # 更新任务状态
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                # 更新计数器
                self._status_counters[TaskStatus.PENDING] -= 1
                self._status_counters[TaskStatus.RUNNING] += 1
                
                # 持久化状态变更
                await self._persist_task(task)
                
            return task
            
        except asyncio.TimeoutError:
            return None
    
    # 实现任务: 完成队列的所有方法
    # 预估时间: 2天
    # 依赖: data_models.py
```

#### 3. 批量处理器模块 (processor.py)

```python
# src/gs_video_report/batch/processor.py
"""
批量处理核心引擎
"""
import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from .data_models import VideoInput, VideoTask, BatchStatus, BatchResult
from .task_queue import TaskQueue
from .worker_pool import WorkerPool
from .progress_monitor import ProgressMonitor
from .checkpoint_manager import CheckpointManager
from ..config import Config

logger = logging.getLogger(__name__)

class BatchProcessor:
    """批量处理核心引擎"""
    
    def __init__(self, config: Config, options: 'BatchOptions'):
        self.config = config
        self.options = options
        self.batch_id = self._generate_batch_id()
        
        # 初始化子组件
        self.task_queue = TaskQueue()
        self.worker_pool = WorkerPool(
            max_workers=options.parallel,
            config=config
        )
        self.progress_monitor = ProgressMonitor()
        self.checkpoint_manager = CheckpointManager(
            checkpoint_dir=options.checkpoint_dir
        )
        
        # 状态管理
        self.status = BatchStatus.INITIALIZING
        self._shutdown_event = asyncio.Event()
        self._pause_event = asyncio.Event()
        
    async def process_batch(self, inputs: List[VideoInput]) -> BatchResult:
        """执行批量处理主流程"""
        logger.info(f"Starting batch processing: {self.batch_id}")
        
        try:
            # Phase 1: 初始化
            await self._initialize_batch(inputs)
            
            # Phase 2: 执行处理
            await self._execute_processing()
            
            # Phase 3: 完成处理
            return await self._finalize_batch()
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            await self._handle_batch_error(e)
            raise
        finally:
            await self._cleanup_resources()
    
    async def _initialize_batch(self, inputs: List[VideoInput]) -> None:
        """初始化批量处理"""
        logger.info(f"Initializing batch with {len(inputs)} inputs")
        
        # 1. 创建任务
        tasks = [self._create_task(inp) for inp in inputs]
        
        # 2. 添加到队列
        await self.task_queue.add_tasks(tasks)
        
        # 3. 初始化进度监控
        self.progress_monitor.start_monitoring(len(tasks))
        
        # 4. 保存初始检查点
        await self.checkpoint_manager.save_initial_state(self._get_batch_state())
        
        # 5. 更新状态
        self.status = BatchStatus.RUNNING
        logger.info("Batch initialization completed")
    
    # 实现任务: 完成批量处理器的所有核心方法
    # 预估时间: 3天
    # 依赖: task_queue.py, worker_pool.py, progress_monitor.py
```

#### 4. CLI扩展模块 (batch_cli.py)

```python
# src/gs_video_report/batch_cli.py
"""
批量处理CLI命令扩展
"""
import typer
from pathlib import Path
from typing import Optional

from .batch.processor import BatchProcessor
from .batch.data_models import VideoInput, InputType
from .batch.utils import parse_input_source
from .config import load_config

# 创建批量处理子命令
batch_app = typer.Typer(name="batch", help="批量视频处理命令")

@batch_app.command()
def process(
    # 输入源参数 (互斥)
    input_dir: Optional[str] = typer.Option(None, "--input-dir", "-d", help="视频文件目录"),
    file_list: Optional[str] = typer.Option(None, "--file-list", "-f", help="文件列表路径"),
    url_list: Optional[str] = typer.Option(None, "--url-list", "-u", help="URL列表路径"),
    
    # 处理配置参数
    template: str = typer.Option("chinese_transcript", "--template", "-t", help="处理模板"),
    output: str = typer.Option("./batch_output", "--output", "-o", help="输出目录"),
    parallel: int = typer.Option(4, "--parallel", "-p", help="并发数", min=1, max=8),
    
    # 控制参数
    config: Optional[str] = typer.Option(None, "--config", "-c", help="配置文件路径"),
    progress_file: Optional[str] = typer.Option(None, "--progress-file", help="进度文件路径"),
    resume_from: Optional[str] = typer.Option(None, "--resume-from", help="检查点ID"),
    
    # 行为控制
    dry_run: bool = typer.Option(False, "--dry-run", help="预览模式"),
    skip_existing: bool = typer.Option(False, "--skip-existing", help="跳过已存在文件"),
    max_retries: int = typer.Option(3, "--max-retries", help="最大重试次数"),
    timeout: int = typer.Option(1800, "--timeout", help="任务超时时间(秒)"),
    
    # 输出控制
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="静默模式")
):
    """批量处理视频文件"""
    
    # 参数验证
    input_sources = [input_dir, file_list, url_list]
    if sum(bool(src) for src in input_sources) != 1:
        typer.echo("❌ Error: 必须指定且只能指定一个输入源", err=True)
        raise typer.Exit(1)
    
    if verbose and quiet:
        typer.echo("❌ Error: --verbose 和 --quiet 不能同时使用", err=True)
        raise typer.Exit(1)
    
    try:
        # 加载配置
        app_config = load_config(config)
        
        # 解析输入源
        input_source = input_dir or file_list or url_list
        inputs = parse_input_source(input_source, template, output)
        
        # 创建批量处理选项
        batch_options = BatchOptions(
            parallel=parallel,
            checkpoint_dir="./checkpoints",
            dry_run=dry_run,
            skip_existing=skip_existing,
            max_retries=max_retries,
            timeout=timeout,
            progress_file=progress_file,
            verbose=verbose,
            quiet=quiet
        )
        
        # 预览模式
        if dry_run:
            show_dry_run_preview(inputs, batch_options)
            return
        
        # 恢复模式
        if resume_from:
            resume_batch_processing(resume_from, batch_options)
            return
        
        # 正常批量处理
        run_batch_processing(app_config, inputs, batch_options)
        
    except Exception as e:
        typer.echo(f"❌ 批量处理失败: {e}", err=True)
        raise typer.Exit(1)

# 实现任务: 完成CLI命令的所有参数处理和调用逻辑
# 预估时间: 2天
# 依赖: processor.py, 输入解析器
```

## 开发任务分解

### 1. 基础设施任务

#### T1.1: 数据模型定义
- **文件**: `batch/data_models.py`
- **描述**: 定义所有核心数据结构
- **预估时间**: 1天
- **依赖**: 无
- **验收标准**:
  - [ ] 所有枚举类型定义完整
  - [ ] 数据类支持序列化/反序列化
  - [ ] 包含完整的类型注解
  - [ ] 通过mypy类型检查

#### T1.2: 数据库持久化
- **文件**: `batch/persistence.py`
- **描述**: 实现SQLite数据库操作
- **预估时间**: 1天
- **依赖**: T1.1
- **验收标准**:
  - [ ] 数据库表结构创建
  - [ ] CRUD操作实现
  - [ ] 事务支持
  - [ ] 索引优化

#### T1.3: 配置系统扩展
- **文件**: `config.py` (扩展)
- **描述**: 添加批量处理配置支持
- **预估时间**: 0.5天
- **依赖**: T1.1
- **验收标准**:
  - [ ] 批量处理配置段定义
  - [ ] 向后兼容性保证
  - [ ] 配置验证逻辑

### 2. 核心功能任务

#### T2.1: 任务队列系统
- **文件**: `batch/task_queue.py`
- **描述**: 实现高性能任务队列
- **预估时间**: 2天
- **依赖**: T1.1, T1.2
- **验收标准**:
  - [ ] 优先级队列实现
  - [ ] 状态持久化
  - [ ] 并发安全
  - [ ] 性能测试通过

#### T2.2: 工作线程池
- **文件**: `batch/worker_pool.py`
- **描述**: 实现并发工作线程池
- **预估时间**: 2天
- **依赖**: T2.1
- **验收标准**:
  - [ ] 动态线程管理
  - [ ] 资源控制
  - [ ] 错误隔离
  - [ ] 优雅关闭

#### T2.3: 批量处理引擎
- **文件**: `batch/processor.py`
- **描述**: 核心批量处理协调器
- **预估时间**: 3天
- **依赖**: T2.1, T2.2
- **验收标准**:
  - [ ] 完整生命周期管理
  - [ ] 暂停/恢复功能
  - [ ] 错误处理机制
  - [ ] 状态同步

#### T2.4: 进度监控系统
- **文件**: `batch/progress_monitor.py`
- **描述**: 实时进度跟踪和ETA计算
- **预估时间**: 1.5天
- **依赖**: T2.1
- **验收标准**:
  - [ ] 实时进度计算
  - [ ] ETA估算算法
  - [ ] 性能统计
  - [ ] 事件通知

### 3. CLI集成任务

#### T3.1: CLI命令扩展
- **文件**: `batch_cli.py`
- **描述**: 添加batch子命令
- **预估时间**: 2天
- **依赖**: T2.3
- **验收标准**:
  - [ ] 完整参数支持
  - [ ] 输入验证
  - [ ] 错误处理
  - [ ] 帮助信息

#### T3.2: 输入解析器
- **文件**: `batch/input_parser.py`
- **描述**: 解析各种输入源
- **预估时间**: 1.5天
- **依赖**: T1.1
- **验收标准**:
  - [ ] 目录扫描
  - [ ] 文件列表解析
  - [ ] CSV格式支持
  - [ ] URL验证

#### T3.3: 输出格式化
- **文件**: `batch/output_formatter.py`
- **描述**: 格式化批量处理输出
- **预估时间**: 1天
- **依赖**: T2.4
- **验收标准**:
  - [ ] Rich进度显示
  - [ ] 报告生成
  - [ ] 日志格式化
  - [ ] 错误信息

### 4. 高级功能任务

#### T4.1: 检查点管理
- **文件**: `batch/checkpoint_manager.py`
- **描述**: 实现断点续传功能
- **预估时间**: 2天
- **依赖**: T2.3
- **验收标准**:
  - [ ] 自动检查点保存
  - [ ] 状态恢复
  - [ ] 检查点清理
  - [ ] 完整性验证

#### T4.2: API限流器
- **文件**: `batch/api_limiter.py`
- **描述**: 智能API调用限制
- **预估时间**: 1.5天
- **依赖**: T2.2
- **验收标准**:
  - [ ] 令牌桶算法
  - [ ] 动态限制调整
  - [ ] 配额跟踪
  - [ ] 背压处理

#### T4.3: 性能优化
- **文件**: `batch/performance_optimizer.py`
- **描述**: 自动性能调优
- **预估时间**: 2天
- **依赖**: T2.3, T2.4
- **验收标准**:
  - [ ] 资源监控
  - [ ] 自适应调整
  - [ ] 性能指标
  - [ ] 调优日志

## 实现优先级

### P0 (必须实现) - MVP
1. **T1.1**: 数据模型定义
2. **T2.1**: 任务队列系统
3. **T2.2**: 工作线程池
4. **T2.3**: 批量处理引擎
5. **T3.1**: CLI命令扩展
6. **T3.2**: 输入解析器

### P1 (重要功能)
1. **T2.4**: 进度监控系统
2. **T3.3**: 输出格式化
3. **T4.1**: 检查点管理
4. **T1.2**: 数据库持久化

### P2 (增强功能)
1. **T4.2**: API限流器
2. **T4.3**: 性能优化
3. **T1.3**: 配置系统扩展

## 开发时间估算

### 总体时间分配
- **Week 1**: T1.1, T1.2, T1.3 (基础设施)
- **Week 2**: T2.1, T2.2 (队列和线程池)
- **Week 3**: T2.3, T2.4 (处理引擎和监控)
- **Week 4**: T3.1, T3.2, T3.3 (CLI集成)
- **Week 5**: T4.1, T4.2 (高级功能)
- **Week 6**: T4.3, 优化和调试
- **Week 7-8**: 测试和文档

### 里程碑定义

#### M1 - 基础架构完成 (Week 2 End)
- [ ] 数据模型和持久化就绪
- [ ] 任务队列可用
- [ ] 基础测试通过

#### M2 - 核心功能完成 (Week 4 End)
- [ ] 批量处理引擎工作
- [ ] CLI命令可用
- [ ] 基本用例测试通过

#### M3 - 功能完整 (Week 6 End)
- [ ] 所有P0和P1功能完成
- [ ] 性能测试通过
- [ ] 错误处理验证

#### M4 - 发布就绪 (Week 8 End)
- [ ] 完整测试覆盖
- [ ] 文档完整
- [ ] 性能基准达标

## 代码质量标准

### 编码规范
1. **类型注解**: 所有公共方法必须有完整类型注解
2. **文档字符串**: 所有公共类和方法必须有docstring
3. **错误处理**: 所有异常情况必须有适当处理
4. **日志记录**: 关键操作必须有日志记录

### 测试要求
1. **单元测试**: 代码覆盖率 > 80%
2. **集成测试**: 核心流程必须有集成测试
3. **性能测试**: 关键性能指标必须验证
4. **错误测试**: 错误场景必须覆盖

### 代码审查清单
- [ ] 类型检查通过 (mypy)
- [ ] 代码格式化 (black)
- [ ] Import排序 (isort)
- [ ] 安全检查 (bandit)
- [ ] 复杂度检查 (radon)

## 依赖管理

### 新增依赖
```python
# pyproject.toml 新增依赖
[tool.poetry.dependencies]
# 已有依赖...
aiofiles = "^23.1.0"        # 异步文件操作
psutil = "^5.9.0"           # 系统资源监控
msgpack = "^1.0.0"          # 高效序列化
aiosqlite = "^0.19.0"       # 异步SQLite

[tool.poetry.group.dev.dependencies]
# 已有依赖...
memory_profiler = "^0.61.0"  # 内存分析
line_profiler = "^4.1.0"     # 性能分析
```

### 向后兼容性
- 现有API保持不变
- 新功能作为可选依赖
- 配置文件向下兼容
- 模板系统保持兼容

## 部署和发布

### 版本规划
- **v0.2.0-alpha**: MVP功能就绪
- **v0.2.0-beta**: 完整功能测试版
- **v0.2.0**: 正式发布版本

### 发布检查清单
- [ ] 所有自动化测试通过
- [ ] 性能基准测试达标
- [ ] 文档更新完整
- [ ] 向后兼容性验证
- [ ] 安全检查通过

---

*文档版本: v1.0*  
*创建日期: 2025-08-18*  
*负责人: 架构师@qa.mdc*  
*状态: 实现指南完成*
