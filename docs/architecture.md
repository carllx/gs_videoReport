# gs_videoReport 架构文档

## 1. 高层架构 (High Level Architecture)

### 技术摘要 (Technical Summary)

本项目 `gs_videoReport` 的架构是一个模块化的、运行于 macOS 终端的 Python 命令行工具 (CLI)。其核心是一个直接与 Google Gemini API 交互的客户端应用。整个架构遵循关注点分离 (Separation of Concerns) 的原则，将输入处理、AI 分析、以及教案生成等功能解耦为独立的服务模块，以提高代码的可测试性、可维护性和未来的可扩展性。

### 高层概览 (High Level Overview)

- **架构风格**: 客户端-API (Client-API) 架构。
    
- **仓库结构**: 单一仓库 (Monorepo)。
    
- **核心数据流**:
    
    1. 用户在终端输入命令 (`gs_videoReport <video_file_path>`)。
        
    2. **CLI 模块** 解析并验证输入参数，支持灵活的API密钥管理(CLI > Env Var > Config)。
        
    3. **Gemini 服务模块** 接收本地视频文件路径，上传文件到 Google Gemini API 进行分析。支持多种认证方式(API Key/OAuth)和多模型选择。
        
    4. **教案生成模块** 使用一个标准模板，将 API 返回的结果格式化为 Markdown 内容，并注入 Obsidian 兼容的元数据。
        
    5. **文件输出模块** 将最终的 Markdown 字符串写入本地文件系统。
        

### 高层项目图 (High Level Project Diagram)

```
graph TD
    subgraph User's macOS
        A[Terminal] --> B{gs_videoReport CLI};
    end

    subgraph gs_videoReport Application
        B --> C[1. Input Parser & Validator];
        C --> E[2. Gemini API Service];
        E --> F[3. Report Generator];
        F --> G[4. File Writer];
    end

    subgraph External Services
        E -- Uploads Video File for Analysis --> I[Google Gemini API];
    end

    G -- Writes File --> J[教案.md];

    style J fill:#f9f,stroke:#333,stroke-width:2px
```

### 架构与设计模式 (Architectural and Design Patterns)

- **命令行接口 (CLI)**: 作为与用户交互的主要模式。
    
- **适配器模式 (Adapter Pattern)**: 我们将把与 Google Gemini API 的直接交互封装在一个“适配器”或“服务”类中。
    
- **模板方法模式 (Template Method Pattern)**: 教案的生成将基于一个基础模板。
    
- **依赖注入 (Dependency Injection)**: 在构建应用时，我们会将外部依赖“注入”到需要它的模块中，以简化测试。
    

## 2. 技术栈 (Tech Stack)

|   |   |   |   |   |
|---|---|---|---|---|
|**分类 (Category)**|**技术 (Technology)**|**版本 (Version)**|**用途 (Purpose)**|**理由 (Rationale)**|
|**语言 (Language)**|Python|`~3.11`|主要开发语言|社区成熟，拥有强大的 AI 和数据处理生态。|
|**依赖管理 (Dependency Mgmt)**|Poetry|`~1.8`|管理项目依赖、打包和虚拟环境|现代化的 Python 依赖管理工具。|
|**命令行框架 (CLI Framework)**|Typer|`~0.12`|构建命令行交互界面|代码简洁、易于维护，并能自动生成帮助文档。|
|**AI 服务 SDK (AI Service SDK)**|google-genai|`latest`|与 Google Gemini API 交互|最新官方 Python SDK，支持现代化API接口和函数调用功能。|
|**配置管理 (Config Mgmt)**|PyYAML|`~6.0`|解析 `config.yaml` 配置文件|处理 YAML 文件的标准库。|
|**UI增强 (UI Enhancement)**|Rich|`latest`|终端UI美化和进度显示|提供丰富的终端用户界面，包括进度条、表格等。|
|**HTTP 客户端 (HTTP Client)**|httpx|`~0.27`|HTTP 请求处理|google-genai SDK 的默认 HTTP 客户端，支持同步/异步。|
|**测试框架 (Testing Framework)**|Pytest|`~8.2`|编写和执行单元与集成测试|Python 测试的事实标准。|

