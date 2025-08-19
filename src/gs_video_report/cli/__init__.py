"""
Modular CLI for gs_videoReport v0.2.0

重构的模块化CLI架构，提供：
- 职责单一的命令处理器
- 可复用的业务逻辑处理器  
- 统一的验证和格式化
- 易于测试和维护的代码结构
"""

# 导入新的模块化CLI应用
from .app import app

__all__ = ['app']