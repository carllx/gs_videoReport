"""
Test cases for lesson_formatter.py module.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.gs_video_report.lesson_formatter import (
    TimestampFormatter, 
    LessonPlanData, 
    LessonFormatter
)
from src.gs_video_report.config import Config


class TestTimestampFormatter:
    """Test cases for TimestampFormatter utility class."""
    
    def test_seconds_to_display_format(self):
        """Test timestamp display formatting."""
        # Test minutes and seconds
        assert TimestampFormatter.seconds_to_display(125) == "02:05"
        assert TimestampFormatter.seconds_to_display(59) == "00:59"
        assert TimestampFormatter.seconds_to_display(0) == "00:00"
        
        # Test hours, minutes and seconds
        assert TimestampFormatter.seconds_to_display(3661) == "01:01:01"
        assert TimestampFormatter.seconds_to_display(7200) == "02:00:00"
        assert TimestampFormatter.seconds_to_display(86400) == "24:00:00"
    
    def test_create_youtube_timestamp_url(self):
        """Test YouTube timestamp URL creation."""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        expected = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s"
        
        result = TimestampFormatter.create_youtube_timestamp_url(video_url, 120)
        assert result == expected
        
        # Test with youtu.be format
        short_url = "https://youtu.be/dQw4w9WgXcQ"
        result = TimestampFormatter.create_youtube_timestamp_url(short_url, 60)
        assert result == "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=60s"
    
    def test_extract_video_id(self):
        """Test video ID extraction from various URL formats."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("invalid-url", None),
            ("", None)
        ]
        
        for url, expected in test_cases:
            result = TimestampFormatter._extract_video_id(url)
            assert result == expected


class TestLessonPlanData:
    """Test cases for LessonPlanData class."""
    
    @pytest.fixture
    def sample_gemini_result(self):
        """Sample Gemini API result for testing."""
        return {
            'title': 'Python Programming Basics',
            'author': 'Tech Teacher',
            'duration': '45:30',
            'summary': 'Introduction to Python programming concepts',
            'learning_objectives': 'Learn variables, loops, and functions',
            'content_sections': [
                {
                    'title': 'Variables and Data Types',
                    'content': 'Variables store data values...',
                    'timestamp_seconds': 120,
                    'key_points': ['Variables', 'Data types', 'Assignment']
                },
                {
                    'title': 'Control Structures',
                    'content': 'If statements and loops...',
                    'timestamp_seconds': 300
                }
            ],
            'important_timestamps': [
                {'seconds': 120, 'description': 'Variables introduction'},
                {'seconds': 300, 'description': 'Loop examples'}
            ],
            'suggested_activities': 'Practice coding exercises',
            'related_resources': 'Python documentation'
        }
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        config_data = {
            'output': {
                'directory': './test_output',
                'template_directory': 'templates/outputs'
            }
        }
        return Config(config_data)
    
    def test_lesson_plan_data_initialization(self, sample_gemini_result, sample_config):
        """Test LessonPlanData initialization."""
        video_url = "https://www.youtube.com/watch?v=test123"
        
        lesson_data = LessonPlanData(sample_gemini_result, video_url, sample_config)
        
        assert lesson_data.video_title == 'Python Programming Basics'
        assert lesson_data.video_author == 'Tech Teacher'
        assert lesson_data.video_duration == '45:30'
        assert lesson_data.video_url == video_url
        assert isinstance(lesson_data.creation_date, str)
    
    def test_process_content_sections(self, sample_gemini_result, sample_config):
        """Test content sections processing with timestamps."""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Valid 11-char video ID
        lesson_data = LessonPlanData(sample_gemini_result, video_url, sample_config)
        
        sections = lesson_data.content_sections
        assert len(sections) == 2
        
        # First section with timestamp
        assert sections[0]['title'] == 'Variables and Data Types'
        assert sections[0]['timestamp_display'] == '02:00'
        assert 'dQw4w9WgXcQ&t=120s' in sections[0]['timestamp_url']
        assert sections[0]['key_points'] == ['Variables', 'Data types', 'Assignment']
        
        # Second section with timestamp
        assert sections[1]['title'] == 'Control Structures'
        assert sections[1]['timestamp_display'] == '05:00'
        assert 'dQw4w9WgXcQ&t=300s' in sections[1]['timestamp_url']
    
    def test_extract_important_timestamps(self, sample_gemini_result, sample_config):
        """Test important timestamps extraction."""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Valid 11-char video ID
        lesson_data = LessonPlanData(sample_gemini_result, video_url, sample_config)
        
        timestamps = lesson_data.important_timestamps
        assert len(timestamps) == 2
        
        assert timestamps[0]['time_display'] == '02:00'
        assert timestamps[0]['description'] == 'Variables introduction'
        assert 'dQw4w9WgXcQ&t=120s' in timestamps[0]['url']
    
    def test_generate_frontmatter(self, sample_gemini_result, sample_config):
        """Test YAML frontmatter generation."""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Valid 11-char video ID
        lesson_data = LessonPlanData(sample_gemini_result, video_url, sample_config)
        
        frontmatter = lesson_data.generate_frontmatter("test_template", "2.0")
        
        assert frontmatter['title'] == 'Python Programming Basics'
        assert frontmatter['author'] == 'Tech Teacher'
        assert frontmatter['template_used'] == 'test_template'
        assert frontmatter['template_version'] == '2.0'
        assert frontmatter['type'] == 'lesson_plan'
        assert 'lesson_plan' in frontmatter['tags']
        assert 'video_analysis' in frontmatter['tags']
    
    def test_generate_tags(self, sample_gemini_result, sample_config):
        """Test tag generation for metadata."""
        # Add subject to gemini result
        sample_gemini_result['subject'] = 'Computer Science'
        sample_gemini_result['tags'] = ['programming', 'python']
        
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Valid 11-char video ID
        lesson_data = LessonPlanData(sample_gemini_result, video_url, sample_config)
        
        tags = lesson_data._generate_tags()
        
        assert 'lesson_plan' in tags
        assert 'video_analysis' in tags
        assert 'programming' in tags
        assert 'python' in tags
        assert 'computer_science' in tags  # Subject converted to tag format


