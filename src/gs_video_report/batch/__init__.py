"""
Enhanced Batch Processing Module v0.2.0

Professional-grade batch video processing with:
- State management and resume capabilities
- Intelligent worker pools with concurrency control
- Smart retry mechanisms with exponential backoff
- Real-time progress monitoring
- Security-aware API key management
"""

from .simple_processor import SimpleBatchProcessor
from .enhanced_processor import EnhancedBatchProcessor
from .state_manager import (
    StateManager, 
    BatchState, 
    TaskRecord, 
    TaskStatus, 
    BatchStatus
)
from .worker_pool import WorkerPool
from .retry_manager import (
    RetryManager, 
    ErrorCategory, 
    ErrorClassifier,
    RetryPolicy
)

# For backward compatibility
__all__ = [
    # Legacy
    'SimpleBatchProcessor',
    
    # Enhanced v0.2.0
    'EnhancedBatchProcessor',
    'StateManager',
    'BatchState', 
    'TaskRecord',
    'TaskStatus',
    'BatchStatus',
    'WorkerPool',
    'RetryManager',
    'ErrorCategory',
    'ErrorClassifier', 
    'RetryPolicy'
]

# Version info
__version__ = '0.2.0'