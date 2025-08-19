#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flux工作流实现
专门处理Flux Kontext模型的工作流创建
"""

import random
from typing import Any, Dict

from config.settings import (
    TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT, 
    DEFAULT_STEPS, DEFAULT_COUNT
)

from .base_workflow import BaseWorkflow


class FluxWorkflow(BaseWorkflow):
    """Flux工作流创建器"""
    
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建Flux工作流
        
        Args:
            reference_image_path: 参考图像路径
            description: 图像描述
            parameters: 生成参数
            
        Returns:
            Flux工作流字典
        """
        print(f"🎨 创建Flux工作流: {self.model_config.display_name}")
        
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 处理参考图像
        processed_image_path = self._process_reference_image(reference_image_path)
        
        # 创建基础工作流
        workflow = self._create_base_workflow(description, validated_params)
        
        # 处理LoRA配置
        loras = validated_params.get("loras", [])
        if loras:
            workflow = self._add_lora_nodes(workflow, loras, description)
        
        # 处理参考图像
        if processed_image_path:
            workflow = self._add_reference_image_nodes(workflow, processed_image_path)
        
        # 更新最终参数
        workflow = self._update_final_parameters(workflow, validated_params)
        
        print(f"✅ Flux工作流创建完成，包含 {len(workflow)} 个节点")
        return workflow
    
    def _create_base_workflow(self, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建基础Flux工作流"""
        workflow = {
            "6": {
                "inputs": {
                    "text": description,
                    "clip": ["38", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP文本编码器"}
            },
            "8": {
                "inputs": {
                    "samples": ["31", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE解码"}
            },
            "31": {
                "inputs": {
                    "seed": parameters.get("seed", random.randint(1, 2**32 - 1)),
                    "steps": parameters.get("steps", DEFAULT_STEPS),
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "batch_size": parameters.get("count", DEFAULT_COUNT),
                    "model": ["37", 0],
                    "positive": ["35", 0],
                    "negative": ["135", 0],
                    "latent_image": ["124", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "K采样器"}
            },
            "35": {
                "inputs": {
                    "guidance": 2.5,
                    "conditioning": ["177", 0]
                },
                "class_type": "FluxGuidance",
                "_meta": {"title": "Flux引导"}
            },
            "37": {
                "inputs": {
                    "unet_name": self.model_config.unet_file,
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "UNET加载器"}
            },
            "38": {
                "inputs": {
                    "clip_name1": "clip_l.safetensors",
                    "clip_name2": "t5xxl_fp8_e4m3fn_scaled.safetensors",
                    "type": "flux",
                    "device": "default"
                },
                "class_type": "DualCLIPLoader",
                "_meta": {"title": "双CLIP加载器"}
            },
            "39": {
                "inputs": {
                    "vae_name": "ae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {"title": "VAE加载器"}
            },
            "42": {
                "inputs": {
                    "width": TARGET_IMAGE_WIDTH,
                    "height": TARGET_IMAGE_HEIGHT,
                    "batch_size": 1,
                    "color": 0
                },
                "class_type": "EmptyImage",
                "_meta": {"title": "空图像"}
            },
            "124": {
                "inputs": {
                    "pixels": ["42", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEEncode",
                "_meta": {"title": "VAE编码"}
            },
            "135": {
                "inputs": {
                    "conditioning": ["6", 0]
                },
                "class_type": "ConditioningZeroOut",
                "_meta": {"title": "条件零化"}
            },
            "136": {
                "inputs": {
                    "filename_prefix": "yeepay/yeepay",
                    "images": ["8", 0],
                    "save_all": True
                },
                "class_type": "SaveImage",
                "_meta": {"title": "保存图像"}
            },
            "177": {
                "inputs": {
                    "conditioning": ["6", 0],
                    "latent": ["124", 0]
                },
                "class_type": "ReferenceLatent",
                "_meta": {"title": "ReferenceLatent"}
            }
        }
        
        return workflow
    
    def _add_lora_nodes(self, workflow: Dict[str, Any], loras: list, description: str) -> Dict[str, Any]:
        """添加LoRA节点"""
        processed_loras = self._process_loras(loras)
        
        if not processed_loras:
            return workflow
        
        print(f"🎨 检测到 {len(processed_loras)} 个LoRA配置")
        
        current_model_node = "37"  # UNETLoader
        current_clip_node = "38"   # DualCLIPLoader
        
        for i, lora_config in enumerate(processed_loras):
            lora_node_id = str(50 + i)  # 50, 51, 52, 53
            lora_name = lora_config["name"]
            strength_model = lora_config["strength_model"]
            strength_clip = lora_config["strength_clip"]
            trigger_word = lora_config["trigger_word"]
            
            print(f"🎨 添加LoRA {i+1}: {lora_name} (UNET: {strength_model}, CLIP: {strength_clip})")
            
            # 添加LoRA节点
            workflow[lora_node_id] = {
                "inputs": {
                    "model": [current_model_node, 0],
                    "clip": [current_clip_node, 0],
                    "lora_name": lora_name,
                    "strength_model": strength_model,
                    "strength_clip": strength_clip
                },
                "class_type": "LoraLoader",
                "_meta": {"title": f"LoRA加载器{i+1}"}
            }
            
            # 更新当前节点引用
            current_model_node = lora_node_id
            current_clip_node = lora_node_id
            
            # 添加触发词
            if trigger_word and trigger_word not in description:
                description = f"{trigger_word}, {description}"
                print(f"🔤 添加触发词: {trigger_word}")
        
        # 更新连接
        workflow["31"]["inputs"]["model"] = [current_model_node, 0]
        workflow["6"]["inputs"]["clip"] = [current_clip_node, 1]
        workflow["6"]["inputs"]["text"] = description
        
        print(f"✅ LoRA节点连接完成: UNET -> {current_model_node}, CLIP -> {current_clip_node}")
        return workflow
    
    def _add_reference_image_nodes(self, workflow: Dict[str, Any], image_path: str) -> Dict[str, Any]:
        """添加参考图像节点"""
        print("检测到参考图，使用参考图模式")
        
        # 添加LoadImageOutput节点
        workflow["142"] = {
            "inputs": {
                "image": image_path,
                "refresh": "refresh"
            },
            "class_type": "LoadImageOutput",
            "_meta": {"title": "加载图像（来自输出）"}
        }
        
        # 更新ImageScale节点
        workflow["42"] = {
            "inputs": {
                "image": ["142", 0],
                "width": TARGET_IMAGE_WIDTH,
                "height": TARGET_IMAGE_HEIGHT,
                "crop": "disabled",
                "upscale_method": "lanczos",
                "downscale_method": "area"
            },
            "class_type": "ImageScale",
            "_meta": {"title": "图像缩放"}
        }
        
        # 更新VAEEncode节点
        workflow["124"]["inputs"]["pixels"] = ["42", 0]
        
        print(f"✅ 配置参考图模式工作流")
        return workflow
    
    def _update_final_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新最终参数"""
        # 更新生成参数
        if parameters.get("steps"):
            workflow["31"]["inputs"]["steps"] = parameters["steps"]
        
        if parameters.get("cfg"):
            workflow["31"]["inputs"]["cfg"] = parameters["cfg"]
        
        if parameters.get("guidance"):
            workflow["35"]["inputs"]["guidance"] = parameters["guidance"]
        
        # 处理生成数量
        count = parameters.get("count", 1)
        workflow["31"]["inputs"]["batch_size"] = count
        
        if count > 1:
            workflow["136"]["inputs"]["save_all"] = True
            print(f"设置batch_size为: {count}")
        
        # 设置种子
        if parameters.get("seed"):
            workflow["31"]["inputs"]["seed"] = parameters["seed"]
            print(f"使用指定种子: {parameters['seed']}")
        else:
            seed = random.randint(1, 2**32 - 1)
            workflow["31"]["inputs"]["seed"] = seed
            print(f"使用随机种子: {seed}")
        
        print(f"工作流参数更新完成: 步数={workflow['31']['inputs']['steps']}, CFG={workflow['31']['inputs']['cfg']}, 引导={workflow['35']['inputs']['guidance']}")
        return workflow
