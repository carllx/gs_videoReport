"""
URL Validator for CLI

提供URL验证功能：
- YouTube URL格式验证
- 视频ID提取
- URL可访问性检查
- 安全性验证
"""

import re
import requests
from typing import Tuple, Optional, List
from urllib.parse import urlparse, parse_qs


class URLValidator:
    """URL验证器
    
    提供YouTube URL和其他URL的验证功能。
    """
    
    # YouTube URL模式 (视频ID必须恰好11个字符)
    YOUTUBE_PATTERNS: List[str] = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(?:\&.*)?$',
        r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})(?:\?.*)?$',
        r'https?://(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})(?:\&.*)?$',
        r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})(?:\?.*)?$',
        r'https?://(?:www\.)?youtube-nocookie\.com/embed/([a-zA-Z0-9_-]{11})(?:\?.*)?$'
    ]
    
    @classmethod
    def validate_youtube_url(cls, url: str) -> Tuple[bool, Optional[str]]:
        """
        验证YouTube URL并提取视频ID
        
        Args:
            url: 要验证的URL
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 视频ID)
        """
        if not url or not isinstance(url, str):
            return False, None
        
        # 清理URL（移除多余空格）
        url = url.strip()
        
        # 检查URL格式
        for pattern in cls.YOUTUBE_PATTERNS:
            match = re.match(pattern, url)
            if match:
                video_id = match.group(1)
                # 验证视频ID格式
                if cls._is_valid_video_id(video_id):
                    return True, video_id
        
        return False, None
    
    @classmethod
    def is_valid_youtube_url(cls, url: str) -> bool:
        """
        检查是否为有效的YouTube URL
        
        Args:
            url: 要检查的URL
            
        Returns:
            bool: 是否为有效URL
        """
        is_valid, _ = cls.validate_youtube_url(url)
        return is_valid
    
    @classmethod
    def extract_video_id(cls, url: str) -> Optional[str]:
        """
        从YouTube URL提取视频ID
        
        Args:
            url: YouTube URL
            
        Returns:
            Optional[str]: 视频ID，如果无效则返回None
        """
        is_valid, video_id = cls.validate_youtube_url(url)
        return video_id if is_valid else None
    
    @classmethod
    def check_url_accessibility(cls, url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
        """
        检查URL是否可访问
        
        Args:
            url: 要检查的URL
            timeout: 超时时间（秒）
            
        Returns:
            Tuple[bool, Optional[str]]: (是否可访问, 错误消息)
        """
        try:
            # 基础URL格式验证
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "URL格式无效"
            
            # 发送HEAD请求检查可访问性
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            
            if response.status_code == 200:
                return True, None
            elif response.status_code == 404:
                return False, "资源不存在 (404)"
            elif response.status_code == 403:
                return False, "访问被禁止 (403)"
            elif response.status_code >= 500:
                return False, f"服务器错误 ({response.status_code})"
            else:
                return False, f"无法访问 (HTTP {response.status_code})"
                
        except requests.exceptions.Timeout:
            return False, f"请求超时 ({timeout}秒)"
        except requests.exceptions.ConnectionError:
            return False, "网络连接错误"
        except requests.exceptions.TooManyRedirects:
            return False, "重定向次数过多"
        except requests.exceptions.RequestException as e:
            return False, f"请求失败: {str(e)}"
        except Exception as e:
            return False, f"URL检查失败: {str(e)}"
    
    @classmethod
    def normalize_youtube_url(cls, url: str) -> Optional[str]:
        """
        标准化YouTube URL为统一格式
        
        Args:
            url: YouTube URL
            
        Returns:
            Optional[str]: 标准化的URL，如果无效则返回None
        """
        video_id = cls.extract_video_id(url)
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return None
    
    @classmethod
    def get_video_thumbnail_url(cls, url: str, quality: str = 'maxresdefault') -> Optional[str]:
        """
        获取YouTube视频缩略图URL
        
        Args:
            url: YouTube URL
            quality: 缩略图质量 ('maxresdefault', 'hqdefault', 'mqdefault', 'default')
            
        Returns:
            Optional[str]: 缩略图URL，如果无效则返回None
        """
        video_id = cls.extract_video_id(url)
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
        return None
    
    @classmethod
    def validate_playlist_url(cls, url: str) -> Tuple[bool, Optional[str]]:
        """
        验证YouTube播放列表URL
        
        Args:
            url: 播放列表URL
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 播放列表ID)
        """
        if not url or not isinstance(url, str):
            return False, None
        
        # YouTube播放列表模式
        playlist_patterns = [
            r'https?://(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)',
            r'https?://(?:www\.)?youtube\.com/watch\?.*list=([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in playlist_patterns:
            match = re.search(pattern, url)
            if match:
                playlist_id = match.group(1)
                if len(playlist_id) >= 10:  # 播放列表ID通常较长
                    return True, playlist_id
        
        return False, None
    
    @classmethod
    def _is_valid_video_id(cls, video_id: str) -> bool:
        """
        验证YouTube视频ID格式
        
        Args:
            video_id: 视频ID
            
        Returns:
            bool: 是否为有效的视频ID
        """
        if not video_id or len(video_id) != 11:
            return False
        
        # 检查字符集（YouTube视频ID只包含字母、数字、下划线和连字符）
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-')
        return all(c in valid_chars for c in video_id)
    
    @classmethod
    def get_url_info(cls, url: str) -> dict:
        """
        获取URL的详细信息
        
        Args:
            url: 要分析的URL
            
        Returns:
            dict: URL信息字典
        """
        info = {
            'url': url,
            'is_valid': False,
            'is_youtube': False,
            'video_id': None,
            'is_playlist': False,
            'playlist_id': None,
            'normalized_url': None,
            'thumbnail_url': None
        }
        
        try:
            # 检查YouTube视频URL
            is_valid_video, video_id = cls.validate_youtube_url(url)
            if is_valid_video:
                info.update({
                    'is_valid': True,
                    'is_youtube': True,
                    'video_id': video_id,
                    'normalized_url': cls.normalize_youtube_url(url),
                    'thumbnail_url': cls.get_video_thumbnail_url(url)
                })
            
            # 检查YouTube播放列表URL
            is_valid_playlist, playlist_id = cls.validate_playlist_url(url)
            if is_valid_playlist:
                info.update({
                    'is_playlist': True,
                    'playlist_id': playlist_id
                })
            
            # 如果都不是，检查基本URL格式
            if not info['is_valid']:
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    info['is_valid'] = True
            
        except Exception:
            # 如果出错，保持默认值
            pass
        
        return info
