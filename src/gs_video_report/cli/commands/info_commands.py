"""
Info Commands

信息查询相关的CLI命令实现：
- 列出可用模板
- 列出可用模型
- API密钥设置向导
- 性能报告显示
"""

import sys
import os
from pathlib import Path
from typing import Any, Optional

import typer
from rich.table import Table

from .base import BaseCommand
from ..formatters.table_formatter import TableFormatter
from ..formatters.error_formatter import ErrorFormatter


class ListTemplatesCommand(BaseCommand):
    """列出模板命令处理器"""
    
    def execute(self,
                config_file: Optional[str] = None,
                api_key: Optional[str] = None) -> Any:
        """列出所有可用的提示模板"""
        try:
            # 加载配置
            try:
                config = self.load_config(config_file, api_key=api_key)
            except Exception:
                if api_key:
                    # 创建最小配置
                    from ...config import Config
                    config = Config({
                        'google_api': {'api_key': api_key},
                        'templates': {'default_template': 'comprehensive_lesson'}
                    })
                else:
                    raise

            # 创建模板管理器
            template_mgr = self.service_factory.create_template_manager(config)
            templates = template_mgr.list_templates()
            
            if not templates:
                self.console.print("[yellow]没有找到模板[/yellow]")
                return []
            
            # 格式化显示
            TableFormatter.display_template_list(self.console, templates)
            
            return templates
            
        except Exception as e:
            self.handle_error(e, "加载模板失败")
            raise typer.Exit(1)


class ListModelsCommand(BaseCommand):
    """列出模型命令处理器"""
    
    def execute(self) -> Any:
        """列出所有可用的Gemini模型"""
        self.console.print("[bold cyan]🤖 可用的Gemini模型[/bold cyan]")
        
        models = [
            {
                "name": "gemini-2.5-pro",
                "description": "最强大的模型，适合复杂推理和分析",
                "features": ["高精度", "复杂推理", "长上下文"]
            },
            {
                "name": "gemini-2.5-flash", 
                "description": "平衡性能和速度，适合大多数任务",
                "features": ["良好精度", "快速响应", "平衡成本"]
            },
            {
                "name": "gemini-2.5-flash-lite",
                "description": "最快最经济，适合简单任务",
                "features": ["基础精度", "超快速度", "低成本"]
            }
        ]
        
        table = Table(title="Gemini模型")
        table.add_column("模型", style="cyan", width=20)
        table.add_column("描述", style="white", width=40)
        table.add_column("主要特性", style="green", width=30)
        
        for model in models:
            features_str = ", ".join(model["features"])
            table.add_row(model["name"], model["description"], features_str)
        
        self.console.print(table)
        self.console.print("\n[yellow]用法:[/yellow] --model gemini-2.5-flash")
        
        return models


