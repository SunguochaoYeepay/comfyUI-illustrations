#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器
负责管理不同的基础模型（Flux、Qwen等）
集成配置客户端，支持动态模型配置
"""

import json
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

from config.settings import COMFYUI_MAIN_OUTPUT_DIR, COMFYUI_MODELS_DIR, ADMIN_BACKEND_URL


class ModelType(Enum):
    """模型类型枚举"""
    FLUX = "flux"
    QWEN = "qwen"
    WAN = "wan" # Added WAN model type
    GEMINI = "gemini" # Added GEMINI model type
    SEEDREAM4 = "seedream4" # Added SEEDREAM4 model type


class ModelConfig:
    """模型配置类 - 移除template_path依赖，完全数据库化"""
    
    def __init__(self, model_type: ModelType, name: str, display_name: str, 
                 unet_file: str, clip_file: str, vae_file: str, 
                 template_path: str = "", description: str = ""):
        self.model_type = model_type
        self.name = name
        self.display_name = display_name
        self.unet_file = unet_file
        self.clip_file = clip_file
        self.vae_file = vae_file
        self.template_path = template_path  # 保留参数以兼容现有代码，但不再使用
        self.description = description
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查模型文件是否可用"""
        try:
            # API模型（如Gemini）不需要本地文件，直接返回可用
            if self.model_type == ModelType.GEMINI:
                print(f"✅ API模型 {self.name} 可用")
                return True
            
            # 使用统一配置的模型目录路径
            model_dir = COMFYUI_MODELS_DIR
            
            # 在Docker环境中，如果模型目录不存在，假设模型通过挂载可用
            if not model_dir.exists():
                print(f"⚠️ 模型目录不存在，假设模型 {self.name} 通过挂载可用: {model_dir}")
                return True
            
            # 根据模型类型确定文件路径
            if self.model_type == ModelType.FLUX:
                unet_path = model_dir / "checkpoints" / self.unet_file
                clip_path = model_dir / "clip" / self.clip_file
                vae_path = model_dir / "vae" / self.vae_file
            elif self.model_type == ModelType.QWEN:
                unet_path = model_dir / "diffusion_models" / self.unet_file
                clip_path = model_dir / "text_encoders" / self.clip_file
                vae_path = model_dir / "vae" / self.vae_file
            elif self.model_type == ModelType.WAN: # Added WAN model type
                unet_path = model_dir / "diffusion_models" / self.unet_file
                clip_path = model_dir / "text_encoders" / self.clip_file
                vae_path = model_dir / "vae" / self.vae_file
            else:
                # 默认使用checkpoints目录
                unet_path = model_dir / "checkpoints" / self.unet_file
                clip_path = model_dir / "clip" / self.clip_file
                vae_path = model_dir / "vae" / self.vae_file
            
            unet_exists = unet_path.exists()
            clip_exists = clip_path.exists()
            vae_exists = vae_path.exists()
            
            # 调试信息（生产环境可注释掉）
            # print(f"🔍 检查模型 {self.name} 文件:")
            # print(f"  - UNet: {unet_path} - {'✅' if unet_exists else '❌'}")
            # print(f"  - CLIP: {clip_path} - {'✅' if clip_exists else '❌'}")
            # print(f"  - VAE: {vae_path} - {'✅' if vae_exists else '❌'}")
            
            return (unet_exists and clip_exists and vae_exists)
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "type": self.model_type.value,
            "name": self.name,
            "display_name": self.display_name,
            "unet_file": self.unet_file,
            "clip_file": self.clip_file,
            "vae_file": self.vae_file,
            "description": self.description,
            "available": self.available
        }


