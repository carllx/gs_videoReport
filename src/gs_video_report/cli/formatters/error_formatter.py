"""
Error Formatter for CLI

提供错误显示和处理功能：
- 统一的错误消息格式
- 错误分类和解决建议
- 堆栈跟踪格式化
- 用户友好的错误提示
"""

import traceback
from typing import Optional, Dict, Any, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class ErrorFormatter:
    """错误格式化器
    
    提供统一的错误显示和处理功能。
    """
    
    @staticmethod
    def display_error(console: Console, 
                     error: Exception, 
                     context: str = "", 
                     show_traceback: bool = False) -> None:
        """
        显示错误信息
        
        Args:
            console: Rich控制台
            error: 异常对象
            context: 错误上下文
            show_traceback: 是否显示堆栈跟踪
        """
        # 错误标题
        if context:
            title = f"❌ {context}"
        else:
            title = "❌ 错误"
        
        # 错误消息
        error_msg = str(error)
        error_type = type(error).__name__
        
        # 创建错误内容
        error_content = f"[red]{error_type}:[/red] {error_msg}"
        
        # 添加解决建议
        suggestions = ErrorFormatter._get_error_suggestions(error)
        if suggestions:
            error_content += "\n\n[yellow]💡 解决建议:[/yellow]"
            for suggestion in suggestions:
                error_content += f"\n   • {suggestion}"
        
        # 显示错误面板
        error_panel = Panel(
            error_content,
            title=title,
            border_style="red"
        )
        console.print(error_panel)
        
        # 显示堆栈跟踪（如果需要）
        if show_traceback:
            ErrorFormatter._display_traceback(console, error)
    
    @staticmethod
    def display_validation_errors(console: Console, 
                                errors: List[Dict[str, Any]]) -> None:
        """
        显示验证错误列表
        
        Args:
            console: Rich控制台
            errors: 验证错误列表
        """
        if not errors:
            return
        
        console.print("[red]❌ 验证失败[/red]")
        
        for i, error in enumerate(errors, 1):
            field = error.get('field', '未知字段')
            message = error.get('message', '验证失败')
            value = error.get('value', '')
            
            error_text = f"[red]{i}. {field}:[/red] {message}"
            if value:
                error_text += f"\n   [dim]当前值: {value}[/dim]"
            
            console.print(error_text)
    
    @staticmethod
    def display_api_error(console: Console, 
                         error_code: str, 
                         error_message: str, 
                         details: Optional[Dict[str, Any]] = None) -> None:
        """
        显示API错误
        
        Args:
            console: Rich控制台
            error_code: 错误代码
            error_message: 错误消息
            details: 可选的详细信息
        """
        # API错误标题
        title = f"🌐 API错误 ({error_code})"
        
        # 错误内容
        error_content = f"[red]{error_message}[/red]"
        
        # 添加详细信息
        if details:
            error_content += "\n\n[cyan]详细信息:[/cyan]"
            for key, value in details.items():
                error_content += f"\n   [dim]{key}:[/dim] {value}"
        
        # 添加API特定的解决建议
        suggestions = ErrorFormatter._get_api_error_suggestions(error_code, error_message)
        if suggestions:
            error_content += "\n\n[yellow]💡 解决建议:[/yellow]"
            for suggestion in suggestions:
                error_content += f"\n   • {suggestion}"
        
        # 显示API错误面板
        api_error_panel = Panel(
            error_content,
            title=title,
            border_style="red"
        )
        console.print(api_error_panel)
    
    @staticmethod
    def display_file_error(console: Console, 
                          filepath: str, 
                          error_message: str, 
                          error_type: str = "文件错误") -> None:
        """
        显示文件相关错误
        
        Args:
            console: Rich控制台
            filepath: 文件路径
            error_message: 错误消息
            error_type: 错误类型
        """
        title = f"📁 {error_type}"
        
        error_content = f"[red]文件:[/red] {filepath}\n"
        error_content += f"[red]错误:[/red] {error_message}"
        
        # 文件错误的解决建议
        suggestions = ErrorFormatter._get_file_error_suggestions(error_message)
        if suggestions:
            error_content += "\n\n[yellow]💡 解决建议:[/yellow]"
            for suggestion in suggestions:
                error_content += f"\n   • {suggestion}"
        
        file_error_panel = Panel(
            error_content,
            title=title,
            border_style="red"
        )
        console.print(file_error_panel)
    
    @staticmethod
    def display_config_error(console: Console, 
                           config_file: Optional[str], 
                           error_message: str) -> None:
        """
        显示配置错误
        
        Args:
            console: Rich控制台
            config_file: 配置文件路径
            error_message: 错误消息
        """
        title = "⚙️ 配置错误"
        
        error_content = f"[red]配置文件:[/red] {config_file or '默认配置'}\n"
        error_content += f"[red]错误:[/red] {error_message}"
        
        # 配置错误的解决建议
        suggestions = [
            "检查配置文件语法是否正确",
            "使用 gs_videoreport setup-api 重新配置",
            "参考 config.yaml.example 模板",
            "确保API密钥格式正确"
        ]
        
        error_content += "\n\n[yellow]💡 解决建议:[/yellow]"
        for suggestion in suggestions:
            error_content += f"\n   • {suggestion}"
        
        config_error_panel = Panel(
            error_content,
            title=title,
            border_style="red"
        )
        console.print(config_error_panel)
    
    @staticmethod
    def display_warning(console: Console, 
                       message: str, 
                       details: Optional[str] = None) -> None:
        """
        显示警告信息
        
        Args:
            console: Rich控制台
            message: 警告消息
            details: 可选的详细信息
        """
        warning_content = f"[yellow]{message}[/yellow]"
        
        if details:
            warning_content += f"\n[dim]{details}[/dim]"
        
        warning_panel = Panel(
            warning_content,
            title="⚠️ 警告",
            border_style="yellow"
        )
        console.print(warning_panel)
    
    @staticmethod
    def _display_traceback(console: Console, error: Exception) -> None:
        """显示堆栈跟踪"""
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb_text = "".join(tb_lines)
        
        traceback_panel = Panel(
            tb_text,
            title="🔍 堆栈跟踪",
            border_style="dim red"
        )
        console.print(traceback_panel)
    
    @staticmethod
    def _get_error_suggestions(error: Exception) -> List[str]:
        """根据错误类型获取解决建议"""
        error_str = str(error).lower()
        error_type = type(error).__name__
        suggestions = []
        
        # API相关错误
        if "api key" in error_str or "unauthorized" in error_str:
            suggestions.extend([
                "检查API密钥: gs_videoreport setup-api",
                "使用--api-key参数: gs_videoreport --api-key YOUR_KEY",
                "获取API密钥: https://makersuite.google.com/app/apikey"
            ])
        
        # 文件相关错误
        elif "file not found" in error_str or "no such file" in error_str:
            suggestions.extend([
                "检查文件路径是否正确",
                "确保文件存在且有读取权限",
                "使用绝对路径重试"
            ])
        
        # 网络相关错误
        elif "network" in error_str or "connection" in error_str:
            suggestions.extend([
                "检查网络连接",
                "验证API密钥是否有效",
                "稍后重试"
            ])
        
        # 配额相关错误
        elif "quota" in error_str or "limit" in error_str:
            suggestions.extend([
                "API配额已用完，请检查使用情况",
                "等待配额重置或升级API计划",
                "使用更小的文件或降低处理频率"
            ])
        
        # 权限相关错误
        elif "permission" in error_str or error_type == "PermissionError":
            suggestions.extend([
                "检查文件或目录的访问权限",
                "确保有足够的系统权限",
                "尝试使用不同的输出目录"
            ])
        
        # 通用建议
        if not suggestions:
            suggestions.extend([
                "检查输入参数是否正确",
                "使用--verbose参数获取更多信息",
                "查看文档或联系支持"
            ])
        
        return suggestions
    
    @staticmethod
    def _get_api_error_suggestions(error_code: str, error_message: str) -> List[str]:
        """获取API错误的解决建议"""
        suggestions = []
        
        if error_code in ["400", "401", "403"]:
            suggestions.extend([
                "检查API密钥是否有效",
                "验证API密钥权限",
                "确认API服务是否启用"
            ])
        elif error_code in ["429"]:
            suggestions.extend([
                "API请求过于频繁，请稍后重试",
                "检查API配额使用情况",
                "考虑升级API计划"
            ])
        elif error_code in ["500", "502", "503"]:
            suggestions.extend([
                "API服务暂时不可用",
                "稍后重试",
                "检查API服务状态"
            ])
        else:
            suggestions.extend([
                "检查API文档了解错误详情",
                "验证请求参数",
                "联系API支持"
            ])
        
        return suggestions
    
    @staticmethod
    def _get_file_error_suggestions(error_message: str) -> List[str]:
        """获取文件错误的解决建议"""
        error_lower = error_message.lower()
        suggestions = []
        
        if "not found" in error_lower:
            suggestions.extend([
                "检查文件路径是否正确",
                "确认文件是否存在",
                "使用绝对路径"
            ])
        elif "permission" in error_lower:
            suggestions.extend([
                "检查文件访问权限",
                "确保有读取/写入权限",
                "尝试使用不同的目录"
            ])
        elif "size" in error_lower or "large" in error_lower:
            suggestions.extend([
                "文件可能过大",
                "尝试压缩视频文件",
                "使用更小的文件测试"
            ])
        elif "format" in error_lower:
            suggestions.extend([
                "检查文件格式是否支持",
                "转换为支持的格式 (mp4, mov, avi等)",
                "确认文件未损坏"
            ])
        else:
            suggestions.extend([
                "检查文件完整性",
                "确认文件路径正确",
                "尝试使用不同的文件"
            ])
        
        return suggestions