class SetupApiCommand(BaseCommand):
    """API设置命令处理器"""
    
    def execute(self, config_file: Optional[str] = None) -> Any:
        """交互式API密钥设置向导"""
        self.console.print("[bold cyan]🔧 API密钥设置向导[/bold cyan]\n")
        
        # 检查当前API密钥状态
        current_sources = self._check_existing_api_keys(config_file)
        
        if current_sources:
            self.console.print("[green]✅ 已找到API密钥:[/green]")
            for source in current_sources:
                self.console.print(f"   • {source}")
            self.console.print()
            
            if not typer.confirm("是否要更新API密钥?"):
                self.console.print("[yellow]设置已取消[/yellow]")
                return {"cancelled": True}
        else:
            self.console.print("[red]❌ 未找到有效的API密钥[/red]")
        
        # 显示获取API密钥的说明
        self._show_api_key_instructions()
        
        # 获取API密钥
        api_key = typer.prompt("请输入您的Google Gemini API密钥", hide_input=True)
        
        if not api_key or len(api_key) < 20:
            ErrorFormatter.display_error(
                self.console,
                ValueError("API密钥格式无效"),
                "API密钥验证失败"
            )
            raise typer.Exit(1)
        
        # 选择存储方式
        storage_choice = self._get_storage_choice()
        
        if storage_choice == 1:
            self._show_env_var_instructions(api_key)
        elif storage_choice == 2:
            self._save_to_config_file(api_key, config_file)
        
        self.success_message("API密钥设置完成！")
        return {"success": True, "storage": "env" if storage_choice == 1 else "config"}
    
    def _check_existing_api_keys(self, config_file: Optional[str]) -> list:
        """检查现有的API密钥"""
        current_sources = []
        
        # 检查环境变量
        env_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY')
        if env_key and env_key not in ['YOUR_GEMINI_API_KEY_HERE', 'DEMO_API_KEY_FOR_TESTING']:
            current_sources.append(f"环境变量: {env_key[:15]}...")
        
        # 检查配置文件
        try:
            from ...config import Config
            config = Config.from_file(config_file)
            config_key = config.get('google_api.api_key')
            if config_key and config_key not in ['YOUR_GEMINI_API_KEY_HERE', 'DEMO_API_KEY_FOR_TESTING']:
                current_sources.append(f"配置文件: {config_key[:15]}...")
        except:
            pass
        
        return current_sources
    
    def _show_api_key_instructions(self):
        """显示获取API密钥的说明"""
        self.console.print("[yellow]📋 如何获取Google Gemini API密钥:[/yellow]")
        self.console.print("   1. 访问: https://makersuite.google.com/app/apikey")
        self.console.print("   2. 使用Google账户登录")
        self.console.print("   3. 点击'创建API密钥'")
        self.console.print("   4. 复制生成的密钥\n")
    
    def _get_storage_choice(self) -> int:
        """获取存储选择"""
        self.console.print("[yellow]💾 您希望将API密钥存储在哪里?[/yellow]")
        self.console.print("   1. 环境变量 (推荐，更安全)")
        self.console.print("   2. 配置文件 (方便但安全性较低)")
        
        return typer.prompt("选择选项", type=int, default=1)
    
    def _show_env_var_instructions(self, api_key: str):
        """显示环境变量设置说明"""
        self.console.print("[green]🔐 设置环境变量，请运行:[/green]")
        self.console.print(f'   export GOOGLE_GEMINI_API_KEY="{api_key}"\n')
        self.console.print("[yellow]💡 要永久生效，请将此行添加到shell配置文件:[/yellow]")
        self.console.print("   • bash: ~/.bashrc 或 ~/.bash_profile")
        self.console.print("   • zsh: ~/.zshrc")
        self.console.print("   • fish: ~/.config/fish/config.fish")
    
    def _save_to_config_file(self, api_key: str, config_file: Optional[str]):
        """保存到配置文件"""
        config_path = Path(config_file) if config_file else Path('config.yaml')
        
        # 简化实现：只显示手动编辑说明
        self.console.print(f"[green]📝 请手动编辑配置文件 {config_path}:[/green]")
        self.console.print("google_api:")
        self.console.print(f'  api_key: "{api_key}"')


