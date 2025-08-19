# 开发环境设置指南 - gs_videoReport

## 📋 概述

本指南提供安全、标准化的开发环境设置步骤，确保所有开发者拥有一致的开发体验和安全的配置管理。

---

## 🔐 安全优先原则

### 核心安全要求
- ✅ **绝不提交敏感信息** - API密钥、凭据文件不得进入版本控制
- ✅ **使用环境变量** - 优先使用环境变量存储敏感配置
- ✅ **验证配置安全** - 定期运行安全检查
- ✅ **遵循最小权限** - 仅获取必需的API权限

---

## 🛠️ 开发环境设置

### 1. 基础环境准备

#### 系统要求
```bash
# Python版本要求
python >= 3.11

# 操作系统支持
- macOS 10.15+
- Ubuntu 20.04+
- Windows 10+

# 内存建议
- 最低: 4GB RAM
- 推荐: 8GB+ RAM (用于并发处理)
```

#### 必需工具安装
```bash
# 1. Python 环境管理 (推荐pyenv)
curl https://pyenv.run | bash

# 2. Poetry 依赖管理
curl -sSL https://install.python-poetry.org | python3 -

# 3. Git 版本控制
# 根据系统安装git

# 4. 验证安装
python --version  # 应显示 3.11+
poetry --version   # 应显示 1.8+
git --version      # 应显示 2.30+
```

### 2. 项目克隆和设置

```bash
# 克隆项目
git clone https://github.com/your-org/gs_videoReport.git
cd gs_videoReport

# 检查安全状态
python scripts/security_check.py --setup-guide

# 设置Python环境
pyenv install 3.11.9
pyenv local 3.11.9

# 安装依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 3. 安全配置设置

#### 方法 1: 环境变量 (推荐)
```bash
# 创建 .env 文件 (已被gitignore忽略)
cat > .env << EOF
GOOGLE_GEMINI_API_KEY=your-actual-api-key-here
GEMINI_API_KEY=your-actual-api-key-here
EOF

# 加载环境变量
source .env

# 或者直接设置环境变量
export GOOGLE_GEMINI_API_KEY="your-actual-api-key-here"
```

#### 方法 2: 配置文件
```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 编辑配置文件 (确保已被gitignore忽略)
vim config.yaml
# 替换 YOUR_GEMINI_API_KEY_HERE 为真实API密钥
```

#### API密钥获取指南
```bash
# 1. 访问 Google AI Studio
open https://makersuite.google.com/app/apikey

# 2. 登录Google账户

# 3. 创建新的API密钥
# 4. 复制密钥并安全存储

# 5. 验证密钥格式 (应以 AIza 开头)
echo $GOOGLE_GEMINI_API_KEY | grep -E '^AIza[0-9A-Za-z-_]{35}$'
```

### 4. 配置验证

```bash
# 运行安全检查
python scripts/security_check.py

# 应显示:
# 🔒 整体安全状态: SECURE 或 GOOD

# 如有问题，运行自动修复
python scripts/security_check.py --fix
```

---

## 🧪 开发工作流

### 1. 日常开发流程

```bash
# 1. 激活开发环境
poetry shell

# 2. 更新依赖 (如有需要)
poetry install

# 3. 运行安全检查
python scripts/security_check.py

# 4. 开始开发...
```

### 2. 测试执行

```bash
# 运行基础测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_config.py -v

# 运行覆盖率测试
pytest --cov=src/gs_video_report tests/

# 运行安全相关测试
pytest tests/test_security.py -v
```

### 3. 代码质量检查

```bash
# 代码格式化
black src/ tests/

# Import排序
isort src/ tests/

# 类型检查
mypy src/gs_video_report/

# Lint检查
flake8 src/ tests/
```

---

## 📦 依赖管理

### 1. 添加新依赖

```bash
# 生产依赖
poetry add package-name

# 开发依赖
poetry add --group dev package-name

# 可选依赖
poetry add --optional package-name
```

### 2. 依赖版本管理

```toml
# pyproject.toml - 版本锁定策略
[tool.poetry.dependencies]
python = "^3.11"                    # 允许小版本更新
google-genai = "^0.3.0"            # 允许兼容更新  
typer = "~0.12.0"                   # 锁定次版本
requests = "2.31.0"                 # 锁定具体版本 (如有安全需求)
```

### 3. 依赖更新流程

```bash
# 检查过期依赖
poetry show --outdated

