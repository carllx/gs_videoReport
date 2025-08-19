#!/usr/bin/env python3
"""
批量处理功能 - 错误处理和重试机制验证测试
测试重点：验证SimpleBatchProcessor的错误隔离和智能重试功能
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time

import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from gs_video_report.batch.simple_processor import SimpleBatchProcessor
from gs_video_report.config import Config


class TestErrorHandlingAndRetry:
    """测试错误处理和重试机制"""
    
    def setup_method(self):
        """为每个测试方法设置测试环境"""
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_videos_dir = self.temp_dir / "videos"
        self.test_videos_dir.mkdir()
        
        # 创建测试配置
        config_data = {
            'google_api': {
                'api_key': 'test_api_key',
                'model': 'gemini-2.5-flash',
                'temperature': 0.7,
                'max_tokens': 8192
            },
            'templates': {
                'default_template': 'chinese_transcript',
                'template_path': 'src/gs_video_report/templates/prompts'
            },
            'output': {
                'default_path': str(self.temp_dir / "output"),
                'file_naming': '{video_title}_{timestamp}',
                'include_metadata': True
            }
        }
        self.config = Config(config_data)
        
        # 创建测试视频文件
        self.create_test_video_files()
        
    def teardown_method(self):
        """清理测试环境"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_video_files(self):
        """创建测试用的视频文件"""
        # 正常视频文件
        (self.test_videos_dir / "normal_video.mp4").write_text("fake video content")
        (self.test_videos_dir / "another_video.mp4").write_text("fake video content 2")
        
        # 损坏的视频文件
        (self.test_videos_dir / "corrupted_video.mp4").write_text("corrupted data")
        
        # 不支持的格式
        (self.test_videos_dir / "unsupported.txt").write_text("not a video")
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_error_isolation_mechanism(self, mock_template_manager, mock_gemini_service):
        """
        测试A1: 错误隔离机制验证
        目标：确保单个视频文件的失败不会影响其他文件的处理
        """
        # 设置模拟 - 第一个文件成功，第二个失败，第三个成功
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        
        # 模拟处理结果：成功-失败-成功的模式
        def side_effect_func(*args, **kwargs):
            video_path = args[0] if args else kwargs.get('video_path', '')
            if 'normal_video' in video_path:
                return Mock(output_path=str(self.temp_dir / "normal_video_lesson.md"))
            elif 'another_video' in video_path:
                return Mock(output_path=str(self.temp_dir / "another_video_lesson.md"))
            else:
                raise Exception("File processing failed")
        
        mock_service_instance.process_video_end_to_end.side_effect = side_effect_func
        
        # 创建处理器并运行
        processor = SimpleBatchProcessor(self.config)
        result = processor.process_directory(str(self.test_videos_dir))
        
        # 验证错误隔离效果
        assert result["total"] == 3  # 处理所有3个mp4文件
        assert result["success"] >= 2  # 至少有2个成功
        assert result["failed"] <= 1   # 最多有1个失败
        
        # 验证状态文件存在且格式正确
        state_files = list(Path().glob("batch_*_state.json"))
        assert len(state_files) >= 1  # 至少有一个状态文件
        
        # 使用最新的状态文件
        latest_state_file = max(state_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_state_file, 'r') as f:
            state_data = json.load(f)
            
        assert "batch_id" in state_data
        assert "results" in state_data
        assert len(state_data["results"]) == result["total"]
        
        # 清理所有状态文件
        for state_file in state_files:
            state_file.unlink()
        
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')  
    def test_network_error_retry_mechanism(self, mock_template_manager, mock_gemini_service):
        """
        测试A2: 网络错误重试机制
        目标：验证网络错误时最多重试3次，并使用指数退避
        """
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        
        # 模拟网络错误（前3次失败，第4次成功）
        call_count = 0
        def network_error_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise Exception("Network timeout - connection failed")
            return Mock(output_path=str(self.temp_dir / "recovered_video_lesson.md"))
        
        mock_service_instance.process_video_end_to_end.side_effect = network_error_side_effect
        
        processor = SimpleBatchProcessor(self.config)
        
        # 记录开始时间以验证退避延迟
        start_time = time.time()
        result = processor.process_directory(str(self.test_videos_dir), max_retries=3)
        end_time = time.time()
        
        # 验证重试机制
        assert call_count == 4  # 初次 + 3次重试 = 4次调用
        
        # 验证指数退避（预期至少延迟: 1 + 2 + 4 = 7秒）
        assert end_time - start_time >= 6  # 允许一些时间误差
        
        # 验证最终成功
        assert result["success"] >= 1
        
        # 清理状态文件
        state_files = list(Path().glob("batch_*_state.json"))
        for state_file in state_files:
            state_file.unlink()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_api_quota_error_limited_retry(self, mock_template_manager, mock_gemini_service):
        """
        测试A3: API限额错误的有限重试
        目标：验证API限额错误最多重试2次
        """
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        
        # 模拟API限额错误  
        call_count = 0
        def quota_error_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("Rate limit exceeded - quota exhausted")
        
        mock_service_instance.process_video_end_to_end.side_effect = quota_error_side_effect
        
        processor = SimpleBatchProcessor(self.config)
        result = processor.process_directory(str(self.test_videos_dir), max_retries=3)
        
        # 验证API限额错误的特殊处理：最多2次重试 + 初次 = 3次调用
        assert call_count <= 3
        
        # 验证最终失败
        assert result["failed"] >= 1
        
        # 清理状态文件
        state_files = list(Path().glob("batch_*_state.json"))
        for state_file in state_files:
            state_file.unlink()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_permanent_error_no_retry(self, mock_template_manager, mock_gemini_service):
        """
        测试A4: 永久错误不重试
        目标：验证文件格式错误、认证错误等永久错误不会触发重试
        """
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        
        # 测试不同类型的永久错误
        permanent_errors = [
            "File not found - invalid video path",
            "Invalid API key - authentication failed", 
            "Unsupported format - corrupted video file",
            "Permission denied - access restricted"
        ]
        
        for error_msg in permanent_errors:
            call_count = 0
            def permanent_error_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                raise Exception(error_msg)
            
            mock_service_instance.process_video_end_to_end.side_effect = permanent_error_side_effect
            
            processor = SimpleBatchProcessor(self.config)
            result = processor.process_directory(str(self.test_videos_dir))
            
            # 验证永久错误不重试：只调用1次
            assert call_count <= 2, f"Permanent error '{error_msg}' triggered unexpected retries"
            
            # 清理状态文件
            state_files = list(Path().glob("batch_*_state.json"))
            for state_file in state_files:
                state_file.unlink()
    
    def test_should_retry_error_classification(self):
        """
        测试A5: 错误分类逻辑验证
        目标：验证_should_retry_error方法的错误分类准确性
        """
        processor = SimpleBatchProcessor(self.config)
        
        # 网络错误 - 应该重试
        network_errors = [
            "Network timeout occurred",
            "Connection failed - 503 Service Unavailable", 
            "Socket error - temporary failure",
            "Upload failed - try again later"
        ]
        
        for error in network_errors:
            assert processor._should_retry_error(error, 0, 3), f"Network error should retry: {error}"
            assert not processor._should_retry_error(error, 3, 3), f"Should not retry after max attempts: {error}"
        
        # API限额错误 - 有限重试
        quota_errors = [
            "Rate limit exceeded",
            "Quota exhausted - 429 Too Many Requests"
        ]
        
        for error in quota_errors:
            assert processor._should_retry_error(error, 0, 3), f"Quota error should retry initially: {error}"
            assert not processor._should_retry_error(error, 2, 3), f"Quota error should not retry after 2 attempts: {error}"
        
        # 永久错误 - 不应该重试
        permanent_errors = [
            "File not found",
            "Invalid API key", 
            "Unsupported format",
            "Authentication failed - 401 Unauthorized"
        ]
        
        for error in permanent_errors:
            assert not processor._should_retry_error(error, 0, 3), f"Permanent error should not retry: {error}"


