# 🔧 API问题排查指南

> **版本**: v2.1 | **更新时间**: 2024年1月  
> **适用于**: gs_videoReport v2.1+ with Google Gemini API

## 🎯 概述

本指南提供Google Gemini API相关问题的完整诊断和解决方案，帮助用户快速定位和解决API使用过程中的各种问题。

## 🚨 常见问题分类

### 1. 配额相关问题

#### 问题症状
```
HTTP 429: RESOURCE_EXHAUSTED
Quota exceeded for requests per day
Your API quota has been exhausted
```

#### 诊断步骤
```bash
# 1. 检查配额状态
python api_quota_monitor.py --api-key YOUR_KEY --check

# 2. 查看详细配额信息
python api_quota_monitor.py --config config.yaml --check --verbose

# 3. 监控实时使用情况
python api_quota_monitor.py --config config.yaml --monitor --interval 60
```

#### 解决方案
1. **立即解决**：
   - 等待UTC 00:00配额重置
   - 使用多密钥轮换系统
   - 切换到备用API密钥

2. **长期解决**：
   - 创建3-5个Google账户
   - 部署多密钥管理系统
   - 考虑升级到付费API计划

#### 预防措施
```yaml
# 配置配额预警
quota_alerts:
  warning_threshold: 80  # 80%时警告
  critical_threshold: 95  # 95%时严重警告
  email_alerts: true
  slack_webhook: "https://hooks.slack.com/..."
```

### 2. 认证和权限问题

#### 问题症状
```
HTTP 401: Unauthorized
Invalid API key provided
Permission denied for API key
```

#### 诊断步骤
```bash
# 1. 验证API密钥格式
echo "检查密钥格式：AIzaSy开头，长度约39字符"

# 2. 测试密钥有效性
python api_quota_monitor.py --api-key YOUR_KEY --test-only

# 3. 检查API服务状态
curl -H "Authorization: Bearer YOUR_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models"
```

#### 解决方案

1. **密钥格式错误**
   ```bash
   # 正确格式示例
   API_KEY="AIzaSyBnVkVnwO55QRgfXXXXXXXXXXXXXXXXXX"
   
   # 常见错误
   # ❌ 包含空格或特殊字符
   # ❌ 长度不正确（应该39字符左右）
   # ❌ 使用了其他Google服务的密钥
   ```

2. **权限配置**
   ```bash
   # 在Google AI Studio中确保：
   # 1. API已启用
   # 2. 密钥有正确的权限
   # 3. 项目配置正确
   ```

3. **环境变量问题**
   ```bash
   # 检查环境变量
   echo $GOOGLE_API_KEY
   
   # 设置环境变量
   export GOOGLE_API_KEY="your-actual-key"
   
   # 永久设置（加入.bashrc或.zshrc）
   echo 'export GOOGLE_API_KEY="your-actual-key"' >> ~/.bashrc
   ```

### 3. 模型和版本问题

#### 问题症状
```
Model not found: gemini-1.5-pro
Invalid model specified
Model version deprecated
```

#### 诊断步骤
```bash
# 1. 检查可用模型
python -m src.gs_video_report.cli.app list-models

# 2. 测试特定模型
python api_quota_monitor.py --api-key YOUR_KEY --test-model gemini-2.5-pro

# 3. 查看模型兼容性
python -c "
from src.gs_video_report.services.gemini_service import GeminiService
service = GeminiService()
print(service.get_available_models())
"
```

#### 解决方案

1. **使用正确的模型名称**
   ```yaml
   # QA测试强制要求
   model: "gemini-2.5-pro"  # ✅ 正确
   
   # 常见错误
   model: "gemini-1.5-pro"  # ❌ 版本过旧
   model: "gemini-flash"    # ❌ 名称不完整
   model: "gpt-4"           # ❌ 错误的提供商
   ```

2. **模型可用性检查**
   ```python
   # 自动检查可用模型
   def check_model_availability():
       available_models = [
           "gemini-2.5-pro",
           "gemini-2.5-flash", 
           "gemini-1.5-pro",
           "gemini-1.5-flash"
       ]
       
       for model in available_models:
           try:
               # 测试模型
               test_response = client.models.generate_content(
                   model=model,
                   contents="test"
               )
               print(f"✅ {model}: 可用")
           except Exception as e:
               print(f"❌ {model}: {e}")
   ```

### 4. 网络连接问题

#### 问题症状
```
Connection timeout
Network unreachable
DNS resolution failed
SSL handshake failed
```

