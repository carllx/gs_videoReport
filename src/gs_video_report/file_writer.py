"""
File writer module for managing lesson plan file output and storage.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .config import Config


logger = logging.getLogger(__name__)


class FileWriterError(Exception):
    """Custom exception for file writing errors."""
    pass


class FileWriterResult:
    """Result object for file writing operations."""
    
    def __init__(self, success: bool, file_path: str = "", 
                 file_size: int = 0, error_message: str = ""):
        self.success = success
        self.file_path = file_path
        self.file_size = file_size
        self.error_message = error_message
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'success': self.success,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat()
        }


class FileWriter:
    """File writer class for handling lesson plan file operations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.default_output_dir = Path(
            config.data.get('output', {}).get('directory', './output')
        )
        
        # File operation settings
        self.encoding = 'utf-8'
        self.max_file_size_mb = config.data.get('output', {}).get('max_file_size_mb', 50)
        self.backup_enabled = config.data.get('output', {}).get('create_backup', True)
        
    def write_lesson_plan(self, content: str, file_path: Optional[str] = None, 
                         filename: Optional[str] = None, 
                         overwrite: bool = False) -> FileWriterResult:
        """
        Write lesson plan content to a file.
        
        Args:
            content: The lesson plan content to write
            file_path: Full path to the output file (optional)
            filename: Just the filename (optional, uses default directory)
            overwrite: Whether to overwrite existing files
            
        Returns:
            FileWriterResult object with operation details
        """
        try:
            # Determine the final file path
            final_path = self._determine_file_path(file_path, filename)
            logger.info(f"Writing lesson plan to: {final_path}")
            
            # Validate content
            self._validate_content(content)
            
            # Check if file exists and handle accordingly
            if final_path.exists() and not overwrite:
                if self._should_create_backup(final_path):
                    backup_path = self._create_backup(final_path)
                    logger.info(f"Created backup: {backup_path}")
                
                # Always generate new filename when not overwriting
                final_path = self._generate_unique_filename(final_path)
                logger.info(f"Generated unique filename: {final_path}")
            
            # Ensure parent directory exists
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(final_path, 'w', encoding=self.encoding) as f:
                f.write(content)
            
            # Get file statistics
            file_size = final_path.stat().st_size
            
            logger.info(f"Successfully wrote {file_size} bytes to {final_path}")
            
            return FileWriterResult(
                success=True,
                file_path=str(final_path),
                file_size=file_size
            )
            
        except Exception as e:
            error_msg = f"Failed to write lesson plan: {e}"
            logger.error(error_msg)
            return FileWriterResult(
                success=False,
                error_message=error_msg
            )
    
    def _determine_file_path(self, file_path: Optional[str], 
                           filename: Optional[str]) -> Path:
        """Determine the final file path for writing."""
        if file_path:
            return Path(file_path)
        elif filename:
            return self.default_output_dir / filename
        else:
            # Generate default filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f"lesson_plan_{timestamp}.md"
            return self.default_output_dir / default_filename
    
    def _validate_content(self, content: str) -> None:
        """Validate the content before writing."""
        if not content or not content.strip():
            raise FileWriterError("Content is empty")
        
        # Check content size
        content_size_mb = len(content.encode(self.encoding)) / (1024 * 1024)
        if content_size_mb > self.max_file_size_mb:
            raise FileWriterError(
                f"Content size ({content_size_mb:.2f} MB) exceeds maximum "
                f"allowed size ({self.max_file_size_mb} MB)"
            )
        
        # Basic validation for YAML frontmatter
        if content.startswith('---'):
            lines = content.split('\n')
            frontmatter_end = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    frontmatter_end = i
                    break
            
            if frontmatter_end == -1:
                logger.warning("YAML frontmatter appears malformed")
    
    def _should_create_backup(self, file_path: Path) -> bool:
        """Check if backup should be created for existing file."""
        return (
            self.backup_enabled and 
            file_path.exists() and 
            file_path.stat().st_size > 0
        )
    
    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of existing file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        backup_path = file_path.parent / backup_name
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _generate_unique_filename(self, file_path: Path) -> Path:
        """Generate a unique filename by adding a counter."""
        base_path = file_path.parent / file_path.stem
        suffix = file_path.suffix
        counter = 1
        
        while True:
            new_path = Path(f"{base_path}_{counter}{suffix}")
            if not new_path.exists():
                return new_path
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 1000:
                raise FileWriterError("Unable to generate unique filename")
    
    def create_output_directory(self, directory_path: Optional[str] = None) -> Path:
        """
        Create output directory if it doesn't exist.
        
        Args:
            directory_path: Optional custom directory path
            
        Returns:
            Path object for the created directory
        """
        if directory_path:
            output_dir = Path(directory_path)
        else:
            output_dir = self.default_output_dir
        
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory ready: {output_dir}")
            return output_dir
        except Exception as e:
            logger.error(f"Failed to create output directory {output_dir}: {e}")
            raise FileWriterError(f"Cannot create output directory: {e}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {'exists': False}
            
            stat = path.stat()
            return {
                'exists': True,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'is_readable': os.access(path, os.R_OK),
                'is_writable': os.access(path, os.W_OK),
                'absolute_path': str(path.absolute())
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {'exists': False, 'error': str(e)}
    
    def open_file_location(self, file_path: str) -> bool:
        """
        Open the directory containing the file in the system file manager.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            directory = path.parent
            
            # Platform-specific file manager opening
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                os.system(f'open "{directory}"')
            elif system == "Windows":
                os.system(f'explorer "{directory}"')
            else:  # Linux and others
                os.system(f'xdg-open "{directory}"')
            
            logger.info(f"Opened file location: {directory}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open file location: {e}")
            return False
    
    def cleanup_old_files(self, directory: Optional[str] = None, 
                         days_old: int = 30, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up old lesson plan files.
        
        Args:
            directory: Directory to clean (default: output directory)
            days_old: Remove files older than this many days
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            if directory:
                clean_dir = Path(directory)
            else:
                clean_dir = self.default_output_dir
            
            if not clean_dir.exists():
                return {'error': 'Directory does not exist'}
            
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            files_to_remove = []
            total_size = 0
            
            # Find old files
            for file_path in clean_dir.glob('*.md'):
                if file_path.stat().st_mtime < cutoff_time:
                    size = file_path.stat().st_size
                    files_to_remove.append({
                        'path': str(file_path),
                        'size': size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                    })
                    total_size += size
            
            # Remove files if not dry run
            removed_count = 0
            if not dry_run:
                for file_info in files_to_remove:
                    try:
                        Path(file_info['path']).unlink()
                        removed_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_info['path']}: {e}")
            
            return {
                'found': len(files_to_remove),
                'removed': removed_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'dry_run': dry_run,
                'files': files_to_remove if dry_run else []
            }
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {'error': str(e)}


class SuccessReporter:
    """Utility class for reporting successful file operations to the user."""
    
    @staticmethod
    def format_success_message(result: FileWriterResult) -> str:
        """Format a user-friendly success message."""
        if not result.success:
            return f"❌ Failed to save lesson plan: {result.error_message}"
        
        file_size_mb = round(result.file_size / (1024 * 1024), 3)
        
        message = f"✅ Lesson plan successfully saved!\n"
        message += f"📁 File: {result.file_path}\n"
        message += f"📊 Size: {result.file_size} bytes ({file_size_mb} MB)\n"
        message += f"⏰ Generated: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    @staticmethod
    def format_file_info(file_info: Dict[str, Any]) -> str:
        """Format file information for display."""
        if not file_info.get('exists', False):
            return "❌ File does not exist"
        
        info = "📄 File Information:\n"
        info += f"  Size: {file_info['size_mb']} MB\n"
        info += f"  Created: {file_info['created']}\n"
        info += f"  Modified: {file_info['modified']}\n"
        info += f"  Readable: {'✅' if file_info['is_readable'] else '❌'}\n"
        info += f"  Writable: {'✅' if file_info['is_writable'] else '❌'}\n"
        info += f"  Path: {file_info['absolute_path']}"
        
        return info
