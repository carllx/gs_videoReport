"""
Progress Formatter for CLI

提供进度显示功能：
- 视频处理进度
- 批量任务进度
- 文件上传进度
- 实时状态更新
"""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text


class ProgressFormatter:
    """进度格式化器
    
    提供各种进度显示和状态更新功能。
    """
    
    @staticmethod
    def display_video_result(console: Console, result: Dict[str, Any]) -> None:
        """
        显示视频处理结果
        
        Args:
            console: Rich控制台
            result: 处理结果字典
        """
        if not result.get('success', False):
            console.print("[red]❌ 视频处理失败[/red]")
            return
        
        analysis_result = result.get('analysis_result')
        if not analysis_result:
            console.print("[yellow]⚠️  处理结果不完整[/yellow]")
            return
        
        # 成功消息
        console.print("[bold green]🎉 视频处理完成！[/bold green]")
        
        # 基本统计信息
        metadata = analysis_result.metadata
        stats_panel = ProgressFormatter._create_stats_panel(metadata)
        console.print(stats_panel)
        
        # 输出文件信息
        output_path = result.get('output_path')
        if output_path:
            console.print(f"[cyan]📄 输出文件: {output_path}[/cyan]")
        
        # 内容预览
        content = analysis_result.content
        if content:
            preview_length = 200
            if len(content) > preview_length:
                preview = content[:preview_length] + "..."
            else:
                preview = content
            
            preview_panel = Panel(
                preview,
                title="📋 内容预览",
                border_style="blue"
            )
            console.print(preview_panel)
    
    @staticmethod
    def display_batch_progress(console: Console, 
                             batch_id: str, 
                             completed: int, 
                             total: int, 
                             current_file: Optional[str] = None) -> None:
        """
        显示批量处理进度
        
        Args:
            console: Rich控制台
            batch_id: 批次ID
            completed: 已完成数量
            total: 总数量
            current_file: 当前处理的文件
        """
        progress_percentage = (completed / total * 100) if total > 0 else 0
        
        # 进度信息
        progress_text = f"[cyan]📦 批次: {batch_id}[/cyan]\n"
        progress_text += f"[green]进度: {completed}/{total} ({progress_percentage:.1f}%)[/green]"
        
        if current_file:
            # 截断长文件名
            if len(current_file) > 50:
                display_file = "..." + current_file[-47:]
            else:
                display_file = current_file
            progress_text += f"\n[blue]当前: {display_file}[/blue]"
        
        # 创建进度面板
        progress_panel = Panel(
            progress_text,
            title="🚀 批量处理进度",
            border_style="cyan"
        )
        
        console.print(progress_panel)
    
    @staticmethod
    def display_upload_progress(console: Console, 
                              filename: str, 
                              uploaded_bytes: int, 
                              total_bytes: int) -> None:
        """
        显示文件上传进度
        
        Args:
            console: Rich控制台
            filename: 文件名
            uploaded_bytes: 已上传字节数
            total_bytes: 总字节数
        """
        progress_percentage = (uploaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
        
        # 格式化文件大小
        def format_bytes(bytes_count):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_count < 1024.0:
                    return f"{bytes_count:.1f} {unit}"
                bytes_count /= 1024.0
            return f"{bytes_count:.1f} TB"
        
        uploaded_str = format_bytes(uploaded_bytes)
        total_str = format_bytes(total_bytes)
        
        # 截断长文件名
        if len(filename) > 40:
            display_filename = "..." + filename[-37:]
        else:
            display_filename = filename
        
        upload_text = f"[cyan]📤 上传: {display_filename}[/cyan]\n"
        upload_text += f"[green]{uploaded_str} / {total_str} ({progress_percentage:.1f}%)[/green]"
        
        upload_panel = Panel(
            upload_text,
            title="📤 文件上传",
            border_style="blue"
        )
        
        console.print(upload_panel)
    
    @staticmethod
    def display_processing_status(console: Console, 
                                status: str, 
                                details: Optional[Dict[str, Any]] = None) -> None:
        """
        显示处理状态
        
        Args:
            console: Rich控制台
            status: 状态描述
            details: 可选的详细信息
        """
        # 状态图标映射
        status_icons = {
            'initializing': '🔧',
            'uploading': '📤',
            'processing': '🧠',
            'analyzing': '🔍',
            'formatting': '📝',
            'saving': '💾',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '⏹️'
        }
        
        # 状态颜色映射
        status_colors = {
            'initializing': 'yellow',
            'uploading': 'blue',
            'processing': 'cyan',
            'analyzing': 'magenta',
            'formatting': 'green',
            'saving': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'dim'
        }
        
        # 获取图标和颜色
        icon = status_icons.get(status.lower(), '🔄')
        color = status_colors.get(status.lower(), 'white')
        
        # 状态文本
        status_text = f"[{color}]{icon} {status}[/{color}]"
        
        # 添加详细信息
        if details:
            for key, value in details.items():
                status_text += f"\n[dim]{key}: {value}[/dim]"
        
        # 显示状态面板
        status_panel = Panel(
            status_text,
            title="🔄 处理状态",
            border_style=color
        )
        
        console.print(status_panel)
    
    @staticmethod
    def create_progress_bar(console: Console, description: str = "处理中...") -> tuple[Progress, TaskID]:
        """
        创建进度条
        
        Args:
            console: Rich控制台
            description: 进度描述
            
        Returns:
            tuple[Progress, TaskID]: 进度条对象和任务ID
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        )
        
        task_id = progress.add_task(description, total=100)
        return progress, task_id
    
    @staticmethod
    def update_progress_bar(progress: Progress, 
                          task_id: TaskID, 
                          completed: int, 
                          total: int, 
                          description: Optional[str] = None) -> None:
        """
        更新进度条
        
        Args:
            progress: 进度条对象
            task_id: 任务ID
            completed: 已完成数量
            total: 总数量
            description: 可选的新描述
        """
        progress_value = (completed / total * 100) if total > 0 else 0
        
        update_kwargs = {'completed': progress_value}
        if description:
            update_kwargs['description'] = description
        
        progress.update(task_id, **update_kwargs)
    
    @staticmethod
    def display_summary(console: Console, 
                       title: str, 
                       stats: Dict[str, Any], 
                       success: bool = True) -> None:
        """
        显示处理摘要
        
        Args:
            console: Rich控制台
            title: 摘要标题
            stats: 统计信息
            success: 是否成功
        """
        # 摘要标题
        if success:
            title_text = f"[bold green]✅ {title}[/bold green]"
        else:
            title_text = f"[bold red]❌ {title}[/bold red]"
        
        console.print(title_text)
        
        # 统计信息
        if stats:
            stats_text = ""
            for key, value in stats.items():
                # 格式化键名
                display_key = key.replace('_', ' ').title()
                stats_text += f"[cyan]• {display_key}:[/cyan] {value}\n"
            
            stats_panel = Panel(
                stats_text.rstrip(),
                title="📊 统计信息",
                border_style="green" if success else "red"
            )
            console.print(stats_panel)
    
    @staticmethod
    def _create_stats_panel(metadata: Dict[str, Any]) -> Panel:
        """创建统计信息面板"""
        stats_text = ""
        
        # 基本信息
        if 'model' in metadata:
            stats_text += f"[cyan]• 使用模型:[/cyan] {metadata['model']}\n"
        
        if 'template' in metadata:
            stats_text += f"[cyan]• 模板:[/cyan] {metadata['template']}\n"
        
        if 'processing_time_seconds' in metadata:
            processing_time = metadata['processing_time_seconds']
            stats_text += f"[cyan]• 处理时间:[/cyan] {processing_time:.1f}秒\n"
        
        if 'estimated_cost_usd' in metadata:
            cost = metadata['estimated_cost_usd']
            stats_text += f"[cyan]• 估算成本:[/cyan] ${cost:.4f} USD\n"
        
        # 文件信息
        if 'file_size_bytes' in metadata:
            file_size_mb = metadata['file_size_bytes'] / (1024**2)
            stats_text += f"[cyan]• 文件大小:[/cyan] {file_size_mb:.1f} MB\n"
        
        # Token信息
        if 'input_tokens_estimated' in metadata:
            input_tokens = metadata['input_tokens_estimated']
            stats_text += f"[cyan]• 输入Tokens:[/cyan] {input_tokens:,}\n"
        
        if 'output_tokens_estimated' in metadata:
            output_tokens = metadata['output_tokens_estimated']
            stats_text += f"[cyan]• 输出Tokens:[/cyan] {output_tokens:,}\n"
        
        # 回退信息
        if metadata.get('fallback_used', False):
            stats_text += f"[yellow]• ⚠️  使用了模型回退[/yellow]\n"
        
        return Panel(
            stats_text.rstrip(),
            title="📊 处理统计",
            border_style="green"
        )
