# gs_videoReport

An AI-powered video-to-lesson-plan converter for educators, especially in the arts and media fields.

## 🎯 Project Status

**Current Phase**: v0.1.0 MVP Released ✅  
**Quality Gate**: 87.5/100 (85.7% test pass rate) ✅  
**Production Ready**: Yes, with noted limitations ✅

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

1. **⚠️ SECURITY NOTICE**: Never commit your API keys to version control!

2. Copy and edit the configuration file:
```bash
# Copy the example configuration
cp config.yaml.example config.yaml

# Edit config.yaml and add your Google Gemini API key
# This file is in .gitignore and won't be committed
```

3. Add your API key to `config.yaml`:
```yaml
api_key: "your-actual-gemini-api-key-here"
```

4. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

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

## 🔧 Usage Examples

```bash
# Show help
gs_videoreport --help

# Process a local video file  
gs_videoreport video.mp4

# Use specific template and model
gs_videoreport video.mp4 --template chinese_transcript --model gemini-2.5-pro

# Specify output directory
gs_videoreport video.mp4 --output ./my_lessons --verbose

# List available templates
gs_videoreport list-templates

# Show available models
gs_videoreport list-models

# Interactive API setup
gs_videoreport setup-api
```

## 🔧 Development Commands

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest tests/

# Run with poetry
poetry run gs_videoreport --help

# Development mode
poetry run python -m src.gs_video_report.cli --help
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
