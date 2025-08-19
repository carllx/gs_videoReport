#!/usr/bin/env python3
"""
gs_videoReport 安全配置检查工具

此脚本检查项目的安全配置状态，包括：
- API密钥配置和格式验证
- .gitignore安全设置
- 配置文件安全状态
- 环境变量设置

使用方法：
    python scripts/security_check.py
    python scripts/security_check.py --config custom_config.yaml
    python scripts/security_check.py --fix  # 自动修复某些安全问题
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from gs_video_report.security import api_key_manager, APIKeyValidationError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

def display_security_status(status):
    """显示安全状态报告"""
    
    # 状态颜色映射
    status_colors = {
        "secure": "green",
        "good": "blue", 
        "needs_improvement": "yellow",
        "insecure": "red",
        "unknown": "dim"
    }
    
    # 整体状态
    overall_color = status_colors.get(status["overall_status"], "dim")
    console.print(f"\n🔒 整体安全状态: [{overall_color}]{status['overall_status'].upper()}[/{overall_color}]\n")
    
    # 详细状态表格
    table = Table(title="安全配置详情", show_header=True, header_style="bold blue")
    table.add_column("检查项目", style="cyan", width=20)
    table.add_column("状态", style="bold", width=15)
    table.add_column("详情", width=40)
    
    # API密钥检查
    api_key_status = "✅ 有效" if status["api_key_valid"] else "❌ 无效"
    api_key_source = status["api_key_source"].replace("_", " ").title()
    table.add_row("API密钥", api_key_status, f"来源: {api_key_source}")
    
    # 配置文件安全
    config_status = "✅ 安全" if status["config_file_secure"] else "⚠️ 风险"
    table.add_row("配置文件", config_status, "检查是否被Git忽略")
    
    # .gitignore安全
    gitignore_status = "✅ 配置正确" if status["gitignore_secure"] else "⚠️ 需要改进"
    table.add_row(".gitignore", gitignore_status, "检查敏感文件忽略模式")
    
    # 环境变量
    env_count = len(status["environment_variables"])
    env_status = f"📦 {env_count} 个变量" if env_count > 0 else "📭 未使用"
    env_details = ", ".join(status["environment_variables"]) if env_count > 0 else "建议使用环境变量"
    table.add_row("环境变量", env_status, env_details)
    
    console.print(table)
    
    # 警告信息
    if status["warnings"]:
        console.print("\n⚠️  警告信息:", style="bold yellow")
        for warning in status["warnings"]:
            console.print(f"  • {warning}", style="yellow")
    
    # 建议
    if status["recommendations"]:
        console.print("\n💡 安全建议:", style="bold green")
        for recommendation in status["recommendations"]:
            console.print(f"  • {recommendation}", style="green")

def display_setup_guide():
    """显示安全设置指南"""
    
    guide_text = """
🔒 API密钥安全设置指南

1. 获取API密钥：
   访问 https://makersuite.google.com/app/apikey
   登录Google账户并创建新的API密钥

2. 安全设置方法（推荐）：
   使用环境变量（最安全）:
   
   # Linux/macOS
   export GOOGLE_GEMINI_API_KEY="your-api-key-here"
   
   # Windows
   set GOOGLE_GEMINI_API_KEY=your-api-key-here

3. 配置文件方法（备选）：
   复制 config.yaml.example 为 config.yaml
   替换 YOUR_GEMINI_API_KEY_HERE 为真实API密钥
   
4. 验证设置：
   python scripts/security_check.py

🛡️ 安全最佳实践：
  • 绝不要将API密钥提交到版本控制
  • 定期轮换API密钥
  • 使用环境变量存储敏感信息
  • 确保.gitignore正确配置
  • 不要在公共场所分享API密钥
"""
    
    console.print(Panel(guide_text, title="安全设置指南", border_style="green"))

def fix_gitignore():
    """修复.gitignore文件的安全配置"""
    
    gitignore_path = Path(".gitignore")
    
    # 必需的安全模式
    required_patterns = [
        "# API Keys and Secrets (CRITICAL - Never commit these)",
        "config.yaml",
        "test_config.yaml", 
        "*api_key*",
        "*secret*",
        "*token*",
        ".env",
        ".env.local",
        ".env.production",
        "*.key",
        "credentials.json",
        "client_secret*.json"
    ]
    
    try:
        # 读取现有内容
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing_content = f.read()
        else:
            existing_content = ""
        
        # 检查缺失的模式
        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in existing_content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            # 添加缺失的模式
            with open(gitignore_path, 'a') as f:
                f.write("\n# 安全配置 - 自动添加\n")
                for pattern in missing_patterns:
                    f.write(f"{pattern}\n")
            
            console.print(f"✅ 已修复.gitignore文件，添加了 {len(missing_patterns)} 个安全模式", style="green")
            return True
        else:
            console.print("✅ .gitignore文件已正确配置", style="green")
            return False
            
    except Exception as e:
        console.print(f"❌ 修复.gitignore失败: {e}", style="red")
        return False

def create_secure_config():
    """创建安全的配置文件模板"""
    
    config_path = Path("config.yaml")
    example_path = Path("config.yaml.example")
    
    if config_path.exists():
        console.print("⚠️ config.yaml已存在，跳过创建", style="yellow")
        return False
    
    if not example_path.exists():
        console.print("❌ config.yaml.example不存在，无法创建配置文件", style="red")
        return False
    
    try:
        # 复制示例文件
        with open(example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        console.print("✅ 已创建config.yaml文件，请编辑并添加您的API密钥", style="green")
        return True
        
    except Exception as e:
        console.print(f"❌ 创建配置文件失败: {e}", style="red")
        return False

def main():
    parser = argparse.ArgumentParser(description="gs_videoReport 安全配置检查工具")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--fix", action="store_true", help="自动修复安全问题")
    parser.add_argument("--setup-guide", action="store_true", help="显示安全设置指南")
    
    args = parser.parse_args()
    
    console.print("🔍 gs_videoReport 安全配置检查", style="bold blue")
    console.print("=" * 50)
    
    if args.setup_guide:
        display_setup_guide()
        return
    
    # 检查安全状态
    try:
        status = api_key_manager.check_security_status(args.config)
        display_security_status(status)
        
        # 自动修复选项
        if args.fix:
            console.print("\n🔧 自动修复安全问题...", style="bold blue")
            
            fixed_issues = 0
            
            # 修复.gitignore
            if fix_gitignore():
                fixed_issues += 1
            
            # 创建配置文件（如果不存在）
            if create_secure_config():
                fixed_issues += 1
            
            if fixed_issues > 0:
                console.print(f"\n✅ 已修复 {fixed_issues} 个安全问题", style="bold green")
                console.print("建议重新运行安全检查验证结果", style="dim")
            else:
                console.print("\n💡 没有可自动修复的问题", style="blue")
        
        # 根据状态给出退出码
        if status["overall_status"] in ["secure", "good"]:
            sys.exit(0)  # 成功
        elif status["overall_status"] == "needs_improvement":
            sys.exit(1)  # 需要改进
        else:
            sys.exit(2)  # 不安全
            
    except Exception as e:
        console.print(f"❌ 安全检查失败: {e}", style="red")
        sys.exit(3)

if __name__ == "__main__":
    main()
