"""
简单但健壮的批量处理器
专注于错误处理和重试机制
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import traceback

from ..services.gemini_service import GeminiService
from ..config import Config
from ..template_manager import TemplateManager
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

class SimpleBatchProcessor:
    """简单但健壮的批量处理器 - 专注于可靠性"""
    
    def __init__(self, config: Config):
        self.config = config
        self.gemini_service = GeminiService(config)
        self.template_manager = TemplateManager(config.data)
        self.state_file = None
        
    def process_directory(self, 
                         input_dir: str, 
                         template_name: str = "chinese_transcript",
                         output_dir: Optional[str] = None,
                         skip_existing: bool = False,
                         max_retries: int = 3) -> Dict[str, Any]:
        """
        处理目录中的所有视频文件
        
        Args:
            input_dir: 输入视频目录
            template_name: 处理模板
            output_dir: 输出目录 
            skip_existing: 是否跳过已存在的输出文件
            max_retries: 最大重试次数
            
        Returns:
            处理结果统计
        """
        
        # 1. 扫描视频文件
        video_files = self._scan_video_files(input_dir)
        if not video_files:
            console.print("[yellow]⚠️  在指定目录中没有找到视频文件[/yellow]")
            return {"total": 0, "success": 0, "failed": 0, "skipped": 0}
        
        console.print(f"[cyan]📁 发现 {len(video_files)} 个视频文件[/cyan]")
        
        # 2. 创建状态文件
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.state_file = Path(f"{batch_id}_state.json")
        
        # 3. 初始化统计
        stats = {
            "batch_id": batch_id,
            "total": len(video_files),
            "success": 0,
            "failed": 0, 
            "skipped": 0,
            "start_time": datetime.now().isoformat(),
            "results": []
        }
        
        # 4. 开始处理 - 使用进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("处理视频中...", total=len(video_files))
            
            for i, video_file in enumerate(video_files):
                progress.update(task, description=f"处理: {video_file.name}")
                
                # 处理单个视频 (带重试和错误隔离)
                result = self._process_single_video_safe(
                    video_file, 
                    template_name, 
                    output_dir,
                    skip_existing,
                    max_retries
                )
                
                # 更新统计
                if result["status"] == "success":
                    stats["success"] += 1
                    console.print(f"✅ [{i+1}/{len(video_files)}] {video_file.name}")
                elif result["status"] == "skipped":
                    stats["skipped"] += 1
                    console.print(f"⏭️  [{i+1}/{len(video_files)}] {video_file.name} (已存在)")
                else:
                    stats["failed"] += 1
                    console.print(f"❌ [{i+1}/{len(video_files)}] {video_file.name} - {result['error']}")
                
                stats["results"].append(result)
                
                # 立即保存状态 (关键：防止数据丢失)
                self._save_state(stats)
                
                progress.update(task, advance=1)
        
        # 5. 完成处理
        stats["end_time"] = datetime.now().isoformat()
        self._save_state(stats)
        
        return stats
    
    def _process_single_video_safe(self, 
                                   video_file: Path, 
                                   template_name: str,
                                   output_dir: Optional[str],
                                   skip_existing: bool,
                                   max_retries: int) -> Dict[str, Any]:
        """
        安全的单视频处理 - 完全错误隔离
        这是整个系统的核心：确保单个视频的问题不会影响批量处理
        """
        
        result = {
            "video_path": str(video_file),
            "video_name": video_file.name,
            "status": "unknown",
            "output_path": None,
            "error": None,
            "attempts": 0,
            "processed_at": datetime.now().isoformat()
        }
        
        try:
            # 检查是否跳过已存在的文件
            if skip_existing:
                expected_output = self._get_expected_output_path(video_file, output_dir)
                if expected_output and Path(expected_output).exists():
                    result["status"] = "skipped"
                    result["output_path"] = str(expected_output)
                    return result
            
            # 重试循环 - 处理网络中断和临时错误
            last_error = None
            for attempt in range(max_retries + 1):
                result["attempts"] = attempt + 1
                
                try:
                    # 使用现有的 GeminiService 处理视频
                    processing_result = self.gemini_service.process_video_end_to_end(
                        video_path=str(video_file),
                        template_manager=self.template_manager,
                        template_name=template_name,
                        cleanup_file=True
                    )
                    
                    # 成功处理
                    result["status"] = "success"
                    result["output_path"] = getattr(processing_result, 'output_path', 
                                                   self._get_expected_output_path(video_file, output_dir))
                    return result
                    
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    
                    # 错误分类 - 决定是否重试
                    should_retry = self._should_retry_error(error_str, attempt, max_retries)
                    
                    if should_retry:
                        # 指数退避策略
                        sleep_time = min(2 ** attempt, 16)  # 最大16秒
                        console.print(f"⚠️  网络错误，{sleep_time}秒后第{attempt+2}次重试: {video_file.name}")
                        time.sleep(sleep_time)
                        continue
                    else:
                        # 不可重试的错误，直接失败
                        break
            
            # 所有重试都失败了
            result["status"] = "failed"
            result["error"] = str(last_error)
            return result
            
        except Exception as e:
            # 捕获所有其他异常 - 确保不会崩溃整个批量处理
            result["status"] = "failed"
            result["error"] = f"处理异常: {str(e)}"
            console.print(f"[red]💥 严重错误: {video_file.name} - {e}[/red]")
            return result
    
    def _should_retry_error(self, error_str: str, attempt: int, max_retries: int) -> bool:
        """
        智能错误分类 - 判断是否应该重试
        
        这是错误处理的核心：区分临时错误和永久错误
        """
        error_lower = error_str.lower()
        
        # 网络相关错误 - 应该重试
        network_keywords = [
            "network", "timeout", "connection", "503", "502", "504", 
            "temporary failure", "try again", "upload failed", "socket"
        ]
        if any(keyword in error_lower for keyword in network_keywords):
            return attempt < max_retries
        
        # API限额错误 - 短暂重试
        if "quota" in error_lower or "rate limit" in error_lower or "429" in error_lower:
            return attempt < 2  # 最多重试2次
        
        # 文件相关错误 - 不重试
        permanent_keywords = [
            "file not found", "permission denied", "invalid format", 
            "unsupported format", "corrupted", "access denied", "no such file"
        ]
        if any(keyword in error_lower for keyword in permanent_keywords):
            return False
        
        # API认证错误 - 不重试
        auth_keywords = ["invalid api key", "authentication", "unauthorized", "401", "403"]
        if any(keyword in error_lower for keyword in auth_keywords):
            return False
        
        # Gemini API 特定错误 - 不重试
        gemini_keywords = ["invalid video", "video too large", "unsupported video format"]
        if any(keyword in error_lower for keyword in gemini_keywords):
            return False
        
        # 其他未知错误 - 保守重试1次
        return attempt < 1
    
    def _scan_video_files(self, input_dir: str) -> List[Path]:
        """扫描目录中的视频文件"""
        supported_formats = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        video_files = []
        
        input_path = Path(input_dir)
        if not input_path.exists():
            console.print(f"[red]❌ 目录不存在: {input_dir}[/red]")
            return []
        
        for ext in supported_formats:
            video_files.extend(input_path.glob(f"*{ext}"))
            video_files.extend(input_path.glob(f"*{ext.upper()}"))
        
        return sorted(video_files)
    
    def _get_expected_output_path(self, video_file: Path, output_dir: Optional[str]) -> Optional[str]:
        """获取预期的输出文件路径"""
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = video_file.parent
        
        # 简单的文件名转换: video.mp4 -> video_lesson.md
        output_name = f"{video_file.stem}_lesson.md"
        return str(output_path / output_name)
    
    def _save_state(self, stats: Dict[str, Any]):
        """保存处理状态到JSON文件"""
        if self.state_file:
            try:
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False)
            except Exception as e:
                console.print(f"[yellow]⚠️  状态保存失败: {e}[/yellow]")
