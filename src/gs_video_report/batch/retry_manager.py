"""
Enhanced Retry Mechanism with Intelligent Error Classification
Provides exponential backoff, jitter, and API-aware retry strategies.
"""
import time
import random
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

from rich.console import Console

console = Console()

class ErrorCategory(Enum):
    """错误分类枚举"""
    NETWORK_ERROR = "network_error"           # 网络连接问题
    API_RATE_LIMIT = "api_rate_limit"        # API速率限制
    API_QUOTA_EXCEEDED = "api_quota_exceeded" # API配额超限
    FILE_ERROR = "file_error"                # 文件相关错误
    AUTH_ERROR = "auth_error"                # 认证错误
    SERVER_ERROR = "server_error"            # 服务器错误
    CLIENT_ERROR = "client_error"            # 客户端错误
    GEMINI_SPECIFIC = "gemini_specific"      # Gemini特定错误
    UNKNOWN_ERROR = "unknown_error"          # 未知错误

@dataclass
class RetryPolicy:
    """重试策略配置"""
    max_attempts: int = 3
    base_delay: float = 1.0                  # 基础延迟(秒)
    max_delay: float = 60.0                  # 最大延迟(秒)
    exponential_base: float = 2.0            # 指数退避的底数
    jitter_factor: float = 0.1               # 抖动因子 (0-1)
    retry_on_categories: Set[ErrorCategory] = field(default_factory=lambda: {
        ErrorCategory.NETWORK_ERROR,
        ErrorCategory.API_RATE_LIMIT,
        ErrorCategory.SERVER_ERROR
    })

@dataclass
class RetryAttempt:
    """重试尝试记录"""
    attempt_number: int
    timestamp: str
    error_category: ErrorCategory
    error_message: str
    delay_seconds: float
    success: bool = False

@dataclass
class RetryBudget:
    """重试预算管理"""
    max_retries_per_hour: int = 100
    max_retries_per_day: int = 500
    current_hour_retries: int = 0
    current_day_retries: int = 0
    hour_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    day_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def can_retry(self) -> bool:
        """检查是否还有重试预算"""
        now = datetime.now(timezone.utc)
        
        # 检查是否需要重置小时计数
        if now - self.hour_start >= timedelta(hours=1):
            self.hour_start = now
            self.current_hour_retries = 0
        
        # 检查是否需要重置日计数
        if now - self.day_start >= timedelta(days=1):
            self.day_start = now
            self.current_day_retries = 0
        
        return (self.current_hour_retries < self.max_retries_per_hour and
                self.current_day_retries < self.max_retries_per_day)
    
    def consume_retry(self):
        """消费一次重试预算"""
        self.current_hour_retries += 1
        self.current_day_retries += 1

