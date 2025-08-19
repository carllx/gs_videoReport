"""
Batch Manager Handler

提供批量处理的业务逻辑：
- 批量任务创建和管理
- 批量处理状态监控
- 批量任务恢复和取消
- 批量处理结果汇总
"""

import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from pathlib import Path
from rich.console import Console

if TYPE_CHECKING:
    from ...config import Config
    from ...batch.enhanced_processor import EnhancedBatchProcessor

logger = logging.getLogger(__name__)


class BatchManager:
    """批量处理管理器
    
    封装批量处理的管理逻辑，提供批量任务的创建、监控、恢复等功能。
    """
    
    def __init__(self, config: 'Config', console: Console):
        """
        初始化批量管理器
        
        Args:
            config: 配置对象
            console: Rich控制台
        """
        self.config = config
        self.console = console
        
        # 延迟初始化批量处理器
        self._batch_processor: Optional['EnhancedBatchProcessor'] = None
    
    @property
    def batch_processor(self) -> 'EnhancedBatchProcessor':
        """获取批量处理器实例（懒加载）"""
        if self._batch_processor is None:
            from ...batch.enhanced_processor import EnhancedBatchProcessor
            self._batch_processor = EnhancedBatchProcessor(self.config)
        return self._batch_processor
    
    def create_batch(self, 
                    input_dir: str,
                    template: Optional[str] = None,
                    output_dir: Optional[str] = None,
                    skip_existing: bool = False,
                    max_retries: int = 3) -> str:
        """
        创建新的批量处理任务
        
        Args:
            input_dir: 输入目录
            template: 模板名称
            output_dir: 输出目录
            skip_existing: 是否跳过已存在的文件
            max_retries: 最大重试次数
            
        Returns:
            str: 批次ID
            
        Raises:
            Exception: 创建失败时抛出异常
        """
        try:
            # 验证输入目录
            self._validate_input_directory(input_dir)
            
            # 确定参数
            template_name = template or self._get_default_template()
            output_directory = output_dir or self._get_default_output_dir()
            
            # 创建批量任务
            batch_id = self.batch_processor.create_new_batch(
                input_dir=input_dir,
                template_name=template_name,
                output_dir=output_directory,
                skip_existing=skip_existing,
                max_retries=max_retries
            )
            
            self.console.print(f"[green]✅ 批量任务已创建: {batch_id}[/green]")
            return batch_id
            
        except Exception as e:
            logger.error(f"Batch creation failed: {e}")
            raise Exception(f"批量任务创建失败: {e}")
    
    def process_batch(self, batch_id: str, verbose: bool = False) -> Dict[str, Any]:
        """
        处理批量任务
        
        Args:
            batch_id: 批次ID
            verbose: 是否启用详细输出
            
        Returns:
            Dict[str, Any]: 处理结果
            
        Raises:
            Exception: 处理失败时抛出异常
        """
        try:
            self.console.print(f"[cyan]🚀 开始批量处理: {batch_id}[/cyan]")
            
            # 执行批量处理
            result = self.batch_processor.process_batch(batch_id)
            
            # 显示处理结果
            self._display_batch_result(result, verbose)
            
            return result
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise Exception(f"批量处理失败: {e}")
    
    def resume_batch(self, batch_id: str, verbose: bool = False) -> Dict[str, Any]:
        """
        恢复批量处理
        
        Args:
            batch_id: 批次ID
            verbose: 是否启用详细输出
            
        Returns:
            Dict[str, Any]: 处理结果
            
        Raises:
            Exception: 恢复失败时抛出异常
        """
        try:
            if not self.can_resume(batch_id):
                raise ValueError(f"无法恢复批次: {batch_id}")
            
            self.console.print(f"[cyan]🔄 恢复批量处理: {batch_id}[/cyan]")
            
            # 恢复处理
            if not self.batch_processor.resume_batch(batch_id):
                raise Exception("批次恢复失败")
            
            # 继续处理
            result = self.batch_processor.process_batch(batch_id)
            
            # 显示处理结果
            self._display_batch_result(result, verbose)
            
            return result
            
        except Exception as e:
            logger.error(f"Batch resume failed: {e}")
            raise Exception(f"批量处理恢复失败: {e}")
    
    def can_resume(self, batch_id: str) -> bool:
        """
        检查是否可以恢复批次
        
        Args:
            batch_id: 批次ID
            
        Returns:
            bool: 是否可以恢复
        """
        try:
            return self.batch_processor.can_resume_batch(batch_id)
        except Exception as e:
            logger.warning(f"Failed to check resume capability: {e}")
            return False
    
    def list_batches(self) -> List[Dict[str, Any]]:
        """
        列出所有批量任务
        
        Returns:
            List[Dict[str, Any]]: 批量任务列表
        """
        try:
            return self.batch_processor.list_batches()
        except Exception as e:
            logger.error(f"Failed to list batches: {e}")
            return []
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        获取批量任务状态
        
        Args:
            batch_id: 批次ID
            
        Returns:
            Optional[Dict[str, Any]]: 批次状态信息
        """
        try:
            return self.batch_processor.get_batch_status(batch_id)
        except Exception as e:
            logger.error(f"Failed to get batch status: {e}")
            return None
    
    def cancel_batch(self, batch_id: str) -> bool:
        """
        取消批量任务
        
        Args:
            batch_id: 批次ID
            
        Returns:
            bool: 是否取消成功
        """
        try:
            success = self.batch_processor.cancel_batch(batch_id)
            if success:
                self.console.print(f"[yellow]⏹️  批次已取消: {batch_id}[/yellow]")
            else:
                self.console.print(f"[red]❌ 无法取消批次: {batch_id}[/red]")
            return success
        except Exception as e:
            logger.error(f"Failed to cancel batch: {e}")
            return False
    
    def cleanup_old_batches(self, days: int = 30) -> int:
        """
        清理旧的批量任务
        
        Args:
            days: 保留天数
            
        Returns:
            int: 清理的任务数量
        """
        try:
            count = self.batch_processor.cleanup_old_states(days)
            if count > 0:
                self.console.print(f"[green]🧹 已清理 {count} 个旧批次[/green]")
            else:
                self.console.print("[dim]🧹 没有需要清理的旧批次[/dim]")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup old batches: {e}")
            return 0
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """
        获取批量处理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            batches = self.list_batches()
            
            stats = {
                'total_batches': len(batches),
                'pending_batches': 0,
                'running_batches': 0,
                'completed_batches': 0,
                'failed_batches': 0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'failed_tasks': 0
            }
            
            for batch in batches:
                status = batch.get('status', '').lower()
                if status == 'pending':
                    stats['pending_batches'] += 1
                elif status == 'running':
                    stats['running_batches'] += 1
                elif status == 'completed':
                    stats['completed_batches'] += 1
                elif status == 'failed':
                    stats['failed_batches'] += 1
                
                stats['total_tasks'] += batch.get('total_tasks', 0)
                stats['completed_tasks'] += batch.get('completed_tasks', 0)
                stats['failed_tasks'] += batch.get('failed_tasks', 0)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get batch statistics: {e}")
            return {}
    
    def _validate_input_directory(self, input_dir: str) -> None:
        """验证输入目录"""
        from ..validators.file_validator import FileValidator
        
        is_valid, error_msg = FileValidator.validate_directory(input_dir, must_contain_videos=True)
        if not is_valid:
            raise ValueError(f"输入目录验证失败: {error_msg}")
    
    def _get_default_template(self) -> str:
        """获取默认模板"""
        # 🎯 统一配置：使用统一的模板配置获取函数
        from ...config import get_default_template
        return get_default_template(self.config.data)
    
    def _get_default_output_dir(self) -> str:
        """获取默认输出目录"""
        # 🎯 统一配置：使用统一的输出目录配置获取函数
        from ...config import get_default_output_directory
        return get_default_output_directory(self.config.data)
    
    def _display_batch_result(self, result: Dict[str, Any], verbose: bool = False) -> None:
        """显示批量处理结果"""
        success = result.get('success', False)
        
        if success:
            self.console.print("[bold green]🎉 批量处理完成！[/bold green]")
        else:
            self.console.print("[bold red]❌ 批量处理失败[/bold red]")
        
        # 显示统计信息
        stats = result.get('statistics', {})
        if stats:
            self.console.print("[cyan]📊 处理统计:[/cyan]")
            for key, value in stats.items():
                display_key = key.replace('_', ' ').title()
                self.console.print(f"  • {display_key}: {value}")
        
        # 如果有错误，显示错误信息
        errors = result.get('errors', [])
        if errors and verbose:
            self.console.print("[red]❌ 错误详情:[/red]")
            for error in errors[:5]:  # 只显示前5个错误
                self.console.print(f"  • {error}")
            if len(errors) > 5:
                self.console.print(f"  • ... 还有 {len(errors) - 5} 个错误")
        
        # 恢复提示
        if not success and result.get('resumable', False):
            batch_id = result.get('batch_id', '')
            if batch_id:
                self.console.print(f"[yellow]💡 使用以下命令恢复处理: gs_videoreport resume {batch_id}[/yellow]")
    
    def cleanup(self) -> None:
        """清理资源"""
        if self._batch_processor is not None and hasattr(self._batch_processor, 'cleanup'):
            try:
                self._batch_processor.cleanup()
            except Exception as e:
                logger.warning(f"Failed to cleanup batch processor: {e}")
        
        self._batch_processor = None
    
    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            self.cleanup()
        except:
            pass  # 忽略清理时的错误