class TestLessonFormatter:
    """Test cases for LessonFormatter class."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        config_data = {
            'output': {
                'directory': './test_output',
                'template_directory': 'src/gs_video_report/templates/outputs'
            },
            'google_api': {
                'model': 'gemini-2.5-flash'
            }
        }
        return Config(config_data)
    
    @pytest.fixture
    def sample_gemini_result(self):
        """Sample Gemini result for testing."""
        return {
            'title': 'Test Video',
            'author': 'Test Author',
            'duration': '10:00',
            'summary': 'Test video summary',
            'learning_objectives': 'Test objectives',
            'content_sections': [
                {
                    'title': 'Test Section',
                    'content': 'Test content',
                    'timestamp_seconds': 60,
                    'key_points': ['Point 1', 'Point 2']
                }
            ],
            'important_timestamps': [],
            'suggested_activities': 'Test activities',
            'related_resources': 'Test resources'
        }
    
    @pytest.fixture
    def temp_template_dir(self):
        """Create temporary template directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            # Create basic template file
            template_content = """---
title: "{{ video_title }}"
author: "{{ video_author }}"
---

# {{ lesson_title }}

## Content
{{ content_summary }}

{% for section in content_sections %}
### {{ section.title }}
{{ section.content }}
{% endfor %}
"""
            template_file = template_dir / "basic_lesson_plan.md"
            template_file.write_text(template_content)
            
            yield template_dir
    
    def test_lesson_formatter_initialization(self, sample_config):
        """Test LessonFormatter initialization."""
        formatter = LessonFormatter(sample_config)
        assert formatter.config == sample_config
    
    @patch('src.gs_video_report.lesson_formatter.Environment')
    def test_format_lesson_plan_success(self, mock_env, sample_config, sample_gemini_result):
        """Test successful lesson plan formatting."""
        # Mock Jinja2 template
        mock_template = Mock()
        mock_template.render.return_value = "# Formatted Lesson Plan\n\nTest content"
        
        mock_jinja_env = Mock()
        mock_jinja_env.get_template.return_value = mock_template
        mock_env.return_value = mock_jinja_env
        
        formatter = LessonFormatter(sample_config)
        formatter.jinja_env = mock_jinja_env
        
        result = formatter.format_lesson_plan(
            sample_gemini_result,
            video_url="test_video.mp4",
            template_name="basic_lesson_plan"
        )
        
        # Verify result contains YAML frontmatter and content
        assert result.startswith('---\n')
        assert '# Formatted Lesson Plan' in result
        assert 'title: Test Video' in result
    
    def test_format_lesson_plan_fallback(self, sample_config, sample_gemini_result):
        """Test fallback lesson plan creation when template loading fails."""
        formatter = LessonFormatter(sample_config)
        
        # Mock template loading to fail
        with patch.object(formatter, '_load_template', return_value=None):
            result = formatter.format_lesson_plan(
                sample_gemini_result,
                video_url="test_video.mp4"
            )
        
        # Verify fallback content
        assert result.startswith('---\n')
        assert '# Test Video' in result
        assert 'Test video summary' in result
    
    def test_prepare_template_variables(self, sample_config, sample_gemini_result):
        """Test template variable preparation."""
        formatter = LessonFormatter(sample_config)
        lesson_data = LessonPlanData(sample_gemini_result, "test_video.mp4", sample_config)
        
        variables = formatter._prepare_template_variables(lesson_data, "test_template")
        
        assert variables['video_title'] == 'Test Video'
        assert variables['template_name'] == 'test_template'
        assert variables['template_version'] == '1.0'
        assert variables['api_model'] == 'gemini-2.5-flash'
        assert 'generation_timestamp' in variables
    
    @patch('src.gs_video_report.lesson_formatter.datetime')
    def test_generate_filename(self, mock_datetime, sample_config, sample_gemini_result):
        """Test filename generation."""
        # Mock datetime
        mock_datetime.now.return_value.strftime.return_value = "20240127_1430"
        
        formatter = LessonFormatter(sample_config)
        lesson_data = LessonPlanData(sample_gemini_result, "test_video.mp4", sample_config)
        
        filename = formatter.generate_filename(lesson_data)
        
        assert filename.endswith("_lesson_plan.md")
        assert "Test_Video" in filename
        assert "20240127_1430" in filename
    
    def test_generate_filename_with_custom_output_dir(self, sample_config, sample_gemini_result):
        """Test filename generation with custom output directory."""
        formatter = LessonFormatter(sample_config)
        lesson_data = LessonPlanData(sample_gemini_result, "test_video.mp4", sample_config)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = formatter.generate_filename(lesson_data, output_dir=temp_dir)
            assert temp_dir in filename


