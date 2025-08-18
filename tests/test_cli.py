"""
Tests for CLI functionality.
"""
import pytest
from typer.testing import CliRunner

from src.gs_video_report.cli import app, validate_youtube_url


runner = CliRunner()


class TestYouTubeURLValidation:
    """Test YouTube URL validation functionality."""
    
    def test_valid_youtube_urls(self):
        """Test validation of valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ", 
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "http://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            is_valid, video_id = validate_youtube_url(url)
            assert is_valid, f"URL should be valid: {url}"
            assert video_id == "dQw4w9WgXcQ", f"Video ID should be extracted from: {url}"
    
    def test_invalid_youtube_urls(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            "https://vimeo.com/123456789",
            "https://www.google.com",
            "not-a-url",
            "https://youtube.com/invalid",
            "https://www.youtube.com/watch?v=short",  # Video ID too short
            "https://youtu.be/toolongvideoid123",     # Video ID too long
            ""
        ]
        
        for url in invalid_urls:
            is_valid, video_id = validate_youtube_url(url)
            assert not is_valid, f"URL should be invalid: {url}"
            assert video_id is None, f"Video ID should be None for invalid URL: {url}"


class TestCLICommands:
    """Test CLI command functionality."""
    
    def test_version_command(self):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "gs_videoReport" in result.stdout
        assert "0.1.0-dev" in result.stdout
    
    def test_list_templates_command(self):
        """Test list-templates command."""
        result = runner.invoke(app, ["list-templates"])
        assert result.exit_code == 0
        assert "comprehensive_lesson" in result.stdout
        assert "summary_report" in result.stdout
    
    def test_help_command(self):
        """Test help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "AI-powered video-to-lesson-plan converter" in result.stdout
        assert "main" in result.stdout
        assert "list-templates" in result.stdout
    
    def test_invalid_file_path_error(self):
        """Test error handling for invalid file paths."""
        result = runner.invoke(app, ["main", "nonexistent-file.mp4"])
        assert result.exit_code == 1
        assert "File not found" in result.stdout
    
    def test_youtube_url_mvp_limitation(self):
        """Test that YouTube URLs show MVP limitation message."""
        result = runner.invoke(app, ["main", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
        assert result.exit_code == 1
        assert "YouTube video download not yet implemented in MVP" in result.stdout
        assert "provide the local file path instead" in result.stdout
    
    def test_local_file_processing(self):
        """Test processing with local video file."""
        # Create a temporary test file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = runner.invoke(app, ["main", temp_path])
            assert result.exit_code == 0
            assert "Processing local video file with template" in result.stdout
            assert "not yet implemented" in result.stdout
        finally:
            os.unlink(temp_path)
    
    def test_template_selection(self):
        """Test template selection via CLI."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = runner.invoke(app, [
                "main", 
                temp_path,
                "--template", "summary_report"
            ])
            assert result.exit_code == 0
            assert "template: summary_report" in result.stdout
        finally:
            os.unlink(temp_path)
    
    def test_invalid_template_error(self):
        """Test error handling for invalid template."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = runner.invoke(app, [
                "main",
                temp_path, 
                "--template", "nonexistent_template"
            ])
            assert result.exit_code == 1
            assert "Template 'nonexistent_template' not found" in result.stdout
        finally:
            os.unlink(temp_path)
    
    def test_invalid_file_format(self):
        """Test error handling for unsupported file formats."""
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = runner.invoke(app, ["main", temp_path])
            assert result.exit_code == 1
            assert "Unsupported video format" in result.stdout
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__])