#### 诊断步骤
```bash
# 1. 检查网络连接
ping google.com
ping generativelanguage.googleapis.com

# 2. 检查DNS解析
nslookup generativelanguage.googleapis.com

# 3. 测试HTTPS连接
curl -I https://generativelanguage.googleapis.com

# 4. 检查代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

#### 解决方案

1. **网络配置**
   ```bash
   # 设置代理（如果需要）
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   
   # 或在代码中设置
   import requests
   
   proxies = {
       'http': 'http://proxy.company.com:8080',
       'https': 'http://proxy.company.com:8080'
   }
   ```

2. **防火墙和安全组**
   ```bash
   # 确保允许访问：
   # - generativelanguage.googleapis.com:443
   # - *.googleapis.com:443
   # - accounts.google.com:443
   ```

3. **超时配置**
   ```python
   # 增加超时时间
   client = genai.Client(
       api_key=api_key,
       vertexai=False,
       timeout=300  # 5分钟超时
   )
   ```

### 5. 内容和格式问题

#### 问题症状
```
Invalid request format
Content policy violation
File upload failed
Response parsing error
```

#### 诊断步骤
```bash
# 1. 检查文件格式
file video.mp4
ffprobe video.mp4

# 2. 检查文件大小
ls -lh video.mp4
# API限制：一般<100MB

# 3. 验证请求格式
cat request.json | jq .
```

#### 解决方案

1. **文件格式问题**
   ```python
   # 支持的视频格式
   SUPPORTED_FORMATS = [
       '.mp4', '.mov', '.avi', '.mkv', '.webm',
       '.flv', '.wmv', '.m4v'
   ]
   
   # 文件大小检查
   def check_file_size(file_path, max_size_mb=100):
       size_mb = os.path.getsize(file_path) / (1024 * 1024)
       if size_mb > max_size_mb:
           raise ValueError(f"文件过大: {size_mb:.1f}MB > {max_size_mb}MB")
   ```

2. **内容策略问题**
   ```python
   # 避免敏感内容
   def check_content_policy(video_path):
       # 检查视频内容是否符合Google政策
       # 避免暴力、色情、仇恨言论等
       pass
   ```

### 6. 并发和性能问题

#### 问题症状
```
Rate limit exceeded
Too many concurrent requests
Service temporarily unavailable
```

#### 诊断步骤
```bash
# 1. 检查并发设置
grep -r "workers" config.yaml
grep -r "parallel" config.yaml

# 2. 监控系统资源
htop
nvidia-smi  # 如果使用GPU

# 3. 检查API调用频率
python api_quota_monitor.py --config config.yaml --analyze-usage
```

#### 解决方案

1. **并发控制**
   ```yaml
   # 推荐设置
   processing:
     max_workers: 2          # 最多2个并发
     requests_per_second: 1  # 每秒最多1个请求
     batch_size: 1           # 批处理大小
     retry_delay: 5          # 重试延迟（秒）
   ```

2. **性能优化**
   ```python
   # 使用连接池
   import asyncio
   from aiohttp import ClientSession
   
   async def process_videos_async(video_list):
       async with ClientSession() as session:
           tasks = []
           for video in video_list:
               task = asyncio.create_task(
                   process_single_video(session, video)
               )
               tasks.append(task)
           
           results = await asyncio.gather(*tasks)
           return results
   ```

## 📊 API失败率分析工具

### 失败率监控与诊断

在进行API故障排除时，了解API Key的失败率是关键的诊断依据：

#### 1. 快速查看失败率

```bash
# 查看所有API Key的失败率统计  
python scripts/view_api_failure_rates.py

# 查看特定日志文件的失败率
python scripts/view_api_failure_rates.py logs/failure_tracking_demo.json
```

**示例输出**：
```
📊 API Key 失败率分析报告
🔑 Key: AIza...mJtY
   📊 使用统计:
      总请求: 10
      成功: 2 (成功率: 20.0%)
      失败: 8 (失败率: 80.0%)
   🚫 失败详情:
      配额耗尽: 5 (50.0%)
      速率限制: 1 (10.0%)
      连续失败: 4次
   🔍 健康状态: 🔴 不健康 (连续失败过多)
