"""
简化的Gemini服务 - 专注核心功能，避免过度开发
核心功能：视频上传、内容分析、文件清理、基本错误处理
"""
import time
import logging
import re
import json
from pathlib import Path
from typing import Dict, Any, Optional

from google import genai
from google.genai import types
from rich.console import Console

from ..template_manager import TemplateManager
from ..security.api_key_manager import api_key_manager
from ..security.multi_key_manager import get_multi_key_manager, MultiKeyManager
from .gemini_service import GeminiAnalysisResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Console for rich output
console = Console()


class SimpleGeminiService:
    """
    🎯 简化的Gemini服务 - 专注核心功能
    - 视频文件上传
    - Gemini 2.5 Pro内容分析
    - 429错误智能重试机制（支持exponential backoff）
    - API请求计数监控（免费层限制：100请求/天）
    - 多API密钥智能轮循和失效检测
    - 基本错误处理
    - 文件清理
    """
    
    def __init__(self, config: Dict[str, Any], api_keys: Optional[list] = None):
        """
        初始化简化Gemini服务
        
        Args:
            config: 配置字典
            api_keys: 可选的API密钥列表，启用多密钥轮循模式
        """
        self.config = config
        self._client = None
        self.current_api_key = None
        self.current_key_id = None
        
        # 重试配置
        self.max_retries = 3
        self.base_retry_delay = 30  # 基础重试延迟（秒）
        
        # API请求计数（免费层真实限制）
        self.daily_request_count = 0
        self.daily_request_limit = 100  # 免费层每日100请求限制
        
        # 多密钥管理器
        self.multi_key_mode = bool(api_keys)
        if self.multi_key_mode:
            self.multi_key_manager = get_multi_key_manager(api_keys)
            console.print(f"[cyan]🔄 启用多密钥轮循模式，管理 {len(api_keys)} 个API密钥[/cyan]")
        else:
            self.multi_key_manager = None
            console.print("[cyan]🔧 使用传统单密钥模式[/cyan]")
        
        self._setup_client()
    
    def _setup_client(self) -> None:
        """初始化Google Gen AI客户端"""
        try:
            if self.multi_key_mode and self.multi_key_manager:
                # 使用多密钥管理器
                api_key, key_id = self.multi_key_manager.get_current_api_key()
                self.current_api_key = api_key
                self.current_key_id = key_id
                masked_key = f"{key_id}"
                console.print(f"[blue]🔧 Gemini服务初始化成功 (多密钥模式, 当前密钥: {masked_key})[/blue]")
            else:
                # 使用传统单密钥模式
                api_key = api_key_manager.get_api_key(self.config)
                self.current_api_key = api_key
                self.current_key_id = "SINGLE_KEY"
                masked_key = api_key_manager.get_masked_api_key(api_key)
                console.print(f"[blue]🔧 Gemini服务初始化成功 (单密钥模式, API密钥: {masked_key})[/blue]")
            
            self._client = genai.Client(api_key=api_key, vertexai=False)
            console.print(f"[yellow]⚠️  免费层限制: {self.daily_request_limit}请求/天，当前已用: {self.daily_request_count}[/yellow]")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise Exception(f"Gemini client initialization failed: {e}")
    
    def _rotate_api_key(self) -> bool:
        """
        轮换到下一个API密钥
        
        Returns:
            bool: 是否成功轮换
        """
        if not self.multi_key_mode or not self.multi_key_manager:
            logger.warning("⚠️ 非多密钥模式，无法轮换密钥")
            return False
        
        try:
            if self.multi_key_manager.rotate_to_next_key():
                # 重新设置客户端
                api_key, key_id = self.multi_key_manager.get_current_api_key()
                self.current_api_key = api_key
                self.current_key_id = key_id
                self._client = genai.Client(api_key=api_key, vertexai=False)
                console.print(f"[blue]🔄 API密钥轮换成功，切换至: {key_id}[/blue]")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"API密钥轮换失败: {e}")
            return False
    
    def _record_api_call(self, success: bool, error_type: Optional[str] = None):
        """
        记录API调用结果
        
        Args:
            success: 是否成功
            error_type: 错误类型（如果失败）
        """
        if self.multi_key_mode and self.multi_key_manager and self.current_key_id:
            self.multi_key_manager.record_api_call(self.current_key_id, success, error_type)
    
    @property
    def client(self) -> genai.Client:
        """获取Gemini客户端实例"""
        if not self._client:
            raise RuntimeError("Gemini client not initialized")
        return self._client
    
    def upload_video_file(self, video_path: str, display_name: Optional[str] = None) -> types.File:
        """
        🎯 简单视频文件上传
        
        Args:
            video_path: 视频文件路径
            display_name: 显示名称
            
        Returns:
            types.File: 上传的文件对象
        """
        video_file = Path(video_path)
        
        # 基本验证
        if not video_file.exists():
            raise ValueError(f"视频文件不存在: {video_path}")
        
        if not display_name:
            display_name = f"video_{video_file.stem}"
        
        try:
            # 检查API请求配额
            if self._check_request_quota():
                console.print(f"[red]❌ 已达到免费层日请求限制({self.daily_request_limit})，停止处理[/red]")
                raise Exception(f"已达到API日请求限制({self.daily_request_limit}请求)")
            
            console.print(f"[yellow]📤 上传视频文件: {video_file.name}[/yellow]")
            
            uploaded_file = self.client.files.upload(
                path=str(video_path),
                config=types.UploadFileConfig(
                    display_name=display_name,
                    mime_type=self._get_mime_type(video_file.suffix)
                )
            )
            
            # 记录API请求
            self._increment_request_count("file_upload")
            self._record_api_call(success=True)
            
            console.print(f"[blue]⬆️ 文件上传成功: {uploaded_file.name}[/blue]")
            return uploaded_file
            
        except Exception as e:
            logger.error(f"Video upload failed: {e}")
            self._record_api_call(success=False, error_type=str(e))
            raise Exception(f"视频上传失败: {e}")
    
    def wait_for_file_processing(self, uploaded_file: types.File, timeout_seconds: int = 600) -> types.File:
        """
        🎯 等待文件处理完成
        
        Args:
            uploaded_file: 上传的文件对象
            timeout_seconds: 超时时间（秒）
            
        Returns:
            types.File: 处理完成的文件对象
        """
        start_time = time.time()
        console.print(f"[cyan]⠋ 等待文件处理...[/cyan]")
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise TimeoutError(f"文件处理超时 ({timeout_seconds}秒)")
            
            try:
                file_info = self.client.files.get(name=uploaded_file.name)
                
                # 记录API请求（状态检查）
                self._increment_request_count("file_status_check")
                self._record_api_call(success=True)
                
                if file_info.state == "ACTIVE":
                    console.print(f"[blue]📹 视频文件处理完成，可以开始分析[/blue]")
                    return file_info
                elif file_info.state == "FAILED":
                    error_msg = getattr(file_info, 'error', 'Unknown error')
                    raise Exception(f"文件处理失败: {error_msg}")
                
                # 简单进度显示
                console.print(f"\r[cyan]⠋ 处理中... ({elapsed:.0f}s)[/cyan]", end="")
                    
            except Exception as e:
                logger.error(f"Error checking file status: {e}")
                self._record_api_call(success=False, error_type=str(e))
                raise Exception(f"检查文件处理状态失败: {e}")
                
            # 🎯 优化：减少API请求频率，延长检查间隔
            time.sleep(10)  # 从5秒增加到10秒，减少状态检查请求
    
    def _extract_retry_delay_from_error(self, error_str: str) -> Optional[int]:
        """
        🎯 从API错误响应中提取重试延迟时间
        
        Args:
            error_str: 错误信息字符串
            
        Returns:
            Optional[int]: 重试延迟秒数，如果无法提取则返回None
        """
        try:
            # 查找RetryInfo中的retryDelay字段
            retry_pattern = r"'retryDelay':\s*'(\d+)s'"
            match = re.search(retry_pattern, error_str)
            if match:
                return int(match.group(1))
            
            # 备用模式：查找数字+s的模式
            delay_pattern = r"(\d+)s"
            match = re.search(delay_pattern, error_str)
            if match:
                return int(match.group(1))
                
        except Exception as e:
            logger.warning(f"Failed to extract retry delay: {e}")
        
        return None
    
    def _is_quota_exhausted_error(self, error_str: str) -> bool:
        """检查是否为配额耗尽错误"""
        quota_indicators = [
            "RESOURCE_EXHAUSTED",
            "exceeded your current quota",
            "quota_failure",
            "QuotaFailure",
            "429"
        ]
        return any(indicator.lower() in error_str.lower() for indicator in quota_indicators)
    
    def _is_retryable_error(self, error_str: str) -> bool:
        """检查是否为可重试的错误"""
        retryable_indicators = [
            "429",
            "RESOURCE_EXHAUSTED", 
            "rate limit",
            "quota",
            "temporarily unavailable",
            "service unavailable"
        ]
        return any(indicator.lower() in error_str.lower() for indicator in retryable_indicators)
    
    def _handle_quota_exhausted_error(self, error_str: str, attempt: int) -> bool:
        """
        🎯 处理配额耗尽错误
        
        Args:
            error_str: 错误信息
            attempt: 当前重试次数
            
        Returns:
            bool: 是否应该继续重试
        """
        console.print(f"[red]💸 API配额耗尽 (尝试 {attempt}/{self.max_retries})[/red]")
        
        # 提取API建议的重试延迟
        suggested_delay = self._extract_retry_delay_from_error(error_str)
        
        if attempt >= self.max_retries:
            console.print("[red]❌ 已达到最大重试次数，停止重试[/red]")
            console.print("[yellow]💡 真实配额限制说明：[/yellow]")
            console.print("   🚨 免费层每天只能发送100个API请求")
            console.print("   📊 每个视频需要4-5个请求（上传+状态检查+分析）")
            console.print("   🎯 所以免费层每天只能处理约20-25个视频")
            console.print("[yellow]💡 建议解决方案：[/yellow]")
            console.print("   1. 等待24小时让请求配额重置（每天100个请求）")
            console.print("   2. 升级到付费API账户（更高请求限制）")
            console.print("   3. 使用其他API密钥")
            console.print("   4. 优化批量处理策略（减少API调用频率）")
            return False
        
        # 计算重试延迟：使用API建议延迟或指数退避
        if suggested_delay:
            retry_delay = suggested_delay
            console.print(f"[cyan]⏰ 使用API建议的重试延迟: {retry_delay}秒[/cyan]")
        else:
            # 指数退避策略：30s, 60s, 120s
            retry_delay = self.base_retry_delay * (2 ** (attempt - 1))
            console.print(f"[cyan]⏰ 使用指数退避重试延迟: {retry_delay}秒[/cyan]")
        
        console.print(f"[yellow]🔄 第{attempt}次重试，等待{retry_delay}秒后继续...[/yellow]")
        
        # 显示倒计时
        for remaining in range(retry_delay, 0, -10):
            console.print(f"\r[dim]⏳ 重试倒计时: {remaining}秒[/dim]", end="")
            time.sleep(min(10, remaining))
        
        console.print(f"\r[yellow]🔄 开始第{attempt}次重试...[/yellow]")
        return True
    
    def analyze_video_content(self,
                            uploaded_file: types.File,
                            template_manager: TemplateManager,
                            template_name: str,
                            preferred_model: str = "gemini-2.5-pro",
                            **template_params) -> GeminiAnalysisResult:
        """
        🎯 简单视频内容分析 - 支持429错误智能重试
        
        Args:
            uploaded_file: 已上传的视频文件
            template_manager: 模板管理器
            template_name: 模板名称
            preferred_model: 模型名称（默认gemini-2.5-pro）
            **template_params: 模板参数
            
        Returns:
            GeminiAnalysisResult: 分析结果
        """
        start_time = time.time()
        
        # 检查API请求配额
        if self._check_request_quota():
            console.print(f"[red]❌ 已达到免费层日请求限制({self.daily_request_limit})，停止处理[/red]")
            raise Exception(f"已达到API日请求限制({self.daily_request_limit}请求)")
        
        # 渲染提示模板（在重试循环外，避免重复计算）
        prompt = template_manager.render_prompt(template_name, **template_params)
        model_config = template_manager.get_model_config(template_name)
        
        # 真实限制提醒（不是成本，是请求数量）
        remaining_requests = self.daily_request_limit - self.daily_request_count
        console.print(f"[cyan]📊 剩余API请求数: {remaining_requests}/{self.daily_request_limit}[/cyan]")
        
        # 🎯 重试循环 - 处理429错误
        for attempt in range(1, self.max_retries + 1):
            try:
                console.print(f"[blue]🧠 使用模型分析视频: {preferred_model} (尝试 {attempt}/{self.max_retries})[/blue]")
                
                # 生成内容
                response = self.client.models.generate_content(
                    model=preferred_model,
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
                
                # 记录API请求（内容生成）
                self._increment_request_count("content_generation")
                
                if not response or not response.text:
                    raise Exception("API返回空响应")
                
                # 🎉 成功：记录成功的API调用并计算处理时间
                self._record_api_call(success=True)
                processing_time = time.time() - start_time
                requests_used = self.daily_request_count  # 记录使用的请求数
                
                result = GeminiAnalysisResult(
                    content=response.text,
                    metadata={
                        'model': preferred_model,
                        'template': template_name,
                        'file_name': uploaded_file.display_name,
                        'file_size_bytes': uploaded_file.size_bytes,
                        'processing_time_seconds': processing_time,
                        'api_requests_used': requests_used,  # 记录请求数而不是成本
                        'remaining_daily_requests': self.daily_request_limit - requests_used,
                        'retry_attempts': attempt - 1,  # 记录重试次数
                        'current_api_key_id': self.current_key_id if self.multi_key_mode else 'SINGLE_KEY'
                    }
                )
                
                success_msg = f"[green]✅ 分析完成 ({result.word_count} 字, 用{requests_used}个请求)"
                if attempt > 1:
                    success_msg += f" [重试{attempt-1}次后成功]"
                if self.multi_key_mode:
                    success_msg += f" [密钥: {self.current_key_id}]"
                success_msg += "[/green]"
                console.print(success_msg)
                
                return result
                
            except Exception as e:
                error_str = str(e)
                logger.error(f"Video analysis failed (attempt {attempt}): {e}")
                
                # 记录失败的API调用
                self._record_api_call(success=False, error_type=error_str)
                
                # 🔍 检查是否为可重试的错误
                if self._is_retryable_error(error_str):
                    if self._is_quota_exhausted_error(error_str):
                        # 处理配额耗尽错误 - 尝试轮换密钥
                        if self.multi_key_mode and self._rotate_api_key():
                            console.print(f"[cyan]🔄 密钥轮换成功，继续使用新密钥重试...[/cyan]")
                            continue  # 使用新密钥立即重试
                        else:
                            # 单密钥模式或轮换失败，使用传统重试机制
                            should_retry = self._handle_quota_exhausted_error(error_str, attempt)
                            if not should_retry:
                                break
                    else:
                        # 其他可重试错误（如网络问题）
                        if attempt < self.max_retries:
                            # 如果是多密钥模式，也可以尝试轮换
                            if self.multi_key_mode and attempt > 1:
                                if self._rotate_api_key():
                                    console.print(f"[cyan]🔄 轮换密钥后继续重试...[/cyan]")
                                    continue
                            
                            console.print(f"[yellow]🔄 检测到可重试错误，等待{self.base_retry_delay}秒后重试...[/yellow]")
                            time.sleep(self.base_retry_delay)
                            continue
                        else:
                            console.print(f"[red]❌ 达到最大重试次数，停止重试[/red]")
                            break
                else:
                    # 不可重试的错误（如文件格式问题）
                    console.print(f"[red]❌ 检测到不可重试错误，直接失败[/red]")
                    break
        
        # 所有重试都失败了
        final_error = f"视频分析失败（已重试{self.max_retries}次）: {error_str}"
        logger.error(final_error)
        raise Exception(final_error)
    
    def print_usage_report(self):
        """打印API密钥使用情况报告"""
        if self.multi_key_mode and self.multi_key_manager:
            self.multi_key_manager.print_usage_report()
        else:
            print("\n" + "="*60)
            print("📊 单密钥模式使用报告")
            print("="*60)
            print(f"API请求计数: {self.daily_request_count}/{self.daily_request_limit}")
            print(f"剩余请求数: {self.daily_request_limit - self.daily_request_count}")
            print(f"当前密钥: {self.current_key_id}")
            print("="*60)
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """获取使用情况摘要"""
        if self.multi_key_mode and self.multi_key_manager:
            return self.multi_key_manager.get_usage_summary()
        else:
            return {
                "mode": "single_key",
                "total_requests": self.daily_request_count,
                "remaining_requests": self.daily_request_limit - self.daily_request_count,
                "current_key_id": self.current_key_id
            }
    
    def process_video_end_to_end_enhanced(self,
                                        video_path: str,
                                        template_manager: TemplateManager,
                                        template_name: str,
                                        preferred_model: Optional[str] = None,
                                        enable_fallback: bool = True,
                                        cleanup_file: bool = True,
                                        **template_params) -> GeminiAnalysisResult:
        """
        🎯 简化的端到端视频处理
        
        Args:
            video_path: 视频文件路径
            template_manager: 模板管理器
            template_name: 模板名称
            preferred_model: 首选模型（强制使用gemini-2.5-pro）
            enable_fallback: 忽略此参数（简化版本不支持回退）
            cleanup_file: 是否清理上传的文件
            **template_params: 模板参数
            
        Returns:
            GeminiAnalysisResult: 分析结果
        """
        uploaded_file = None
        
        # 🎯 强制使用Gemini 2.5 Pro
        if not preferred_model:
            from ..config import get_default_model
            preferred_model = get_default_model(self.config)
        
        try:
            console.print(f"[bold cyan]🚀 开始增强型视频处理: {Path(video_path).name}[/bold cyan]")
            
            # 步骤1: 上传视频
            uploaded_file = self.upload_video_file(video_path)
            
            # 步骤2: 等待文件处理
            processed_file = self.wait_for_file_processing(uploaded_file)
            
            # 步骤3: 分析内容
            result = self.analyze_video_content(
                processed_file,
                template_manager,
                template_name,
                preferred_model,
                **template_params
            )
            
            return result
            
        finally:
            # 清理上传的文件
            if cleanup_file and uploaded_file:
                self.cleanup_uploaded_file(uploaded_file)
    
    def cleanup_uploaded_file(self, uploaded_file: types.File) -> None:
        """🎯 清理上传的文件"""
        try:
            self.client.files.delete(name=uploaded_file.name)
            console.print(f"[dim]🗑️  已清理上传文件: {uploaded_file.name}[/dim]")
        except Exception as e:
            logger.warning(f"File cleanup failed: {e}")
    
    def _get_mime_type(self, file_extension: str) -> str:
        """获取视频文件的MIME类型"""
        mime_types = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.m4v': 'video/x-m4v'
        }
        return mime_types.get(file_extension.lower(), 'video/mp4')
    
    def _check_request_quota(self) -> bool:
        """
        🎯 检查是否接近API请求配额限制
        
        Returns:
            bool: True表示已接近或超过限制，应停止处理
        """
        remaining = self.daily_request_limit - self.daily_request_count
        
        if remaining <= 0:
            return True
        elif remaining <= 10:  # 剩余少于10个请求时警告
            console.print(f"[yellow]⚠️  API请求配额即将耗尽，剩余{remaining}个[/yellow]")
        
        return False
    
    def _increment_request_count(self, request_type: str) -> None:
        """
        🎯 增加API请求计数
        
        Args:
            request_type: 请求类型（用于调试）
        """
        self.daily_request_count += 1
        
        if self.daily_request_count % 10 == 0:  # 每10个请求显示一次
            remaining = self.daily_request_limit - self.daily_request_count
            console.print(f"[dim]📊 API请求: {self.daily_request_count}/{self.daily_request_limit} (剩余{remaining})[/dim]")
