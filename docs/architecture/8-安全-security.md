# 8. 安全 (Security)

- **API 密钥安全**: 用户的 `api_key` **必须** 存储在 `config.yaml` 文件中。该文件**必须**被添加到 `.gitignore` 中，以防止意外提交。项目中将提供一个 `config.yaml.example` 文件作为模板。

- **OAuth 2.0 安全**:
  - **客户端凭据安全**: `client_id` 和 `client_secret` **必须** 存储在 `config.yaml` 文件中，同样受 `.gitignore` 保护。
  - **访问令牌管理**: `access_token` 和 `refresh_token` 自动管理，存储在配置文件中但定期刷新。
  - **令牌过期处理**: 系统自动检测令牌过期并启动刷新流程，无需用户干预。
  - **最小权限原则**: OAuth scope 仅请求访问用户YouTube视频所需的最小权限。

- **多认证模式兼容**: 系统默认使用API Key认证（公有视频），仅在需要时切换至OAuth认证（私有视频），确保现有用户的使用体验不受影响。