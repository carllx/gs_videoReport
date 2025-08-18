"""
Command Line Interface for gs_videoReport

This module implements the CLI for processing YouTube videos and generating lesson plans.
"""
import os
import re
import sys
from pathlib import Path
from typing import Optional

import typer
import requests
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from .config import load_config, Config
from .template_manager import TemplateManager
from .services.gemini_service import GeminiService
from .lesson_formatter import LessonFormatter, LessonPlanData
from .file_writer import FileWriter, SuccessReporter

# Initialize Typer app
app = typer.Typer(
    name="gs_videoreport",
    help="""🎓 gs_videoReport v0.1.1 - AI-powered video-to-lesson-plan converter

Transform your video content into structured educational materials using Google Gemini AI.

QUICK START:
  gs_videoreport video.mp4                    # Basic usage
  gs_videoreport video.mp4 --verbose          # With detailed output  
  gs_videoreport setup-api                    # First-time setup

EXAMPLES:
  gs_videoreport video.mp4 --template chinese_transcript
  gs_videoreport video.mp4 --model gemini-2.5-pro --output ./lessons
  gs_videoreport list-templates               # See available templates
  
For more help: https://github.com/carllx/gs_videoReport""",
    add_completion=False,
    rich_markup_mode="rich"
)

# Console for rich output
console = Console()

# YouTube URL patterns for validation (video ID must be exactly 11 characters)
YOUTUBE_PATTERNS = [
    r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(?:\&.*)?$',
    r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})(?:\?.*)?$',
    r'https?://(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(?:\&.*)?$',
]


