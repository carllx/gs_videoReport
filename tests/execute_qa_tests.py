#!/usr/bin/env python3
"""
QA测试执行脚本
详细执行测试计划中的各项测试用例
"""

import os
import sys
import subprocess
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/qa_test_results.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class QATestExecutor:
    """QA测试执行器"""
    
    def __init__(self):
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'environment': {
                'python_version': sys.version,
                'platform': os.name,
                'working_directory': os.getcwd()
            },
            'test_cases': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
        }
        
        self.test_videos = {
            'public': {
                'url': 'https://www.youtube.com/watch?v=7r7ZDugy3EE',
                'video_id': '7r7ZDugy3EE',
                'description': '公共测试视频',
                'expected_accessible': True,
                'local_filename': 'public_test_7r7ZDugy3EE.mp4'
            },
            'private': {
                'url': 'https://www.youtube.com/watch?v=EXmz9O1xQbM',
                'video_id': 'EXmz9O1xQbM', 
                'description': '私有测试视频',
                'expected_accessible': False,
                'local_filename': 'private_test_EXmz9O1xQbM.mp4'
            }
        }
        
        # 创建测试目录
        self.test_dirs = {
            'videos': Path('./test_videos'),
            'output': Path('./test_output'),
            'logs': Path('./tests/logs')
        }
        
        for dir_path in self.test_dirs.values():
            dir_path.mkdir(exist_ok=True)

    def log_test_result(self, test_id, status, details, performance=None):
        """记录测试结果"""
        self.test_results['test_cases'][test_id] = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'performance': performance or {}
        }
        
        self.test_results['summary']['total'] += 1
        if status == 'PASSED':
            self.test_results['summary']['passed'] += 1
            logger.info(f"✅ {test_id}: PASSED")
        elif status == 'FAILED':
            self.test_results['summary']['failed'] += 1
            logger.error(f"❌ {test_id}: FAILED - {details}")
        else:
            self.test_results['summary']['skipped'] += 1
            logger.warning(f"⏭️  {test_id}: SKIPPED - {details}")

    def check_dependencies(self):
        """TC000: 检查系统依赖"""
        logger.info("=== TC000: 系统依赖检查 ===")
        
        dependencies = {
            'python': {'cmd': [sys.executable, '--version'], 'required': True},
            'yt-dlp': {'cmd': ['yt-dlp', '--version'], 'required': False},
            'requests': {'cmd': [sys.executable, '-c', 'import requests; print(requests.__version__)'], 'required': True}
        }
        
        results = {}
        for dep_name, dep_info in dependencies.items():
            try:
                result = subprocess.run(
                    dep_info['cmd'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    results[dep_name] = {'status': 'OK', 'version': version}
                    logger.info(f"  ✅ {dep_name}: {version}")
                else:
                    results[dep_name] = {'status': 'ERROR', 'error': result.stderr}
                    logger.error(f"  ❌ {dep_name}: {result.stderr}")
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                results[dep_name] = {'status': 'NOT_FOUND', 'error': str(e)}
                if dep_info['required']:
                    logger.error(f"  ❌ {dep_name}: 必需依赖未找到 - {e}")
                else:
                    logger.warning(f"  ⚠️  {dep_name}: 可选依赖未找到 - {e}")
        
        # 检查模板配置
        try:
            cmd = [sys.executable, '-m', 'src.gs_video_report.cli', 'list-templates']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and 'chinese_transcript' in result.stdout:
                results['chinese_transcript_template'] = {'status': 'OK'}
                logger.info("  ✅ 中文转录模板配置正确")
            else:
                results['chinese_transcript_template'] = {'status': 'ERROR', 'details': result.stderr}
                logger.error("  ❌ 中文转录模板配置错误")
        except Exception as e:
            results['chinese_transcript_template'] = {'status': 'ERROR', 'error': str(e)}
            logger.error(f"  ❌ 模板检查失败: {e}")
        
        # 判断整体依赖检查结果
        critical_deps = ['python', 'requests', 'chinese_transcript_template']
        critical_ok = all(results.get(dep, {}).get('status') == 'OK' for dep in critical_deps)
        
        if critical_ok:
            self.log_test_result('TC000', 'PASSED', '所有关键依赖已满足', results)
            return True
        else:
            self.log_test_result('TC000', 'FAILED', '关键依赖检查失败', results)
            return False

    def test_video_accessibility(self, video_type):
        """TC001/TC002: 测试视频可访问性"""
        test_id = f"TC001" if video_type == 'public' else f"TC002"
        video_info = self.test_videos[video_type]
        
        logger.info(f"=== {test_id}: {video_info['description']}访问测试 ===")
        
        start_time = time.time()
        
        try:
            import requests
            
            # 测试视频URL可访问性
            logger.info(f"测试URL: {video_info['url']}")
            
            response = requests.head(
                video_info['url'],
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; gs_videoReport/1.0)'}
            )
            
            access_time = time.time() - start_time
            
            logger.info(f"HTTP状态码: {response.status_code}")
            logger.info(f"响应时间: {access_time:.2f}秒")
            
            # 判断结果
            is_accessible = (response.status_code == 200)
            expected_accessible = video_info['expected_accessible']
            
            if is_accessible == expected_accessible:
                if video_type == 'public':
                    details = f"公共视频可正常访问 (HTTP {response.status_code})"
                    self.log_test_result(test_id, 'PASSED', details, {'response_time': access_time})
                    return True
                else:
                    details = f"私有视频按预期不可访问 (HTTP {response.status_code})"
                    self.log_test_result(test_id, 'PASSED', details, {'response_time': access_time})
                    return False  # 私有视频不可访问是预期行为
            else:
                details = f"访问性与预期不符: 实际={is_accessible}, 预期={expected_accessible}"
                self.log_test_result(test_id, 'FAILED', details, {'response_time': access_time})
                return False
                
        except requests.RequestException as e:
            access_time = time.time() - start_time
            if video_type == 'private':
                # 私有视频网络错误是预期的
                details = f"私有视频按预期无法访问: {str(e)}"
                self.log_test_result(test_id, 'PASSED', details, {'response_time': access_time})
                return False
            else:
                details = f"网络请求失败: {str(e)}"
                self.log_test_result(test_id, 'FAILED', details, {'response_time': access_time})
                return False
        except Exception as e:
            details = f"测试执行错误: {str(e)}"
            self.log_test_result(test_id, 'FAILED', details)
            return False

    def download_test_video(self, video_type):
        """辅助功能：下载测试视频"""
        video_info = self.test_videos[video_type]
        video_path = self.test_dirs['videos'] / video_info['local_filename']
        
        if video_path.exists():
            logger.info(f"视频文件已存在: {video_path}")
            return str(video_path)
        
        logger.info(f"尝试下载{video_info['description']}: {video_info['url']}")
        
        try:
            cmd = [
                'yt-dlp',
                '--format', 'best[ext=mp4][height<=720]',  # 限制质量减少下载时间
                '--output', str(video_path),
                video_info['url']
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0 and video_path.exists():
                file_size = video_path.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"下载成功: {video_path} ({file_size:.1f} MB)")
                return str(video_path)
            else:
                logger.error(f"下载失败: {result.stderr}")
                return None
                
        except FileNotFoundError:
            logger.warning("yt-dlp未安装，无法下载视频。建议: pip install yt-dlp")
            return None
        except subprocess.TimeoutExpired:
            logger.error("视频下载超时")
            return None
        except Exception as e:
            logger.error(f"下载过程出错: {e}")
            return None

    def test_chinese_transcript_template(self, video_path=None):
        """TC003: 中文转录模板功能测试"""
        test_id = "TC003"
        logger.info(f"=== {test_id}: 中文转录模板功能测试 ===")
        
        if not video_path:
            # 尝试下载公共视频进行测试
            video_path = self.download_test_video('public')
            if not video_path:
                self.log_test_result(test_id, 'SKIPPED', '无可用测试视频文件')
                return False
        
        start_time = time.time()
        
        try:
            # 使用中文转录模板分析视频
            output_dir = self.test_dirs['output']
            cmd = [
                sys.executable, '-m', 'src.gs_video_report.cli', 'main',
                video_path,
                '--template', 'chinese_transcript',
                '--output', str(output_dir),
                '--config', 'test_config.yaml',
                '--verbose'
            ]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900  # 15分钟超时
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"处理时间: {processing_time:.2f}秒")
            logger.info(f"退出代码: {result.returncode}")
            
            if result.returncode == 0:
                # 检查输出文件
                output_files = list(output_dir.glob("*.md"))
                if output_files:
                    output_file = output_files[-1]  # 最新的输出文件
                    
                    # 验证输出格式
                    content = output_file.read_text(encoding='utf-8')
                    format_checks = self._validate_chinese_transcript_format(content)
                    
                    details = f"模板执行成功，生成文件: {output_file.name}"
                    performance = {
                        'processing_time': processing_time,
                        'output_file_size': output_file.stat().st_size,
                        'format_validation': format_checks
                    }
                    
                    if all(format_checks.values()):
                        self.log_test_result(test_id, 'PASSED', details, performance)
                        return True
                    else:
                        failed_checks = [k for k, v in format_checks.items() if not v]
                        details += f" (格式验证失败: {failed_checks})"
                        self.log_test_result(test_id, 'FAILED', details, performance)
                        return False
                else:
                    details = "模板执行完成但未生成输出文件"
                    self.log_test_result(test_id, 'FAILED', details, {'processing_time': processing_time})
                    return False
            else:
                details = f"模板执行失败: {result.stderr}"
                self.log_test_result(test_id, 'FAILED', details, {'processing_time': processing_time})
                logger.error(f"STDERR: {result.stderr}")
                logger.info(f"STDOUT: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            details = "模板执行超时"
            self.log_test_result(test_id, 'FAILED', details)
            return False
        except Exception as e:
            details = f"测试执行错误: {str(e)}"
            self.log_test_result(test_id, 'FAILED', details)
            return False

    def _validate_chinese_transcript_format(self, content):
        """验证中文转录输出格式"""
        checks = {
            'has_yaml_frontmatter': content.startswith('---\n') and '\n---\n' in content,
            'has_video_title': '# ' in content and '中文逐字稿分析' in content,
            'has_basic_info': '## 基本信息' in content,
            'has_transcript_content': '## 逐字稿内容' in content,
            'has_first_person_summary': '第一人称' in content,
            'has_key_terms': '关键术语' in content or '术语' in content,
            'has_timestamps': '[' in content and ']' in content,  # 检查时间戳格式
            'is_utf8_encoded': True  # 文件已成功读取，说明编码正确
        }
        
        for check, result in checks.items():
            logger.info(f"  格式检查 {check}: {'✅' if result else '❌'}")
        
        return checks

    def generate_test_report(self):
        """生成测试报告"""
        self.test_results['end_time'] = datetime.now().isoformat()
        
        # 计算总执行时间
        start = datetime.fromisoformat(self.test_results['start_time'])
        end = datetime.fromisoformat(self.test_results['end_time'])
        duration = (end - start).total_seconds()
        
        self.test_results['execution_time'] = f"{duration:.2f} seconds"
        
        # 保存详细结果
        report_file = Path('tests/qa_test_results.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        # 生成简要报告
        logger.info("=" * 60)
        logger.info("QA测试执行完成")
        logger.info("=" * 60)
        logger.info(f"执行时间: {self.test_results['execution_time']}")
        logger.info(f"测试总数: {self.test_results['summary']['total']}")
        logger.info(f"通过: {self.test_results['summary']['passed']} ✅")
        logger.info(f"失败: {self.test_results['summary']['failed']} ❌")
        logger.info(f"跳过: {self.test_results['summary']['skipped']} ⏭️")
        
        success_rate = (self.test_results['summary']['passed'] / 
                       max(self.test_results['summary']['total'], 1)) * 100
        logger.info(f"成功率: {success_rate:.1f}%")
        
        logger.info(f"详细结果: {report_file}")
        
        return self.test_results

    def run_all_tests(self, download_videos=False):
        """执行所有测试"""
        logger.info("开始QA测试执行")
        
        # TC000: 依赖检查
        if not self.check_dependencies():
            logger.error("关键依赖检查失败，终止测试")
            return self.generate_test_report()
        
        # TC001: 公共视频访问测试
        public_accessible = self.test_video_accessibility('public')
        
        # TC002: 私有视频访问测试  
        self.test_video_accessibility('private')
        
        # TC003: 中文转录模板测试
        if download_videos and public_accessible:
            self.test_chinese_transcript_template()
        else:
            self.log_test_result('TC003', 'SKIPPED', '需要下载视频或公共视频不可访问')
        
        return self.generate_test_report()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='执行QA测试')
    parser.add_argument('--download', action='store_true', help='下载视频进行完整测试')
    parser.add_argument('--test-case', help='执行特定测试用例 (如: TC001)')
    
    args = parser.parse_args()
    
    executor = QATestExecutor()
    
    if args.test_case:
        # 执行特定测试用例
        if args.test_case == 'TC000':
            executor.check_dependencies()
        elif args.test_case == 'TC001':
            executor.test_video_accessibility('public')
        elif args.test_case == 'TC002':
            executor.test_video_accessibility('private')
        elif args.test_case == 'TC003':
            executor.test_chinese_transcript_template()
        else:
            logger.error(f"未知测试用例: {args.test_case}")
            sys.exit(1)
        executor.generate_test_report()
    else:
        # 执行所有测试
        results = executor.run_all_tests(download_videos=args.download)
        
        # 根据测试结果设置退出代码
        if results['summary']['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    main()
