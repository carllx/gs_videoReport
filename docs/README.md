# gs_videoReport 文档中心

🎓 **AI驱动视频转教案工具** - 完整文档导航系统

欢迎来到gs_videoReport项目的文档中心。本页面为您提供项目所有文档的完整索引和导航。

> 📖 **多语言支持**: [English](../README.md) | [中文](../README-zh.md) | [变更日志](../CHANGELOG-zh.md)

## 🚀 快速导航

### 🎯 新用户入门
| 文档 | 描述 | 状态 |
|------|------|------|
| [快速开始 (README)](../README-zh.md) | 项目介绍、安装配置、使用示例 | ✅ v0.1.1 |
| [API密钥设置](./API_KEY_SETUP.md) | Google Gemini API密钥获取和配置 | ✅ 完整 |
| [变更日志](../CHANGELOG-zh.md) | 版本历史和功能更新记录 | ✅ 最新 |

### 👥 开发者资源
| 文档 | 描述 | 状态 |
|------|------|------|
| [架构文档总览](./architecture/README.md) | 完整技术架构导航索引 | ✅ v1.2 |
| [架构快速导航](./architecture/index.md) | 架构文档快速浏览页面 | ✅ 完整 |
| [用户故事集合](#-用户故事与功能规范) | 功能需求和验收标准 | ✅ v0.1.1完成 |
| [产品需求文档](#-产品需求文档-prd) | 完整产品规范和需求 | ✅ 已更新 |

---

## 📋 文档分类索引

### 📋 项目规划和管理
| 目录 | 描述 | 状态 |
|------|------|------|
| [📋 规划文档](./planning/) | 项目路线图、开发计划和阶段规划 | ✅ 最新 |
| [📊 项目报告](./reports/) | 技术分析报告和评估文档 | ✅ 完整 |
| [🧪 QA和测试](./qa/) | 质量保证规则和测试报告 | ✅ 强制执行 |

### 🏗️ 架构文档

#### 核心架构 (v0.1.1 生产就绪)
| 序号 | 文档 | 描述 | 负责人 | 状态 |
|------|------|------|--------|------|
| 1 | [高层架构](./architecture/1-高层架构-high-level-architecture.md) | 系统整体设计和数据流 | @dev-lead | ✅ 已更新 |
| 2 | [技术栈](./architecture/2-技术栈-tech-stack.md) | 依赖库和技术选型 | @dev-lead | ✅ 生产就绪 |
| 3 | [源码树](./architecture/3-源码树-source-tree.md) | 代码组织结构 | @dev-lead | ✅ 已更新 |
| 4 | [数据模型](./architecture/4-数据模型-data-models.md) | 核心数据结构定义 | @architect | ✅ 已扩展 |
| 5 | [核心工作流](./architecture/5-核心工作流-core-workflow.md) | 端到端处理流程 | @architect | ✅ 已更新 |

#### 质量保证架构
| 序号 | 文档 | 描述 | 负责人 | 状态 |
|------|------|------|--------|------|
| 6 | [错误处理策略](./architecture/6-错误处理策略-error-handling-strategy.md) | 异常处理和恢复机制 | @dev-lead | ✅ v0.1.1增强 |
| 7 | [测试策略](./architecture/7-测试策略-test-strategy.md) | 测试框架和覆盖率 | @qa-engineer | ✅ 85.7%通过率 |
| 8 | [安全](./architecture/8-安全-security.md) | 安全策略和认证机制 | @architect | ✅ OAuth就绪 |

#### 企业级批量处理架构 (v0.2.0 开发中)
| 文档 | 描述 | 负责人 | 状态 |
|------|------|--------|------|
| **[批量处理主文档](./architecture/batch_processing/README.md)** | **完整批量处理架构导航** | **@architect** | **✅ 完整** |
| [架构设计总览](./architecture/batch_processing/overview.md) | 高层设计和技术决策 | @architect | ✅ 完整 |
| [技术实现指南](./architecture/batch_processing/implementation_guide.md) | 8周开发计划和任务分解 | @architect | ✅ 完整 |
| [API接口规范](./architecture/batch_processing/api_specification.md) | CLI和内部API设计 | @architect | ✅ 完整 |
| [数据流设计](./architecture/batch_processing/data_flow_design.md) | 任务流和状态管理 | @architect | ✅ 完整 |
| [性能优化策略](./architecture/batch_processing/performance_optimization.md) | 性能调优和监控 | @architect | ✅ 完整 |
| [技术设计](./architecture/batch_processing/technical_design.md) | 详细技术实现 | @architect | ✅ 完整 |
| [技术可行性](./architecture/batch_processing/technical_feasibility.md) | 技术方案可行性分析 | @architect | ✅ 完整 |
| [测试策略](./architecture/batch_processing/testing_strategy.md) | 批量处理测试方案 | @qa-engineer | ✅ 完整 |
| [用户场景](./architecture/batch_processing/user_scenarios.md) | 企业用户使用场景 | @architect | ✅ 完整 |
| [开发团队移交](./architecture/batch_processing/HANDOVER_TO_DEV_TEAM.md) | 开发启动指导 | @architect | ✅ 完整 |

### 📊 产品需求文档 (PRD)

#### PRD总览
| 文档 | 描述 | 状态 |
|------|------|------|
| **[产品需求总文档](./prd.md)** | **完整产品需求和规范** | **✅ v0.1.1已更新** |
| [PRD导航索引](./prd/index.md) | PRD文档结构化导航 | ✅ 完整 |

#### PRD分章节文档
| 序号 | 章节 | 文档 | 描述 | 状态 |
|------|------|------|------|------|
| 1 | 目标与背景 | [goals-and-background](./prd/1-目标与背景-goals-and-background-context.md) | 项目目标和背景上下文 | ✅ 完整 |
| 2 | 需求规范 | [requirements](./prd/2-需求-requirements.md) | 功能需求和非功能需求 | ✅ v0.1.1更新 |
| 3 | 技术假设 | [technical-assumptions](./prd/3-技术假设-technical-assumptions.md) | 技术约束和假设条件 | ✅ 完整 |
| 4 | 史诗列表 | [epic-list](./prd/4-史诗列表-epic-list.md) | 高层功能史诗规划 | ✅ 完整 |
| 5 | 核心引擎史诗 | [mvp-epic](./prd/5-史诗-1-核心视频转教案引擎-mvp.md) | MVP核心功能详细规范 | ✅ v0.1.1完成 |
| 6 | 清单检查报告 | [checklist-report](./prd/6-清单检查结果报告-checklist-results-report.md) | 需求完整性验证报告 | ✅ 完整 |
| 7 | 下一步规划 | [next-steps](./prd/7-下一步-next-steps.md) | 后续版本规划 | ✅ v0.2.0规划 |

### 📖 用户故事与功能规范

#### MVP功能故事 (v0.1.1 已完成)
| 故事编号 | 文档 | 功能描述 | 状态 | QA结果 |
|----------|------|----------|------|---------|
| 1.1 | [本地视频处理](./stories/1.1.youtube-video-processing.md) | 本地视频文件分析和教案生成 | ✅ 完成 | ✅ 100%通过 |
| 1.2 | [CLI输入验证](./stories/1.2.cli-input-validation.md) | 命令行界面和参数验证 | ✅ 完成 | ✅ v0.1.1增强 |
| 1.3 | [API集成分析](./stories/1.3.api-integration-analysis.md) | Google Gemini API集成 | ✅ 完成 | ✅ 认证增强 |
| 1.4 | [教案格式化输出](./stories/1.4.lesson-formatting-output.md) | Markdown教案生成和输出 | ✅ 完成 | ✅ 模板系统 |

### 🔧 技术参考文档

#### v2.1 新增指南文档
| 文档 | 描述 | 更新时间 | 状态 |
|------|------|----------|------|
| [API配额管理指南](./guides/QUOTA_MANAGEMENT_GUIDE.md) | 多密钥轮换和配额监控完整解决方案 | 2025-01-19 | ✅ v2.1 完整 |
| [纯中文模板指南](./guides/CHINESE_TEMPLATE_USAGE_GUIDE.md) | v2.0中文模板使用和参数优化指南 | 2025-01-19 | ✅ v2.0 完整 |
| [API故障排查指南](./troubleshooting/API_TROUBLESHOOTING_GUIDE.md) | Google Gemini API问题诊断和解决方案 | 2025-01-19 | ✅ 完整 |

#### 专项技术文档
| 文档 | 描述 | 更新时间 | 状态 |
|------|------|----------|------|
| [OAuth集成指南](./OAUTH_INTEGRATION.md) | OAuth 2.0认证集成详细指南 | 2025-01-27 | ✅ 完整 |
| [API密钥设置指南](./API_KEY_SETUP.md) | Google Gemini API密钥获取和配置 | 2025-01-27 | ✅ 完整 |

#### 历史文档和参考资料
| 文档 | 描述 | 状态 |
|------|------|------|
| [架构总览](./architecture/overview.md) | 早期架构设计概览 | 📚 历史参考 |
| [项目简介](./brief.md) | 项目初期简介 | 📚 历史参考 |
| [头脑风暴](./brainstorm.md) | 初期创意和想法记录 | 📚 历史参考 |

---

## 📈 文档状态统计

### 完成度统计
```yaml
总文档数量: "44个文档 (+3个v2.1新增指南)"
完成状态:
  ✅ 完整: "44个文档 (100%)"
  🚧 开发中: "0个文档"
  📚 历史参考: "3个文档"

分类完成度:
  架构文档: "100% (单体 + 批量处理)"
  用户故事: "100% (v0.1.1 MVP)"
  产品需求: "100% (含v2.2规划)"
  技术参考: "100%"
  🆕 运维指南: "100% (v2.1新增)"
  🆕 故障排查: "100% (v2.1新增)"
  
索引完整性: "100% (所有文档已索引)"
```

### 版本对应关系
| 版本 | 文档状态 | 主要变更 |
|------|----------|----------|
| **v0.1.0** | 基础文档完整 | 初始MVP文档集合 |
| **v0.1.1** | 生产就绪文档 | 错误处理增强、CLI一致性 |
| **v2.1** | 🆕 运维指南完整 | API配额管理、中文模板v2.0、故障排查指南 |
| **v2.2** | 企业架构规划 | 自动化密钥管理、智能成本优化 |

---

## 🧭 文档使用指南

### 📍 按角色导航

#### 🆕 新用户/产品经理
1. 从 [项目README](../README-zh.md) 开始了解项目
2. 查看 [产品需求文档](./prd.md) 了解功能规划
3. 阅读 [用户故事](#-用户故事与功能规范) 了解具体功能
4. 🆕 **API配额问题**: 查看 [配额管理指南](./guides/QUOTA_MANAGEMENT_GUIDE.md)
5. 🆕 **中文模板使用**: 参考 [中文模板指南](./guides/CHINESE_TEMPLATE_USAGE_GUIDE.md)

#### 👨‍💻 开发工程师
1. 查看 [架构文档总览](./architecture/README.md) 了解技术架构
2. 按序号阅读核心架构文档 (1-8)
3. 参考 [批量处理实现指南](./architecture/batch_processing/implementation_guide.md)
4. 🆕 **API问题排查**: 使用 [故障排查指南](./troubleshooting/API_TROUBLESHOOTING_GUIDE.md)

#### 🧪 QA工程师
1. 查看 [测试策略](./architecture/7-测试策略-test-strategy.md) 
2. 了解 [错误处理策略](./architecture/6-错误处理策略-error-handling-strategy.md)
3. 参考 [批量处理测试策略](./architecture/batch_processing/testing_strategy.md)

#### 🏗️ 架构师/技术负责人
1. 查看 [高层架构](./architecture/1-高层架构-high-level-architecture.md)
2. 深入 [批量处理架构设计](./architecture/batch_processing/)
3. 参考 [技术假设文档](./prd/3-技术假设-technical-assumptions.md)

### 🔍 按主题导航

#### 单视频处理功能 (v0.1.1 生产就绪)
- **入门**: [项目README](../README-zh.md)
- **架构**: [核心架构文档](#核心架构-v011-生产就绪) (1-8)
- **实现**: [用户故事 1.1-1.4](#mvp功能故事-v011-已完成)

#### 批量处理功能 (v0.2.0 开发中)
- **总览**: [批量处理主文档](./architecture/batch_processing/README.md)
- **设计**: [架构设计总览](./architecture/batch_processing/overview.md)
- **开发**: [实现指南](./architecture/batch_processing/implementation_guide.md)

#### OAuth集成功能
- **指南**: [OAuth集成文档](./OAUTH_INTEGRATION.md)
- **安全**: [安全策略](./architecture/8-安全-security.md)
- **工作流**: [核心工作流](./architecture/5-核心工作流-core-workflow.md)

---

## 🔄 文档维护

### 维护责任分工
- **@po (产品经理)**: PRD文档、用户故事、需求变更
- **@architect (架构师)**: 批量处理架构文档权威维护
- **@dev-lead (开发负责人)**: 核心架构文档、实现文档
- **@qa-engineer (质量工程师)**: 测试策略、质量门禁文档

### 更新频次
- **版本发布时**: 全面文档审核和更新
- **功能开发中**: 相关架构文档实时更新
- **重大技术决策**: ADR记录立即更新

### 文档贡献指南
1. **新增文档**: 按现有分类结构添加，更新本索引
2. **修改文档**: 保持版本标记，记录变更历史
3. **删除文档**: 移至历史参考区，保留链接完整性

---

## 📞 获取帮助

### 快速问题解决
- **使用问题**: 查看 [快速开始指南](../README-zh.md)
- **配置问题**: 参考 [API密钥设置](./API_KEY_SETUP.md)  
- **🆕 API配额问题**: 查看 [配额管理指南](./guides/QUOTA_MANAGEMENT_GUIDE.md)
- **🆕 API故障排查**: 使用 [故障排查指南](./troubleshooting/API_TROUBLESHOOTING_GUIDE.md)
- **错误排查**: 查看 [错误处理策略](./architecture/6-错误处理策略-error-handling-strategy.md)

### 深度技术咨询
- **架构问题**: 联系 @architect，参考批量处理架构文档
- **开发问题**: 联系 @dev-lead，参考核心架构文档  
- **测试问题**: 联系 @qa-engineer，参考测试策略文档

---

**📝 文档索引版本**: v2.1  
**🔄 最后更新**: 2025-01-19  
**👥 维护团队**: 全项目团队  
**🎯 下次更新**: v2.2企业级增强发布时  

> **💡 导航提示**: 
> - 🆕 **新用户** → 从 [README](../README-zh.md) 开始
> - 👨‍💻 **开发者** → 直接查看 [架构文档](./architecture/README.md)  
> - 🏗️ **架构师** → 重点关注 [批量处理设计](./architecture/batch_processing/)
> - 📊 **产品** → 查看 [PRD文档](./prd.md) 和用户故事

**🎉 欢迎使用gs_videoReport！所有文档持续更新中，助力您的AI教案生成之旅！**
