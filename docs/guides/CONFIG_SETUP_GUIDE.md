# 🔧 配置设置完整指南

> **版本**: v2.1 | **更新时间**: 2025-01-19  
> **适用于**: gs_videoReport v2.1+ with 多密钥管理

## 🎯 概述

本指南详细介绍gs_videoReport v2.1的配置系统，包括单密钥模式和多密钥轮换模式的完整设置方法。

## 📋 配置文件结构

### 1. 主配置文件 (config.yaml)

```bash
# 复制示例配置
cp config.yaml.example config.yaml

# 编辑配置文件
nano config.yaml  # 或使用您喜欢的编辑器
```

#### 基础配置
```yaml
# Google Gemini API配置
api_key: "your-gemini-api-key-here"

# 默认模板和模型
default_template: "chinese_transcript"  # v2.0纯中文模板
default_model: "gemini-2.5-pro"         # QA测试必须使用

# 输出配置
output:
  directory: "output"
  format: "markdown"
  include_metadata: true
```

#### QA测试强制配置
```yaml
# QA测试标准化配置 (不可修改)
qa_testing:
  input_directory: "test_videos"     # 强制输入目录
  output_directory: "test_output"    # 强制输出目录
  template: "chinese_transcript"     # 强制v2.0中文模板
  model: "gemini-2.5-pro"           # 强制2.5 Pro模型
```

#### 并发处理配置
```yaml
# 并发控制 (防止配额快速耗尽)
parallel_workers: 2              # 最大2个并发
max_concurrent_keys: 2           # 最大并发密钥数
requests_per_video: 5            # 每视频预估请求
safety_buffer: 10                # 安全缓冲请求
```

#### 模板特定配置
```yaml
# v2.1模板优化参数
template_configs:
  chinese_transcript:
    temperature: 1.0             # 增强创造性
    max_tokens: 65536            # 支持超长视频
    top_p: 0.95                  # 输出质量控制
    detail_level: "comprehensive"
    include_visual_analysis: true
    strict_chinese_only: true    # 强制纯中文输出
```

### 2. 多密钥配置文件 (multi_key_config.yaml)

```bash
# 复制多密钥示例配置
cp multi_key_config.yaml.example multi_key_config.yaml

# 编辑多密钥配置
nano multi_key_config.yaml
```

#### 多密钥定义
```yaml
api_keys:
  account_1:
    key: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX"
    name: "主账户"
    daily_limit: 100
    priority: 1
    
  account_2:
    key: "AIzaSyYYYYYYYYYYYYYYYYYYYYYYYY"
    name: "备用账户1"
    daily_limit: 100
    priority: 2
    
  account_3:
    key: "AIzaSyZZZZZZZZZZZZZZZZZZZZZZZZ"
    name: "备用账户2"
    daily_limit: 100
    priority: 3
```

#### 处理策略配置
```yaml
processing:
  max_concurrent_keys: 2        # 同时使用密钥数
  requests_per_video: 5         # 每视频请求预估
  safety_buffer: 10             # 安全缓冲
  retry_attempts: 3             # 重试次数
  exponential_backoff: true     # 指数退避
```

#### 监控配置
```yaml
monitoring:
  check_interval: 300           # 5分钟检查间隔
  quota_warning_threshold: 20   # 警告阈值
  save_status_file: true        # 保存状态文件
  enable_dashboard: true        # Rich仪表盘
```

## 🚀 快速配置步骤

### Step 1: 获取API密钥

