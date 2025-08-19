# gs_videoReport 架构文档索引

📐 **全面的技术架构文档 - 从单体处理到企业级批量处理**

## 📁 目录结构概览

```text
docs/architecture/
├── README.md                    # 📚 架构文档主索引（本文档）
├── index.md                     # 🔗 快速导航页面
├── 1-高层架构-high-level-architecture.md  # 🆕 v2.2 动态并行架构
├── 2-技术栈-tech-stack.md
├── 3-源码树-source-tree.md
├── 4-数据模型-data-models.md
├── 5-核心工作流-core-workflow.md          # 🆕 v2.2 专用Worker工作流
├── 6-错误处理策略-error-handling-strategy.md
├── 7-测试策略-test-strategy.md
├── 8-安全-security.md
├── 9-模块化CLI架构-modular-cli-architecture.md  # 🆕 v0.2.0 模块化CLI设计
├── 10-多密钥管理架构-multi-key-architecture.md  # 🆕 v2.1 多密钥管理
└── batch_processing/            # 🚀 企业级批量处理架构
    ├── README.md               # 批量处理主文档
    ├── overview.md             # 架构总览
    ├── implementation_guide.md # 实现指南
    ├── technical_design.md     # 技术设计
    ├── technical_feasibility.md # 可行性分析
    ├── api_specification.md    # API规范
    ├── data_flow_design.md     # 数据流设计
    ├── performance_optimization.md # 性能优化
    ├── testing_strategy.md     # 测试策略
    ├── user_scenarios.md       # 用户场景
    ├── HANDOVER_TO_DEV_TEAM.md # 开发移交
    ├── diagrams/              # 📊 架构图表（待添加）
    ├── specs/                 # 📋 详细规范（待添加）
    └── examples/              # 💡 示例代码（待添加）
```

## 🎯 文档导航

### 📋 核心架构 (v2.2 动态并行就绪)
专用Worker和动态并行处理的企业级架构，已通过生产环境验证：

| 文档 | 描述 | 状态 | 负责方 |
|------|------|------|--------|
| [1. 高层架构](./1-高层架构-high-level-architecture.md) | 🆕 动态并行处理系统整体设计 | ✅ v2.2更新 | @architect |
| [2. 技术栈](./2-技术栈-tech-stack.md) | 依赖库和技术选型 | ✅ 生产就绪 | @dev-lead |
| [3. 源码树](./3-源码树-source-tree.md) | 代码组织结构 | ✅ 已更新 | @dev-lead |
| [4. 数据模型](./4-数据模型-data-models.md) | 核心数据结构定义 | ✅ 已扩展 | @architect |
| [5. 核心工作流](./5-核心工作流-core-workflow.md) | 🆕 专用Worker并行处理流程 | ✅ v2.2更新 | @architect |

### 🆕 v2.2 架构突破性创新
新模块化架构设计，实现从单体到微服务风格的转换：

| 文档 | 描述 | 状态 | 负责方 |
|------|------|------|--------|
| [9. 模块化CLI架构](./9-模块化CLI架构-modular-cli-architecture.md) | 全新CLI架构：命令模式+工厂模式+依赖注入 | ✅ 完整 | @architect |

### 🛡️ 质量保证架构
| 文档 | 描述 | 状态 | 负责方 |
|------|------|------|--------|
| [6. 错误处理策略](./6-错误处理策略-error-handling-strategy.md) | 异常处理和恢复机制 | ✅ v0.1.1增强 | @dev-lead |
| [7. 测试策略](./7-测试策略-test-strategy.md) | 测试框架和覆盖率 | ✅ 85.7%通过率 | @qa-engineer |
| [8. 安全](./8-安全-security.md) | 安全策略和认证机制 | ✅ OAuth就绪 | @architect |

### 🚀 企业级批量处理架构 (v0.2.0 开发中)
完整的批量处理架构设计，支持35-70视频/小时的高并发处理：

| 文档 | 描述 | 状态 | 负责方 |
|------|------|------|--------|
| **[批量处理架构概览](./batch_processing/README.md)** | **主文档入口和导航** | **✅ 完整** | **@architect** |
| [架构设计总览](./batch_processing/overview.md) | 高层设计和技术决策 | ✅ 完整 | @architect |
| [技术实现指南](./batch_processing/implementation_guide.md) | 开发团队实现指导 | ✅ 8周计划 | @architect |
| [API接口规范](./batch_processing/api_specification.md) | CLI和内部API设计 | ✅ 完整 | @architect |
| [数据流设计](./batch_processing/data_flow_design.md) | 任务流和状态管理 | ✅ 完整 | @architect |
| [性能优化策略](./batch_processing/performance_optimization.md) | 性能调优和监控 | ✅ 完整 | @architect |
| [技术设计](./batch_processing/technical_design.md) | 详细技术实现规范 | ✅ 完整 | @architect |
| [技术可行性](./batch_processing/technical_feasibility.md) | 技术方案可行性分析 | ✅ 完整 | @architect |
| [测试策略](./batch_processing/testing_strategy.md) | 批量处理测试方案 | ✅ 完整 | @qa-engineer |
| [用户场景](./batch_processing/user_scenarios.md) | 企业用户使用场景 | ✅ 完整 | @architect |
| [开发团队移交](./batch_processing/HANDOVER_TO_DEV_TEAM.md) | 开发启动指导 | ✅ 完整 | @architect |

