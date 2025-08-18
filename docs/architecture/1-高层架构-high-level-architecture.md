# 1. 高层架构 (High Level Architecture)

## 技术摘要 (Technical Summary)

本项目 `gs_videoReport` 的架构是一个模块化的、运行于 macOS 终端的 Python 命令行工具 (CLI)。其核心是一个直接与 Google Gemini API 交互的客户端应用。整个架构遵循关注点分离 (Separation of Concerns) 的原则，将输入处理、AI 分析、以及教案生成等功能解耦为独立的服务模块，以提高代码的可测试性、可维护性和未来的可扩展性。

## 高层概览 (High Level Overview)

- **架构风格**: 客户端-API (Client-API) 架构。
    
- **仓库结构**: 单一仓库 (Monorepo)。
    
- **核心数据流**:
    
    1. 用户在终端输入命令 (`gs_videoReport <youtube_url>`)。
        
    2. **CLI 模块** 解析并验证输入参数。
        
    3. **Gemini 服务模块** 直接接收 YouTube URL，并将其发送给 Google Gemini API 进行分析和总结。SDK 会在后台处理视频内容的提取。
        
    4. **教案生成模块** 使用一个标准模板，将 API 返回的结果格式化为 Markdown 内容，并注入 Obsidian 兼容的元数据。
        
    5. **文件输出模块** 将最终的 Markdown 字符串写入本地文件系统。
        

## 高层项目图 (High Level Project Diagram)

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
        E -- Sends YouTube URL for Analysis --> I[Google Gemini API];
    end

    G -- Writes File --> J[教案.md];

    style J fill:#f9f,stroke:#333,stroke-width:2px
```

## 架构与设计模式 (Architectural and Design Patterns)

- **命令行接口 (CLI)**: 作为与用户交互的主要模式。
    
- **适配器模式 (Adapter Pattern)**: 我们将把与 Google Gemini API 的直接交互封装在一个“适配器”或“服务”类中。
    
- **模板方法模式 (Template Method Pattern)**: 教案的生成将基于一个基础模板。
    
- **依赖注入 (Dependency Injection)**: 在构建应用时，我们会将外部依赖“注入”到需要它的模块中，以简化测试。
    
