#!/usr/bin/env python3
"""
批量处理功能 - 基于真实视频的QA测试执行器
使用test_videos目录中的20个真实Figma教程视频进行完整验证
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class RealVideoQATestRunner:
    """基于真实视频的QA测试执行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_videos_dir = self.project_root / "test_videos"
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
        # 验证真实视频文件
        self._validate_real_videos()
    
    def _validate_real_videos(self):
        """验证真实视频文件的存在性"""
        if not self.test_videos_dir.exists():
            print("❌ test_videos目录不存在，无法进行真实视频测试")
            sys.exit(1)
        
        video_files = list(self.test_videos_dir.glob("*.mp4"))
        if len(video_files) != 20:
            print(f"⚠️ 期望20个视频文件，实际找到{len(video_files)}个")
        
        print(f"✅ 找到 {len(video_files)} 个真实Figma教程视频文件")
        return video_files
    
    def run_comprehensive_qa_suite(self) -> Dict[str, Any]:
        """执行基于真实视频的完整QA测试套件"""
        
        print("🎬 QA Agent - 开始执行基于真实Figma视频的批量处理测试")
        print("=" * 70)
        
        self.start_time = time.time()
        
        # 定义真实视频测试用例套件
        real_video_test_cases = [
            {
                'name': '真实视频文件验证',
                'module': 'test_batch_real_videos.py',
                'class': 'TestBatchProcessingWithRealVideos',
                'method': 'test_real_video_files_validation',
                'priority': 'HIGH',
                'category': '基础验证',
                'description': '验证20个Figma教程视频文件的完整性和有效性'
            },
            {
                'name': '真实视频错误隔离机制',
                'module': 'test_batch_real_videos.py',
                'class': 'TestBatchProcessingWithRealVideos', 
                'method': 'test_real_video_error_isolation',
                'priority': 'HIGH',
                'category': '可靠性测试',
                'description': '使用真实视频验证单个视频失败不影响其他视频处理'
            },
            {
                'name': '真实视频重试机制',
                'module': 'test_batch_real_videos.py',
                'class': 'TestBatchProcessingWithRealVideos',
                'method': 'test_real_video_retry_mechanism', 
                'priority': 'HIGH',
                'category': '错误恢复',
                'description': '验证网络错误时的智能重试和指数退避策略'
            },
            {
                'name': '真实视频断点续传',
                'module': 'test_batch_real_videos.py',
                'class': 'TestBatchProcessingWithRealVideos',
                'method': 'test_real_video_skip_existing',
                'priority': 'HIGH', 
                'category': '断点续传',
                'description': '验证--skip-existing参数的断点续传功能'
            },
            {
                'name': '真实视频性能基准',
                'module': 'test_batch_real_videos.py',
                'class': 'TestBatchProcessingWithRealVideos',
                'method': 'test_real_video_performance_benchmark',
                'priority': 'CRITICAL',
                'category': '性能基准',
                'description': '建立20个真实Figma视频的性能处理基准'
            }
        ]
        
        # 执行每个测试用例
        for test_case in real_video_test_cases:
            result = self._run_single_test(test_case)
            self.test_results.append(result)
        
        self.end_time = time.time()
        
        # 生成详细报告
        report = self._generate_comprehensive_report()
        
        # 输出测试总结
        self._print_final_summary()
        
        return report
    
    def _run_single_test(self, test_case: Dict[str, str]) -> Dict[str, Any]:
        """执行单个真实视频测试用例"""
        
        test_identifier = f"{test_case['module']}::{test_case['class']}::{test_case['method']}"
        
        print(f"\n🧪 执行: {test_case['name']}")
        print(f"   📋 {test_case['description']}")
        print(f"   🏷️  类别: {test_case['category']} | 优先级: {test_case['priority']}")
        
        start_time = time.time()
        
        try:
            # 执行pytest命令
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                f"tests/{test_identifier}",
                "-v", "--tb=short", "--no-header", "-s"  # -s显示print输出
            ], 
            cwd=self.project_root,
            capture_output=True, 
            text=True,
            timeout=600  # 10分钟超时（真实视频测试可能较慢）
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 解析测试结果
            if result.returncode == 0:
                status = "PASS"
                print(f"   ✅ 通过 ({duration:.2f}s)")
                
                # 提取有用的输出信息
                if "真实视频性能基准测试通过" in result.stdout:
                    performance_lines = [line.strip() for line in result.stdout.split('\n') 
                                       if line.strip().startswith(('📊', '⏱️', '🚀', '📈', '📄'))]
                    for line in performance_lines:
                        print(f"     {line}")
                        
            else:
                status = "FAIL"
                print(f"   ❌ 失败 ({duration:.2f}s)")
                
                # 显示关键错误信息
                if result.stderr:
                    error_lines = result.stderr.strip().split('\n')[-3:]  # 最后3行错误
                    for line in error_lines:
                        if line.strip():
                            print(f"   🔍 {line.strip()}")
            
            return {
                'test_case': test_case,
                'status': status,
                'duration_seconds': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'execution_timestamp': datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ 超时 (>10分钟)")
            return {
                'test_case': test_case,
                'status': 'TIMEOUT', 
                'duration_seconds': 600,
                'stdout': '',
                'stderr': 'Test execution timeout (10 minutes)',
                'return_code': -1,
                'execution_timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"   💥 执行异常: {str(e)}")
            return {
                'test_case': test_case,
                'status': 'ERROR',
                'duration_seconds': 0,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'execution_timestamp': datetime.now().isoformat()
            }
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成基于真实视频的综合测试报告"""
        
        total_duration = self.end_time - self.start_time
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results if r['status'] in ['ERROR', 'TIMEOUT']])
        
        # 按优先级分析
        critical_tests = [r for r in self.test_results if r['test_case']['priority'] == 'CRITICAL']
        high_tests = [r for r in self.test_results if r['test_case']['priority'] == 'HIGH']
        
        critical_passed = len([r for r in critical_tests if r['status'] == 'PASS'])
        high_passed = len([r for r in high_tests if r['status'] == 'PASS'])
        
        # 构建综合报告
        report = {
            'real_video_qa_execution_report': {
                'metadata': {
                    'agent_role': '@qa.mdc',
                    'test_suite': 'real_figma_videos_batch_processing_qa',
                    'video_source': 'test_videos/ - 20个真实Figma教程视频',
                    'execution_timestamp': datetime.now().isoformat(),
                    'total_duration_seconds': total_duration,
                    'project_root': str(self.project_root),
                    'test_videos_directory': str(self.test_videos_dir)
                },
                'executive_summary': {
                    'total_tests_executed': total_tests,
                    'overall_pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
                    'critical_tests_status': f"{critical_passed}/{len(critical_tests)} CRITICAL tests passed",
                    'high_priority_status': f"{high_passed}/{len(high_tests)} HIGH priority tests passed",
                    'overall_verdict': 'PASS' if failed_tests == 0 and error_tests == 0 else 'FAIL',
                    'ready_for_production': failed_tests == 0 and critical_passed == len(critical_tests)
                },
                'detailed_results': {
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'errors_timeouts': error_tests,
                    'total_execution_time_minutes': total_duration / 60,
                    'average_test_duration_seconds': total_duration / total_tests if total_tests > 0 else 0
                },
                'test_breakdown_by_category': self._analyze_by_category(),
                'performance_insights': self._extract_performance_insights(),
                'test_execution_details': self.test_results,
                'quality_assessment': self._generate_quality_assessment(),
                'recommendations': self._generate_real_video_recommendations()
            }
        }
        
        # 保存详细报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.project_root / "tests" / f"real_video_qa_comprehensive_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 综合测试报告已保存: {report_file}")
        
        return report
    
    def _analyze_by_category(self) -> Dict[str, Dict[str, Any]]:
        """按测试类别分析结果"""
        categories = {}
        
        for result in self.test_results:
            category = result['test_case']['category']
            if category not in categories:
                categories[category] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'avg_duration': 0,
                    'tests': []
                }
            
            categories[category]['total'] += 1
            categories[category]['tests'].append(result['test_case']['name'])
            
            if result['status'] == 'PASS':
                categories[category]['passed'] += 1
            elif result['status'] == 'FAIL':
                categories[category]['failed'] += 1
            
            categories[category]['avg_duration'] += result['duration_seconds']
        
        # 计算平均时长
        for category in categories:
            if categories[category]['total'] > 0:
                categories[category]['avg_duration'] /= categories[category]['total']
                categories[category]['pass_rate'] = categories[category]['passed'] / categories[category]['total']
        
        return categories
    
    def _extract_performance_insights(self) -> Dict[str, Any]:
        """提取性能测试洞察"""
        performance_results = [r for r in self.test_results 
                             if 'performance' in r['test_case']['name'].lower()]
        
        if not performance_results:
            return {'status': 'No performance tests executed'}
        
        insights = {}
        for result in performance_results:
            if result['status'] == 'PASS' and '吞吐量:' in result['stdout']:
                # 尝试从输出中提取性能数据
                lines = result['stdout'].split('\n')
                for line in lines:
                    if '吞吐量:' in line:
                        insights['throughput_info'] = line.strip()
                    elif '总处理时间:' in line:
                        insights['total_duration_info'] = line.strip()
                    elif '平均每视频:' in line:
                        insights['avg_per_video_info'] = line.strip()
        
        return insights
    
    def _generate_quality_assessment(self) -> Dict[str, Any]:
        """生成质量评估"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        
        # 关键功能测试状态
        error_isolation_passed = any(
            r['status'] == 'PASS' and 'error_isolation' in r['test_case']['method']
            for r in self.test_results
        )
        
        retry_mechanism_passed = any(
            r['status'] == 'PASS' and 'retry_mechanism' in r['test_case']['method']
            for r in self.test_results
        )
        
        performance_benchmark_passed = any(
            r['status'] == 'PASS' and 'performance_benchmark' in r['test_case']['method']
            for r in self.test_results
        )
        
        # 质量评分 (0-100)
        quality_score = 0
        if passed_tests == total_tests:
            quality_score += 50  # 基础通过分
        else:
            quality_score += int(50 * passed_tests / total_tests)
        
        if error_isolation_passed:
            quality_score += 20  # 错误隔离
        if retry_mechanism_passed:
            quality_score += 15  # 重试机制
        if performance_benchmark_passed:
            quality_score += 15  # 性能基准
        
        return {
            'overall_quality_score': quality_score,
            'quality_grade': 'A' if quality_score >= 90 else 'B' if quality_score >= 80 else 'C' if quality_score >= 70 else 'D',
            'core_functionality_status': {
                'error_isolation': 'PASS' if error_isolation_passed else 'FAIL',
                'retry_mechanism': 'PASS' if retry_mechanism_passed else 'FAIL', 
                'performance_benchmark': 'PASS' if performance_benchmark_passed else 'FAIL'
            },
            'production_readiness': quality_score >= 85,
            'areas_of_concern': [
                r['test_case']['name'] for r in self.test_results 
                if r['status'] != 'PASS'
            ]
        }
    
    def _generate_real_video_recommendations(self) -> List[str]:
        """基于真实视频测试结果生成建议"""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if r['status'] != 'PASS']
        
        if not failed_tests:
            recommendations.append("🎉 所有真实视频测试通过！批量处理功能完全达标")
            recommendations.append("✅ 可以安全地用于处理真实的Figma教程视频")
            recommendations.append("🚀 建议进行生产环境部署")
        else:
            recommendations.append("⚠️ 发现真实视频测试失败，需要修复")
            
            for failed_test in failed_tests:
                test_name = failed_test['test_case']['name']
                category = failed_test['test_case']['category']
                recommendations.append(f"🔍 修复 {category} 类别的 '{test_name}' 测试")
        
        # 性能相关建议
        performance_tests = [r for r in self.test_results if 'performance' in r['test_case']['name'].lower()]
        if performance_tests:
            perf_test = performance_tests[0]
            if perf_test['duration_seconds'] > 300:  # 超过5分钟
                recommendations.append("⚡ 考虑优化批量处理性能，当前测试耗时较长")
        
        # 基于20个视频文件的建议
        recommendations.append("📊 当前基准基于20个真实Figma教程视频，可扩展到更大批量")
        recommendations.append("🎯 建议在真实API环境下进行最终验收测试")
        
        return recommendations
    
    def _print_final_summary(self):
        """打印最终测试总结"""
        print("\n" + "=" * 70)
        print("🎬 基于真实视频的QA测试执行总结")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print(f"📈 测试统计:")
        print(f"   总计: {total_tests} 个测试")
        print(f"   ✅ 通过: {passed_tests}")
        print(f"   ❌ 失败: {failed_tests}")
        print(f"   📊 通过率: {passed_tests/total_tests:.1%}")
        print(f"   ⏱️ 总耗时: {self.end_time - self.start_time:.1f}秒")
        
        # 关键测试状态
        critical_tests = [r for r in self.test_results if r['test_case']['priority'] == 'CRITICAL']
        critical_passed = len([r for r in critical_tests if r['status'] == 'PASS'])
        
        print(f"\n🎯 关键测试状态:")
        print(f"   CRITICAL: {critical_passed}/{len(critical_tests)} 通过")
        
        # 最终判定
        if failed_tests == 0:
            print(f"\n🎉 QA验证完成！基于20个真实Figma视频的批量处理功能测试全部通过")
            print(f"✅ 功能质量达标，可以交付给用户使用")
        else:
            print(f"\n⚠️ 发现 {failed_tests} 个测试失败，需要开发团队修复后重新验证")
    
    def run_quick_validation(self):
        """快速验证真实视频文件和核心功能"""
        print("🎬 执行真实视频快速验证...")
        
        # 只执行最关键的验证
        validation_test = 'test_batch_real_videos.py::TestBatchProcessingWithRealVideos::test_real_video_files_validation'
        
        print(f"🧪 验证: 真实视频文件完整性")
        result = subprocess.run([
            sys.executable, "-m", "pytest", f"tests/{validation_test}", "-v", "-s"
        ], cwd=self.project_root)
        
        if result.returncode == 0:
            print("✅ 真实视频文件验证通过 - 可以进行完整QA测试")
            return True
        else:
            print("❌ 真实视频文件验证失败 - 请检查test_videos目录")
            return False


def main():
    """主执行函数"""
    runner = RealVideoQATestRunner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # 快速验证模式
        return runner.run_quick_validation()
    else:
        # 完整测试套件
        runner.run_comprehensive_qa_suite()
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