class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self._config_client = None
        self._init_models()
    
    def _init_models(self):
        """初始化模型配置 - 完全依赖配置客户端，无硬编码"""
        # 不再硬编码任何模型配置
        # 所有模型配置都通过配置客户端动态获取
        pass
    
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
    
    async def get_available_models_from_config(self) -> List[Dict[str, Any]]:
        """从配置客户端获取可用的模型列表"""
        try:
            config_client = self._get_config_client()
            if config_client:
                config = await config_client.get_models_config()
                models = config.get("models", [])
                
                # 过滤掉不可用的模型
                available_models = [model for model in models if model.get("available", True)]
                print(f"🔍 从配置获取模型: 总数 {len(models)}, 可用 {len(available_models)}")
                
                # 应用模型排序
                return self.apply_model_order_config(available_models)
            else:
                # 配置客户端不可用，使用默认方法
                return self.get_available_models()
        except Exception as e:
            print(f"从配置获取模型失败: {e}")
            # 降级到默认方法
            return self.get_available_models()
    
    def apply_model_order_config(self, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用模型排序配置"""
        # 按sort_order排序
        sorted_models = sorted(models, key=lambda x: x.get("sort_order", 999))
        return sorted_models
    
    def check_model_availability(self, model_name: str) -> bool:
        """检查模型可用性"""
        # 首先检查本地模型配置
        if model_name in self.models:
            return self.models[model_name].available
        
        # 如果本地没有，尝试从配置客户端获取
        try:
            config_client = self._get_config_client()
            if config_client:
                # 这里可以添加异步检查逻辑
                return True  # 暂时返回True，实际应该检查配置
        except:
            pass
        
        return False
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用的模型列表（降级方法）- 完全依赖配置客户端"""
        try:
            # 尝试同步获取配置
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，创建任务
                task = asyncio.create_task(self.get_available_models_from_config())
                # 这里不能直接等待，返回空列表让异步方法处理
                return []
            else:
                # 如果事件循环未运行，直接运行
                return loop.run_until_complete(self.get_available_models_from_config())
        except Exception as e:
            print(f"降级方法获取模型失败: {e}")
            # 最后的保底：返回空列表，让前端显示错误
            return []
    
    async def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """获取指定模型的配置 - 完全依赖配置客户端（异步版本）"""
        try:
            # 确保配置客户端已初始化
            config_client = self._get_config_client()
            if config_client is None:
                print(f"❌ 配置客户端不可用")
                return None
            
            # 通过配置客户端获取模型配置
            models_response = await config_client.get_models_config()
            
            # 从响应中提取模型列表
            models_config = models_response.get("models", [])
            
            # 查找指定名称的模型
            for model_data in models_config:
                if model_data.get("name") == model_name:
                    return self._convert_dict_to_model_config(model_data)
            
            print(f"⚠️ 未找到模型配置: {model_name}")
            return None
            
        except Exception as e:
            print(f"❌ 获取模型配置失败: {e}")
            return None
    
    def get_model_config_sync(self, model_name: str) -> Optional[ModelConfig]:
        """获取指定模型的配置 - 同步版本（兼容性）"""
        try:
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 如果已经在事件循环中，使用同步方式获取
                return self._get_model_config_sync_fallback(model_name)
            except RuntimeError:
                # 没有运行的事件循环，可以使用asyncio.run
                return asyncio.run(self.get_model_config(model_name))
        except Exception as e:
            print(f"❌ 获取模型配置失败: {e}")
            return None
    
    def _get_model_config_sync_fallback(self, model_name: str) -> Optional[ModelConfig]:
        """同步回退方法 - 通过admin API获取"""
        try:
            import requests
            
            # 通过admin API获取模型配置
            admin_url = f"{ADMIN_BACKEND_URL}/api/admin/config-sync/models"
            response = requests.get(admin_url, timeout=5)
            
            if response.status_code != 200:
                print(f"❌ admin API调用失败: {response.status_code}")
                return None
            
            data = response.json()
            models = data.get("models", [])
            
            # 查找指定模型
            for model_data in models:
                if model_data.get("name") == model_name:
                    print(f"✅ 通过admin API获取模型配置: {model_name}")
                    return self._convert_dict_to_model_config(model_data)
            
            print(f"⚠️ admin API中未找到模型: {model_name}")
            return None
                
        except Exception as e:
            print(f"❌ 通过admin API获取模型配置失败: {e}")
            return None
    
    def _convert_dict_to_model_config(self, model_data: Dict[str, Any]) -> ModelConfig:
        """将字典转换为ModelConfig对象"""
        return ModelConfig(
            model_type=ModelType(model_data.get("model_type", "unknown")),
            name=model_data.get("name", ""),
            display_name=model_data.get("display_name", ""),
            unet_file=model_data.get("unet_file", ""),
            clip_file=model_data.get("clip_file", ""),
            vae_file=model_data.get("vae_file", ""),
            template_path="",  # 已移除，完全数据库化
            description=model_data.get("description", "")
        )
    
    def get_default_model(self) -> Optional[ModelConfig]:
        """获取默认模型 - 完全依赖配置客户端"""
        # 不再硬编码默认模型
        # 默认模型也通过配置客户端获取
        return None
    
    def is_model_available(self, model_name: str) -> bool:
        """检查模型是否可用 - 完全依赖配置客户端"""
        # 不再从硬编码的models字典检查
        # 模型可用性通过配置客户端检查
        return True  # 暂时返回True，实际应该通过配置客户端检查
    
    def get_model_template_path(self, model_name: str) -> Optional[str]:
        """获取模型的工作流模板路径 - 完全依赖配置客户端"""
        # 不再从硬编码的models字典获取
        # 模板路径通过配置客户端获取
        return None
    
    def get_available_loras(self) -> List[Dict[str, Any]]:
        """获取可用的 LoRA 文件列表 - 完全依赖配置客户端"""
        # 不再硬编码扫描本地文件
        # 所有LoRA配置都通过配置客户端获取
        return []


# 全局模型管理器实例
model_manager = ModelManager()


def get_available_models() -> List[Dict[str, Any]]:
    """获取可用的模型列表（同步方法，降级使用）- 完全依赖配置客户端"""
    return model_manager.get_available_models()


async def get_available_models_async() -> List[Dict[str, Any]]:
    """获取可用的模型列表（异步方法，优先使用配置客户端）"""
    return await model_manager.get_available_models_from_config()


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """获取指定模型的配置 - 完全依赖配置客户端"""
    return model_manager.get_model_config(model_name)


def get_default_model() -> Optional[ModelConfig]:
    """获取默认模型 - 完全依赖配置客户端"""
    return model_manager.get_default_model()


def is_model_available(model_name: str) -> bool:
    """检查模型是否可用 - 完全依赖配置客户端"""
    return model_manager.is_model_available(model_name)


def get_available_loras() -> List[Dict[str, Any]]:
    """获取可用的 LoRA 文件列表 - 完全依赖配置客户端"""
    return model_manager.get_available_loras()
