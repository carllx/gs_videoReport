"""
gs_video_report 安全模块

提供API密钥管理、配置验证和安全检查功能。

主要功能：
- API密钥安全管理和验证
- 配置文件安全检查
- 敏感信息泄露防护
- 安全最佳实践指导
"""

from .api_key_manager import APIKeyManager, APIKeyValidationError, api_key_manager

__all__ = [
    'APIKeyManager',
    'APIKeyValidationError', 
    'api_key_manager'
]

# 版本信息
__version__ = '1.0.0'

# 安全配置
SECURITY_FEATURES = {
    'api_key_validation': True,
    'environment_variable_support': True,
    'sensitive_data_filtering': True,
    'configuration_validation': True,
    'git_security_check': True
}

def get_security_info():
    """获取安全模块信息"""
    return {
        'version': __version__,
        'features': SECURITY_FEATURES,
        'description': '提供企业级安全功能的API密钥管理模块'
    }
