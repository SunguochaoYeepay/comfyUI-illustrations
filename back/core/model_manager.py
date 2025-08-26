#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理器
负责管理不同的基础模型（Flux、Qwen等）
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

from config.settings import COMFYUI_MAIN_OUTPUT_DIR, COMFYUI_MODELS_DIR


class ModelType(Enum):
    """模型类型枚举"""
    FLUX = "flux"
    QWEN = "qwen"


class ModelConfig:
    """模型配置类"""
    
    def __init__(self, model_type: ModelType, name: str, display_name: str, 
                 unet_file: str, clip_file: str, vae_file: str, 
                 template_path: str, description: str = ""):
        self.model_type = model_type
        self.name = name
        self.display_name = display_name
        self.unet_file = unet_file
        self.clip_file = clip_file
        self.vae_file = vae_file
        self.template_path = template_path
        self.description = description
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查模型文件是否可用"""
        try:
            # 使用统一配置的模型目录路径
            model_dir = COMFYUI_MODELS_DIR
            
            # 根据模型类型确定文件路径
            if self.model_type == ModelType.FLUX:
                unet_path = model_dir / "checkpoints" / self.unet_file
                clip_path = model_dir / "clip" / self.clip_file
                vae_path = model_dir / "vae" / self.vae_file
            elif self.model_type == ModelType.QWEN:
                unet_path = model_dir / "diffusion_models" / self.unet_file
                clip_path = model_dir / "text_encoders" / self.clip_file
                vae_path = model_dir / "vae" / self.vae_file
            else:
                # 默认使用checkpoints目录
                unet_path = model_dir / "checkpoints" / self.unet_file
                clip_path = model_dir / "clip" / self.clip_file
                vae_path = model_dir / "vae" / self.vae_file
            
            return (unet_path.exists() and 
                   clip_path.exists() and 
                   vae_path.exists())
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
        self._init_models()
    
    def _init_models(self):
        """初始化模型配置"""
        # Flux模型配置
        flux_config = ModelConfig(
            model_type=ModelType.FLUX,
            name="flux1-dev",
            display_name="Flux Kontext",
            unet_file="flux1-dev-kontext_fp8_scaled.safetensors",
            clip_file="clip_l.safetensors",  # 双CLIP架构
            vae_file="ae.safetensors",
            template_path="flux_kontext_dev_basic.json",
            description="Flux Kontext开发版本，支持高质量图像生成"
        )
        
        # Qwen模型配置
        qwen_config = ModelConfig(
            model_type=ModelType.QWEN,
            name="qwen-image",
            display_name="Qwen",
            unet_file="qwen_image_edit_fp8_e4m3fn.safetensors",  # 在diffusion_models目录
            clip_file="qwen_2.5_vl_7b_fp8_scaled.safetensors",  # 在text_encoders目录
            vae_file="qwen_image_vae.safetensors",  # 在vae目录
            template_path="workflows/qwen_image_generation_workflow.json",  # 使用workflows目录下的标准工作流
            description="千问图像模型，支持高质量图像生成"
        )
        
        self.models[flux_config.name] = flux_config
        self.models[qwen_config.name] = qwen_config
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用的模型列表"""
        available_models = []
        for model in self.models.values():
            if model.available:
                available_models.append(model.to_dict())
        return available_models
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """获取指定模型的配置"""
        return self.models.get(model_name)
    
    def get_default_model(self) -> ModelConfig:
        """获取默认模型（Flux）"""
        return self.models["flux1-dev"]
    
    def is_model_available(self, model_name: str) -> bool:
        """检查模型是否可用"""
        model = self.models.get(model_name)
        return model is not None and model.available
    
    def get_model_template_path(self, model_name: str) -> Optional[str]:
        """获取模型的工作流模板路径"""
        model = self.models.get(model_name)
        if model and model.available:
            return model.template_path
        return None
    
    def get_available_loras(self) -> List[Dict[str, Any]]:
        """获取可用的 LoRA 文件列表"""
        try:
            # 使用统一配置的 LoRA 目录路径
            from config.settings import COMFYUI_LORAS_DIR
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
            print(f"Error getting LoRAs: {e}")
            return []


# 全局模型管理器实例
model_manager = ModelManager()


def get_available_models() -> List[Dict[str, Any]]:
    """获取可用的模型列表"""
    return model_manager.get_available_models()


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """获取指定模型的配置"""
    return model_manager.get_model_config(model_name)


def get_default_model() -> ModelConfig:
    """获取默认模型"""
    return model_manager.get_default_model()


def is_model_available(model_name: str) -> bool:
    """检查模型是否可用"""
    return model_manager.is_model_available(model_name)


def get_available_loras() -> List[Dict[str, Any]]:
    """获取可用的 LoRA 文件列表"""
    return model_manager.get_available_loras()
