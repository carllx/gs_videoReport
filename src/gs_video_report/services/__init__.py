"""
Services module for gs_videoReport.

This module contains service classes for external API integrations
and business logic processing.

v0.2.0: Simplified Gemini service focusing on core functionality,
avoiding over-engineering.
"""

from .gemini_service import GeminiService, GeminiAnalysisResult
from .simple_gemini_service import SimpleGeminiService

__all__ = [
    # Core services
    'GeminiService',
    'GeminiAnalysisResult',
    
    # v0.2.0 Simplified service (preferred)
    'SimpleGeminiService',
]
