#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置缓存管理模块
负责本地配置缓存、缓存过期管理、配置版本控制
"""

import json
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ConfigCache:
    """配置缓存管理器"""
    
    def __init__(self, cache_dir: Optional[Path] = None, default_ttl: int = 300):
        """
        初始化配置缓存
        
        Args:
            cache_dir: 缓存目录路径
            default_ttl: 默认缓存过期时间（秒）
        """
        self.default_ttl = default_ttl
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "cache" / "config"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}
        
        # 加载现有缓存
        self._load_cache_metadata()
    
    def _get_cache_key(self, config_type: str, params: Optional[Dict[str, Any]] = None) -> str:
        """生成缓存键"""
        if params:
            # 将参数序列化为字符串并生成哈希
            params_str = json.dumps(params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            return f"{config_type}_{params_hash}"
        return config_type
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.cache"
    
    def _get_metadata_file_path(self, cache_key: str) -> Path:
        """获取元数据文件路径"""
        return self.cache_dir / f"{cache_key}.meta"
    
    def _load_cache_metadata(self):
        """加载缓存元数据"""
        try:
            metadata_file = self.cache_dir / "cache_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self._cache_metadata = json.load(f)
            else:
                self._cache_metadata = {}
        except Exception as e:
            logger.error(f"加载缓存元数据失败: {e}")
            self._cache_metadata = {}
    
    def _save_cache_metadata(self):
        """保存缓存元数据"""
        try:
            metadata_file = self.cache_dir / "cache_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存缓存元数据失败: {e}")
    
    def _is_cache_valid(self, cache_key: str, ttl: Optional[int] = None) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._cache_metadata:
            return False
        
        metadata = self._cache_metadata[cache_key]
        cache_time = datetime.fromisoformat(metadata["created_at"])
        cache_ttl = ttl or metadata.get("ttl", self.default_ttl)
        
        return datetime.now() - cache_time < timedelta(seconds=cache_ttl)
    
    def get(self, config_type: str, params: Optional[Dict[str, Any]] = None, 
            ttl: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        获取缓存配置
        
        Args:
            config_type: 配置类型
            params: 查询参数
            ttl: 缓存过期时间
            
        Returns:
            缓存的配置数据，如果不存在或已过期则返回None
        """
        cache_key = self._get_cache_key(config_type, params)
        
        # 检查内存缓存
        if cache_key in self._memory_cache and self._is_cache_valid(cache_key, ttl):
            logger.debug(f"从内存缓存获取配置: {config_type}")
            return self._memory_cache[cache_key]
        
        # 检查文件缓存
        cache_file = self._get_cache_file_path(cache_key)
        if cache_file.exists() and self._is_cache_valid(cache_key, ttl):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # 更新内存缓存
                self._memory_cache[cache_key] = cached_data
                logger.debug(f"从文件缓存获取配置: {config_type}")
                return cached_data
            except Exception as e:
                logger.error(f"读取文件缓存失败: {e}")
                # 删除损坏的缓存文件
                self.remove(config_type, params)
        
        return None
    
    def set(self, config_type: str, data: Dict[str, Any], 
            params: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None):
        """
        设置缓存配置
        
        Args:
            config_type: 配置类型
            data: 配置数据
            params: 查询参数
            ttl: 缓存过期时间
        """
        cache_key = self._get_cache_key(config_type, params)
        cache_ttl = ttl or self.default_ttl
        
        # 更新内存缓存
        self._memory_cache[cache_key] = data
        
        # 更新元数据
        self._cache_metadata[cache_key] = {
            "config_type": config_type,
            "params": params,
            "created_at": datetime.now().isoformat(),
            "ttl": cache_ttl,
            "size": len(str(data))
        }
        
        # 保存到文件缓存
        try:
            cache_file = self._get_cache_file_path(cache_key)
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            self._save_cache_metadata()
            logger.debug(f"配置已缓存: {config_type}")
        except Exception as e:
            logger.error(f"保存文件缓存失败: {e}")
    
    def remove(self, config_type: str, params: Optional[Dict[str, Any]] = None):
        """
        删除缓存配置
        
        Args:
            config_type: 配置类型
            params: 查询参数
        """
        cache_key = self._get_cache_key(config_type, params)
        
        # 删除内存缓存
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
        
        # 删除文件缓存
        cache_file = self._get_cache_file_path(cache_key)
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"删除缓存文件失败: {e}")
        
        # 删除元数据
        if cache_key in self._cache_metadata:
            del self._cache_metadata[cache_key]
            self._save_cache_metadata()
        
        logger.debug(f"缓存已删除: {config_type}")
    
    def clear(self, config_type: Optional[str] = None):
        """
        清空缓存
        
        Args:
            config_type: 指定配置类型，如果为None则清空所有缓存
        """
        if config_type:
            # 清空指定类型的缓存
            keys_to_remove = [
                key for key in self._cache_metadata.keys()
                if self._cache_metadata[key]["config_type"] == config_type
            ]
            for key in keys_to_remove:
                self._remove_by_key(key)
        else:
            # 清空所有缓存
            keys_to_remove = list(self._cache_metadata.keys())
            for key in keys_to_remove:
                self._remove_by_key(key)
        
        logger.info(f"缓存已清空: {config_type or 'all'}")
    
    def _remove_by_key(self, cache_key: str):
        """根据缓存键删除缓存"""
        # 删除内存缓存
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
        
        # 删除文件缓存
        cache_file = self._get_cache_file_path(cache_key)
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"删除缓存文件失败: {e}")
        
        # 删除元数据
        if cache_key in self._cache_metadata:
            del self._cache_metadata[cache_key]
    
    def cleanup_expired(self):
        """清理过期缓存"""
        expired_keys = []
        current_time = datetime.now()
        
        for cache_key, metadata in self._cache_metadata.items():
            cache_time = datetime.fromisoformat(metadata["created_at"])
            cache_ttl = metadata.get("ttl", self.default_ttl)
            
            if current_time - cache_time >= timedelta(seconds=cache_ttl):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            self._remove_by_key(key)
        
        if expired_keys:
            self._save_cache_metadata()
            logger.info(f"已清理 {len(expired_keys)} 个过期缓存")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        total_size = 0
        valid_count = 0
        expired_count = 0
        
        for cache_key, metadata in self._cache_metadata.items():
            total_size += metadata.get("size", 0)
            
            if self._is_cache_valid(cache_key):
                valid_count += 1
            else:
                expired_count += 1
        
        return {
            "total_entries": len(self._cache_metadata),
            "valid_entries": valid_count,
            "expired_entries": expired_count,
            "total_size": total_size,
            "cache_dir": str(self.cache_dir),
            "default_ttl": self.default_ttl
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "by_type": {},
            "by_age": {
                "recent": 0,      # 1小时内
                "old": 0,         # 1-24小时
                "very_old": 0     # 24小时以上
            }
        }
        
        current_time = datetime.now()
        
        for cache_key, metadata in self._cache_metadata.items():
            config_type = metadata["config_type"]
            created_at = datetime.fromisoformat(metadata["created_at"])
            age_hours = (current_time - created_at).total_seconds() / 3600
            
            # 按类型统计
            if config_type not in stats["by_type"]:
                stats["by_type"][config_type] = {
                    "count": 0,
                    "size": 0,
                    "valid": 0,
                    "expired": 0
                }
            
            stats["by_type"][config_type]["count"] += 1
            stats["by_type"][config_type]["size"] += metadata.get("size", 0)
            
            if self._is_cache_valid(cache_key):
                stats["by_type"][config_type]["valid"] += 1
            else:
                stats["by_type"][config_type]["expired"] += 1
            
            # 按年龄统计
            if age_hours < 1:
                stats["by_age"]["recent"] += 1
            elif age_hours < 24:
                stats["by_age"]["old"] += 1
            else:
                stats["by_age"]["very_old"] += 1
        
        return stats


# 全局缓存实例
_config_cache: Optional[ConfigCache] = None


def get_config_cache() -> ConfigCache:
    """获取配置缓存实例"""
    global _config_cache
    if _config_cache is None:
        _config_cache = ConfigCache()
    return _config_cache


# 便捷函数
def cache_config(config_type: str, data: Dict[str, Any], 
                params: Optional[Dict[str, Any]] = None, ttl: Optional[int] = None):
    """缓存配置"""
    cache = get_config_cache()
    cache.set(config_type, data, params, ttl)


def get_cached_config(config_type: str, params: Optional[Dict[str, Any]] = None, 
                     ttl: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """获取缓存的配置"""
    cache = get_config_cache()
    return cache.get(config_type, params, ttl)


def clear_config_cache(config_type: Optional[str] = None):
    """清空配置缓存"""
    cache = get_config_cache()
    cache.clear(config_type)


def cleanup_expired_cache():
    """清理过期缓存"""
    cache = get_config_cache()
    cache.cleanup_expired()


def get_cache_info() -> Dict[str, Any]:
    """获取缓存信息"""
    cache = get_config_cache()
    return cache.get_cache_info()


def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息"""
    cache = get_config_cache()
    return cache.get_cache_stats()
