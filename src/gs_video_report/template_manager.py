"""
Template management for gs_videoReport

This module handles loading, validating, and rendering prompt templates.
"""
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from string import Template


class TemplateManager:
    """Manages prompt templates for video analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize template manager.
        
        Args:
            config: Application configuration dictionary
        """
        self.config = config
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load all templates from the templates directory."""
        template_path = self.config.get('templates', {}).get('template_path', 
                                                             'src/gs_video_report/templates/prompts')
        
        # Convert relative path to absolute
        if not Path(template_path).is_absolute():
            template_path = Path(__file__).parent.parent.parent / template_path
        else:
            template_path = Path(template_path)
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template directory not found: {template_path}")
        
        # Load all YAML files in templates directory
        for template_file in template_path.glob("*.yaml"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = yaml.safe_load(f)
                
                if template_data and 'templates' in template_data:
                    # File contains multiple templates
                    for name, template in template_data['templates'].items():
                        template['name'] = name  # Ensure name is set
                        self.templates[name] = template
                elif template_data:
                    # File contains single template
                    name = template_data.get('name', template_file.stem)
                    template_data['name'] = name
                    self.templates[name] = template_data
                    
            except Exception as e:
                print(f"Warning: Failed to load template from {template_file}: {e}")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        Get list of all available templates.
        
        Returns:
            List of template metadata dictionaries
        """
        return [
            {
                'name': template['name'],
                'version': template.get('version', '1.0'),
                'description': template.get('description', 'No description available'),
                'parameters': template.get('parameters', [])
            }
            for template in self.templates.values()
        ]
    
    def _get_api_model(self) -> str:
        """获取API模型配置"""
        # 🎯 统一配置：使用统一的模型配置获取函数
        from .config import get_default_model
        return get_default_model(self.config)
    
    def has_template(self, name: str) -> bool:
        """
        Check if template exists.
        
        Args:
            name: Template name to check
            
        Returns:
            True if template exists, False otherwise
        """
        return name in self.templates
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template dictionary or None if not found
        """
        return self.templates.get(name)
    
    def render_prompt(self, template_name: str, **kwargs) -> str:
        """
        Render a prompt template with provided parameters.
        
        Args:
            template_name: Name of template to render
            **kwargs: Template parameters
            
        Returns:
            Rendered prompt string
            
        Raises:
            ValueError: If template not found or required parameters missing
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        prompt_template = template.get('prompt', '')
        if not prompt_template:
            raise ValueError(f"Template '{template_name}' has no prompt content")
        
        # Check for required parameters
        required_params = template.get('parameters', [])
        missing_params = [param for param in required_params if param not in kwargs]
        if missing_params:
            raise ValueError(f"Missing required parameters for template '{template_name}': {missing_params}")
        
        # Set default values for common parameters
        defaults = {
            'video_duration': kwargs.get('video_duration', 'unknown'),
            'subject_area': kwargs.get('subject_area', 'general'),
            'detail_level': kwargs.get('detail_level', 'comprehensive'),
            'max_length': kwargs.get('max_length', '500'),
            'focus_areas': kwargs.get('focus_areas', 'key concepts and learning points')
        }
        
        # Merge provided kwargs with defaults
        render_params = {**defaults, **kwargs}
        
        try:
            # Use Python's string Template for safe parameter substitution
            template_obj = Template(prompt_template)
            rendered = template_obj.safe_substitute(**render_params)
            return rendered
        except Exception as e:
            raise ValueError(f"Failed to render template '{template_name}': {e}")
    
    def get_model_config(self, template_name: str) -> Dict[str, Any]:
        """
        Get model configuration for a template.
        
        Args:
            template_name: Name of template
            
        Returns:
            Model configuration dictionary
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        model_config = template.get('model_config', {})
        
        # Set defaults from main config
        defaults = {
            'temperature': self.config.get('google_api', {}).get('temperature', 0.7),
            'max_tokens': self.config.get('google_api', {}).get('max_tokens', 8192),
            # 🎯 统一配置：使用统一的模型配置获取函数
            'model': self._get_api_model()
        }
        
        return {**defaults, **model_config}
    
    def validate_template(self, template: Dict[str, Any]) -> List[str]:
        """
        Validate template structure and content.
        
        Args:
            template: Template dictionary to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        if 'name' not in template:
            errors.append("Template missing 'name' field")
        
        if 'prompt' not in template or not template['prompt'].strip():
            errors.append("Template missing 'prompt' content")
        
        # Check version format
        version = template.get('version', '1.0')
        if not isinstance(version, str):
            errors.append("Template 'version' must be a string")
        
        # Check parameters are list
        parameters = template.get('parameters', [])
        if not isinstance(parameters, list):
            errors.append("Template 'parameters' must be a list")
        
        # Check model_config is dict
        model_config = template.get('model_config', {})
        if not isinstance(model_config, dict):
            errors.append("Template 'model_config' must be a dictionary")
        
        return errors
