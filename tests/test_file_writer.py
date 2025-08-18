"""
Test cases for file_writer.py module.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, mock_open

from src.gs_video_report.file_writer import (
    FileWriter, 
    FileWriterResult, 
    FileWriterError, 
    SuccessReporter
)
from src.gs_video_report.config import Config


class TestFileWriterResult:
    """Test cases for FileWriterResult class."""
    
    def test_successful_result_creation(self):
        """Test creating a successful FileWriterResult."""
        result = FileWriterResult(
            success=True,
            file_path="/path/to/file.md",
            file_size=1024
        )
        
        assert result.success is True
        assert result.file_path == "/path/to/file.md"
        assert result.file_size == 1024
        assert result.error_message == ""
        assert isinstance(result.timestamp, datetime)
    
    def test_failed_result_creation(self):
        """Test creating a failed FileWriterResult."""
        result = FileWriterResult(
            success=False,
            error_message="File not found"
        )
        
        assert result.success is False
        assert result.error_message == "File not found"
        assert result.file_path == ""
        assert result.file_size == 0
    
    def test_to_dict_conversion(self):
        """Test converting FileWriterResult to dictionary."""
        result = FileWriterResult(success=True, file_path="/test/file.md", file_size=512)
        result_dict = result.to_dict()
        
        expected_keys = ['success', 'file_path', 'file_size', 'error_message', 'timestamp']
        assert all(key in result_dict for key in expected_keys)
        assert result_dict['success'] is True
        assert result_dict['file_path'] == "/test/file.md"
        assert result_dict['file_size'] == 512


class TestFileWriter:
    """Test cases for FileWriter class."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        config_data = {
            'output': {
                'directory': './test_output',
                'create_backup': True,
                'max_file_size_mb': 10
            }
        }
        return Config(config_data)
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_file_writer_initialization(self, sample_config):
        """Test FileWriter initialization."""
        writer = FileWriter(sample_config)
        
        assert writer.config == sample_config
        assert writer.encoding == 'utf-8'
        assert writer.max_file_size_mb == 10
        assert writer.backup_enabled is True
    
    def test_write_lesson_plan_success(self, sample_config, temp_output_dir):
        """Test successful lesson plan writing."""
        # Update config to use temp directory
        sample_config.data['output']['directory'] = str(temp_output_dir)
        writer = FileWriter(sample_config)
        
        content = """---
title: "Test Lesson"
type: "lesson_plan"
---

# Test Lesson

This is test content.
"""
        
        result = writer.write_lesson_plan(
            content=content,
            filename="test_lesson.md"
        )
        
        assert result.success is True
        assert result.file_size > 0
        assert Path(result.file_path).exists()
        assert "test_lesson.md" in result.file_path
        
        # Verify file content
        written_content = Path(result.file_path).read_text(encoding='utf-8')
        assert written_content == content
    
    def test_write_lesson_plan_empty_content(self, sample_config):
        """Test writing with empty content should fail."""
        writer = FileWriter(sample_config)
        
        result = writer.write_lesson_plan(content="", filename="empty.md")
        
        assert result.success is False
        assert "Content is empty" in result.error_message
    
    def test_write_lesson_plan_content_too_large(self, sample_config):
        """Test writing with content exceeding size limit."""
        writer = FileWriter(sample_config)
        
        # Create content larger than max_file_size_mb (10MB)
        large_content = "A" * (11 * 1024 * 1024)  # 11MB
        
        result = writer.write_lesson_plan(content=large_content, filename="large.md")
        
        assert result.success is False
        assert "exceeds maximum allowed size" in result.error_message
    
    def test_determine_file_path_variants(self, sample_config, temp_output_dir):
        """Test different ways of determining file path."""
        sample_config.data['output']['directory'] = str(temp_output_dir)
        writer = FileWriter(sample_config)
        
        # Test with full file_path
        full_path = temp_output_dir / "specific_path.md"
        result_path = writer._determine_file_path(str(full_path), None)
        assert result_path == full_path
        
        # Test with filename only
        result_path = writer._determine_file_path(None, "test_file.md")
        assert result_path == temp_output_dir / "test_file.md"
        
        # Test with neither (should generate default)
        result_path = writer._determine_file_path(None, None)
        assert result_path.parent == temp_output_dir
        assert result_path.name.startswith("lesson_plan_")
        assert result_path.suffix == ".md"
    
    def test_backup_creation(self, sample_config, temp_output_dir):
        """Test backup file creation."""
        sample_config.data['output']['directory'] = str(temp_output_dir)
        writer = FileWriter(sample_config)
        
        # Create existing file
        existing_file = temp_output_dir / "existing.md"
        existing_file.write_text("Original content")
        
        # Create backup
        backup_path = writer._create_backup(existing_file)
        
        assert backup_path.exists()
        assert "backup_" in backup_path.name
        assert backup_path.read_text() == "Original content"
    
    def test_unique_filename_generation(self, sample_config, temp_output_dir):
        """Test unique filename generation when file exists."""
        sample_config.data['output']['directory'] = str(temp_output_dir)
        writer = FileWriter(sample_config)
        
        # Create existing file
        original_file = temp_output_dir / "test.md"
        original_file.write_text("Existing content")
        
        # Generate unique filename
        unique_path = writer._generate_unique_filename(original_file)
        
        assert unique_path != original_file
        assert "test_1.md" in str(unique_path)
        assert not unique_path.exists()
    
    def test_create_output_directory(self, sample_config, temp_output_dir):
        """Test output directory creation."""
        writer = FileWriter(sample_config)
        
        # Test creating nested directory
        nested_dir = temp_output_dir / "nested" / "deep" / "structure"
        result_dir = writer.create_output_directory(str(nested_dir))
        
        assert result_dir.exists()
        assert result_dir.is_dir()
        assert result_dir == nested_dir
    
    def test_create_output_directory_default(self, sample_config, temp_output_dir):
        """Test creating default output directory."""
        sample_config.data['output']['directory'] = str(temp_output_dir / "default")
        writer = FileWriter(sample_config)
        
        result_dir = writer.create_output_directory()
        
        assert result_dir.exists()
        assert result_dir == temp_output_dir / "default"
    
    def test_get_file_info_existing(self, sample_config, temp_output_dir):
        """Test getting file information for existing file."""
        writer = FileWriter(sample_config)
        
        # Create test file
        test_file = temp_output_dir / "info_test.md"
        test_content = "This is test content for file info"
        test_file.write_text(test_content)
        
        file_info = writer.get_file_info(str(test_file))
        
        assert file_info['exists'] is True
        assert file_info['size'] == len(test_content.encode('utf-8'))
        assert 'created' in file_info
        assert 'modified' in file_info
        assert file_info['is_readable'] is True
        assert file_info['is_writable'] is True
    
    def test_get_file_info_nonexistent(self, sample_config):
        """Test getting file information for non-existent file."""
        writer = FileWriter(sample_config)
        
        file_info = writer.get_file_info("/nonexistent/file.md")
        
        assert file_info['exists'] is False
    
    @patch('os.system')
    def test_open_file_location_macos(self, mock_system, sample_config, temp_output_dir):
        """Test opening file location on macOS."""
        writer = FileWriter(sample_config)
        
        # Create test file
        test_file = temp_output_dir / "open_test.md"
        test_file.write_text("Test content")
        
        with patch('platform.system', return_value='Darwin'):
            result = writer.open_file_location(str(test_file))
        
        assert result is True
        mock_system.assert_called_once()
        assert 'open' in mock_system.call_args[0][0]
    
    @patch('os.system')
    def test_open_file_location_windows(self, mock_system, sample_config, temp_output_dir):
        """Test opening file location on Windows."""
        writer = FileWriter(sample_config)
        
        test_file = temp_output_dir / "open_test.md"
        test_file.write_text("Test content")
        
        with patch('platform.system', return_value='Windows'):
            result = writer.open_file_location(str(test_file))
        
        assert result is True
        mock_system.assert_called_once()
        assert 'explorer' in mock_system.call_args[0][0]
    
    @patch('os.system')
    def test_open_file_location_linux(self, mock_system, sample_config, temp_output_dir):
        """Test opening file location on Linux."""
        writer = FileWriter(sample_config)
        
        test_file = temp_output_dir / "open_test.md"
        test_file.write_text("Test content")
        
        with patch('platform.system', return_value='Linux'):
            result = writer.open_file_location(str(test_file))
        
        assert result is True
        mock_system.assert_called_once()
        assert 'xdg-open' in mock_system.call_args[0][0]
    
    def test_open_file_location_nonexistent(self, sample_config):
        """Test opening file location for non-existent file."""
        writer = FileWriter(sample_config)
        
        result = writer.open_file_location("/nonexistent/file.md")
        
        assert result is False
    
    def test_cleanup_old_files_dry_run(self, sample_config, temp_output_dir):
        """Test cleanup old files in dry run mode."""
        sample_config.data['output']['directory'] = str(temp_output_dir)
        writer = FileWriter(sample_config)
        
        # Create old and new files
        old_file = temp_output_dir / "old_lesson.md"
        new_file = temp_output_dir / "new_lesson.md"
        
        old_file.write_text("Old content")
        new_file.write_text("New content")
        
        # Manually set old file modification time (simulate old file)
        import os
        old_time = datetime.now().timestamp() - (35 * 24 * 3600)  # 35 days ago
        os.utime(old_file, (old_time, old_time))
        
        result = writer.cleanup_old_files(directory=str(temp_output_dir), days_old=30, dry_run=True)
        
        assert result['found'] >= 1
        assert result['removed'] == 0
        assert result['dry_run'] is True
        assert len(result['files']) >= 1
        
        # Files should still exist
        assert old_file.exists()
        assert new_file.exists()
    
    def test_cleanup_old_files_actual_cleanup(self, sample_config, temp_output_dir):
        """Test actual cleanup of old files."""
        sample_config.data['output']['directory'] = str(temp_output_dir)
        writer = FileWriter(sample_config)
        
        # Create old file
        old_file = temp_output_dir / "old_lesson.md"
        old_file.write_text("Old content")
        
        # Manually set old file modification time
        import os
        old_time = datetime.now().timestamp() - (35 * 24 * 3600)  # 35 days ago
        os.utime(old_file, (old_time, old_time))
        
        result = writer.cleanup_old_files(directory=str(temp_output_dir), days_old=30, dry_run=False)
        
        assert result['found'] >= 1
        assert result['removed'] >= 1
        assert result['dry_run'] is False
        
        # Old file should be removed
        assert not old_file.exists()
    
    def test_validate_content_yaml_frontmatter(self, sample_config):
        """Test content validation with YAML frontmatter."""
        writer = FileWriter(sample_config)
        
        # Valid YAML frontmatter
        valid_content = """---
title: "Test"
type: "lesson_plan"
---

# Content"""
        
        # Should not raise exception
        writer._validate_content(valid_content)
        
        # Invalid YAML frontmatter (missing closing ---)
        invalid_content = """---
title: "Test"
type: "lesson_plan"

# Content"""
        
        # Should log warning but not raise exception
        writer._validate_content(invalid_content)


