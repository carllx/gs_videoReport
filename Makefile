# gs_videoReport Development Makefile
# 提供常用的开发、测试和部署命令

.PHONY: help install test security setup validate clean format lint

# 默认目标
help: ## 显示帮助信息
	@echo "🔧 gs_videoReport 开发工具"
	@echo "===================="
	@echo "可用命令："
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ 🏗️ 环境设置
install: ## 安装项目依赖
	@echo "📦 安装依赖..."
	poetry install
	@echo "✅ 依赖安装完成"

setup: ## 完整环境设置（首次使用）
	@echo "🚀 初始化开发环境..."
	poetry install
	cp config.yaml.example config.yaml
	python scripts/security_check.py --fix
	python scripts/validate_setup.py --fix
	@echo "✅ 环境设置完成"
	@echo "⚠️  请编辑 config.yaml 并设置您的API密钥"

##@ 🔍 验证和检查
validate: ## 运行完整环境验证
	@echo "🔍 运行环境验证..."
	python scripts/validate_setup.py

security: ## 运行安全配置检查
	@echo "🔒 检查安全配置..."
	python scripts/security_check.py

security-fix: ## 自动修复安全问题
	@echo "🔧 自动修复安全问题..."
	python scripts/security_check.py --fix

##@ 🧪 测试
test: ## 运行所有测试
	@echo "🧪 运行测试..."
	poetry run pytest tests/ -v

test-cov: ## 运行测试并生成覆盖率报告
	@echo "📊 运行测试覆盖率..."
	poetry run pytest --cov=src/gs_video_report tests/ --cov-report=html

test-security: ## 运行安全相关测试
	@echo "🔐 运行安全测试..."
	poetry run pytest tests/test_security.py -v

##@ 📝 代码质量
format: ## 格式化代码
	@echo "🎨 格式化代码..."
	poetry run black src/ tests/ scripts/
	poetry run isort src/ tests/ scripts/

lint: ## 检查代码质量
	@echo "🔍 检查代码质量..."
	poetry run flake8 src/ tests/ scripts/
	poetry run mypy src/gs_video_report/

quality: format lint ## 运行完整代码质量检查

##@ 🚀 运行和构建
run: ## 运行主程序（示例）
	@echo "🚀 运行程序..."
	poetry run python -m gs_video_report.main --help

build: ## 构建项目包
	@echo "📦 构建项目..."
	poetry build

##@ 🧹 清理
clean: ## 清理临时文件
	@echo "🧹 清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/

clean-all: clean ## 深度清理（包括虚拟环境）
	@echo "💥 深度清理..."
	poetry env remove --all

##@ 📚 文档和帮助
docs: ## 生成文档
	@echo "📚 生成文档..."
	@echo "文档位置: docs/"

setup-guide: ## 显示设置指南
	@echo "📖 显示设置指南..."
	python scripts/security_check.py --setup-guide

dev-info: ## 显示开发环境信息
	@echo "💻 开发环境信息"
	@echo "=================="
	@echo "Python版本: $(shell python --version)"
	@echo "Poetry版本: $(shell poetry --version 2>/dev/null || echo 'Poetry 未安装')"
	@echo "项目根目录: $(shell pwd)"
	@echo "虚拟环境: $(shell poetry env info --path 2>/dev/null || echo '未创建')"

##@ 🔄 Git和版本管理
git-check: ## 检查Git状态和安全
	@echo "📝 检查Git状态..."
	git status
	@echo "\n🔒 检查敏感文件..."
	@if git ls-files | grep -E "(config\.yaml|\.env|.*secret.*|.*key.*)" ; then \
		echo "⚠️  发现敏感文件在Git中！" ; \
		echo "请确保这些文件被.gitignore忽略" ; \
	else \
		echo "✅ 未发现敏感文件在Git中" ; \
	fi

pre-commit: security validate test ## 提交前检查
	@echo "✅ 提交前检查完成"

##@ 🎯 完整工作流
all: clean install security-fix validate test quality ## 运行完整开发工作流

quick-check: security validate ## 快速检查

# 特殊目标：确保scripts目录中的脚本可执行
scripts/%.py:
	chmod +x $@

# 依赖目标：确保Poetry已安装
check-poetry:
	@which poetry > /dev/null || (echo "❌ Poetry未安装。请访问 https://python-poetry.org/docs/#installation" && exit 1)

# 所有需要Poetry的目标都依赖这个检查
install test test-cov format lint build clean-all: | check-poetry
