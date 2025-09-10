#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis缓存管理器
负责缓存历史记录、任务状态、图片元数据等
"""

import json
import os
import redis
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta


class CacheManager:
    """Redis缓存管理器"""
    
    def __init__(self):
        """初始化缓存管理器"""
        self.redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        if self.redis_enabled:
            try:
                self.redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
                # 测试连接
                self.redis.ping()
                print("✅ Redis连接成功")
            except Exception as e:
                print(f"❌ Redis连接失败: {e}")
                self.redis_enabled = False
                self.redis = None
        else:
            print("ℹ️ Redis缓存已禁用")
            self.redis = None
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        return f"yeepay:{prefix}:{':'.join(str(arg) for arg in args)}"
    
    def _serialize_data(self, data: Any) -> str:
        """序列化数据"""
        return json.dumps(data, ensure_ascii=False, default=str)
    
    def _deserialize_data(self, data: str) -> Any:
        """反序列化数据"""
        return json.loads(data) if data else None
    
    # =============================================================================
    # 历史记录缓存
    # =============================================================================
    
    def get_history_cache(self, limit: int, offset: int, order: str, 
                        favorite_filter: str = None, time_filter: str = None) -> Optional[Dict]:
        """获取历史记录缓存"""
        if not self.redis_enabled:
            return None
        
        cache_key = self._get_cache_key(
            "history", limit, offset, order, 
            favorite_filter or "all", time_filter or "all"
        )
        
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                print(f"🎯 缓存命中: {cache_key}")
                return self._deserialize_data(cached_data)
        except Exception as e:
            print(f"❌ 获取历史记录缓存失败: {e}")
        
        return None
    
    def set_history_cache(self, data: Dict, limit: int, offset: int, order: str,
                         favorite_filter: str = None, time_filter: str = None, ttl: int = 300):
        """设置历史记录缓存"""
        if not self.redis_enabled:
            return
        
        cache_key = self._get_cache_key(
            "history", limit, offset, order,
            favorite_filter or "all", time_filter or "all"
        )
        
        try:
            serialized_data = self._serialize_data(data)
            self.redis.setex(cache_key, ttl, serialized_data)
            print(f"💾 历史记录已缓存: {cache_key} (TTL: {ttl}s)")
        except Exception as e:
            print(f"❌ 设置历史记录缓存失败: {e}")
    
    def invalidate_history_cache(self):
        """清除所有历史记录缓存"""
        if not self.redis_enabled:
            return
        
        try:
            pattern = self._get_cache_key("history", "*")
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                print(f"🗑️ 清除历史记录缓存: {len(keys)} 个键")
        except Exception as e:
            print(f"❌ 清除历史记录缓存失败: {e}")
    
    # =============================================================================
    # 任务状态缓存
    # =============================================================================
    
    def get_task_cache(self, task_id: str) -> Optional[Dict]:
        """获取任务状态缓存"""
        if not self.redis_enabled:
            return None
        
        cache_key = self._get_cache_key("task", task_id)
        
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                print(f"🎯 任务缓存命中: {task_id}")
                return self._deserialize_data(cached_data)
        except Exception as e:
            print(f"❌ 获取任务缓存失败: {e}")
        
        return None
    
    def set_task_cache(self, task_id: str, data: Dict, ttl: int = 600):
        """设置任务状态缓存"""
        if not self.redis_enabled:
            return
        
        cache_key = self._get_cache_key("task", task_id)
        
        try:
            serialized_data = self._serialize_data(data)
            self.redis.setex(cache_key, ttl, serialized_data)
            print(f"💾 任务状态已缓存: {task_id} (TTL: {ttl}s)")
        except Exception as e:
            print(f"❌ 设置任务缓存失败: {e}")
    
    def invalidate_task_cache(self, task_id: str):
        """清除任务缓存"""
        if not self.redis_enabled:
            return
        
        cache_key = self._get_cache_key("task", task_id)
        
        try:
            self.redis.delete(cache_key)
            print(f"🗑️ 清除任务缓存: {task_id}")
        except Exception as e:
            print(f"❌ 清除任务缓存失败: {e}")
    
    # =============================================================================
    # 图片元数据缓存
    # =============================================================================
    
    def get_image_metadata_cache(self, task_id: str, filename: str = None) -> Optional[Dict]:
        """获取图片元数据缓存"""
        if not self.redis_enabled:
            return None
        
        cache_key = self._get_cache_key("image_meta", task_id, filename or "default")
        
        try:
            cached_data = self.redis.get(cache_key)
            if cached_data:
                print(f"🎯 图片元数据缓存命中: {task_id}")
                return self._deserialize_data(cached_data)
        except Exception as e:
            print(f"❌ 获取图片元数据缓存失败: {e}")
        
        return None
    
    def set_image_metadata_cache(self, task_id: str, data: Dict, filename: str = None, ttl: int = 3600):
        """设置图片元数据缓存"""
        if not self.redis_enabled:
            return
        
        cache_key = self._get_cache_key("image_meta", task_id, filename or "default")
        
        try:
            serialized_data = self._serialize_data(data)
            self.redis.setex(cache_key, ttl, serialized_data)
            print(f"💾 图片元数据已缓存: {task_id} (TTL: {ttl}s)")
        except Exception as e:
            print(f"❌ 设置图片元数据缓存失败: {e}")
    
    def invalidate_image_cache(self, task_id: str):
        """清除图片相关缓存"""
        if not self.redis_enabled:
            return
        
        try:
            # 清除图片元数据缓存
            pattern = self._get_cache_key("image_meta", task_id, "*")
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                print(f"🗑️ 清除图片缓存: {len(keys)} 个键")
        except Exception as e:
            print(f"❌ 清除图片缓存失败: {e}")
    
    # =============================================================================
    # 通用缓存操作
    # =============================================================================
    
    def clear_all_cache(self):
        """清除所有缓存"""
        if not self.redis_enabled:
            return
        
        try:
            pattern = self._get_cache_key("*")
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                print(f"🗑️ 清除所有缓存: {len(keys)} 个键")
        except Exception as e:
            print(f"❌ 清除所有缓存失败: {e}")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        if not self.redis_enabled:
            return {"enabled": False}
        
        try:
            info = self.redis.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "used_memory_peak": info.get("used_memory_peak_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0)
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}


# 全局缓存管理器实例
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """获取缓存管理器实例（单例模式）"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
