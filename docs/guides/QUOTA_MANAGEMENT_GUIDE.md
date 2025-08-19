# 📊 Google Gemini API 配额管理完整指南

> **版本**: v2.1 | **更新时间**: 2024年1月  
> **适用于**: gs_videoReport v2.1+ with 多密钥轮换支持

## 🎯 概述

本指南提供完整的Google Gemini API配额管理解决方案，帮助用户解决API配额耗尽问题，实现大规模视频批量处理。

## 🚨 核心问题诊断

### 常见配额限制问题

1. **免费层限制**
   - 每日100个请求（非6M tokens）
   - 每个视频处理约消耗5个请求
   - 实际可处理约20个视频/天

2. **配额耗尽症状**
   ```
   HTTP 429: RESOURCE_EXHAUSTED
   Quota exceeded for requests
   ```

3. **影响评估**
   - 单密钥每日最多处理20个视频
   - 批量处理会被阻塞
   - 需要等待24小时重置

## 🛠️ 解决方案架构

### 1. API配额监控工具

```bash
# 实时监控配额状态
python api_quota_monitor.py --api-key YOUR_KEY --check

# 持续监控模式
python api_quota_monitor.py --config config.yaml --monitor --interval 300
```

**功能特点**：
- ✅ 实时配额使用监控
- ✅ 多密钥状态跟踪  
- ✅ 处理能力预估
- ✅ 模型可用性检测
- ✅ Rich界面可视化

### 2. 多密钥智能轮换处理器

```python
from multi_key_processor import MultiKeyProcessor

# 配置多个API密钥
api_keys = {
    "account_1": "AIzaSyXXXXXXXXXXXXXXXXXX",
    "account_2": "AIzaSyYYYYYYYYYYYYYYYYYY", 
    "account_3": "AIzaSyZZZZZZZZZZZZZZZZZZ",
}

# 创建处理器
processor = MultiKeyProcessor(api_keys)

# 自动轮换处理视频
result = processor.process_video_with_rotation(video_path, prompt)
```

**智能特性**：
- 🔄 自动密钥轮换
- 🧠 智能负载均衡
- 💾 配额使用跟踪
- 🛡️ 错误恢复机制
- ⚡ 并发处理支持

## 📋 部署步骤

### Step 1: 创建多个Google账户

1. **新建Google账户**
   ```
   账户1: your_name+video1@gmail.com
   账户2: your_name+video2@gmail.com  
   账户3: your_name+video3@gmail.com
   ```

2. **为每个账户申请API密钥**
   - 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
   - 创建新项目（每个账户）
   - 生成API密钥

### Step 2: 配置多密钥系统

创建 `multi_key_config.yaml`:

```yaml
# 多密钥配置
api_keys:
  account_1:
    key: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX"
    name: "主账户"
    daily_limit: 100
  account_2:
    key: "AIzaSyYYYYYYYYYYYYYYYYYYYYYYYY"  
    name: "备用账户1"
    daily_limit: 100
  account_3:
    key: "AIzaSyZZZZZZZZZZZZZZZZZZZZZZZZ"
    name: "备用账户2"
    daily_limit: 100

# 处理配置
processing:
  max_concurrent_keys: 2
  requests_per_video: 5
  safety_buffer: 10
  retry_attempts: 3

# 监控配置
monitoring:
  check_interval: 300  # 5分钟
  quota_warning_threshold: 20
  save_status_file: true
```

### Step 3: 集成到现有工作流

修改 `config.yaml`:

```yaml
# 启用多密钥支持
multi_key_support: true
multi_key_config_path: "multi_key_config.yaml"

# QA测试配置（保持不变）
qa_testing:
  input_directory: "test_videos"
  output_directory: "test_output" 
  template: "chinese_transcript"
  model: "gemini-2.5-pro"

# 并发控制
parallel_workers: 2
```

## 🔧 实际使用示例

### 1. 配额状态检查

