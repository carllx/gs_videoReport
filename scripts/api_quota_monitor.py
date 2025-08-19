#!/usr/bin/env python3
"""
Google Gemini API 配额监控工具
实时监控API配额使用情况，预警配额耗尽问题

Author: gs_videoReport Team
Version: 1.0
License: MIT
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json

from google import genai
from google.genai import types
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class QuotaInfo:
    """API配额信息"""
    key_name: str
    api_key: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    quota_exhausted: bool = False
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    estimated_remaining: int = 100  # 免费层每日100请求
    reset_time: Optional[datetime] = None

@dataclass
class ModelInfo:
    """模型信息"""
    model_name: str
    is_available: bool
    supports_video: bool
    cost_per_request: float = 0.0
    description: str = ""

class APIQuotaMonitor:
    """API配额监控器"""
    
    def __init__(self, api_keys: Union[str, Dict[str, str]], 
                 save_path: Optional[str] = None):
        """
        初始化配额监控器
        
        Args:
            api_keys: 单个API密钥(str)或多个密钥字典
            save_path: 配额数据保存路径
        """
        self.quota_data: Dict[str, QuotaInfo] = {}
        self.models: Dict[str, ModelInfo] = {}
        self.save_path = save_path or "quota_status.json"
        
        # 标准化API密钥输入
        if isinstance(api_keys, str):
            self.api_keys = {"default": api_keys}
        else:
            self.api_keys = api_keys
            
        self._load_saved_data()
        self._initialize_quota_tracking()
        
    def _load_saved_data(self):
        """加载已保存的配额数据"""
        try:
            if Path(self.save_path).exists():
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    
                for key_name, data in saved_data.get('quota_data', {}).items():
                    if key_name in self.api_keys:
                        # 转换时间戳
                        if data.get('last_request_time'):
                            data['last_request_time'] = datetime.fromisoformat(data['last_request_time'])
                        if data.get('reset_time'):
                            data['reset_time'] = datetime.fromisoformat(data['reset_time'])
                        
                        self.quota_data[key_name] = QuotaInfo(**data)
        except Exception as e:
            console.print(f"[yellow]⚠️  加载配额数据失败: {e}[/yellow]")
    
    def _save_data(self):
        """保存配额数据"""
        try:
            save_data = {
                'quota_data': {},
                'last_updated': datetime.now().isoformat()
            }
            
            for key_name, quota_info in self.quota_data.items():
                data = asdict(quota_info)
                # 转换时间为字符串
                if data.get('last_request_time'):
                    data['last_request_time'] = data['last_request_time'].isoformat()
                if data.get('reset_time'):
                    data['reset_time'] = data['reset_time'].isoformat()
                save_data['quota_data'][key_name] = data
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存配额数据失败: {e}")
    
    def _initialize_quota_tracking(self):
        """初始化配额跟踪"""
        console.print(f"[cyan]🔧 初始化 {len(self.api_keys)} 个API密钥的配额监控...[/cyan]")
        
        for key_name, api_key in self.api_keys.items():
            if key_name not in self.quota_data:
                # 创建新的配额信息
                self.quota_data[key_name] = QuotaInfo(
                    key_name=key_name,
                    api_key=api_key,
                    reset_time=self._calculate_next_reset()
                )
            else:
                # 更新API密钥（可能已更改）
                self.quota_data[key_name].api_key = api_key
        
        # 检测可用模型
        self._detect_available_models()
    
    def _calculate_next_reset(self) -> datetime:
        """计算下次配额重置时间（UTC时间每日重置）"""
        now = datetime.now()
        next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_reset
    
    def _detect_available_models(self):
        """检测可用的模型"""
        console.print(f"[cyan]🤖 检测可用模型...[/cyan]")
        
        # 定义已知模型信息
        known_models = {
            'gemini-2.5-pro': ModelInfo(
                model_name='gemini-2.5-pro',
                is_available=False,
                supports_video=True,
                cost_per_request=5.0,  # 估算每个视频请求消耗
                description='最新Gemini 2.5 Pro模型，支持视频分析'
            ),
            'gemini-2.5-flash': ModelInfo(
                model_name='gemini-2.5-flash',
                is_available=False,
                supports_video=True,
                cost_per_request=2.0,
                description='Gemini 2.5 Flash模型，速度较快'
            ),
            'gemini-1.5-pro': ModelInfo(
                model_name='gemini-1.5-pro',
                is_available=False,
                supports_video=True,
                cost_per_request=4.0,
                description='Gemini 1.5 Pro模型'
            ),
            'gemini-1.5-flash': ModelInfo(
                model_name='gemini-1.5-flash',
                is_available=False,
                supports_video=True,
                cost_per_request=1.0,
                description='Gemini 1.5 Flash模型，最经济选择'
            )
        }
        
        # 选择第一个可用的API密钥进行测试
        test_key_name = list(self.api_keys.keys())[0]
        test_api_key = self.api_keys[test_key_name]
        
        try:
            client = genai.Client(api_key=test_api_key, vertexai=False)
            
            for model_name, model_info in known_models.items():
                try:
                    # 简单测试每个模型
                    response = client.models.generate_content(
                        model=model_name,
                        contents='Test'
                    )
                    
                    if response and response.text:
                        model_info.is_available = True
                        console.print(f"   ✅ {model_name}: 可用")
                    else:
                        console.print(f"   ⚠️  {model_name}: 响应异常")
                        
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        model_info.is_available = False
                        console.print(f"   💸 {model_name}: 配额限制")
                    else:
                        console.print(f"   ❌ {model_name}: {str(e)[:30]}...")
                
                self.models[model_name] = model_info
                time.sleep(1)  # 避免过快请求
                
        except Exception as e:
            console.print(f"[red]❌ 模型检测失败: {e}[/red]")
    
    def check_quota_status(self, key_name: Optional[str] = None) -> Dict[str, Any]:
        """
        检查配额状态
        
        Args:
            key_name: 特定密钥名称，None表示检查所有密钥
            
        Returns:
            配额状态信息
        """
        if key_name:
            keys_to_check = [key_name] if key_name in self.quota_data else []
        else:
            keys_to_check = list(self.quota_data.keys())
        
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for key_name in keys_to_check:
                task = progress.add_task(f"检查 {key_name} 配额状态", total=None)
                
                quota_info = self.quota_data[key_name]
                api_key = quota_info.api_key
                
                try:
                    client = genai.Client(api_key=api_key, vertexai=False)
                    
                    # 测试请求
                    start_time = time.time()
                    response = client.models.generate_content(
                        model='gemini-2.5-pro',
                        contents='配额测试请求'
                    )
                    end_time = time.time()
                    
                    if response and response.text:
                        # 成功请求
                        quota_info.successful_requests += 1
                        quota_info.total_requests += 1
                        quota_info.last_request_time = datetime.now()
                        quota_info.quota_exhausted = False
                        quota_info.last_error = None
                        
                        # 更新预估剩余
                        quota_info.estimated_remaining = max(0, 100 - quota_info.total_requests)
                        
                        results[key_name] = {
                            'status': 'active',
                            'response_time': round(end_time - start_time, 2),
                            'estimated_remaining': quota_info.estimated_remaining,
                            'total_used': quota_info.total_requests
                        }
                        
                    else:
                        quota_info.failed_requests += 1
                        quota_info.total_requests += 1
                        quota_info.last_error = "空响应"
                        
                        results[key_name] = {
                            'status': 'warning',
                            'error': '空响应',
                            'total_used': quota_info.total_requests
                        }
                
                except Exception as e:
                    error_str = str(e)
                    quota_info.failed_requests += 1
                    quota_info.total_requests += 1
                    quota_info.last_request_time = datetime.now()
                    quota_info.last_error = error_str
                    
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        quota_info.quota_exhausted = True
                        quota_info.estimated_remaining = 0
                        
                        results[key_name] = {
                            'status': 'exhausted',
                            'error': '配额耗尽',
                            'reset_time': quota_info.reset_time.isoformat() if quota_info.reset_time else None
                        }
                    else:
                        results[key_name] = {
                            'status': 'error',
                            'error': str(e)[:50] + '...' if len(str(e)) > 50 else str(e)
                        }
                
                progress.update(task, completed=100)
        
        # 保存更新的数据
        self._save_data()
        return results
    
    def get_best_available_key(self) -> Optional[str]:
        """获取最佳可用密钥"""
        available_keys = []
        
        for key_name, quota_info in self.quota_data.items():
            if (not quota_info.quota_exhausted and 
                quota_info.estimated_remaining > 5):  # 保留5个请求作为缓冲
                available_keys.append((key_name, quota_info.estimated_remaining))
        
        if not available_keys:
            return None
        
        # 返回剩余配额最多的密钥
        available_keys.sort(key=lambda x: x[1], reverse=True)
        return available_keys[0][0]
    
    def estimate_processing_capacity(self) -> Dict[str, int]:
        """估算处理能力"""
        total_remaining = sum(
            quota_info.estimated_remaining 
            for quota_info in self.quota_data.values()
            if not quota_info.quota_exhausted
        )
        
        # 每个视频大约消耗5个请求
        estimated_videos = total_remaining // 5
        
        return {
            'total_requests_remaining': total_remaining,
            'estimated_videos_processable': estimated_videos,
            'active_keys': len([q for q in self.quota_data.values() if not q.quota_exhausted]),
            'total_keys': len(self.quota_data)
        }
    
    def display_status_dashboard(self):
        """显示状态仪表盘"""
        # 标题
        console.print(Panel.fit(
            "[bold green]🚀 Google Gemini API 配额监控仪表盘[/bold green]",
            border_style="green"
        ))
        
        # 整体状态
        capacity = self.estimate_processing_capacity()
        
        console.print(f"\n[bold cyan]📊 整体状态概览[/bold cyan]")
        console.print(f"[green]活跃密钥: {capacity['active_keys']}/{capacity['total_keys']}[/green]")
        console.print(f"[yellow]剩余请求: ~{capacity['total_requests_remaining']} 个[/yellow]")
        console.print(f"[blue]可处理视频: ~{capacity['estimated_videos_processable']} 个[/blue]")
        
        # 密钥详细状态表
        table = Table(title="密钥状态详情", show_header=True, header_style="bold magenta")
        table.add_column("密钥名称", style="cyan", width=15)
        table.add_column("状态", justify="center", width=10)
        table.add_column("已用请求", justify="right", width=10)
        table.add_column("剩余估算", justify="right", width=10)
        table.add_column("最后使用", width=20)
        table.add_column("错误信息", width=30)
        
        for key_name, quota_info in self.quota_data.items():
            if quota_info.quota_exhausted:
                status = "[red]❌ 耗尽[/red]"
            elif quota_info.estimated_remaining > 20:
                status = "[green]✅ 良好[/green]"
            elif quota_info.estimated_remaining > 5:
                status = "[yellow]⚠️  警告[/yellow]"
            else:
                status = "[red]🔴 危险[/red]"
            
            last_used = (
                quota_info.last_request_time.strftime("%m-%d %H:%M:%S") 
                if quota_info.last_request_time else "从未使用"
            )
            
            error_display = quota_info.last_error[:25] + "..." if quota_info.last_error and len(quota_info.last_error) > 25 else quota_info.last_error or ""
            
            table.add_row(
                key_name,
                status,
                str(quota_info.total_requests),
                str(quota_info.estimated_remaining),
                last_used,
                error_display
            )
        
        console.print(f"\n")
        console.print(table)
        
        # 可用模型状态
        if self.models:
            console.print(f"\n[bold cyan]🤖 可用模型状态[/bold cyan]")
            model_table = Table(show_header=True, header_style="bold green")
            model_table.add_column("模型名称", style="cyan")
            model_table.add_column("状态", justify="center")
            model_table.add_column("视频支持", justify="center")
            model_table.add_column("每次成本", justify="right")
            model_table.add_column("描述")
            
            for model_name, model_info in self.models.items():
                status = "[green]✅ 可用[/green]" if model_info.is_available else "[red]❌ 不可用[/red]"
                video_support = "✅" if model_info.supports_video else "❌"
                
                model_table.add_row(
                    model_name,
                    status,
                    video_support,
                    f"~{model_info.cost_per_request} 请求",
                    model_info.description
                )
            
            console.print(model_table)
        
        # 建议和提醒
        if capacity['active_keys'] == 0:
            console.print(f"\n[bold red]🚨 警告：所有API密钥均已耗尽！[/bold red]")
            console.print(f"[red]建议：[/red]")
            console.print(f"  1. 等待明日配额重置（UTC 00:00）")
            console.print(f"  2. 创建新的Google账户获取更多API密钥")
            console.print(f"  3. 考虑升级到付费API计划")
        elif capacity['estimated_videos_processable'] < 10:
            console.print(f"\n[bold yellow]⚠️  提醒：剩余处理能力不足！[/bold yellow]")
            console.print(f"[yellow]建议提前准备额外的API密钥[/yellow]")


def main():
    """主程序入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Google Gemini API 配额监控工具")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--api-key", help="单个API密钥")
    parser.add_argument("--check", action="store_true", help="检查配额状态")
    parser.add_argument("--monitor", action="store_true", help="持续监控模式")
    parser.add_argument("--interval", type=int, default=300, help="监控间隔（秒）")
    
    args = parser.parse_args()
    
    # 获取API密钥
    api_keys = {}
    
    if args.config:
        # 从配置文件加载
        import yaml
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if 'api_key' in config:
                    api_keys['default'] = config['api_key']
                elif 'api_keys' in config:
                    api_keys.update(config['api_keys'])
        except Exception as e:
            console.print(f"[red]❌ 读取配置文件失败: {e}[/red]")
            return
    
    if args.api_key:
        api_keys['cmd_line'] = args.api_key
    
    if not api_keys:
        console.print("[red]❌ 未提供API密钥！[/red]")
        console.print("使用 --api-key 参数或 --config 配置文件提供API密钥")
        return
    
    # 创建监控器
    monitor = APIQuotaMonitor(api_keys)
    
    if args.monitor:
        # 持续监控模式
        console.print(f"[cyan]🔄 启动持续监控模式，间隔 {args.interval} 秒[/cyan]")
        try:
            while True:
                monitor.check_quota_status()
                monitor.display_status_dashboard()
                console.print(f"\n[dim]下次检查将在 {args.interval} 秒后进行...[/dim]")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            console.print(f"\n[yellow]👋 监控已停止[/yellow]")
    else:
        # 单次检查
        if args.check:
            monitor.check_quota_status()
        monitor.display_status_dashboard()

if __name__ == "__main__":
    main()
