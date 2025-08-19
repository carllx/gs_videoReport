"""
CLI Utils Module

提供CLI工具函数：
- 服务工厂 - 统一创建和配置各种服务
- 参数解析工具 - 命令行参数的高级解析
- 响应辅助工具 - 标准化的响应处理
"""

from .service_factory import ServiceFactory

__all__ = [
    'ServiceFactory'
]
