"""
Enhanced Batch Processor v0.2.0
Professional-grade batch processing with state management, worker pools, and intelligent retry.
"""
import os
import signal
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import threading

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .state_manager import (
    StateManager, BatchState, TaskRecord, TaskStatus, BatchStatus
)
from .worker_pool import WorkerPool
from .dedicated_worker_pool import DedicatedWorkerPool
from .retry_manager import RetryManager, RetryBudget
from ..config import Config
from ..template_manager import TemplateManager
from ..security.api_key_manager import api_key_manager

console = Console()

class EnhancedBatchProcessor:
    """
    增强型批量处理器 v0.2.0
    
    特性：
    - 专业级状态管理和断点续传
    - 智能并发控制和工作池管理  
    - 基于错误类型的智能重试策略
    - API速率限制和配额管理
    - 实时进度监控和统计
    - 安全的API密钥管理
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.template_manager = TemplateManager(config.data)
        
        # 核心组件初始化
        self.state_manager = StateManager()
        self.retry_manager = RetryManager()
        self.worker_pool: Optional[WorkerPool] = None
        
        # 当前批次状态
        self.current_batch: Optional[BatchState] = None
        self.shutdown_requested = False
        
        # 注册信号处理器以支持优雅关闭
        self._setup_signal_handlers()
        
        # 安全检查
        self._perform_security_check()
    
    def _setup_signal_handlers(self):
        """设置信号处理器支持优雅中断"""
        self._signal_received = False  # 防止重复处理信号
        
        def signal_handler(signum, frame):
            # 防止重复处理信号
            if self._signal_received:
                console.print(f"\n[red]🚨 强制退出...[/red]")
                import os
                os._exit(1)  # 强制退出
                return
                
            self._signal_received = True
            console.print(f"\n[yellow]⚠️  收到中断信号 ({signum})，正在安全关闭...[/yellow]")
            self.shutdown_requested = True
            
            # 立即停止工作池
            if self.worker_pool:
                self.worker_pool.pause()
                console.print("[yellow]⏸️  工作池已暂停，正在清理资源...[/yellow]")
                try:
                    self.worker_pool.shutdown(wait=False)  # 不等待，立即关闭
                except:
                    pass
            
            # 保存当前批次状态
            if self.current_batch:
                try:
                    self.current_batch.pause_batch()
                    self.state_manager.save_state(self.current_batch)
                    console.print("[green]💾 批次状态已保存，可使用resume命令继续[/green]")
                except:
                    pass
            
            console.print("[blue]🔧 安全退出完成[/blue]")
            import sys
            sys.exit(0)  # 优雅退出
        
        # 注册SIGINT (Ctrl+C) 和 SIGTERM 信号
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _perform_security_check(self):
        """执行安全检查"""
        try:
            # 验证API密钥
            api_key = api_key_manager.get_api_key(self.config.data)
            masked_key = api_key_manager.get_masked_api_key(api_key)
            console.print(f"[green]🔐 API密钥验证成功: {masked_key}[/green]")
            
        except Exception as e:
            console.print(f"[red]❌ API密钥验证失败: {e}[/red]")
            raise
    
    def create_new_batch(self, 
                        input_dir: str,
                        template_name: str = "chinese_transcript",
                        output_dir: Optional[str] = None,
                        batch_id: Optional[str] = None,
                        **kwargs) -> str:
        """
        创建新的批量处理任务
        
        Args:
            input_dir: 输入视频目录
            template_name: 处理模板名称
            output_dir: 输出目录
            batch_id: 自定义批次ID（可选）
            **kwargs: 其他配置参数
            
        Returns:
            str: 批次ID
        """
        
        # 生成批次ID
        if not batch_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_id = f"batch_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        console.print(f"[cyan]📋 创建新批次: {batch_id}[/cyan]")
        
        # 扫描视频文件
        video_files = self._scan_video_files(input_dir)
        if not video_files:
            raise ValueError(f"在目录 {input_dir} 中未找到支持的视频文件")
        
        console.print(f"[cyan]📹 发现 {len(video_files)} 个视频文件[/cyan]")
        
        # 创建批次状态
        self.current_batch = BatchState(
            batch_id=batch_id,
            input_dir=input_dir,
            template_name=template_name,
            output_dir=output_dir
        )
        
        # 应用配置参数
        batch_config = self.config.get('batch_processing', {})
        self.current_batch.max_workers = batch_config.get('parallel_workers', 2)
        self.current_batch.max_retries = batch_config.get('max_retries', 3)
        self.current_batch.skip_existing = kwargs.get('skip_existing', False)
        
        # 创建任务记录
        for video_file in video_files:
            task_id = f"{batch_id}_{video_file.stem}_{uuid.uuid4().hex[:6]}"
            
            # 生成输出路径
            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = video_file.parent
            
            output_filename = f"{video_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M')}_lesson_plan.md"
            expected_output = str(output_path / output_filename)
            
            # 创建任务记录
            task = TaskRecord(
                task_id=task_id,
                video_path=str(video_file),
                template_name=template_name,
                output_path=expected_output
            )
            
            # 计算文件哈希以支持完整性检查
            task.calculate_file_hash()
            task.max_retries = self.current_batch.max_retries
            
            # 检查是否跳过已存在文件
            if self.current_batch.skip_existing and Path(expected_output).exists():
                task.complete_skipped("输出文件已存在")
                console.print(f"[yellow]⏭️  跳过已存在: {video_file.name}[/yellow]")
            
            self.current_batch.add_task(task)
        
        # 保存初始状态
        if not self.state_manager.save_state(self.current_batch):
            raise RuntimeError("无法保存批次状态")
        
        console.print(f"[blue]📋 批次创建成功: {batch_id}[/blue]")
        return batch_id
    
    def resume_batch(self, batch_id: str) -> bool:
        """
        从断点恢复批量处理
        
        Args:
            batch_id: 要恢复的批次ID
            
        Returns:
            bool: 是否成功加载批次
        """
        console.print(f"[cyan]🔄 恢复批次: {batch_id}[/cyan]")
        
        # 加载批次状态
        self.current_batch = self.state_manager.load_state(batch_id)
        if not self.current_batch:
            console.print(f"[red]❌ 无法加载批次状态: {batch_id}[/red]")
            return False
        
        # 验证批次状态
        stats = self.current_batch.get_statistics()
        console.print(f"[cyan]📊 批次状态: {stats['completed']}/{stats['total']} 已完成[/cyan]")
        
        if self.current_batch.status == BatchStatus.COMPLETED:
            console.print("[blue]📋 批次已完成[/blue]")
            return True
        
        console.print(f"[blue]📋 批次恢复成功: {batch_id}[/blue]")
        return True
    
    def process_batch(self, 
                     batch_id: Optional[str] = None,
                     **kwargs) -> Dict[str, Any]:
        """
        执行批量处理
        
        Args:
            batch_id: 批次ID（如果为None，处理当前批次）
            **kwargs: 处理参数
            
        Returns:
            Dict: 处理结果
        """
        
        # 确定要处理的批次
        if batch_id and batch_id != (self.current_batch.batch_id if self.current_batch else None):
            if not self.resume_batch(batch_id):
                return {"success": False, "error": f"无法加载批次 {batch_id}"}
        
        if not self.current_batch:
            return {"success": False, "error": "没有活跃的批次"}
        
        # 检查批次状态
        if self.current_batch.status == BatchStatus.COMPLETED:
            stats = self.current_batch.get_statistics()
            return {"success": True, "message": "批次已完成", "statistics": stats}
        
        console.print(f"[bold green]🚀 开始处理批次: {self.current_batch.batch_id}[/bold green]")
        
        try:
            # 🎯 创建专用工作池 - 每个API密钥负责独立的视频任务
            self.worker_pool = DedicatedWorkerPool(
                config=self.config.data,
                template_manager=self.template_manager,
                state_manager=self.state_manager
            )
            
            # 显示处理前统计
            stats = self.current_batch.get_statistics()
            self._display_batch_summary(stats)
            
            # 启动专用Worker池
            if not self.worker_pool.start():
                raise RuntimeError("无法启动专用Worker池")
            
            # 获取待处理任务
            pending_tasks = [task for task in self.current_batch.tasks.values() 
                           if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]]
            
            if pending_tasks:
                console.print(f"[cyan]📋 使用专用Worker分配: {len(pending_tasks)}个任务，避免重复执行[/cyan]")
                
                # 添加任务到专用Worker队列
                self.worker_pool.add_tasks(pending_tasks)
                
                # 等待所有任务完成
                self.worker_pool.wait_for_completion()
            
            # 模拟result格式以保持兼容性
            result = {"success": True, "worker_stats": {}}
            
            # 获取最终统计
            final_stats = self.current_batch.get_statistics()
            retry_stats = self.retry_manager.get_retry_statistics()
            
            # 显示处理结果
            self._display_completion_summary(final_stats, retry_stats)
            
            return {
                "success": True,
                "batch_id": self.current_batch.batch_id,
                "statistics": final_stats,
                "retry_statistics": retry_stats,
                "worker_statistics": result.get("worker_stats", {})
            }
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  处理被用户中断[/yellow]")
            if self.current_batch:
                self.current_batch.pause_batch()
                self.state_manager.save_state(self.current_batch)
            return {"success": False, "error": "用户中断", "resumable": True}
            
        except Exception as e:
            console.print(f"[red]❌ 批量处理失败: {e}[/red]")
            if self.current_batch:
                self.current_batch.status = BatchStatus.FAILED
                self.state_manager.save_state(self.current_batch)
            return {"success": False, "error": str(e)}
            
        finally:
            # 清理资源
            if self.worker_pool:
                self.worker_pool.shutdown(wait=True)
                self.worker_pool = None
    
    def list_batches(self) -> List[Dict[str, Any]]:
        """列出所有批次"""
        return self.state_manager.list_batch_states()
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """获取批次状态"""
        batch_state = self.state_manager.load_state(batch_id)
        if not batch_state:
            return None
        
        stats = batch_state.get_statistics()
        return {
            "batch_id": batch_id,
            "status": batch_state.status.value,
            "created_at": batch_state.created_at,
            "input_dir": batch_state.input_dir,
            "template_name": batch_state.template_name,
            "statistics": stats
        }
    
    def cancel_batch(self, batch_id: str) -> bool:
        """取消批次处理"""
        if self.current_batch and self.current_batch.batch_id == batch_id:
            self.shutdown_requested = True
            if self.worker_pool:
                self.worker_pool.pause()
            
            self.current_batch.cancel_batch()
            self.state_manager.save_state(self.current_batch)
            console.print(f"[yellow]🛑 批次已取消: {batch_id}[/yellow]")
            return True
        
        # 取消非活跃批次
        batch_state = self.state_manager.load_state(batch_id)
        if batch_state:
            batch_state.cancel_batch()
            self.state_manager.save_state(batch_state)
            console.print(f"[yellow]🛑 批次已取消: {batch_id}[/yellow]")
            return True
        
        return False
    
    def cleanup_old_states(self, days: int = 7) -> int:
        """清理旧的状态文件"""
        cleaned_count = self.state_manager.cleanup_old_states(days)
        if cleaned_count > 0:
            console.print(f"[green]🧹 清理了 {cleaned_count} 个旧状态文件[/green]")
        return cleaned_count
    
    def _scan_video_files(self, input_dir: str) -> List[Path]:
        """扫描视频文件"""
        video_config = self.config.get('video_processing', {})
        supported_formats = video_config.get('supported_formats', 
                                           ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v'])
        
        input_path = Path(input_dir)
        if not input_path.exists():
            raise ValueError(f"目录不存在: {input_dir}")
        
        video_files = []
        for ext in supported_formats:
            if not ext.startswith('.'):
                ext = '.' + ext
            video_files.extend(input_path.glob(f"*{ext}"))
            video_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        return sorted(set(video_files))  # 去重并排序
    
    def _display_batch_summary(self, stats: Dict[str, Any]):
        """显示批次摘要"""
        table = Table(title="批次处理摘要")
        table.add_column("项目", style="cyan")
        table.add_column("数量", style="green")
        
        table.add_row("总视频数", str(stats['total']))
        table.add_row("待处理", str(stats['pending']))
        table.add_row("已完成", str(stats['completed']))
        table.add_row("已跳过", str(stats['skipped']))
        table.add_row("失败重试", str(len(self.current_batch.get_failed_retryable_tasks())))
        
        console.print(table)
    
    def _display_completion_summary(self, 
                                  final_stats: Dict[str, Any], 
                                  retry_stats: Dict[str, Any]):
        """显示完成摘要"""
        
        # 主要统计表格
        main_table = Table(title="📊 批次处理完成")
        main_table.add_column("项目", style="cyan")
        main_table.add_column("数量", style="green")
        main_table.add_column("百分比", style="yellow")
        
        total = final_stats['total']
        main_table.add_row("总数", str(total), "100%")
        main_table.add_row("成功", str(final_stats['success']), 
                          f"{final_stats['success']/total*100:.1f}%" if total > 0 else "0%")
        main_table.add_row("失败", str(final_stats['failed']), 
                          f"{final_stats['failed']/total*100:.1f}%" if total > 0 else "0%")
        main_table.add_row("跳过", str(final_stats['skipped']), 
                          f"{final_stats['skipped']/total*100:.1f}%" if total > 0 else "0%")
        
        console.print(main_table)
        
        # 重试统计
        if retry_stats['total_retries'] > 0:
            retry_table = Table(title="🔄 重试统计")
            retry_table.add_column("项目", style="cyan")
            retry_table.add_column("数量", style="green")
            
            retry_table.add_row("总重试次数", str(retry_stats['total_retries']))
            retry_table.add_row("成功重试", str(retry_stats['successful_retries']))
            retry_table.add_row("重试成功率", f"{retry_stats['success_rate_percentage']:.1f}%")
            
            console.print(retry_table)
            
            # 按错误类型分类
            if retry_stats['retry_by_category']:
                category_info = "重试错误分类: " + ", ".join([
                    f"{cat}: {count}" for cat, count in retry_stats['retry_by_category'].items()
                ])
                console.print(f"[dim]{category_info}[/dim]")
        
        # 状态文件信息
        state_file = self.state_manager._get_state_file_path(self.current_batch.batch_id)
        console.print(f"\n[dim]💾 状态文件: {state_file}[/dim]")
        
        # 成功/失败状态面板
        if final_stats['failed'] == 0:
            console.print(Panel("[bold green]🎉 所有视频处理成功！[/bold green]", 
                              style="green"))
        elif final_stats['success'] > 0:
            console.print(Panel(f"[bold yellow]⚠️  部分成功：{final_stats['success']} 成功，{final_stats['failed']} 失败[/bold yellow]", 
                              style="yellow"))
        else:
            console.print(Panel("[bold red]❌ 批次处理失败[/bold red]", 
                              style="red"))