## 3. 源码树 (Source Tree)

```
gs-video-report/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── project_brief.md
│   ├── prd.md
│   └── architecture.md
├── src/
│   └── gs_video_report/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── gemini_service.py
│       ├── templates/
│       │   ├── prompts/
│       │   │   ├── default_templates.yaml
│       │   │   ├── comprehensive_lesson.yaml
│       │   │   └── summary_report.yaml
│       │   └── outputs/
│       │       └── basic_lesson_plan.md
│       ├── template_manager.py
│       ├── report_generator.py
│       ├── file_writer.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   └── test_gemini_service.py
├── .gitignore
├── config.yaml.example
├── pyproject.toml
└── README.md
```

## 4. 数据模型 (Data Models)

- **`Configuration`**: 代表从 `config.yaml` 文件中加载的配置信息 (`api_key`, `model_name`, `default_output_path`, `default_prompt_template`, `auth_type`, `oauth_config`)。支持多种认证方式和API密钥优先级管理。

- **`PromptTemplate`**: 代表提示词模板的结构化数据 (`name`, `version`, `description`, `parameters`, `prompt_content`, `model_config`)。

- **`TemplateManager`**: 管理提示词模板的加载、选择和参数化功能 (`load_templates()`, `get_template()`, `render_prompt()`)。
    
- **`LessonPlan`**: 代表最终生成的教案内容的结构化表示 (`video_title`, `video_url`, `obsidian_metadata`, `content_markdown`, `template_used`)。
    

## 5. 核心工作流 (Core Workflow)

```
sequenceDiagram
    participant User as 用户
    participant CLI as 命令行接口
    participant Config as 配置模块
    participant TemplateManager as 模板管理器
    participant GeminiService as Gemini服务
    participant ReportGenerator as 教案生成器
    participant FileWriter as 文件写入器

    User->>+CLI: 运行 `gs_videoReport <video_file> [--template <type>] [--model <model>]`
    CLI->>+Config: 加载配置()
    Config-->>-CLI: 返回配置对象
    CLI->>+TemplateManager: 加载提示模板(template_type, config)
    TemplateManager-->>-CLI: 返回选定的PromptTemplate
    CLI->>+GeminiService: 分析视频(file_path, prompt_template, config)
    GeminiService->>GeminiService: 上传视频文件到Gemini
    GeminiService->>GeminiService: 渲染提示词模板(视频参数)
    GeminiService->>+Gemini API: 发起分析请求(视频文件, 渲染后的提示词)
    Gemini API-->>-GeminiService: 返回分析结果
    GeminiService-->>-CLI: 返回LessonPlan数据(含使用的模板信息)
    CLI->>+ReportGenerator: 生成教案(LessonPlan)
    ReportGenerator-->>-CLI: 返回格式化的Markdown字符串
    CLI->>+FileWriter: 写入文件(markdown_string, path)
    FileWriter-->>-CLI: 写入成功
    CLI-->>-User: 显示成功信息、文件路径和使用的模板信息
```

## 6. 错误处理策略 (Error Handling Strategy)

- **用户输入错误**: 返回清晰的错误信息，程序以状态码 `1` 退出。
    
- **配置错误**: 打印指导信息，程序以状态码 `2` 退出。
    
- **API 错误**: 捕获 API 异常，显示友好的错误信息，程序以状态码 `3` 退出。
    
- **文件写入错误**: 处理文件系统权限问题，程序以状态码 `4` 退出。
    

## 7. 测试策略 (Test Strategy)

- **单元测试**: 使用 `pytest` 对所有独立模块进行测试，并对外部依赖（如 API、文件系统）进行模拟 (Mocking)。
    
- **集成测试**: 创建一个单独的端到端测试，使用真实的 API 密钥对一个简短视频进行测试，以验证与 Google Gemini API 的集成。
    

## 8. 安全 (Security)

- **API 密钥安全**: 用户的 `api_key` **必须** 存储在 `config.yaml` 文件中。该文件**必须**被添加到 `.gitignore` 中，以防止意外提交。项目中将提供一个 `config.yaml.example` 文件作为模板。