class TestIntegration:
    """Integration tests for lesson formatting workflow."""
    
    def test_end_to_end_lesson_creation(self):
        """Test complete lesson plan creation workflow."""
        # Sample data
        config_data = {
            'output': {'directory': './test_output'},
            'google_api': {'model': 'gemini-2.5-flash'}
        }
        config = Config(config_data)
        
        gemini_result = {
            'title': 'Integration Test Video',
            'author': 'Test Author',
            'duration': '15:00',
            'summary': 'This is an integration test',
            'learning_objectives': 'Test the complete workflow',
            'content_sections': [
                {
                    'title': 'Introduction',
                    'content': 'This is the introduction section',
                    'timestamp_seconds': 0,
                    'key_points': ['Welcome', 'Overview']
                }
            ],
            'important_timestamps': [],
            'suggested_activities': 'Complete the integration test',
            'related_resources': 'Test documentation'
        }
        
        # Create lesson formatter
        formatter = LessonFormatter(config)
        
        # Format lesson plan (should use fallback template)
        result = formatter.format_lesson_plan(
            gemini_result,
            video_url="https://example.com/test_video",
            template_name="nonexistent_template"  # Force fallback
        )
        
        # Verify structure
        assert result.startswith('---\n')
        lines = result.split('\n')
        yaml_end = lines.index('---', 1)
        
        # Parse YAML frontmatter
        yaml_content = '\n'.join(lines[1:yaml_end])
        frontmatter = yaml.safe_load(yaml_content)
        
        assert frontmatter['title'] == 'Integration Test Video'
        assert frontmatter['type'] == 'lesson_plan'
        assert 'lesson_plan' in frontmatter['tags']
        
        # Verify content structure
        content = '\n'.join(lines[yaml_end + 1:])
        assert '# Integration Test Video' in content
        assert 'This is an integration test' in content
        assert '### Introduction' in content
