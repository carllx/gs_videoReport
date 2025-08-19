# 3. 源码树 (Source Tree v2.2)

## 新模块化架构

```
gs_videoReport/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── architecture/                    # 架构文档目录
│   │   ├── README.md
│   │   ├── index.md
│   │   ├── 1-高层架构-high-level-architecture.md
│   │   ├── 2-技术栈-tech-stack.md
│   │   ├── 3-源码树-source-tree.md
│   │   ├── 4-数据模型-data-models.md
│   │   ├── 5-核心工作流-core-workflow.md
│   │   ├── 6-错误处理策略-error-handling-strategy.md
│   │   ├── 7-测试策略-test-strategy.md
│   │   ├── 8-安全-security.md
│   │   └── batch_processing/
│   ├── project_brief.md
│   └── prd.md
├── src/
│   └── gs_video_report/
│       ├── __init__.py
│       ├── cli/                        # 模块化CLI架构 (已完成)
│       │   ├── __init__.py
│       │   ├── app.py                  # 主应用和路由配置
│       │   ├── commands/               # 命令处理器
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # 基础命令类
│       │   │   ├── single_video.py    # 单视频处理命令
│       │   │   ├── batch_commands.py  # 批量处理命令集
│       │   │   ├── management_commands.py # 管理命令集
│       │   │   └── info_commands.py   # 信息查询命令集
│       │   ├── handlers/               # 业务处理器
│       │   │   ├── __init__.py
│       │   │   ├── video_processor.py # 视频处理业务逻辑
│       │   │   ├── batch_manager.py   # 批量处理管理
│       │   │   ├── config_handler.py  # 配置处理
│       │   │   └── report_generator.py # 报告生成
│       │   ├── validators/             # 验证器
│       │   │   ├── __init__.py
│       │   │   ├── url_validator.py   # URL验证
│       │   │   ├── file_validator.py  # 文件验证
│       │   │   └── config_validator.py # 配置验证
│       │   ├── formatters/             # 输出格式化
│       │   │   ├── __init__.py
│       │   │   ├── table_formatter.py # 表格格式化
│       │   │   ├── progress_formatter.py # 进度显示
│       │   │   └── error_formatter.py # 错误格式化
│       │   └── utils/                  # 工具函数
│       │       ├── __init__.py
│       │       ├── argument_parser.py # 参数解析工具
│       │       ├── service_factory.py # 服务工厂
│       │       └── response_helpers.py # 响应辅助工具
│       ├── config.py
│       ├── services/                   # 外部服务集成
│       │   ├── __init__.py
│       │   ├── gemini_service.py      # 原始Gemini服务
│       │   └── simple_gemini_service.py # 🆕 多密钥Gemini服务(v2.2)
│       ├── batch/                      # 🆕 v2.2 动态并行处理核心
│       │   ├── __init__.py
│       │   ├── dedicated_worker_pool.py # 🆕 专用Worker池架构
│       │   ├── simple_processor.py    # 简单批量处理器
│       │   ├── enhanced_processor.py  # 🆕 增强型批量处理器(v2.2)
│       │   ├── simple_worker_pool.py  # 简化Worker池
│       │   ├── worker_pool.py         # 传统工作池(兼容保留)
│       │   ├── state_manager.py       # 状态管理和断点续传
│       │   └── retry_manager.py       # 智能重试管理
│       ├── security/                   # 🆕 v2.1 安全和密钥管理
│       │   ├── __init__.py
│       │   └── multi_key_manager.py   # 🆕 多API密钥轮换管理
│       ├── templates/                  # 模板系统
│       │   ├── prompts/
│       │   │   └── default_templates.yaml
│       │   └── outputs/
│       │       └── basic_lesson_plan.md
│       ├── template_manager.py
│       ├── lesson_formatter.py
│       ├── file_writer.py
│       ├── report_generator.py
│       └── main.py
├── tests/                              # 测试套件
│   ├── __init__.py
│   ├── unit/                          # 单元测试
│   │   ├── test_cli_commands.py
│   │   ├── test_validators.py
│   │   ├── test_formatters.py
│   │   └── test_handlers.py
│   ├── integration/                   # 集成测试
│   │   ├── test_cli_integration.py
│   │   └── test_service_integration.py
│   └── fixtures/                      # 测试数据
│       └── sample_videos/
├── scripts/                           # 辅助脚本
│   └── security_check.py
├── .gitignore
├── config.yaml.example
├── pyproject.toml
├── Makefile
└── README.md
```

## 架构层次说明

### CLI 层 (cli/)
- **commands/**: 命令处理器，每个CLI命令对应一个处理器类
- **validators/**: 输入验证器，确保数据的有效性和安全性
- **formatters/**: 输出格式化器，提供一致的用户界面体验
- **utils/**: CLI工具函数，包括服务工厂和参数解析

### 业务逻辑层 (handlers/)
- **video_processor.py**: 单视频处理的完整业务逻辑
- **batch_manager.py**: 批量处理管理和协调
- **config_handler.py**: 配置文件处理和验证
- **report_generator.py**: 性能和状态报告生成

### 服务层 (services/, batch/)
- **enhanced_gemini_service.py**: 增强型AI服务，支持模型回退和成本监控
- **batch/**: 企业级批量处理核心组件
- **security/**: 安全相关服务，包括API密钥管理

### 数据层 (templates/, 配置文件)
- **templates/**: 模板系统和输出格式定义
- **config.yaml.example**: 配置模板和安全指南
