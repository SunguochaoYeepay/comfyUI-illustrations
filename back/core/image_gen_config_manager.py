#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生图配置管理器
负责集成生图配置到主服务，支持动态默认参数
"""

import os
import asyncio
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ImageGenConfigManager:
    """生图配置管理器"""
    
    def __init__(self):
        """初始化生图配置管理器"""
        self._config_client = None
        self._default_config = self._get_default_config()
    
    def _get_config_client(self):
        """获取配置客户端"""
        if self._config_client is None:
            try:
                from core.config_client import get_config_client
                self._config_client = get_config_client()
            except ImportError:
                return None
        return self._config_client
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认生图配置"""
        return {
            "default_size": {"width": 1024, "height": 1024},
            "size_ratios": ["1:1", "4:3", "3:4", "16:9", "9:16"],
            "default_steps": 20,
            "default_count": 1,
            "supported_formats": ["png", "jpg", "jpeg", "webp"],
            "quality_settings": {
                "low": {"steps": 10, "cfg": 7.0},
                "medium": {"steps": 20, "cfg": 8.0},
                "high": {"steps": 30, "cfg": 9.0}
            },
            "config_source": "default"
        }
    
    async def get_image_gen_config(self) -> Dict[str, Any]:
        """获取生图配置"""
        try:
            config_client = self._get_config_client()
            if config_client:
                config = await config_client.get_image_gen_config()
                return config
            else:
                # 配置客户端不可用，使用默认配置
                return self._default_config
        except Exception as e:
            logger.error(f"获取生图配置失败: {e}")
            return self._default_config
    
    async def get_default_image_size(self) -> Tuple[int, int]:
        """获取默认图像尺寸"""
        try:
            config = await self.get_image_gen_config()
            default_size = config.get("default_size", {"width": 1024, "height": 1024})
            return default_size.get("width", 1024), default_size.get("height", 1024)
        except Exception as e:
            logger.error(f"获取默认图像尺寸失败: {e}")
            return 1024, 1024
    
    async def get_default_steps(self) -> int:
        """获取默认步数"""
        try:
            config = await self.get_image_gen_config()
            return config.get("default_steps", 20)
        except Exception as e:
            logger.error(f"获取默认步数失败: {e}")
            return 20
    
    async def get_default_count(self) -> int:
        """获取默认数量"""
        try:
            config = await self.get_image_gen_config()
            return config.get("default_count", 1)
        except Exception as e:
            logger.error(f"获取默认数量失败: {e}")
            return 1
    
    async def get_supported_ratios(self) -> List[str]:
        """获取支持的尺寸比例"""
        try:
            config = await self.get_image_gen_config()
            return config.get("size_ratios", ["1:1", "4:3", "3:4", "16:9", "9:16"])
        except Exception as e:
            logger.error(f"获取支持的尺寸比例失败: {e}")
            return ["1:1", "4:3", "3:4", "16:9", "9:16"]
    
    async def get_supported_formats(self) -> List[str]:
        """获取支持的图像格式"""
        try:
            config = await self.get_image_gen_config()
            return config.get("supported_formats", ["png", "jpg", "jpeg", "webp"])
        except Exception as e:
            logger.error(f"获取支持的图像格式失败: {e}")
            return ["png", "jpg", "jpeg", "webp"]
    
    async def get_quality_settings(self) -> Dict[str, Dict[str, Any]]:
        """获取质量设置"""
        try:
            config = await self.get_image_gen_config()
            return config.get("quality_settings", {
                "low": {"steps": 10, "cfg": 7.0},
                "medium": {"steps": 20, "cfg": 8.0},
                "high": {"steps": 30, "cfg": 9.0}
            })
        except Exception as e:
            logger.error(f"获取质量设置失败: {e}")
            return {
                "low": {"steps": 10, "cfg": 7.0},
                "medium": {"steps": 20, "cfg": 8.0},
                "high": {"steps": 30, "cfg": 9.0}
            }
    
    def parse_size_string(self, size_str: str) -> Tuple[int, int]:
        """解析尺寸字符串"""
        try:
            if "x" in size_str:
                width, height = size_str.split("x")
                return int(width), int(height)
            else:
                # 默认返回1024x1024
                return 1024, 1024
        except Exception as e:
            logger.error(f"解析尺寸字符串失败: {size_str}, 错误: {e}")
            return 1024, 1024
    
    def format_size_string(self, width: int, height: int) -> str:
        """格式化尺寸字符串"""
        return f"{width}x{height}"
    
    async def get_size_from_ratio(self, ratio: str, base_size: int = 1024) -> Tuple[int, int]:
        """根据比例获取尺寸"""
        try:
            if ":" in ratio:
                w_ratio, h_ratio = ratio.split(":")
                w_ratio, h_ratio = int(w_ratio), int(h_ratio)
                
                # 计算尺寸
                if w_ratio >= h_ratio:
                    width = base_size
                    height = int(base_size * h_ratio / w_ratio)
                else:
                    height = base_size
                    width = int(base_size * w_ratio / h_ratio)
                
                return width, height
            else:
                return base_size, base_size
        except Exception as e:
            logger.error(f"根据比例获取尺寸失败: {ratio}, 错误: {e}")
            return base_size, base_size
    
    async def validate_image_size(self, width: int, height: int) -> bool:
        """验证图像尺寸是否有效"""
        try:
            # 基本验证
            if width <= 0 or height <= 0:
                return False
            
            # 最大尺寸限制
            max_size = 2048
            if width > max_size or height > max_size:
                return False
            
            # 最小尺寸限制
            min_size = 64
            if width < min_size or height < min_size:
                return False
            
            return True
        except Exception as e:
            logger.error(f"验证图像尺寸失败: {e}")
            return False
    
    async def get_optimal_size(self, requested_size: str, model_name: str = "flux1-dev") -> Tuple[int, int]:
        """获取最优尺寸"""
        try:
            # 解析请求的尺寸
            width, height = self.parse_size_string(requested_size)
            
            # 验证尺寸
            if not await self.validate_image_size(width, height):
                # 如果尺寸无效，使用默认尺寸
                return await self.get_default_image_size()
            
            # 根据模型调整尺寸
            if model_name == "flux1-dev" or model_name == "flux1":
                # Flux模型通常支持更大的尺寸
                max_size = 1536
                if width > max_size:
                    width = max_size
                if height > max_size:
                    height = max_size
            elif model_name == "qwen-image":
                # Qwen模型支持自定义尺寸，但需要确保是64的倍数
                width = (width // 64) * 64
                height = (height // 64) * 64
                # 确保最小尺寸
                if width < 64:
                    width = 64
                if height < 64:
                    height = 64
            
            return width, height
        except Exception as e:
            logger.error(f"获取最优尺寸失败: {e}")
            return await self.get_default_image_size()
    
    async def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        try:
            config = await self.get_image_gen_config()
            default_width, default_height = await self.get_default_image_size()
            
            return {
                "default_size": {
                    "width": default_width,
                    "height": default_height,
                    "string": self.format_size_string(default_width, default_height)
                },
                "default_steps": await self.get_default_steps(),
                "default_count": await self.get_default_count(),
                "supported_ratios": await self.get_supported_ratios(),
                "supported_formats": await self.get_supported_formats(),
                "quality_settings": await self.get_quality_settings(),
                "config_source": config.get("config_source", "unknown"),
                "last_updated": config.get("last_updated", "unknown")
            }
        except Exception as e:
            logger.error(f"获取配置摘要失败: {e}")
            return {
                "default_size": {"width": 1024, "height": 1024, "string": "1024x1024"},
                "default_steps": 20,
                "default_count": 1,
                "supported_ratios": ["1:1", "4:3", "3:4", "16:9", "9:16"],
                "supported_formats": ["png", "jpg", "jpeg", "webp"],
                "quality_settings": {
                    "low": {"steps": 10, "cfg": 7.0},
                    "medium": {"steps": 20, "cfg": 8.0},
                    "high": {"steps": 30, "cfg": 9.0}
                },
                "config_source": "error",
                "error": str(e)
            }


# 全局生图配置管理器实例
_image_gen_config_manager: Optional[ImageGenConfigManager] = None


def get_image_gen_config_manager() -> ImageGenConfigManager:
    """获取生图配置管理器实例"""
    global _image_gen_config_manager
    if _image_gen_config_manager is None:
        _image_gen_config_manager = ImageGenConfigManager()
    return _image_gen_config_manager


# 便捷函数
async def get_default_image_size() -> Tuple[int, int]:
    """获取默认图像尺寸"""
    manager = get_image_gen_config_manager()
    return await manager.get_default_image_size()


async def get_default_steps() -> int:
    """获取默认步数"""
    manager = get_image_gen_config_manager()
    return await manager.get_default_steps()


async def get_default_count() -> int:
    """获取默认数量"""
    manager = get_image_gen_config_manager()
    return await manager.get_default_count()


async def get_supported_ratios() -> List[str]:
    """获取支持的尺寸比例"""
    manager = get_image_gen_config_manager()
    return await manager.get_supported_ratios()


async def get_supported_formats() -> List[str]:
    """获取支持的图像格式"""
    manager = get_image_gen_config_manager()
    return await manager.get_supported_formats()


async def get_quality_settings() -> Dict[str, Dict[str, Any]]:
    """获取质量设置"""
    manager = get_image_gen_config_manager()
    return await manager.get_quality_settings()


async def get_optimal_size(requested_size: str, model_name: str = "flux1-dev") -> Tuple[int, int]:
    """获取最优尺寸"""
    manager = get_image_gen_config_manager()
    return await manager.get_optimal_size(requested_size, model_name)


async def get_image_gen_config_summary() -> Dict[str, Any]:
    """获取生图配置摘要"""
    manager = get_image_gen_config_manager()
    return await manager.get_config_summary()
