"""
Lesson formatter module for converting Gemini API analysis results into structured lesson plans.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re
import yaml
from jinja2 import Environment, FileSystemLoader, Template
from jinja2.exceptions import TemplateError

from .config import Config


logger = logging.getLogger(__name__)


class TimestampFormatter:
    """Utility class for formatting YouTube timestamps and links."""
    
    @staticmethod
    def seconds_to_display(seconds: int) -> str:
        """Convert seconds to MM:SS or HH:MM:SS format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def create_youtube_timestamp_url(video_url: str, seconds: int) -> str:
        """Create a clickable YouTube URL with timestamp."""
        # Extract video ID from various YouTube URL formats
        video_id = TimestampFormatter._extract_video_id(video_url)
        if not video_id:
            logger.warning(f"Could not extract video ID from URL: {video_url}")
            return video_url
            
        return f"https://www.youtube.com/watch?v={video_id}&t={seconds}s"
    
    @staticmethod
    def _extract_video_id(url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None


class LessonPlanData:
    """Data class for holding lesson plan information."""
    
    def __init__(self, gemini_result: Dict[str, Any], video_url: str = "", config: Optional[Config] = None):
        self.gemini_result = gemini_result
        self.video_url = video_url
        self.config = config or Config({})
        self.creation_date = datetime.now().isoformat()
        
        # Extract basic information
        self.video_title = gemini_result.get('title', 'Untitled Video')
        self.video_author = gemini_result.get('author', 'Unknown')
        self.video_duration = gemini_result.get('duration', 'Unknown')
        self.content_summary = gemini_result.get('summary', '')
        self.learning_objectives = gemini_result.get('learning_objectives', '')
        
        # Process content sections with timestamps
        self.content_sections = self._process_content_sections()
        self.important_timestamps = self._extract_important_timestamps()
        
        # Additional content
        self.suggested_activities = gemini_result.get('suggested_activities', '')
        self.related_resources = gemini_result.get('related_resources', '')
        
    def _process_content_sections(self) -> List[Dict[str, Any]]:
        """Process content sections and add timestamp information."""
        sections = self.gemini_result.get('content_sections', [])
        processed_sections = []
        
        for section in sections:
            processed_section = {
                'title': section.get('title', ''),
                'content': section.get('content', ''),
                'key_points': section.get('key_points', [])
            }
            
            # Process timestamp if available
            timestamp_seconds = section.get('timestamp_seconds')
            if timestamp_seconds is not None:
                processed_section['timestamp_display'] = TimestampFormatter.seconds_to_display(timestamp_seconds)
                processed_section['timestamp_url'] = TimestampFormatter.create_youtube_timestamp_url(
                    self.video_url, timestamp_seconds
                )
            else:
                processed_section['timestamp_display'] = '00:00'
                processed_section['timestamp_url'] = self.video_url
                
            processed_sections.append(processed_section)
            
        return processed_sections
    
    def _extract_important_timestamps(self) -> List[Dict[str, Any]]:
        """Extract and format important timestamps from the analysis."""
        timestamps = self.gemini_result.get('important_timestamps', [])
        processed_timestamps = []
        
        for ts in timestamps:
            timestamp_seconds = ts.get('seconds')
            if timestamp_seconds is not None:
                processed_timestamps.append({
                    'time_display': TimestampFormatter.seconds_to_display(timestamp_seconds),
                    'url': TimestampFormatter.create_youtube_timestamp_url(self.video_url, timestamp_seconds),
                    'description': ts.get('description', '')
                })
                
        return processed_timestamps
    
    def generate_frontmatter(self, template_name: str = "basic_lesson_plan", 
                           template_version: str = "1.0") -> Dict[str, Any]:
        """Generate YAML frontmatter for Obsidian Dataview compatibility."""
        frontmatter = {
            'title': self.video_title,
            'author': self.video_author,
            'duration': self.video_duration,
            'source_url': self.video_url,
            'created_date': self.creation_date,
            'template_used': template_name,
            'template_version': template_version,
            'type': 'lesson_plan',
            'tags': self._generate_tags()
        }
        
        # Add additional metadata if available
        if 'subject' in self.gemini_result:
            frontmatter['subject'] = self.gemini_result['subject']
        if 'difficulty_level' in self.gemini_result:
            frontmatter['difficulty'] = self.gemini_result['difficulty_level']
            
        return frontmatter
    
    def _generate_tags(self) -> List[str]:
        """Generate tags based on content analysis."""
        tags = ['lesson_plan', 'video_analysis']
        
        # Add tags from Gemini result if available
        if 'tags' in self.gemini_result:
            tags.extend(self.gemini_result['tags'])
        if 'subject' in self.gemini_result:
            tags.append(self.gemini_result['subject'].lower().replace(' ', '_'))
            
        return list(set(tags))  # Remove duplicates


class LessonFormatter:
    """Main lesson formatter class for creating structured lesson plans."""
    
    def __init__(self, config: Config, template_manager=None):
        self.config = config
        self.template_manager = template_manager
        
        # Setup Jinja2 environment for template rendering
        template_path = Path(config.data.get('output', {}).get('template_directory', 
                            'src/gs_video_report/templates/outputs'))
        
        if template_path.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_path)),
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            logger.warning(f"Template directory not found: {template_path}")
            self.jinja_env = Environment()
    
    def _get_api_model(self) -> str:
        """获取API模型配置"""
        # 🎯 统一配置：使用统一的模型配置获取函数
        from .config import get_default_model
        return get_default_model(self.config.data)
            
    def format_lesson_plan(self, gemini_result: Dict[str, Any], 
                          video_url: str = "",
                          template_name: str = "basic_lesson_plan") -> str:
        """
        Format a complete lesson plan from Gemini API results.
        
        Args:
            gemini_result: Analysis results from Gemini API
            video_url: Source video URL
            template_name: Name of template to use
            
        Returns:
            Formatted lesson plan as Markdown string
        """
        try:
            logger.info(f"Formatting lesson plan using template: {template_name}")
            
            # Create lesson plan data
            lesson_data = LessonPlanData(gemini_result, video_url, self.config)
            
            # Load template
            template = self._load_template(template_name)
            if not template:
                logger.error(f"Failed to load template: {template_name}")
                return self._create_fallback_lesson_plan(lesson_data)
            
            # Prepare template variables
            template_vars = self._prepare_template_variables(lesson_data, template_name)
            
            # Render template
            rendered_content = template.render(**template_vars)
            
            # Add YAML frontmatter
            frontmatter = lesson_data.generate_frontmatter(template_name)
            yaml_header = yaml.dump(frontmatter, default_flow_style=False, 
                                  allow_unicode=True, sort_keys=False)
            
            # Combine frontmatter and content
            full_lesson_plan = f"---\n{yaml_header}---\n\n{rendered_content}"
            
            logger.info("Successfully formatted lesson plan")
            return full_lesson_plan
            
        except Exception as e:
            logger.error(f"Error formatting lesson plan: {e}")
            return self._create_fallback_lesson_plan(
                LessonPlanData(gemini_result, video_url, self.config)
            )
    
    def _load_template(self, template_name: str) -> Optional[Template]:
        """Load Jinja2 template by name."""
        try:
            # Try to load from file system
            template_filename = f"{template_name}.md"
            return self.jinja_env.get_template(template_filename)
            
        except TemplateError as e:
            logger.warning(f"Failed to load template {template_name}: {e}")
            return None
    
    def _prepare_template_variables(self, lesson_data: LessonPlanData, 
                                  template_name: str) -> Dict[str, Any]:
        """Prepare all variables for template rendering."""
        return {
            # Basic video information
            'video_title': lesson_data.video_title,
            'video_author': lesson_data.video_author,
            'video_duration': lesson_data.video_duration,
            'video_url': lesson_data.video_url,
            'creation_date': lesson_data.creation_date,
            
            # Template information
            'template_name': template_name,
            'template_version': '1.0',
            
            # Content information
            'lesson_title': lesson_data.video_title,
            'content_summary': lesson_data.content_summary,
            'learning_objectives': lesson_data.learning_objectives,
            'content_sections': lesson_data.content_sections,
            'important_timestamps': lesson_data.important_timestamps,
            'suggested_activities': lesson_data.suggested_activities,
            'related_resources': lesson_data.related_resources,
            
            # Generation metadata
            # 🎯 统一配置：使用统一的模型配置获取函数
            'api_model': self._get_api_model(),
            'generation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tags_list': lesson_data._generate_tags()
        }
    
    def _create_fallback_lesson_plan(self, lesson_data: LessonPlanData) -> str:
        """Create a basic lesson plan when template loading fails."""
        logger.info("Creating fallback lesson plan")
        
        frontmatter = lesson_data.generate_frontmatter()
        yaml_header = yaml.dump(frontmatter, default_flow_style=False, 
                              allow_unicode=True, sort_keys=False)
        
        content = f"""# {lesson_data.video_title}

## 视频信息 (Video Information)
- **标题 (Title)**: {lesson_data.video_title}
- **时长 (Duration)**: {lesson_data.video_duration}
- **来源 (Source)**: [{lesson_data.video_url}]({lesson_data.video_url})
- **生成日期 (Generated)**: {lesson_data.creation_date}

## 内容概览 (Content Overview)
{lesson_data.content_summary}

## 学习目标 (Learning Objectives)  
{lesson_data.learning_objectives}

## 详细内容 (Detailed Content)
"""

        # Add content sections
        for section in lesson_data.content_sections:
            content += f"\n### {section['title']}\n\n{section['content']}\n\n"
            if section.get('timestamp_url'):
                content += f"**关键时间点**: [{section['timestamp_display']}]({section['timestamp_url']})\n\n"
        
        # Add important timestamps
        if lesson_data.important_timestamps:
            content += "\n## 重要时间戳 (Important Timestamps)\n\n"
            for ts in lesson_data.important_timestamps:
                content += f"- [{ts['time_display']}]({ts['url']}) - {ts['description']}\n"
        
        return f"---\n{yaml_header}---\n\n{content}"
    
    def generate_filename(self, lesson_data: LessonPlanData, 
                         output_dir: Optional[str] = None) -> str:
        """
        Generate an intelligent filename for the lesson plan.
        
        Args:
            lesson_data: Lesson plan data
            output_dir: Optional output directory
            
        Returns:
            Full file path as string
        """
        # Clean video title for filename
        safe_title = re.sub(r'[^\w\s-]', '', lesson_data.video_title)
        safe_title = re.sub(r'\s+', '_', safe_title.strip())[:50]  # Limit length
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        # Create filename
        filename = f"{safe_title}_{timestamp}_lesson_plan.md"
        
        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Path(self.config.data.get('output', {}).get('directory', './output'))
        
        output_path.mkdir(parents=True, exist_ok=True)
        return str(output_path / filename)
