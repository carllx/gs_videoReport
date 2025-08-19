"""
Video Processor Handler

提供单视频处理的业务逻辑：
- 视频文件验证和预处理
- Gemini服务调用和结果处理
- 教案格式化和文件输出
- 错误处理和状态更新
"""

import logging
from pathlib import Path
from typing import Optional, Any, Dict, TYPE_CHECKING
from rich.console import Console

if TYPE_CHECKING:
    from ...config import Config
    from ...services.simple_gemini_service import SimpleGeminiService
    from ...template_manager import TemplateManager
    from ...lesson_formatter import LessonFormatter
    from ...file_writer import FileWriter

logger = logging.getLogger(__name__)


class VideoProcessor:
    """视频处理器
    
    封装单视频处理的完整业务逻辑，提供从文件验证到结果输出的端到端处理。
    """
    
    def __init__(self, 
                 config: 'Config', 
                 console: Console, 
                 verbose: bool = False):
        """
        初始化视频处理器
        
        Args:
            config: 配置对象
            console: Rich控制台
            verbose: 是否启用详细输出
        """
        self.config = config
        self.console = console
        self.verbose = verbose
        
        # 延迟初始化服务（按需创建）
        self._gemini_service: Optional['SimpleGeminiService'] = None
        self._template_manager: Optional['TemplateManager'] = None
        self._lesson_formatter: Optional['LessonFormatter'] = None
        self._file_writer: Optional['FileWriter'] = None
    
    @property
    def gemini_service(self) -> 'SimpleGeminiService':
        """获取Gemini服务实例（懒加载）"""
        if self._gemini_service is None:
            from ...services.simple_gemini_service import SimpleGeminiService
            self._gemini_service = SimpleGeminiService(self.config.data)
            if self.verbose:
                self.console.print("[dim]🔧 简化Gemini服务已初始化[/dim]")
        return self._gemini_service
    
    @property
    def template_manager(self) -> 'TemplateManager':
        """获取模板管理器实例（懒加载）"""
        if self._template_manager is None:
            from ...template_manager import TemplateManager
            self._template_manager = TemplateManager(self.config)
            if self.verbose:
                self.console.print("[dim]🔧 模板管理器已初始化[/dim]")
        return self._template_manager
    
    @property
    def lesson_formatter(self) -> 'LessonFormatter':
        """获取教案格式化器实例（懒加载）"""
        if self._lesson_formatter is None:
            from ...lesson_formatter import LessonFormatter
            self._lesson_formatter = LessonFormatter(self.config)
            if self.verbose:
                self.console.print("[dim]🔧 教案格式化器已初始化[/dim]")
        return self._lesson_formatter
    
    @property
    def file_writer(self) -> 'FileWriter':
        """获取文件写入器实例（懒加载）"""
        if self._file_writer is None:
            from ...file_writer import FileWriter
            self._file_writer = FileWriter(self.config)
            if self.verbose:
                self.console.print("[dim]🔧 文件写入器已初始化[/dim]")
        return self._file_writer
    
    def process_single_video(self, 
                           video_path: str, 
                           template: Optional[str] = None,
                           output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        处理单个视频文件
        
        Args:
            video_path: 视频文件路径
            template: 模板名称
            output_dir: 输出目录
            
        Returns:
            Dict[str, Any]: 处理结果字典
            
        Raises:
            Exception: 处理失败时抛出异常
        """
        try:
            if self.verbose:
                self.console.print(f"[cyan]🎬 开始处理视频: {Path(video_path).name}[/cyan]")
            
            # 1. 验证输入文件
            self._validate_input_file(video_path)
            
            # 2. 准备处理参数
            template_name = template or self._get_default_template()
            template_params = self._prepare_template_params(video_path)
            preferred_model = self._get_preferred_model()
            
            if self.verbose:
                self.console.print(f"[dim]📝 使用模板: {template_name}[/dim]")
                self.console.print(f"[dim]🤖 首选模型: {preferred_model}[/dim]")
            
            # 3. 处理视频
            analysis_result = self._analyze_video(
                video_path=video_path,
                template_name=template_name,
                preferred_model=preferred_model,
                template_params=template_params
            )
            
            # 4. 格式化结果
            # 将分析结果转换为字典格式
            if hasattr(analysis_result, '__dict__'):
                analysis_dict = analysis_result.__dict__
            else:
                analysis_dict = analysis_result
            lesson_data = self._format_lesson_plan(analysis_dict, template_name)
            
            # 5. 保存文件
            output_path = self._determine_output_path(video_path, output_dir)
            write_result = self._save_lesson_plan(lesson_data, output_path)
            
            # 6. 构建结果
            result = {
                'success': write_result.success,
                'analysis_result': analysis_result,
                'lesson_data': lesson_data,
                'output_path': write_result.file_path if write_result.success else None,
                'write_result': write_result
            }
            
            if self.verbose:
                self.console.print("[green]✅ 视频处理完成[/green]")
            
            return result
            
        except Exception as e:
            logger.error(f"Video processing failed: {e}")
            raise Exception(f"视频处理失败: {e}")
    
    def get_processing_info(self) -> Dict[str, Any]:
        """
        获取处理器信息
        
        Returns:
            Dict[str, Any]: 处理器信息字典
        """
        info = {
            'config_loaded': self.config is not None,
            'verbose_mode': self.verbose,
            'services_initialized': {
                'gemini_service': self._gemini_service is not None,
                'template_manager': self._template_manager is not None,
                'lesson_formatter': self._lesson_formatter is not None,
                'file_writer': self._file_writer is not None
            }
        }
        
        # 如果Gemini服务已初始化，获取其信息
        if self._gemini_service is not None:
            info['gemini_service_info'] = self._gemini_service.get_client_info_enhanced()
        
        return info
    
    def cleanup(self) -> None:
        """清理资源"""
        if self._gemini_service is not None and hasattr(self._gemini_service, 'cleanup'):
            try:
                self._gemini_service.cleanup()
                if self.verbose:
                    self.console.print("[dim]🧹 Gemini服务已清理[/dim]")
            except Exception as e:
                logger.warning(f"Failed to cleanup Gemini service: {e}")
        
        # 重置服务引用
        self._gemini_service = None
        self._template_manager = None
        self._lesson_formatter = None
        self._file_writer = None
    
    def _validate_input_file(self, video_path: str) -> None:
        """验证输入文件"""
        from ..validators.file_validator import FileValidator
        
        is_valid, error_msg = FileValidator.validate_video_file(video_path)
        if not is_valid:
            raise ValueError(f"视频文件验证失败: {error_msg}")
        
        if self.verbose:
            file_info = FileValidator.get_file_info(video_path)
            if file_info:
                self.console.print(f"[dim]📊 文件大小: {file_info['size_mb']:.1f} MB[/dim]")
    
    def _get_default_template(self) -> str:
        """获取默认模板"""
        # 🎯 统一配置：使用统一的模板配置获取函数
        from ...config import get_default_template
        return get_default_template(self.config.data)
    
    def _get_preferred_model(self) -> str:
        """获取首选模型"""
        # 🎯 统一配置：使用统一的模型配置获取函数
        from ...config import get_default_model
        return get_default_model(self.config.data)
    
    def _prepare_template_params(self, video_path: str) -> Dict[str, Any]:
        """准备模板参数"""
        video_file = Path(video_path)
        
        # 基础参数
        params = {
            'video_title': video_file.stem,
            'video_duration': 'analyzing...',
            'subject_area': 'general',
            'detail_level': 'comprehensive',
            'current_timestamp': self._get_current_timestamp(),
            
            # 为chinese_transcript模板提供必需参数
            'language_preference': 'simplified_chinese',
            
            # 为其他模板提供通用参数
            'max_length': '500',
            'focus_areas': 'key concepts and learning objectives'
        }
        
        return params
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _analyze_video(self, 
                      video_path: str, 
                      template_name: str, 
                      preferred_model: str, 
                      template_params: Dict[str, Any]) -> Any:
        """分析视频内容"""
        if self.verbose:
            self.console.print("[cyan]🧠 开始AI分析...[/cyan]")
        
        try:
            result = self.gemini_service.process_video_end_to_end_enhanced(
                video_path=video_path,
                template_manager=self.template_manager,
                template_name=template_name,
                preferred_model=preferred_model,
                enable_fallback=True,
                cleanup_file=True,
                **template_params
            )
            
            if self.verbose:
                processing_time = result.metadata.get('processing_time_seconds', 0)
                cost = result.metadata.get('estimated_cost_usd', 0)
                self.console.print(f"[dim]⏱️  处理时间: {processing_time:.1f}秒[/dim]")
                self.console.print(f"[dim]💰 预估成本: ${cost:.4f}[/dim]")
            
            return result
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise Exception(f"视频分析失败: {e}")
    
    def _format_lesson_plan(self, analysis_result: Any, template_name: str) -> Any:
        """格式化教案"""
        if self.verbose:
            self.console.print("[cyan]📝 格式化教案...[/cyan]")
        
        try:
            lesson_data = self.lesson_formatter.format_lesson_plan(
                analysis_result, 
                template_name
            )
            
            if self.verbose:
                word_count = len(lesson_data.content.split()) if hasattr(lesson_data, 'content') else 0
                self.console.print(f"[dim]📄 教案字数: {word_count}[/dim]")
            
            return lesson_data
            
        except Exception as e:
            logger.error(f"Lesson formatting failed: {e}")
            raise Exception(f"教案格式化失败: {e}")
    
    def _determine_output_path(self, video_path: str, output_dir: Optional[str]) -> str:
        """确定输出路径"""
        video_file = Path(video_path)
        filename = f"{video_file.stem}_lesson.md"
        
        if output_dir:
            output_path = Path(output_dir) / filename
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            return str(output_path)
        else:
            # 使用默认输出路径
            # 🎯 统一配置：使用统一的输出目录配置获取函数
            from ...config import get_default_output_directory
            default_output = get_default_output_directory(self.config.data)
            output_path = Path(default_output) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            return str(output_path)
    
    def _save_lesson_plan(self, lesson_data: Any, output_path: str) -> Any:
        """保存教案文件"""
        if self.verbose:
            self.console.print(f"[cyan]💾 保存到: {output_path}[/cyan]")
        
        try:
            write_result = self.file_writer.write_lesson_plan(lesson_data, output_path)
            
            if not write_result.success:
                raise Exception(f"文件写入失败: {write_result.error_message}")
            
            if self.verbose:
                file_size = Path(output_path).stat().st_size / 1024  # KB
                self.console.print(f"[dim]📄 文件大小: {file_size:.1f} KB[/dim]")
            
            return write_result
            
        except Exception as e:
            logger.error(f"File writing failed: {e}")
            raise Exception(f"文件保存失败: {e}")
    
    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            self.cleanup()
        except:
            pass  # 忽略清理时的错误
