# 批量处理功能 - API接口规范

## 概述

本文档定义批量处理功能的CLI接口规范，包括新增命令、参数定义、配置格式和输出规范。设计遵循现有CLI接口风格，确保用户体验的一致性。

## CLI命令接口设计

### 主命令：batch

#### 基础语法
```bash
gs_videoreport batch [OPTIONS] INPUT_SOURCE
```

#### 完整命令规范
```bash
gs_videoreport batch \
  --input-dir <directory> | --file-list <file> | --url-list <file> \
  [--template <template_name>] \
  [--output <output_directory>] \
  [--parallel <number>] \
  [--config <config_file>] \
  [--progress-file <file>] \
  [--resume-from <checkpoint_id>] \
  [--dry-run] \
  [--skip-existing] \
  [--max-retries <number>] \
  [--timeout <seconds>] \
  [--cost-limit <amount>] \
  [--webhook <url>] \
  [--verbose] \
  [--quiet] \
  [--help]
```

### 参数详细定义

#### 输入源参数 (互斥，必选其一)

##### --input-dir, -d
```bash
--input-dir <directory>
```
- **描述**: 指定包含视频文件的目录
- **行为**: 递归扫描目录中的所有支持格式视频文件
- **支持格式**: mp4, mov, avi, mkv, webm, m4v
- **示例**: 
  ```bash
  gs_videoreport batch --input-dir ./videos/
  gs_videoreport batch -d /path/to/video/library/
  ```

##### --file-list, -f
```bash
--file-list <file_path>
```
- **描述**: 从文件中读取视频文件路径列表
- **格式支持**: TXT (每行一个路径)
- **路径类型**: 支持绝对路径和相对路径
- **示例**:
  ```bash
  gs_videoreport batch --file-list videos.txt
  gs_videoreport batch -f ./input/video_list.txt
  ```
  
  文件格式示例 (videos.txt):
  ```
  ./video1.mp4
  /absolute/path/video2.mov
  ./subfolder/video3.avi
  ```

##### --url-list, -u
```bash
--url-list <file_path>
```
- **描述**: 从文件中读取YouTube URL列表
- **格式支持**: TXT, CSV
- **URL类型**: 支持YouTube各种URL格式
- **示例**:
  ```bash
  gs_videoreport batch --url-list youtube_urls.txt
  gs_videoreport batch -u ./input/video_urls.csv
  ```
  
  TXT格式示例:
  ```
  https://www.youtube.com/watch?v=dQw4w9WgXcQ
  https://youtu.be/dQw4w9WgXcQ
  ```
  
  CSV格式示例:
  ```csv
  url,template,output_name
  https://www.youtube.com/watch?v=dQw4w9WgXcQ,chinese_transcript,video1
  https://youtu.be/xyz123,summary_report,video2
  ```

#### 处理配置参数

##### --template, -t
```bash
--template <template_name>
```
- **描述**: 指定处理模板
- **默认值**: chinese_transcript
- **可选值**: chinese_transcript, comprehensive_lesson, summary_report
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --template comprehensive_lesson
  ```

##### --output, -o
```bash
--output <output_directory>
```
- **描述**: 指定输出目录
- **默认值**: ./batch_output/
- **行为**: 自动创建目录（如不存在）
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --output ./lesson_plans/
  ```

##### --parallel, -p
```bash
--parallel <number>
```
- **描述**: 并发处理任务数
- **默认值**: 4
- **取值范围**: 1-8
- **限制**: 受API限制自动调整
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --parallel 6
  ```

#### 控制参数

##### --config, -c
```bash
--config <config_file>
```
- **描述**: 指定配置文件路径
- **默认值**: ./config.yaml
- **格式**: YAML格式
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --config ./batch_config.yaml
  ```

##### --progress-file
```bash
--progress-file <file_path>
```
- **描述**: 实时进度状态保存文件
- **格式**: JSON格式
- **用途**: 外部监控和集成
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --progress-file ./progress.json
  ```

##### --resume-from
```bash
--resume-from <checkpoint_id>
```
- **描述**: 从指定检查点恢复处理
- **格式**: 检查点ID字符串
- **行为**: 跳过已完成任务，继续未完成任务
- **示例**:
  ```bash
  gs_videoreport batch --resume-from batch_20240818_1630_001
  ```

#### 行为控制参数

##### --dry-run
```bash
--dry-run
```
- **描述**: 干运行模式，仅预览不实际处理
- **行为**: 显示将要处理的文件列表和估算信息
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --dry-run
  ```

