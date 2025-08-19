"""
CLI Commands Module

提供模块化的CLI命令处理器：
- 基础命令抽象类
- 单视频处理命令
- 批量处理命令集
- 管理命令集
- 信息查询命令集
"""

from .base import BaseCommand
from .single_video import SingleVideoCommand, create_single_video_command
from .batch_commands import BatchCommand, ResumeCommand, create_batch_command, create_resume_command
from .management_commands import (
    ListBatchesCommand, StatusCommand, CancelCommand, CleanupCommand,
    create_list_batches_command, create_status_command, 
    create_cancel_command, create_cleanup_command
)
from .info_commands import (
    ListTemplatesCommand, ListModelsCommand, SetupApiCommand, PerformanceReportCommand,
    create_list_templates_command, create_list_models_command,
    create_setup_api_command, create_performance_report_command
)

__all__ = [
    'BaseCommand',
    'SingleVideoCommand',
    'create_single_video_command',
    'BatchCommand',
    'ResumeCommand', 
    'create_batch_command',
    'create_resume_command',
    'ListBatchesCommand',
    'StatusCommand',
    'CancelCommand', 
    'CleanupCommand',
    'create_list_batches_command',
    'create_status_command',
    'create_cancel_command',
    'create_cleanup_command',
    'ListTemplatesCommand',
    'ListModelsCommand', 
    'SetupApiCommand',
    'PerformanceReportCommand',
    'create_list_templates_command',
    'create_list_models_command',
    'create_setup_api_command',
    'create_performance_report_command'
]