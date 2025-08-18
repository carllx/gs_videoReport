"""
Tests for Gemini service functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from src.gs_video_report.services.gemini_service import GeminiService, GeminiAnalysisResult
from src.gs_video_report.template_manager import TemplateManager


class TestGeminiAnalysisResult:
    """Test GeminiAnalysisResult functionality."""
    
    def test_result_initialization(self):
        """Test result object initialization."""
        content = "Test analysis content"
        metadata = {"model": "gemini-2.5-flash", "template": "test"}
        
        result = GeminiAnalysisResult(content, metadata)
        
        assert result.content == content
        assert result.metadata == metadata
        assert result.timestamp > 0
        assert result.word_count == 3  # "Test", "analysis", "content"
    
    def test_word_count_calculation(self):
        """Test word count calculation."""
        result = GeminiAnalysisResult("Hello world test", {})
        assert result.word_count == 3
        
        result_empty = GeminiAnalysisResult("", {})
        assert result_empty.word_count == 0
        
        result_none = GeminiAnalysisResult(None, {})
        assert result_none.word_count == 0
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        content = "Test content"
        metadata = {"test": "data"}
        
        result = GeminiAnalysisResult(content, metadata)
        result_dict = result.to_dict()
        
        assert result_dict['content'] == content
        assert result_dict['metadata'] == metadata
        assert 'timestamp' in result_dict
        assert 'word_count' in result_dict


class TestGeminiService:
    """Test GeminiService functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'google_api': {
                'api_key': 'test_api_key',
                'model': 'gemini-2.5-flash',
                'max_file_size_mb': 100,
                'processing_timeout_seconds': 300
            },
            'templates': {
                'default_template': 'test_template'
            }
        }
    
    def test_service_initialization_success(self, mock_config):
        """Test successful service initialization."""
        with patch('src.gs_video_report.services.gemini_service.genai.Client') as mock_client:
            service = GeminiService(mock_config)
            
            assert service.config == mock_config
            mock_client.assert_called_once_with(api_key='test_api_key')
    
    def test_service_initialization_no_api_key(self, mock_config):
        """Test initialization failure with missing API key."""
        mock_config['google_api']['api_key'] = ''
        
        with pytest.raises(ValueError, match="Google API key not configured"):
            GeminiService(mock_config)
    
    def test_validate_video_file_success(self, mock_config):
        """Test successful video file validation."""
        with patch('src.gs_video_report.services.gemini_service.genai.Client'):
            service = GeminiService(mock_config)
        
        # Create a temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b'fake video content')
        
        try:
            is_valid, error_msg = service.validate_video_file(temp_path)
            assert is_valid
            assert error_msg is None
        finally:
            os.unlink(temp_path)
    
    def test_validate_video_file_not_found(self, mock_config):
        """Test video file validation with non-existent file."""
        with patch('src.gs_video_report.services.gemini_service.genai.Client'):
            service = GeminiService(mock_config)
        
        is_valid, error_msg = service.validate_video_file('/nonexistent/file.mp4')
        assert not is_valid
        assert "not found" in error_msg
    
    def test_validate_video_file_unsupported_format(self, mock_config):
        """Test video file validation with unsupported format."""
        with patch('src.gs_video_report.services.gemini_service.genai.Client'):
            service = GeminiService(mock_config)
        
        # Create temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            is_valid, error_msg = service.validate_video_file(temp_path)
            assert not is_valid
            assert "Unsupported video format" in error_msg
        finally:
            os.unlink(temp_path)
    
    def test_validate_video_file_too_large(self, mock_config):
        """Test video file validation with file too large."""
        mock_config['google_api']['max_file_size_mb'] = 0.001  # 1KB limit
        
        with patch('src.gs_video_report.services.gemini_service.genai.Client'):
            service = GeminiService(mock_config)
        
        # Create temporary file larger than limit
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(b'x' * 2048)  # 2KB file
            temp_path = temp_file.name
        
        try:
            is_valid, error_msg = service.validate_video_file(temp_path)
            assert not is_valid
            assert "too large" in error_msg
        finally:
            os.unlink(temp_path)
    
    @patch('src.gs_video_report.services.gemini_service.genai.Client')
    def test_upload_video_file_success(self, mock_client_class, mock_config):
        """Test successful video file upload."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_uploaded_file = Mock()
        mock_uploaded_file.name = 'test_file_id'
        mock_uploaded_file.size_bytes = 1024
        mock_client.files.upload.return_value = mock_uploaded_file
        
        service = GeminiService(mock_config)
        
        # Create temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(b'fake video content')
        
        try:
            result = service.upload_video_file(temp_path, "test_video")
            
            assert result == mock_uploaded_file
            mock_client.files.upload.assert_called_once()
        finally:
            os.unlink(temp_path)
    
    @patch('src.gs_video_report.services.gemini_service.genai.Client')
    def test_get_client_info(self, mock_client_class, mock_config):
        """Test client info retrieval."""
        mock_client_class.return_value = Mock()
        
        service = GeminiService(mock_config)
        info = service.get_client_info()
        
        assert info['client_initialized'] is True
        assert info['api_configured'] is True
        assert info['max_file_size_mb'] == 100
        assert info['default_model'] == 'gemini-2.5-flash'
    
    def test_mime_type_detection(self, mock_config):
        """Test MIME type detection for different video formats."""
        with patch('src.gs_video_report.services.gemini_service.genai.Client'):
            service = GeminiService(mock_config)
        
        # Test various formats
        assert service._get_mime_type('.mp4') == 'video/mp4'
        assert service._get_mime_type('.mov') == 'video/quicktime'
        assert service._get_mime_type('.avi') == 'video/x-msvideo'
        assert service._get_mime_type('.mkv') == 'video/x-matroska'
        assert service._get_mime_type('.webm') == 'video/webm'
        assert service._get_mime_type('.m4v') == 'video/x-m4v'
        assert service._get_mime_type('.unknown') == 'video/mp4'  # Default


if __name__ == "__main__":
    pytest.main([__file__])
