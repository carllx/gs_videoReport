"""
Configuration management for gs_videoReport

This module handles loading and validating configuration from YAML files.
Integrates with security module for safe API key management.
"""
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Optional path to config file. If None, uses default config.yaml
        
    Returns:
        Dictionary containing configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        ValueError: If required configuration is missing
    """
    if config_path is None:
        # Default config path relative to project root
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}")
    
    if config is None:
        config = {}
    
    # Validate required configuration
    validate_config(config)
    
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration has required fields and secure API key setup.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If required configuration is missing
    """
    # Try to import security module (may not be available during initial setup)
    try:
        from .security.api_key_manager import api_key_manager, APIKeyValidationError
        use_security_validation = True
    except ImportError:
        use_security_validation = False
        logging.warning("Security module not available, using basic validation")
    
    # Check for Google API configuration
    if 'google_api' not in config:
        raise ValueError("Missing 'google_api' section in configuration")
    
    # Enhanced API key validation using security module
    if use_security_validation:
        try:
            # Attempt to get and validate API key using security manager
            api_key = api_key_manager.get_api_key(config)
            if api_key:
                masked_key = api_key_manager.get_masked_api_key(api_key)
                logging.info(f"✅ 已验证API密钥: {masked_key}")
        except APIKeyValidationError as e:
            # Non-fatal during config loading, just warn
            logging.warning(f"⚠️ API密钥配置问题: {e}")
            print(f"⚠️ API密钥配置问题: {e}")
    else:
        # Fallback to basic validation
        google_api = config['google_api']
        if not google_api.get('api_key'):
            print("⚠️ Warning: Google API key not configured. Set api_key in config.yaml for full functionality.")
    
    # Set defaults for missing optional fields
    config.setdefault('templates', {})
    config['templates'].setdefault('default_template', 'comprehensive_lesson')
    config['templates'].setdefault('template_path', 'src/gs_video_report/templates/prompts')
    
    config.setdefault('output', {})
    config['output'].setdefault('default_path', './output')
    config['output'].setdefault('file_naming', '{video_title}_{timestamp}')
    config['output'].setdefault('include_metadata', True)
    
    config.setdefault('processing', {})
    config['processing'].setdefault('verbose', False)
    config['processing'].setdefault('retry_attempts', 3)
    config['processing'].setdefault('timeout_seconds', 300)
    
    config.setdefault('video', {})
    config['video'].setdefault('max_duration_minutes', 60)
    config['video'].setdefault('download_quality', 'best')
    
    # v0.2.0: 批量处理配置
    config.setdefault('batch_processing', {})
    config['batch_processing'].setdefault('parallel_workers', 2)  # 单密钥模式默认值，多密钥模式将基于密钥数量动态调整
    config['batch_processing'].setdefault('enable_resume', True)
    config['batch_processing'].setdefault('checkpoint_interval', 10)
    config['batch_processing'].setdefault('api_rate_limit', 60)
    config['batch_processing'].setdefault('adaptive_concurrency', False)
    config['batch_processing'].setdefault('max_retries', 3)
    
    # 视频处理增强配置
    config.setdefault('video_processing', {})
    config['video_processing'].setdefault('max_file_size_mb', 100)
    config['video_processing'].setdefault('supported_formats', ['mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v'])
    config['video_processing'].setdefault('upload_timeout_seconds', 300)
    
    # 🚨 QA测试专用：强制设置Google Gemini 2.5 Pro模型
    config.setdefault('google_api', {})
    config['google_api'].setdefault('model', 'gemini-2.5-pro')  # 统一默认模型配置
    
    # 🚨 QA测试专用：统一的目录和模板配置
    config.setdefault('qa_testing', {})
    config['qa_testing'].setdefault('input_directory', 'test_videos')
    config['qa_testing'].setdefault('output_directory', 'test_output') 
    config['qa_testing'].setdefault('template', 'chinese_transcript')
    config['qa_testing'].setdefault('model', 'gemini-2.5-pro')  # 强制确保模型一致性


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get configuration value using dot notation path.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated key path (e.g., 'google_api.model')
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    keys = key_path.split('.')
    value = config
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def get_default_model(config: Dict[str, Any]) -> str:
    """
    🎯 统一的模型配置获取函数 - 所有地方都应该使用这个函数
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Model name string
    """
    return get_config_value(config, 'google_api.model', 'gemini-2.5-pro')


def get_default_input_directory(config: Dict[str, Any]) -> str:
    """
    🎯 统一的输入目录配置获取函数
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Input directory path
    """
    # 🚨 QA测试专用：强制使用test_videos目录
    return get_config_value(config, 'qa_testing.input_directory', 'test_videos')


def get_default_output_directory(config: Dict[str, Any]) -> str:
    """
    🎯 统一的输出目录配置获取函数
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Output directory path
    """
    # 🚨 QA测试专用：强制使用test_output目录
    return get_config_value(config, 'qa_testing.output_directory', 'test_output')


def get_default_template(config: Dict[str, Any]) -> str:
    """
    🎯 统一的模板配置获取函数
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Template name
    """
    # 🚨 QA测试专用：强制使用chinese_transcript模板
    return get_config_value(config, 'qa_testing.template', 'chinese_transcript')


def get_dynamic_parallel_workers(config: Dict[str, Any]) -> int:
    """
    🎯 基于API密钥数量动态计算并行worker数量
    
    Args:
        config: Configuration dictionary
        
    Returns:
        动态计算的并行worker数量
    """
    # 尝试获取多密钥配置
    multi_key_config = config.get('multi_api_keys', {})
    
    if multi_key_config.get('enabled', False):
        # 多密钥模式：基于API密钥数量决定并行数
        api_keys = multi_key_config.get('api_keys', [])
        num_keys = len(api_keys)
        
        if num_keys > 0:
            # 每个API密钥支持1个并行worker，最少1个，最多8个（安全限制）
            dynamic_workers = min(max(num_keys, 1), 8)
            logging.info(f"🔄 多密钥模式：{num_keys}个API密钥 → {dynamic_workers}个并行worker")
            return dynamic_workers
    
    # 单密钥模式或未配置多密钥：使用保守的默认值
    default_workers = get_config_value(config, 'batch_processing.parallel_workers', 2)
    logging.info(f"🔧 单密钥模式：使用默认{default_workers}个并行worker")
    return default_workers


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Optional path to config file. If None, uses default config.yaml
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


class Config:
    """Configuration wrapper class for easier access to config data."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize Config with data dictionary."""
        if config_data is None:
            self.data = {}
        else:
            self.data = config_data.copy()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        return get_config_value(self.data, key_path, default)
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        current = self.data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access to top-level keys."""
        return self.data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in config."""
        return key in self.data
    
    @classmethod
    def from_file(cls, config_path: Optional[str] = None) -> 'Config':
        """Load Config from file."""
        config_data = load_config(config_path)
        return cls(config_data)
