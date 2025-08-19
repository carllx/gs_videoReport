# 1. 高层架构 (High Level Architecture)

## 技术摘要 (Technical Summary)

本项目 `gs_videoReport` 的架构是一个模块化的、运行于 macOS 终端的 Python 命令行工具 (CLI)。v0.2.0 版本采用了全新的模块化 CLI 架构，其核心是一个直接与 Google Gemini API 交互的客户端应用。整个架构遵循关注点分离 (Separation of Concerns) 和单一职责原则 (Single Responsibility Principle)，将 CLI 处理、业务逻辑、验证、格式化等功能解耦为独立的模块，以提高代码的可测试性、可维护性和未来的可扩展性。

## v2.2 架构重大更新

- **模块化 CLI**: 将原本 1,193 行的单体 CLI 重构为 17 个职责单一的模块
- **企业级批量处理**: 新增智能并发控制、状态管理和恢复机制  
- **增强型 Gemini 服务**: 实现模型兼容性检测、智能回退和成本追踪
- **🆕 动态并行处理**: 根据API密钥数量自动调整worker数量(1-8个)
- **🆕 专用Worker池**: 每个API密钥绑定专用worker，防止任务冲突
- **🆕 断点续传**: 智能跳过已处理文件，节省80%+处理时间
- **🆕 模板子文件夹**: 按模板组织输出结构，如test_output/chinese_transcript/

## 高层概览 (High Level Overview)

- **架构风格**: 客户端-API (Client-API) 架构。
    
- **仓库结构**: 单一仓库 (Monorepo)。
    
- **核心数据流 (v2.2 动态并行更新)**:
    
    1. 用户在终端输入命令 (`gs_videoreport video.mp4` 或 `gs_videoreport batch ./videos/`)。
        
    2. **模块化 CLI 系统** 解析命令并路由到对应的命令处理器。
        
    3. **配置管理器** 加载多密钥配置，动态计算worker数量(基于API密钥数)。
        
    4. **命令处理器** 使用验证器验证输入，通过服务工厂创建所需服务。
        
    5. **🆕 专用Worker池** 为每个API密钥创建专用worker，实现任务隔离。
        
    6. **🆕 断点续传检查** 扫描输出目录，跳过已处理的视频文件。
        
    7. **增强型 Gemini 服务** 进行模型兼容性检测，每个worker使用专用API密钥。
        
    8. **业务处理器** (单视频/批量) 协调整个处理流程，支持并发状态管理。
        
    9. **教案格式化器** 使用标准模板将 API 结果格式化为 Markdown 内容。
        
    10. **文件输出模块** 按模板创建子文件夹，写入本地文件系统，支持状态持久化。
        

## 高层项目图 (High Level Project Diagram v2.2)

```
graph TD
    subgraph User's macOS
        A[Terminal] --> B{Modular CLI App};
    end

    subgraph CLI Layer
        B --> C[Command Router];
        C --> D[Command Handlers];
        D --> E[Validators];
        D --> F[Service Factory];
    end

    subgraph Business Logic Layer
        F --> G[Video Processor];
        F --> H[Batch Manager];
        F --> I[Enhanced Gemini Service];
        G --> I;
        H --> I;
    end

    subgraph Service Layer
        I --> J[Model Compatibility Detector];
        I --> K[Cost Estimator];
        I --> L[Template Manager];
        I --> M[State Manager];
    end

    subgraph External Services
        I -- Smart Model Selection --> N[Google Gemini API];
    end

    subgraph Output Layer
        G --> O[Lesson Formatter];
        H --> P[Batch State Files];
        O --> Q[File Writer];
        P --> Q;
        Q --> R[教案文件/批量结果];
    end

    style R fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style I fill:#fff3e0,stroke:#e65100,stroke-width:2px
```

## 架构与设计模式 (Architectural and Design Patterns v0.2.0)

### 核心架构模式

- **模块化 CLI 架构**: 将单体 CLI 拆分为职责单一的模块。
- **分层架构 (Layered Architecture)**: CLI层 → 业务逻辑层 → 服务层 → 外部服务层。
- **微服务风格组件**: 每个模块都可以独立测试和部署。

### 应用设计模式

- **命令模式 (Command Pattern)**: 每个 CLI 命令对应一个独立的命令处理器类。
- **工厂模式 (Factory Pattern)**: 统一的服务工厂负责创建和配置所有服务实例。
- **策略模式 (Strategy Pattern)**: 不同的处理策略（单视频vs批量）可以灵活替换。
- **适配器模式 (Adapter Pattern)**: Gemini API 交互封装在增强型服务适配器中。
- **观察者模式 (Observer Pattern)**: 批量处理进度和状态变化的实时监控。
- **模板方法模式 (Template Method Pattern)**: 教案生成基于可配置的模板系统。
- **依赖注入 (Dependency Injection)**: 服务工厂负责依赖管理，简化测试和维护。

### 企业级模式

- **断路器模式 (Circuit Breaker)**: API 调用失败时的智能回退机制。
- **重试模式 (Retry Pattern)**: 带有指数退避和抖动的智能重试策略。
- **缓存模式 (Caching Pattern)**: 配置和服务实例的智能缓存。
- **状态机模式 (State Machine)**: 批量任务的状态管理和转换。
    