##### --skip-existing
```bash
--skip-existing
```
- **描述**: 跳过已存在的输出文件
- **判断依据**: 输出目录中是否存在同名文件
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --skip-existing
  ```

##### --max-retries
```bash
--max-retries <number>
```
- **描述**: 失败任务的最大重试次数
- **默认值**: 3
- **取值范围**: 0-10
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --max-retries 5
  ```

##### --timeout
```bash
--timeout <seconds>
```
- **描述**: 单个任务的超时时间（秒）
- **默认值**: 1800 (30分钟)
- **取值范围**: 300-3600
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --timeout 2400
  ```

##### --cost-limit
```bash
--cost-limit <amount>
```
- **描述**: API调用成本上限（美元）
- **行为**: 达到限制时停止处理
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --cost-limit 50.00
  ```

#### 通知参数

##### --webhook
```bash
--webhook <url>
```
- **描述**: 完成时发送通知的Webhook URL
- **格式**: HTTP/HTTPS URL
- **请求**: POST请求，JSON格式数据
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --webhook https://api.company.com/notify
  ```

#### 输出控制参数

##### --verbose, -v
```bash
--verbose
```
- **描述**: 启用详细输出模式
- **行为**: 显示详细的处理过程信息
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --verbose
  ```

##### --quiet, -q
```bash
--quiet
```
- **描述**: 静默模式，仅显示错误和结果
- **冲突**: 与--verbose互斥
- **示例**:
  ```bash
  gs_videoreport batch -d ./videos/ --quiet
  ```

## 配置文件扩展

### 批量处理配置段
```yaml
# 现有配置保持不变
google_api:
  api_key: "your-api-key"
  model: "gemini-2.5-flash"

templates:
  default_template: "chinese_transcript"

# 新增批量处理配置
batch_processing:
  # 默认设置
  default_parallel: 4
  default_output_dir: "./batch_output"
  default_timeout: 1800
  default_max_retries: 3
  
  # 性能优化
  auto_adjust_concurrency: true
  memory_limit_mb: 2048
  checkpoint_interval_minutes: 5
  checkpoint_max_count: 10
  
  # 错误处理
  auto_retry_network_errors: true
  auto_retry_api_errors: true
  fail_fast_on_auth_errors: true
  
  # 输出控制
  default_output_pattern: "{title}_{timestamp}.md"
  create_summary_report: true
  create_error_report: true
  
  # 通知设置
  notifications:
    enabled: false
    webhook_url: ""
    email_enabled: false
    email_recipient: ""
    
  # 成本控制
  cost_tracking:
    enabled: true
    daily_limit: 100.00
    warning_threshold: 80.00
    
  # API限制
  api_limits:
    max_concurrent_requests: 5
    requests_per_minute: 60
    requests_per_day: 1000
    backoff_multiplier: 2.0
    max_backoff_seconds: 300
```

## 输出格式规范

### 命令行输出

#### 标准模式输出
```
🚀 Starting batch processing...

📁 Input source: ./videos/ (15 videos found)
📋 Template: chinese_transcript
📂 Output: ./batch_output/
⚙️  Parallel: 4 workers
💾 Checkpoint: Auto-save every 5 minutes

Processing Progress:
████████████████████ 100% │ 15/15 │ 0 failed │ ETA: 00:00:00

✅ Batch processing completed!

📊 Summary:
  • Total videos: 15
  • Processed: 14 (93.3%)
  • Failed: 1 (6.7%)
  • Total time: 45m 32s
  • Average time: 3m 15s per video
  • Output directory: ./batch_output/

❌ Failed videos:
  • video_corrupted.mp4: File format not supported

📄 Reports generated:
  • Summary: ./batch_output/batch_summary_20240818_1630.md
  • Error log: ./batch_output/batch_errors_20240818_1630.log
```

