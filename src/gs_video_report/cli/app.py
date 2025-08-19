"""
Modular CLI Application

gs_videoReport v0.2.0 的新模块化CLI主应用：
- 基于命令模式的架构
- 统一的服务工厂和依赖注入
- 完整的错误处理和用户体验
- 支持单视频处理和批量处理
"""

import typer
from rich.console import Console

from .commands import (
    create_single_video_command,
    create_batch_command, 
    create_resume_command,
    create_list_batches_command,
    create_status_command,
    create_cancel_command,
    create_cleanup_command,
    create_list_templates_command,
    create_list_models_command,
    create_setup_api_command,
    create_performance_report_command
)
from .utils.service_factory import ServiceFactory
from .formatters.error_formatter import ErrorFormatter

# 创建主应用
app = typer.Typer(
    name="gs_videoreport",
    help="""🎓 gs_videoReport v0.2.0 - Professional AI-powered video batch processor

Transform your video content into structured educational materials using Google Gemini AI.
NEW: Enterprise-grade batch processing with intelligent concurrency and resume capabilities.

QUICK START:
  gs_videoreport video.mp4                    # Single video processing  
  gs_videoreport batch ./videos/              # Batch processing (NEW!)
  gs_videoreport setup-api                    # First-time setup

BATCH PROCESSING (NEW v0.2.0):
  gs_videoreport batch ./videos/ --template chinese_transcript
  gs_videoreport resume batch_20250101_120000_abc123    # Resume from interruption
  gs_videoreport list-batches                 # View all batch jobs
  gs_videoreport status batch_id              # Check batch progress

SINGLE VIDEO WITH SMART MODEL FALLBACK:
  gs_videoreport video.mp4 --template chinese_transcript
  gs_videoreport video.mp4 --model gemini-2.5-pro --output ./lessons
  gs_videoreport list-templates               # See available templates

PERFORMANCE & MONITORING:
  gs_videoreport performance-report           # View API usage & costs
  gs_videoreport list-models                  # See model capabilities
  
For more help: https://github.com/carllx/gs_videoReport""",
    add_completion=False,
    rich_markup_mode="rich"
)

# 全局服务
console = Console()
service_factory = ServiceFactory()

# 注册核心命令
app.command(name="main")(create_single_video_command(console, service_factory))
app.command(name="batch")(create_batch_command(console, service_factory))
app.command(name="resume")(create_resume_command(console, service_factory))

# 注册管理命令
app.command(name="list-batches")(create_list_batches_command(console, service_factory))
app.command(name="status")(create_status_command(console, service_factory))
app.command(name="cancel")(create_cancel_command(console, service_factory))
app.command(name="cleanup")(create_cleanup_command(console, service_factory))

# 注册信息命令
app.command(name="setup-api")(create_setup_api_command(console, service_factory))
app.command(name="list-templates")(create_list_templates_command(console, service_factory))
app.command(name="list-models")(create_list_models_command(console, service_factory))
app.command(name="performance-report")(create_performance_report_command(console, service_factory))

@app.command()
def version():
    """显示版本信息"""
    console.print("[bold cyan]gs_videoReport[/bold cyan]")
    console.print("Version: 0.2.0 (Modular CLI Architecture)")
    console.print("AI-powered video-to-lesson-plan converter")
    console.print("\n[green]✅ 所有命令已迁移完成![/green]")
    console.print("  🎯 核心命令: main, batch, resume")
    console.print("  📋 管理命令: list-batches, status, cancel, cleanup")
    console.print("  ℹ️  信息命令: setup-api, list-templates, list-models, performance-report")
    console.print("\n[bold green]🎉 CLI架构重构完成！[/bold green]")
    console.print("  📦 模块化架构: 20个文件")
    console.print("  🏗️  设计模式: 命令模式+工厂模式+依赖注入")
    console.print("  🧪 可测试性: 每个组件独立可测试")

def cleanup_resources():
    """清理应用资源"""
    try:
        service_factory.clear_cache()
        console.print("[dim]🧹 资源已清理[/dim]")
    except Exception as e:
        console.print(f"[dim red]清理资源时出错: {e}[/dim]")

# 应用关闭时清理资源
import atexit
atexit.register(cleanup_resources)

if __name__ == "__main__":
    app()
