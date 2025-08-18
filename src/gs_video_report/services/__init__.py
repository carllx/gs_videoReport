"""
Services module for gs_videoReport.

This module contains service classes for external API integrations
and business logic processing.
"""

from .gemini_service import GeminiService, GeminiAnalysisResult

__all__ = [
    'GeminiService',
    'GeminiAnalysisResult'
]
