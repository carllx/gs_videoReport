"""
简化的工作池 - 专注核心功能，避免过度开发
核心功能：2个并发worker、断点续传、6分钟超时、模板参数处理
"""
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, Future, as_completed, TimeoutError
from pathlib import Path

from rich.console import Console

from .state_manager import TaskRecord, BatchState, StateManager
from ..services.simple_gemini_service import SimpleGeminiService
from ..template_manager import TemplateManager
from ..security.api_key_manager import api_key_manager
from ..config import get_dynamic_parallel_workers

console = Console()

class WorkerPool:
    """
    🎯 简化的工作池 - 专注核心功能
    - 固定2个并发worker（避免网络拥塞和Token浪费）
    - 断点续传（检查输出文件是否已存在）
    - 6分钟超时控制（超时跳过有问题的视频）
    - 统一模板参数处理
    """
    
    def __init__(self, 
                 config: Dict[str, Any],
                 template_manager: TemplateManager,
                 state_manager: StateManager):
        self.config = config
        self.template_manager = template_manager
        self.state_manager = state_manager
        
        # 🎯 动态配置：基于API密钥数量决定并行worker数
        self.max_workers = get_dynamic_parallel_workers(config)
        console.print(f"[cyan]🔧 配置并行worker数: {self.max_workers}[/cyan]")
        
        # 工作池状态
        self.executor: Optional[ThreadPoolExecutor] = None
        self.active_futures: Dict[Future, str] = {}
        self.shutdown_event = threading.Event()
        
        # 简单统计
        self.total_processed = 0
        self.total_failed = 0
        self.total_skipped = 0
        
        # 线程安全
        self._lock = threading.Lock()
        
        # 初始化Gemini服务
        self._init_gemini_service()
    
    def _init_gemini_service(self):
        """初始化Gemini服务"""
        try:
            # 检查是否启用多密钥模式
            multi_key_config = self.config.get('multi_api_keys', {})
            
            if multi_key_config.get('enabled', False):
                # 多密钥模式：传递API密钥列表给SimpleGeminiService
                api_keys = multi_key_config.get('api_keys', [])
                if api_keys:
                    safe_config = self.config.copy()
                    self.gemini_service = SimpleGeminiService(safe_config, api_keys=api_keys)
                    console.print(f"[green]✅ Gemini服务初始化成功 (多密钥模式, {len(api_keys)}个API密钥)[/green]")
                else:
                    # 多密钥启用但没有密钥列表，回退到单密钥
                    api_key = api_key_manager.get_api_key(self.config)
                    safe_config = self.config.copy()
                    safe_config.setdefault('google_api', {})
                    safe_config['google_api']['api_key'] = api_key
                    self.gemini_service = SimpleGeminiService(safe_config)
                    masked_key = api_key_manager.get_masked_api_key(api_key)
                    console.print(f"[yellow]⚠️ 多密钥模式启用但无密钥列表，使用单密钥: {masked_key}[/yellow]")
            else:
                # 单密钥模式：使用传统方式
                api_key = api_key_manager.get_api_key(self.config)
                safe_config = self.config.copy()
                safe_config.setdefault('google_api', {})
                safe_config['google_api']['api_key'] = api_key
                self.gemini_service = SimpleGeminiService(safe_config)
                masked_key = api_key_manager.get_masked_api_key(api_key)
                console.print(f"[green]✅ Gemini服务初始化成功 (单密钥模式, API密钥: {masked_key})[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ Gemini服务初始化失败: {e}[/red]")
            raise
    
    def start(self) -> bool:
        """启动工作池"""
        try:
            if self.executor is not None:
                console.print("[yellow]⚠️  工作池已经在运行[/yellow]")
                return False
            
            self.executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="VideoProcessor"
            )
            
            self.shutdown_event.clear()
            console.print(f"[green]🚀 工作池启动成功，{self.max_workers}个并发worker[/green]")
            return True
                
        except Exception as e:
            console.print(f"[red]❌ 工作池启动失败: {e}[/red]")
            return False
    
    def shutdown(self, wait: bool = True) -> bool:
        """关闭工作池"""
        try:
            if self.executor is None:
                return True
            
            console.print("[yellow]🛑 正在关闭工作池...[/yellow]")
            self.shutdown_event.set()
            
            if not wait:
                # 强制取消所有未完成的任务
                console.print("[yellow]⚡ 强制取消所有正在运行的任务...[/yellow]")
                for future in list(self.active_futures):
                    try:
                        future.cancel()
                    except:
                        pass
                self.active_futures.clear()
            
            self.executor.shutdown(wait=wait)
            self.executor = None
            
            console.print("[green]✅ 工作池已关闭[/green]")
            return True
                
        except Exception as e:
            console.print(f"[red]❌ 工作池关闭失败: {e}[/red]")
            return False
    
    def _prepare_template_params(self, video_path: str) -> Dict[str, Any]:
        """🎯 准备模板参数"""
        video_file = Path(video_path)
        
        return {
            'video_title': video_file.stem,
            'video_duration': 'analyzing...',
            'subject_area': 'general',
            'detail_level': 'comprehensive',
            'current_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'language_preference': 'simplified_chinese',  # chinese_transcript模板必需
            'max_length': '500',
            'focus_areas': 'key concepts and learning objectives'
        }
    
    def _check_output_file_exists(self, task: TaskRecord) -> tuple[bool, str]:
        """🎯 检查输出文件是否已存在（断点续传功能）"""
        from ..config import get_default_output_directory, get_default_template
        
        try:
            # 🎯 强制使用统一的模板子文件夹结构，忽略预设的output_path
            video_path = Path(task.video_path)
            output_dir = get_default_output_directory(self.config)
            
            # 🎯 模板子文件夹结构
            template_name = task.template_name or get_default_template(self.config)
            template_subdir = Path(output_dir) / template_name
            template_subdir.mkdir(parents=True, exist_ok=True)
            
            # 🎯 简单逻辑：提取纯文件名，添加.md扩展名
            # 001 - name.mp4.mp4 -> 001 - name.md  
            base_name = Path(video_path.stem).stem  # 连续两次去扩展名
            output_name = f"{base_name}.md"
            output_path = str(template_subdir / output_name)
            
            output_file = Path(output_path)
            
            # 🎯 调试信息
            console.print(f"[dim]🔍 断点续传检查: {output_file}[/dim]")
            console.print(f"[dim]   文件存在: {output_file.exists()}[/dim]")
            if output_file.exists():
                console.print(f"[dim]   文件大小: {output_file.stat().st_size} 字节[/dim]")
            
            if output_file.exists() and output_file.stat().st_size > 0:
                console.print(f"[green]✅ 输出文件已存在，启用断点续传: {output_path}[/green]")
                return True, output_path
            else:
                console.print(f"[dim]💾 输出文件不存在，需要处理: {output_path}[/dim]")
                return False, output_path
                
        except Exception as e:
            console.print(f"[yellow]⚠️  检查输出文件时出错: {e}[/yellow]")
            return False, ""
    
    def _process_video_with_timeout(self, task: TaskRecord, template_params: Dict[str, Any], preferred_model: str, timeout: int) -> Any:
        """🎯 带超时控制的视频处理（使用线程安全的方法）"""
        import threading
        from concurrent.futures import Future, ThreadPoolExecutor
        
        try:
            # 使用单独的线程池执行视频处理，支持超时
            with ThreadPoolExecutor(max_workers=1) as timeout_executor:
                future = timeout_executor.submit(
                    self.gemini_service.process_video_end_to_end_enhanced,
                    video_path=task.video_path,
                    template_manager=self.template_manager,
                    template_name=task.template_name,
                    preferred_model=preferred_model,
                    enable_fallback=True,
                    cleanup_file=True,
                    **template_params
                )
                
                # 等待结果，支持超时
                try:
                    result = future.result(timeout=timeout)
                    return result
                except TimeoutError:
                    console.print(f"[yellow]⏰ 处理超时（{timeout}秒），跳过视频: {task.video_path}[/yellow]")
                    future.cancel()  # 尝试取消任务
                    raise TimeoutError(f"视频处理超时 ({timeout}秒)")
                
        except TimeoutError as e:
            raise e
        except Exception as e:
            console.print(f"[red]❌ 视频处理失败: {e}[/red]")
            raise e
    
    def _process_task(self, task: TaskRecord) -> TaskRecord:
        """处理单个任务"""
        worker_id = f"worker-{threading.current_thread().ident}"
        start_time = time.time()
        
        try:
            task.start_processing(worker_id)
            console.print(f"[cyan]🎬  开始处理: {task.video_path}[/cyan]")
            
            # 🎯 断点续传检查
            output_file_exists, output_path = self._check_output_file_exists(task)
            if output_file_exists:
                console.print(f"[green]✅  输出文件已存在，跳过处理: {output_path}[/green]")
                task.complete_success(output_path, 0)
                with self._lock:
                    self.total_skipped += 1
                return task
            
            # 检查文件完整性
            if not task.validate_file_integrity():
                raise ValueError(f"文件已被修改或损坏: {task.video_path}")
            
            # 🎯 统一配置获取
            from ..config import get_default_model
            preferred_model = get_default_model(self.config)
            
            # 🎯 准备模板参数
            template_params = self._prepare_template_params(task.video_path)
            
            # 🎯 超时控制：6分钟
            processing_timeout = 360  # 6分钟
            console.print(f"[dim]⏱️  设置处理超时: {processing_timeout}秒[/dim]")
            
            # 🎯 处理视频（带超时）
            result = self._process_video_with_timeout(
                task=task,
                template_params=template_params,
                preferred_model=preferred_model,
                timeout=processing_timeout
            )
            
            processing_time = time.time() - start_time
            
            # 🎯 强制使用与断点续传检查相同的路径逻辑
            _, correct_output_path = self._check_output_file_exists(task)
            task.output_path = correct_output_path
            
            # 🎯 保存文件到正确路径（与断点续传检查路径一致）
            if hasattr(result, 'content'):
                output_path = Path(task.output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.content)
                console.print(f"[green]💾 文件已保存: {output_path}[/green]")
            
            task.complete_success(task.output_path, processing_time)
            
            console.print(f"[green]✅  完成处理: {task.video_path} ({processing_time:.1f}s)[/green]")
            
            with self._lock:
                self.total_processed += 1
            
            return task
            
        except (TimeoutError, Exception) as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            task.complete_failed(error_msg)
            console.print(f"[red]❌  处理失败: {task.video_path} - {error_msg}[/red]")
            
            with self._lock:
                self.total_failed += 1
            
            return task
    
    def process_batch(self, batch_state: BatchState) -> Dict[str, Any]:
        """🎯 处理整个批次 - 简化版本"""
        if not self.start():
            return {"success": False, "error": "无法启动工作池"}
        
        try:
            # 获取待处理任务
            pending_tasks = batch_state.get_pending_tasks()
            retryable_tasks = batch_state.get_failed_retryable_tasks()
            
            for task in retryable_tasks:
                task.reset_for_retry()
            
            all_tasks = pending_tasks + retryable_tasks
            
            if not all_tasks:
                console.print("[green]✅ 没有待处理的任务[/green]")
                return {"success": True, "processed": 0}
            
            console.print(f"[cyan]📋 准备处理 {len(all_tasks)} 个任务[/cyan]")
            batch_state.start_batch()
            
            # 提交所有任务
            future_to_task = {}
            for task in all_tasks:
                if self.executor:
                    future = self.executor.submit(self._process_task, task)
                    future_to_task[future] = task
                    with self._lock:
                        self.active_futures[future] = task.task_id
            
            # 等待任务完成
            completed_count = 0
            total_tasks = len(all_tasks)
            
            for future in as_completed(future_to_task.keys()):
                if self.shutdown_event.is_set():
                    console.print("[yellow]🛑 检测到中断信号，正在保存状态...[/yellow]")
                    break
                
                completed_task = future.result()
                completed_count += 1
                percentage = (completed_count / total_tasks) * 100
                
                # 简单进度显示
                console.print(f"⠋ 处理进度: {completed_count}/{total_tasks} ({percentage:.0f}%)")
                
                # 保存状态
                self.state_manager.save_state(batch_state)
            
            # 完成批次
            batch_state.complete_batch()
            self.state_manager.save_state(batch_state)
            
            return {
                "success": True,
                "processed": self.total_processed,
                "failed": self.total_failed,
                "skipped": self.total_skipped,
                "total": total_tasks
            }
            
        finally:
            self.shutdown(wait=True)