```bash
# 检查所有密钥状态
python api_quota_monitor.py --config multi_key_config.yaml --check

# 输出示例:
📊 整体状态概览
活跃密钥: 2/3
剩余请求: ~150 个  
可处理视频: ~30 个

密钥状态详情
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ 密钥名称      ┃ 状态     ┃ 已用请求 ┃ 剩余估算 ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ account_1     │ ❌ 耗尽  │ 100      │ 0        │
│ account_2     │ ✅ 良好  │ 25       │ 75       │  
│ account_3     │ ✅ 良好  │ 30       │ 70       │
└───────────────┴──────────┴──────────┴──────────┘
```

### 2. 批量处理（多密钥版）

```bash
# 使用多密钥处理大批量视频
python -m src.gs_video_report.cli.app batch test_videos \
  --output test_output \
  --multi-key-config multi_key_config.yaml \
  --workers 2 \
  --verbose
```

### 3. 编程接口使用

```python
# 直接使用多密钥处理器
from multi_key_processor import MultiKeyProcessor

def process_video_batch(video_files, api_keys):
    processor = MultiKeyProcessor(api_keys)
    
    results = []
    for video_file in video_files:
        result = processor.process_video_with_rotation(
            video_path=video_file,
            prompt="请生成中文教学报告"
        )
        
        if result["success"]:
            print(f"✅ {video_file} 处理成功")
            results.append(result["content"])
        else:
            print(f"❌ {video_file} 处理失败: {result['error']}")
    
    # 显示最终状态
    processor.display_status()
    return results
```

## 📈 性能优化指南

### 1. 配额使用优化

```yaml
# 优化设置
processing_optimization:
  # 减少每视频请求数
  enable_request_bundling: true
  
  # 智能重试机制
  exponential_backoff: true
  max_retry_delay: 300
  
  # 预缓存机制
  enable_response_caching: true
  cache_duration_hours: 24
```

### 2. 并发处理策略

```python
# 自适应并发控制
class AdaptiveConcurrencyControl:
    def __init__(self, api_keys):
        self.available_keys = len(api_keys)
        self.optimal_workers = min(self.available_keys, 4)
    
    def get_worker_count(self, queue_size):
        """根据队列大小调整并发数"""
        if queue_size < 10:
            return max(1, self.optimal_workers // 2)
        elif queue_size < 50:
            return self.optimal_workers
        else:
            return min(self.optimal_workers * 2, self.available_keys)
```

### 3. 成本控制措施

| 策略 | 节省效果 | 实现难度 | 推荐程度 |
|------|----------|----------|----------|
| 多密钥轮换 | 300%+ | 中等 | ⭐⭐⭐⭐⭐ |
| 请求合并 | 20-30% | 简单 | ⭐⭐⭐⭐ |
| 响应缓存 | 50-70% | 中等 | ⭐⭐⭐⭐ |
| 智能重试 | 10-15% | 简单 | ⭐⭐⭐ |

## 🚨 故障排查指南

### 常见问题诊断

1. **所有密钥都显示耗尽**
   ```bash
   # 重新测试所有密钥
   python api_quota_monitor.py --config multi_key_config.yaml --check --force-refresh
   ```

2. **密钥轮换失败**
   ```python
   # 检查密钥有效性
   def validate_all_keys(api_keys):
       for name, key in api_keys.items():
           try:
               client = genai.Client(api_key=key, vertexai=False)
               response = client.models.generate_content(
                   model='gemini-2.5-pro',
                   contents='test'
               )
               print(f"✅ {name}: 有效")
           except Exception as e:
               print(f"❌ {name}: {e}")
   ```

3. **处理性能下降**
   ```bash
   # 性能分析和优化
   python -m src.gs_video_report.cli.app benchmark \
     --multi-key-config multi_key_config.yaml \
     --test-videos 5 \
     --profile-performance
   ```

### 紧急恢复方案

1. **立即获取新密钥**
   - 创建新Google账户
   - 立即申请API密钥
   - 添加到配置文件

2. **切换到付费API**
   ```yaml
   # 临时付费配置
   emergency_config:
     use_paid_tier: true
     monthly_budget_limit: 100  # USD
     auto_scale_quota: true
   ```

3. **降级处理模式**
   ```yaml
   # 降级设置
   fallback_config:
     model: "gemini-1.5-flash"  # 更便宜的模型
     reduce_analysis_depth: true
     skip_visual_analysis: true
   ```

## 📊 监控仪表盘

### 实时监控界面

