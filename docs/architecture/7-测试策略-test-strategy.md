# 7. 测试策略 (Test Strategy)

- **单元测试**: 使用 `pytest` 对所有独立模块进行测试，并对外部依赖（如 API、文件系统）进行模拟 (Mocking)。
    
- **集成测试**: 创建一个单独的端到端测试，使用真实的 API 密钥对一个简短视频进行测试，以验证与 Google Gemini API 的集成。
    