class ErrorClassifier:
    """智能错误分类器"""
    
    # 错误模式匹配规则
    ERROR_PATTERNS = {
        ErrorCategory.NETWORK_ERROR: [
            r'connection.*error',
            r'timeout',
            r'network.*unreachable',
            r'dns.*resolution.*failed',
            r'socket.*error',
            r'connection.*reset',
            r'connection.*refused',
            r'read.*timeout',
            r'write.*timeout',
            r'ssl.*error',
            r'certificate.*error'
        ],
        
        ErrorCategory.API_RATE_LIMIT: [
            r'rate.*limit.*exceeded',
            r'too.*many.*requests',
            r'quota.*exceeded.*temporarily',
            r'throttled',
            r'429',
            r'rate.*limiting'
        ],
        
        ErrorCategory.API_QUOTA_EXCEEDED: [
            r'quota.*exceeded',
            r'billing.*account.*suspended',
            r'api.*limit.*reached',
            r'usage.*limit.*exceeded',
            r'insufficient.*quota',
            r'credit.*exhausted'
        ],
        
        ErrorCategory.FILE_ERROR: [
            r'file.*not.*found',
            r'no.*such.*file',
            r'permission.*denied',
            r'access.*denied',
            r'file.*corrupted',
            r'invalid.*file.*format',
            r'unsupported.*format',
            r'file.*too.*large',
            r'disk.*full',
            r'io.*error'
        ],
        
        ErrorCategory.AUTH_ERROR: [
            r'authentication.*failed',
            r'invalid.*api.*key',
            r'unauthorized',
            r'access.*denied',
            r'forbidden',
            r'401',
            r'403',
            r'invalid.*credentials',
            r'token.*expired',
            r'signature.*invalid'
        ],
        
        ErrorCategory.SERVER_ERROR: [
            r'internal.*server.*error',
            r'server.*unavailable',
            r'service.*unavailable',
            r'bad.*gateway',
            r'gateway.*timeout',
            r'500',
            r'502',
            r'503',
            r'504',
            r'upstream.*error'
        ],
        
        ErrorCategory.CLIENT_ERROR: [
            r'bad.*request',
            r'invalid.*request',
            r'malformed.*request',
            r'400',
            r'422',
            r'unprocessable.*entity',
            r'validation.*error'
        ],
        
        ErrorCategory.GEMINI_SPECIFIC: [
            r'video.*not.*supported',
            r'video.*too.*large',
            r'invalid.*video.*format',
            r'video.*processing.*failed',
            r'model.*not.*available',
            r'gemini.*error',
            r'content.*policy.*violation',
            r'safety.*filter.*triggered'
        ]
    }
    
    @classmethod
    def classify_error(cls, error_message: str) -> ErrorCategory:
        """
        根据错误消息分类错误类型
        
        Args:
            error_message: 错误消息
            
        Returns:
            ErrorCategory: 错误分类
        """
        error_lower = error_message.lower()
        
        # 按优先级匹配模式
        for category, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_lower):
                    return category
        
        return ErrorCategory.UNKNOWN_ERROR
    
    @classmethod
    def is_retryable(cls, error_category: ErrorCategory) -> bool:
        """判断错误是否可重试"""
        retryable_categories = {
            ErrorCategory.NETWORK_ERROR,
            ErrorCategory.API_RATE_LIMIT,
            ErrorCategory.SERVER_ERROR,
            ErrorCategory.UNKNOWN_ERROR  # 保守策略：未知错误允许重试一次
        }
        return error_category in retryable_categories
    
    @classmethod
    def get_retry_strategy(cls, error_category: ErrorCategory) -> RetryPolicy:
        """根据错误类型获取重试策略"""
        
        if error_category == ErrorCategory.NETWORK_ERROR:
            return RetryPolicy(
                max_attempts=5,
                base_delay=2.0,
                max_delay=30.0,
                exponential_base=1.5,
                jitter_factor=0.2
            )
        
        elif error_category == ErrorCategory.API_RATE_LIMIT:
            return RetryPolicy(
                max_attempts=3,
                base_delay=10.0,
                max_delay=120.0,
                exponential_base=2.0,
                jitter_factor=0.3
            )
        
        elif error_category == ErrorCategory.SERVER_ERROR:
            return RetryPolicy(
                max_attempts=4,
                base_delay=5.0,
                max_delay=60.0,
                exponential_base=2.0,
                jitter_factor=0.1
            )
        
        elif error_category == ErrorCategory.UNKNOWN_ERROR:
            return RetryPolicy(
                max_attempts=2,
                base_delay=3.0,
                max_delay=10.0,
                exponential_base=1.8,
                jitter_factor=0.1
            )
        
        else:
            # 不可重试的错误类型
            return RetryPolicy(max_attempts=0)

