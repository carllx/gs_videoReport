"""
Enhanced State Management System for Batch Processing
Provides reliable JSON state persistence, integrity validation, and resume capabilities.
"""
import json
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import hashlib
import fcntl
import tempfile
import shutil

from rich.console import Console

console = Console()

class TaskStatus(Enum):
    """Task processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing" 
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"

class BatchStatus(Enum):
    """Batch processing status enumeration"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskRecord:
    """Individual task record with full metadata"""
    
    def __init__(self, 
                 task_id: str,
                 video_path: str,
                 template_name: str,
                 output_path: Optional[str] = None,
                 status: TaskStatus = TaskStatus.PENDING):
        self.task_id = task_id
        self.video_path = video_path
        self.template_name = template_name
        self.output_path = output_path
        self.status = status
        
        # Execution metadata
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.attempts = 0
        self.max_retries = 3
        
        # Result metadata
        self.error_message: Optional[str] = None
        self.file_size_bytes: Optional[int] = None
        self.processing_time_seconds: Optional[float] = None
        self.worker_id: Optional[str] = None
        
        # For resume validation
        self.file_hash: Optional[str] = None
        
    def start_processing(self, worker_id: str):
        """Mark task as started"""
        self.status = TaskStatus.PROCESSING
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.worker_id = worker_id
        self.attempts += 1
        
    def complete_success(self, output_path: str, processing_time: float):
        """Mark task as successfully completed"""
        self.status = TaskStatus.SUCCESS
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.output_path = output_path
        self.processing_time_seconds = processing_time
        
    def complete_failed(self, error_message: str):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.error_message = error_message
        
    def complete_skipped(self, reason: str):
        """Mark task as skipped"""
        self.status = TaskStatus.SKIPPED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.error_message = reason
        
    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return (self.status == TaskStatus.FAILED and 
                self.attempts < self.max_retries)
    
    def reset_for_retry(self):
        """Reset task state for retry"""
        if self.can_retry():
            self.status = TaskStatus.PENDING
            self.started_at = None
            self.completed_at = None
            self.error_message = None
            self.worker_id = None
    
    def calculate_file_hash(self) -> str:
        """Calculate SHA256 hash of video file for validation"""
        if not Path(self.video_path).exists():
            return ""
        
        sha256_hash = hashlib.sha256()
        with open(self.video_path, "rb") as f:
            # Read in 64kb chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        
        self.file_hash = sha256_hash.hexdigest()
        return self.file_hash
    
    def validate_file_integrity(self) -> bool:
        """Validate file hasn't changed since task creation"""
        if not self.file_hash:
            return True  # No hash to validate against
        
        current_hash = self.calculate_file_hash()
        return current_hash == self.file_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'task_id': self.task_id,
            'video_path': self.video_path,
            'template_name': self.template_name,
            'output_path': self.output_path,
            'status': self.status.value,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'attempts': self.attempts,
            'max_retries': self.max_retries,
            'error_message': self.error_message,
            'file_size_bytes': self.file_size_bytes,
            'processing_time_seconds': self.processing_time_seconds,
            'worker_id': self.worker_id,
            'file_hash': self.file_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskRecord':
        """Create TaskRecord from dictionary"""
        task = cls(
            task_id=data['task_id'],
            video_path=data['video_path'],
            template_name=data['template_name'],
            output_path=data.get('output_path'),
            status=TaskStatus(data['status'])
        )
        
        # Restore metadata
        task.created_at = data.get('created_at', task.created_at)
        task.started_at = data.get('started_at')
        task.completed_at = data.get('completed_at')
        task.attempts = data.get('attempts', 0)
        task.max_retries = data.get('max_retries', 3)
        task.error_message = data.get('error_message')
        task.file_size_bytes = data.get('file_size_bytes')
        task.processing_time_seconds = data.get('processing_time_seconds')
        task.worker_id = data.get('worker_id')
        task.file_hash = data.get('file_hash')
        
        return task

