#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缩略图管理器
负责生成和管理图片缩略图
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageOps
import hashlib


class ThumbnailManager:
    """缩略图管理器"""
    
    def __init__(self, thumbnail_dir: str = "thumbnails"):
        """初始化缩略图管理器
        
        Args:
            thumbnail_dir: 缩略图存储目录
        """
        self.thumbnail_dir = Path(thumbnail_dir)
        self.thumbnail_dir.mkdir(exist_ok=True)
        
        # 缩略图尺寸配置
        self.thumbnail_sizes = {
            'small': (300, 300),    # 小缩略图，用于列表显示
            'medium': (400, 400),   # 中等缩略图，用于预览
            'large': (600, 600)     # 大缩略图，用于详情页
        }
        
        # 支持的图片格式
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}
    
    def _get_thumbnail_path(self, original_path: str, size_key: str) -> Path:
        """获取缩略图文件路径
        
        Args:
            original_path: 原图路径
            size_key: 尺寸键 (small, medium, large)
            
        Returns:
            缩略图文件路径
        """
        # 生成原图路径的哈希值作为文件名
        path_hash = hashlib.md5(str(original_path).encode()).hexdigest()
        
        # 获取原图文件扩展名
        original_ext = Path(original_path).suffix.lower()
        if original_ext not in self.supported_formats:
            original_ext = '.jpg'  # 默认使用jpg格式
        
        # 生成缩略图文件名
        thumbnail_filename = f"{path_hash}_{size_key}{original_ext}"
        
        return self.thumbnail_dir / thumbnail_filename
    
    def _is_thumbnail_valid(self, thumbnail_path: Path, original_path: str) -> bool:
        """检查缩略图是否有效
        
        Args:
            thumbnail_path: 缩略图路径
            original_path: 原图路径
            
        Returns:
            是否有效
        """
        if not thumbnail_path.exists():
            return False
        
        # 检查原图是否存在
        if not Path(original_path).exists():
            return False
        
        # 检查缩略图是否比原图新（避免原图更新后缩略图过期）
        try:
            thumbnail_mtime = thumbnail_path.stat().st_mtime
            original_mtime = Path(original_path).stat().st_mtime
            return thumbnail_mtime >= original_mtime
        except OSError:
            return False
    
    def generate_thumbnail(self, original_path: str, size_key: str = 'small', 
                          quality: int = 85) -> Optional[Path]:
        """生成缩略图
        
        Args:
            original_path: 原图路径
            size_key: 尺寸键 (small, medium, large)
            quality: JPEG质量 (1-100)
            
        Returns:
            缩略图路径，失败返回None
        """
        try:
            original_path = Path(original_path)
            
            # 检查原图是否存在
            if not original_path.exists():
                print(f"❌ 原图不存在: {original_path}")
                return None
            
            # 检查文件格式
            if original_path.suffix.lower() not in self.supported_formats:
                print(f"❌ 不支持的图片格式: {original_path.suffix}")
                return None
            
            # 获取目标尺寸
            if size_key not in self.thumbnail_sizes:
                print(f"❌ 无效的尺寸键: {size_key}")
                return None
            
            target_size = self.thumbnail_sizes[size_key]
            thumbnail_path = self._get_thumbnail_path(str(original_path), size_key)
            
            # 检查缩略图是否已存在且有效
            if self._is_thumbnail_valid(thumbnail_path, str(original_path)):
                print(f"✅ 缩略图已存在: {thumbnail_path}")
                return thumbnail_path
            
            # 打开原图
            with Image.open(original_path) as img:
                # 转换为RGB模式（处理RGBA等格式）
                if img.mode in ('RGBA', 'LA', 'P'):
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 生成缩略图（保持宽高比）
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # 如果图片尺寸小于目标尺寸，居中放置
                if img.size[0] < target_size[0] or img.size[1] < target_size[1]:
                    # 创建目标尺寸的白色背景
                    final_img = Image.new('RGB', target_size, (255, 255, 255))
                    
                    # 计算居中位置
                    x = (target_size[0] - img.size[0]) // 2
                    y = (target_size[1] - img.size[1]) // 2
                    
                    # 粘贴图片到中心
                    final_img.paste(img, (x, y))
                    img = final_img
                
                # 保存缩略图
                save_kwargs = {'optimize': True}
                if thumbnail_path.suffix.lower() in ['.jpg', '.jpeg']:
                    save_kwargs['quality'] = quality
                
                img.save(thumbnail_path, **save_kwargs)
                
                print(f"✅ 缩略图生成成功: {thumbnail_path}")
                return thumbnail_path
                
        except Exception as e:
            print(f"❌ 生成缩略图失败: {e}")
            return None
    
    def get_thumbnail_url(self, original_path: str, size_key: str = 'small') -> Optional[str]:
        """获取缩略图URL
        
        Args:
            original_path: 原图路径
            size_key: 尺寸键 (small, medium, large)
            
        Returns:
            缩略图URL，失败返回None
        """
        thumbnail_path = self.generate_thumbnail(original_path, size_key)
        if thumbnail_path:
            # 返回相对于项目根目录的路径
            return f"/api/thumbnail/{thumbnail_path.name}"
        return None
    
    def get_thumbnail_path(self, original_path: str, size_key: str = 'small') -> Optional[Path]:
        """获取缩略图文件路径
        
        Args:
            original_path: 原图路径
            size_key: 尺寸键 (small, medium, large)
            
        Returns:
            缩略图文件路径，失败返回None
        """
        thumbnail_path = self._get_thumbnail_path(original_path, size_key)
        if self._is_thumbnail_valid(thumbnail_path, original_path):
            return thumbnail_path
        return self.generate_thumbnail(original_path, size_key)
    
    def delete_thumbnail(self, original_path: str) -> bool:
        """删除原图对应的所有缩略图
        
        Args:
            original_path: 原图路径
            
        Returns:
            是否成功删除
        """
        try:
            deleted_count = 0
            for size_key in self.thumbnail_sizes.keys():
                thumbnail_path = self._get_thumbnail_path(original_path, size_key)
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
                    deleted_count += 1
            
            print(f"✅ 删除缩略图: {deleted_count} 个")
            return True
            
        except Exception as e:
            print(f"❌ 删除缩略图失败: {e}")
            return False
    
    def cleanup_orphaned_thumbnails(self) -> int:
        """清理孤立的缩略图（原图已删除但缩略图仍存在）
        
        Returns:
            清理的缩略图数量
        """
        try:
            cleaned_count = 0
            
            for thumbnail_file in self.thumbnail_dir.iterdir():
                if thumbnail_file.is_file():
                    # 从文件名中提取原图哈希
                    filename = thumbnail_file.stem
                    if '_' in filename:
                        original_hash = filename.split('_')[0]
                        
                        # 检查是否有对应的原图存在
                        found_original = False
                        for original_file in Path('.').rglob('*'):
                            if (original_file.is_file() and 
                                original_file.suffix.lower() in self.supported_formats and
                                hashlib.md5(str(original_file).encode()).hexdigest() == original_hash):
                                found_original = True
                                break
                        
                        if not found_original:
                            thumbnail_file.unlink()
                            cleaned_count += 1
            
            print(f"✅ 清理孤立缩略图: {cleaned_count} 个")
            return cleaned_count
            
        except Exception as e:
            print(f"❌ 清理孤立缩略图失败: {e}")
            return 0


# 全局缩略图管理器实例
_thumbnail_manager = None

def get_thumbnail_manager() -> ThumbnailManager:
    """获取缩略图管理器实例（单例模式）"""
    global _thumbnail_manager
    if _thumbnail_manager is None:
        _thumbnail_manager = ThumbnailManager()
    return _thumbnail_manager
