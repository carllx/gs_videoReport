"""
Base Command Class for CLI

提供所有CLI命令的基础抽象类，包含：
- 统一的配置加载机制
- 标准化的错误处理
- 一致的日志记录
- 可复用的服务创建
"""

import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING
from pathlib import Path

import typer
from rich.console import Console

if TYPE_CHECKING:
    from ..utils.service_factory import ServiceFactory
    from ...config import Config


class BaseCommand(ABC):
    """CLI命令基类
    
    提供所有命令通用的功能：
    - 配置管理
    - 错误处理
    - 服务创建
    - 响应格式化
    """
    
    def __init__(self, console: Console, service_factory: 'ServiceFactory'):
        """
        初始化基础命令
        
        Args:
            console: Rich控制台实例，用于输出
            service_factory: 服务工厂，用于创建各种服务实例
        """
        self.console = console
        self.service_factory = service_factory
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        执行命令的具体逻辑
        
        Args:
            **kwargs: 命令参数
            
        Returns:
            Any: 命令执行结果
            
        Raises:
            typer.Exit: 当命令执行失败时
        """
        pass
    
    def load_config(self, config_file: Optional[str] = None, **overrides) -> 'Config':
        """
        加载配置，支持覆盖参数
        
        Args:
            config_file: 配置文件路径
            **overrides: 覆盖配置参数
            
        Returns:
            Config: 配置对象
            
        Raises:
            ValueError: 配置加载失败
        """
        try:
            return self.service_factory.load_config(config_file, **overrides)
        except Exception as e:
            self.handle_error(e, "配置加载失败")
            raise typer.Exit(1)
    
    def handle_error(self, error: Exception, context: str = "") -> None:
        """
        统一的错误处理
        
        Args:
            error: 异常对象
            context: 错误上下文描述
        """
        error_msg = str(error)
        
        # 基础错误信息
        if context:
            self.console.print(f"[red]❌ {context}: {error_msg}[/red]")
        else:
            self.console.print(f"[red]❌ 错误: {error_msg}[/red]")
        
        # 根据错误类型提供解决建议
        self._provide_error_suggestions(error)
    
    def _provide_error_suggestions(self, error: Exception) -> None:
        """根据错误类型提供解决建议"""
        error_str = str(error).lower()
        
        if "api key" in error_str or "unauthorized" in error_str:
            self.console.print("[yellow]💡 解决建议:[/yellow]")
            self.console.print("   • 检查API密钥: gs_videoreport setup-api")
            self.console.print("   • 使用--api-key参数: gs_videoreport --api-key YOUR_KEY")
            self.console.print("   • 获取API密钥: https://makersuite.google.com/app/apikey")
        elif "file not found" in error_str or "no such file" in error_str:
            self.console.print("[yellow]💡 解决建议:[/yellow]")
            self.console.print("   • 检查文件路径是否正确")
            self.console.print("   • 确保文件存在且有读取权限")
            self.console.print("   • 使用绝对路径重试")
        elif "network" in error_str or "connection" in error_str:
            self.console.print("[yellow]💡 解决建议:[/yellow]")
            self.console.print("   • 检查网络连接")
            self.console.print("   • 验证API密钥是否有效")
            self.console.print("   • 稍后重试")
        elif "quota" in error_str or "limit" in error_str:
            self.console.print("[yellow]💡 解决建议:[/yellow]")
            self.console.print("   • API配额已用完，请检查使用情况")
            self.console.print("   • 等待配额重置或升级API计划")
            self.console.print("   • 使用更小的文件或降低处理频率")
    
    def success_message(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        显示成功消息
        
        Args:
            message: 成功消息
            details: 可选的详细信息字典
        """
        self.console.print(f"[bold green]✅ {message}[/bold green]")
        
        if details:
            self.console.print("[cyan]📊 详细信息:[/cyan]")
            for key, value in details.items():
                self.console.print(f"  • {key}: {value}")
    
    def warning_message(self, message: str) -> None:
        """显示警告消息"""
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")
    
    def info_message(self, message: str) -> None:
        """显示信息消息"""
        self.console.print(f"[blue]ℹ️  {message}[/blue]")
    
    def validate_file_path(self, file_path: str, must_exist: bool = True) -> Path:
        """
        验证文件路径
        
        Args:
            file_path: 文件路径
            must_exist: 是否必须存在
            
        Returns:
            Path: 验证后的路径对象
            
        Raises:
            ValueError: 路径验证失败
        """
        path = Path(file_path)
        
        if must_exist and not path.exists():
            raise ValueError(f"文件不存在: {file_path}")
        
        if must_exist and not path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")
        
        return path
    
    def validate_directory_path(self, dir_path: str, must_exist: bool = True) -> Path:
        """
        验证目录路径
        
        Args:
            dir_path: 目录路径
            must_exist: 是否必须存在
            
        Returns:
            Path: 验证后的路径对象
            
        Raises:
            ValueError: 路径验证失败
        """
        path = Path(dir_path)
        
        if must_exist and not path.exists():
            raise ValueError(f"目录不存在: {dir_path}")
        
        if must_exist and not path.is_dir():
            raise ValueError(f"路径不是目录: {dir_path}")
        
        return path
