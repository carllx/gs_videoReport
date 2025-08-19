"""
Batch Processing Commands

批量处理相关的CLI命令实现：
- 创建新的批量任务
- 恢复中断的批量任务
- 批量任务管理功能
"""

import sys
from typing import Any, Optional

import typer

from .base import BaseCommand
from ..validators.file_validator import FileValidator
from ..formatters.progress_formatter import ProgressFormatter
from ..formatters.error_formatter import ErrorFormatter


class BatchCommand(BaseCommand):
    """批量处理命令处理器"""
    
    def execute(self,
                input_dir: str,
                template: str = "chinese_transcript",
                output: Optional[str] = None,
                skip_existing: bool = False,
                max_retries: int = 3,
                config_file: Optional[str] = None,
                verbose: bool = False) -> Any:
        """
        执行批量处理
        
        Args:
            input_dir: 输入目录
            template: 模板名称
            output: 输出目录
            skip_existing: 是否跳过已存在的文件
            max_retries: 最大重试次数
            config_file: 配置文件路径
            verbose: 是否详细输出
            
        Returns:
            Any: 处理结果
        """
        try:
            if verbose:
                self.console.print("[bold green]🚀 开始批量处理[/bold green]")
                self.console.print(f"输入目录: {input_dir}")
                self.console.print(f"模板: {template}")
                self.console.print(f"输出目录: {output or '(同输入目录)'}")
            
            # 1. 验证输入目录
            is_valid, error_msg = FileValidator.validate_directory(input_dir, must_contain_videos=True)
            if not is_valid:
                ErrorFormatter.display_file_error(self.console, input_dir, error_msg, "目录验证失败")
                raise typer.Exit(1)
            
            # 2. 加载配置
            config = self.load_config(config_file)
            
            if verbose:
                self.console.print("[green]✅ 配置加载成功[/green]")
            
            # 3. 创建批量管理器
            batch_manager = self.service_factory.create_batch_manager(config, self.console)
            
            # 4. 创建新批次
            self.console.print("[cyan]📋 创建新批次...[/cyan]")
            batch_id = batch_manager.create_batch(
                input_dir=input_dir,
                template=template,
                output_dir=output,
                skip_existing=skip_existing,
                max_retries=max_retries
            )
            
            # 5. 处理批次
            self.console.print("[cyan]🎯 开始批量处理...[/cyan]")
            result = batch_manager.process_batch(batch_id, verbose)
            
            # 6. 显示结果
            success = result.get("success", False)
            if success:
                self.success_message(f"批次 {batch_id} 处理完成！")
            else:
                if result.get("resumable"):
                    self.warning_message(f"使用以下命令恢复处理: gs_videoreport resume {batch_id}")
                raise typer.Exit(1)
            
            return result
            
        except Exception as e:
            self.handle_error(e, "批量处理失败")
            raise typer.Exit(1)


class ResumeCommand(BaseCommand):
    """批量处理恢复命令处理器"""
    
    def execute(self,
                batch_id: str,
                config_file: Optional[str] = None,
                verbose: bool = False) -> Any:
        """
        恢复批量处理
        
        Args:
            batch_id: 批次ID
            config_file: 配置文件路径
            verbose: 是否详细输出
            
        Returns:
            Any: 处理结果
        """
        try:
            if verbose:
                self.console.print("[bold green]🔄 恢复批量处理[/bold green]")
                self.console.print(f"批次ID: {batch_id}")
            
            # 1. 加载配置
            config = self.load_config(config_file)
            
            if verbose:
                self.console.print("[green]✅ 配置加载成功[/green]")
            
            # 2. 创建批量管理器
            batch_manager = self.service_factory.create_batch_manager(config, self.console)
            
            # 3. 检查是否可以恢复
            if not batch_manager.can_resume(batch_id):
                ErrorFormatter.display_error(
                    self.console,
                    ValueError(f"无法恢复批次: {batch_id}"),
                    "批次恢复检查失败"
                )
                self.console.print("[yellow]💡 使用 'gs_videoreport list-batches' 查看可用批次[/yellow]")
                raise typer.Exit(1)
            
            # 4. 恢复并继续处理
            self.console.print("[cyan]🎯 继续批量处理...[/cyan]")
            result = batch_manager.resume_batch(batch_id, verbose)
            
            # 5. 显示结果
            success = result.get("success", False)
            if success:
                self.success_message(f"批次 {batch_id} 恢复处理完成！")
            else:
                if result.get("resumable"):
                    self.warning_message(f"批次再次中断，可继续恢复: gs_videoreport resume {batch_id}")
                raise typer.Exit(1)
            
            return result
            
        except Exception as e:
            self.handle_error(e, "批次恢复失败")
            raise typer.Exit(1)


def create_batch_command(console, service_factory) -> typer.Typer:
    """创建批量处理命令的Typer应用"""
    
    cmd_handler = BatchCommand(console, service_factory)
    
    def batch_command(
        input_dir: str = typer.Argument(
            ..., 
            help="包含视频文件的目录路径"
        ),
        template: str = typer.Option(
            "chinese_transcript", 
            "--template", 
            "-t", 
            help="分析模板类型"
        ),
        output: Optional[str] = typer.Option(
            None,
            "--output",
            "-o", 
            help="输出目录（默认为输入目录）"
        ),
        skip_existing: bool = typer.Option(
            False,
            "--skip-existing",
            help="跳过已存在的输出文件"
        ),
        max_retries: int = typer.Option(
            3,
            "--max-retries",
            help="每个视频的最大重试次数"
        ),
        config_file: Optional[str] = typer.Option(
            None,
            "--config",
            "-c",
            help="配置文件路径"
        ),
        verbose: bool = typer.Option(
            False, 
            "--verbose", 
            "-v", 
            help="显示详细输出"
        )
    ):
        """
        🎬 批量处理目录中的所有视频文件
        
        特点:
        • 自动重试网络错误
        • 单个失败不影响其他视频
        • 自动保存进度状态
        • 支持断点续传
        
        示例:
          gs_videoreport batch ./videos/                           # 基本用法
          gs_videoreport batch ./videos/ --template summary_report # 指定模板
          gs_videoreport batch ./videos/ --skip-existing --verbose # 跳过已有文件
        """
        return cmd_handler.execute(
            input_dir=input_dir,
            template=template,
            output=output,
            skip_existing=skip_existing,
            max_retries=max_retries,
            config_file=config_file,
            verbose=verbose
        )
    
    return batch_command


def create_resume_command(console, service_factory) -> typer.Typer:
    """创建恢复命令的Typer应用"""
    
    cmd_handler = ResumeCommand(console, service_factory)
    
    def resume_command(
        batch_id: str = typer.Argument(
            ..., 
            help="要恢复的批次ID"
        ),
        config_file: Optional[str] = typer.Option(
            None,
            "--config",
            "-c",
            help="配置文件路径"
        ),
        verbose: bool = typer.Option(
            False, 
            "--verbose", 
            "-v", 
            help="显示详细输出"
        )
    ):
        """
        🔄 从断点恢复批量处理
        
        支持任意时间中断后的无缝恢复，保持所有进度和状态。
        
        示例:
          gs_videoreport resume batch_20250101_120000_abc123  # 恢复指定批次
          gs_videoreport resume batch_20250101_120000_abc123 --verbose  # 详细输出
        """
        return cmd_handler.execute(
            batch_id=batch_id,
            config_file=config_file,
            verbose=verbose
        )
    
    return resume_command
