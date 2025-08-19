"""
专用Worker池 - 每个API密钥绑定一个专门的Worker线程
确保任务独立分配，避免冲突和重复执行
"""
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
import queue

from rich.console import Console

from .state_manager import TaskRecord, StateManager
from ..services.simple_gemini_service import SimpleGeminiService
from ..template_manager import TemplateManager
from ..config import get_dynamic_parallel_workers

console = Console()


class DedicatedWorker:
    """专用Worker - 每个Worker绑定一个API密钥"""
    
    def __init__(self, 
                 worker_id: str,
                 api_key: str,
                 config: Dict[str, Any],
                 template_manager: TemplateManager,
                 task_queue: queue.Queue,
                 results_queue: queue.Queue,
                 shutdown_event: threading.Event):
        self.worker_id = worker_id
        self.api_key = api_key
        self.config = config
        self.template_manager = template_manager
        self.task_queue = task_queue
        self.results_queue = results_queue
        self.shutdown_event = shutdown_event
        
        # 初始化专用的Gemini服务（单密钥模式）
        self.gemini_service = self._init_dedicated_gemini_service()
        
        # Worker统计
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        console.print(f"[blue]🔧 Worker {worker_id} 初始化完成，绑定API密钥: {api_key[:8]}...{api_key[-4:]}[/blue]")
    
    def _init_dedicated_gemini_service(self) -> SimpleGeminiService:
        """为Worker初始化专用的Gemini服务"""
        # 为这个Worker创建专用配置
        dedicated_config = self.config.copy()
        dedicated_config.setdefault('google_api', {})
        dedicated_config['google_api']['api_key'] = self.api_key
        
        # 使用单密钥模式（不传递api_keys参数）
        return SimpleGeminiService(dedicated_config)
    
    def run(self):
        """Worker主循环 - 处理任务队列中的视频"""
        console.print(f"[blue]🚀 Worker {self.worker_id} 开始运行[/blue]")
        
        while not self.shutdown_event.is_set():
            try:
                # 从任务队列获取任务（超时1秒，避免无限等待）
                try:
                    task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue  # 队列为空，继续检查shutdown事件
                
                # 处理任务
                try:
                    result = self._process_task(task)
                    self.results_queue.put(result)
                    
                    if result.status == 'completed':
                        self.processed_count += 1
                    elif result.status == 'failed':
                        self.failed_count += 1
                    elif result.status == 'skipped':
                        self.skipped_count += 1
                        
                except Exception as e:
                    console.print(f"[red]❌ Worker {self.worker_id} 处理任务失败: {e}[/red]")
                    task.complete_failed(str(e))
                    self.results_queue.put(task)
                    self.failed_count += 1
                finally:
                    self.task_queue.task_done()
                    
            except Exception as e:
                console.print(f"[red]❌ Worker {self.worker_id} 循环异常: {e}[/red]")
                time.sleep(1)  # 避免快速重试
        
        console.print(f"[yellow]🔚 Worker {self.worker_id} 已停止[/yellow]")
    
    def _process_task(self, task: TaskRecord) -> TaskRecord:
        """处理单个视频任务"""
        start_time = time.time()
        
        try:
            task.start_processing(self.worker_id)
            console.print(f"[cyan]🎬 Worker {self.worker_id} 开始处理: {Path(task.video_path).name}[/cyan]")
            
            # 断点续传检查
            output_file_exists, output_path = self._check_output_file_exists(task)
            if output_file_exists:
                console.print(f"[yellow]⏭️ Worker {self.worker_id} - 输出文件已存在，跳过: {Path(output_path).name}[/yellow]")
                task.complete_success(output_path, 0)
                return task
            
            # 文件完整性检查
            if not task.validate_file_integrity():
                raise ValueError(f"文件已被修改或损坏: {task.video_path}")
            
            # 获取配置
            from ..config import get_default_model
            preferred_model = get_default_model(self.config)
            
            # 准备模板参数
            template_params = self._prepare_template_params(task.video_path)
            
            # 🎯 核心处理：使用专用的Gemini服务
            result = self.gemini_service.process_video_end_to_end_enhanced(
                video_path=task.video_path,
                template_manager=self.template_manager,
                template_name=task.template_name,
                preferred_model=preferred_model,
                enable_fallback=True,
                cleanup_file=True,
                **template_params
            )
            
            processing_time = time.time() - start_time
            task.complete_success(result.output_path, processing_time)
            
            console.print(f"[green]✅ Worker {self.worker_id} 完成: {Path(task.video_path).name} ({processing_time:.1f}s)[/green]")
            return task
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            task.complete_failed(error_msg)
            console.print(f"[red]❌ Worker {self.worker_id} 处理失败: {Path(task.video_path).name} - {error_msg}[/red]")
            return task
    
    def _check_output_file_exists(self, task: TaskRecord) -> tuple[bool, Optional[str]]:
        """🎯 检查输出文件是否已存在（断点续传功能）"""
        from ..config import get_default_output_directory, get_default_template
        
        try:
            # 🎯 强制使用统一的模板子文件夹结构，忽略预设的output_path
            video_path = Path(task.video_path)
            output_dir = get_default_output_directory(self.config)
            
            # 🎯 模板子文件夹结构: test_output/chinese_transcript/
            template_name = task.template_name or get_default_template(self.config)
            template_subdir = Path(output_dir) / template_name
            template_subdir.mkdir(parents=True, exist_ok=True)
            
            # 🎯 简单逻辑：提取纯文件名，添加.md扩展名
            # 001 - name.mp4 -> 001 - name.md  
            base_name = Path(video_path.stem).stem  # 连续两次去扩展名处理.mp4.mp4情况
            output_name = f"{base_name}.md"
            output_path = str(template_subdir / output_name)
            
            output_file = Path(output_path)
            
            # 🎯 调试信息
            console.print(f"[dim]🔍 断点续传检查: {template_name}/{output_name}[/dim]")
            
            if output_file.exists() and output_file.stat().st_size > 0:
                console.print(f"[yellow]⏭️ Worker {self.worker_id} - 输出文件已存在，启用断点续传: {output_path}[/yellow]")
                return True, output_path
            else:
                console.print(f"[dim]📝 Worker {self.worker_id} - 需要处理: {output_name}[/dim]")
                return False, output_path
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Worker {self.worker_id} - 断点续传检查失败: {e}[/yellow]")
            # 发生错误时，继续处理
            return False, None
    
    def _prepare_template_params(self, video_path: str) -> Dict[str, Any]:
        """准备模板参数"""
        video_file = Path(video_path)
        
        return {
            'video_title': video_file.stem,
            'video_duration': 'analyzing...',
            'subject_area': 'general',
            'detail_level': 'comprehensive',
            'current_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'language_preference': 'simplified_chinese',
            'max_length': '500',
            'focus_areas': 'key concepts and learning objectives'
        }


