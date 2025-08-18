# QA测试设置说明

## 🔑 API密钥配置

### 第一步：获取Google Gemini API密钥
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建新的API密钥
3. 复制生成的API密钥

### 第二步：配置测试环境
```bash
# 复制测试配置文件并设置API密钥
cp test_config.yaml test_config_local.yaml

# 编辑配置文件，将 YOUR_GEMINI_API_KEY_HERE 替换为实际的API密钥
# 或者使用环境变量（更安全）
export GOOGLE_GEMINI_API_KEY="your_actual_api_key_here"
```

## 🧪 执行完整功能测试

### 测试TC003: 中文转录模板功能
```bash
# 方法1: 使用测试脚本（推荐）
python tests/execute_qa_tests.py --test-case TC003

# 方法2: 直接使用CLI（手动测试）
python -m src.gs_video_report.cli main \
    "test_videos/public_test_7r7ZDugy3EE.webm" \
    --template chinese_transcript \
    --output ./test_output \
    --config test_config_local.yaml \
    --verbose
```

### 预期输出验证
生成的文件应包含：

1. **YAML Frontmatter**:
```yaml
---
title: "视频标题"
author: "讲者名字"
type: "lesson_plan"
template_used: "chinese_transcript" 
tags: ["lesson_plan", "video_analysis"]
---
```

2. **中文转录内容结构**:
```markdown
# 视频标题 - 中文逐字稿分析

## 基本信息
- 视频标题：xxx
- 视频时长：xxx
- 分析时间：2025-01-27T16:xx:xx

## 逐字稿内容

### [00:15] 讲者名称
转录的中文内容...

### [02:30] 讲者名称
更多转录内容...

## 重点整理（第一人称视角）
我从这个视频中学到了...

## 关键术语和人物
- 术语1 (English Term)：中文解释
- 人物1 (English Name)：背景介绍

## 图像补充信息
图像分析补充的信息...
```

## 📊 测试验证检查点

### ✅ 格式验证
- [ ] YAML frontmatter格式正确
- [ ] 包含所有必需的metadata字段
- [ ] 文件编码为UTF-8
- [ ] 时间戳格式 `[MM:SS]` 或 `[HH:MM:SS]`

### ✅ 内容验证  
- [ ] 生成简体中文逐字稿
- [ ] 包含讲者标识
- [ ] 第一人称重点整理存在
- [ ] 术语和人物使用英语显示
- [ ] 时间戳与内容对应

### ✅ 功能验证
- [ ] 文件成功保存到指定目录
- [ ] 文件名包含时间戳信息
- [ ] 处理时间在合理范围内
- [ ] 无严重错误或崩溃

## 🚨 常见问题排查

### API密钥问题
```bash
# 错误: API key not valid
# 解决: 检查API密钥是否正确设置
grep "api_key" test_config_local.yaml
```

### 视频格式问题
```bash
# 错误: Video format not supported  
# 解决: 检查支持的格式列表
python -m src.gs_video_report.cli --help
```

### 内存或超时问题
```bash
# 解决: 调整配置文件中的超时设置
# processing_timeout_seconds: 900  # 15分钟
# max_file_size_mb: 200
```

## 📋 测试报告记录

每次测试后记录：
- 测试时间和环境
- 视频文件信息（大小、时长、格式）
- 处理时间和性能指标
- 生成文件质量评分
- 发现的问题和改进建议

## 🎯 成功标准

测试通过标准：
- 所有格式验证通过 ✅
- 中文转录质量满足要求 ✅  
- 时间戳准确度 > 95% ✅
- 第一人称整理逻辑清晰 ✅
- 术语标识正确率 > 90% ✅
- 无功能性错误 ✅
