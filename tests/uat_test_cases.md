# GS_VIDEOREPORT V0.1.0 - 用户接受测试(UAT)用例

## 测试概述

用户接受测试用例旨在验证 gs_videoReport 在真实使用场景下的表现，确保产品满足用户需求和期望。

## 测试环境要求

### 系统要求
- Python 3.11+ 
- 可用的 Google Gemini API 密钥
- 网络连接(用于 YouTube 视频下载)
- 至少 2GB 可用磁盘空间

### 测试数据准备
- 公共 YouTube 视频链接
- 本地测试视频文件(mp4格式)
- 有效的配置文件

## UAT 测试用例

### UC001: 教师基础视频分析场景

**背景**: 教师想要分析一个教育视频并生成中文教案  
**角色**: 教育工作者  
**前置条件**: 已安装软件，配置了API密钥  

#### 操作步骤:
1. 打开终端，导航到项目目录
2. 执行命令分析本地视频:
   ```bash
   python -m src.gs_video_report.cli main ./test_videos/007\ -\ what-is-lo-fi-wireframe-vs-high-fidelity-in-figma.mp4 --template chinese_transcript --verbose
   ```
3. 等待处理完成
4. 检查输出目录中生成的文件

#### 验收标准:
- [ ] 命令成功执行，无错误
- [ ] 生成包含中文逐字稿的 Markdown 文件
- [ ] 文件包含时间戳标记
- [ ] 文件格式符合 Obsidian 兼容性
- [ ] 处理时间在合理范围内(< 10分钟)
- [ ] 输出文件名包含视频标题和时间戳

#### 预期输出:
- 生成 `.md` 文件在 `./output/` 目录
- 文件包含 YAML frontmatter
- 包含 "基本信息"、"逐字稿内容"、"重点整理" 等章节

---

### UC002: YouTube视频在线分析场景

**背景**: 研究人员需要分析 YouTube 上的公开教育视频  
**角色**: 研究人员/学者  
**前置条件**: 网络连接正常，有有效API密钥  

#### 操作步骤:
1. 选择公共 YouTube 视频链接
2. 执行在线分析命令:
   ```bash
   python -m src.gs_video_report.cli main "https://www.youtube.com/watch?v=7r7ZDugy3EE" --template comprehensive_lesson --output ./my_analysis
   ```
3. 观察下载和分析过程
4. 检查生成的综合教案

#### 验收标准:
- [ ] 成功识别并下载 YouTube 视频
- [ ] 生成综合教案格式的分析报告
- [ ] 包含学习目标、时间戳、重点内容
- [ ] 输出保存到指定目录
- [ ] 处理过程提供清晰的状态信息

---

### UC003: 自定义配置高级使用场景

**背景**: 高级用户需要使用自定义配置进行批量处理  
**角色**: 技术用户/开发者  
**前置条件**: 准备好自定义配置文件  

#### 操作步骤:
1. 创建自定义配置文件:
   ```yaml
   google_api:
     api_key: "your-api-key"
     model: "gemini-2.5-pro"
     temperature: 0.2
   
   output:
     default_path: "./custom_output"
     include_metadata: true
   
   processing:
     verbose: true
     timeout_seconds: 300
   ```

2. 使用自定义配置分析视频:
   ```bash
   python -m src.gs_video_report.cli main ./test_video.mp4 --config ./custom_config.yaml --template summary_report
   ```

3. 验证配置是否生效

#### 验收标准:
- [ ] 自定义配置被正确加载
- [ ] 输出目录符合配置设置
- [ ] 使用指定的模型和参数
- [ ] 详细模式输出有用的调试信息
- [ ] 生成的报告符合 summary_report 格式

---

### UC004: 模板切换对比测试场景

**背景**: 用户想要比较不同模板的输出效果  
**角色**: 内容创作者  
**前置条件**: 同一个测试视频，多个可用模板  

#### 操作步骤:
1. 查看可用模板:
   ```bash
   python -m src.gs_video_report.cli list-templates --config test_config_v2.yaml
   ```

2. 使用不同模板分析同一视频:
   ```bash
   # 中文逐字稿模板
   python -m src.gs_video_report.cli main ./test_video.mp4 --template chinese_transcript --output ./output_chinese
   
   # 综合教案模板  
   python -m src.gs_video_report.cli main ./test_video.mp4 --template comprehensive_lesson --output ./output_lesson
   
   # 摘要报告模板
   python -m src.gs_video_report.cli main ./test_video.mp4 --template summary_report --output ./output_summary
   ```

