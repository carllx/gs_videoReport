# 🎯 QA测试规则 - 强制执行标准

**QA Agent**: @qa.mdc  
**制定日期**: 2025-08-19  
**项目**: gs_videoReport v0.2.0  
**状态**: **强制执行** - 不得违反

---

## ⚠️ **关键警告**

**本文档制定的测试规则为强制性标准，任何QA测试都必须严格遵循，不得有任何例外或变通。**

---

## 📋 **强制性测试目录规则**

### 1. **输入目录: test_videos/**
- ✅ **必须使用**: `/Users/yamlam/Documents/GitHub/gs_videoReport/test_videos/`
- ❌ **禁止使用**: 任何其他目录，包括但不限于：
  - `parallel_test_videos/`
  - `sample_videos/`  
  - `demo_videos/`
  - 任何临时创建的测试目录

### 2. **输出目录: test_output/**
- ✅ **必须输出到**: `/Users/yamlam/Documents/GitHub/gs_videoReport/test_output/`
- ❌ **禁止输出到**: 任何其他位置

### 3. **真实视频文件要求**
- ✅ **必须使用**: test_videos/ 目录中的20个真实Figma教程视频
- ✅ **验证文件总数**: 20个.mp4文件
- ✅ **验证文件大小**: 总大小约140MB
- ❌ **禁止使用**: 模拟文件、符号链接、示例文件

---

## 🤖 **强制性API模型规则**

### **Gemini模型要求**
- ✅ **必须使用**: `gemini-2.5-pro`
- ❌ **禁止使用**: 
  - `gemini-2.5-flash`
  - `gemini-pro`
  - `gemini-1.5-pro`
  - 任何其他模型

### **配置验证要求**
```yaml
google_api:
  model: "gemini-2.5-pro"  # 强制指定
```

---

## 📊 **测试执行命令标准**

### **单视频测试**
```bash
# ✅ 正确命令
python -m src.gs_video_report.cli.app main test_videos/[具体视频文件] --output test_output --model gemini-2.5-pro --verbose

# ❌ 错误示例
python -m src.gs_video_report.cli.app main parallel_test_videos/video.mp4  # 错误目录
```

### **批量处理测试**
```bash
# ✅ 正确命令  
python -m src.gs_video_report.cli.app batch test_videos --output test_output --verbose

# ❌ 错误示例
python -m src.gs_video_report.cli.app batch parallel_test_videos  # 错误目录
```

---

## 🔍 **测试前强制性验证清单**

在开始任何测试前，必须执行以下验证：

### 1. **目录验证**
```bash
# 验证输入目录存在且包含20个视频
ls -la test_videos/*.mp4 | wc -l  # 必须返回20

# 验证输出目录存在且可写
test -w test_output && echo "✅ 输出目录可写" || echo "❌ 输出目录不可写"
```

### 2. **模型配置验证**
```bash
# 验证配置中的模型设置
python -c "
from src.gs_video_report.config import Config
config = Config.load_config()
model = config.get('google_api', {}).get('model', 'unknown')
print(f'当前模型: {model}')
assert model == 'gemini-2.5-pro', f'错误！模型应为gemini-2.5-pro，实际为{model}'
print('✅ 模型配置验证通过')
"
```

### 3. **API密钥验证**
```bash
# 验证API密钥配置
python -m src.gs_video_report.cli.app setup-api
```

### 4. **API失败率统计验证** 🆕

**所有QA测试必须包含API使用统计的验证**：

```bash
# 验证API统计文件生成
test -f logs/api_key_usage.json && echo "✅ API统计文件存在" || echo "❌ 缺少API统计文件"

# 验证失败率计算工具可用
python scripts/view_api_failure_rates.py --help > /dev/null 2>&1 && echo "✅ 失败率分析工具可用" || echo "❌ 失败率分析工具不可用"

# 验证实时监控工具可用
python scripts/monitor_api_rates.py --help > /dev/null 2>&1 && echo "✅ 实时监控工具可用" || echo "❌ 实时监控工具不可用"
```

**API统计质量要求**：
```bash
# API失败率不得超过30%
python3 -c "
import json, sys
with open('logs/api_key_usage.json', 'r') as f:
    stats = json.load(f)
    
overall_requests = sum(data['total_requests'] for data in stats.values())
overall_failures = sum(data['failed_requests'] for data in stats.values())

if overall_requests > 0:
    failure_rate = (overall_failures / overall_requests) * 100
    print(f'整体失败率: {failure_rate:.1f}%')
    
    if failure_rate > 30:
        print('❌ 失败率过高，测试不达标')
        sys.exit(1)
    else:
        print('✅ 失败率在可接受范围内')
else:
    print('⚠️ 无API调用记录')
"
```

---

## 🚫 **禁止行为清单**

### **绝对禁止**
1. ❌ 创建任何临时测试目录
2. ❌ 使用符号链接或软链接文件
3. ❌ 修改test_videos/目录中的原始文件
4. ❌ 使用除gemini-2.5-pro外的任何模型
5. ❌ 输出到test_output/以外的任何位置
6. ❌ 跳过目录和模型验证步骤

### **测试无效情况**
如果出现以下情况，测试结果无效，必须重新执行：
1. 使用了错误的输入目录
2. 使用了错误的输出目录  
3. 使用了错误的AI模型
4. 跳过了验证步骤
5. 修改了原始测试文件

---

## ✅ **测试执行标准流程**