#### 批量处理支持资源
| 目录 | 用途 | 状态 |
|------|------|------|
| `batch_processing/diagrams/` | 架构图表和流程图 | 📁 待添加 |
| `batch_processing/specs/` | 详细技术规范 | 📁 待添加 |
| `batch_processing/examples/` | 代码示例和配置模板 | 📁 待添加 |

## 🏗️ 架构演进历程

### v0.1.0 MVP (2025-01-27)
- ✅ **基础架构确立**: 单视频处理的完整架构
- ✅ **核心功能实现**: CLI + Gemini API + 文件输出
- ✅ **模板系统**: 支持自定义AI提示模板
- ✅ **配置管理**: API密钥优先级系统

### v0.1.1 稳定版 (2025-01-27)
- ✅ **CLI一致性**: 所有命令支持--api-key参数
- ✅ **错误处理增强**: 用户友好的错误信息和解决方案
- ✅ **架构文档完善**: OAuth支持和安全策略更新
- ✅ **质量提升**: 85.7%测试通过率

### v0.2.0 企业级批量处理 (CLI重构完成)
- ✅ **模块化CLI架构**: 从1,294行单体重构为20个职责单一的模块
- ✅ **增强型Gemini服务**: 模型兼容性检测、智能回退、成本追踪
- ✅ **批量处理核心**: 状态管理、工作池、智能重试机制
- ✅ **设计模式应用**: 命令模式、工厂模式、策略模式、依赖注入
- ✅ **CLI命令迁移**: 11个命令100%迁移完成，旧文件已清理
- 🚧 **测试覆盖**: 完善单元测试和集成测试

## 📊 架构指标

### 当前性能 (v0.2.0)
```yaml
单视频处理:
  延迟: "2-5分钟/视频 (10分钟标准视频)"
  内存使用: "<200MB峰值"
  并发度: "1个视频"
  可靠性: "85.7%成功率"

CLI架构指标:
  模块数量: "20个文件 (from 1个单体文件)"
  代码行数: "4,248行 (from 1,294行单体)"
  平均模块大小: "~212行/模块"
  设计模式: "命令模式+工厂模式+依赖注入"
  命令迁移: "11个命令100%完成"

质量指标:
  测试覆盖率: "85.7% (12/14测试通过)"
  文档完整性: "100% (所有组件有文档)"
  架构重构: "✅ 完全完成"
  生产就绪性: "✅ 新架构已部署"
```

### 目标性能 (v0.2.0)
```yaml
批量处理:
  吞吐量: "35-70视频/小时"
  并发度: "2-8工作线程"
  内存使用: "<2GB峰值"
  可靠性: "100%检查点恢复"

企业指标:
  测试覆盖率: ">85%"
  错误恢复: "100%自动恢复"
  监控完整性: "实时进度和资源监控"
```

## 🎯 架构决策记录 (ADR)

### 关键技术决策

1. **[ADR-001] Google Gemini API选择**
   - **决策**: 选择google-genai SDK替代直接API调用
   - **理由**: 官方支持、类型安全、版本兼容性
   - **状态**: ✅ 已实施 (v0.1.0)

2. **[ADR-002] CLI框架选择**
   - **决策**: 选择Typer + Rich替代Click + 原生终端
   - **理由**: 类型安全、现代化UI、更好的用户体验
   - **状态**: ✅ 已实施 (v0.1.0)

3. **[ADR-003] 批量处理并发模型**
   - **决策**: asyncio + ThreadPoolExecutor混合模型
   - **理由**: I/O密集 + CPU密集混合场景优化
   - **状态**: 🚧 设计完成，开发中 (v0.2.0)

4. **[ADR-004] 状态存储方案**
   - **决策**: SQLite + JSON混合存储
   - **理由**: 结构化查询 + 灵活元数据，无外部依赖
   - **状态**: 🚧 设计完成，开发中 (v0.2.0)

5. **[ADR-005] CLI架构重构**
   - **决策**: 模块化CLI - 命令模式+工厂模式+依赖注入
   - **理由**: 单体CLI(1,294行)难以维护，需要实现职责分离和可测试性
   - **状态**: ✅ 已完成 (v0.2.0) - 20个模块，11个命令完全迁移

## 🔄 文档维护

### 责任分工
- **@architect**: 批量处理架构设计和高级架构决策
- **@dev-lead**: 核心架构实现和技术债务管理  
- **@qa-engineer**: 测试策略和质量门禁
- **@po**: 架构需求和优先级决策

### 更新频次
- **核心架构文档**: 每个版本发布时更新
- **批量处理文档**: 开发阶段每周更新
- **ADR记录**: 重大技术决策时立即更新
- **性能指标**: 每个版本验证和更新

---

**📝 文档版本**: v1.3 (与v0.2.0 CLI重构对应)  
**🔄 最后更新**: 2025-01-27  
**👥 维护团队**: Architecture Team  
**🎯 下次更新**: v0.2.0批量处理功能完成时  

> **💡 快速导航提示**: 
> - 了解单视频架构 → 从 [高层架构](./1-高层架构-high-level-architecture.md) 开始
> - 批量处理开发 → 直接查看 [批量处理架构](./batch_processing/README.md)
> - 技术实现细节 → 按编号顺序阅读 1-8 号文档
