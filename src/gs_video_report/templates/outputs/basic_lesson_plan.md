---
title: "{{ video_title }}"
author: "{{ video_author }}"
duration: "{{ video_duration }}"
source_url: "{{ video_url }}"
created_date: "{{ creation_date }}"
template_used: "{{ template_name }}"
tags: {{ tags_list }}
type: "lesson_plan"
---

# {{ lesson_title }}

## 视频信息 (Video Information)
- **标题 (Title)**: {{ video_title }}
- **时长 (Duration)**: {{ video_duration }}
- **来源 (Source)**: [{{ video_url }}]({{ video_url }})
- **生成日期 (Generated)**: {{ creation_date }}
- **模板 (Template)**: {{ template_name }} v{{ template_version }}

## 内容概览 (Content Overview)
{{ content_summary }}

## 学习目标 (Learning Objectives)
{{ learning_objectives }}

## 详细内容 (Detailed Content)

{% for section in content_sections %}
### {{ section.title }}

{{ section.content }}

**关键时间点 (Key Timestamp)**: [{{ section.timestamp_display }}]({{ section.timestamp_url }})

{% if section.key_points %}
**要点 (Key Points)**:
{% for point in section.key_points %}
- {{ point }}
{% endfor %}
{% endif %}

---
{% endfor %}

## 重要时间戳 (Important Timestamps)

{% for timestamp in important_timestamps %}
- [{{ timestamp.time_display }}]({{ timestamp.url }}) - {{ timestamp.description }}
{% endfor %}

## 延伸学习 (Extended Learning)

### 建议活动 (Suggested Activities)
{{ suggested_activities }}

### 相关资源 (Related Resources)
{{ related_resources }}

## 生成信息 (Generation Info)
- **工具 (Tool)**: gs_videoReport
- **模板 (Template)**: {{ template_name }}
- **API模型 (API Model)**: {{ api_model }}
- **生成时间 (Generated At)**: {{ generation_timestamp }}