### **Phase 1: 环境验证**
```bash
# 1. 验证目录结构
echo "🔍 验证测试环境..."
test -d test_videos && echo "✅ test_videos存在" || exit 1
test -d test_output && echo "✅ test_output存在" || exit 1

# 2. 验证视频文件数量
VIDEO_COUNT=$(ls test_videos/*.mp4 | wc -l)
echo "📹 发现视频文件: $VIDEO_COUNT 个"
[[ $VIDEO_COUNT -eq 20 ]] && echo "✅ 视频数量正确" || exit 1

# 3. 验证模型配置
echo "🤖 验证AI模型配置..."
python -c "
from src.gs_video_report.config import Config
config = Config.load_config()
model = config.get('google_api', {}).get('model')
assert model == 'gemini-2.5-pro', f'模型错误: {model}'
print('✅ Gemini 2.5 Pro配置正确')
"
```

### **Phase 2: 测试执行**
```bash
# 单视频测试
echo "🎬 执行单视频测试..."
python -m src.gs_video_report.cli.app main test_videos/001*.mp4 --output test_output --verbose

# 批量处理测试  
echo "📦 执行批量处理测试..."
python -m src.gs_video_report.cli.app batch test_videos --output test_output --verbose
```

### **Phase 3: 结果验证**
```bash
# 验证输出文件
echo "📋 验证测试结果..."
ls -la test_output/*.md
echo "✅ 测试完成，结果已保存到test_output/"

# Phase 3.1: API统计验证
echo "📊 验证API使用统计..."
python scripts/view_api_failure_rates.py
echo "✅ API统计分析完成"

# Phase 3.2: 失败率合规检查
python3 -c "
import json
with open('logs/api_key_usage.json', 'r') as f:
    stats = json.load(f)
    
total_requests = sum(data['total_requests'] for data in stats.values())
total_failures = sum(data['failed_requests'] for data in stats.values())

if total_requests > 0:
    failure_rate = (total_failures / total_requests) * 100
    print(f'📊 整体API失败率: {failure_rate:.1f}%')
    
    if failure_rate <= 30:
        print('✅ API质量达标 (失败率 ≤ 30%)')
    else:
        print(f'❌ API质量不达标 (失败率 {failure_rate:.1f}% > 30%)')
        exit(1)
else:
    print('⚠️ 无API统计数据')
"
```

---

## 📝 **测试报告要求**

每次测试必须记录：
1. ✅ 使用的输入目录: `test_videos/`
2. ✅ 使用的输出目录: `test_output/`  
3. ✅ 使用的AI模型: `gemini-2.5-pro`
4. ✅ 处理的视频数量: 实际数量/20
5. ✅ 成功率统计
6. ✅ 错误信息（如有）
7. ✅ **API失败率统计** (新增): 
   - 总API请求数
   - API成功率/失败率
   - 各密钥使用情况
   - 失败类型分布（配额耗尽、速率限制等）

### **API失败率报告模板**

```bash
# 生成标准化的API失败率报告
python3 -c "
import json
from datetime import datetime

print('=' * 60)
print('📊 QA测试 - API失败率统计报告')
print('=' * 60)
print(f'📅 测试时间: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
print(f'🤖 测试模型: gemini-2.5-pro')
print(f'📁 输入目录: test_videos/')
print(f'📁 输出目录: test_output/')

with open('logs/api_key_usage.json', 'r') as f:
    stats = json.load(f)

total_requests = sum(data['total_requests'] for data in stats.values())
total_success = sum(data['successful_requests'] for data in stats.values())
total_failures = sum(data['failed_requests'] for data in stats.values())
total_quota_exhausted = sum(data['quota_exhausted_count'] for data in stats.values())

print(f'\\n📊 整体统计:')
print(f'   总请求数: {total_requests}')
print(f'   成功请求: {total_success}')
print(f'   失败请求: {total_failures}')

if total_requests > 0:
    success_rate = (total_success / total_requests) * 100
    failure_rate = (total_failures / total_requests) * 100
    print(f'   成功率: {success_rate:.1f}%')
    print(f'   失败率: {failure_rate:.1f}%')
    print(f'   配额耗尽: {total_quota_exhausted}次')
    
    print(f'\\n🎯 质量评估:')
    if failure_rate <= 10:
        print('   ✅ 优秀 (失败率 ≤ 10%)')
    elif failure_rate <= 30:
        print('   ✅ 良好 (失败率 ≤ 30%)')
    else:
        print(f'   ❌ 不达标 (失败率 {failure_rate:.1f}% > 30%)')

print('=' * 60)
"
```

---

## 🎖️ **责任声明**

**@qa.mdc 承诺**：
- ✅ 严格遵循本文档规定的所有测试规则
- ✅ 在每次测试前执行完整的验证流程
- ✅ 使用指定的test_videos/和test_output/目录
- ✅ 使用指定的gemini-2.5-pro模型
- ✅ 任何违反规则的测试将被视为无效，必须重新执行

**违规后果**：
- 🚫 违反规则的测试结果一律无效
- 🚫 必须重新按规则执行测试
- 🚫 不得以任何理由绕过本规则

---

**文档版本**: v1.0  
**最后更新**: 2025-08-19  
**执行状态**: 🔒 **强制执行中**

---

## 🔄 **立即执行**

**现在开始，所有QA测试必须严格按照本规则执行，不得有任何例外！**
