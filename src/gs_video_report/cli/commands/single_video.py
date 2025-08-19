"""
Single Video Processing Command

处理单个视频文件的CLI命令实现：
- 本地视频文件处理
- YouTube URL支持（未来功能）
- 模板选择和参数配置
- 增强型Gemini服务集成
"""

import sys
from pathlib import Path
from typing import Any, Optional

import typer
from rich import print as rprint

from .base import BaseCommand
from ..validators.file_validator import FileValidator
from ..validators.url_validator import URLValidator
from ..formatters.progress_formatter import ProgressFormatter
from ..formatters.error_formatter import ErrorFormatter


class SingleVideoCommand(BaseCommand):
    """单视频处理命令处理器"""
    
    def execute(self, 
                video_input: str,
                template: Optional[str] = None,
                output: Optional[str] = None,
                verbose: bool = False,
                config_file: Optional[str] = None,
                api_key: Optional[str] = None,
                model: Optional[str] = None) -> Any:
        """
        执行单视频处理
        
        Args:
            video_input: 视频输入路径或URL
            template: 模板名称
            output: 输出目录
            verbose: 是否详细输出
            config_file: 配置文件路径
            api_key: API密钥
            model: 模型名称
            
        Returns:
            Any: 处理结果
        """
        try:
            if verbose:
                self.console.print("[bold green]🚀 Starting gs_videoReport v0.2.0[/bold green]")
                self.console.print(f"Input: {video_input}")
            
            # 1. 检测输入类型并验证
            input_type = self._detect_input_type(video_input)
            
            if input_type == 'youtube':
                return self._handle_youtube_url(video_input, verbose)
            else:
                return self._handle_local_video(
                    video_input=video_input,
                    template=template,
                    output=output,
                    verbose=verbose,
                    config_file=config_file,
                    api_key=api_key,
                    model=model
                )
                
        except Exception as e:
            ErrorFormatter.display_error(self.console, e, "单视频处理失败")
            raise typer.Exit(1)
    
    def _detect_input_type(self, video_input: str) -> str:
        """检测输入类型：YouTube URL 或本地文件"""
        if URLValidator.is_valid_youtube_url(video_input):
            return 'youtube'
        return 'local_file'
    
    def _handle_youtube_url(self, url: str, verbose: bool) -> None:
        """处理YouTube URL（当前版本暂不支持）"""
        is_valid, video_id = URLValidator.validate_youtube_url(url)
        
        if not is_valid:
            ErrorFormatter.display_error(
                self.console,
                ValueError("无效的YouTube URL"),
                "YouTube URL验证失败"
            )
            
            self.console.print("[yellow]💡 支持的YouTube URL格式:[/yellow]")
            self.console.print("  • https://www.youtube.com/watch?v=VIDEO_ID")
            self.console.print("  • https://youtu.be/VIDEO_ID")
            self.console.print("  • https://m.youtube.com/watch?v=VIDEO_ID")
            raise typer.Exit(1)
        
        if verbose:
            self.console.print(f"[green]✅ YouTube URL detected[/green]")
            self.console.print(f"Video ID: {video_id}")
        
        # YouTube功能暂未实现
        self.warning_message("YouTube视频下载功能暂未在v0.2.0中实现")
        self.console.print("[yellow]请手动下载视频后使用本地文件路径：[/yellow]")
        self.console.print("示例: gs_videoreport /path/to/downloaded_video.mp4")
        raise typer.Exit(1)
    
    def _handle_local_video(self, 
                          video_input: str,
                          template: Optional[str],
                          output: Optional[str],
                          verbose: bool,
                          config_file: Optional[str],
                          api_key: Optional[str],
                          model: Optional[str]) -> Any:
        """处理本地视频文件"""
        
        # 1. 验证视频文件
        is_valid, error_msg = FileValidator.validate_video_file(video_input)
        if not is_valid:
            ErrorFormatter.display_file_error(self.console, video_input, error_msg)
            raise typer.Exit(1)
        
        if verbose:
            self.console.print(f"[green]✅ 本地视频文件验证通过[/green]")
            file_info = FileValidator.get_file_info(video_input)
            if file_info:
                self.console.print(f"[dim]文件大小: {file_info['size_mb']:.1f} MB[/dim]")
        
        # 2. 加载配置
        config_overrides = {}
        if api_key:
            config_overrides['api_key'] = api_key
        if model:
            config_overrides['model'] = model
            
        config = self.load_config(config_file, **config_overrides)
        
        if verbose:
            self.console.print("[green]✅ 配置加载成功[/green]")
        
        # 3. 验证和设置模型
        if model:
            valid_models = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite']
            if model not in valid_models:
                self.handle_error(
                    ValueError(f"无效的模型 '{model}'，有效模型: {', '.join(valid_models)}"),
                    "模型验证失败"
                )
                raise typer.Exit(1)
            
            if verbose:
                self.console.print(f"[blue]🤖 使用模型: {model}[/blue]")
        
        # 4. 初始化服务
        template_manager = self.service_factory.create_template_manager(config)
        
        # 5. 验证模板
        # 🎯 统一配置：使用统一的模板配置获取函数
        from ...config import get_default_template
        template_name = template or get_default_template(config.data)
        
        if not template_manager.has_template(template_name):
            ErrorFormatter.display_error(
                self.console,
                ValueError(f"模板 '{template_name}' 不存在"),
                "模板验证失败"
            )
            
            self.console.print("[yellow]💡 可用模板:[/yellow]")
            self.console.print("  • comprehensive_lesson")
            self.console.print("  • summary_report") 
            self.console.print("  • chinese_transcript")
            self.console.print("使用 'gs_videoreport list-templates' 查看详细信息")
            raise typer.Exit(1)
        
        if verbose:
            self.console.print(f"[blue]📝 使用模板: {template_name}[/blue]")
        
        # 6. 处理视频
        try:
            # 显示处理状态
            ProgressFormatter.display_processing_status(
                self.console, 
                "initializing",
                {"template": template_name, "file": Path(video_input).name}
            )
            
            # 创建视频处理器
            video_processor = self.service_factory.create_video_processor(config, self.console, verbose)
            
            # 执行处理
            result = video_processor.process_single_video(
                video_path=video_input,
                template=template_name,
                output_dir=output
            )
            
            # 显示处理结果
            ProgressFormatter.display_video_result(self.console, result)
            
            # 成功信息
            analysis_result = result.get('analysis_result')
            if analysis_result:
                self.success_message("视频处理完成", {
                    "输出文件": result.get('output_path', 'N/A'),
                    "字数": analysis_result.word_count,
                    "模板": template_name
                })
            
            return result
            
        except Exception as e:
            self.handle_error(e, "视频处理失败")
            raise typer.Exit(1)


