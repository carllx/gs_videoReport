"""
Configuration management for gs_videoReport

This module handles loading and validating configuration from YAML files.
"""
import yaml
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
    Validate configuration has required fields.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If required configuration is missing
    """
    # Check for Google API configuration
    if 'google_api' not in config:
        raise ValueError("Missing 'google_api' section in configuration")
    
    google_api = config['google_api']
    
    if not google_api.get('api_key'):
        # Allow empty API key for CLI testing, but warn
        print("⚠️  Warning: Google API key not configured. Set api_key in config.yaml for full functionality.")
    
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