# 更新依赖 (谨慎操作)
poetry update

# 更新特定包
poetry update package-name

# 更新后运行完整测试
pytest tests/ --cov=src/
```

---

## 🔧 IDE 配置

### 1. VS Code 配置

创建 `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "config.yaml": true,
        ".env": true
    },
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

### 2. PyCharm 配置

1. **解释器设置**: File → Settings → Project → Python Interpreter
2. **代码格式**: Settings → Tools → External Tools → 添加Black
3. **排除文件**: Settings → Project → Project Structure → 排除config.yaml

---

## 🚨 故障排除

### 1. 常见问题

#### API密钥问题
```bash
# 问题: API密钥无效
python scripts/security_check.py

# 解决: 检查密钥格式
echo $GOOGLE_GEMINI_API_KEY | grep -E '^AIza[0-9A-Za-z-_]{35}$'

# 如格式错误，重新获取密钥
```

#### 依赖冲突
```bash
# 问题: 依赖安装失败
poetry install

# 解决: 清理缓存重新安装
poetry cache clear pypi --all
poetry install --no-cache
```

#### 权限问题
```bash
# 问题: 文件权限错误
ls -la config.yaml

# 解决: 设置正确权限
chmod 600 config.yaml  # 仅所有者可读写
```

### 2. 日志调试

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG

# 运行测试查看详细输出
python -m gs_video_report.main --debug

# 检查日志文件
tail -f logs/app.log
```

---

## 🛡️ 安全最佳实践

### 1. 开发安全检查清单

- [ ] config.yaml已被.gitignore忽略
- [ ] API密钥使用环境变量或安全配置
- [ ] 运行`security_check.py`通过
- [ ] 代码中无硬编码密钥
- [ ] 测试文件不包含真实密钥
- [ ] 日志不输出敏感信息

### 2. 定期安全维护

```bash
# 每周运行安全检查
python scripts/security_check.py

# 每月轮换API密钥
# 1. 生成新的API密钥
# 2. 更新环境变量/配置
# 3. 删除旧密钥

# 每季度依赖安全更新
poetry update
poetry audit  # 检查已知漏洞
```

### 3. 团队协作安全

```bash
# 分享配置模板（不含密钥）
cp config.yaml config.yaml.team-template
# 编辑移除所有敏感信息
git add config.yaml.team-template

# 共享环境变量设置指南
# （不共享实际值）
```

---

## 📋 环境变量参考

### 必需环境变量
```bash
# API认证
GOOGLE_GEMINI_API_KEY          # Gemini API密钥
GEMINI_API_KEY                 # 备用密钥名

# 可选配置
GOOGLE_CLOUD_PROJECT           # GCP项目ID (OAuth使用)
GOOGLE_CLOUD_LOCATION          # GCP区域 (OAuth使用)
```

### 开发环境变量
```bash
# 调试配置
LOG_LEVEL=DEBUG                # 日志级别
DEBUG_MODE=true                # 调试模式

# 测试配置
TEST_API_KEY=test-key          # 测试用API密钥
SKIP_INTEGRATION_TESTS=false   # 跳过集成测试
```

---

## 🔄 CI/CD 集成

### 1. GitHub Actions 配置

```yaml
# .github/workflows/security-check.yml
name: Security Check
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install
      - name: Run security check
        run: |
          poetry run python scripts/security_check.py
        env:
          GOOGLE_GEMINI_API_KEY: ${{ secrets.GOOGLE_GEMINI_API_KEY }}
```

### 2. Secrets 管理

```bash
# GitHub Secrets 设置
# Repository → Settings → Secrets and variables → Actions

# 添加密钥:
GOOGLE_GEMINI_API_KEY=your-api-key-here
```

---

## 📚 相关文档

- [API Key Setup Guide](docs/API_KEY_SETUP.md)
- [Architecture Documentation](docs/architecture/)
- [Security Module Documentation](src/gs_video_report/security/)
- [Testing Guide](tests/README.md)

---

## 💬 获得帮助

### 联系方式
- **技术问题**: 创建GitHub Issue
- **安全问题**: 私信项目维护者
- **文档问题**: 提交Pull Request

### 资源链接
- [Google AI Studio](https://makersuite.google.com/app/apikey)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Python Security Guide](https://python.org/dev/security/)

---

**文档版本**: v1.0  
**最后更新**: 2025年1月26日  
**维护者**: @sec.mdc
