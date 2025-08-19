#!/usr/bin/env python3
"""
批量处理功能 - QA测试执行器
快速执行关键测试用例并生成测试报告
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class BatchQATestRunner:
    """批量处理QA测试执行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def run_test_suite(self) -> Dict[str, Any]:
        """执行完整的QA测试套件"""
        
        print("🔍 QA Agent - 开始执行批量处理功能测试套件")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # 定义测试用例套件
        test_cases = [
            {
                'name': '错误隔离机制验证',
                'module': 'test_batch_error_handling.py',
                'class': 'TestErrorHandlingAndRetry',
                'method': 'test_error_isolation_mechanism',
                'priority': 'HIGH',
                'category': '可靠性'
            },
            {
                'name': '网络错误重试机制',
                'module': 'test_batch_error_handling.py', 
                'class': 'TestErrorHandlingAndRetry',
                'method': 'test_network_error_retry_mechanism',
                'priority': 'HIGH',
                'category': '错误处理'
            },
            {
                'name': '永久错误识别',
                'module': 'test_batch_error_handling.py',
                'class': 'TestErrorHandlingAndRetry', 
                'method': 'test_permanent_error_no_retry',
                'priority': 'HIGH',
                'category': '智能重试'
            },
            {
                'name': '状态持久化中断测试',
                'module': 'test_batch_error_handling.py',
                'class': 'TestFileUploadInterruption',
                'method': 'test_state_persistence_on_interruption', 
                'priority': 'HIGH',
                'category': '中断恢复'
            },
            {
                'name': '小批量性能基线',
                'module': 'test_batch_performance.py',
                'class': 'TestBatchPerformanceBenchmark',
                'method': 'test_c1_small_batch_performance_baseline',
                'priority': 'MEDIUM',
                'category': '性能基准'
            },
            {
                'name': '中等批量性能测试',
                'module': 'test_batch_performance.py',
                'class': 'TestBatchPerformanceBenchmark', 
                'method': 'test_c2_medium_batch_performance',
                'priority': 'MEDIUM',
                'category': '性能验证'
            },
            {
                'name': '真实视频性能测试',
                'module': 'test_batch_performance.py',
                'class': 'TestRealWorldPerformance',
                'method': 'test_real_figma_videos_performance',
                'priority': 'HIGH', 
                'category': '真实场景'
            }
        ]
        
        # 执行每个测试用例
        for test_case in test_cases:
            result = self._run_single_test(test_case)
            self.test_results.append(result)
        
        self.end_time = time.time()
        
        # 生成测试报告
        report = self._generate_test_report()
        
        # 输出结果摘要
        self._print_summary()
        
        return report
    
    def _run_single_test(self, test_case: Dict[str, str]) -> Dict[str, Any]:
        """执行单个测试用例"""
        
        test_identifier = f"{test_case['module']}::{test_case['class']}::{test_case['method']}"
        
        print(f"\n🧪 执行: {test_case['name']}")
        print(f"   📋 类别: {test_case['category']} | 优先级: {test_case['priority']}")
        
        start_time = time.time()
        
        try:
            # 执行pytest命令
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                f"tests/{test_identifier}",
                "-v", "--tb=short", "--no-header"
            ], 
            cwd=self.project_root,
            capture_output=True, 
            text=True,
            timeout=300  # 5分钟超时
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 解析测试结果
            if result.returncode == 0:
                status = "PASS"
                print(f"   ✅ 通过 ({duration:.2f}s)")
            else:
                status = "FAIL"
                print(f"   ❌ 失败 ({duration:.2f}s)")
                if result.stderr:
                    print(f"   🔍 错误: {result.stderr.strip()[:200]}")
            
            return {
                'test_case': test_case,
                'status': status,
                'duration_seconds': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ 超时 (>300s)")
            return {
                'test_case': test_case,
                'status': 'TIMEOUT', 
                'duration_seconds': 300,
                'stdout': '',
                'stderr': 'Test execution timeout',
                'return_code': -1
            }
        except Exception as e:
            print(f"   💥 异常: {str(e)}")
            return {
                'test_case': test_case,
                'status': 'ERROR',
                'duration_seconds': 0,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1
            }
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """生成详细的测试报告"""
        
        total_duration = self.end_time - self.start_time
        
        # 统计结果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results if r['status'] in ['ERROR', 'TIMEOUT']])
        
        # 按类别分组
        category_stats = {}
        priority_stats = {}
        
        for result in self.test_results:
            category = result['test_case']['category']
            priority = result['test_case']['priority']
            status = result['status']
            
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'pass': 0, 'fail': 0}
            category_stats[category]['total'] += 1
            if status == 'PASS':
                category_stats[category]['pass'] += 1
            elif status == 'FAIL':
                category_stats[category]['fail'] += 1
            
            if priority not in priority_stats:
                priority_stats[priority] = {'total': 0, 'pass': 0, 'fail': 0}
            priority_stats[priority]['total'] += 1
            if status == 'PASS':
                priority_stats[priority]['pass'] += 1
            elif status == 'FAIL':
                priority_stats[priority]['fail'] += 1
        
        # 构建完整报告
        report = {
            'qa_test_execution_report': {
                'metadata': {
                    'agent_role': '@qa.mdc',
                    'test_suite': 'batch_processing_qa',
                    'execution_timestamp': datetime.now().isoformat(),
                    'total_duration_seconds': total_duration,
                    'project_root': str(self.project_root)
                },
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'errors': error_tests,
                    'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
                    'overall_status': 'PASS' if failed_tests == 0 and error_tests == 0 else 'FAIL'
                },
                'category_breakdown': category_stats,
                'priority_breakdown': priority_stats,
                'test_results': self.test_results,
                'recommendations': self._generate_recommendations()
            }
        }
        
        # 保存报告到文件
        report_file = self.project_root / "tests" / f"qa_batch_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 详细测试报告已保存: {report_file}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """基于测试结果生成改进建议"""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if r['status'] != 'PASS']
        
        if not failed_tests:
            recommendations.append("✅ 所有测试通过，批量处理功能质量达标")
            recommendations.append("🚀 可以推进到生产环境部署")
        else:
            recommendations.append("⚠️ 发现测试失败，需要进一步调试和修复")
            
            # 分析失败模式
            error_patterns = {}
            for result in failed_tests:
                category = result['test_case']['category']
                if category not in error_patterns:
                    error_patterns[category] = 0
                error_patterns[category] += 1
            
            for category, count in error_patterns.items():
                recommendations.append(f"🔍 {category} 类别有 {count} 个失败测试，需要重点关注")
        
        # 性能相关建议
        performance_tests = [r for r in self.test_results if 'performance' in r['test_case']['name'].lower()]
        slow_tests = [r for r in performance_tests if r['duration_seconds'] > 60]
        
        if slow_tests:
            recommendations.append(f"⏱️ 发现 {len(slow_tests)} 个耗时较长的性能测试，建议优化")
        
        return recommendations
    
    def _print_summary(self):
        """打印测试结果摘要"""
        print("\n" + "=" * 60)
        print("📊 QA测试执行摘要")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print(f"📈 总计测试: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")
        print(f"📊 通过率: {passed_tests/total_tests:.1%}")
        print(f"⏱️ 总耗时: {self.end_time - self.start_time:.2f}秒")
        
        # 关键测试状态
        critical_tests = [r for r in self.test_results if r['test_case']['priority'] == 'HIGH']
        critical_passed = len([r for r in critical_tests if r['status'] == 'PASS'])
        
        print(f"\n🎯 关键测试 (HIGH优先级): {critical_passed}/{len(critical_tests)} 通过")
        
        if failed_tests == 0:
            print(f"\n🎉 QA验证完成！批量处理功能质量达标，可以交付使用。")
        else:
            print(f"\n⚠️ 发现 {failed_tests} 个测试失败，需要开发团队进一步修复。")
    
    def run_quick_smoke_test(self):
        """执行快速冒烟测试 - 验证核心功能"""
        print("🚀 执行快速冒烟测试...")
        
        # 只执行最关键的测试
        critical_tests = [
            'test_batch_error_handling.py::TestErrorHandlingAndRetry::test_error_isolation_mechanism'
        ]
        
        for test in critical_tests:
            print(f"🧪 执行: {test}")
            result = subprocess.run([
                sys.executable, "-m", "pytest", f"tests/{test}", "-v"
            ], cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ 冒烟测试通过 - 核心功能正常")
                return True
            else:
                print("❌ 冒烟测试失败 - 需要修复核心问题")
                return False


def main():
    """主执行函数"""
    runner = BatchQATestRunner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        # 快速冒烟测试
        return runner.run_quick_smoke_test()
    else:
        # 完整测试套件
        runner.run_test_suite()
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
