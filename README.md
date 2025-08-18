# gs_videoReport

An AI-powered video-to-lesson-plan converter for educators, especially in the arts and media fields.

## 🎯 Project Status

**Current Phase**: Development Ready ✅  
**Project Structure**: Created ✅  
**Next Step**: Begin Story 1.2 - CLI Development

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** 
2. **Poetry** (recommended) or pip
3. **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

#### Option 1: Using Poetry (Recommended)
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install

# Activate virtual environment
poetry shell
```

#### Option 2: Using pip
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies manually
pip install google-genai typer pyyaml yt-dlp httpx pytest
```

### Configuration

1. Copy and edit the configuration file:
```bash
# Configuration file already created at config.yaml
# Edit config.yaml and add your Google Gemini API key
```

2. Add your API key to `config.yaml`:
```yaml
google_api:
  api_key: "YOUR_ACTUAL_API_KEY_HERE"
```

## 📁 Project Structure

```
gs_videoReport/
├── src/gs_video_report/          # Main application code
│   ├── cli.py                    # Command line interface
│   ├── config.py                 # Configuration management
│   ├── template_manager.py       # Prompt template management
│   ├── services/
│   │   └── gemini_service.py     # Google Gemini API integration
│   ├── templates/
│   │   ├── prompts/              # Prompt templates for AI
│   │   └── outputs/              # Output format templates
│   ├── report_generator.py       # Lesson plan generation
│   ├── file_writer.py           # File output handling
│   └── main.py                  # Application entry point
├── tests/                       # Test files
├── docs/                        # Project documentation
├── config.yaml                 # Configuration file
└── pyproject.toml              # Dependencies and project metadata
```

## 🎯 Development Roadmap

### Phase 1: MVP Implementation
- [ ] **Story 1.2**: CLI Interface and Input Validation
- [ ] **Story 1.3**: API Integration and Prompt Template Management  
- [ ] **Story 1.4**: Lesson Plan Formatting and Output
- [ ] **Story 1.1**: End-to-End Integration Testing

### Current Development Priority
**Start with Story 1.2** - Command Line Interface
- Most independent component
- No external API dependencies needed
- Quick wins to build confidence

## 🔧 Development Commands

```bash
# Run tests
pytest tests/

# Run the application (when implemented)
poetry run gs_videoreport --help
poetry run gs_videoreport https://youtube.com/watch?v=xxx

# Development mode
poetry run python -m gs_video_report.main
```

## 📚 Key Features

- **Prompt Template Management**: Customizable AI prompts for different lesson types
- **Multiple Output Formats**: Comprehensive lessons, summaries, detailed analysis
- **Obsidian Integration**: Compatible YAML frontmatter and timestamps
- **YouTube Integration**: Direct video URL processing
- **Precise Timestamps**: Clickable time-coded links back to video

## 🎨 Template System

The application supports multiple prompt templates:

- **comprehensive_lesson**: Full lesson plan with detailed analysis
- **summary_report**: Concise video summary
- **custom templates**: User-defined prompt templates

Templates are stored in `src/gs_video_report/templates/prompts/` and can be customized.

## 📖 Documentation

- **Development Handoff**: `DEVELOPMENT_HANDOFF.md` - Complete development guide
- **User Stories**: `docs/stories/` - Detailed feature specifications  
- **Architecture**: `docs/architecture/` - Technical architecture documentation
- **PRD**: `docs/prd/` - Product requirements and specifications

## 🚀 Next Steps

1. **Begin Development**: Start with Story 1.2 (CLI Interface)
2. **Set up Testing**: Initialize test framework
3. **Implement Core Features**: Follow the user story sequence
4. **Integration Testing**: Verify end-to-end functionality

## 🤝 Contributing

This is currently a personal project. Development follows the user stories defined in `docs/stories/`.

## 📄 License

[Add your license here]

---

**Ready to start development!** 🎉

Begin with Story 1.2: CLI Interface and Input Validation.
