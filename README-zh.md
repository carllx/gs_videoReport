# gs_videoReport

🎓 面向教育工作者的AI驱动视频转教案工具，特别适用于艺术和媒体领域。

将您的视频内容转换为结构化教学材料，使用Google Gemini AI - 现已生产就绪，企业级批量处理功能即将推出！

> 📖 **English Documentation**: [README.md](./README.md) | [CHANGELOG.md](./CHANGELOG.md)

## 🎯 项目状态

**当前版本**: v0.1.1 生产就绪 ✅  
**质量门禁**: 增强错误处理和CLI一致性 ✅  
**GitHub发布**: [v0.1.1](https://github.com/carllx/gs_videoReport/releases/tag/v0.1.1) ✅  
**批量处理**: 架构设计完成，开发启动中 🚧

> **最新成就**: v0.1.1热修复版本成功解决了所有QA识别的问题，提供了改进的用户体验和所有命令的CLI参数一致性。

## 🚀 快速开始

### 前置要求

1. **Python 3.11+** 
2. **Poetry**（推荐）或 pip
3. **Google Gemini API密钥** ([在这里获取](https://makersuite.google.com/app/apikey))

### 安装

#### 选项1: 使用Poetry（推荐）
```bash
# 如未安装Poetry，先安装
curl -sSL https://install.python-poetry.org | python3 -

# 安装项目依赖
poetry install

# 激活虚拟环境
poetry shell
```

#### 选项2: 使用pip
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows用户: venv\Scripts\activate

# 手动安装依赖
pip install google-genai typer pyyaml yt-dlp httpx pytest
```

### 配置

1. **⚠️ 安全提示**: 切勿将API密钥提交到版本控制！

2. 复制并编辑配置文件:
```bash
# 复制示例配置文件
cp config.yaml.example config.yaml

# 编辑config.yaml并添加您的Google Gemini API密钥
# 此文件在.gitignore中，不会被提交
```

3. 在`config.yaml`中添加您的API密钥:
```yaml
api_key: "your-actual-gemini-api-key-here"
```

4. 从[Google AI Studio](https://makersuite.google.com/app/apikey)获取您的API密钥

## 📁 项目结构

```
gs_videoReport/
├── src/gs_video_report/              # 主应用程序代码 (v0.1.1)
│   ├── cli.py                        # 增强的CLI，具有参数一致性
│   ├── config.py                     # 健壮的配置管理
│   ├── template_manager.py           # 提示模板管理
│   ├── lesson_formatter.py           # 教案格式化引擎
│   ├── file_writer.py               # 文件输出处理
│   ├── services/
│   │   └── gemini_service.py         # Google Gemini API集成
│   ├── templates/
│   │   ├── prompts/                  # AI提示模板（Schema验证）
│   │   │   ├── default_templates.yaml
│   │   │   └── chinese_transcript_template.yaml
│   │   └── outputs/                  # 输出格式模板
│   └── batch/                        # 🚧 批量处理 (v0.2.0 开发中)
│       ├── processor.py              # 批量处理引擎
│       ├── task_queue.py             # 任务队列管理
│       ├── worker_pool.py            # 并发工作线程池
│       └── progress_monitor.py       # 进度跟踪系统
├── tests/                           # 综合测试套件 (85.7%通过率)
├── docs/                            # 完整项目文档
│   ├── architecture/                 # 技术架构文档
│   │   ├── batch_processing/         # 企业级批量处理设计
│   │   └── README.md                 # 架构文档索引
│   ├── stories/                      # 用户故事规范
│   └── prd.md                       # 产品需求文档
├── schemas/                         # 验证用JSON Schema定义
│   ├── config.schema.json           # 配置文件验证
│   └── prompt-template.schema.json  # 模板文件验证
├── config.yaml                     # 主配置文件（API密钥管理）
└── pyproject.toml                  # 依赖（Poetry管理）
```

## 🎯 开发路线图

### ✅ 阶段1: MVP实现 (已完成 v0.1.1)
- [x] **故事1.1**: 本地视频处理和教案生成
- [x] **故事1.2**: CLI界面和输入验证  
- [x] **故事1.3**: API集成和内容分析
- [x] **故事1.4**: 教案格式化和输出
- [x] **v0.1.1热修复**: 增强错误处理和CLI一致性

### 🚧 阶段2: 批量处理 (v0.2.0 - 开发中)
**架构完成**: 企业级批量处理设计 ✅
- [ ] **M1 (第1-2周)**: 核心数据模型和任务队列系统
- [ ] **M2 (第3-4周)**: 批量处理引擎与并发工作线程
- [ ] **M3 (第5-6周)**: 性能优化和检查点恢复
- [ ] **M4 (第7-8周)**: 测试、文档和生产发布

### 📈 性能目标 (v0.2.0)
- **吞吐量**: 35-70视频/小时（3-10倍提升）
- **并发性**: 2-8个并行工作线程
- **内存**: 大批量处理时峰值<2GB
- **可靠性**: 100%检查点恢复支持

### 🔮 阶段3: 未来增强
- 使用yt-dlp的YouTube URL集成
- 高级分析仪表板
- 多语言模板支持
- Obsidian插件集成

## 🔧 使用示例

### 单视频处理 (v0.1.1)
```bash
# 显示增强格式的帮助
gs_videoreport --help

# 处理本地视频文件（基本用法）
gs_videoreport video.mp4

# 使用特定模板和模型，API密钥覆盖
gs_videoreport video.mp4 --template chinese_transcript --model gemini-2.5-pro --api-key YOUR_KEY

# 指定输出目录并启用详细日志
gs_videoreport video.mp4 --output ./my_lessons --verbose

# 列出可用模板 (v0.1.1增强)
gs_videoreport list-templates --api-key YOUR_KEY

# 显示可用模型
gs_videoreport list-models

# 交互式API设置 (v0.1.1增强)
gs_videoreport setup-api --api-key YOUR_KEY
```

### 批量处理 (v0.2.0 - 即将推出!)
```bash
# 批量处理多个视频
gs_videoreport batch-process ./videos/*.mp4 --workers 4

# 恢复中断的批量处理
gs_videoreport batch-resume --checkpoint batch_20240118_1430

# 监控批量处理状态
gs_videoreport batch-status

# 使用自定义输出结构的批量处理
gs_videoreport batch-process videos/ --output-pattern "{date}/{filename}"
```

## 🔧 开发命令

```bash
# 安装依赖
poetry install

# 运行测试
poetry run pytest tests/

# 使用poetry运行
poetry run gs_videoreport --help

# 开发模式
poetry run python -m src.gs_video_report.cli --help
```

## 📚 核心功能

### ✅ 生产就绪 (v0.1.1)
- **🎯 本地视频处理**: 支持.mp4、.mov、.avi、.mkv、.webm格式
- **🧠 AI驱动分析**: Google Gemini 2.5 Pro/Flash集成
- **📋 模板系统**: 中文转录、综合教案、自定义模板
- **⚙️ 灵活配置**: CLI > 环境变量 > 配置文件优先级系统  
- **🛡️ 健壮错误处理**: 用户友好的错误信息和可执行解决方案
- **📊 丰富CLI体验**: 进度指示器、彩色输出、结构化帮助
- **📝 Schema验证**: IDE集成的配置和模板YAML验证

### 🚧 企业功能 (v0.2.0 开发中)
- **⚡ 批量处理**: 使用并发工作线程处理35-70视频/小时
- **💾 检查点恢复**: 自动恢复中断的批量作业
- **📈 性能监控**: 实时进度跟踪和资源使用情况
- **🔧 高级配置**: 批量特定设置和优化控制

## 🎨 模板系统

应用程序支持多种提示模板:

- **comprehensive_lesson**: 包含详细分析的完整教案
- **summary_report**: 简洁的视频摘要
- **chinese_transcript**: 中文转录模板
- **custom templates**: 用户自定义提示模板

模板存储在`src/gs_video_report/templates/prompts/`中，可以自定义。

## 📖 文档

### 核心文档
- **📋 用户故事**: `docs/stories/` - 完整功能规范（所有v0.1.1故事已完成）
- **🏗️ 架构**: `docs/architecture/` - 技术架构文档
  - **单体处理**: 当前v0.1.1架构  
  - **批量处理**: 企业v0.2.0架构设计
- **📊 PRD**: `docs/prd.md` - 产品需求和规范
- **🔄 变更日志**: 完整版本历史和发布说明

### 开发资源  
- **🔧 模式**: `schemas/` - 配置和模板验证的JSON Schema
- **✅ 发布说明**: [v0.1.1 GitHub发布](https://github.com/carllx/gs_videoReport/releases/tag/v0.1.1)
- **📈 架构指南**: `docs/architecture/README.md` - 完整架构索引
- **📚 主文档索引**: `docs/README.md` - 完整项目文档导航中心

## 🚀 当前状态和下一步

### ✅ 已完成 (v0.1.1)
1. **生产发布**: 稳定的单视频处理，增强的CLI
2. **质量保证**: 85.7%测试通过率，全面错误处理  
3. **文档**: 完整的用户故事、架构和发布文档
4. **团队协调**: 成功的开发负责人和架构师协作

### 🎯 近期下一步 (第1-2周)
1. **批量处理开发**: 开始阶段1实现
2. **资源分配**: 将开发团队分配给8周路线图
3. **开发分支**: 创建`feature/batch-processing`分支
4. **依赖设置**: 向项目添加批量处理依赖

## 🤝 贡献

这目前是一个个人项目。开发遵循`docs/stories/`中定义的用户故事。

## 📄 许可证

[在此添加您的许可证]

---

## 🎉 **生产就绪与企业扩展！**

✅ **v0.1.1**: 增强CLI的单视频处理 - **[立即获取](https://github.com/carllx/gs_videoReport/releases/tag/v0.1.1)**

🚧 **v0.2.0**: 企业级批量处理（35-70视频/小时）- **开发启动**

以生产就绪的可靠性和企业级性能将您的视频内容转换为结构化教学材料！

---
*最后更新: v0.1.1 - 增强错误处理和CLI一致性 | 批量处理架构完成*