class BatchState:
    """Complete batch processing state with all tasks and metadata"""
    
    def __init__(self, batch_id: str, input_dir: str, template_name: str, output_dir: Optional[str] = None):
        self.batch_id = batch_id
        self.input_dir = input_dir
        self.template_name = template_name
        self.output_dir = output_dir
        
        # Batch metadata
        self.status = BatchStatus.CREATED
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        
        # Configuration
        self.max_workers = 1
        self.max_retries = 3
        self.skip_existing = False
        
        # Tasks
        self.tasks: Dict[str, TaskRecord] = {}
        
        # Statistics (computed dynamically)
        self._lock = threading.Lock()
        
    def add_task(self, task: TaskRecord):
        """Add task to batch"""
        with self._lock:
            self.tasks[task.task_id] = task
    
    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def get_pending_tasks(self) -> List[TaskRecord]:
        """Get all pending tasks"""
        return [task for task in self.tasks.values() 
                if task.status == TaskStatus.PENDING]
    
    def get_failed_retryable_tasks(self) -> List[TaskRecord]:
        """Get failed tasks that can be retried"""
        return [task for task in self.tasks.values() if task.can_retry()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current batch statistics"""
        with self._lock:
            stats = {
                'total': len(self.tasks),
                'pending': 0,
                'processing': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0,
                'cancelled': 0
            }
            
            for task in self.tasks.values():
                stats[task.status.value] += 1
            
            stats['completed'] = stats['success'] + stats['failed'] + stats['skipped']
            stats['progress_percentage'] = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            return stats
    
    def start_batch(self):
        """Mark batch as started"""
        self.status = BatchStatus.RUNNING
        self.started_at = datetime.now(timezone.utc).isoformat()
    
    def complete_batch(self):
        """Mark batch as completed"""
        stats = self.get_statistics()
        if stats['failed'] > 0:
            self.status = BatchStatus.FAILED
        else:
            self.status = BatchStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc).isoformat()
    
    def pause_batch(self):
        """Mark batch as paused"""
        self.status = BatchStatus.PAUSED
    
    def resume_batch(self):
        """Mark batch as resumed"""
        self.status = BatchStatus.RUNNING
    
    def cancel_batch(self):
        """Mark batch as cancelled"""
        self.status = BatchStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        
        # Cancel all pending/processing tasks
        with self._lock:
            for task in self.tasks.values():
                if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'batch_id': self.batch_id,
            'input_dir': self.input_dir,
            'template_name': self.template_name,
            'output_dir': self.output_dir,
            'status': self.status.value,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'max_workers': self.max_workers,
            'max_retries': self.max_retries,
            'skip_existing': self.skip_existing,
            'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            'statistics': self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchState':
        """Create BatchState from dictionary"""
        batch = cls(
            batch_id=data['batch_id'],
            input_dir=data['input_dir'],
            template_name=data['template_name'],
            output_dir=data.get('output_dir')
        )
        
        # Restore metadata
        batch.status = BatchStatus(data['status'])
        batch.created_at = data.get('created_at', batch.created_at)
        batch.started_at = data.get('started_at')
        batch.completed_at = data.get('completed_at')
        batch.max_workers = data.get('max_workers', 1)
        batch.max_retries = data.get('max_retries', 3)
        batch.skip_existing = data.get('skip_existing', False)
        
        # Restore tasks
        tasks_data = data.get('tasks', {})
        for task_id, task_data in tasks_data.items():
            batch.tasks[task_id] = TaskRecord.from_dict(task_data)
        
        return batch

class StateManager:
    """
    Thread-safe state manager with atomic operations and file locking.
    Provides reliable persistence and recovery for batch processing.
    """
    
    def __init__(self, state_dir: str = "batch_states"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(exist_ok=True)
        
        # Thread safety
        self._lock = threading.Lock()
        self._file_locks: Dict[str, threading.Lock] = {}
        
    def _get_state_file_path(self, batch_id: str) -> Path:
        """Get the state file path for a batch"""
        return self.state_dir / f"{batch_id}_state.json"
    
    def _get_file_lock(self, batch_id: str) -> threading.Lock:
        """Get or create thread lock for batch file"""
        if batch_id not in self._file_locks:
            with self._lock:
                if batch_id not in self._file_locks:
                    self._file_locks[batch_id] = threading.Lock()
        return self._file_locks[batch_id]
    
    def save_state(self, batch_state: BatchState) -> bool:
        """
        Atomically save batch state to JSON file with file locking.
        Returns True if successful, False otherwise.
        """
        file_lock = self._get_file_lock(batch_state.batch_id)
        state_file = self._get_state_file_path(batch_state.batch_id)
        
        try:
            with file_lock:
                # Create temporary file for atomic write
                with tempfile.NamedTemporaryFile(
                    mode='w', 
                    suffix='.tmp',
                    dir=state_file.parent,
                    delete=False,
                    encoding='utf-8'
                ) as tmp_file:
                    
                    # Acquire file lock on temp file
                    fcntl.flock(tmp_file.fileno(), fcntl.LOCK_EX)
                    
                    # Write state data
                    state_data = batch_state.to_dict()
                    state_data['_metadata'] = {
                        'version': '1.0',
                        'saved_at': datetime.now(timezone.utc).isoformat(),
                        'checksum': self._calculate_checksum(state_data)
                    }
                    
                    json.dump(state_data, tmp_file, indent=2, ensure_ascii=False)
                    tmp_file.flush()
                    
                    # Atomic move
                    shutil.move(tmp_file.name, state_file)
                    
                return True
                
        except Exception as e:
            console.print(f"[red]❌ Failed to save state for batch {batch_state.batch_id}: {e}[/red]")
            return False
    
    def load_state(self, batch_id: str) -> Optional[BatchState]:
        """
        Load batch state from JSON file with integrity validation.
        Returns None if file doesn't exist or is corrupted.
        """
        file_lock = self._get_file_lock(batch_id)
        state_file = self._get_state_file_path(batch_id)
        
        if not state_file.exists():
            return None
        
        try:
            with file_lock:
                with open(state_file, 'r', encoding='utf-8') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                    state_data = json.load(f)
                
                # Validate checksum if present
                if '_metadata' in state_data:
                    metadata = state_data.pop('_metadata')
                    expected_checksum = metadata.get('checksum')
                    actual_checksum = self._calculate_checksum(state_data)
                    
                    if expected_checksum != actual_checksum:
                        console.print(f"[red]❌ State file corrupted for batch {batch_id} (checksum mismatch)[/red]")
                        return None
                
                batch_state = BatchState.from_dict(state_data)
                
                # Validate file integrity for pending/processing tasks
                corrupted_tasks = []
                for task in batch_state.tasks.values():
                    if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                        if not task.validate_file_integrity():
                            corrupted_tasks.append(task.task_id)
                            console.print(f"[yellow]⚠️  File changed: {task.video_path}[/yellow]")
                
                if corrupted_tasks:
                    console.print(f"[yellow]⚠️  {len(corrupted_tasks)} files have changed since last run[/yellow]")
                
                return batch_state
                
        except Exception as e:
            console.print(f"[red]❌ Failed to load state for batch {batch_id}: {e}[/red]")
            return None
    
    def delete_state(self, batch_id: str) -> bool:
        """Delete batch state file"""
        file_lock = self._get_file_lock(batch_id)
        state_file = self._get_state_file_path(batch_id)
        
        try:
            with file_lock:
                if state_file.exists():
                    state_file.unlink()
                return True
        except Exception as e:
            console.print(f"[red]❌ Failed to delete state for batch {batch_id}: {e}[/red]")
            return False
    
    def list_batch_states(self) -> List[Dict[str, Any]]:
        """List all available batch states with basic metadata"""
        batch_states = []
        
        for state_file in self.state_dir.glob("*_state.json"):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                # Extract basic metadata
                batch_info = {
                    'batch_id': state_data.get('batch_id'),
                    'status': state_data.get('status'),
                    'created_at': state_data.get('created_at'),
                    'input_dir': state_data.get('input_dir'),
                    'statistics': state_data.get('statistics', {}),
                    'file_path': str(state_file)
                }
                batch_states.append(batch_info)
                
            except Exception as e:
                console.print(f"[yellow]⚠️  Skipping corrupted state file {state_file}: {e}[/yellow]")
        
        # Sort by creation time (newest first)
        batch_states.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return batch_states
    
    def cleanup_old_states(self, keep_days: int = 7) -> int:
        """Clean up state files older than specified days"""
        cutoff_time = time.time() - (keep_days * 24 * 3600)
        cleaned_count = 0
        
        for state_file in self.state_dir.glob("*_state.json"):
            try:
                if state_file.stat().st_mtime < cutoff_time:
                    state_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                console.print(f"[yellow]⚠️  Failed to clean up {state_file}: {e}[/yellow]")
        
        return cleaned_count
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA256 checksum of state data for integrity validation"""
        # Convert to JSON string with sorted keys for consistent hashing
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    def create_checkpoint(self, batch_id: str) -> bool:
        """Create a checkpoint backup of current state"""
        try:
            state_file = self._get_state_file_path(batch_id)
            if not state_file.exists():
                return False
            
            checkpoint_dir = self.state_dir / "checkpoints"
            checkpoint_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_file = checkpoint_dir / f"{batch_id}_checkpoint_{timestamp}.json"
            
            shutil.copy2(state_file, checkpoint_file)
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to create checkpoint for batch {batch_id}: {e}[/red]")
            return False
