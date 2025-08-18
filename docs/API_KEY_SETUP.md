# API密钥设置指南

## 🔑 API密钥配置优先级

gs_videoReport 支持多种API密钥设置方式，按优先级排序：

1. **命令行参数** (最高优先级)
```bash
gs_videoreport video.mp4 --api-key "your_api_key_here"
```

2. **环境变量**
```bash
export GOOGLE_GEMINI_API_KEY="your_api_key_here"
# 或者
export GEMINI_API_KEY="your_api_key_here"
```

3. **配置文件** (config.yaml)
```yaml
google_api:
  api_key: "your_api_key_here"
```

## 🚀 快速设置方法

### 方法1：使用设置向导 ⭐ 推荐
```bash
python -m src.gs_video_report.cli setup-api
```

这会启动交互式向导，帮助您：
- 检查当前API密钥状态
- 获取API密钥的详细步骤
- 选择安全的存储方式
- 自动配置系统

### 方法2：环境变量设置 (推荐用于生产环境)
```bash
# 临时设置 (当前会话)
export GOOGLE_GEMINI_API_KEY="your_actual_api_key_here"

# 永久设置 (添加到shell配置文件)
echo 'export GOOGLE_GEMINI_API_KEY="your_actual_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

### 方法3：直接命令行传递 (适合脚本使用)
```bash
python -m src.gs_video_report.cli main video.mp4 \
    --template chinese_transcript \
    --api-key "your_api_key_here"
```

## 🤖 多模型支持

### 查看可用模型
```bash
python -m src.gs_video_report.cli list-models
```

### 选择特定模型
```bash
# 使用高性能模型 (更准确，但较慢)
gs_videoreport video.mp4 --model gemini-2.5-pro

# 使用平衡模型 (默认)
gs_videoreport video.mp4 --model gemini-2.5-flash  

# 使用快速模型 (更快，但精度稍低)
gs_videoreport video.mp4 --model gemini-2.5-flash-lite
```

## 📋 完整使用示例

### 基础用法
```bash
# 使用中文转录模板
python -m src.gs_video_report.cli main video.mp4 --template chinese_transcript

# 指定输出目录
python -m src.gs_video_report.cli main video.mp4 --output ./my_lessons
```

### 高级用法
```bash
# 完整命令示例
python -m src.gs_video_report.cli main video.mp4 \
    --template chinese_transcript \
    --model gemini-2.5-pro \
    --api-key "your_key" \
    --output ./lessons \
    --verbose

# 使用配置文件
python -m src.gs_video_report.cli main video.mp4 \
    --config my_config.yaml \
    --model gemini-2.5-flash
```

## 🛡️ 安全最佳实践

### ✅ 推荐做法
- 使用环境变量存储API密钥
- 不要在代码中硬编码API密钥
- 定期轮换API密钥
- 在共享系统上使用临时API密钥参数

### ❌ 避免做法
- 不要将API密钥提交到版本控制
- 不要在日志中打印完整的API密钥
- 不要在公共配置文件中存储API密钥

## 🔧 故障排除

### 常见错误及解决方案

#### 1. "API key not valid"
```bash
# 检查API密钥格式
echo $GOOGLE_GEMINI_API_KEY | wc -c  # 应该是40+字符

# 重新获取API密钥
python -m src.gs_video_report.cli setup-api
```

#### 2. "This method is only supported in the Gemini Developer client"
```bash
# 取消Vertex AI模式
unset GOOGLE_GENAI_USE_VERTEXAI
```

#### 3. "Missing 'google_api' section"
```bash
# 使用设置向导创建配置文件
python -m src.gs_video_report.cli setup-api
```

## 📖 相关命令

```bash
# 查看所有可用命令
python -m src.gs_video_report.cli --help

# 查看可用模板
python -m src.gs_video_report.cli list-templates

# 查看可用模型
python -m src.gs_video_report.cli list-models

# API密钥设置向导
python -m src.gs_video_report.cli setup-api

# 查看版本信息
python -m src.gs_video_report.cli version
```

## 🎯 模型选择建议

| 用途 | 推荐模型 | 原因 |
|-----|---------|------|
| 学术研究/详细分析 | gemini-2.5-pro | 最高精度和分析深度 |
| 日常教学视频转录 | gemini-2.5-flash | 平衡的性能和成本 |
| 快速预览/草稿 | gemini-2.5-flash-lite | 快速响应，低成本 |
| 长视频批量处理 | gemini-2.5-flash | 稳定性和成本效益 |

## 💡 提示和技巧

1. **环境变量持久化**: 将API密钥添加到shell配置文件，避免每次重新设置
2. **模型测试**: 先用小视频测试不同模型的效果，选择最适合的
3. **配置复用**: 为不同用途创建不同的配置文件
4. **批量处理**: 编写脚本使用命令行参数进行批量视频处理
