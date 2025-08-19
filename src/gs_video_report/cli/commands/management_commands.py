"""
Management Commands

批量处理管理相关的CLI命令实现：
- 列出所有批次
- 查看批次状态
- 取消批次处理
- 清理旧状态文件
"""

import sys
from typing import Any, Optional
from datetime import datetime

import typer

from .base import BaseCommand
from ..formatters.table_formatter import TableFormatter
from ..formatters.error_formatter import ErrorFormatter


class ListBatchesCommand(BaseCommand):
    """列出批次命令处理器"""
    
    def execute(self,
                config_file: Optional[str] = None,
                limit: int = 10) -> Any:
        """
        列出所有批量处理批次
        
        Args:
            config_file: 配置文件路径
            limit: 显示的批次数量限制
            
        Returns:
            Any: 批次列表
        """
        try:
            # 加载配置（创建最小配置用于列表功能）
            try:
                config = self.load_config(config_file)
            except Exception:
                from ...config import Config
                config = Config({})
            
            # 创建批量管理器
            batch_manager = self.service_factory.create_batch_manager(config, self.console)
            
            # 获取批次列表
            batches = batch_manager.list_batches()
            
            if not batches:
                self.console.print("[yellow]📝 没有找到任何批次[/yellow]")
                return []
            
            # 限制显示数量
            if limit > 0:
                batches = batches[:limit]
            
            # 使用表格格式化器显示批次列表
            TableFormatter.display_batch_list(self.console, batches)
            
            # 显示操作提示
            self.console.print(f"\n[dim]💡 使用 'gs_videoreport status <batch_id>' 查看详细信息[/dim]")
            self.console.print(f"[dim]💡 使用 'gs_videoreport resume <batch_id>' 恢复处理[/dim]")
            
            return batches
            
        except Exception as e:
            self.handle_error(e, "获取批次列表失败")
            raise typer.Exit(1)


class StatusCommand(BaseCommand):
    """查看批次状态命令处理器"""
    
    def execute(self,
                batch_id: str,
                config_file: Optional[str] = None) -> Any:
        """
        查看批次详细状态
        
        Args:
            batch_id: 批次ID
            config_file: 配置文件路径
            
        Returns:
            Any: 批次状态信息
        """
        try:
            # 加载配置
            try:
                config = self.load_config(config_file)
            except Exception:
                from ...config import Config
                config = Config({})
            
            # 创建批量管理器
            batch_manager = self.service_factory.create_batch_manager(config, self.console)
            
            # 获取批次状态
            status_info = batch_manager.get_batch_status(batch_id)
            
            if not status_info:
                ErrorFormatter.display_error(
                    self.console,
                    ValueError(f"批次不存在: {batch_id}"),
                    "批次状态查询失败"
                )
                self.console.print("[yellow]💡 使用 'gs_videoreport list-batches' 查看可用批次[/yellow]")
                raise typer.Exit(1)
            
            # 使用表格格式化器显示批次状态
            TableFormatter.display_batch_status(self.console, status_info)
            
            # 显示操作建议
            self._display_operation_suggestions(batch_id, status_info)
            
            return status_info
            
        except Exception as e:
            self.handle_error(e, "状态查询失败")
            raise typer.Exit(1)
    
    def _display_operation_suggestions(self, batch_id: str, status_info: dict) -> None:
        """显示操作建议"""
        self.console.print(f"\n[dim]💡 可用操作:[/dim]")
        
        status_value = status_info.get('status', '')
        stats = status_info.get('statistics', {})
        
        if status_value in ['paused', 'failed'] and stats.get('pending', 0) > 0:
            self.console.print(f"[dim]   • 恢复处理: gs_videoreport resume {batch_id}[/dim]")
        
        if status_value not in ['completed', 'cancelled']:
            self.console.print(f"[dim]   • 取消批次: gs_videoreport cancel {batch_id}[/dim]")
        
        self.console.print(f"[dim]   • 查看所有批次: gs_videoreport list-batches[/dim]")


class CancelCommand(BaseCommand):
    """取消批次命令处理器"""
    
    def execute(self,
                batch_id: str,
                config_file: Optional[str] = None) -> Any:
        """
        取消批量处理
        
        Args:
            batch_id: 批次ID
            config_file: 配置文件路径
            
        Returns:
            Any: 取消结果
        """
        try:
            # 加载配置
            try:
                config = self.load_config(config_file)
            except Exception:
                from ...config import Config
                config = Config({})
            
            # 创建批量管理器
            batch_manager = self.service_factory.create_batch_manager(config, self.console)
            
            # 取消批次
            success = batch_manager.cancel_batch(batch_id)
            
            if success:
                self.success_message(f"批次已取消: {batch_id}")
            else:
                ErrorFormatter.display_error(
                    self.console,
                    ValueError(f"无法取消批次: {batch_id}"),
                    "批次取消失败"
                )
                raise typer.Exit(1)
            
            return {"success": success, "batch_id": batch_id}
            
        except Exception as e:
            self.handle_error(e, "取消操作失败")
            raise typer.Exit(1)


