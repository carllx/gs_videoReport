#!/usr/bin/env python3
"""
批量处理功能 - 性能基准测试
重点：验证批量处理的吞吐量、内存使用和稳定性
"""

import json
import pytest  
import tempfile
import shutil
import psutil
import time
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
import threading
import statistics
from typing import List, Dict, Any

import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from gs_video_report.batch.simple_processor import SimpleBatchProcessor
from gs_video_report.config import Config


class PerformanceMonitor:
    """性能监控工具类"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.start_time = None
        self.memory_samples = []
        self.cpu_samples = []
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """开始性能监控"""
        self.start_time = time.time()
        self.monitoring = True
        self.memory_samples = []
        self.cpu_samples = []
        
        def monitor_loop():
            while self.monitoring:
                try:
                    memory_info = self.process.memory_info()
                    cpu_percent = self.process.cpu_percent()
                    
                    self.memory_samples.append({
                        'timestamp': time.time(),
                        'rss': memory_info.rss / 1024 / 1024,  # MB
                        'vms': memory_info.vms / 1024 / 1024,  # MB
                    })
                    self.cpu_samples.append(cpu_percent)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                    
                time.sleep(0.5)  # 每0.5秒采样一次
        
        self.monitor_thread = threading.Thread(target=monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """停止监控并返回统计数据"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        
        if not self.memory_samples:
            return {'duration': duration, 'error': 'No samples collected'}
        
        rss_values = [sample['rss'] for sample in self.memory_samples]
        vms_values = [sample['vms'] for sample in self.memory_samples]
        
        return {
            'duration': duration,
            'memory': {
                'peak_rss_mb': max(rss_values),
                'avg_rss_mb': statistics.mean(rss_values),
                'peak_vms_mb': max(vms_values),
                'avg_vms_mb': statistics.mean(vms_values),
            },
            'cpu': {
                'avg_cpu_percent': statistics.mean(self.cpu_samples) if self.cpu_samples else 0,
                'max_cpu_percent': max(self.cpu_samples) if self.cpu_samples else 0,
            },
            'samples_count': len(self.memory_samples)
        }


