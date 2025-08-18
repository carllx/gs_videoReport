#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for gs_videoReport v0.1.0
综合质量保证测试套件

这个脚本提供完整的自动化测试，包括：
- 环境验证
- 功能测试  
- 性能测试
- 错误场景测试
- 用户体验测试
"""

import os
import sys
import subprocess
import json
import time
import hashlib
import psutil
import threading
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import logging
from typing import Dict, Any, List, Optional
import yaml

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/comprehensive_qa_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.peak_memory = 0
        self.monitoring = False
        self.memory_samples = []
        
    def start_monitoring(self):
        """开始监控"""
        self.start_time = time.time()
        self.monitoring = True
        self.memory_samples = []
        
        # 启动内存监控线程
        monitor_thread = threading.Thread(target=self._monitor_memory)
        monitor_thread.daemon = True
        monitor_thread.start()
        
    def stop_monitoring(self):
        """停止监控"""
        self.end_time = time.time()
        self.monitoring = False
        return self.get_results()
        
    def _monitor_memory(self):
        """监控内存使用"""
        while self.monitoring:
            try:
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.memory_samples.append(memory_mb)
                self.peak_memory = max(self.peak_memory, memory_mb)
                time.sleep(1)  # 每秒采样一次
            except Exception:
                break
                
    def get_results(self):
        """获取性能结果"""
        duration = 0
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            
        avg_memory = sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0
        
        return {
            'duration_seconds': duration,
            'peak_memory_mb': self.peak_memory,
            'average_memory_mb': avg_memory,
            'memory_samples_count': len(self.memory_samples)
        }

class ComprehensiveQATestSuite:
    """综合QA测试套件"""
    
    def __init__(self):
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'environment': {
                'python_version': sys.version,
                'platform': os.name,
                'working_directory': os.getcwd(),
                'cpu_count': psutil.cpu_count(),
                'total_memory_gb': psutil.virtual_memory().total / (1024**3)
            },
            'test_suites': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'total_suites': 0
            }
        }
        
        # 测试配置
        self.test_configs = {
            'valid': 'test_config_v2.yaml',
            'invalid_api': 'test_configs/invalid_api_key.yaml',
            'missing_api': 'test_configs/missing_api_key.yaml',
            'performance': 'test_configs/performance_test.yaml'
        }
        
        # 测试视频
        self.test_videos = {
            'public': {
                'url': 'https://www.youtube.com/watch?v=7r7ZDugy3EE',
                'local_file': 'test_videos/007 - what-is-lo-fi-wireframe-vs-high-fidelity-in-figma.mp4',
                'description': '公共测试视频'
            },
            'private': {
                'url': 'https://www.youtube.com/watch?v=EXmz9O1xQbM',
                'description': '私有测试视频'
            }
        }
        
        # 创建测试目录
        self.test_dirs = {
            'output': Path('./test_output'),
            'performance': Path('./test_output/performance'),
            'error_test': Path('./test_output/error_test'),
            'logs': Path('./tests/logs'),
            'configs': Path('./test_configs')
        }
        
        for dir_path in self.test_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

    def log_test_result(self, suite_name: str, test_name: str, status: str, 
                       details: str, performance: Optional[Dict] = None):
        """记录测试结果"""
        if suite_name not in self.test_results['test_suites']:
            self.test_results['test_suites'][suite_name] = {
                'tests': {},
                'summary': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}
            }
            self.test_results['summary']['total_suites'] += 1
            
        suite = self.test_results['test_suites'][suite_name]
        
        suite['tests'][test_name] = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'performance': performance or {}
        }
        
        # 更新统计
        suite['summary']['total'] += 1
        self.test_results['summary']['total_tests'] += 1
        
        if status == 'PASSED':
            suite['summary']['passed'] += 1
            self.test_results['summary']['passed_tests'] += 1
            logger.info(f"✅ {suite_name}.{test_name}: PASSED")
        elif status == 'FAILED':
            suite['summary']['failed'] += 1
            self.test_results['summary']['failed_tests'] += 1
            logger.error(f"❌ {suite_name}.{test_name}: FAILED - {details}")
        else:
            suite['summary']['skipped'] += 1
            self.test_results['summary']['skipped_tests'] += 1
            logger.warning(f"⏭️  {suite_name}.{test_name}: SKIPPED - {details}")

    def test_environment_setup(self):
        """TS001: 环境设置测试套件"""
        suite_name = "TS001_Environment"
        logger.info(f"=== {suite_name}: 环境设置测试 ===")
        
        # TC001.1: Python版本检查
        python_version = sys.version_info
        if python_version >= (3, 11):
            self.log_test_result(suite_name, "TC001_1_Python_Version", "PASSED", 
                               f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            self.log_test_result(suite_name, "TC001_1_Python_Version", "FAILED", 
                               f"Python版本过低: {python_version}")
        
        # TC001.2: 依赖包检查
        required_packages = ['yaml', 'requests', 'typer', 'pathlib']
        failed_imports = []
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                failed_imports.append(package)
                
        if not failed_imports:
            self.log_test_result(suite_name, "TC001_2_Dependencies", "PASSED", 
                               f"所有依赖包可用: {required_packages}")
        else:
            self.log_test_result(suite_name, "TC001_2_Dependencies", "FAILED", 
                               f"缺失依赖包: {failed_imports}")
        
        # TC001.3: CLI模块导入
        try:
            result = subprocess.run([sys.executable, '-m', 'src.gs_video_report.cli', '--help'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.log_test_result(suite_name, "TC001_3_CLI_Import", "PASSED", 
                                   "CLI模块成功导入")
            else:
                self.log_test_result(suite_name, "TC001_3_CLI_Import", "FAILED", 
                                   f"CLI模块导入失败: {result.stderr}")
        except Exception as e:
            self.log_test_result(suite_name, "TC001_3_CLI_Import", "FAILED", 
                               f"CLI测试异常: {str(e)}")

    def test_cli_basic_functionality(self):
        """TS002: CLI基础功能测试套件"""
        suite_name = "TS002_CLI_Basic"
        logger.info(f"=== {suite_name}: CLI基础功能测试 ===")
        
        # TC002.1: 版本信息
        try:
            result = subprocess.run([sys.executable, '-m', 'src.gs_video_report.cli', 'version'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and "0.1.0" in result.stdout:
                self.log_test_result(suite_name, "TC002_1_Version", "PASSED", 
                                   f"版本信息正确: {result.stdout.strip()}")
            else:
                self.log_test_result(suite_name, "TC002_1_Version", "FAILED", 
                                   f"版本信息错误: {result.stdout}")
        except Exception as e:
            self.log_test_result(suite_name, "TC002_1_Version", "FAILED", 
                               f"版本检查异常: {str(e)}")
        
        # TC002.2: 模板列表
        try:
            result = subprocess.run([sys.executable, '-m', 'src.gs_video_report.cli', 
                                   'list-templates', '--config', self.test_configs['valid']], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and "chinese_transcript" in result.stdout:
                template_count = result.stdout.count('│')  # 粗略计算模板数量
                self.log_test_result(suite_name, "TC002_2_Templates", "PASSED", 
                                   f"模板列表正常，包含中文转录模板")
            else:
                self.log_test_result(suite_name, "TC002_2_Templates", "FAILED", 
                                   f"模板列表异常: {result.stderr}")
        except Exception as e:
            self.log_test_result(suite_name, "TC002_2_Templates", "FAILED", 
                               f"模板列表异常: {str(e)}")
        
        # TC002.3: 帮助信息
        try:
            result = subprocess.run([sys.executable, '-m', 'src.gs_video_report.cli', '--help'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and "Commands" in result.stdout:
                self.log_test_result(suite_name, "TC002_3_Help", "PASSED", 
                                   "帮助信息完整")
            else:
                self.log_test_result(suite_name, "TC002_3_Help", "FAILED", 
                                   "帮助信息不完整")
        except Exception as e:
            self.log_test_result(suite_name, "TC002_3_Help", "FAILED", 
                               f"帮助信息异常: {str(e)}")

    def test_error_scenarios(self):
        """TS003: 错误场景测试套件"""
        suite_name = "TS003_Error_Scenarios"
        logger.info(f"=== {suite_name}: 错误场景测试 ===")
        
        # TC003.1: 无效API密钥
        if Path(self.test_configs['invalid_api']).exists():
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'src.gs_video_report.cli', 'list-templates',
                    '--config', self.test_configs['invalid_api']
                ], capture_output=True, text=True, timeout=30)
                
                # 应该显示警告但不应该崩溃
                if "Warning" in result.stdout or result.returncode == 0:
                    self.log_test_result(suite_name, "TC003_1_Invalid_API", "PASSED", 
                                       "无效API密钥处理正确")
                else:
                    self.log_test_result(suite_name, "TC003_1_Invalid_API", "FAILED", 
                                       f"无效API密钥处理异常: {result.stderr}")
            except Exception as e:
                self.log_test_result(suite_name, "TC003_1_Invalid_API", "FAILED", 
                                   f"无效API密钥测试异常: {str(e)}")
        else:
            self.log_test_result(suite_name, "TC003_1_Invalid_API", "SKIPPED", 
                               "配置文件不存在")
        
        # TC003.2: 无效视频文件
        try:
            fake_video_path = "nonexistent_video.mp4"
            result = subprocess.run([
                sys.executable, '-m', 'src.gs_video_report.cli', 'main',
                fake_video_path, '--config', self.test_configs['valid']
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0 and ("not found" in result.stderr.lower() or 
                                         "error" in result.stderr.lower()):
                self.log_test_result(suite_name, "TC003_2_Invalid_Video", "PASSED", 
                                   "无效视频文件错误处理正确")
            else:
                self.log_test_result(suite_name, "TC003_2_Invalid_Video", "FAILED", 
                                   f"无效视频文件处理异常: {result.stderr}")
        except Exception as e:
            self.log_test_result(suite_name, "TC003_2_Invalid_Video", "FAILED", 
                               f"无效视频文件测试异常: {str(e)}")

    def test_template_system(self):
        """TS004: 模板系统测试套件"""
        suite_name = "TS004_Template_System"
        logger.info(f"=== {suite_name}: 模板系统测试 ===")
        
        templates_to_test = ['comprehensive_lesson', 'summary_report', 'chinese_transcript']
        
        for template in templates_to_test:
            try:
                # 测试模板在列表中是否存在
                result = subprocess.run([
                    sys.executable, '-m', 'src.gs_video_report.cli', 'list-templates',
                    '--config', self.test_configs['valid']
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and template in result.stdout:
                    self.log_test_result(suite_name, f"TC004_{template}_exists", "PASSED", 
                                       f"模板{template}存在于系统中")
                else:
                    self.log_test_result(suite_name, f"TC004_{template}_exists", "FAILED", 
                                       f"模板{template}不存在")
                    
            except Exception as e:
                self.log_test_result(suite_name, f"TC004_{template}_exists", "FAILED", 
                                   f"模板{template}测试异常: {str(e)}")

    def test_performance_scenarios(self):
        """TS005: 性能测试套件"""
        suite_name = "TS005_Performance"
        logger.info(f"=== {suite_name}: 性能测试 ===")
        
        # TC005.1: 内存使用监控
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        try:
            # 执行一个轻量级操作
            result = subprocess.run([
                sys.executable, '-m', 'src.gs_video_report.cli', 'list-templates',
                '--config', self.test_configs['valid']
            ], capture_output=True, text=True, timeout=30)
            
            time.sleep(2)  # 等待监控数据
            perf_results = monitor.stop_monitoring()
            
            if perf_results['peak_memory_mb'] < 200:  # 200MB以下认为正常
                self.log_test_result(suite_name, "TC005_1_Memory_Usage", "PASSED", 
                                   f"内存使用正常", perf_results)
            else:
                self.log_test_result(suite_name, "TC005_1_Memory_Usage", "FAILED", 
                                   f"内存使用过高", perf_results)
                
        except Exception as e:
            monitor.stop_monitoring()
            self.log_test_result(suite_name, "TC005_1_Memory_Usage", "FAILED", 
                               f"性能测试异常: {str(e)}")

    def test_user_experience(self):
        """TS006: 用户体验测试套件"""
        suite_name = "TS006_User_Experience"
        logger.info(f"=== {suite_name}: 用户体验测试 ===")
        
        # TC006.1: 错误信息友好性
        try:
            result = subprocess.run([
                sys.executable, '-m', 'src.gs_video_report.cli', 'main'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0 and ("Usage:" in result.stderr or "error" in result.stderr.lower()):
                self.log_test_result(suite_name, "TC006_1_Error_Messages", "PASSED", 
                                   "错误信息友好清晰")
            else:
                self.log_test_result(suite_name, "TC006_1_Error_Messages", "FAILED", 
                                   "错误信息不够友好")
        except Exception as e:
            self.log_test_result(suite_name, "TC006_1_Error_Messages", "FAILED", 
                               f"错误信息测试异常: {str(e)}")
        
        # TC006.2: 帮助信息清晰度
        try:
            result = subprocess.run([
                sys.executable, '-m', 'src.gs_video_report.cli', 'main', '--help'
            ], capture_output=True, text=True, timeout=30)
            
            help_keywords = ['Usage:', 'Options:', 'Arguments:']
            keywords_found = sum(1 for keyword in help_keywords if keyword in result.stdout)
            
            if keywords_found >= 2:
                self.log_test_result(suite_name, "TC006_2_Help_Clarity", "PASSED", 
                                   f"帮助信息包含{keywords_found}个关键元素")
            else:
                self.log_test_result(suite_name, "TC006_2_Help_Clarity", "FAILED", 
                                   f"帮助信息不够详细，仅包含{keywords_found}个关键元素")
        except Exception as e:
            self.log_test_result(suite_name, "TC006_2_Help_Clarity", "FAILED", 
                               f"帮助信息测试异常: {str(e)}")

    def generate_comprehensive_report(self):
        """生成综合测试报告"""
        self.test_results['end_time'] = datetime.now().isoformat()
        
        # 计算总执行时间
        start = datetime.fromisoformat(self.test_results['start_time'])
        end = datetime.fromisoformat(self.test_results['end_time'])
        duration = (end - start).total_seconds()
        
        self.test_results['execution_time'] = f"{duration:.2f} seconds"
        
        # 保存详细结果
        report_file = Path('tests/comprehensive_qa_results.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        # 生成简要报告
        logger.info("=" * 80)
        logger.info("GS_VIDEOREPORT V0.1.0 - 综合QA测试报告")
        logger.info("=" * 80)
        logger.info(f"测试执行时间: {self.test_results['execution_time']}")
        logger.info(f"测试套件数: {self.test_results['summary']['total_suites']}")
        logger.info(f"测试用例总数: {self.test_results['summary']['total_tests']}")
        logger.info(f"通过: {self.test_results['summary']['passed_tests']} ✅")
        logger.info(f"失败: {self.test_results['summary']['failed_tests']} ❌")
        logger.info(f"跳过: {self.test_results['summary']['skipped_tests']} ⏭️")
        
        success_rate = (self.test_results['summary']['passed_tests'] / 
                       max(self.test_results['summary']['total_tests'], 1)) * 100
        logger.info(f"成功率: {success_rate:.1f}%")
        
        # 详细套件结果
        logger.info("\n" + "="*60)
        logger.info("测试套件详细结果:")
        logger.info("="*60)
        
        for suite_name, suite_data in self.test_results['test_suites'].items():
            suite_summary = suite_data['summary']
            suite_success_rate = (suite_summary['passed'] / max(suite_summary['total'], 1)) * 100
            logger.info(f"{suite_name}: {suite_success_rate:.1f}% "
                       f"({suite_summary['passed']}/{suite_summary['total']})")
            
            # 显示失败的测试
            for test_name, test_data in suite_data['tests'].items():
                if test_data['status'] == 'FAILED':
                    logger.info(f"  ❌ {test_name}: {test_data['details']}")
        
        logger.info(f"\n详细结果保存至: {report_file}")
        
        return self.test_results

    def run_all_tests(self):
        """执行所有测试套件"""
        logger.info("开始执行GS_VIDEOREPORT V0.1.0综合QA测试")
        
        try:
            self.test_environment_setup()
            self.test_cli_basic_functionality()
            self.test_template_system()
            self.test_error_scenarios()
            self.test_performance_scenarios()
            self.test_user_experience()
            
        except KeyboardInterrupt:
            logger.warning("测试被用户中断")
        except Exception as e:
            logger.error(f"测试执行出现意外错误: {e}")
        
        return self.generate_comprehensive_report()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GS_VIDEOREPORT V0.1.0 综合QA测试')
    parser.add_argument('--suite', help='执行特定测试套件 (如: TS001)')
    parser.add_argument('--test', help='执行特定测试用例 (如: TC001_1)')
    parser.add_argument('--report-only', action='store_true', help='仅生成报告')
    
    args = parser.parse_args()
    
    suite = ComprehensiveQATestSuite()
    
    if args.report_only:
        # 读取现有结果并生成报告
        try:
            with open('tests/comprehensive_qa_results.json', 'r', encoding='utf-8') as f:
                suite.test_results = json.load(f)
            suite.generate_comprehensive_report()
        except FileNotFoundError:
            logger.error("没有找到测试结果文件，请先运行测试")
            sys.exit(1)
    elif args.suite:
        # 执行特定套件
        suite_methods = {
            'TS001': suite.test_environment_setup,
            'TS002': suite.test_cli_basic_functionality,
            'TS003': suite.test_error_scenarios,
            'TS004': suite.test_template_system,
            'TS005': suite.test_performance_scenarios,
            'TS006': suite.test_user_experience
        }
        
        if args.suite in suite_methods:
            suite_methods[args.suite]()
            suite.generate_comprehensive_report()
        else:
            logger.error(f"未知测试套件: {args.suite}")
            sys.exit(1)
    else:
        # 执行所有测试
        results = suite.run_all_tests()
        
        # 根据测试结果设置退出代码
        if results['summary']['failed_tests'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    main()
