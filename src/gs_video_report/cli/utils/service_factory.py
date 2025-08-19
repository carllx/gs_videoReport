"""
Service Factory for CLI

统一的服务创建和配置管理：
- 配置加载和缓存
- 服务实例创建
- 依赖注入管理
- 资源清理
"""

import logging
from typing import Optional, Any, Dict, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from ...config import Config
    from ...services.simple_gemini_service import SimpleGeminiService
    from ...template_manager import TemplateManager
    from ...lesson_formatter import LessonFormatter
    from ...file_writer import FileWriter

logger = logging.getLogger(__name__)


class ServiceFactory:
    """
    服务工厂，统一创建和配置各种服务
    
    特性：
    - 配置缓存：避免重复加载相同配置
    - 懒加载：按需创建服务实例
    - 依赖管理：自动处理服务间依赖关系
    - 资源清理：统一的资源清理机制
    """
    
    def __init__(self):
        """初始化服务工厂"""
        self._config_cache: Dict[str, 'Config'] = {}
        self._service_cache: Dict[str, Any] = {}
        self._initialized = True
    
    def load_config(self, config_file: Optional[str] = None, **overrides) -> 'Config':
        """
        加载配置，支持缓存和覆盖
        
        Args:
            config_file: 配置文件路径
            **overrides: 覆盖参数
            
        Returns:
            Config: 配置对象
            
        Raises:
            Exception: 配置加载失败
        """
        # 创建缓存键
        cache_key = self._create_cache_key(config_file, overrides)
        
        # 检查缓存
        if cache_key in self._config_cache:
            logger.debug(f"Using cached config: {cache_key}")
            return self._config_cache[cache_key]
        
        try:
            # 加载基础配置
            from ...config import load_config, Config
            config_dict = load_config(config_file)
            
            # 应用覆盖参数
            self._apply_overrides(config_dict, overrides)
            
            # 创建配置对象
            config = Config(config_dict)
            
            # 缓存配置
            self._config_cache[cache_key] = config
            logger.debug(f"Loaded and cached config: {cache_key}")
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise Exception(f"配置加载失败: {e}")
    
    def create_gemini_service(self, config: 'Config'):
        """
        创建Gemini服务（简化版），支持多密钥轮循
        
        Args:
            config: 配置对象
            
        Returns:
            SimpleGeminiService: 简化Gemini服务实例
        """
        service_key = f"gemini_service_{id(config)}"
        
        if service_key not in self._service_cache:
            try:
                # 🎯 使用简化服务，避免过度开发
                from ...services.simple_gemini_service import SimpleGeminiService
                
                # 🔄 检查是否启用多密钥轮循模式
                api_keys = None
                multi_key_config = config.data.get('multi_api_keys', {})
                if multi_key_config.get('enabled', False):
                    api_keys = multi_key_config.get('api_keys', [])
                    if api_keys:
                        logger.info(f"🔄 启用多密钥轮循模式，管理 {len(api_keys)} 个API密钥")
                    else:
                        logger.warning("⚠️ 多密钥模式已启用但未提供API密钥，将回退到单密钥模式")
                        api_keys = None
                
                service = SimpleGeminiService(config.data, api_keys=api_keys)
                self._service_cache[service_key] = service
                logger.debug("Created new SimpleGeminiService instance")
            except Exception as e:
                logger.error(f"Failed to create Gemini service: {e}")
                raise Exception(f"Gemini服务创建失败: {e}")
        
        return self._service_cache[service_key]
    
    def create_template_manager(self, config: Optional['Config'] = None) -> 'TemplateManager':
        """
        创建模板管理器
        
        Args:
            config: 配置对象（可选）
        
        Returns:
            TemplateManager: 模板管理器实例
        """
        cache_key = f"template_manager_{id(config) if config else 'default'}"
        
        if cache_key not in self._service_cache:
            try:
                from ...template_manager import TemplateManager
                if config:
                    service = TemplateManager(config)
                else:
                    # 尝试获取默认配置
                    try:
                        default_config = self.load_config()
                        service = TemplateManager(default_config)
                    except:
                        # 如果无法加载配置，使用默认构造
                        service = TemplateManager()
                self._service_cache[cache_key] = service
                logger.debug("Created new TemplateManager instance")
            except Exception as e:
                logger.error(f"Failed to create template manager: {e}")
                raise Exception(f"模板管理器创建失败: {e}")
        
        return self._service_cache[cache_key]
    
    def create_lesson_formatter(self) -> 'LessonFormatter':
        """
        创建教案格式化器
        
        Returns:
            LessonFormatter: 教案格式化器实例
        """
        if 'lesson_formatter' not in self._service_cache:
            try:
                from ...lesson_formatter import LessonFormatter
                service = LessonFormatter()
                self._service_cache['lesson_formatter'] = service
                logger.debug("Created new LessonFormatter instance")
            except Exception as e:
                logger.error(f"Failed to create lesson formatter: {e}")
                raise Exception(f"教案格式化器创建失败: {e}")
        
        return self._service_cache['lesson_formatter']
    
    def create_file_writer(self) -> 'FileWriter':
        """
        创建文件写入器
        
        Returns:
            FileWriter: 文件写入器实例
        """
        if 'file_writer' not in self._service_cache:
            try:
                from ...file_writer import FileWriter
                service = FileWriter()
                self._service_cache['file_writer'] = service
                logger.debug("Created new FileWriter instance")
            except Exception as e:
                logger.error(f"Failed to create file writer: {e}")
                raise Exception(f"文件写入器创建失败: {e}")
        
        return self._service_cache['file_writer']
    
    def create_batch_processor(self, config: 'Config'):
        """
        创建批量处理器
        
        Args:
            config: 配置对象
            
        Returns:
            EnhancedBatchProcessor: 批量处理器实例
        """
        service_key = f"batch_processor_{id(config)}"
        
        if service_key not in self._service_cache:
            try:
                from ...batch.enhanced_processor import EnhancedBatchProcessor
                service = EnhancedBatchProcessor(config)
                self._service_cache[service_key] = service
                logger.debug("Created new EnhancedBatchProcessor instance")
            except Exception as e:
                logger.error(f"Failed to create batch processor: {e}")
                raise Exception(f"批量处理器创建失败: {e}")
        
        return self._service_cache[service_key]
    
    def create_video_processor(self, config: 'Config', console, verbose: bool = False):
        """
        创建视频处理器
        
        Args:
            config: 配置对象
            console: Rich控制台
            verbose: 是否详细输出
            
        Returns:
            VideoProcessor: 视频处理器实例
        """
        service_key = f"video_processor_{id(config)}_{verbose}"
        
        if service_key not in self._service_cache:
            try:
                from ..handlers.video_processor import VideoProcessor
                service = VideoProcessor(config, console, verbose)
                self._service_cache[service_key] = service
                logger.debug("Created new VideoProcessor instance")
            except Exception as e:
                logger.error(f"Failed to create video processor: {e}")
                raise Exception(f"视频处理器创建失败: {e}")
        
        return self._service_cache[service_key]
    
    def create_batch_manager(self, config: 'Config', console):
        """
        创建批量管理器
        
        Args:
            config: 配置对象
            console: Rich控制台
            
        Returns:
            BatchManager: 批量管理器实例
        """
        service_key = f"batch_manager_{id(config)}"
        
        if service_key not in self._service_cache:
            try:
                from ..handlers.batch_manager import BatchManager
                service = BatchManager(config, console)
                self._service_cache[service_key] = service
                logger.debug("Created new BatchManager instance")
            except Exception as e:
                logger.error(f"Failed to create batch manager: {e}")
                raise Exception(f"批量管理器创建失败: {e}")
        
        return self._service_cache[service_key]
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取服务信息
        
        Returns:
            Dict[str, Any]: 服务信息字典
        """
        return {
            'cached_configs': len(self._config_cache),
            'cached_services': len(self._service_cache),
            'service_types': list(set(
                key.split('_')[0] if '_' in key else key 
                for key in self._service_cache.keys()
            )),
            'initialized': self._initialized
        }
    
    def clear_cache(self) -> None:
        """清理所有缓存"""
        # 清理服务缓存（某些服务可能需要特殊清理）
        for service_key, service in self._service_cache.items():
            if hasattr(service, 'cleanup'):
                try:
                    service.cleanup()
                    logger.debug(f"Cleaned up service: {service_key}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup service {service_key}: {e}")
        
        # 清空缓存
        self._config_cache.clear()
        self._service_cache.clear()
        logger.info("Cleared all service factory caches")
    
    def _create_cache_key(self, config_file: Optional[str], overrides: Dict[str, Any]) -> str:
        """创建配置缓存键"""
        # 使用配置文件路径和覆盖参数的哈希作为键
        config_path = str(Path(config_file).resolve()) if config_file else "default"
        overrides_hash = hash(frozenset(overrides.items()) if overrides else frozenset())
        return f"{config_path}_{overrides_hash}"
    
    def _apply_overrides(self, config_dict: Dict[str, Any], overrides: Dict[str, Any]) -> None:
        """应用配置覆盖参数"""
        if not overrides:
            return
        
        # API密钥覆盖
        if overrides.get('api_key'):
            config_dict.setdefault('google_api', {})['api_key'] = overrides['api_key']
            logger.debug("Applied API key override")
        
        # 模型覆盖
        if overrides.get('model'):
            config_dict.setdefault('google_api', {})['model'] = overrides['model']
            logger.debug(f"Applied model override: {overrides['model']}")
        
        # 其他覆盖参数
        for key, value in overrides.items():
            if key not in ['api_key', 'model'] and value is not None:
                config_dict[key] = value
                logger.debug(f"Applied config override: {key} = {value}")
    
    def __del__(self):
        """析构函数，清理资源"""
        if hasattr(self, '_initialized') and self._initialized:
            self.clear_cache()