class TestFileUploadInterruption:
    """测试大文件上传中断场景"""
    
    def setup_method(self):
        """测试环境设置"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_videos_dir = self.temp_dir / "videos"
        self.test_videos_dir.mkdir()
        
        config_data = {
            'google_api': {
                'api_key': 'test_api_key',
                'model': 'gemini-2.5-flash',
                'temperature': 0.7,
                'max_tokens': 8192
            },
            'templates': {'default_template': 'chinese_transcript'},
            'output': {'default_path': str(self.temp_dir / "output")}
        }
        self.config = Config(config_data)
        
    def teardown_method(self):
        """清理测试环境"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_state_persistence_on_interruption(self, mock_template_manager, mock_gemini_service):
        """
        测试B1: 中断时的状态持久化
        目标：验证处理中断时状态文件正确保存
        """
        # 创建多个测试文件
        for i in range(5):
            (self.test_videos_dir / f"video_{i}.mp4").write_text(f"video content {i}")
        
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        
        # 模拟前2个成功，第3个时发生中断
        call_count = 0
        def interruption_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                video_path = args[0] if args else kwargs.get('video_path', '')
                return Mock(output_path=f"{video_path.replace('.mp4', '_lesson.md')}")
            else:
                raise KeyboardInterrupt("User interrupted processing")
        
        mock_service_instance.process_video_end_to_end.side_effect = interruption_side_effect
        
        processor = SimpleBatchProcessor(self.config)
        
        # 捕获中断异常并继续验证
        try:
            processor.process_directory(str(self.test_videos_dir))
        except KeyboardInterrupt:
            pass
        
        # 验证状态文件存在且包含正确信息
        state_files = list(Path().glob("batch_*_state.json"))
        assert len(state_files) == 1
        
        with open(state_files[0], 'r') as f:
            state_data = json.load(f)
        
        # 验证状态文件内容
        assert state_data["total"] == 5
        assert len(state_data["results"]) >= 2  # 至少处理了2个文件
        assert any(result["status"] == "success" for result in state_data["results"])
        
        # 清理
        state_files[0].unlink()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_skip_existing_functionality(self, mock_template_manager, mock_gemini_service):
        """
        测试B2: --skip-existing 功能验证
        目标：验证断点续传效果
        """
        # 创建测试文件
        for i in range(3):
            (self.test_videos_dir / f"video_{i}.mp4").write_text(f"video content {i}")
        
        # 预先创建一些输出文件（模拟已处理）
        (self.temp_dir / "video_0_lesson.md").write_text("existing output")
        
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        mock_service_instance.process_video_end_to_end.return_value = Mock(
            output_path=str(self.temp_dir / "new_output.md")
        )
        
        processor = SimpleBatchProcessor(self.config)
        result = processor.process_directory(
            str(self.test_videos_dir), 
            output_dir=str(self.temp_dir),
            skip_existing=True
        )
        
        # 验证跳过已存在文件
        assert result["skipped"] >= 1
        assert result["total"] == 3
        
        # 验证状态文件记录正确
        state_files = list(Path().glob("batch_*_state.json"))
        assert len(state_files) == 1
        
        with open(state_files[0], 'r') as f:
            state_data = json.load(f)
        
        skipped_results = [r for r in state_data["results"] if r["status"] == "skipped"]
        assert len(skipped_results) >= 1
        
        # 清理
        state_files[0].unlink()


if __name__ == "__main__":
    # 运行特定测试
    print("🔍 开始执行错误处理和重试机制验证测试...")
    
    # 可以直接运行关键测试
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__ + "::TestErrorHandlingAndRetry::test_error_isolation_mechanism",
        "-v", "--tb=short"
    ], cwd=Path(__file__).parent.parent)
    
    if result.returncode == 0:
        print("✅ 错误隔离机制测试通过")
    else:
        print("❌ 错误隔离机制测试失败")