```bash
# 启动实时仪表盘
python api_quota_monitor.py \
  --config multi_key_config.yaml \
  --monitor \
  --interval 60 \
  --dashboard
```

**仪表盘功能**：
- 📈 实时配额使用图表
- 🔄 密钥轮换状态
- ⚡ 处理速度统计
- 💰 成本消耗追踪
- 🚨 异常告警提醒

### API失败率监控 

#### 1. 查看详细失败率统计

```bash
# 使用专用的失败率分析工具
python scripts/view_api_failure_rates.py

# 查看特定统计文件
python scripts/view_api_failure_rates.py logs/api_key_usage.json
```

**输出示例**：
```
📊 API Key 失败率分析报告
📅 生成时间: 2025-08-19 12:48:07
📁 数据源: logs/api_key_usage.json

🔑 API Key: AIza...XiPo
   📊 使用统计:
      总请求: 10
      成功: 6 (成功率: 60.0%)
      失败: 4 (失败率: 40.0%)
   🚫 失败详情:
      配额耗尽: 3 (30.0%)
      速率限制: 1 (10.0%)
      连续失败: 2次
   🔍 健康状态: 🟡 不稳定 (成功率低)
```

#### 2. 实时失败率监控

```bash
# 启动实时监控（每5秒更新）
python scripts/monitor_api_rates.py

# 自定义监控间隔
python scripts/monitor_api_rates.py --interval 10
```

#### 3. 失败率计算公式

**标准计算方法**：
```
失败率 = 失败请求数 ÷ 总请求数 × 100%
成功率 = 成功请求数 ÷ 总请求数 × 100%

健康判断标准：
- 🟢 健康: 成功率 > 80%
- 🟡 警告: 50% ≤ 成功率 ≤ 80%  
- 🔴 不健康: 成功率 < 50% 或连续失败 > 5次
```

#### 4. 命令行快速查看

```bash
# 使用jq快速分析JSON统计
cat logs/api_key_usage.json | jq -r '
to_entries[] | 
select(.value.total_requests > 0) | 
"🔑 Key: \(.key)
   成功率: \((.value.successful_requests / .value.total_requests * 100 | . * 10 | round / 10))%
   失败率: \((.value.failed_requests / .value.total_requests * 100 | . * 10 | round / 10))%
   状态: \(.value.current_status)"
'

# Python一行命令分析
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

### 报告生成

```bash
# 生成每日配额报告
python api_quota_monitor.py --generate-report daily

# 生成成本分析报告
python api_quota_monitor.py --generate-report cost-analysis
```

## 🔮 未来规划

### v2.2 增强功能

1. **自动密钥管理**
   - Google账户自动化创建
   - API密钥自动申请
   - 密钥生命周期管理

2. **智能成本优化**
   - 机器学习驱动的请求优化
   - 动态模型选择
   - 预测性配额管理

3. **企业级功能**
   - 团队配额池共享
   - 详细计费追踪
   - 合规性报告

## 💡 最佳实践建议

### 1. 配额管理策略
- 🎯 **预防为主**: 始终维持3个以上有效API密钥
- 📊 **定期监控**: 每日检查配额使用状况
- 🔄 **轮换使用**: 均匀分布使用各个密钥
- 💰 **成本控制**: 设置每日/每月消耗上限

### 2. 生产环境部署
- 🛡️ **安全存储**: 使用环境变量或密钥管理服务
- 🏗️ **高可用**: 部署配额监控服务
- 📈 **扩展性**: 支持动态添加新密钥
- 🔍 **可观测**: 完整的日志和指标收集

### 3. 团队协作
- 📋 **文档化**: 维护最新的密钥清单
- 👥 **权限管理**: 限制密钥访问权限
- 🔔 **告警机制**: 配额耗尽自动通知
- 🗂️ **版本控制**: 配置文件版本管理

---

## 🆘 支持与反馈

如果您在使用过程中遇到问题：

1. **检查配置**: 确保所有配置文件格式正确
2. **查看日志**: 检查详细的错误日志信息  
3. **测试密钥**: 使用监控工具验证所有密钥状态
4. **社区支持**: 在GitHub Issues中寻求帮助

---

*最后更新: 2024年1月 | gs_videoReport v2.1 | 多密钥轮换架构*
