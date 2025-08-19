"""
多API密钥轮循管理器
支持智能密钥轮循、使用统计追踪和失效检测

功能特性：
1. API密钥列表轮循使用
2. 保持环境变量支持（向后兼容）
3. 智能失效检测（区分暂时失效vs永久失效）
4. JSON格式使用统计和日志记录
5. 自动切换和重试机制
6. 密钥健康状态监控
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class KeyStatus(Enum):
    """API密钥状态枚举"""
    ACTIVE = "active"           # 活跃可用
    QUOTA_EXHAUSTED = "quota_exhausted"  # 配额耗尽（临时）
    INVALID = "invalid"         # 无效密钥（永久）
    RATE_LIMITED = "rate_limited"  # 速率限制（临时）
    UNKNOWN = "unknown"         # 未知状态

@dataclass
class KeyUsageStats:
    """API密钥使用统计"""
    key_id: str                           # 密钥ID（前4位+后4位）
    total_requests: int = 0               # 总请求数
    successful_requests: int = 0          # 成功请求数
    failed_requests: int = 0              # 失败请求数
    quota_exhausted_count: int = 0        # 配额耗尽次数
    rate_limit_count: int = 0             # 速率限制次数
    last_used: Optional[str] = None       # 最后使用时间
    last_success: Optional[str] = None    # 最后成功时间
    last_failure: Optional[str] = None    # 最后失败时间
    current_status: str = KeyStatus.UNKNOWN.value  # 当前状态
    consecutive_failures: int = 0         # 连续失败次数

    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    def is_healthy(self) -> bool:
        """判断密钥是否健康"""
        # 连续失败超过5次认为不健康
        if self.consecutive_failures > 5:
            return False
        # 成功率低于50%且请求数超过10次认为不健康
        if self.total_requests > 10 and self.success_rate() < 0.5:
            return False
        return True

class MultiKeyManager:
    """多API密钥轮循管理器"""
    
    def __init__(self, 
                 api_keys: Optional[List[str]] = None,
                 usage_log_path: str = "logs/api_key_usage.json",
                 enable_fallback_to_env: bool = True):
        """
        初始化多密钥管理器
        
        Args:
            api_keys: API密钥列表，如果为None则从配置文件读取
            usage_log_path: 使用日志文件路径
            enable_fallback_to_env: 是否启用环境变量回退
        """
        self.api_keys = api_keys or []
        self.usage_log_path = Path(usage_log_path)
        self.enable_fallback_to_env = enable_fallback_to_env
        self.current_key_index = 0
        self.usage_stats: Dict[str, KeyUsageStats] = {}
        
        # 确保日志目录存在
        self.usage_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载使用统计
        self._load_usage_stats()
        
        # 初始化密钥统计
        self._initialize_key_stats()
        
        logger.info(f"✅ 多密钥管理器初始化完成，管理 {len(self.api_keys)} 个密钥")

    def _get_key_id(self, api_key: str) -> str:
        """生成密钥ID（前4位+后4位，便于识别）"""
        if len(api_key) < 8:
            return api_key
        return f"{api_key[:4]}...{api_key[-4:]}"

    def _initialize_key_stats(self):
        """初始化密钥统计信息"""
        for api_key in self.api_keys:
            key_id = self._get_key_id(api_key)
            if key_id not in self.usage_stats:
                self.usage_stats[key_id] = KeyUsageStats(key_id=key_id)

    def _load_usage_stats(self):
        """加载使用统计"""
        try:
            if self.usage_log_path.exists():
                with open(self.usage_log_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key_id, stats_dict in data.items():
                        self.usage_stats[key_id] = KeyUsageStats(**stats_dict)
                logger.info(f"📊 已加载 {len(self.usage_stats)} 个密钥的使用统计")
        except Exception as e:
            logger.warning(f"⚠️ 加载使用统计失败: {e}")
            self.usage_stats = {}

    def _save_usage_stats(self):
        """保存使用统计"""
        try:
            stats_dict = {key_id: asdict(stats) for key_id, stats in self.usage_stats.items()}
            with open(self.usage_log_path, 'w', encoding='utf-8') as f:
                json.dump(stats_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ 保存使用统计失败: {e}")

    def get_current_api_key(self) -> Tuple[str, str]:
        """
        获取当前可用的API密钥
        
        Returns:
            Tuple[str, str]: (api_key, key_id)
            
        Raises:
            Exception: 当所有密钥都不可用时
        """
        # 如果没有配置多密钥，尝试使用环境变量
        if not self.api_keys and self.enable_fallback_to_env:
            env_key = self._get_env_api_key()
            if env_key:
                return env_key, "ENV_VAR"
            
        if not self.api_keys:
            raise Exception("❌ 没有可用的API密钥")

        # 尝试找到健康的密钥
        healthy_keys = []
        for i, api_key in enumerate(self.api_keys):
            key_id = self._get_key_id(api_key)
            stats = self.usage_stats.get(key_id)
            if not stats or stats.is_healthy():
                healthy_keys.append((i, api_key, key_id))

        if not healthy_keys:
            # 如果没有健康的密钥，使用轮循策略
            logger.warning("⚠️ 没有发现健康的密钥，使用轮循策略")
            current_key = self.api_keys[self.current_key_index]
            key_id = self._get_key_id(current_key)
            return current_key, key_id

        # 选择最健康的密钥（成功率最高或最近未使用的）
        best_key_info = min(healthy_keys, key=lambda x: (
            self.usage_stats.get(x[2], KeyUsageStats(x[2])).consecutive_failures,
            -self.usage_stats.get(x[2], KeyUsageStats(x[2])).success_rate()
        ))
        
        self.current_key_index = best_key_info[0]
        return best_key_info[1], best_key_info[2]

    def _get_env_api_key(self) -> Optional[str]:
        """从环境变量获取API密钥"""
        env_vars = ['GOOGLE_GEMINI_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_API_KEY']
        for env_var in env_vars:
            api_key = os.environ.get(env_var)
            if api_key and api_key.strip():
                logger.info(f"🔧 使用环境变量 {env_var} 中的API密钥")
                return api_key.strip()
        return None

    def rotate_to_next_key(self) -> bool:
        """
        轮换到下一个密钥
        
        Returns:
            bool: 是否成功轮换
        """
        if len(self.api_keys) <= 1:
            logger.warning("⚠️ 只有一个密钥，无法轮换")
            return False
        
        old_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        old_key_id = self._get_key_id(self.api_keys[old_index])
        new_key_id = self._get_key_id(self.api_keys[self.current_key_index])
        
        logger.info(f"🔄 API密钥轮换: {old_key_id} -> {new_key_id}")
        return True

    def record_api_call(self, key_id: str, success: bool, error_type: Optional[str] = None):
        """
        记录API调用结果
        
        Args:
            key_id: 密钥ID
            success: 是否成功
            error_type: 错误类型（如果失败）
        """
        if key_id not in self.usage_stats:
            self.usage_stats[key_id] = KeyUsageStats(key_id=key_id)
        
        stats = self.usage_stats[key_id]
        current_time = datetime.now().isoformat()
        
        # 更新基本统计
        stats.total_requests += 1
        stats.last_used = current_time
        
        if success:
            stats.successful_requests += 1
            stats.last_success = current_time
            stats.consecutive_failures = 0
            stats.current_status = KeyStatus.ACTIVE.value
        else:
            stats.failed_requests += 1
            stats.last_failure = current_time
            stats.consecutive_failures += 1
            
            # 根据错误类型更新状态
            if error_type:
                if "quota" in error_type.lower() or "exhausted" in error_type.lower():
                    stats.quota_exhausted_count += 1
                    stats.current_status = KeyStatus.QUOTA_EXHAUSTED.value
                elif "rate" in error_type.lower() or "limit" in error_type.lower():
                    stats.rate_limit_count += 1
                    stats.current_status = KeyStatus.RATE_LIMITED.value
                elif "invalid" in error_type.lower() or "unauthorized" in error_type.lower():
                    stats.current_status = KeyStatus.INVALID.value
                else:
                    stats.current_status = KeyStatus.UNKNOWN.value

        # 保存统计
        self._save_usage_stats()
        
        # 记录详细日志
        log_level = logging.INFO if success else logging.WARNING
        logger.log(log_level, 
                  f"📊 API调用记录 - 密钥: {key_id}, 成功: {success}, "
                  f"总计: {stats.total_requests}, 成功率: {stats.success_rate():.1%}, "
                  f"连续失败: {stats.consecutive_failures}")

    def get_usage_summary(self) -> Dict[str, Any]:
        """获取使用情况摘要"""
        summary = {
            "total_keys": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "current_key_id": self._get_key_id(self.api_keys[self.current_key_index]) if self.api_keys else None,
            "key_stats": {},
            "overall_stats": {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "overall_success_rate": 0.0
            }
        }
        
        total_requests = 0
        total_successful = 0
        
        for key_id, stats in self.usage_stats.items():
            summary["key_stats"][key_id] = {
                "total_requests": stats.total_requests,
                "success_rate": stats.success_rate(),
                "consecutive_failures": stats.consecutive_failures,
                "current_status": stats.current_status,
                "is_healthy": stats.is_healthy(),
                "last_used": stats.last_used,
                "last_success": stats.last_success
            }
            
            total_requests += stats.total_requests
            total_successful += stats.successful_requests
        
        summary["overall_stats"]["total_requests"] = total_requests
        summary["overall_stats"]["successful_requests"] = total_successful
        summary["overall_stats"]["failed_requests"] = total_requests - total_successful
        if total_requests > 0:
            summary["overall_stats"]["overall_success_rate"] = total_successful / total_requests
            
        return summary

    def print_usage_report(self):
        """打印使用情况报告"""
        summary = self.get_usage_summary()
        
        print("\n" + "="*60)
        print("📊 多API密钥使用情况报告")
        print("="*60)
        
        print(f"总密钥数: {summary['total_keys']}")
        print(f"当前密钥: {summary['current_key_id']}")
        print(f"整体成功率: {summary['overall_stats']['overall_success_rate']:.1%}")
        print(f"总请求数: {summary['overall_stats']['total_requests']}")
        
        print("\n密钥详情:")
        print("-" * 60)
        for key_id, stats in summary["key_stats"].items():
            status_emoji = "✅" if stats["is_healthy"] else "❌"
            print(f"{status_emoji} {key_id}:")
            print(f"   请求数: {stats['total_requests']}, 成功率: {stats['success_rate']:.1%}")
            print(f"   连续失败: {stats['consecutive_failures']}, 状态: {stats['current_status']}")
            if stats['last_used']:
                print(f"   最后使用: {stats['last_used'][:19]}")
            print()

# 创建全局实例
multi_key_manager: Optional[MultiKeyManager] = None

def get_multi_key_manager(api_keys: Optional[List[str]] = None) -> MultiKeyManager:
    """
    获取多密钥管理器实例（单例模式）
    
    Args:
        api_keys: API密钥列表（仅在首次调用时使用）
        
    Returns:
        MultiKeyManager: 多密钥管理器实例
    """
    global multi_key_manager
    if multi_key_manager is None:
        multi_key_manager = MultiKeyManager(api_keys=api_keys)
    return multi_key_manager