3. 比较三种输出的差异和特点

#### 验收标准:
- [ ] 三个模板都能成功执行
- [ ] 输出格式明显不同，体现各模板特色
- [ ] chinese_transcript: 包含详细时间戳和逐字内容
- [ ] comprehensive_lesson: 包含学习目标和教学结构
- [ ] summary_report: 内容简洁，重点突出
- [ ] 所有输出都是有效的 Markdown 格式

---

### UC005: 错误恢复和帮助查询场景

**背景**: 新用户在使用过程中遇到问题需要帮助  
**角色**: 初学者  
**前置条件**: 初次使用软件  

#### 操作步骤:
1. 查看总体帮助:
   ```bash
   python -m src.gs_video_report.cli --help
   ```

2. 查看特定命令帮助:
   ```bash
   python -m src.gs_video_report.cli main --help
   ```

3. 尝试错误命令并观察错误提示:
   ```bash
   # 缺少参数
   python -m src.gs_video_report.cli main
   
   # 无效文件
   python -m src.gs_video_report.cli main nonexistent.mp4
   ```

4. 使用设置向导(如果可用):
   ```bash
   python -m src.gs_video_report.cli setup-api
   ```

#### 验收标准:
- [ ] 帮助信息清晰易懂
- [ ] 包含使用示例
- [ ] 错误信息具有指导性
- [ ] 提供解决方案建议
- [ ] 设置向导功能正常(如果实现)

---

### UC006: 性能和稳定性压力测试场景

**背景**: 验证系统在处理较大文件时的性能表现  
**角色**: 系统管理员/QA工程师  
**前置条件**: 准备不同大小的测试视频  

#### 操作步骤:
1. 测试小文件(< 50MB):
   ```bash
   time python -m src.gs_video_report.cli main ./small_video.mp4 --template chinese_transcript
   ```

2. 测试中等文件(50-200MB):
   ```bash
   time python -m src.gs_video_report.cli main ./medium_video.mp4 --template comprehensive_lesson
   ```

3. 监控系统资源使用:
   ```bash
   # 在另一个终端监控
   top -p $(pgrep -f gs_video_report)
   ```

4. 测试长时间运行的稳定性

#### 验收标准:
- [ ] 小文件处理时间 < 5分钟
- [ ] 中等文件处理时间 < 15分钟
- [ ] 内存使用峰值 < 1GB
- [ ] 处理过程中无内存泄漏
- [ ] 系统保持响应，不会冻结
- [ ] 成功完成处理并生成输出

---

## 测试执行指南

### 测试前准备
1. **环境验证**:
   ```bash
   python --version  # 确认 Python 3.11+
   python -m src.gs_video_report.cli version  # 确认软件安装
   ```

2. **配置验证**:
   ```bash
   python -m src.gs_video_report.cli list-templates --config test_config_v2.yaml
   ```

3. **测试数据准备**:
   - 确保测试视频文件存在
   - 验证网络连接
   - 准备足够的磁盘空间

### 测试执行记录

**测试人员**: ___________  
**测试日期**: ___________  
**测试环境**: ___________  

| 测试用例 | 执行状态 | 实际结果 | 问题记录 | 备注 |
|---------|---------|---------|---------|------|
| UC001 | [ ] 通过 [ ] 失败 | | | |
| UC002 | [ ] 通过 [ ] 失败 | | | |
| UC003 | [ ] 通过 [ ] 失败 | | | |
| UC004 | [ ] 通过 [ ] 失败 | | | |
| UC005 | [ ] 通过 [ ] 失败 | | | |
| UC006 | [ ] 通过 [ ] 失败 | | | |

### 测试完成标准

**最低通过标准**:
- UC001-UC004 必须全部通过
- UC005 至少80%功能正常
- UC006 满足基本性能要求

**优秀标准**:
- 所有用例100%通过
- 性能超出预期
- 用户体验流畅
- 错误处理完善

### 问题报告模板

**问题标题**: 简短描述问题  
**严重程度**: 严重/重要/一般  
**复现步骤**: 
1. 
2. 
3. 

**预期结果**: 
**实际结果**: 
**环境信息**: 
**建议解决方案**: 

---

*UAT测试用例 v1.0 | 更新日期: 2025-08-18*
