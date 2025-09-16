#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尺寸配置管理器
负责管理图像尺寸配置，支持比例选择和自定义尺寸
"""

import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SizeInfo:
    """尺寸信息"""
    name: str
    width: int
    height: int
    pixels: int
    ratio: str
    is_default: bool = False


@dataclass
class RatioInfo:
    """比例信息"""
    ratio: str
    name: str
    description: str
    sizes: List[SizeInfo]


class SizeConfigManager:
    """尺寸配置管理器"""
    
    def __init__(self):
        self.size_mappings = self._load_size_mappings()
        self.model_size_limits = self._load_model_size_limits()
    
    def get_available_ratios(self) -> List[RatioInfo]:
        """获取可用的比例"""
        ratios = []
        for ratio, sizes in self.size_mappings.items():
            ratio_info = RatioInfo(
                ratio=ratio,
                name=self._get_ratio_name(ratio),
                description=self._get_ratio_description(ratio),
                sizes=[SizeInfo(ratio=ratio, **size) for size in sizes]
            )
            ratios.append(ratio_info)
        return ratios
    
    def get_sizes_by_ratio(self, ratio: str) -> List[SizeInfo]:
        """根据比例获取可用尺寸"""
        if ratio not in self.size_mappings:
            return []
        
        return [SizeInfo(ratio=ratio, **size) for size in self.size_mappings[ratio]]
    
    def get_size_info(self, width: int, height: int) -> SizeInfo:
        """获取尺寸信息"""
        pixels = width * height
        ratio = self._calculate_ratio(width, height)
        
        return SizeInfo(
            name=f"{width}x{height}",
            width=width,
            height=height,
            pixels=pixels,
            ratio=ratio
        )
    
    def validate_size(self, width: int, height: int, model_type: str = None) -> Tuple[bool, str]:
        """验证尺寸是否有效"""
        # 基础验证
        if width < 64 or width > 2048:
            return False, "宽度必须在64-2048之间"
        
        if height < 64 or height > 2048:
            return False, "高度必须在64-2048之间"
        
        # 检查是否为64的倍数
        if width % 64 != 0 or height % 64 != 0:
            return False, "尺寸必须是64的倍数"
        
        # 检查像素总数限制
        pixels = width * height
        if pixels > 2097152:  # 2M像素
            return False, "像素总数不能超过2,097,152"
        
        # 模型特定验证
        if model_type:
            model_limits = self.model_size_limits.get(model_type, {})
            max_width = model_limits.get("max_width", 2048)
            max_height = model_limits.get("max_height", 2048)
            max_pixels = model_limits.get("max_pixels", 2097152)
            
            if width > max_width:
                return False, f"{model_type}模型最大宽度为{max_width}"
            
            if height > max_height:
                return False, f"{model_type}模型最大高度为{max_height}"
            
            if pixels > max_pixels:
                return False, f"{model_type}模型最大像素数为{max_pixels}"
        
        return True, "尺寸有效"
    
    def get_recommended_sizes(self, model_type: str = None, ratio: str = None) -> List[SizeInfo]:
        """获取推荐尺寸"""
        recommended = []
        
        if ratio:
            # 根据比例获取尺寸
            sizes = self.get_sizes_by_ratio(ratio)
        else:
            # 获取所有尺寸
            all_sizes = []
            for ratio_sizes in self.size_mappings.values():
                all_sizes.extend([SizeInfo(ratio=self._calculate_ratio(size["width"], size["height"]), **size) for size in ratio_sizes])
            sizes = all_sizes
        
        # 根据模型类型过滤
        if model_type:
            model_limits = self.model_size_limits.get(model_type, {})
            max_pixels = model_limits.get("max_pixels", 2097152)
            sizes = [size for size in sizes if size.pixels <= max_pixels]
        
        # 按像素数排序
        sizes.sort(key=lambda x: x.pixels)
        
        return sizes
    
    def get_default_size(self, model_type: str = None, ratio: str = "1:1") -> SizeInfo:
        """获取默认尺寸"""
        sizes = self.get_sizes_by_ratio(ratio)
        
        if model_type:
            model_limits = self.model_size_limits.get(model_type, {})
            max_pixels = model_limits.get("max_pixels", 2097152)
            sizes = [size for size in sizes if size.pixels <= max_pixels]
        
        # 返回第一个尺寸作为默认
        if sizes:
            return sizes[0]
        
        # 如果没有找到，返回1024x1024
        return SizeInfo(
            name="1024x1024",
            width=1024,
            height=1024,
            pixels=1048576,
            ratio="1:1"
        )
    
    def format_pixels(self, pixels: int) -> str:
        """格式化像素数显示"""
        if pixels >= 1000000:
            return f"{pixels / 1000000:.1f}M"
        elif pixels >= 1000:
            return f"{pixels / 1000:.0f}K"
        else:
            return str(pixels)
    
    def get_size_suggestions(self, current_width: int, current_height: int, model_type: str = None) -> List[SizeInfo]:
        """获取尺寸建议"""
        current_pixels = current_width * current_height
        suggestions = []
        
        # 获取所有可用尺寸
        all_sizes = []
        for ratio_sizes in self.size_mappings.values():
            all_sizes.extend([SizeInfo(ratio=self._calculate_ratio(size["width"], size["height"]), **size) for size in ratio_sizes])
        
        # 根据模型类型过滤
        if model_type:
            model_limits = self.model_size_limits.get(model_type, {})
            max_pixels = model_limits.get("max_pixels", 2097152)
            all_sizes = [size for size in all_sizes if size.pixels <= max_pixels]
        
        # 按像素数接近程度排序
        all_sizes.sort(key=lambda x: abs(x.pixels - current_pixels))
        
        # 返回前5个最接近的尺寸
        return all_sizes[:5]
    
    def _load_size_mappings(self) -> Dict[str, List[Dict]]:
        """加载尺寸映射配置"""
        return {
            "1:1": [
                {"name": "512x512", "width": 512, "height": 512, "pixels": 262144, "is_default": False},
                {"name": "768x768", "width": 768, "height": 768, "pixels": 589824, "is_default": False},
                {"name": "1024x1024", "width": 1024, "height": 1024, "pixels": 1048576, "is_default": True},
                {"name": "1152x1152", "width": 1152, "height": 1152, "pixels": 1327104, "is_default": False}
            ],
            "3:4": [
                {"name": "768x1024", "width": 768, "height": 1024, "pixels": 786432, "is_default": True},
                {"name": "1152x1536", "width": 1152, "height": 1536, "pixels": 1769472, "is_default": False}
            ],
            "4:3": [
                {"name": "1024x768", "width": 1024, "height": 768, "pixels": 786432, "is_default": True},
                {"name": "1536x1152", "width": 1536, "height": 1152, "pixels": 1769472, "is_default": False}
            ],
            "16:9": [
                {"name": "1024x576", "width": 1024, "height": 576, "pixels": 589824, "is_default": True},
                {"name": "1536x864", "width": 1536, "height": 864, "pixels": 1327104, "is_default": False}
            ],
            "9:16": [
                {"name": "576x1024", "width": 576, "height": 1024, "pixels": 589824, "is_default": True},
                {"name": "864x1536", "width": 864, "height": 1536, "pixels": 1327104, "is_default": False}
            ],
            "2:3": [
                {"name": "512x768", "width": 512, "height": 768, "pixels": 393216, "is_default": True},
                {"name": "768x1152", "width": 768, "height": 1152, "pixels": 884736, "is_default": False}
            ],
            "3:2": [
                {"name": "768x512", "width": 768, "height": 512, "pixels": 393216, "is_default": True},
                {"name": "1152x768", "width": 1152, "height": 768, "pixels": 884736, "is_default": False}
            ]
        }
    
    def _load_model_size_limits(self) -> Dict[str, Dict[str, int]]:
        """加载模型尺寸限制"""
        return {
            "qwen": {
                "max_width": 2048,
                "max_height": 2048,
                "max_pixels": 2097152,
                "recommended_width": 1024,
                "recommended_height": 1024
            },
            "flux": {
                "max_width": 2048,
                "max_height": 2048,
                "max_pixels": 2097152,
                "recommended_width": 1024,
                "recommended_height": 1024
            },
            "wan": {
                "max_width": 1024,
                "max_height": 1024,
                "max_pixels": 1048576,
                "recommended_width": 512,
                "recommended_height": 512
            }
        }
    
    def _calculate_ratio(self, width: int, height: int) -> str:
        """计算比例"""
        # 计算最大公约数
        gcd_value = math.gcd(width, height)
        w_ratio = width // gcd_value
        h_ratio = height // gcd_value
        
        return f"{w_ratio}:{h_ratio}"
    
    def _get_ratio_name(self, ratio: str) -> str:
        """获取比例名称"""
        ratio_names = {
            "1:1": "正方形",
            "3:4": "竖屏",
            "4:3": "横屏",
            "16:9": "宽屏",
            "9:16": "竖屏",
            "2:3": "竖屏",
            "3:2": "横屏"
        }
        return ratio_names.get(ratio, ratio)
    
    def _get_ratio_description(self, ratio: str) -> str:
        """获取比例描述"""
        ratio_descriptions = {
            "1:1": "正方形比例，适合头像、图标等",
            "3:4": "竖屏比例，适合手机壁纸、海报等",
            "4:3": "横屏比例，适合传统照片、展示图等",
            "16:9": "宽屏比例，适合电脑壁纸、横幅等",
            "9:16": "竖屏比例，适合手机壁纸、短视频等",
            "2:3": "竖屏比例，适合手机壁纸、海报等",
            "3:2": "横屏比例，适合传统照片、展示图等"
        }
        return ratio_descriptions.get(ratio, f"{ratio}比例")
    
    def get_ratio_by_size(self, width: int, height: int) -> str:
        """根据尺寸获取比例"""
        return self._calculate_ratio(width, height)
    
    def is_standard_size(self, width: int, height: int) -> bool:
        """判断是否为标准尺寸"""
        for ratio_sizes in self.size_mappings.values():
            for size in ratio_sizes:
                if size["width"] == width and size["height"] == height:
                    return True
        return False
    
    def get_closest_standard_size(self, width: int, height: int) -> Optional[SizeInfo]:
        """获取最接近的标准尺寸"""
        current_pixels = width * height
        closest_size = None
        min_diff = float('inf')
        
        for ratio_sizes in self.size_mappings.values():
            for size in ratio_sizes:
                diff = abs(size["pixels"] - current_pixels)
                if diff < min_diff:
                    min_diff = diff
                    closest_size = SizeInfo(ratio=self._calculate_ratio(size["width"], size["height"]), **size)
        
        return closest_size
    
    def get_size_statistics(self) -> Dict[str, any]:
        """获取尺寸统计信息"""
        total_sizes = 0
        total_pixels = 0
        ratio_counts = {}
        
        for ratio, sizes in self.size_mappings.items():
            ratio_counts[ratio] = len(sizes)
            total_sizes += len(sizes)
            for size in sizes:
                total_pixels += size["pixels"]
        
        return {
            "total_ratios": len(self.size_mappings),
            "total_sizes": total_sizes,
            "ratio_counts": ratio_counts,
            "average_pixels": total_pixels / total_sizes if total_sizes > 0 else 0
        }