class TestSuccessReporter:
    """Test cases for SuccessReporter utility class."""
    
    def test_format_success_message_successful(self):
        """Test formatting success message for successful operation."""
        result = FileWriterResult(
            success=True,
            file_path="/path/to/lesson.md",
            file_size=2048
        )
        
        message = SuccessReporter.format_success_message(result)
        
        assert "✅ Lesson plan successfully saved!" in message
        assert "/path/to/lesson.md" in message
        assert "2048 bytes" in message
        assert "MB)" in message
    
    def test_format_success_message_failed(self):
        """Test formatting success message for failed operation."""
        result = FileWriterResult(
            success=False,
            error_message="File permission denied"
        )
        
        message = SuccessReporter.format_success_message(result)
        
        assert "❌ Failed to save lesson plan" in message
        assert "File permission denied" in message
    
    def test_format_file_info_existing(self):
        """Test formatting file info for existing file."""
        file_info = {
            'exists': True,
            'size_mb': 1.5,
            'created': '2024-01-27T10:00:00',
            'modified': '2024-01-27T11:00:00',
            'is_readable': True,
            'is_writable': True,
            'absolute_path': '/absolute/path/to/file.md'
        }
        
        info_message = SuccessReporter.format_file_info(file_info)
        
        assert "📄 File Information:" in info_message
        assert "1.5 MB" in info_message
        assert "2024-01-27T10:00:00" in info_message
        assert "✅" in info_message  # For readable/writable checkmarks
        assert "/absolute/path/to/file.md" in info_message
    
    def test_format_file_info_nonexistent(self):
        """Test formatting file info for non-existent file."""
        file_info = {'exists': False}
        
        info_message = SuccessReporter.format_file_info(file_info)
        
        assert "❌ File does not exist" in info_message