class CleanupCommand(BaseCommand):
    """清理旧状态文件命令处理器"""
    
    def execute(self,
                days: int = 7,
                config_file: Optional[str] = None) -> Any:
        """
        清理旧的批次状态文件
        
        Args:
            days: 清理多少天前的状态文件
            config_file: 配置文件路径
            
        Returns:
            Any: 清理结果
        """
        try:
            # 加载配置
            try:
                config = self.load_config(config_file)
            except Exception:
                from ...config import Config
                config = Config({})
            
            # 创建批量管理器
            batch_manager = self.service_factory.create_batch_manager(config, self.console)
            
            # 执行清理
            cleaned_count = batch_manager.cleanup_old_batches(days)
            
            if cleaned_count > 0:
                self.success_message(f"清理完成: 删除了 {cleaned_count} 个旧状态文件")
            else:
                self.info_message("没有需要清理的文件")
            
            return {"cleaned_count": cleaned_count, "days": days}
            
        except Exception as e:
            self.handle_error(e, "清理操作失败")
            raise typer.Exit(1)


def create_list_batches_command(console, service_factory) -> typer.Typer:
    """创建列出批次命令的Typer应用"""
    
    cmd_handler = ListBatchesCommand(console, service_factory)
    
    def list_batches_command(
        config_file: Optional[str] = typer.Option(
            None,
            "--config",
            "-c",
            help="配置文件路径"
        ),
        limit: int = typer.Option(
            10,
            "--limit",
            "-l",
            help="显示的批次数量限制"
        )
    ):
        """
        📋 列出所有批量处理批次
        
        显示历史和当前的所有批次，包括状态和统计信息。
        
        示例:
          gs_videoreport list-batches              # 显示最近10个批次
          gs_videoreport list-batches --limit 20   # 显示最近20个批次
        """
        return cmd_handler.execute(
            config_file=config_file,
            limit=limit
        )
    
    return list_batches_command


def create_status_command(console, service_factory) -> typer.Typer:
    """创建状态查看命令的Typer应用"""
    
    cmd_handler = StatusCommand(console, service_factory)
    
    def status_command(
        batch_id: str = typer.Argument(
            ..., 
            help="要查看的批次ID"
        ),
        config_file: Optional[str] = typer.Option(
            None,
            "--config",
            "-c",
            help="配置文件路径"
        )
    ):
        """
        📊 查看批次详细状态
        
        显示指定批次的详细信息，包括进度、统计和错误信息。
        
        示例:
          gs_videoreport status batch_20250101_120000_abc123
        """
        return cmd_handler.execute(
            batch_id=batch_id,
            config_file=config_file
        )
    
    return status_command


def create_cancel_command(console, service_factory) -> typer.Typer:
    """创建取消命令的Typer应用"""
    
    cmd_handler = CancelCommand(console, service_factory)
    
    def cancel_command(
        batch_id: str = typer.Argument(
            ..., 
            help="要取消的批次ID"
        ),
        config_file: Optional[str] = typer.Option(
            None,
            "--config",
            "-c",
            help="配置文件路径"
        )
    ):
        """
        🛑 取消批量处理
        
        取消指定的批次处理，停止所有进行中的任务。
        
        示例:
          gs_videoreport cancel batch_20250101_120000_abc123
        """
        return cmd_handler.execute(
            batch_id=batch_id,
            config_file=config_file
        )
    
    return cancel_command


def create_cleanup_command(console, service_factory) -> typer.Typer:
    """创建清理命令的Typer应用"""
    
    cmd_handler = CleanupCommand(console, service_factory)
    
    def cleanup_command(
        days: int = typer.Option(
            7,
            "--days",
            "-d",
            help="清理多少天前的状态文件"
        ),
        config_file: Optional[str] = typer.Option(
            None,
            "--config",
            "-c",
            help="配置文件路径"
        )
    ):
        """
        🧹 清理旧的批次状态文件
        
        删除指定天数之前的批次状态文件以节省空间。
        
        示例:
          gs_videoreport cleanup               # 清理7天前的文件
          gs_videoreport cleanup --days 30    # 清理30天前的文件
        """
        return cmd_handler.execute(
            days=days,
            config_file=config_file
        )
    
    return cleanup_command