def create_single_video_command(console, service_factory) -> typer.Typer:
    """创建单视频处理命令的Typer应用"""
    
    cmd_handler = SingleVideoCommand(console, service_factory)
    
    def main_command(
        video_input: str = typer.Argument(
            ..., 
            help="📹 本地视频文件路径 (.mp4, .mov, .avi, .mkv, .webm)",
            metavar="VIDEO_FILE"
        ),
        template: Optional[str] = typer.Option(
            None, 
            "--template", 
            "-t", 
            help="📝 分析模板 (comprehensive_lesson, summary_report, chinese_transcript)",
            metavar="TEMPLATE"
        ),
        output: Optional[str] = typer.Option(
            None,
            "--output",
            "-o", 
            help="📁 输出目录",
            metavar="DIR"
        ),
        verbose: bool = typer.Option(
            False, 
            "--verbose", 
            "-v", 
            help="🔍 启用详细输出"
        ),
        config_file: Optional[str] = typer.Option(
            None,
            "--config",
            "-c",
            help="⚙️  配置文件路径",
            metavar="FILE"
        ),
        api_key: Optional[str] = typer.Option(
            None,
            "--api-key",
            "-k",
            help="🔑 Google Gemini API密钥（最高优先级）",
            metavar="KEY"
        ),
        model: Optional[str] = typer.Option(
            None,
            "--model",
            "-m",
            help="🤖 AI模型 (gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite)",
            metavar="MODEL"
        )
    ):
        """
        🎓 处理本地视频文件并生成AI驱动的教案
        
        支持格式:
          .mp4, .mov, .avi, .mkv, .webm
        
        示例:
          📚 基本用法:
            gs_videoreport lecture.mp4
            
          🌟 高级用法:
            gs_videoreport video.mp4 --template chinese_transcript --verbose
            gs_videoreport video.mp4 --model gemini-2.5-pro --api-key YOUR_KEY
            gs_videoreport video.mp4 --output ./my_lessons --template summary_report
        
        首次设置:
          gs_videoreport setup-api    # 交互式API密钥设置
          
        获取帮助:
          gs_videoreport list-templates  # 查看可用模板
          gs_videoreport list-models     # 查看可用AI模型
        """
        return cmd_handler.execute(
            video_input=video_input,
            template=template,
            output=output,
            verbose=verbose,
            config_file=config_file,
            api_key=api_key,
            model=model
        )
    
    return main_command