class TestIntegration:
    """Integration tests for file writer workflow."""
    
    def test_end_to_end_file_writing_workflow(self, tmp_path):
        """Test complete file writing workflow."""
        # Setup
        config_data = {
            'output': {
                'directory': str(tmp_path),
                'create_backup': True,
                'max_file_size_mb': 10
            }
        }
        config = Config(config_data)
        writer = FileWriter(config)
        
        lesson_content = """---
title: "Integration Test Lesson"
author: "Test Author"
type: "lesson_plan"
tags: ["integration", "test"]
---

# Integration Test Lesson

## Overview
This is a complete integration test of the file writing system.

## Content Sections

### Section 1
Content for section 1 with some text.

### Section 2
Content for section 2 with more text.

## Conclusion
Test completed successfully.
"""
        
        # Write the file
        result = writer.write_lesson_plan(
            content=lesson_content,
            filename="integration_test_lesson.md"
        )
        
        # Verify successful write
        assert result.success is True
        assert result.file_size > 0
        
        # Verify file exists and content is correct
        file_path = Path(result.file_path)
        assert file_path.exists()
        
        written_content = file_path.read_text(encoding='utf-8')
        assert written_content == lesson_content
        
        # Test file info retrieval
        file_info = writer.get_file_info(result.file_path)
        assert file_info['exists'] is True
        assert file_info['size'] == result.file_size
        
        # Test success message formatting
        success_message = SuccessReporter.format_success_message(result)
        assert "✅ Lesson plan successfully saved!" in success_message
        
        # Test file info formatting
        info_message = SuccessReporter.format_file_info(file_info)
        assert "📄 File Information:" in info_message
    
    def test_overwrite_and_backup_workflow(self, tmp_path):
        """Test overwrite prevention and backup creation."""
        config_data = {
            'output': {
                'directory': str(tmp_path),
                'create_backup': True
            }
        }
        config = Config(config_data)
        writer = FileWriter(config)
        
        # Create original file
        original_content = "Original lesson content"
        first_result = writer.write_lesson_plan(
            content=original_content,
            filename="overwrite_test.md"
        )
        
        assert first_result.success is True
        original_file = Path(first_result.file_path)
        
        # Write again (should create backup and use unique filename)
        new_content = "Updated lesson content"
        second_result = writer.write_lesson_plan(
            content=new_content,
            filename="overwrite_test.md",
            overwrite=False
        )
        
        assert second_result.success is True
        
        # Original file should still exist with original content
        assert original_file.exists()
        assert original_file.read_text() == original_content
        
        # New file should have different name with new content
        new_file = Path(second_result.file_path)
        assert new_file != original_file
        assert new_file.read_text() == new_content
        
        # Should have created a backup
        backup_files = list(tmp_path.glob("*backup*"))
        assert len(backup_files) >= 1