class TestBatchPerformanceBenchmark:
    """批量处理性能基准测试"""
    
    def setup_method(self):
        """测试环境设置"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_videos_dir = self.temp_dir / "videos"
        self.test_videos_dir.mkdir()
        
        # 创建性能测试配置
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
        self.monitor = PerformanceMonitor()
        
    def teardown_method(self):
        """清理测试环境"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_test_video_files(self, count: int, size_kb: int = 1024):
        """创建指定数量和大小的测试视频文件"""
        content = "fake video content " * (size_kb // 20)  # 大致模拟指定大小
        
        for i in range(count):
            video_file = self.test_videos_dir / f"test_video_{i:03d}.mp4"
            video_file.write_text(content)
    
    def simulate_processing_delay(self, min_delay: float = 0.1, max_delay: float = 0.5):
        """模拟视频处理延迟（用于性能测试）"""
        import random
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        return Mock(output_path=f"output_{random.randint(1000,9999)}.md")
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_c1_small_batch_performance_baseline(self, mock_template_manager, mock_gemini_service):
        """
        测试C1: 小批量性能基线测试 (5-10个文件)
        目标：建立小批量处理的性能基准
        """
        # 创建10个测试视频文件
        self.create_test_video_files(count=10, size_kb=2048)  # 2MB each
        
        # 设置模拟服务 - 模拟真实的处理延迟
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        mock_service_instance.process_video_end_to_end.side_effect = lambda *args, **kwargs: self.simulate_processing_delay(0.2, 1.0)
        
        # 开始性能监控
        self.monitor.start_monitoring()
        
        # 执行批量处理
        processor = SimpleBatchProcessor(self.config)
        start_time = time.time()
        result = processor.process_directory(str(self.test_videos_dir))
        end_time = time.time()
        
        # 停止监控并获取性能数据
        perf_data = self.monitor.stop_monitoring()
        
        # 性能基线验证
        processing_time = end_time - start_time
        assert processing_time < 300, f"小批量处理时间超标: {processing_time:.2f}秒 > 300秒"
        assert result["success"] == 10, f"成功率未达标: {result['success']}/10"
        assert perf_data['memory']['peak_rss_mb'] < 1024, f"内存使用超标: {perf_data['memory']['peak_rss_mb']:.2f}MB > 1024MB"
        
        # 生成性能报告
        performance_report = {
            'test_name': 'C1_small_batch_baseline',
            'file_count': 10,
            'file_size_kb': 2048,
            'processing_time_seconds': processing_time,
            'throughput_files_per_minute': (result["total"] / processing_time) * 60,
            'success_rate': result["success"] / result["total"],
            'performance_metrics': perf_data,
            'pass_criteria': {
                'time_limit_seconds': 300,
                'memory_limit_mb': 1024,
                'success_rate_min': 0.9
            },
            'result': 'PASS'
        }
        
        # 保存性能报告
        report_file = self.temp_dir / "c1_performance_report.json"
        with open(report_file, 'w') as f:
            json.dump(performance_report, f, indent=2)
        
        print(f"✅ C1测试通过 - 处理时间: {processing_time:.2f}s, 内存峰值: {perf_data['memory']['peak_rss_mb']:.2f}MB")
        
        # 清理状态文件
        self._cleanup_state_files()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_c2_medium_batch_performance(self, mock_template_manager, mock_gemini_service):
        """
        测试C2: 中等批量性能测试 (20个文件)
        目标：验证类似test_videos目录规模的处理性能
        """
        # 创建20个测试视频文件，模拟真实的Figma教程文件
        self.create_test_video_files(count=20, size_kb=5120)  # 5MB each, 类似真实视频大小
        
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        mock_service_instance.process_video_end_to_end.side_effect = lambda *args, **kwargs: self.simulate_processing_delay(0.5, 2.0)
        
        # 开始监控
        self.monitor.start_monitoring()
        
        # 执行处理
        processor = SimpleBatchProcessor(self.config)
        start_time = time.time()
        result = processor.process_directory(str(self.test_videos_dir))
        end_time = time.time()
        
        perf_data = self.monitor.stop_monitoring()
        
        # 中等批量性能验证
        processing_time = end_time - start_time
        assert processing_time < 1800, f"中等批量处理时间超标: {processing_time:.2f}秒 > 1800秒"  # 30分钟限制
        assert result["success"] >= 18, f"成功率过低: {result['success']}/20 < 18/20"
        assert perf_data['memory']['peak_rss_mb'] < 1024, f"内存使用过高: {perf_data['memory']['peak_rss_mb']:.2f}MB"
        
        # 吞吐量验证
        throughput = (result["total"] / processing_time) * 60  # files per minute
        assert throughput >= 0.8, f"吞吐量过低: {throughput:.2f} files/min < 0.8"
        
        # 性能报告
        performance_report = {
            'test_name': 'C2_medium_batch_performance',
            'file_count': 20,
            'file_size_kb': 5120,
            'processing_time_seconds': processing_time,
            'throughput_files_per_minute': throughput,
            'success_rate': result["success"] / result["total"],
            'performance_metrics': perf_data,
            'pass_criteria': {
                'time_limit_seconds': 1800,
                'memory_limit_mb': 1024,
                'throughput_min_files_per_min': 0.8,
                'success_rate_min': 0.9
            },
            'result': 'PASS'
        }
        
        report_file = self.temp_dir / "c2_performance_report.json"
        with open(report_file, 'w') as f:
            json.dump(performance_report, f, indent=2)
        
        print(f"✅ C2测试通过 - 处理时间: {processing_time:.2f}s, 吞吐量: {throughput:.2f} files/min")
        
        self._cleanup_state_files()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_c3_large_batch_stress_test(self, mock_template_manager, mock_gemini_service):
        """
        测试C3: 大批量压力测试 (50个文件)
        目标：验证大批量处理的稳定性和内存管理
        """
        # 创建50个测试文件，模拟压力测试场景
        self.create_test_video_files(count=50, size_kb=3072)  # 3MB each
        
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        mock_service_instance.process_video_end_to_end.side_effect = lambda *args, **kwargs: self.simulate_processing_delay(0.3, 1.5)
        
        # 开始监控
        self.monitor.start_monitoring()
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # 执行大批量处理
        processor = SimpleBatchProcessor(self.config)
        start_time = time.time()
        result = processor.process_directory(str(self.test_videos_dir))
        end_time = time.time()
        
        perf_data = self.monitor.stop_monitoring()
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # 压力测试验证
        processing_time = end_time - start_time
        memory_growth = final_memory - initial_memory
        
        # 稳定性检查
        assert result["success"] >= 45, f"大批量成功率过低: {result['success']}/50 < 45/50"
        assert memory_growth < 500, f"内存增长过大: {memory_growth:.2f}MB (可能存在内存泄漏)"
        assert perf_data['memory']['peak_rss_mb'] < 1536, f"内存峰值过高: {perf_data['memory']['peak_rss_mb']:.2f}MB"
        
        # 性能稳定性检查
        memory_samples = [sample['rss'] for sample in perf_data.get('memory_samples', [])]
        if len(memory_samples) > 10:
            # 检查内存使用是否稳定（后半程相对前半程增长不超过50%）
            mid_point = len(memory_samples) // 2
            first_half_avg = statistics.mean(memory_samples[:mid_point])
            second_half_avg = statistics.mean(memory_samples[mid_point:])
            growth_rate = (second_half_avg - first_half_avg) / first_half_avg
            
            assert growth_rate < 0.5, f"内存使用增长率过高: {growth_rate:.2%} > 50% (疑似内存泄漏)"
        
        # 压力测试报告
        performance_report = {
            'test_name': 'C3_large_batch_stress_test',
            'file_count': 50,
            'file_size_kb': 3072,
            'processing_time_seconds': processing_time,
            'throughput_files_per_minute': (result["total"] / processing_time) * 60,
            'success_rate': result["success"] / result["total"],
            'memory_analysis': {
                'initial_mb': initial_memory,
                'final_mb': final_memory,
                'growth_mb': memory_growth,
                'peak_mb': perf_data['memory']['peak_rss_mb']
            },
            'performance_metrics': perf_data,
            'stability_checks': {
                'memory_growth_limit_mb': 500,
                'peak_memory_limit_mb': 1536,
                'success_rate_min': 0.9
            },
            'result': 'PASS'
        }
        
        report_file = self.temp_dir / "c3_stress_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(performance_report, f, indent=2)
        
        print(f"✅ C3压力测试通过 - 处理时间: {processing_time:.2f}s, 内存增长: {memory_growth:.2f}MB")
        
        self._cleanup_state_files()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_state_file_performance_impact(self, mock_template_manager, mock_gemini_service):
        """
        测试D1: 状态文件写入性能影响
        目标：验证状态持久化不会显著影响处理性能
        """
        self.create_test_video_files(count=20)
        
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        mock_service_instance.process_video_end_to_end.side_effect = lambda *args, **kwargs: self.simulate_processing_delay(0.1, 0.3)
        
        processor = SimpleBatchProcessor(self.config)
        
        # 测试1: 正常状态保存
        start_time = time.time()
        result = processor.process_directory(str(self.test_videos_dir))
        normal_time = time.time() - start_time
        
        self._cleanup_state_files()
        
        # 测试2: 模拟状态文件写入失败的情况（通过Mock）
        original_save_state = processor._save_state
        def mock_failing_save_state(*args, **kwargs):
            time.sleep(0.01)  # 模拟写入延迟但失败
            pass  # 不实际保存
        
        processor._save_state = mock_failing_save_state
        
        start_time = time.time()
        result_no_save = processor.process_directory(str(self.test_videos_dir))
        no_save_time = time.time() - start_time
        
        # 性能影响分析
        performance_overhead = (normal_time - no_save_time) / no_save_time if no_save_time > 0 else 0
        
        # 验证状态保存的性能开销在可接受范围内
        assert performance_overhead < 0.1, f"状态保存性能开销过大: {performance_overhead:.2%} > 10%"
        assert result["success"] == result_no_save["success"], "状态保存影响了处理成功率"
        
        print(f"✅ 状态文件性能影响测试通过 - 开销: {performance_overhead:.2%}")
    
    def _cleanup_state_files(self):
        """清理生成的状态文件"""
        state_files = list(Path().glob("batch_*_state.json"))
        for state_file in state_files:
            try:
                state_file.unlink()
            except FileNotFoundError:
                pass


class TestRealWorldPerformance:
    """使用真实test_videos数据的性能测试"""
    
    def setup_method(self):
        """使用项目中的真实测试数据"""
        self.project_root = Path(__file__).parent.parent
        self.test_videos_dir = self.project_root / "test_videos"
        
        # 检查真实测试数据是否存在
        if not self.test_videos_dir.exists():
            pytest.skip("真实测试数据目录不存在，跳过真实性能测试")
        
        # 使用真实配置（但API密钥用mock）
        config_data = {
            'google_api': {
                'api_key': 'real_test_scenario',  # 将被mock
                'model': 'gemini-2.5-flash',
                'temperature': 0.7,
                'max_tokens': 8192
            },
            'templates': {
                'default_template': 'chinese_transcript',
                'template_path': 'src/gs_video_report/templates/prompts'
            },
            'output': {
                'default_path': str(self.project_root / "test_output"),
                'file_naming': '{video_title}_{timestamp}',
                'include_metadata': True
            }
        }
        self.config = Config(config_data)
        self.monitor = PerformanceMonitor()
    
    @patch('gs_video_report.batch.simple_processor.GeminiService')
    @patch('gs_video_report.batch.simple_processor.TemplateManager')
    def test_real_figma_videos_performance(self, mock_template_manager, mock_gemini_service):
        """
        测试E1: 真实Figma教程视频性能测试
        目标：使用project中的真实test_videos测试实际性能表现
        """
        # 检查真实视频文件
        video_files = list(self.test_videos_dir.glob("*.mp4"))
        if len(video_files) == 0:
            pytest.skip("没有找到真实的测试视频文件")
        
        print(f"📁 发现 {len(video_files)} 个真实Figma教程视频文件")
        
        # 设置模拟API - 根据文件大小模拟处理时间
        mock_service_instance = Mock()
        mock_gemini_service.return_value = mock_service_instance
        
        def realistic_processing_simulation(*args, **kwargs):
            video_path = args[0] if args else kwargs.get('video_path', '')
            try:
                # 根据文件大小模拟处理时间
                file_size = Path(video_path).stat().st_size / 1024 / 1024  # MB
                # 模拟：每MB大约0.1-0.3秒处理时间
                processing_time = max(0.5, file_size * 0.2 + random.uniform(0.5, 2.0))
                time.sleep(processing_time)
                
                return Mock(output_path=video_path.replace('.mp4', '_lesson.md'))
            except Exception as e:
                # 文件访问错误等
                time.sleep(0.1)
                raise Exception(f"Simulated processing error: {e}")
        
        import random
        mock_service_instance.process_video_end_to_end.side_effect = realistic_processing_simulation
        
        # 开始性能监控
        self.monitor.start_monitoring()
        
        # 执行真实数据批量处理
        processor = SimpleBatchProcessor(self.config)
        start_time = time.time()
        result = processor.process_directory(str(self.test_videos_dir))
        end_time = time.time()
        
        # 获取性能数据
        perf_data = self.monitor.stop_monitoring()
        processing_time = end_time - start_time
        
        # 真实数据性能验证
        total_files = len(video_files)
        success_rate = result["success"] / result["total"]
        throughput = result["total"] / processing_time * 60  # files/min
        
        # 性能断言（基于真实场景的合理期望）
        assert success_rate >= 0.85, f"真实数据成功率过低: {success_rate:.2%} < 85%"
        assert processing_time < 3600, f"处理时间过长: {processing_time:.2f}s > 1小时"
        assert perf_data['memory']['peak_rss_mb'] < 2048, f"内存使用过高: {perf_data['memory']['peak_rss_mb']:.2f}MB"
        
        # 真实场景性能报告
        performance_report = {
            'test_name': 'E1_real_figma_videos_performance',
            'description': 'Using actual Figma tutorial videos from test_videos/',
            'file_count': total_files,
            'video_files': [f.name for f in video_files],
            'processing_time_seconds': processing_time,
            'throughput_files_per_minute': throughput,
            'success_rate': success_rate,
            'results_breakdown': {
                'success': result["success"],
                'failed': result["failed"],
                'skipped': result["skipped"]
            },
            'performance_metrics': perf_data,
            'file_size_analysis': {
                'total_size_mb': sum(f.stat().st_size for f in video_files) / 1024 / 1024,
                'avg_size_mb': statistics.mean(f.stat().st_size / 1024 / 1024 for f in video_files),
                'largest_file_mb': max(f.stat().st_size / 1024 / 1024 for f in video_files)
            },
            'timestamp': datetime.now().isoformat(),
            'result': 'PASS' if success_rate >= 0.85 else 'FAIL'
        }
        
        # 保存详细的真实性能报告
        report_file = self.project_root / "tests" / "real_performance_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(performance_report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 真实数据性能测试完成:")
        print(f"   📊 文件数量: {total_files}")
        print(f"   ⏱️  处理时间: {processing_time:.1f}秒")
        print(f"   📈 成功率: {success_rate:.1%}")
        print(f"   🚀 吞吐量: {throughput:.2f} files/min")
        print(f"   💾 内存峰值: {perf_data['memory']['peak_rss_mb']:.1f}MB")
        print(f"   📄 详细报告: {report_file}")
        
        # 清理状态文件
        state_files = list(self.project_root.glob("batch_*_state.json"))
        for state_file in state_files:
            state_file.unlink()


if __name__ == "__main__":
    # 快速性能基准测试
    print("🚀 开始执行批量处理性能基准测试...")
    
    import subprocess
    import sys
    
    # 执行关键性能测试
    test_cases = [
        "TestBatchPerformanceBenchmark::test_c1_small_batch_performance_baseline",
        "TestBatchPerformanceBenchmark::test_c2_medium_batch_performance", 
        "TestRealWorldPerformance::test_real_figma_videos_performance"
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 执行测试: {test_case}")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            f"{__file__}::{test_case}",
            "-v", "--tb=short"
        ], cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print(f"✅ {test_case} 测试通过")
        else:
            print(f"❌ {test_case} 测试失败")