def validate_youtube_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate YouTube URL and extract video ID.
    
    Args:
        url: The URL to validate
        
    Returns:
        Tuple of (is_valid, video_id)
    """
    for pattern in YOUTUBE_PATTERNS:
        match = re.match(pattern, url)
        if match:
            return True, match.group(1)
    return False, None


def validate_video_file(file_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate local video file exists and has supported format.
    
    Args:
        file_path: Path to local video file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    supported_formats = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    
    try:
        file_path = Path(file_path).resolve()  # Resolve absolute path
    except (OSError, ValueError) as e:
        return False, f"Invalid file path: {e}"
    
    # Check if path exists
    if not file_path.exists():
        return False, f"File not found: {file_path}\n💡 Please check the file path and try again."
    
    # Check if it's actually a file (not a directory)
    if not file_path.is_file():
        return False, f"Path is not a file: {file_path}\n💡 Please provide a path to a video file, not a directory."
    
    # Check file format
    if file_path.suffix.lower() not in supported_formats:
        return False, (
            f"Unsupported video format '{file_path.suffix}'.\n"
            f"💡 Supported formats: {', '.join(supported_formats)}\n"
            f"💡 Convert your video to a supported format or rename the file extension."
        )
    
    # Check file permissions
    if not os.access(file_path, os.R_OK):
        return False, f"Permission denied: Cannot read file {file_path}\n💡 Check file permissions and try again."
    
    # Check file size and warn if very large
    try:
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb == 0:
            return False, f"File is empty: {file_path}\n💡 Please provide a valid video file."
        elif file_size_mb > 1000:  # 1GB limit warning
            return True, f"⚠️ Large file ({file_size_mb:.1f}MB) - processing may take longer"
    except OSError as e:
        return False, f"Cannot access file: {e}\n💡 File may be corrupted or inaccessible."
    
    return True, None


def detect_input_type(video_input: str) -> str:
    """
    Detect whether input is YouTube URL or local file path.
    
    Args:
        video_input: Input string to analyze
        
    Returns:
        'youtube' or 'local_file'
    """
    if validate_youtube_url(video_input)[0]:
        return 'youtube'
    return 'local_file'


def check_url_accessibility(url: str) -> bool:
    """
    Check if URL is accessible.
    
    Args:
        url: The URL to check
        
    Returns:
        True if accessible, False otherwise
    """
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False


@app.command()
def main(
    video_input: str = typer.Argument(
        ..., 
        help="📹 Local video file path to process (.mp4, .mov, .avi, .mkv, .webm)",
        metavar="VIDEO_FILE"
    ),
    template: Optional[str] = typer.Option(
        None, 
        "--template", 
        "-t", 
        help="📝 Template for analysis (comprehensive_lesson, summary_report, chinese_transcript)",
        metavar="TEMPLATE"
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o", 
        help="📁 Output directory for generated lesson plan",
        metavar="DIR"
    ),
    verbose: bool = typer.Option(
        False, 
        "--verbose", 
        "-v", 
        help="🔍 Enable detailed progress output"
    ),
    config_file: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="⚙️  Path to configuration file",
        metavar="FILE"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="🔑 Google Gemini API key (highest priority)",
        metavar="KEY"
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="🤖 AI model to use (gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite)",
        metavar="MODEL"
    )
):
    """
    🎓 Process a local video file and generate an AI-powered lesson plan.
    
    SUPPORTED FORMATS:
      .mp4, .mov, .avi, .mkv, .webm
    
    EXAMPLES:
      📚 Basic usage:
        gs_videoreport lecture.mp4
        
      🌟 Advanced usage:
        gs_videoreport video.mp4 --template chinese_transcript --verbose
        gs_videoreport video.mp4 --model gemini-2.5-pro --api-key YOUR_KEY
        gs_videoreport video.mp4 --output ./my_lessons --template summary_report
    
    FIRST TIME SETUP:
      gs_videoreport setup-api    # Interactive API key setup
      
    GET HELP:
      gs_videoreport list-templates  # See available templates
      gs_videoreport list-models     # See available AI models
    """
    if verbose:
        console.print(f"[bold green]🚀 Starting gs_videoReport[/bold green]")
        console.print(f"Input: {video_input}")
    
    # Detect input type
    input_type = detect_input_type(video_input)
    
    if input_type == 'youtube':
        # Handle YouTube URL
        is_valid, video_id = validate_youtube_url(video_input)
        if not is_valid:
            rprint("[bold red]❌ Error:[/bold red] Invalid YouTube URL")
            rprint("Please provide a valid YouTube URL in one of these formats:")
            rprint("  • https://www.youtube.com/watch?v=VIDEO_ID")
            rprint("  • https://youtu.be/VIDEO_ID")  
            rprint("  • https://m.youtube.com/watch?v=VIDEO_ID")
            sys.exit(1)
        
        if verbose:
            rprint(f"[green]✅ YouTube URL detected[/green]")
            rprint(f"Video ID: {video_id}")
            rprint("[yellow]⚠️  Note: YouTube download not implemented in MVP - please provide local video file[/yellow]")
        
        rprint("[bold red]❌ YouTube video download not yet implemented in MVP[/bold red]")
        rprint("Please download the video manually and provide the local file path instead.")
        rprint("Example: gs_videoreport /path/to/downloaded_video.mp4")
        sys.exit(1)
        
    else:
        # Handle local video file
        is_valid, error_msg = validate_video_file(video_input)
        if not is_valid:
            rprint(f"[bold red]❌ Video File Error:[/bold red] {error_msg}")
            sys.exit(1)
        
        if verbose:
            rprint(f"[green]✅ Local video file detected[/green]")
            if error_msg:  # Warning message
                rprint(f"[yellow]⚠️  {error_msg}[/yellow]")
    
    # Load configuration
    try:
        config = Config.from_file(config_file)
        if verbose:
            rprint("[green]✅ Configuration loaded[/green]")
    except FileNotFoundError as e:
        rprint(f"[bold red]❌ Configuration File Not Found:[/bold red] {e}")
        rprint("[yellow]💡 Solutions:[/yellow]")
        rprint("   • Create a config file: cp config.yaml.example config.yaml")
        rprint("   • Use --config option to specify a different config file")
        rprint("   • Use --api-key option to bypass config file")
        sys.exit(2)
    except Exception as e:
        rprint(f"[bold red]❌ Configuration Error:[/bold red] {e}")
        rprint("[yellow]💡 Check your config.yaml file for syntax errors[/yellow]")
        sys.exit(2)
    
    # Override config with CLI parameters
    if api_key:
        config.set('google_api.api_key', api_key)
        if verbose:
            rprint(f"[blue]🔑 Using API key from command line[/blue]")
    
    if model:
        # Validate model name
        valid_models = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite']
        if model not in valid_models:
            rprint(f"[bold red]❌ Error:[/bold red] Invalid model '{model}'")
            rprint(f"[yellow]Valid models:[/yellow] {', '.join(valid_models)}")
            sys.exit(1)
        config.set('google_api.model', model)
        if verbose:
            rprint(f"[blue]🤖 Using model: {model}[/blue]")
    
    # Initialize template manager
    try:
        template_mgr = TemplateManager(config)
        
        # Use provided template or default
        template_name = template or config.get('templates', {}).get('default_template', 'comprehensive_lesson')
        
        if verbose:
            rprint(f"[blue]📝 Using template: {template_name}[/blue]")
        
        # Validate template exists
        if not template_mgr.has_template(template_name):
            rprint(f"[bold red]❌ Template Not Found:[/bold red] '{template_name}' is not available")
            rprint("[yellow]💡 Solutions:[/yellow]")
            rprint("   • Use: gs_videoreport list-templates (to see available templates)")
            rprint("   • Available templates: comprehensive_lesson, summary_report, chinese_transcript")
            rprint("   • Check spelling and try again")
            sys.exit(1)
            
    except Exception as e:
        rprint(f"[bold red]❌ Template Error:[/bold red] {e}")
        sys.exit(2)
    
    # Process video using Gemini service
    if input_type == 'local_file':
        try:
            rprint(f"[bold green]🎯 Processing local video file with template: {template_name}[/bold green]")
            rprint(f"[blue]📹 Video file: {video_input}[/blue]")
            
            # Initialize Gemini service
            gemini_service = GeminiService(config)
            
            # Add default template parameters
            template_params = {
                'video_title': Path(video_input).stem,
                'video_duration': 'analyzing...',
                'subject_area': 'general',
                'detail_level': 'comprehensive',
                'language_preference': 'simplified_chinese'  # For chinese_transcript template
            }
            
            # Process video end-to-end
            rprint("[cyan]🚀 Starting video analysis with Google Gemini...[/cyan]")
            
            result = gemini_service.process_video_end_to_end(
                video_path=video_input,
                template_manager=template_mgr,
                template_name=template_name,
                cleanup_file=True,  # Clean up uploaded file after analysis
                **template_params
            )
            
            # Display results
            rprint(f"[bold green]🎉 Analysis completed successfully![/bold green]")
            rprint(f"[cyan]📊 Analysis Statistics:[/cyan]")
            rprint(f"  • Word count: {result.word_count}")
            rprint(f"  • Model used: {result.metadata['model']}")
            rprint(f"  • Template: {result.metadata['template']}")
            
            if verbose:
                rprint(f"[dim]📋 Analysis Preview (first 200 chars):[/dim]")
                preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
                rprint(f"[dim]{preview}[/dim]")
            
            # Format and save lesson plan (Story 1.4)
            try:
                rprint("[cyan]📝 Formatting lesson plan...[/cyan]")
                
                # Initialize lesson formatter and file writer
                lesson_formatter = LessonFormatter(config, template_mgr)
                file_writer = FileWriter(config)
                
                # Convert Gemini result to lesson plan format
                # Note: For now, we'll structure the result data properly
                lesson_data = {
                    'title': Path(video_input).stem,
                    'author': 'Unknown',
                    'duration': 'Unknown', 
                    'summary': result.content[:500] + "..." if len(result.content) > 500 else result.content,
                    'learning_objectives': 'Generated from video analysis',
                    'content_sections': [
                        {
                            'title': 'Video Analysis Content',
                            'content': result.content,
                            'timestamp_seconds': 0,
                            'key_points': []
                        }
                    ],
                    'important_timestamps': [],
                    'suggested_activities': 'To be customized based on content',
                    'related_resources': 'Additional resources can be added'
                }
                
                # Format the lesson plan
                formatted_lesson = lesson_formatter.format_lesson_plan(
                    gemini_result=lesson_data,
                    video_url=video_input,  # For local files, this will be the file path
                    template_name=template_name
                )
                
                # Generate output filename
                lesson_plan_data = LessonPlanData(lesson_data, video_input, config)
                output_filename = lesson_formatter.generate_filename(
                    lesson_plan_data,
                    output_dir=output
                )
                
                # Write the file
                write_result = file_writer.write_lesson_plan(
                    content=formatted_lesson,
                    file_path=output_filename,
                    overwrite=False
                )
                
                if write_result.success:
                    # Display success message
                    success_message = SuccessReporter.format_success_message(write_result)
                    rprint(success_message)
                    
                    # Offer to open file location
                    if not verbose:
                        rprint(f"[dim]💡 Use --verbose flag for more details[/dim]")
                    else:
                        file_info = file_writer.get_file_info(write_result.file_path)
                        file_info_message = SuccessReporter.format_file_info(file_info)
                        rprint(f"[dim]{file_info_message}[/dim]")
                        
                        # Attempt to open file location on macOS/Linux/Windows
                        rprint("[dim]🔍 Opening file location...[/dim]")
                        file_writer.open_file_location(write_result.file_path)
                else:
                    rprint(f"[bold red]❌ Failed to save lesson plan:[/bold red] {write_result.error_message}")
                    sys.exit(5)
                    
            except Exception as e:
                rprint(f"[bold red]❌ Lesson Plan Creation Error:[/bold red] {e}")
                if verbose:
                    import traceback
                    rprint(f"[dim]{traceback.format_exc()}[/dim]")
                sys.exit(5)
            
        except ValueError as e:
            rprint(f"[bold red]❌ Configuration Error:[/bold red] {e}")
            rprint("[yellow]💡 Solutions:[/yellow]")
            rprint("   • Set API key: gs_videoreport setup-api")
            rprint("   • Use --api-key option: gs_videoreport video.mp4 --api-key YOUR_KEY")
            rprint("   • Get API key: https://makersuite.google.com/app/apikey")
            sys.exit(3)
        except ConnectionError as e:
            rprint(f"[bold red]❌ Network Error:[/bold red] {e}")
            rprint("[yellow]💡 Solutions:[/yellow]")
            rprint("   • Check your internet connection")
            rprint("   • Verify your API key is valid")
            rprint("   • Try again in a few moments")
            sys.exit(4)
        except Exception as e:
            rprint(f"[bold red]❌ Analysis Error:[/bold red] {e}")
            rprint("[yellow]💡 Solutions:[/yellow]")
            rprint("   • Try with a smaller video file")
            rprint("   • Check video file is not corrupted") 
            rprint("   • Use --verbose flag for more details")
            if verbose:
                import traceback
                rprint(f"[dim]Debug info: {traceback.format_exc()}[/dim]")
            sys.exit(4)
    else:
        # Should not reach here due to earlier exit, but keep for safety
        rprint("[bold red]YouTube processing not available in MVP[/bold red]")


@app.command()
def list_templates(
    config_file: Optional[str] = typer.Option(
        None,
        "--config", 
        "-c",
        help="⚙️  Path to configuration file",
        metavar="FILE"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="🔑 Google Gemini API key (overrides env vars and config file)",
        metavar="KEY"
    )
):
    """📝 List all available prompt templates with descriptions and usage examples."""
    try:
        # Try to load config, but don't fail if API key is provided via CLI
        try:
            config = Config.from_file(config_file)
        except Exception:
            if api_key:
                # Create minimal config if API key provided via CLI
                config = Config({
                    'google_api': {'api_key': api_key},
                    'templates': {'default_template': 'comprehensive_lesson'}
                })
            else:
                raise
        
        # Override config with CLI API key if provided
        if api_key:
            config.set('google_api.api_key', api_key)
        
        template_mgr = TemplateManager(config)
        templates = template_mgr.list_templates()
        
        if not templates:
            rprint("[yellow]No templates found[/yellow]")
            return
        
        table = Table(title="Available Prompt Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")  
        table.add_column("Description", style="white")
        
        for template in templates:
            table.add_row(
                template['name'],
                template.get('version', '1.0'),
                template.get('description', 'No description')
            )
        
        console.print(table)
        
    except Exception as e:
        rprint(f"[bold red]❌ Error loading templates:[/bold red] {e}")
        sys.exit(1)


@app.command()
def list_models():
    """List all available Gemini models."""
    rprint("[bold cyan]Available Gemini Models[/bold cyan]")
    
    models = [
        {
            "name": "gemini-2.5-pro",
            "description": "Most capable model, best for complex reasoning and analysis",
            "features": ["High accuracy", "Complex reasoning", "Longer context"]
        },
        {
            "name": "gemini-2.5-flash", 
            "description": "Balanced performance and speed, good for most tasks",
            "features": ["Good accuracy", "Fast response", "Balanced cost"]
        },
        {
            "name": "gemini-2.5-flash-lite",
            "description": "Fastest and most cost-effective, good for simple tasks",
            "features": ["Basic accuracy", "Very fast", "Low cost"]
        }
    ]
    
    table = Table(title="Gemini Models")
    table.add_column("Model", style="cyan", width=20)
    table.add_column("Description", style="white", width=40)
    table.add_column("Key Features", style="green", width=30)
    
    for model in models:
        features_str = ", ".join(model["features"])
        table.add_row(model["name"], model["description"], features_str)
    
    console.print(table)
    rprint("\n[yellow]Usage:[/yellow] --model gemini-2.5-flash")


@app.command()
def setup_api(
    config_file: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file"
    )
):
    """Interactive setup wizard for API key configuration."""
    rprint("[bold cyan]🔧 API Key Setup Wizard[/bold cyan]")
    rprint()
    
    # Check current API key status
    import os
    from .config import Config
    
    current_sources = []
    
    # Check environment variables
    env_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or os.environ.get('GEMINI_API_KEY')
    if env_key and env_key not in ['YOUR_GEMINI_API_KEY_HERE', 'DEMO_API_KEY_FOR_TESTING']:
        current_sources.append(f"Environment variable: {env_key[:15]}...")
    
    # Check config file
    try:
        config = Config.from_file(config_file)
        config_key = config.get('google_api.api_key')
        if config_key and config_key not in ['YOUR_GEMINI_API_KEY_HERE', 'DEMO_API_KEY_FOR_TESTING']:
            current_sources.append(f"Config file: {config_key[:15]}...")
    except:
        pass
    
    if current_sources:
        rprint("[green]✅ API key found in:[/green]")
        for source in current_sources:
            rprint(f"   • {source}")
        rprint()
        
        if not typer.confirm("Would you like to update your API key?"):
            rprint("[yellow]Setup cancelled.[/yellow]")
            return
    else:
        rprint("[red]❌ No valid API key found[/red]")
    
    rprint()
    rprint("[yellow]📋 How to get a Google Gemini API key:[/yellow]")
    rprint("   1. Visit: https://makersuite.google.com/app/apikey")
    rprint("   2. Sign in with your Google account")  
    rprint("   3. Click 'Create API key'")
    rprint("   4. Copy the generated key")
    rprint()
    
    api_key = typer.prompt("Enter your Google Gemini API key", hide_input=True)
    
    if not api_key or len(api_key) < 20:
        rprint("[red]❌ Invalid API key format[/red]")
        return
    
    rprint()
    rprint("[yellow]💾 Where would you like to store the API key?[/yellow]")
    rprint("   1. Environment variable (recommended for security)")
    rprint("   2. Configuration file (convenient but less secure)")
    
    choice = typer.prompt("Choose option", type=int, default=1)
    
    if choice == 1:
        rprint()
        rprint("[green]🔐 To set as environment variable, run:[/green]")
        rprint(f'   export GOOGLE_GEMINI_API_KEY="{api_key}"')
        rprint()
        rprint("[yellow]💡 To make it permanent, add this line to your shell profile:[/yellow]")
        rprint("   • For bash: ~/.bashrc or ~/.bash_profile") 
        rprint("   • For zsh: ~/.zshrc")
        rprint("   • For fish: ~/.config/fish/config.fish")
    
    elif choice == 2:
        config_file = Path('config.yaml')
        
        if config_file.exists():
            # Update existing config
            content = config_file.read_text()
            if 'api_key:' in content:
                # Replace existing key
                import re
                content = re.sub(
                    r'api_key:\s*["\']?[^"\'\n]*["\']?',
                    f'api_key: "{api_key}"',
                    content
                )
            else:
                # Add key to google_api section
                content = content.replace(
                    'google_api:',
                    f'google_api:\n  api_key: "{api_key}"'
                )
            config_file.write_text(content)
        else:
            # Create new config file
            config_content = f"""# gs_videoReport Configuration File
google_api:
  api_key: "{api_key}"
  model: "gemini-2.5-flash"
  temperature: 0.7
  max_tokens: 8192

templates:
  default_template: "chinese_transcript"
  template_path: "src/gs_video_report/templates/prompts"

output:
  directory: "./output"
  include_metadata: true

processing:
  verbose: false
  retry_attempts: 3

video:
  max_duration_minutes: 60
  supported_formats: [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"]
"""
            config_file.write_text(config_content)
        
        rprint(f"[green]✅ API key saved to {config_file}[/green]")
    
    rprint()
    rprint("[green]🎉 Setup complete! You can now use gs_videoReport.[/green]")
    rprint("[yellow]Test with:[/yellow] gs_videoreport your_video.mp4 --template chinese_transcript")


@app.command()
def version():
    """Show version information."""
    rprint("[bold cyan]gs_videoReport[/bold cyan]")
    rprint("Version: 0.1.1") 
    rprint("AI-powered video-to-lesson-plan converter")


if __name__ == "__main__":
    app()
