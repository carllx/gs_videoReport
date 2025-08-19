# 2. 技术栈 (Tech Stack)

> **版本**: v2.1 | **更新**: 2025-01-19 | **新增**: 多密钥管理架构

|   |   |   |   |   |
|---|---|---|---|---|
|**分类 (Category)**|**技术 (Technology)**|**版本 (Version)**|**用途 (Purpose)**|**理由 (Rationale)**|
|**语言 (Language)**|Python|`~3.11`|主要开发语言|社区成熟，拥有强大的 AI 和数据处理生态。|
|**依赖管理 (Dependency Mgmt)**|Poetry|`~1.8`|管理项目依赖、打包和虚拟环境|现代化的 Python 依赖管理工具。|
|**命令行框架 (CLI Framework)**|Typer|`~0.12`|构建命令行交互界面|代码简洁、易于维护，并能自动生成帮助文档。|
|**AI 服务 SDK (AI Service SDK)**|google-genai|`latest`|与 Google Gemini API 交互|最新官方 Python SDK，支持现代化API接口和函数调用功能。|
|**配置管理 (Config Mgmt)**|PyYAML|`~6.0`|解析 `config.yaml` 配置文件|处理 YAML 文件的标准库。|
|**视频处理 (Video Processing)**|yt-dlp|`latest`|YouTube 视频下载和处理|替代 youtube-dl 的现代化工具，支持更多平台。|
|**HTTP 客户端 (HTTP Client)**|httpx|`~0.27`|HTTP 请求处理|google-genai SDK 的默认 HTTP 客户端，支持同步/异步。|
|**测试框架 (Testing Framework)**|Pytest|`~8.2`|编写和执行单元与集成测试|Python 测试的事实标准。|
|**🆕 多密钥管理**|Multi-Key Architecture|`v2.1`|API配额管理和智能轮换|解决免费层配额限制，提升300%+处理能力。|
|**🆕 配额监控**|APIQuotaMonitor|`v2.1`|实时配额追踪和可视化|Rich界面仪表盘，预测性配额管理。|
|**🆕 用户界面库**|Rich|`~13.0`|终端用户界面和进度显示|现代化CLI体验，支持表格、进度条等。|