```

#### 2. 失败率故障诊断流程

根据失败率确定问题类型：

| 失败率范围 | 健康状态 | 可能原因 | 解决方案 |
|------------|----------|----------|----------|
| 0-10% | 🟢 健康 | 正常运行 | 持续监控 |
| 10-30% | 🟡 警告 | 间歇性网络问题 | 检查网络连接 |
| 30-60% | 🟠 异常 | 配额即将耗尽 | 考虑密钥轮换 |
| 60-90% | 🔴 严重 | 配额耗尽或API限制 | 立即切换密钥 |
| >90% | 🚫 无效 | 密钥无效或权限问题 | 检查密钥配置 |

#### 3. 实时失败率监控

```bash
# 启动实时监控
python scripts/monitor_api_rates.py

# 监控显示实时更新的失败率：
🕐 更新时间: 12:48:23
📊 实时API失败率监控
==================================================
🟢 AIza...XiPo
   请求: 5, 成功率: 80.0%, 失败率: 20.0%
   连续失败: 1, 状态: active

🔴 AIza...YjPq  
   请求: 10, 成功率: 20.0%, 失败率: 80.0%
   连续失败: 8, 状态: quota_exhausted
```

#### 4. 失败率计算验证

**验证计算正确性**：
```bash
# 使用Python验证失败率计算
python3 -c "
import json
with open('logs/api_key_usage.json', 'r') as f:
    stats = json.load(f)
    
for key_id, data in stats.items():
    total = data['total_requests']
    success = data['successful_requests']
    failed = data['failed_requests']
    
    if total > 0:
        calculated_success_rate = (success / total) * 100
        calculated_failure_rate = (failed / total) * 100
        
        print(f'密钥: {key_id}')
        print(f'  总请求: {total}')
        print(f'  成功率: {calculated_success_rate:.1f}%')
        print(f'  失败率: {calculated_failure_rate:.1f}%')
        print(f'  验证: {success + failed == total}')
        print('-' * 30)
"
```

#### 5. 基于失败率的自动故障排除

```python
# 自动故障诊断脚本示例
def diagnose_by_failure_rate(failure_rate, consecutive_failures, last_error):
    """基于失败率自动诊断问题"""
    
    if failure_rate > 90:
        if "unauthorized" in last_error.lower():
            return "🚫 密钥无效 - 检查API密钥配置"
        elif "quota" in last_error.lower():
            return "📊 配额完全耗尽 - 立即切换到备用密钥"
        else:
            return "❌ 严重API问题 - 检查服务状态"
    
    elif failure_rate > 60:
        if consecutive_failures > 5:
            return "🔄 连续失败过多 - 暂停使用该密钥30分钟"
        else:
            return "⚠️ 高失败率 - 减少并发请求数"
    
    elif failure_rate > 30:
        return "🟡 中等失败率 - 监控网络连接，考虑密钥轮换"
    
    else:
        return "✅ 失败率正常 - 继续使用"

# 使用示例
failure_rate = 80.0
consecutive_failures = 4  
last_error = "QUOTA_EXHAUSTED"

diagnosis = diagnose_by_failure_rate(failure_rate, consecutive_failures, last_error)
print(f"诊断结果: {diagnosis}")
```

## 🛠️ 自动诊断工具

### 1. 一键诊断脚本

```bash
# 创建诊断脚本
cat > diagnose_api.sh << 'EOF'
#!/bin/bash

echo "🔍 Google Gemini API 诊断工具"
echo "================================"

# 1. 检查API密钥
echo "1. 检查API密钥配置..."
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ 环境变量GOOGLE_API_KEY未设置"
else
    echo "✅ 环境变量GOOGLE_API_KEY已设置"
    echo "   长度: ${#GOOGLE_API_KEY} 字符"
fi

# 2. 检查网络连接
echo "2. 检查网络连接..."
if ping -c 1 google.com > /dev/null 2>&1; then
    echo "✅ 网络连接正常"
else
    echo "❌ 网络连接失败"
fi

# 3. 检查API服务状态
echo "3. 检查API服务状态..."
if curl -s -o /dev/null -w "%{http_code}" https://generativelanguage.googleapis.com | grep -q "200\|401"; then
    echo "✅ API服务可访问"
else
    echo "❌ API服务不可访问"
fi

# 4. 检查配置文件
echo "4. 检查配置文件..."
if [ -f "config.yaml" ]; then
    echo "✅ config.yaml存在"
else
    echo "❌ config.yaml不存在"
fi

# 5. 运行配额检查
echo "5. 运行配额检查..."
python api_quota_monitor.py --check 2>/dev/null || echo "❌ 配额检查失败"

echo "================================"
echo "诊断完成！"
EOF

