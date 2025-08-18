# 4. 数据模型 (Data Models)

- **`Configuration`**: 代表从 `config.yaml` 文件中加载的配置信息 (`api_key`, `model_name`, `default_output_path`, `default_prompt_template`, `auth_type`, `oauth_config`)。支持多种认证方式以访问公有和私有YouTube视频。

- **`AuthConfig`**: 认证配置的抽象基类，支持不同的认证策略 (`auth_type`, `api_key_config`, `oauth_config`)。

- **`OAuthConfig`**: OAuth 2.0 认证配置信息 (`client_id`, `client_secret`, `access_token`, `refresh_token`, `token_expiry`)，用于访问私有YouTube视频。

- **`PromptTemplate`**: 代表提示词模板的结构化数据 (`name`, `version`, `description`, `parameters`, `prompt_content`, `model_config`)。

- **`TemplateManager`**: 管理提示词模板的加载、选择和参数化功能 (`load_templates()`, `get_template()`, `render_prompt()`)。

- **`LessonPlan`**: 代表最终生成的教案内容的结构化表示 (`video_title`, `video_url`, `obsidian_metadata`, `content_markdown`, `template_used`)。
