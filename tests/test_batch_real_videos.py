#!/usr/bin/env python3
"""
批量处理功能 - 基于真实Figma教程视频的QA测试
使用test_videos目录中的真实视频文件进行测试
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
import time

import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from gs_video_report.batch.simple_processor import SimpleBatchProcessor
from gs_video_report.config import Config


class TestBatchProcessingWithRealVideos:
    """基于真实视频文件的批量处理测试"""
    
    def setup_method(self):
        """测试环境设置 - 使用真实的test_videos目录"""
        self.project_root = Path(__file__).parent.parent
        self.test_videos_dir = self.project_root / "test_videos"
        
        # 验证真实视频文件存在
        if not self.test_videos_dir.exists():
            pytest.skip("真实视频目录不存在，跳过测试")
        
        # 获取所有真实视频文件
        self.video_files = list(self.test_videos_dir.glob("*.mp4"))
        if len(self.video_files) == 0:
            pytest.skip("没有找到真实视频文件，跳过测试")
        
        print(f"📁 发现 {len(self.video_files)} 个真实Figma教程视频")
        
        # 创建临时输出目录
        self.temp_output_dir = Path(tempfile.mkdtemp())
        
        # 创建真实配置
        config_data = {
            'google_api': {
                'api_key': 'test_api_key_for_qa',  # 将被mock
                'model': 'gemini-2.5-flash',
                'temperature': 0.7,
                'max_tokens': 8192
            },
            'templates': {
                'default_template': 'chinese_transcript',
                'template_path': 'src/gs_video_report/templates/prompts'
            },
            'output': {
                'default_path': str(self.temp_output_dir),
                'file_naming': '{video_title}_{timestamp}',
                'include_metadata': True
            }
        }
        self.config = Config(config_data)
        
        # 清理之前的状态文件
        self._cleanup_state_files()
        
    def teardown_method(self):
        """清理测试环境"""
        if self.temp_output_dir.exists():
            shutil.rmtree(self.temp_output_dir)
        self._cleanup_state_files()
    
    def _cleanup_state_files(self):
        """清理状态文件"""
        state_files = list(self.project_root.glob("batch_*_state.json"))
        for state_file in state_files:
            try:
                state_file.unlink()
            except FileNotFoundError:
                pass
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_real_video_error_isolation(self, mock_template_manager, mock_gemini_service):
        """
        测试1: 真实视频错误隔离机制
        目标：使用真实视频验证错误隔离功能
        """
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        
        # 模拟部分成功、部分失败的场景
        call_count = 0
        def realistic_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            video_path = args[0] if args else kwargs.get('video_path', '')
            
            # 模拟：前几个成功，中间几个失败，后面几个成功
            if call_count % 4 == 0:  # 每4个中有1个失败
                raise Exception(f"模拟处理失败: {Path(video_path).name}")
            else:
                return Mock(output_path=video_path.replace('.mp4', '_lesson.md'))
        
        mock_service_instance.process_video_end_to_end.side_effect = realistic_side_effect
        
        # 执行批量处理
        processor = SimpleBatchProcessor(self.config)
        result = processor.process_directory(str(self.test_videos_dir), output_dir=str(self.temp_output_dir))
        
        # 验证结果
        expected_total = len(self.video_files)  # 应该是20个视频文件
        
        assert result["total"] == expected_total, f"处理视频数量不符: {result['total']} != {expected_total}"
        assert result["success"] >= int(expected_total * 0.7), f"成功率过低: {result['success']}/{expected_total}"
        assert result["failed"] <= int(expected_total * 0.3), f"失败率过高: {result['failed']}/{expected_total}"
        
        # 验证错误隔离：成功的视频不受失败视频影响
        assert result["success"] + result["failed"] + result["skipped"] == result["total"]
        
        # 验证状态文件
        state_files = list(self.project_root.glob("batch_*_state.json"))
        assert len(state_files) >= 1
        
        with open(state_files[0], 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        
        assert state_data["total"] == expected_total
        assert len(state_data["results"]) == expected_total
        
        print(f"✅ 错误隔离测试通过 - 成功: {result['success']}, 失败: {result['failed']}")
        
        self._cleanup_state_files()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_real_video_retry_mechanism(self, mock_template_manager, mock_gemini_service):
        """
        测试2: 真实视频重试机制验证
        目标：验证网络错误时的重试功能
        """
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        
        # 测试前3个视频的重试机制
        test_videos = self.video_files[:3]
        test_videos_dir = self.temp_output_dir / "test_subset"
        test_videos_dir.mkdir()
        
        # 复制前3个视频到测试目录（建立软链接避免复制大文件）
        for video in test_videos:
            link_path = test_videos_dir / video.name
            link_path.symlink_to(video)
        
        # 模拟网络错误重试
        retry_counts = {}
        def retry_side_effect(*args, **kwargs):
            video_path = args[0] if args else kwargs.get('video_path', '')
            video_name = Path(video_path).name
            
            if video_name not in retry_counts:
                retry_counts[video_name] = 0
            retry_counts[video_name] += 1
            
            # 前2次失败（网络错误），第3次成功
            if retry_counts[video_name] <= 2:
                raise Exception("Network timeout - connection failed")
            else:
                return Mock(output_path=video_path.replace('.mp4', '_lesson.md'))
        
        mock_service_instance.process_video_end_to_end.side_effect = retry_side_effect
        
        # 记录开始时间
        start_time = time.time()
        
        processor = SimpleBatchProcessor(self.config)
        result = processor.process_directory(str(test_videos_dir), max_retries=3)
        
        end_time = time.time()
        
        # 验证重试机制
        assert result["total"] == 3
        assert result["success"] == 3  # 最终都应该成功
        
        # 验证每个视频都重试了3次
        for video_name, count in retry_counts.items():
            assert count == 3, f"{video_name} 重试次数不正确: {count} != 3"
        
        # 验证指数退避延迟（应该有足够的延迟时间）
        expected_min_delay = 3 * (1 + 2 + 4)  # 3个视频 * (1+2+4秒退避)
        actual_duration = end_time - start_time
        assert actual_duration >= expected_min_delay * 0.8, f"重试延迟时间不足: {actual_duration:.2f}s < {expected_min_delay}s"
        
        print(f"✅ 重试机制测试通过 - 处理时间: {actual_duration:.2f}s, 重试统计: {retry_counts}")
        
        self._cleanup_state_files()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_real_video_skip_existing(self, mock_template_manager, mock_gemini_service):
        """
        测试3: 真实视频跳过已存在文件功能
        目标：验证--skip-existing参数的断点续传效果
        """
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        mock_service_instance.process_video_end_to_end.return_value = Mock(
            output_path="new_output.md"
        )
        
        # 使用前5个视频进行测试
        test_videos = self.video_files[:5]
        test_videos_dir = self.temp_output_dir / "skip_test"
        test_videos_dir.mkdir()
        
        # 创建软链接
        for video in test_videos:
            link_path = test_videos_dir / video.name
            link_path.symlink_to(video)
        
        # 预先创建一些"已处理"的输出文件
        pre_existing_files = [
            test_videos[0].stem + "_lesson.md",  # 第1个视频的输出
            test_videos[2].stem + "_lesson.md",  # 第3个视频的输出
        ]
        
        for filename in pre_existing_files:
            output_file = self.temp_output_dir / filename
            output_file.write_text("已存在的输出内容")
        
        # 执行批量处理（启用跳过已存在文件）
        processor = SimpleBatchProcessor(self.config)
        result = processor.process_directory(
            str(test_videos_dir), 
            output_dir=str(self.temp_output_dir),
            skip_existing=True
        )
        
        # 验证跳过功能
        assert result["total"] == 5
        assert result["skipped"] == 2  # 应该跳过2个已存在的文件
        assert result["success"] == 3   # 处理3个新文件
        assert result["failed"] == 0
        
        # 验证状态文件记录正确
        state_files = list(self.project_root.glob("batch_*_state.json"))
        with open(state_files[0], 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        
        skipped_results = [r for r in state_data["results"] if r["status"] == "skipped"]
        success_results = [r for r in state_data["results"] if r["status"] == "success"]
        
        assert len(skipped_results) == 2
        assert len(success_results) == 3
        
        print(f"✅ 跳过已存在文件测试通过 - 跳过: {result['skipped']}, 新处理: {result['success']}")
        
        self._cleanup_state_files()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_real_video_performance_benchmark(self, mock_template_manager, mock_gemini_service):
        """
        测试4: 真实视频性能基准测试
        目标：建立基于真实20个Figma视频的性能基准
        """
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        
        # 模拟真实的处理延迟
        def realistic_processing_simulation(*args, **kwargs):
            video_path = args[0] if args else kwargs.get('video_path', '')
            video_file = Path(video_path)
            
            # 基于文件名模拟不同的处理时间
            base_delay = 0.5  # 基础延迟
            
            # 根据文件名长度和内容模拟处理复杂度
            complexity_factor = len(video_file.name) / 100.0
            processing_delay = base_delay + complexity_factor
            
            time.sleep(processing_delay)
            return Mock(output_path=video_path.replace('.mp4', '_lesson.md'))
        
        mock_service_instance.process_video_end_to_end.side_effect = realistic_processing_simulation
        
        # 执行性能测试
        start_time = time.time()
        processor = SimpleBatchProcessor(self.config)
        result = processor.process_directory(str(self.test_videos_dir), output_dir=str(self.temp_output_dir))
        end_time = time.time()
        
        total_duration = end_time - start_time
        
        # 性能基准验证
        expected_video_count = 20
        assert result["total"] == expected_video_count
        assert result["success"] == expected_video_count  # 应该全部成功
        
        # 吞吐量计算
        throughput = result["total"] / total_duration * 60  # files/minute
        avg_per_video = total_duration / result["total"]    # seconds/video
        
        # 性能基准断言
        assert total_duration < 1800, f"总处理时间超标: {total_duration:.2f}s > 30分钟"
        assert throughput >= 0.8, f"吞吐量过低: {throughput:.2f} files/min < 0.8"
        assert avg_per_video < 60, f"平均每视频处理时间过长: {avg_per_video:.2f}s > 60s"
        
        # 生成性能报告
        performance_report = {
            'test_name': 'real_figma_videos_performance_benchmark',
            'video_count': expected_video_count,
            'total_duration_seconds': total_duration,
            'throughput_files_per_minute': throughput,
            'avg_seconds_per_video': avg_per_video,
            'success_rate': result["success"] / result["total"],
            'test_timestamp': datetime.now().isoformat(),
            'video_files': [f.name for f in self.video_files],
            'benchmark_criteria': {
                'max_total_duration_seconds': 1800,
                'min_throughput_files_per_minute': 0.8,
                'max_avg_seconds_per_video': 60,
                'min_success_rate': 0.95
            },
            'result': 'PASS'
        }
        
        # 保存性能基准报告
        benchmark_file = self.project_root / "tests" / "real_video_performance_benchmark.json"
        with open(benchmark_file, 'w', encoding='utf-8') as f:
            json.dump(performance_report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 真实视频性能基准测试通过:")
        print(f"   📊 视频数量: {expected_video_count}")
        print(f"   ⏱️  总处理时间: {total_duration:.1f}秒")
        print(f"   🚀 吞吐量: {throughput:.2f} files/min")
        print(f"   📈 平均每视频: {avg_per_video:.2f}秒")
        print(f"   📄 基准报告: {benchmark_file}")
        
        self._cleanup_state_files()
    
    def test_real_video_files_validation(self):
        """
        测试5: 真实视频文件验证
        目标：验证test_videos目录中的文件确实是有效视频
        """
        expected_videos = [
            "001 - introduction-to-figma-essentials-training-course.mp4.mp4",
            "002 - getting-started-with-figma-training.mp4.mp4", 
            "003 - what-is-figma-for-does-it-do-the-coding.mp4.mp4",
            "004 - whats-the-difference-between-ui-and-ux-in-figma.mp4.mp4",
            "005 - what-we-are-making-in-this-figma-course.mp4.mp4",
            "006 - class-project-001-create-your-own-brief.mp4.mp4",
            "007 - what-is-lo-fi-wireframe-vs-high-fidelity-in-figma.mp4.mp4",
            "008 - creating-our-design-file-introducing-frames-in-figma.mp4.mp4",
            "009 - the-basics-of-type-fonts-in-figma.mp4_2.mp4",
            "010 - rectangles-circles-buttons-rounded-corners-in-figma.mp4.mp4",
            "011 - how-to-use-color-in-figma.mp4.mp4",
            "012 - strokes-plus-updating-color-defaults-in-figma.mp4.mp4",
            "013 - object-editing-and-how-to-escape-in-figma.mp4.mp4",
            "014 - scale-vs-selection-tool-in-figma.mp4.mp4",
            "015 - frames-vs-groups-in-figma.mp4.mp4",
            "016 - class-project-002-wireframe.mp4.mp4",
            "017 - where-to-get-free-icons-for-figma.mp4.mp4",
            "018 - matching-the-stroke-of-our-icons.mp4.mp4",
            "019 - how-to-use-plugins-in-figma-for-icons.mp4.mp4",
            "020 - class-project-003-icons.mp4.mp4"
        ]
        
        # 验证文件存在性和数量
        actual_videos = [f.name for f in self.video_files]
        assert len(actual_videos) == 20, f"视频文件数量不对: {len(actual_videos)} != 20"
        
        # 验证预期的视频文件都存在
        for expected_video in expected_videos:
            assert expected_video in actual_videos, f"缺少预期视频: {expected_video}"
        
        # 验证文件大小（真实视频文件应该有合理的大小）
        total_size_mb = sum(f.stat().st_size for f in self.video_files) / 1024 / 1024
        avg_size_mb = total_size_mb / len(self.video_files)
        
        assert total_size_mb > 100, f"总文件大小过小，可能不是真实视频: {total_size_mb:.1f}MB"
        assert avg_size_mb > 1, f"平均文件大小过小: {avg_size_mb:.1f}MB"
        
        print(f"✅ 真实视频文件验证通过:")
        print(f"   📁 文件数量: {len(actual_videos)}")
        print(f"   📊 总大小: {total_size_mb:.1f}MB")
        print(f"   📈 平均大小: {avg_size_mb:.1f}MB/文件")


if __name__ == "__main__":
    # 运行真实视频测试
    print("🎬 开始执行基于真实Figma教程视频的QA测试...")
    
    import subprocess
    
    # 执行关键测试
    critical_tests = [
        "TestBatchProcessingWithRealVideos::test_real_video_files_validation",
        "TestBatchProcessingWithRealVideos::test_real_video_error_isolation", 
        "TestBatchProcessingWithRealVideos::test_real_video_performance_benchmark"
    ]
    
    for test_case in critical_tests:
        print(f"\n🧪 执行: {test_case}")
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            f"{__file__}::{test_case}",
            "-v", "--tb=short"
        ], cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print(f"✅ {test_case} 测试通过")
        else:
            print(f"❌ {test_case} 测试失败")
