# 3. 源码树 (Source Tree)

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