#### 详细模式输出 (--verbose)
```
🚀 Starting batch processing...

🔧 Configuration:
  • Config file: ./config.yaml
  • API key: ****...ABCD (valid)
  • Model: gemini-2.5-flash
  • Memory limit: 2048 MB
  • Checkpoint dir: ./checkpoints/

📁 Scanning input directory: ./videos/
  ✓ video1.mp4 (125 MB, 15:30)
  ✓ video2.mov (89 MB, 8:45)
  ⚠ video3.avi (corrupted, skipped)
  ✓ video4.mp4 (256 MB, 25:12)
  
🏗️  Initializing batch processor...
  • Batch ID: batch_20240818_1630_001
  • Task queue: 14 tasks created
  • Worker pool: 4 workers starting
  • Progress monitor: started
  • Checkpoint manager: ready

⚡ Processing started:
[16:30:15] Worker-1: Processing video1.mp4
[16:30:15] Worker-2: Processing video2.mov
[16:30:15] Worker-3: Processing video4.mp4
[16:30:15] Worker-4: Processing video5.mp4

[16:33:45] Worker-1: ✓ video1.mp4 completed (3m 30s)
[16:33:45] Worker-1: Processing video6.mp4
[16:34:12] Worker-2: ✓ video2.mov completed (3m 57s)
...
```

#### 静默模式输出 (--quiet)
```
Processing 15 videos...
Completed: 14/15 (1 failed)
Results: ./batch_output/
```

### 进度文件格式 (JSON)

#### 实时进度状态 (--progress-file)
```json
{
  "batch_id": "batch_20240818_1630_001",
  "status": "running",
  "start_time": "2024-08-18T16:30:00Z",
  "current_time": "2024-08-18T16:45:30Z",
  "progress": {
    "total_tasks": 15,
    "completed_tasks": 8,
    "failed_tasks": 1,
    "running_tasks": 3,
    "pending_tasks": 3,
    "completion_percentage": 53.3
  },
  "performance": {
    "average_processing_time": 195.5,
    "current_throughput": 0.68,
    "estimated_remaining_time": 1680,
    "eta": "2024-08-18T17:15:00Z"
  },
  "workers": [
    {
      "worker_id": "worker_1",
      "status": "working",
      "current_task": "video9.mp4",
      "task_start_time": "2024-08-18T16:42:15Z"
    },
    {
      "worker_id": "worker_2", 
      "status": "working",
      "current_task": "video10.mp4",
      "task_start_time": "2024-08-18T16:43:20Z"
    }
  ],
  "recent_completions": [
    {
      "task_id": "task_008",
      "video_name": "video8.mp4",
      "completion_time": "2024-08-18T16:45:10Z",
      "processing_time": 180.5,
      "output_file": "./batch_output/video8_20240818_1645.md"
    }
  ],
  "errors": [
    {
      "task_id": "task_003",
      "video_name": "video3.avi",
      "error_type": "UnsupportedFormatError",
      "error_message": "Video format not supported",
      "timestamp": "2024-08-18T16:35:45Z"
    }
  ]
}
```

### 批量报告格式

#### 汇总报告 (batch_summary.md)
```markdown
# 批量处理报告

**批次ID**: batch_20240818_1630_001  
**开始时间**: 2024-08-18 16:30:00  
**结束时间**: 2024-08-18 17:15:32  
**总处理时间**: 45分32秒  

## 处理统计

| 指标 | 数值 | 百分比 |
|------|------|--------|
| 总视频数 | 15 | 100% |
| 处理成功 | 14 | 93.3% |
| 处理失败 | 1 | 6.7% |
| 跳过文件 | 0 | 0% |

## 性能指标

- **平均处理时间**: 3分15秒/视频
- **最快处理**: 1分45秒 (video2.mov)
- **最慢处理**: 8分30秒 (video12.mp4)
- **吞吐量**: 0.68 视频/分钟
- **峰值内存使用**: 1.2 GB
- **API调用次数**: 14次
- **估算成本**: $3.50

## 处理详情

### 成功处理
| 视频文件 | 处理时间 | 输出文件 | 文件大小 |
|----------|----------|----------|----------|
| video1.mp4 | 3m 30s | video1_20240818_1633.md | 15.2 KB |
| video2.mov | 3m 57s | video2_20240818_1634.md | 12.8 KB |
| ... | ... | ... | ... |

### 失败处理
| 视频文件 | 错误类型 | 错误描述 | 重试次数 |
|----------|----------|----------|----------|
| video3.avi | UnsupportedFormatError | Video format not supported | 0 |

## 输出文件

所有成功处理的文件已保存到: `./batch_output/`

## 建议

- 检查失败的video3.avi文件格式
- 考虑使用更多并发任务以提高处理速度
```