1. **访问Google AI Studio**
   - 打开 [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
   - 登录您的Google账户

2. **创建API密钥**
   ```
   点击 "Create API Key" 
   → 选择项目或创建新项目
   → 复制生成的API密钥
   ```

3. **多账户设置** (用于多密钥模式)
   ```
   创建额外的Google账户:
   - your_name+video1@gmail.com
   - your_name+video2@gmail.com
   - your_name+video3@gmail.com
   
   为每个账户重复步骤2
   ```

### Step 2: 配置单密钥模式

1. **复制配置文件**
   ```bash
   cp config.yaml.example config.yaml
   ```

2. **编辑配置**
   ```yaml
   # 填入您的API密钥
   api_key: "AIzaSyYourActualAPIKeyHere"
   
   # 选择模板 (推荐)
   default_template: "chinese_transcript"
   default_model: "gemini-2.5-pro"
   ```

3. **测试配置**
   ```bash
   # 测试单个视频
   python -m src.gs_video_report.cli.app single test_videos/sample.mp4 --output test_output
   ```

### Step 3: 配置多密钥模式

1. **复制多密钥配置**
   ```bash
   cp multi_key_config.yaml.example multi_key_config.yaml
   ```

2. **填入所有API密钥**
   ```yaml
   api_keys:
     account_1:
       key: "AIzaSyYourFirstAPIKey"
       name: "主账户"
     account_2:
       key: "AIzaSyYourSecondAPIKey" 
       name: "备用账户1"
     account_3:
       key: "AIzaSyYourThirdAPIKey"
       name: "备用账户2"
   ```

3. **启用多密钥模式**
   ```yaml
   # 在config.yaml中设置
   multi_key_support: true
   ```

4. **测试多密钥配置**
   ```bash
   # 检查所有密钥状态
   python api_quota_monitor.py --config multi_key_config.yaml --check
   
   # 多密钥批量处理
   python -m src.gs_video_report.cli.app batch test_videos \
     --multi-key-config multi_key_config.yaml \
     --output test_output
   ```

## ⚙️ 高级配置选项

### 1. 环境变量配置

```bash
# 设置环境变量 (优先级最高)
export GOOGLE_API_KEY="your-api-key-here"
export GS_VIDEO_TEMPLATE="chinese_transcript"
export GS_VIDEO_MODEL="gemini-2.5-pro"

# 永久设置 (添加到 .bashrc 或 .zshrc)
echo 'export GOOGLE_API_KEY="your-api-key-here"' >> ~/.bashrc
```

### 2. 配置优先级

1. **命令行参数** (最高优先级)
   ```bash
   python -m src.gs_video_report.cli.app single video.mp4 \
     --api-key YOUR_KEY \
     --template chinese_transcript \
     --model gemini-2.5-pro
   ```

2. **环境变量** (中等优先级)
   ```bash
   export GOOGLE_API_KEY="your-key"
   ```

3. **配置文件** (最低优先级)
   ```yaml
   api_key: "your-key-in-config"
   ```

### 3. 模板自定义配置

```yaml
# 创建自定义模板配置
custom_templates:
  my_chinese_template:
    base_template: "chinese_transcript"
    custom_parameters:
      temperature: 1.2              # 更高创造性
      max_tokens: 32768             # 适中长度
      focus_areas: ["practical", "actionable"]
      output_style: "conversational"
      
  my_english_template:
    base_template: "comprehensive_lesson"
    custom_parameters:
      language: "english"
      detail_level: "advanced"
      include_exercises: true
```

### 4. 日志和调试配置

```yaml
# 详细日志配置
logging:
  level: "DEBUG"                    # DEBUG, INFO, WARNING, ERROR
  file: "logs/gs_video_report.log"  # 日志文件路径
  max_file_size: "10MB"             # 日志文件最大大小
  backup_count: 5                   # 保留日志文件数量
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
# 性能监控
performance:
  enable_timing: true               # 启用性能计时
  enable_memory_monitoring: true    # 启用内存监控
  profile_api_calls: true           # API调用性能分析
```

### 5. 错误处理配置

```yaml
# 全面错误处理策略
error_handling:
  max_retries: 5                    # 最大重试次数
  exponential_backoff: true         # 指数退避
  retry_delay_base: 3               # 基础延迟(秒)
  max_retry_delay: 300              # 最大延迟(秒)
  
  # 不同错误类型的处理
  quota_exhausted:
    auto_switch_key: true           # 自动切换密钥
    notify_user: true               # 通知用户
    
  network_timeout:
    retry_count: 3                  # 网络超时重试
    increase_timeout: true          # 递增超时时间
    
  api_server_error:
    retry_count: 2                  # 服务器错误重试
    backoff_multiplier: 2.0         # 退避倍数
```

## 🔍 配置验证

### 1. 配置文件语法检查

```python
# 创建配置验证脚本
#!/usr/bin/env python3
"""配置文件验证工具"""

import yaml
import sys
from pathlib import Path

def validate_config(config_path: str):
    """验证配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查必需字段
        required_fields = ['api_key', 'default_template', 'default_model']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"❌ 缺少必需字段: {missing_fields}")
            return False
        
        # 检查API密钥格式
        if not config['api_key'].startswith('AIzaSy'):
            print(f"❌ API密钥格式错误")
            return False
            
        print(f"✅ 配置文件验证通过: {config_path}")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ YAML语法错误: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        return False

if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    validate_config(config_file)
```

### 2. API密钥测试

```bash
# 测试API密钥有效性
python api_quota_monitor.py --api-key YOUR_KEY --test-only

# 测试所有多密钥
python api_quota_monitor.py --config multi_key_config.yaml --test-all-keys
```

### 3. 模板配置测试

```bash
# 测试模板渲染
python -c "
from src.gs_video_report.template_manager import TemplateManager
tm = TemplateManager()
template = tm.get_template('chinese_transcript')
print('✅ 模板加载成功')
"
```

## 🛠️ 常见配置问题

### 1. API密钥相关问题

**问题**: `Invalid API key`
```yaml
# 解决方案: 检查密钥格式
api_key: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX"  # ✅ 正确格式
api_key: "your-api-key-here"              # ❌ 占位符未替换
api_key: "AIzaSy12345"                    # ❌ 长度不足
```

**问题**: `Permission denied`
```bash
# 解决方案: 检查API密钥权限
1. 确保API已启用
2. 检查项目配置
3. 验证密钥权限
```

### 2. 模板配置问题

**问题**: `Template not found`
```yaml
# 解决方案: 使用正确的模板名称
default_template: "chinese_transcript"    # ✅ 正确
default_template: "chinese_template"      # ❌ 错误名称
default_template: "ChineseTranscript"     # ❌ 大小写错误
```

### 3. 多密钥配置问题

**问题**: `All keys exhausted`
```yaml
# 解决方案: 检查密钥配置和状态
api_keys:
  account_1:
    key: "有效的API密钥"                  # ✅ 确保密钥有效
    daily_limit: 100                     # ✅ 正确的限制
  # 添加更多密钥以增加容量
```

### 4. QA测试配置问题

**问题**: QA测试失败
```yaml
# 解决方案: 检查强制配置
qa_testing:
  input_directory: "test_videos"         # ✅ 必须是这个目录
  output_directory: "test_output"        # ✅ 必须是这个目录
  template: "chinese_transcript"         # ✅ 必须v2.0模板
  model: "gemini-2.5-pro"               # ✅ 必须2.5 Pro版本
```

## 📊 配置性能优化

### 1. 并发优化

```yaml
# 根据配额情况调整并发数
performance_profiles:
  single_key:
    parallel_workers: 1               # 单密钥保守设置
    max_concurrent_keys: 1
    
  multi_key_conservative:
    parallel_workers: 2               # 多密钥保守设置
    max_concurrent_keys: 2
    
  multi_key_aggressive:
    parallel_workers: 4               # 多密钥激进设置 (需更多密钥)
    max_concurrent_keys: 3
```

### 2. 内存优化

```yaml
# 内存使用优化
memory_optimization:
  batch_size: 5                       # 批处理大小
  clear_cache_interval: 10            # 缓存清理间隔
  max_memory_usage: "2GB"             # 最大内存限制
  
  # 大文件处理
  large_video_threshold: "100MB"      # 大视频阈值
  large_video_strategy: "streaming"   # 流式处理
```

### 3. 网络优化

```yaml
# 网络连接优化
network:
  timeout: 300                        # 请求超时(秒)
  max_connections: 10                 # 最大连接数
  retry_on_timeout: true              # 超时重试
  connection_pool_size: 5             # 连接池大小
  
  # 代理设置 (如需要)
  proxy:
    http: "http://proxy.company.com:8080"
    https: "http://proxy.company.com:8080"
```

## 💡 配置最佳实践

### 1. 安全最佳实践

- ✅ 永远不要将API密钥提交到版本控制
- ✅ 使用环境变量存储敏感信息  
- ✅ 定期轮换API密钥
- ✅ 限制API密钥权限和访问范围
- ✅ 使用不同密钥进行开发和生产

### 2. 性能最佳实践

- ✅ 根据处理量配置合适的并发数
- ✅ 为多密钥设置合理的安全缓冲
- ✅ 启用配额监控和预警
- ✅ 使用适合的模型版本 (2.5 Pro vs Flash)

### 3. 维护最佳实践

- ✅ 定期检查配置文件有效性
- ✅ 监控API使用情况和成本
- ✅ 保持配置文档更新
- ✅ 备份重要的配置设置

---

## 📞 配置支持

### 获取帮助
- **配置问题**: 查看 [故障排查指南](../troubleshooting/API_TROUBLESHOOTING_GUIDE.md)
- **多密钥设置**: 参考 [配额管理指南](./QUOTA_MANAGEMENT_GUIDE.md)
- **模板配置**: 查看 [中文模板指南](./CHINESE_TEMPLATE_USAGE_GUIDE.md)

### 相关文档
- [API密钥设置](../API_KEY_SETUP.md)
- [多密钥管理架构](../architecture/10-多密钥管理架构-multi-key-architecture.md)
- [核心工作流](../architecture/5-核心工作流-core-workflow.md)

---

*最后更新: 2025-01-19 | gs_videoReport v2.1 | 配置系统完整指南*
