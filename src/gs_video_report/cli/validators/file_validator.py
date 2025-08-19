"""
File Validator for CLI

提供文件和目录验证功能：
- 视频文件格式验证
- 文件大小和权限检查
- 目录结构验证
- 路径安全性检查
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional, Set


class FileValidator:
    """文件验证器
    
    提供各种文件和目录验证功能，确保输入的安全性和有效性。
    """
    
    # 支持的视频格式
    SUPPORTED_VIDEO_FORMATS: Set[str] = {
        '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.flv', '.wmv'
    }
    
    # 默认最大文件大小 (GB)
    DEFAULT_MAX_FILE_SIZE_GB: int = 5
    
    @classmethod
    def is_valid_video_file(cls, file_path: str, max_size_gb: Optional[int] = None) -> bool:
        """
        检查文件是否为有效的视频文件
        
        Args:
            file_path: 文件路径
            max_size_gb: 最大文件大小限制(GB)，None表示使用默认值
            
        Returns:
            bool: 是否为有效视频文件
        """
        is_valid, _ = cls.validate_video_file(file_path, max_size_gb)
        return is_valid
    
    @classmethod
    def validate_video_file(cls, file_path: str, max_size_gb: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        验证视频文件
        
        Args:
            file_path: 文件路径
            max_size_gb: 最大文件大小限制(GB)
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
        """
        if max_size_gb is None:
            max_size_gb = cls.DEFAULT_MAX_FILE_SIZE_GB
        
        try:
            path = Path(file_path)
            
            # 检查文件是否存在
            if not path.exists():
                return False, f"文件不存在: {file_path}"
            
            # 检查是否为文件（非目录）
            if not path.is_file():
                return False, f"路径不是文件: {file_path}"
            
            # 检查文件格式
            if path.suffix.lower() not in cls.SUPPORTED_VIDEO_FORMATS:
                supported_formats = ', '.join(sorted(cls.SUPPORTED_VIDEO_FORMATS))
                return False, f"不支持的文件格式 {path.suffix}。支持的格式: {supported_formats}"
            
            # 检查文件权限
            if not os.access(path, os.R_OK):
                return False, f"文件无读取权限: {file_path}"
            
            # 检查文件大小
            file_size_gb = path.stat().st_size / (1024**3)
            if file_size_gb > max_size_gb:
                return False, f"文件过大 ({file_size_gb:.2f}GB)，最大支持 {max_size_gb}GB"
            
            # 检查文件是否为空
            if path.stat().st_size == 0:
                return False, f"文件为空: {file_path}"
            
            return True, None
            
        except PermissionError:
            return False, f"访问文件权限不足: {file_path}"
        except OSError as e:
            return False, f"文件系统错误: {e}"
        except Exception as e:
            return False, f"文件验证失败: {e}"
    
    @classmethod
    def validate_directory(cls, dir_path: str, must_contain_videos: bool = False) -> Tuple[bool, Optional[str]]:
        """
        验证目录
        
        Args:
            dir_path: 目录路径
            must_contain_videos: 是否必须包含视频文件
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
        """
        try:
            path = Path(dir_path)
            
            # 检查目录是否存在
            if not path.exists():
                return False, f"目录不存在: {dir_path}"
            
            # 检查是否为目录
            if not path.is_dir():
                return False, f"路径不是目录: {dir_path}"
            
            # 检查目录权限
            if not os.access(path, os.R_OK):
                return False, f"目录无读取权限: {dir_path}"
            
            # 如果需要，检查是否包含视频文件
            if must_contain_videos:
                video_files = cls.find_video_files(dir_path)
                if not video_files:
                    supported_formats = ', '.join(sorted(cls.SUPPORTED_VIDEO_FORMATS))
                    return False, f"目录中未找到支持的视频文件。支持的格式: {supported_formats}"
            
            return True, None
            
        except PermissionError:
            return False, f"访问目录权限不足: {dir_path}"
        except OSError as e:
            return False, f"目录访问错误: {e}"
        except Exception as e:
            return False, f"目录验证失败: {e}"
    
    @classmethod
    def find_video_files(cls, dir_path: str, recursive: bool = False) -> List[str]:
        """
        在目录中查找视频文件
        
        Args:
            dir_path: 目录路径
            recursive: 是否递归搜索子目录
            
        Returns:
            List[str]: 视频文件路径列表
        """
        video_files = []
        
        try:
            path = Path(dir_path)
            
            if not path.exists() or not path.is_dir():
                return video_files
            
            # 确定搜索模式
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            # 搜索文件
            for file_path in path.glob(pattern):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in cls.SUPPORTED_VIDEO_FORMATS):
                    # 进一步验证文件
                    if cls.is_valid_video_file(str(file_path)):
                        video_files.append(str(file_path))
            
        except Exception as e:
            # 如果出错，返回空列表而不是抛出异常
            pass
        
        return sorted(video_files)
    
    @classmethod
    def validate_output_path(cls, output_path: str, create_dirs: bool = True) -> Tuple[bool, Optional[str]]:
        """
        验证输出路径
        
        Args:
            output_path: 输出文件路径
            create_dirs: 是否自动创建不存在的目录
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
        """
        try:
            path = Path(output_path)
            
            # 检查父目录
            parent_dir = path.parent
            
            if not parent_dir.exists():
                if create_dirs:
                    try:
                        parent_dir.mkdir(parents=True, exist_ok=True)
                    except PermissionError:
                        return False, f"无权限创建目录: {parent_dir}"
                    except OSError as e:
                        return False, f"创建目录失败: {e}"
                else:
                    return False, f"输出目录不存在: {parent_dir}"
            
            # 检查父目录权限
            if not os.access(parent_dir, os.W_OK):
                return False, f"输出目录无写入权限: {parent_dir}"
            
            # 检查文件是否已存在
            if path.exists():
                if not path.is_file():
                    return False, f"输出路径已存在且不是文件: {output_path}"
                if not os.access(path, os.W_OK):
                    return False, f"输出文件无写入权限: {output_path}"
            
            return True, None
            
        except Exception as e:
            return False, f"输出路径验证失败: {e}"
    
    @classmethod
    def get_file_info(cls, file_path: str) -> Optional[dict]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[dict]: 文件信息字典，如果文件不存在则返回None
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return None
            
            stat = path.stat()
            
            return {
                'name': path.name,
                'size_bytes': stat.st_size,
                'size_mb': stat.st_size / (1024**2),
                'size_gb': stat.st_size / (1024**3),
                'extension': path.suffix.lower(),
                'is_video': path.suffix.lower() in cls.SUPPORTED_VIDEO_FORMATS,
                'readable': os.access(path, os.R_OK),
                'writable': os.access(path, os.W_OK),
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime
            }
            
        except Exception:
            return None