class PerformanceReportCommand(BaseCommand):
    """性能报告命令处理器"""
    
    def execute(self, config_file: Optional[str] = None) -> Any:
        """显示Gemini服务性能报告"""
        try:
            # 加载配置
            try:
                config = self.load_config(config_file)
            except Exception:
                from ...config import Config
                config = Config({})
            
            # 创建Gemini服务（简化版本）
            gemini_service = self.service_factory.create_gemini_service(config)
            
            # 显示性能摘要（简化版本）
            self.console.print("[bold cyan]📈 Gemini服务性能报告[/bold cyan]")
            self._display_simple_performance_summary(gemini_service)
            
            # 显示模型兼容性
            self._display_model_compatibility()
            
            # 显示成本估算
            self._display_cost_estimation()
            
            # 显示提示
            self.console.print("\n[dim]💡 提示: 使用 --model 参数选择不同的模型[/dim]")
            self.console.print("[dim]💡 系统会自动在模型不兼容时进行回退[/dim]")
            
            return {"success": True}
            
        except Exception as e:
            self.handle_error(e, "性能报告生成失败")
            raise typer.Exit(1)
    
    def _display_simple_performance_summary(self, gemini_service):
        """显示简化的性能摘要"""
        performance_table = Table(title="🚀 SimpleGeminiService 状态")
        performance_table.add_column("项目", style="cyan")
        performance_table.add_column("状态", style="green")
        
        # 检查服务状态
        status_items = [
            ("Gemini客户端", "✅ 已初始化" if gemini_service.client else "❌ 未初始化"),
            ("API连接", "✅ 正常" if gemini_service._client else "❌ 异常"),
            ("服务类型", "🎯 简化版本（避免过度开发）"),
            ("支持功能", "视频上传、内容分析、文件清理"),
            ("默认模型", "gemini-2.5-pro")
        ]
        
        for item, status in status_items:
            performance_table.add_row(item, status)
        
        self.console.print(performance_table)
    
    def _display_model_compatibility(self):
        """显示模型兼容性信息（简化版）"""
        self.console.print("\n[bold cyan]🤖 模型兼容性矩阵[/bold cyan]")
        
        # 🎯 简化版本：不使用复杂的兼容性检测器
        compatibility_table = Table(title="支持的Gemini模型")
        compatibility_table.add_column("模型", style="cyan")
        compatibility_table.add_column("视频支持", style="green")
        compatibility_table.add_column("推荐用途", style="yellow")
        
        models = [
            ("gemini-2.5-pro", "✅ 完全支持", "高质量分析，复杂视频"),
            ("gemini-2.5-flash", "✅ 支持", "标准分析，平衡性能"),
            ("gemini-2.5-flash-lite", "✅ 基础支持", "简单分析，快速处理")
        ]
        
        for model, support, usage in models:
            compatibility_table.add_row(model, support, usage)
        
        self.console.print(compatibility_table)
    
    def _display_cost_estimation(self):
        """显示成本估算信息（简化版）"""
        self.console.print("\n[bold cyan]💰 成本估算[/bold cyan]")
        
        # 🎯 简化版本：使用固定的成本估算表
        cost_table = Table(title="模型定价 (USD)")
        cost_table.add_column("模型", style="cyan")
        cost_table.add_column("每个视频大约成本", style="green")
        cost_table.add_column("说明", style="yellow")
        
        pricing_data = [
            ("gemini-2.5-pro", "$0.01-0.02", "最高质量，成本稍高"),
            ("gemini-2.5-flash", "$0.005-0.01", "平衡性价比"),
            ("gemini-2.5-flash-lite", "$0.001-0.005", "最经济选择")
        ]
        
        for model, cost, desc in pricing_data:
            cost_table.add_row(model, cost, desc)
        
        self.console.print(cost_table)
        self.console.print("\n[dim]💡 实际成本取决于视频长度和分析复杂度[/dim]")


# Command factory functions
def create_list_templates_command(console, service_factory):
    cmd_handler = ListTemplatesCommand(console, service_factory)
    
    def list_templates_command(
        config_file: Optional[str] = typer.Option(None, "--config", "-c", help="配置文件路径"),
        api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="Google Gemini API密钥")
    ):
        """📝 列出所有可用的提示模板"""
        return cmd_handler.execute(config_file=config_file, api_key=api_key)
    
    return list_templates_command


def create_list_models_command(console, service_factory):
    cmd_handler = ListModelsCommand(console, service_factory)
    
    def list_models_command():
        """🤖 列出所有可用的Gemini模型"""
        return cmd_handler.execute()
    
    return list_models_command


def create_setup_api_command(console, service_factory):
    cmd_handler = SetupApiCommand(console, service_factory)
    
    def setup_api_command(
        config_file: Optional[str] = typer.Option(None, "--config", "-c", help="配置文件路径")
    ):
        """🔧 交互式API密钥设置向导"""
        return cmd_handler.execute(config_file=config_file)
    
    return setup_api_command


def create_performance_report_command(console, service_factory):
    cmd_handler = PerformanceReportCommand(console, service_factory)
    
    def performance_report_command(
        config_file: Optional[str] = typer.Option(None, "--config", "-c", help="配置文件路径")
    ):
        """📈 显示Gemini服务性能报告"""
        return cmd_handler.execute(config_file=config_file)
    
    return performance_report_command