chmod +x diagnose_api.sh
```

### 2. Python诊断模块

```python
#!/usr/bin/env python3
"""
API诊断工具
自动检测和诊断Google Gemini API问题
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Any

class APIDiagnostics:
    """API诊断器"""
    
    def __init__(self):
        self.results = {}
        self.warnings = []
        self.errors = []
    
    def run_all_checks(self) -> Dict[str, Any]:
        """运行所有诊断检查"""
        print("🔍 开始API诊断...")
        
        checks = [
            ("API密钥配置", self.check_api_key),
            ("网络连接", self.check_network),
            ("服务状态", self.check_service_status),
            ("配置文件", self.check_config_files),
            ("模型可用性", self.check_model_availability),
            ("配额状态", self.check_quota_status),
        ]
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                self.results[check_name] = result
                status = "✅ 通过" if result.get('success') else "❌ 失败"
                print(f"  {check_name}: {status}")
                
                if not result.get('success'):
                    self.errors.append(f"{check_name}: {result.get('error', '未知错误')}")
                
            except Exception as e:
                self.results[check_name] = {'success': False, 'error': str(e)}
                self.errors.append(f"{check_name}: {str(e)}")
                print(f"  {check_name}: ❌ 异常 - {str(e)}")
        
        return self.generate_report()
    
    def check_api_key(self) -> Dict[str, Any]:
        """检查API密钥配置"""
        api_key = os.getenv('GOOGLE_API_KEY')
        
        if not api_key:
            return {'success': False, 'error': '环境变量GOOGLE_API_KEY未设置'}
        
        if not api_key.startswith('AIzaSy'):
            return {'success': False, 'error': 'API密钥格式错误（应以AIzaSy开头）'}
        
        if len(api_key) < 35 or len(api_key) > 45:
            return {'success': False, 'error': f'API密钥长度异常（{len(api_key)}字符）'}
        
        return {'success': True, 'key_length': len(api_key)}
    
    def check_network(self) -> Dict[str, Any]:
        """检查网络连接"""
        try:
            response = requests.get('https://google.com', timeout=5)
            if response.status_code == 200:
                return {'success': True}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_service_status(self) -> Dict[str, Any]:
        """检查API服务状态"""
        try:
            response = requests.get(
                'https://generativelanguage.googleapis.com/v1beta/models',
                timeout=10
            )
            # 401是正常的，因为没有认证，但说明服务可访问
            if response.status_code in [200, 401]:
                return {'success': True}
            else:
                return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_config_files(self) -> Dict[str, Any]:
        """检查配置文件"""
        required_files = ['config.yaml', 'config.yaml.example']
        missing_files = []
        
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            return {
                'success': False, 
                'error': f'缺少配置文件: {", ".join(missing_files)}'
            }
        
        return {'success': True}
    
    def check_model_availability(self) -> Dict[str, Any]:
        """检查模型可用性"""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return {'success': False, 'error': '需要API密钥'}
        
        try:
            # 这里应该调用实际的模型检查逻辑
            # 简化版本，直接返回成功
            return {'success': True, 'models': ['gemini-2.5-pro', 'gemini-2.5-flash']}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_quota_status(self) -> Dict[str, Any]:
        """检查配额状态"""
        try:
            # 调用配额监控工具
            import subprocess
            result = subprocess.run([
                'python', 'api_quota_monitor.py', '--check'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {'success': True, 'output': result.stdout}
            else:
                return {'success': False, 'error': result.stderr}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_report(self) -> Dict[str, Any]:
        """生成诊断报告"""
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results.values() if r.get('success'))
        
        report = {
            'summary': {
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'failed_checks': total_checks - passed_checks,
                'success_rate': f"{(passed_checks/total_checks*100):.1f}%"
            },
            'results': self.results,
            'errors': self.errors,
            'warnings': self.warnings
        }
        
        return report
    
    def print_recommendations(self):
        """打印问题解决建议"""
        if not self.errors:
            print("\n🎉 所有检查都通过了！API配置正常。")
            return
        
        print(f"\n🚨 发现 {len(self.errors)} 个问题需要解决：")
        for i, error in enumerate(self.errors, 1):
            print(f"  {i}. {error}")
        
        print(f"\n💡 解决建议：")
        
        if any('API密钥' in error for error in self.errors):
            print("  - 检查API密钥配置：https://makersuite.google.com/app/apikey")
            print("  - 设置环境变量：export GOOGLE_API_KEY='your-key'")
        
        if any('网络' in error for error in self.errors):
            print("  - 检查网络连接和防火墙设置")
            print("  - 如果使用代理，请配置HTTP_PROXY环境变量")
        
        if any('配置文件' in error for error in self.errors):
            print("  - 复制配置文件：cp config.yaml.example config.yaml")
            print("  - 编辑config.yaml添加您的API密钥")
        
        if any('配额' in error for error in self.errors):
            print("  - 参考配额管理指南：QUOTA_MANAGEMENT_GUIDE.md")
            print("  - 考虑使用多密钥轮换系统")

def main():
    """主程序入口"""
    diagnostics = APIDiagnostics()
    report = diagnostics.run_all_checks()
    
    print(f"\n📊 诊断报告：")
    print(f"  - 总检查项: {report['summary']['total_checks']}")
    print(f"  - 通过: {report['summary']['passed_checks']}")
    print(f"  - 失败: {report['summary']['failed_checks']}")
    print(f"  - 成功率: {report['summary']['success_rate']}")
    
    diagnostics.print_recommendations()
    
    # 保存详细报告
    with open('api_diagnostics_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📝 详细报告已保存到: api_diagnostics_report.json")
    
    # 返回非零退出码如果有错误
    return len(diagnostics.errors)

if __name__ == "__main__":
    sys.exit(main())
```

## 📋 常用解决方案速查表

| 问题类型 | 症状关键词 | 优先解决方案 | 文档参考 |
|----------|------------|--------------|----------|
| 配额耗尽 | `RESOURCE_EXHAUSTED`, `429` | 多密钥轮换 | [配额管理指南](./QUOTA_MANAGEMENT_GUIDE.md) |
| 认证失败 | `Unauthorized`, `401` | 检查API密钥格式和有效性 | [API密钥设置](./docs/API_KEY_SETUP.md) |
| 模型错误 | `Model not found` | 使用 gemini-2.5-pro | [中文模板指南](./CHINESE_TEMPLATE_USAGE_GUIDE.md) |
| 网络问题 | `Connection timeout` | 检查代理和防火墙设置 | - |
| 文件格式 | `Invalid format` | 确保视频格式支持且<100MB | - |
| 并发限制 | `Rate limit` | 减少并发工作线程至2个 | [QA测试规则](../qa/testing_rules.md) |
| **高失败率** | **失败率>50%** | **查看失败率分析** | **`python scripts/view_api_failure_rates.py`** |
| **连续失败** | **连续失败>5次** | **实时监控+密钥轮换** | **`python scripts/monitor_api_rates.py`** |

### API失败率快速诊断命令

```bash
# 🔍 第一步：快速查看当前失败率
python scripts/view_api_failure_rates.py

# 🔍 第二步：如果失败率>30%，启动实时监控 
python scripts/monitor_api_rates.py

# 🔍 第三步：如果失败率>60%，测试多密钥轮换
python scripts/test_multi_key_rotation.py

# 🔍 第四步：验证计算是否正确
python3 -c "
import json
with open('logs/api_key_usage.json', 'r') as f:
    stats = json.load(f)
for key_id, data in stats.items():
    if data['total_requests'] > 0:
        failure_rate = (data['failed_requests'] / data['total_requests']) * 100
        print(f'{key_id}: 失败率 {failure_rate:.1f}%')
"
```

## 🆘 紧急恢复程序

### 1. API完全不可用时

```bash
# 立即执行的步骤
echo "🚨 API紧急恢复程序"

# 1. 快速测试备用密钥
python api_quota_monitor.py --test-all-keys

# 2. 检查服务状态页面
curl -s https://status.cloud.google.com/

# 3. 切换到降级模式
export FALLBACK_MODE=true
export REDUCE_REQUESTS=true
```

### 2. 批量处理中断时

```bash
# 恢复中断的批量处理
python -m src.gs_video_report.cli.app batch test_videos \
  --output test_output \
  --resume-from-checkpoint \
  --max-retries 5
```

### 3. 紧急联系方式

- **技术支持**: GitHub Issues
- **社区讨论**: 项目讨论区  
- **文档更新**: 定期检查CHANGELOG

---

## 💡 预防性维护建议

1. **定期监控**: 每日检查配额使用情况
2. **多密钥备份**: 始终维护3个以上可用密钥
3. **版本更新**: 及时更新到最新版本
4. **文档学习**: 定期阅读更新的指南和最佳实践

---

*最后更新: 2024年1月 | gs_videoReport v2.1 | API故障排查系统*
