#!/usr/bin/env python3
"""
gs_videoReport 完整开发环境验证工具

验证开发环境是否正确设置，包括：
- Python版本和依赖
- 安全配置
- 项目文件结构
- 配置验证

使用方法：
    python scripts/validate_setup.py
    python scripts/validate_setup.py --full  # 完整验证
    python scripts/validate_setup.py --fix   # 自动修复问题
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path
from typing import Dict, List, Tuple, Any
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class SetupValidator:
    """开发环境设置验证器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.issues = []
        self.warnings = []
        self.suggestions = []
    
    def validate_python_version(self) -> bool:
        """验证Python版本"""
        console.print("🐍 检查Python版本...", style="blue")
        
        version = sys.version_info
        required_major, required_minor = 3, 11
        
        if version.major != required_major or version.minor < required_minor:
            self.issues.append(f"Python版本不符合要求。当前: {version.major}.{version.minor}, 要求: {required_major}.{required_minor}+")
            return False
        
        console.print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}", style="green")
        return True
    
    def validate_dependencies(self) -> bool:
        """验证依赖安装"""
        console.print("📦 检查依赖安装...", style="blue")
        
        required_packages = {
            'yaml': 'pyyaml',
            'typer': 'typer',
            'rich': 'rich',
            'google.genai': 'google-genai',
            'httpx': 'httpx'
        }
        
        missing_packages = []
        version_info = {}
        
        for import_name, package_name in required_packages.items():
            try:
                module = importlib.import_module(import_name)
                version = getattr(module, '__version__', 'unknown')
                version_info[package_name] = version
                console.print(f"  ✅ {package_name}: {version}", style="green")
            except ImportError:
                missing_packages.append(package_name)
                console.print(f"  ❌ {package_name}: 未安装", style="red")
        
        if missing_packages:
            self.issues.append(f"缺少依赖包: {', '.join(missing_packages)}")
            self.suggestions.append("运行 'poetry install' 安装依赖")
            return False
        
        return True
    
    def validate_project_structure(self) -> bool:
        """验证项目文件结构"""
        console.print("📁 检查项目结构...", style="blue")
        
        required_files = [
            "pyproject.toml",
            "config.yaml.example", 
            "src/gs_video_report/__init__.py",
            "src/gs_video_report/config.py",
            "src/gs_video_report/security/__init__.py",
            "scripts/security_check.py"
        ]
        
        required_dirs = [
            "src/gs_video_report",
            "src/gs_video_report/security",
            "tests",
            "docs",
            "scripts"
        ]
        
        missing_files = []
        missing_dirs = []
        
        # 检查文件
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
                console.print(f"  ❌ 缺少文件: {file_path}", style="red")
            else:
                console.print(f"  ✅ {file_path}", style="green")
        
        # 检查目录
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
                console.print(f"  ❌ 缺少目录: {dir_path}", style="red")
            else:
                console.print(f"  ✅ {dir_path}/", style="green")
        
        if missing_files or missing_dirs:
            self.issues.append("项目文件结构不完整")
            return False
        
        return True
    
    def validate_security_config(self) -> bool:
        """验证安全配置"""
        console.print("🔒 检查安全配置...", style="blue")
        
        try:
            from gs_video_report.security import api_key_manager
            
            # 运行安全检查
            status = api_key_manager.check_security_status()
            
            if status["overall_status"] in ["secure", "good"]:
                console.print("  ✅ 安全配置正常", style="green")
                return True
            elif status["overall_status"] == "needs_improvement":
                console.print("  ⚠️ 安全配置需要改进", style="yellow")
                self.warnings.extend(status.get("warnings", []))
                self.suggestions.extend(status.get("recommendations", []))
                return True
            else:
                console.print("  ❌ 安全配置存在问题", style="red")
                self.issues.extend(status.get("warnings", []))
                return False
                
        except ImportError as e:
            self.issues.append(f"无法导入安全模块: {e}")
            return False
        except Exception as e:
            self.issues.append(f"安全检查失败: {e}")
            return False
    
    def validate_config_file(self) -> bool:
        """验证配置文件"""
        console.print("⚙️ 检查配置文件...", style="blue")
        
        try:
            from gs_video_report.config import load_config, validate_config
            
            config_path = self.project_root / "config.yaml"
            example_path = self.project_root / "config.yaml.example"
            
            # 检查示例文件
            if not example_path.exists():
                self.issues.append("config.yaml.example文件不存在")
                return False
            
            console.print("  ✅ config.yaml.example存在", style="green")
            
            # 检查配置文件
            if not config_path.exists():
                self.warnings.append("config.yaml不存在，需要从示例文件创建")
                self.suggestions.append("复制config.yaml.example为config.yaml并配置API密钥")
                return True
            
            # 验证配置格式
            try:
                config = load_config(str(config_path))
                console.print("  ✅ config.yaml格式正确", style="green")
                
                # 检查API密钥配置
                if 'google_api' in config and config['google_api'].get('api_key'):
                    api_key = config['google_api']['api_key']
                    if api_key == "YOUR_GEMINI_API_KEY_HERE":
                        self.warnings.append("API密钥使用默认占位符，需要设置真实密钥")
                    else:
                        console.print("  ✅ API密钥已配置", style="green")
                else:
                    self.warnings.append("未配置API密钥")
                
                return True
                
            except Exception as e:
                self.issues.append(f"配置文件格式错误: {e}")
                return False
                
        except ImportError as e:
            self.issues.append(f"无法导入配置模块: {e}")
            return False
    
    def validate_git_setup(self) -> bool:
        """验证Git设置"""
        console.print("📝 检查Git设置...", style="blue")
        
        try:
            # 检查git是否可用
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.issues.append("Git未安装或不可用")
                return False
            
            console.print(f"  ✅ Git版本: {result.stdout.strip()}", style="green")
            
            # 检查是否在git仓库中
            result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode != 0:
                self.warnings.append("不在Git仓库中")
                return True
            
            # 检查.gitignore
            gitignore_path = self.project_root / ".gitignore"
            if not gitignore_path.exists():
                self.issues.append(".gitignore文件不存在")
                return False
            
            # 检查config.yaml是否被忽略
            result = subprocess.run(['git', 'check-ignore', 'config.yaml'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                console.print("  ✅ config.yaml被Git忽略", style="green")
            else:
                self.warnings.append("config.yaml可能未被Git正确忽略")
            
            return True
            
        except FileNotFoundError:
            self.issues.append("Git未安装")
            return False
        except Exception as e:
            self.warnings.append(f"Git检查失败: {e}")
            return True
    
    def validate_poetry_setup(self) -> bool:
        """验证Poetry设置"""
        console.print("🎭 检查Poetry设置...", style="blue")
        
        try:
            result = subprocess.run(['poetry', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.warnings.append("Poetry未安装或不可用")
                self.suggestions.append("安装Poetry: curl -sSL https://install.python-poetry.org | python3 -")
                return True  # Poetry是可选的
            
            console.print(f"  ✅ Poetry版本: {result.stdout.strip()}", style="green")
            
            # 检查pyproject.toml
            pyproject_path = self.project_root / "pyproject.toml"
            if not pyproject_path.exists():
                self.issues.append("pyproject.toml文件不存在")
                return False
            
            # 检查虚拟环境
            result = subprocess.run(['poetry', 'env', 'info', '--path'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                venv_path = result.stdout.strip()
                console.print(f"  ✅ 虚拟环境: {venv_path}", style="green")
            else:
                self.warnings.append("Poetry虚拟环境未激活")
                self.suggestions.append("运行 'poetry install' 创建虚拟环境")
            
            return True
            
        except FileNotFoundError:
            self.warnings.append("Poetry未安装")
            return True
        except Exception as e:
            self.warnings.append(f"Poetry检查失败: {e}")
            return True
    
    def run_basic_tests(self) -> bool:
        """运行基础测试"""
        console.print("🧪 运行基础测试...", style="blue")
        
        try:
            # 测试模块导入
            from gs_video_report import __version__
            console.print(f"  ✅ 模块导入正常, 版本: {__version__}", style="green")
            
            # 测试配置加载
            from gs_video_report.config import Config
            config = Config()
            console.print("  ✅ 配置模块正常", style="green")
            
            # 测试安全模块
            from gs_video_report.security import api_key_manager
            console.print("  ✅ 安全模块正常", style="green")
            
            return True
            
        except Exception as e:
            self.issues.append(f"基础测试失败: {e}")
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        
        total_checks = 8
        passed_checks = 0
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("运行环境验证...", total=total_checks)
            
            checks = [
                ("Python版本", self.validate_python_version),
                ("依赖安装", self.validate_dependencies),
                ("项目结构", self.validate_project_structure),
                ("安全配置", self.validate_security_config),
                ("配置文件", self.validate_config_file),
                ("Git设置", self.validate_git_setup),
                ("Poetry设置", self.validate_poetry_setup),
                ("基础测试", self.run_basic_tests)
            ]
            
            results = {}
            
            for check_name, check_func in checks:
                try:
                    result = check_func()
                    results[check_name] = result
                    if result:
                        passed_checks += 1
                except Exception as e:
                    results[check_name] = False
                    self.issues.append(f"{check_name}检查失败: {e}")
                
                progress.advance(task)
        
        # 确定整体状态
        if passed_checks == total_checks and not self.issues:
            overall_status = "excellent"
        elif passed_checks >= total_checks - 1 and not self.issues:
            overall_status = "good"
        elif passed_checks >= total_checks - 2:
            overall_status = "needs_improvement"
        else:
            overall_status = "poor"
        
        return {
            "overall_status": overall_status,
            "passed_checks": passed_checks,
            "total_checks": total_checks,
            "results": results,
            "issues": self.issues,
            "warnings": self.warnings,
            "suggestions": self.suggestions
        }

def display_report(report: Dict[str, Any]):
    """显示验证报告"""
    
    status_colors = {
        "excellent": "bright_green",
        "good": "green",
        "needs_improvement": "yellow",
        "poor": "red"
    }
    
    status_text = {
        "excellent": "优秀",
        "good": "良好", 
        "needs_improvement": "需要改进",
        "poor": "较差"
    }
    
    overall_color = status_colors.get(report["overall_status"], "white")
    overall_text = status_text.get(report["overall_status"], "未知")
    
    console.print(f"\n🎯 环境验证完成!", style="bold blue")
    console.print(f"整体状态: [{overall_color}]{overall_text}[/{overall_color}]")
    console.print(f"通过检查: {report['passed_checks']}/{report['total_checks']}")
    
    # 详细结果表格
    table = Table(title="详细检查结果", show_header=True, header_style="bold blue")
    table.add_column("检查项目", style="cyan", width=15)
    table.add_column("状态", width=10)
    table.add_column("说明", width=40)
    
    for check_name, result in report["results"].items():
        status = "✅ 通过" if result else "❌ 失败"
        status_style = "green" if result else "red"
        table.add_row(check_name, f"[{status_style}]{status}[/{status_style}]", "")
    
    console.print(table)
    
    # 问题报告
    if report["issues"]:
        console.print("\n❌ 需要解决的问题:", style="bold red")
        for issue in report["issues"]:
            console.print(f"  • {issue}", style="red")
    
    # 警告信息
    if report["warnings"]:
        console.print("\n⚠️ 警告信息:", style="bold yellow")
        for warning in report["warnings"]:
            console.print(f"  • {warning}", style="yellow")
    
    # 建议
    if report["suggestions"]:
        console.print("\n💡 改进建议:", style="bold green")
        for suggestion in report["suggestions"]:
            console.print(f"  • {suggestion}", style="green")

def auto_fix_issues():
    """自动修复可修复的问题"""
    console.print("🔧 自动修复问题...", style="bold blue")
    
    fixed_count = 0
    
    try:
        # 运行安全检查修复
        result = subprocess.run([
            sys.executable, "scripts/security_check.py", "--fix"
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            console.print("✅ 安全配置已修复", style="green")
            fixed_count += 1
        
    except Exception as e:
        console.print(f"⚠️ 自动修复失败: {e}", style="yellow")
    
    # 创建config.yaml（如果不存在）
    config_path = project_root / "config.yaml"
    example_path = project_root / "config.yaml.example"
    
    if not config_path.exists() and example_path.exists():
        try:
            import shutil
            shutil.copy2(example_path, config_path)
            console.print("✅ 已创建config.yaml文件", style="green")
            fixed_count += 1
        except Exception as e:
            console.print(f"⚠️ 创建config.yaml失败: {e}", style="yellow")
    
    if fixed_count > 0:
        console.print(f"\n🎉 成功修复 {fixed_count} 个问题", style="bold green")
    else:
        console.print("\n💡 没有可自动修复的问题", style="blue")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="gs_videoReport 开发环境验证工具")
    parser.add_argument("--full", action="store_true", help="运行完整验证")
    parser.add_argument("--fix", action="store_true", help="自动修复问题")
    parser.add_argument("--output", help="保存报告到文件")
    
    args = parser.parse_args()
    
    console.print("🔍 gs_videoReport 开发环境验证", style="bold blue")
    console.print("=" * 50)
    
    if args.fix:
        auto_fix_issues()
        console.print("\n重新运行验证...", style="blue")
    
    # 运行验证
    validator = SetupValidator()
    report = validator.generate_report()
    
    # 显示报告
    display_report(report)
    
    # 保存报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        console.print(f"\n📄 报告已保存到: {args.output}", style="blue")
    
    # 根据结果设置退出码
    if report["overall_status"] in ["excellent", "good"]:
        sys.exit(0)
    elif report["overall_status"] == "needs_improvement":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
