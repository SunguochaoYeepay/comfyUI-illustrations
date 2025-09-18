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
    
    async def get_supported_ratios(self) -> List[Dict[str, Any]]:
        """获取支持的尺寸比例"""
        try:
            config = await self.get_image_gen_config()
            size_ratios = config.get("size_ratios", [])
            
            # 默认尺寸映射
            default_sizes = {
                '1:1': {'width': 1024, 'height': 1024},
                '4:3': {'width': 1024, 'height': 768},
                '3:4': {'width': 768, 'height': 1024},
                '16:9': {'width': 1024, 'height': 576},
                '9:16': {'width': 576, 'height': 1024},
                '21:9': {'width': 1024, 'height': 439},
                '3:2': {'width': 1024, 'height': 683},
                '2:3': {'width': 683, 'height': 1024}
            }
            
            # 如果size_ratios为空，尝试从supported_ratios获取
            if not size_ratios:
                supported_ratios = config.get("supported_ratios", ["1:1", "4:3", "3:4", "16:9", "9:16"])
                size_ratios = supported_ratios
            
            # 统一处理：将字符串数组转换为对象数组
            result_ratios = []
            for ratio in size_ratios:
                if isinstance(ratio, str):
                    # 字符串格式，需要转换为对象
                    default_size = default_sizes.get(ratio, {'width': 1024, 'height': 1024})
                    result_ratios.append({
                        'ratio': ratio,
                        'width': default_size['width'],
                        'height': default_size['height'],
                        'description': ''
                    })
                elif isinstance(ratio, dict) and 'ratio' in ratio:
                    # 已经是对象格式，直接使用
                    result_ratios.append(ratio)
            
            return result_ratios
        except Exception as e:
            logger.error(f"获取支持的尺寸比例失败: {e}")
            # 返回默认配置
            return [
                {'ratio': '1:1', 'width': 1024, 'height': 1024, 'description': ''},
                {'ratio': '4:3', 'width': 1024, 'height': 768, 'description': ''},
                {'ratio': '3:4', 'width': 768, 'height': 1024, 'description': ''},
                {'ratio': '16:9', 'width': 1024, 'height': 576, 'description': ''},
                {'ratio': '9:16', 'width': 576, 'height': 1024, 'description': ''}
            ]
    
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
    
    async def get_optimal_size(self, requested_size: str, model_name: str) -> Tuple[int, int]:
        """获取最优尺寸"""
        try:
            # 解析请求的尺寸
            width, height = self.parse_size_string(requested_size)
            
            # 验证尺寸
            if not await self.validate_image_size(width, height):
                # 如果尺寸无效，使用默认尺寸
                return await self.get_default_image_size()
            
            # 根据模型调整尺寸
            if model_name == "flux-dev":
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
            supported_ratios = await self.get_supported_ratios()
            
            return {
                "default_size": {
                    "width": default_width,
                    "height": default_height,
                    "string": self.format_size_string(default_width, default_height)
                },
                "default_steps": await self.get_default_steps(),
                "default_count": await self.get_default_count(),
                "supported_ratios": supported_ratios,  # 现在是对象数组
                "size_ratios": supported_ratios,  # 添加size_ratios字段，与supported_ratios保持一致
                "supported_formats": await self.get_supported_formats(),
                "quality_settings": await self.get_quality_settings(),
                "base_model_order": config.get("base_model_order", []),  # 添加基础模型顺序
                "lora_order": config.get("lora_order", {}),  # 添加LoRA排序配置
                "config_source": config.get("config_source", "unknown"),
                "last_updated": config.get("last_updated", "unknown")
            }
        except Exception as e:
            logger.error(f"获取配置摘要失败: {e}")
            return {
                "default_size": {"width": 1024, "height": 1024, "string": "1024x1024"},
                "default_steps": 20,
                "default_count": 1,
                "supported_ratios": [
                    {'ratio': '1:1', 'width': 1024, 'height': 1024, 'description': ''},
                    {'ratio': '4:3', 'width': 1024, 'height': 768, 'description': ''},
                    {'ratio': '3:4', 'width': 768, 'height': 1024, 'description': ''},
                    {'ratio': '16:9', 'width': 1024, 'height': 576, 'description': ''},
                    {'ratio': '9:16', 'width': 576, 'height': 1024, 'description': ''}
                ],
                "size_ratios": [
                    {'ratio': '1:1', 'width': 1024, 'height': 1024, 'description': ''},
                    {'ratio': '4:3', 'width': 1024, 'height': 768, 'description': ''},
                    {'ratio': '3:4', 'width': 768, 'height': 1024, 'description': ''},
                    {'ratio': '16:9', 'width': 1024, 'height': 576, 'description': ''},
                    {'ratio': '9:16', 'width': 576, 'height': 1024, 'description': ''}
                ],
                "supported_formats": ["png", "jpg", "jpeg", "webp"],
                "quality_settings": {
                    "low": {"steps": 10, "cfg": 7.0},
                    "medium": {"steps": 20, "cfg": 8.0},
                    "high": {"steps": 30, "cfg": 9.0}
                },
                "base_model_order": [],
                "lora_order": {},
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


async def get_optimal_size(requested_size: str, model_name: str) -> Tuple[int, int]:
    """获取最优尺寸"""
    manager = get_image_gen_config_manager()
    return await manager.get_optimal_size(requested_size, model_name)


async def get_image_gen_config_summary() -> Dict[str, Any]:
    """获取生图配置摘要"""
    manager = get_image_gen_config_manager()
    return await manager.get_config_summary()
