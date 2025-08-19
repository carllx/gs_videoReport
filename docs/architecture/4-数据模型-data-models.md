# 4. 数据模型 (Data Models v2.2)

## 核心配置模型

- **`Configuration`**: 代表从 `config.yaml` 文件中加载的配置信息 (`api_key`, `model_name`, `default_output_path`, `default_prompt_template`, `auth_type`, `oauth_config`, `🆕 multi_api_keys`, `🆕 batch_processing`)。支持多种认证方式和动态并行配置。

- **`🆕 MultiApiKeysConfig`**: v2.2多API密钥配置 (`enabled: bool`, `api_keys: List[str]`, `rotation_strategy: str`, `quota_tracking: bool`)，支持智能密钥轮换。

- **`🆕 BatchProcessingConfig`**: 批量处理配置 (`parallel_workers: int`, `max_retries: int`, `timeout_seconds: int`, `resume_on_failure: bool`)，支持动态并发控制。

## 认证和安全模型

- **`AuthConfig`**: 认证配置的抽象基类，支持不同的认证策略 (`auth_type`, `api_key_config`, `oauth_config`)。

- **`OAuthConfig`**: OAuth 2.0 认证配置信息 (`client_id`, `client_secret`, `access_token`, `refresh_token`, `token_expiry`)，用于访问私有YouTube视频。

- **`🆕 ApiKeyInfo`**: v2.2 API密钥信息模型 (`key_id: str`, `usage_count: int`, `last_used: datetime`, `quota_exhausted: bool`, `error_count: int`)。

## 模板和内容模型

- **`PromptTemplate`**: 代表提示词模板的结构化数据 (`name`, `version`, `description`, `parameters`, `prompt_content`, `model_config`)。

- **`TemplateManager`**: 管理提示词模板的加载、选择和参数化功能 (`load_templates()`, `get_template()`, `render_prompt()`)。

- **`LessonPlan`**: 代表最终生成的教案内容的结构化表示 (`video_title`, `video_url`, `obsidian_metadata`, `content_markdown`, `template_used`)。

## v2.2 并行处理模型

- **`🆕 TaskRecord`**: 任务记录模型 (`task_id: str`, `video_path: str`, `status: TaskStatus`, `worker_id: str`, `api_key_id: str`, `start_time: datetime`, `completion_time: datetime`, `error_info: Optional[dict]`)。

- **`🆕 TaskStatus`**: 任务状态枚举 (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `SKIPPED`)。

- **`🆕 WorkerInfo`**: Worker信息模型 (`worker_id: str`, `api_key: str`, `current_task: Optional[str]`, `total_processed: int`, `status: WorkerStatus`)。

- **`🆕 BatchState`**: 批量处理状态模型 (`batch_id: str`, `total_tasks: int`, `completed_tasks: int`, `failed_tasks: int`, `skipped_tasks: int`, `worker_stats: Dict[str, WorkerInfo]`, `start_time: datetime`)。
