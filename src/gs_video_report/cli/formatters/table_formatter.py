"""
Table Formatter for CLI

提供美观的表格显示功能：
- 批量任务列表显示
- 模型信息表格
- 性能统计表格
- 配置信息展示
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text


class TableFormatter:
    """表格格式化器
    
    提供各种数据的表格化显示功能。
    """
    
    @staticmethod
    def display_batch_list(console: Console, batches: List[Dict[str, Any]]) -> None:
        """
        显示批量任务列表
        
        Args:
            console: Rich控制台
            batches: 批量任务列表
        """
        if not batches:
            console.print("[yellow]📋 当前没有批量任务[/yellow]")
            return
        
        table = Table(title="📋 批量任务列表")
        table.add_column("批次ID", style="cyan", no_wrap=True)
        table.add_column("状态", style="green")
        table.add_column("进度", style="blue")
        table.add_column("输入目录", style="dim")
        table.add_column("创建时间", style="dim")
        table.add_column("完成/总数", style="yellow")
        
        for batch in batches:
            # 状态图标和颜色
            status = batch.get('status', 'unknown')
            status_display = TableFormatter._get_status_display(status)
            
            # 进度百分比
            total_tasks = batch.get('total_tasks', 0)
            completed_tasks = batch.get('completed_tasks', 0)
            progress = f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
            
            # 时间格式化
            created_time = batch.get('created_time', '')
            if created_time:
                try:
                    dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    time_display = dt.strftime('%m-%d %H:%M')
                except:
                    time_display = created_time[:16]
            else:
                time_display = "未知"
            
            # 输入目录（缩短显示）
            input_dir = batch.get('input_dir', '')
            if len(input_dir) > 30:
                input_dir = "..." + input_dir[-27:]
            
            table.add_row(
                batch.get('batch_id', ''),
                status_display,
                progress,
                input_dir,
                time_display,
                f"{completed_tasks}/{total_tasks}"
            )
        
        console.print(table)
    
    @staticmethod
    def display_batch_status(console: Console, batch_info: Dict[str, Any]) -> None:
        """
        显示批量任务详细状态
        
        Args:
            console: Rich控制台
            batch_info: 批量任务信息
        """
        batch_id = batch_info.get('batch_id', 'Unknown')
        console.print(f"[bold cyan]📊 批次状态: {batch_id}[/bold cyan]")
        
        # 基本信息表格
        info_table = Table(title="基本信息")
        info_table.add_column("属性", style="cyan")
        info_table.add_column("值", style="green")
        
        info_table.add_row("批次ID", batch_info.get('batch_id', ''))
        info_table.add_row("状态", TableFormatter._get_status_display(batch_info.get('status', '')))
        info_table.add_row("输入目录", batch_info.get('input_dir', ''))
        info_table.add_row("输出目录", batch_info.get('output_dir', ''))
        info_table.add_row("模板", batch_info.get('template_name', ''))
        
        # 时间信息
        created_time = batch_info.get('created_time', '')
        if created_time:
            try:
                dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                time_display = dt.strftime('%Y-%m-%d %H:%M:%S')
                info_table.add_row("创建时间", time_display)
            except:
                info_table.add_row("创建时间", created_time)
        
        console.print(info_table)
        
        # 进度信息表格
        progress_table = Table(title="进度统计")
        progress_table.add_column("指标", style="cyan")
        progress_table.add_column("数量", style="green")
        progress_table.add_column("百分比", style="blue")
        
        total_tasks = batch_info.get('total_tasks', 0)
        completed_tasks = batch_info.get('completed_tasks', 0)
        failed_tasks = batch_info.get('failed_tasks', 0)
        pending_tasks = total_tasks - completed_tasks - failed_tasks
        
        if total_tasks > 0:
            progress_table.add_row(
                "总任务数", 
                str(total_tasks), 
                "100%"
            )
            progress_table.add_row(
                "已完成", 
                str(completed_tasks), 
                f"{(completed_tasks/total_tasks*100):.1f}%"
            )
            progress_table.add_row(
                "失败", 
                str(failed_tasks), 
                f"{(failed_tasks/total_tasks*100):.1f}%"
            )
            progress_table.add_row(
                "待处理", 
                str(pending_tasks), 
                f"{(pending_tasks/total_tasks*100):.1f}%"
            )
        
        console.print(progress_table)
        
        # 如果有任务详情，显示任务表格
        tasks = batch_info.get('tasks', [])
        if tasks:
            TableFormatter._display_task_details(console, tasks)
    
    @staticmethod
    def display_model_capabilities(console: Console, models: Dict[str, Dict[str, Any]]) -> None:
        """
        显示模型能力对比表格
        
        Args:
            console: Rich控制台
            models: 模型信息字典
        """
        if not models:
            console.print("[yellow]📋 没有可用的模型信息[/yellow]")
            return
        
        table = Table(title="🤖 模型能力对比")
        table.add_column("模型", style="cyan")
        table.add_column("视频处理", style="green")
        table.add_column("最大文件大小", style="yellow")
        table.add_column("最大时长", style="blue")
        table.add_column("支持格式", style="dim")
        
        for model_name, capabilities in models.items():
            video_support = "✅" if capabilities.get('video_processing', False) else "❌"
            max_size = f"{capabilities.get('max_file_size_mb', 0)}MB"
            max_duration = f"{capabilities.get('max_video_duration_minutes', 0)}min"
            
            formats = capabilities.get('supported_formats', [])
            formats_str = ", ".join(formats[:3])  # 只显示前3个格式
            if len(formats) > 3:
                formats_str += "..."
            
            table.add_row(
                model_name,
                video_support,
                max_size,
                max_duration,
                formats_str
            )
        
        console.print(table)
    
    @staticmethod
    def display_performance_stats(console: Console, stats: Dict[str, Any]) -> None:
        """
        显示性能统计表格
        
        Args:
            console: Rich控制台
            stats: 性能统计数据
        """
        # API统计表格
        api_stats = stats.get('api_statistics', {})
        
        api_table = Table(title="📈 API使用统计")
        api_table.add_column("指标", style="cyan")
        api_table.add_column("值", style="green")
        
        api_table.add_row("总请求数", str(api_stats.get('total_requests', 0)))
        api_table.add_row("总成本 (USD)", f"${api_stats.get('total_cost_usd', 0):.4f}")
        api_table.add_row("平均响应时间", f"{api_stats.get('avg_response_time', 0):.2f}s")
        
        console.print(api_table)
        
        # 模型性能表格
        model_stats = stats.get('model_performance', {})
        if model_stats:
            model_table = Table(title="🤖 模型性能详情")
            model_table.add_column("模型", style="cyan")
            model_table.add_column("成功率", style="green")
            model_table.add_column("性能等级", style="yellow")
            model_table.add_column("请求数", style="blue")
            model_table.add_column("成本 (USD)", style="red")
            
            for model_name, metrics in model_stats.items():
                if metrics.get('total_requests', 0) > 0:
                    success_rate = f"{metrics.get('success_rate', 0):.1%}"
                    performance_level = metrics.get('performance_level', 'unknown')
                    total_requests = str(metrics.get('total_requests', 0))
                    estimated_cost = f"${metrics.get('estimated_cost_usd', 0):.4f}"
                    
                    model_table.add_row(
                        model_name,
                        success_rate,
                        performance_level,
                        total_requests,
                        estimated_cost
                    )
            
            console.print(model_table)
    
    @staticmethod
    def display_template_list(console: Console, templates: List[Dict[str, Any]]) -> None:
        """
        显示模板列表
        
        Args:
            console: Rich控制台
            templates: 模板列表
        """
        if not templates:
            console.print("[yellow]📋 没有可用的模板[/yellow]")
            return
        
        table = Table(title="📝 可用模板")
        table.add_column("模板名称", style="cyan")
        table.add_column("描述", style="green")
        table.add_column("版本", style="yellow")
        table.add_column("参数", style="dim")
        
        for template in templates:
            name = template.get('name', '')
            description = template.get('description', '')
            version = template.get('version', '')
            parameters = template.get('parameters', [])
            
            # 截断长描述
            if len(description) > 50:
                description = description[:47] + "..."
            
            # 参数列表
            params_str = ", ".join(parameters[:3]) if parameters else "无"
            if len(parameters) > 3:
                params_str += "..."
            
            table.add_row(name, description, version, params_str)
        
        console.print(table)
    
    @staticmethod
    def _get_status_display(status: str) -> Text:
        """获取状态的显示文本和颜色"""
        status_map = {
            'pending': ('⏳ 待处理', 'yellow'),
            'running': ('🔄 运行中', 'blue'),
            'completed': ('✅ 已完成', 'green'),
            'failed': ('❌ 失败', 'red'),
            'cancelled': ('⏹️ 已取消', 'dim'),
            'paused': ('⏸️ 已暂停', 'yellow')
        }
        
        text, color = status_map.get(status.lower(), (f'❓ {status}', 'dim'))
        return Text(text, style=color)
    
    @staticmethod
    def _display_task_details(console: Console, tasks: List[Dict[str, Any]]) -> None:
        """显示任务详情表格"""
        # 只显示前10个任务，避免表格过长
        display_tasks = tasks[:10]
        
        task_table = Table(title=f"📋 任务详情 (显示前{len(display_tasks)}个)")
        task_table.add_column("文件名", style="cyan")
        task_table.add_column("状态", style="green")
        task_table.add_column("进度", style="blue")
        task_table.add_column("错误", style="red")
        
        for task in display_tasks:
            filename = task.get('video_path', '').split('/')[-1]  # 只显示文件名
            if len(filename) > 25:
                filename = filename[:22] + "..."
            
            status = task.get('status', 'unknown')
            status_display = TableFormatter._get_status_display(status)
            
            progress = task.get('progress', 0)
            progress_str = f"{progress}%" if isinstance(progress, (int, float)) else str(progress)
            
            error = task.get('error_message', '')
            if len(error) > 30:
                error = error[:27] + "..."
            
            task_table.add_row(filename, status_display, progress_str, error)
        
        console.print(task_table)
        
        if len(tasks) > 10:
            console.print(f"[dim]... 还有 {len(tasks) - 10} 个任务未显示[/dim]")