## 错误处理规范

### 错误分类

#### 用户输入错误
```bash
# 缺少输入源
❌ Error: No input source specified. Use --input-dir, --file-list, or --url-list.

# 输入源不存在
❌ Error: Input directory './videos/' does not exist.

# 无效参数组合
❌ Error: Cannot use --dry-run with --resume-from.

# 参数值超出范围
❌ Error: --parallel value 12 exceeds maximum limit (8).
```

#### 系统配置错误
```bash
# 配置文件问题
❌ Error: Configuration file './config.yaml' not found.
❌ Error: Invalid YAML syntax in configuration file (line 15).

# API密钥问题
❌ Error: Google API key not configured. Set api_key in config.yaml.
❌ Error: Google API key invalid or expired.

# 权限问题
❌ Error: Permission denied accessing output directory './batch_output/'.
❌ Error: Insufficient disk space for batch processing.
```

#### 处理时错误
```bash
# 网络问题
⚠️ Warning: Network timeout processing video5.mp4. Retrying... (attempt 2/3)
❌ Error: Network error processing video5.mp4 after 3 attempts.

# API限制
⚠️ Warning: API rate limit reached. Waiting 60 seconds...
❌ Error: API quota exceeded. Processing paused.

# 文件问题
⚠️ Warning: video3.avi appears corrupted. Skipping.
❌ Error: Cannot read video file: ./videos/video10.mp4
```

### 错误恢复策略

#### 自动重试错误
- NetworkError: 最多3次，指数退避
- APITimeoutError: 最多3次，固定间隔
- RateLimitError: 自动等待，继续处理

#### 需要用户干预错误
- AuthenticationError: 立即失败，检查API密钥
- PermissionError: 立即失败，检查文件权限
- UnsupportedFormatError: 跳过文件，继续处理

#### 致命错误
- ConfigurationError: 停止批处理
- DiskSpaceError: 停止批处理
- QuotaExceededError: 暂停批处理

## 集成接口

### Webhook通知格式

#### 完成通知
```json
{
  "event": "batch_completed",
  "batch_id": "batch_20240818_1630_001",
  "timestamp": "2024-08-18T17:15:32Z",
  "status": "completed",
  "summary": {
    "total_tasks": 15,
    "completed_tasks": 14,
    "failed_tasks": 1,
    "processing_time": 2732,
    "success_rate": 0.933
  },
  "results": {
    "output_directory": "./batch_output/",
    "summary_report": "./batch_output/batch_summary_20240818_1630.md",
    "error_log": "./batch_output/batch_errors_20240818_1630.log"
  }
}
```

#### 错误通知
```json
{
  "event": "batch_error",
  "batch_id": "batch_20240818_1630_001", 
  "timestamp": "2024-08-18T16:45:30Z",
  "error": {
    "type": "QuotaExceededError",
    "message": "Daily API quota exceeded",
    "recovery_suggestion": "Wait until quota resets or increase quota limit"
  },
  "progress": {
    "completed_tasks": 8,
    "total_tasks": 15,
    "can_resume": true,
    "checkpoint_id": "batch_20240818_1630_001_cp3"
  }
}
```

## 兼容性说明

### 向后兼容性
- 现有`main`命令保持不变
- 现有配置文件格式向下兼容
- 现有模板系统完全支持

### 版本支持
- Python 3.11+ (与现有要求一致)
- 配置文件版本: v1.0+ (自动升级)
- 检查点格式: v1.0

### 迁移路径
```bash
# 从单个处理迁移到批量处理
# 原来:
gs_videoreport main video.mp4 --template chinese_transcript

# 现在:
gs_videoreport batch --file-list <(echo "video.mp4") --template chinese_transcript

# 或者使用目录方式:
gs_videoreport batch --input-dir ./single_video/ --template chinese_transcript
```

---

*文档版本: v1.0*  
*创建日期: 2025-08-18*  
*负责人: 架构师@qa.mdc*  
*状态: API规范完成*