class DedicatedWorkerPool:
    """专用Worker池 - 每个API密钥对应一个专门的Worker"""
    
    def __init__(self, 
                 config: Dict[str, Any],
                 template_manager: TemplateManager,
                 state_manager: StateManager):
        self.config = config
        self.template_manager = template_manager
        self.state_manager = state_manager
        
        # 获取API密钥列表
        self.api_keys = self._get_api_keys()
        self.num_workers = len(self.api_keys)
        
        console.print(f"[blue]🔧 初始化专用Worker池: {self.num_workers}个API密钥，{self.num_workers}个专用Worker[/blue]")
        
        # 任务队列和结果队列
        self.task_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        
        # Worker线程列表
        self.workers: List[DedicatedWorker] = []
        self.worker_threads: List[threading.Thread] = []
        
        # 统计信息
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.skipped_tasks = 0
        
        # 正在处理的任务（防止重复）
        self.processing_tasks: Set[str] = set()
        self.processing_lock = threading.Lock()
        
        # 初始化Workers
        self._init_workers()
    
    def _get_api_keys(self) -> List[str]:
        """获取API密钥列表"""
        multi_key_config = self.config.get('multi_api_keys', {})
        
        if multi_key_config.get('enabled', False):
            api_keys = multi_key_config.get('api_keys', [])
            if api_keys:
                console.print(f"[blue]🔧 检测到多密钥配置: {len(api_keys)}个API密钥[/blue]")
                return api_keys
        
        # 回退到单密钥模式
        from ..security.api_key_manager import api_key_manager
        single_key = api_key_manager.get_api_key(self.config)
        console.print(f"[yellow]⚠️ 回退到单密钥模式[/yellow]")
        return [single_key]
    
    def _init_workers(self):
        """初始化所有Workers"""
        for i, api_key in enumerate(self.api_keys):
            worker_id = f"dedicated-worker-{i+1}"
            
            worker = DedicatedWorker(
                worker_id=worker_id,
                api_key=api_key,
                config=self.config,
                template_manager=self.template_manager,
                task_queue=self.task_queue,
                results_queue=self.results_queue,
                shutdown_event=self.shutdown_event
            )
            
            self.workers.append(worker)
    
    def start(self) -> bool:
        """启动所有Worker线程"""
        try:
            for worker in self.workers:
                thread = threading.Thread(target=worker.run, name=worker.worker_id)
                thread.daemon = True
                thread.start()
                self.worker_threads.append(thread)
            
            console.print(f"[blue]🚀 专用Worker池启动成功: {len(self.worker_threads)}个Worker线程[/blue]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Worker池启动失败: {e}[/red]")
            return False
    
    def add_tasks(self, tasks: List[TaskRecord]) -> bool:
        """添加任务到队列"""
        try:
            added_count = 0
            for task in tasks:
                # 检查任务是否已在处理中
                with self.processing_lock:
                    if task.video_path in self.processing_tasks:
                        console.print(f"[yellow]⚠️ 任务已在处理中，跳过: {Path(task.video_path).name}[/yellow]")
                        continue
                    
                    self.processing_tasks.add(task.video_path)
                
                self.task_queue.put(task)
                self.total_tasks += 1
                added_count += 1
                console.print(f"[dim]➕ 添加任务到队列: {Path(task.video_path).name}[/dim]")
            
            console.print(f"[blue]📋 成功添加 {added_count}/{len(tasks)} 个任务到队列，队列大小: {self.task_queue.qsize()}[/blue]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ 添加任务失败: {e}[/red]")
            return False
    
    def wait_for_completion(self):
        """等待所有任务完成"""
        console.print(f"[blue]⏳ 等待所有任务完成... 队列大小: {self.task_queue.qsize()}[/blue]")
        
        try:
            # 等待任务队列清空
            console.print(f"[dim]📊 开始等待队列处理，当前队列大小: {self.task_queue.qsize()}[/dim]")
            self.task_queue.join()
            console.print("[dim]📊 任务队列已清空[/dim]")
            
            # 收集结果
            results_collected = 0
            while not self.results_queue.empty():
                try:
                    result = self.results_queue.get_nowait()
                    results_collected += 1
                    
                    # 从处理中任务列表移除
                    with self.processing_lock:
                        self.processing_tasks.discard(result.video_path)
                    
                    # 更新统计
                    if result.status == TaskStatus.SUCCESS:
                        self.completed_tasks += 1
                    elif result.status == TaskStatus.FAILED:
                        self.failed_tasks += 1
                    elif result.status == TaskStatus.SKIPPED:
                        self.skipped_tasks += 1
                    
                    # 更新状态管理器
                    self.state_manager.update_task_status(result)
                    
                except queue.Empty:
                    break
            
            console.print(f"[blue]📋 所有任务处理完成，收集了 {results_collected} 个结果[/blue]")
            
        except Exception as e:
            console.print(f"[red]❌ 等待任务完成时发生错误: {e}[/red]")
    
    def shutdown(self, wait: bool = True):
        """关闭Worker池"""
        try:
            console.print("[yellow]🛑 正在关闭专用Worker池...[/yellow]")
            
            # 设置关闭事件
            self.shutdown_event.set()
            
            if wait:
                # 等待所有Worker线程结束
                for thread in self.worker_threads:
                    thread.join(timeout=5.0)
            
            console.print("[blue]🔧 专用Worker池已关闭[/blue]")
            
            # 显示统计信息
            self._print_statistics()
            
        except Exception as e:
            console.print(f"[red]❌ 关闭Worker池失败: {e}[/red]")
    
    def _print_statistics(self):
        """显示处理统计信息"""
        console.print("\n[bold cyan]📊 专用Worker池统计[/bold cyan]")
        console.print(f"  总任务: {self.total_tasks}")
        console.print(f"  完成: {self.completed_tasks}")
        console.print(f"  失败: {self.failed_tasks}")
        console.print(f"  跳过: {self.skipped_tasks}")
        
        # Worker级别统计
        for worker in self.workers:
            console.print(f"  {worker.worker_id}: 处理{worker.processed_count}, 失败{worker.failed_count}, 跳过{worker.skipped_count}")