class RetryManager:
    """
    智能重试管理器
    提供基于错误类型的重试策略、指数退避和预算管理
    """
    
    def __init__(self, global_retry_budget: Optional[RetryBudget] = None):
        self.global_retry_budget = global_retry_budget or RetryBudget()
        self.task_retry_history: Dict[str, List[RetryAttempt]] = {}
        self._lock = threading.Lock()
        
        # 统计信息
        self.total_retries = 0
        self.successful_retries = 0
        self.failed_retries = 0
        self.retry_by_category: Dict[ErrorCategory, int] = {}
    
    def should_retry(self, 
                    task_id: str, 
                    error_message: str, 
                    current_attempt: int) -> tuple[bool, Optional[float]]:
        """
        判断是否应该重试，并返回等待时间
        
        Args:
            task_id: 任务ID
            error_message: 错误消息
            current_attempt: 当前尝试次数
            
        Returns:
            tuple: (是否重试, 等待时间秒数)
        """
        
        # 1. 分类错误
        error_category = ErrorClassifier.classify_error(error_message)
        
        # 2. 检查是否可重试
        if not ErrorClassifier.is_retryable(error_category):
            console.print(f"[red]❌ 错误不可重试 ({error_category.value}): {error_message[:100]}[/red]")
            return False, None
        
        # 3. 获取重试策略
        policy = ErrorClassifier.get_retry_strategy(error_category)
        
        # 4. 检查重试次数限制
        if current_attempt >= policy.max_attempts:
            console.print(f"[red]❌ 达到最大重试次数 ({current_attempt}/{policy.max_attempts})[/red]")
            return False, None
        
        # 5. 检查全局重试预算
        if not self.global_retry_budget.can_retry():
            console.print(f"[red]❌ 重试预算耗尽[/red]")
            return False, None
        
        # 6. 计算等待时间
        delay = self._calculate_delay(policy, current_attempt)
        
        # 7. 记录重试尝试
        with self._lock:
            self._record_retry_attempt(task_id, current_attempt, error_category, error_message, delay)
            self.global_retry_budget.consume_retry()
            self.total_retries += 1
            self.retry_by_category[error_category] = self.retry_by_category.get(error_category, 0) + 1
        
        console.print(f"[yellow]🔄 将在 {delay:.1f}s 后重试 (第{current_attempt+1}次, {error_category.value})[/yellow]")
        
        return True, delay
    
    def _calculate_delay(self, policy: RetryPolicy, attempt: int) -> float:
        """
        计算指数退避延迟时间（含抖动）
        
        Args:
            policy: 重试策略
            attempt: 尝试次数
            
        Returns:
            float: 延迟时间（秒）
        """
        # 指数退避计算
        exponential_delay = policy.base_delay * (policy.exponential_base ** attempt)
        
        # 应用最大延迟限制
        capped_delay = min(exponential_delay, policy.max_delay)
        
        # 添加抖动以避免雷群效应
        jitter = capped_delay * policy.jitter_factor * (random.random() * 2 - 1)  # [-jitter, +jitter]
        final_delay = max(0.1, capped_delay + jitter)  # 最小0.1秒
        
        return final_delay
    
    def _record_retry_attempt(self, 
                             task_id: str, 
                             attempt: int, 
                             category: ErrorCategory, 
                             error_message: str, 
                             delay: float):
        """记录重试尝试"""
        
        if task_id not in self.task_retry_history:
            self.task_retry_history[task_id] = []
        
        retry_attempt = RetryAttempt(
            attempt_number=attempt + 1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            error_category=category,
            error_message=error_message[:200],  # 限制长度
            delay_seconds=delay
        )
        
        self.task_retry_history[task_id].append(retry_attempt)
    
    def mark_retry_successful(self, task_id: str):
        """标记重试成功"""
        with self._lock:
            if task_id in self.task_retry_history and self.task_retry_history[task_id]:
                self.task_retry_history[task_id][-1].success = True
                self.successful_retries += 1
    
    def mark_retry_failed(self, task_id: str):
        """标记重试最终失败"""
        with self._lock:
            self.failed_retries += 1
    
    def get_task_retry_history(self, task_id: str) -> List[RetryAttempt]:
        """获取任务的重试历史"""
        return self.task_retry_history.get(task_id, [])
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """获取重试统计信息"""
        with self._lock:
            success_rate = (self.successful_retries / max(1, self.total_retries)) * 100
            
            return {
                "total_retries": self.total_retries,
                "successful_retries": self.successful_retries,
                "failed_retries": self.failed_retries,
                "success_rate_percentage": success_rate,
                "retry_by_category": {cat.value: count for cat, count in self.retry_by_category.items()},
                "budget_status": {
                    "hour_remaining": (self.global_retry_budget.max_retries_per_hour - 
                                     self.global_retry_budget.current_hour_retries),
                    "day_remaining": (self.global_retry_budget.max_retries_per_day - 
                                    self.global_retry_budget.current_day_retries),
                    "hour_used": self.global_retry_budget.current_hour_retries,
                    "day_used": self.global_retry_budget.current_day_retries
                }
            }
    
    def cleanup_old_history(self, days: int = 7):
        """清理旧的重试历史"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        
        with self._lock:
            tasks_to_remove = []
            for task_id, attempts in self.task_retry_history.items():
                # 过滤掉过期的重试记录
                recent_attempts = [
                    attempt for attempt in attempts
                    if datetime.fromisoformat(attempt.timestamp.replace('Z', '+00:00')) > cutoff_time
                ]
                
                if recent_attempts:
                    self.task_retry_history[task_id] = recent_attempts
                else:
                    tasks_to_remove.append(task_id)
            
            # 移除完全过期的任务记录
            for task_id in tasks_to_remove:
                del self.task_retry_history[task_id]
    
    def reset_budgets(self):
        """重置重试预算（用于测试或管理需要）"""
        with self._lock:
            now = datetime.now(timezone.utc)
            self.global_retry_budget.hour_start = now
            self.global_retry_budget.day_start = now
            self.global_retry_budget.current_hour_retries = 0
            self.global_retry_budget.current_day_retries = 0

def create_task_retry_executor(retry_manager: RetryManager) -> Callable:
    """
    创建带重试功能的任务执行器装饰器
    
    Args:
        retry_manager: 重试管理器实例
        
    Returns:
        可重试的任务执行器装饰器
    """
    
    def retry_executor(task_function: Callable) -> Callable:
        """重试执行器装饰器"""
        
        def wrapper(task_id: str, *args, **kwargs):
            """包装后的任务执行函数"""
            attempt = 0
            last_error = None
            
            while True:
                try:
                    # 执行原始任务函数
                    result = task_function(task_id, *args, **kwargs)
                    
                    # 如果有重试历史，标记为成功
                    if attempt > 0:
                        retry_manager.mark_retry_successful(task_id)
                        console.print(f"[green]✅ 重试成功: {task_id} (第{attempt+1}次尝试)[/green]")
                    
                    return result
                    
                except Exception as e:
                    last_error = e
                    error_message = str(e)
                    
                    # 判断是否应该重试
                    should_retry, delay = retry_manager.should_retry(task_id, error_message, attempt)
                    
                    if not should_retry:
                        # 标记重试失败
                        if attempt > 0:
                            retry_manager.mark_retry_failed(task_id)
                        
                        # 重新抛出最后的错误
                        raise last_error
                    
                    # 等待重试
                    if delay and delay > 0:
                        time.sleep(delay)
                    
                    attempt += 1
            
        return wrapper
    return retry_executor

# 预定义的重试策略
NETWORK_RETRY_POLICY = RetryPolicy(
    max_attempts=5,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=1.5,
    jitter_factor=0.2
)

API_LIMIT_RETRY_POLICY = RetryPolicy(
    max_attempts=3,
    base_delay=10.0,
    max_delay=120.0,
    exponential_base=2.0,
    jitter_factor=0.3
)

CONSERVATIVE_RETRY_POLICY = RetryPolicy(
    max_attempts=2,
    base_delay=5.0,
    max_delay=15.0,
    exponential_base=1.8,
    jitter_factor=0.1
)
