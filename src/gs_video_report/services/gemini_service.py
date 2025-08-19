"""
Google Gemini API integration service for video content analysis.

This module provides services for uploading video files to Google Gemini
and generating structured lesson plans using AI analysis.

Based on the latest Google Gen AI Python SDK documentation from MCP Context7.
"""
import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from google import genai
from google.genai import types
from rich.console import Console
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from ..template_manager import TemplateManager
from ..config import get_config_value

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Console for rich output
console = Console()


class GeminiAnalysisResult:
    """Container for Gemini analysis results."""
    
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata
        self.timestamp = time.time()
    
    @property
    def word_count(self) -> int:
        """Get approximate word count of the analysis."""
        return len(self.content.split()) if self.content else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
            'word_count': self.word_count
        }


class GeminiService:
    """Service for interacting with Google Gemini API for video analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Gemini service.
        
        Args:
            config: Application configuration dictionary
            
        Raises:
            ValueError: If API key is not configured
            Exception: If client initialization fails
        """
        self.config = config
        self._client = None
        self._setup_client()
    
    def _setup_client(self) -> None:
        """Initialize Google Gen AI client."""
        # Priority: Config File (CLI overriden) > Environment Variable > Error
        api_key = (
            get_config_value(self.config, 'google_api.api_key') or
            os.environ.get('GOOGLE_GEMINI_API_KEY') or 
            os.environ.get('GEMINI_API_KEY')
        )
        
        if not api_key or api_key in ['YOUR_GEMINI_API_KEY_HERE', 'DEMO_API_KEY_FOR_TESTING']:
            raise ValueError(
                "Google API key not configured. Set one of:\n"
                "  1. Command line: --api-key 'your_key' (highest priority)\n"
                "  2. Environment variable: export GOOGLE_GEMINI_API_KEY='your_key'\n"
                "  3. Config file: Set 'google_api.api_key' in config.yaml"
            )
        
        try:
            # Initialize client with API key for Gemini Developer API (supports file upload)
            # Based on Google Gen AI SDK documentation: file upload is only supported in Gemini Developer client
            # For 0.3.0: Need to explicitly specify vertexai=False to use Gemini Developer API
            self._client = genai.Client(api_key=api_key, vertexai=False)
            logger.info("Gemini Developer client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise Exception(f"Gemini client initialization failed: {e}")
    
    @property
    def client(self) -> genai.Client:
        """Get the Gemini client instance."""
        if not self._client:
            raise RuntimeError("Gemini client not initialized")
        return self._client
    
    def validate_video_file(self, video_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate video file for Gemini processing.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        video_file = Path(video_path)
        
        # Check file exists
        if not video_file.exists():
            return False, f"Video file not found: {video_path}"
        
        # Check file size (Gemini has limits)
        file_size_mb = video_file.stat().st_size / (1024 * 1024)
        max_size_mb = get_config_value(self.config, 'google_api.max_file_size_mb', 100)
        
        if file_size_mb > max_size_mb:
            return False, f"Video file too large ({file_size_mb:.1f}MB). Maximum: {max_size_mb}MB"
        
        # Check supported formats
        supported_formats = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']
        if video_file.suffix.lower() not in supported_formats:
            return False, f"Unsupported video format. Supported: {', '.join(supported_formats)}"
        
        return True, None
    
    def upload_video_file(self, video_path: str, display_name: Optional[str] = None) -> types.File:
        """
        Upload video file to Gemini for processing.
        
        Args:
            video_path: Path to local video file
            display_name: Optional display name for the file
            
        Returns:
            Uploaded file object from Gemini
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            Exception: If upload fails
        """
        # Validate file first
        is_valid, error_msg = self.validate_video_file(video_path)
        if not is_valid:
            raise ValueError(f"Video validation failed: {error_msg}")
        
        video_file = Path(video_path)
        if not display_name:
            display_name = f"video_analysis_{video_file.stem}"
        
        try:
            console.print(f"[yellow]📤 Uploading video file: {video_file.name}[/yellow]")
            
            # Upload using the SDK API v0.3.0 syntax
            uploaded_file = self.client.files.upload(
                path=str(video_path),
                config=types.UploadFileConfig(
                    display_name=display_name,
                    mime_type=self._get_mime_type(video_file.suffix)
                )
            )
            
            console.print(f"[green]✅ File uploaded successfully: {uploaded_file.name}[/green]")
            logger.info(f"Video uploaded - Name: {uploaded_file.name}, Size: {uploaded_file.size_bytes} bytes")
            
            return uploaded_file
            
        except Exception as e:
            logger.error(f"Video upload failed: {e}")
            raise Exception(f"Failed to upload video file: {e}")
    
    def wait_for_file_processing(self, uploaded_file: types.File, timeout_seconds: int = 300) -> types.File:
        """
        Wait for uploaded file to be processed and ready for analysis.
        
        Args:
            uploaded_file: The uploaded file object
            timeout_seconds: Maximum time to wait for processing
            
        Returns:
            File object when ready for analysis
            
        Raises:
            TimeoutError: If processing takes too long
            Exception: If file processing fails
        """
        start_time = time.time()
        
        # 🎯 移除Rich Progress以避免并发冲突
        console.print(f"[cyan]⠋ Processing video file...[/cyan]", end="")
        
        while True:
            # Check elapsed time
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise TimeoutError(f"File processing timeout after {timeout_seconds} seconds")
            
            # Get current file status
            try:
                file_info = self.client.files.get(name=uploaded_file.name)
                    
                # Use string comparison for file state in v0.3.0
                if file_info.state == "ACTIVE":
                    progress.update(task, description="✅ File ready for analysis")
                    console.print(f"[green]✅ Video file processed and ready for analysis[/green]")
                    return file_info
                elif file_info.state == "FAILED":
                    raise Exception(f"File processing failed: {file_info.error}")
                elif file_info.state == "PROCESSING":
                    progress.update(task, description=f"🔄 Processing... ({elapsed:.0f}s)")
                else:
                    progress.update(task, description=f"⏳ Status: {file_info.state} ({elapsed:.0f}s)")
                
            except Exception as e:
                logger.error(f"Error checking file status: {e}")
                raise Exception(f"Failed to check file processing status: {e}")
            
            # Wait before next check
            time.sleep(5)
    
    def analyze_video_content(
        self, 
        uploaded_file: types.File, 
        template_manager: TemplateManager, 
        template_name: str,
        **template_params
    ) -> GeminiAnalysisResult:
        """
        Analyze video content using specified template.
        
        Args:
            uploaded_file: Processed video file from Gemini
            template_manager: Template manager instance
            template_name: Name of the template to use
            **template_params: Parameters for template rendering
            
        Returns:
            Analysis result containing content and metadata
            
        Raises:
            ValueError: If template not found or invalid
            Exception: If analysis fails
        """
        try:
            console.print(f"[blue]🧠 Analyzing video with template: {template_name}[/blue]")
            
            # Render prompt template
            prompt = template_manager.render_prompt(template_name, **template_params)
            model_config = template_manager.get_model_config(template_name)
            
            # Get model name from config
            # 🎯 统一配置：使用统一的模型配置获取函数
            from ..config import get_default_model
            model_name = model_config.get('model', get_default_model(self.config))
            
            console.print(f"[cyan]📝 Using model: {model_name}[/cyan]")
            logger.info(f"Starting analysis with model: {model_name}, template: {template_name}")
            
            # Generate content using uploaded video file and prompt with proper role structure for v0.3.0
            response = self.client.models.generate_content(
                model=model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(prompt), 
                            types.Part.from_uri(
                                uploaded_file.uri, 
                                mime_type=uploaded_file.mime_type
                            )
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=model_config.get('temperature', 0.7),
                    max_output_tokens=model_config.get('max_tokens', 8192)
                )
            )
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini API")
            
            # Create analysis result
            result = GeminiAnalysisResult(
                content=response.text,
                metadata={
                    'model': model_name,
                    'template': template_name,
                    'file_name': uploaded_file.display_name,
                    'file_size_bytes': uploaded_file.size_bytes,
                    'template_params': template_params,
                    'model_config': model_config
                }
            )
            
            console.print(f"[green]✅ Analysis completed ({result.word_count} words)[/green]")
            logger.info(f"Analysis successful - Word count: {result.word_count}")
            
            return result
            
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            raise Exception(f"Failed to analyze video content: {e}")
    
    def cleanup_uploaded_file(self, uploaded_file: types.File) -> None:
        """
        Delete uploaded file from Gemini to free up resources.
        
        Args:
            uploaded_file: File to delete
        """
        try:
            self.client.files.delete(name=uploaded_file.name)
            console.print(f"[dim]🗑️  Cleaned up uploaded file: {uploaded_file.name}[/dim]")
            logger.info(f"File cleanup successful: {uploaded_file.name}")
        except Exception as e:
            logger.warning(f"File cleanup failed: {e}")
    
    def process_video_end_to_end(
        self,
        video_path: str,
        template_manager: TemplateManager,
        template_name: str,
        cleanup_file: bool = True,
        **template_params
    ) -> GeminiAnalysisResult:
        """
        Complete end-to-end video processing workflow.
        
        Args:
            video_path: Path to local video file
            template_manager: Template manager instance
            template_name: Template name for analysis
            cleanup_file: Whether to delete uploaded file after analysis
            **template_params: Template parameters
            
        Returns:
            Analysis result
            
        Raises:
            Various exceptions during processing pipeline
        """
        uploaded_file = None
        
        try:
            # Step 1: Upload video
            uploaded_file = self.upload_video_file(video_path)
            
            # Step 2: Wait for processing
            processed_file = self.wait_for_file_processing(uploaded_file)
            
            # Step 3: Analyze content
            result = self.analyze_video_content(
                processed_file, 
                template_manager, 
                template_name, 
                **template_params
            )
            
            return result
            
        finally:
            # Cleanup uploaded file if requested
            if cleanup_file and uploaded_file:
                self.cleanup_uploaded_file(uploaded_file)
    
    def _get_mime_type(self, file_extension: str) -> str:
        """Get MIME type for video file extension."""
        mime_types = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.m4v': 'video/x-m4v'
        }
        return mime_types.get(file_extension.lower(), 'video/mp4')
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the Gemini client configuration."""
        # 🎯 统一配置：使用统一的模型配置获取函数
        from ..config import get_default_model
        return {
            'client_initialized': self._client is not None,
            'api_configured': bool(get_config_value(self.config, 'google_api.api_key')),
            'max_file_size_mb': get_config_value(self.config, 'google_api.max_file_size_mb', 100),
            'default_model': get_config_value(self.config, 'google_api.model', get_default_model(self.config)),
            'sdk_version': genai.__version__ if hasattr(genai, '__version__') else 'unknown'
        }
