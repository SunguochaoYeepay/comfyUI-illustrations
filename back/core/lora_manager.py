#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoRA管理器
负责从配置客户端获取LoRA配置，支持LoRA分组和排序
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from config.settings import COMFYUI_LORAS_DIR

logger = logging.getLogger(__name__)


class LoraManager:
    """LoRA管理器"""
    
    def __init__(self):
        """初始化LoRA管理器"""
        self._config_client = None
        self._local_loras_cache = {}
        self._last_local_scan = None
        # 模型映射已移除，现在完全依赖配置客户端动态获取
        # 所有模型配置都通过配置客户端从admin后端获取
    
    def _get_config_client(self):
        """获取配置客户端"""
        if self._config_client is None:
            try:
                from core.config_client import get_config_client
                self._config_client = get_config_client()
            except ImportError:
                # 如果配置客户端不可用，返回None
                return None
        return self._config_client
    
    async def get_loras_from_config(self, base_model: Optional[str] = None) -> Dict[str, Any]:
        """从配置客户端获取LoRA配置"""
        try:
            config_client = self._get_config_client()
            if config_client:
                config = await config_client.get_loras_config()
                
                # 获取生图配置中的LoRA排序
                try:
                    image_gen_config = await config_client.get_image_gen_config()
                    lora_order = image_gen_config.get("lora_order", {})
                    logger.info(f"🔍 获取到LoRA排序配置: {lora_order}")
                    print(f"🔍 获取到LoRA排序配置: {lora_order}")
                except Exception as e:
                    logger.warning(f"获取LoRA排序配置失败: {e}")
                    print(f"❌ 获取LoRA排序配置失败: {e}")
                    lora_order = {}
                
                # 如果指定了基础模型，进行过滤
                if base_model:
                    # 使用code字段进行模型匹配，如果没有则使用name字段
                    # 更宽松的过滤逻辑：如果base_model是"未知"或空，也包含进来
                    filtered_loras = [
                        lora for lora in config.get("loras", [])
                        if (lora.get("base_model") == base_model or 
                            lora.get("base_model") in ["未知", "", None] or
                            base_model in lora.get("base_model", ""))
                    ]
                    
                    # 应用排序配置
                    if lora_order and base_model in lora_order:
                        model_lora_order = lora_order[base_model]
                        logger.info(f"🔧 应用LoRA排序配置，模型: {base_model}, 排序列表: {model_lora_order}")
                        print(f"🔧 应用LoRA排序配置，模型: {base_model}, 排序列表: {model_lora_order}")
                        print(f"🔍 排序列表长度: {len(model_lora_order)}")
                        for i, item in enumerate(model_lora_order):
                            print(f"  {i}: '{item}'")
                        # 按配置的排序重新排列
                        def sort_key(lora):
                            # 尝试匹配code字段和name字段
                            lora_code = lora.get("code")
                            lora_name = lora.get("name", "")
                            
                            # 首先尝试匹配code字段
                            if lora_code and lora_code in model_lora_order:
                                order = model_lora_order.index(lora_code)
                                print(f"✅ 匹配code字段: {lora_code} -> 排序: {order}")
                                return order
                            
                           
                            
                            print(f"❌ 未找到匹配: code={lora_code}, name={lora_name}")
                            return 999  # 未配置的排在最后
                        filtered_loras.sort(key=sort_key)
                    
                    config["loras"] = filtered_loras
                    config["filtered_by_model"] = base_model
                    config["actual_base_model"] = base_model
                    config["sort_applied"] = bool(lora_order and base_model in lora_order)
                
                return config
            else:
                # 配置客户端不可用，使用本地扫描
                return await self._get_loras_from_local_scan(base_model)
        except Exception as e:
            logger.error(f"从配置获取LoRA失败: {e}")
            # 降级到本地扫描
            return await self._get_loras_from_local_scan(base_model)
    
    async def _get_loras_from_local_scan(self, base_model: Optional[str] = None) -> Dict[str, Any]:
        """从本地文件系统扫描LoRA"""
        try:
            lora_dir = COMFYUI_LORAS_DIR
            
            if not lora_dir.exists():
                logger.warning(f"LoRA目录不存在: {lora_dir}")
                return {
                    "loras": [],
                    "grouped_by_model": {},
                    "config_source": "local_scan",
                    "error": "LoRA目录不存在"
                }
            
            loras = []
            grouped_by_model = {}
            
            # 扫描LoRA文件
            for file_path in lora_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.safetensors', '.ckpt', '.pt']:
                    # 尝试从文件名推断基础模型
                    inferred_model = self._infer_base_model_from_filename(file_path.name)
                    
                    lora_data = {
                        "name": file_path.name,
                        "display_name": self._generate_display_name(file_path.name),
                        "base_model": inferred_model,
                        "available": True,
                        "file_size": file_path.stat().st_size,
                        "file_path": str(file_path),
                        "file_type": file_path.suffix.lower()
                    }
                    
                    # 如果指定了基础模型，进行过滤
                    if base_model and inferred_model != base_model:
                        continue
                    
                    loras.append(lora_data)
                    
                    # 按模型分组
                    if inferred_model not in grouped_by_model:
                        grouped_by_model[inferred_model] = []
                    grouped_by_model[inferred_model].append(file_path.name)
            
            # 按名称排序
            loras.sort(key=lambda x: x["name"])
            
            return {
                "loras": loras,
                "grouped_by_model": grouped_by_model,
                "config_source": "local_scan",
                "filtered_by_model": base_model,
                "total_count": len(loras)
            }
        except Exception as e:
            logger.error(f"本地LoRA扫描失败: {e}")
            return {
                "loras": [],
                "grouped_by_model": {},
                "config_source": "error",
                "error": str(e)
            }
    
    def _infer_base_model_from_filename(self, filename: str) -> str:
        """从文件名推断基础模型"""
        filename_lower = filename.lower()
        
        # 根据文件名中的关键词推断模型类型
        if "flux" in filename_lower:
            return "flux-dev"
        elif "qwen" in filename_lower:
            return "qwen-image"
        elif "wan" in filename_lower:
            return "wan2.2-video"
        elif "gemini" in filename_lower:
            return "gemini-image"
        else:
            # 如果没有找到匹配的模型，返回第一个可用的模型
            available_models = list(self.model_mapping.keys())
            if available_models:
                return available_models[0]
            return None
    
    def _generate_display_name(self, filename: str) -> str:
        """生成显示名称"""
        # 移除文件扩展名
        name = Path(filename).stem
        
        # 替换下划线和连字符为空格
        name = name.replace("_", " ").replace("-", " ")
        
        # 首字母大写
        name = name.title()
        
        return name
    
    async def get_loras_by_model(self, base_model: str) -> List[Dict[str, Any]]:
        """获取指定模型的LoRA列表"""
        config = await self.get_loras_from_config(base_model)
        return config.get("loras", [])
    
    async def get_all_loras(self) -> Dict[str, Any]:
        """获取所有LoRA配置"""
        return await self.get_loras_from_config()
    
    def get_local_loras(self) -> List[Dict[str, Any]]:
        """获取本地LoRA文件列表（同步方法，降级使用）"""
        try:
            lora_dir = COMFYUI_LORAS_DIR
            
            if not lora_dir.exists():
                return []
            
            loras = []
            for file_path in lora_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.safetensors', '.ckpt', '.pt']:
                    loras.append({
                        "name": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix.lower()
                    })
            
            return loras
        except Exception as e:
            logger.error(f"获取本地LoRA失败: {e}")
            return []
    
    async def check_lora_availability(self, lora_name: str, base_model: Optional[str] = None) -> bool:
        """检查LoRA可用性"""
        try:
            config = await self.get_loras_from_config(base_model)
            loras = config.get("loras", [])
            
            for lora in loras:
                if lora.get("name") == lora_name:
                    return lora.get("available", False)
            
            return False
        except Exception as e:
            logger.error(f"检查LoRA可用性失败: {e}")
            return False
    
    async def get_lora_info(self, lora_name: str, base_model: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """获取LoRA详细信息"""
        try:
            config = await self.get_loras_from_config(base_model)
            loras = config.get("loras", [])
            
            for lora in loras:
                if lora.get("name") == lora_name:
                    return lora
            
            return None
        except Exception as e:
            logger.error(f"获取LoRA信息失败: {e}")
            return None
    
    def refresh_local_cache(self):
        """刷新本地缓存"""
        self._local_loras_cache.clear()
        self._last_local_scan = None
        logger.info("LoRA本地缓存已刷新")


# 全局LoRA管理器实例
_lora_manager: Optional[LoraManager] = None


def get_lora_manager() -> LoraManager:
    """获取LoRA管理器实例"""
    global _lora_manager
    if _lora_manager is None:
        _lora_manager = LoraManager()
    return _lora_manager


# 便捷函数
async def get_loras_from_config(base_model: Optional[str] = None) -> Dict[str, Any]:
    """从配置客户端获取LoRA配置"""
    manager = get_lora_manager()
    return await manager.get_loras_from_config(base_model)


async def get_loras_by_model(base_model: str) -> List[Dict[str, Any]]:
    """获取指定模型的LoRA列表"""
    manager = get_lora_manager()
    return await manager.get_loras_by_model(base_model)


async def get_all_loras() -> Dict[str, Any]:
    """获取所有LoRA配置"""
    manager = get_lora_manager()
    return await manager.get_all_loras()


def get_local_loras() -> List[Dict[str, Any]]:
    """获取本地LoRA文件列表（同步方法，降级使用）"""
    manager = get_lora_manager()
    return manager.get_local_loras()


async def check_lora_availability(lora_name: str, base_model: Optional[str] = None) -> bool:
    """检查LoRA可用性"""
    manager = get_lora_manager()
    return await manager.check_lora_availability(lora_name, base_model)


async def get_lora_info(lora_name: str, base_model: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """获取LoRA详细信息"""
    manager = get_lora_manager()
    return await manager.get_lora_info(lora_name, base_model)


def refresh_lora_cache():
    """刷新LoRA缓存"""
    manager = get_lora_manager()
    manager.refresh_local_cache()
