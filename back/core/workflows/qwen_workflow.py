#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen工作流实现
专门处理Qwen模型的工作流创建
"""

import json
from typing import Any, Dict

from .base_workflow import BaseWorkflow


class QwenWorkflow(BaseWorkflow):
    """Qwen工作流创建器"""
    
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建Qwen工作流
        
        Args:
            reference_image_path: 参考图像路径
            description: 图像描述
            parameters: 生成参数
            
        Returns:
            Qwen工作流字典
        """
        print(f"🎨 创建Qwen工作流: {self.model_config.display_name}")
        
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 加载工作流模板
        workflow = self._load_workflow_template()
        
        # 更新模型配置
        workflow = self._update_model_config(workflow)
        
        # 更新文本描述
        workflow = self._update_text_description(workflow, description)
        
        # 更新采样参数
        workflow = self._update_sampling_parameters(workflow, validated_params)
        
        # 更新保存路径
        workflow = self._update_save_path(workflow)
        
        # 处理LoRA配置
        loras = validated_params.get("loras", [])
        if loras:
            workflow = self._update_lora_config(workflow, loras)
        
        print(f"✅ Qwen工作流创建完成，使用标准ComfyUI格式")
        return workflow
    
    def _load_workflow_template(self) -> Dict[str, Any]:
        """加载工作流模板"""
        try:
            workflow_path = "workflows/qwen_image_generation_workflow.json"
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            print(f"✅ 加载Qwen工作流模板: {workflow_path}")
            return workflow
        except FileNotFoundError:
            print(f"⚠️ Qwen工作流模板文件不存在，使用内置模板")
            return self._get_builtin_template()
        except json.JSONDecodeError as e:
            print(f"❌ Qwen工作流模板文件格式错误: {str(e)}")
            return self._get_builtin_template()
    
    def _get_builtin_template(self) -> Dict[str, Any]:
        """获取内置模板"""
        from config.settings import TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT
        
        return {
            "20": {
                "type": "KSampler",
                "inputs": {
                    "seed": 287237245922212,
                    "steps": 20,
                    "cfg": 3,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1
                }
            },
            "22": {
                "type": "VAELoader", 
                "inputs": {
                    "vae_name": "qwen_image_vae.safetensors"
                }
            },
            "23": {
                "type": "UNETLoader",
                "inputs": {
                    "unet_name": "Qwen-Image_1.0",
                    "weight_dtype": "default"
                }
            },
            "24": {
                "type": "CLIPLoader",
                "inputs": {
                    "clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                    "clip_type": "qwen_image",
                    "weight_dtype": "default"
                }
            },
            "25": {
                "type": "CLIPTextEncode",
                "inputs": {
                    "text": "{{description}}"
                }
            },
            "27": {
                "type": "CR SDXL Aspect Ratio",
                "inputs": {
                    "width": TARGET_IMAGE_WIDTH,
                    "height": TARGET_IMAGE_HEIGHT,
                    "aspect_ratio": "custom",
                    "swap_dimensions": "Off",
                    "upscale_factor": 1,
                    "batch_size": 1
                }
            },
            "28": {
                "type": "SaveImage",
                "inputs": {
                    "filename_prefix": "yeepay/yeepay"
                }
            },
            "33": {
                "type": "Lora Loader Stack (rgthree)",
                "inputs": {
                    "lora_01": "None",
                    "strength_01": 0.8,
                    "lora_02": "None",
                    "strength_02": 0.1,
                    "lora_03": "None",
                    "strength_03": 0.1,
                    "lora_04": "None",
                    "strength_04": 0.1
                }
            }
        }
    
    def _update_model_config(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新模型配置"""
        if "23" in workflow:
            workflow["23"]["inputs"]["unet_name"] = self.model_config.unet_file
            print(f"✅ 更新UNETLoader: {self.model_config.unet_file}")
        
        if "24" in workflow:
            workflow["24"]["inputs"]["clip_name"] = self.model_config.clip_file
            print(f"✅ 更新CLIPLoader: {self.model_config.clip_file}")
        
        if "22" in workflow:
            workflow["22"]["inputs"]["vae_name"] = self.model_config.vae_file
            print(f"✅ 更新VAELoader: {self.model_config.vae_file}")
        
        return workflow
    
    def _update_text_description(self, workflow: Dict[str, Any], description: str) -> Dict[str, Any]:
        """更新文本描述"""
        if "25" in workflow:
            workflow["25"]["inputs"]["text"] = description
            print(f"✅ 更新描述文本: {description[:50]}...")
        
        return workflow
    
    def _update_sampling_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新采样参数"""
        if "20" in workflow:
            if parameters.get("steps"):
                workflow["20"]["inputs"]["steps"] = parameters["steps"]
            if parameters.get("seed"):
                workflow["20"]["inputs"]["seed"] = parameters["seed"]
            print(f"✅ 更新KSampler参数: 步数={parameters.get('steps', 20)}, 种子={parameters.get('seed', 'random')}")
        
        # 动态更新图像尺寸配置
        workflow = self._update_image_dimensions(workflow)
        
        return workflow
    
    def _update_image_dimensions(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """动态更新图像尺寸配置"""
        from config.settings import TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT
        
        # 更新节点27（CR SDXL Aspect Ratio）的尺寸配置
        if "27" in workflow:
            workflow["27"]["inputs"]["width"] = TARGET_IMAGE_WIDTH
            workflow["27"]["inputs"]["height"] = TARGET_IMAGE_HEIGHT
            # 使用custom选项，通过width和height参数控制尺寸
            workflow["27"]["inputs"]["aspect_ratio"] = "custom"
            print(f"✅ 动态更新图像尺寸: {TARGET_IMAGE_WIDTH}x{TARGET_IMAGE_HEIGHT} (自定义)")
        
        return workflow
    
    def _update_save_path(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新保存路径"""
        if "28" in workflow:
            workflow["28"]["inputs"]["filename_prefix"] = "yeepay/yeepay"
            print(f"✅ 更新保存路径: yeepay/yeepay")
        
        return workflow
    
    def _update_lora_config(self, workflow: Dict[str, Any], loras: list) -> Dict[str, Any]:
        """更新LoRA配置"""
        if "33" not in workflow:
            return workflow
        
        processed_loras = self._process_loras(loras)
        
        if not processed_loras:
            print("ℹ️ 未检测到LoRA配置，使用默认设置")
            return workflow
        
        print(f"🎨 检测到 {len(processed_loras)} 个LoRA配置")
        
        # 重置所有LoRA配置
        workflow["33"]["inputs"]["lora_01"] = "None"
        workflow["33"]["inputs"]["strength_01"] = 0.8
        workflow["33"]["inputs"]["lora_02"] = "None"
        workflow["33"]["inputs"]["strength_02"] = 0.1
        workflow["33"]["inputs"]["lora_03"] = "None"
        workflow["33"]["inputs"]["strength_03"] = 0.1
        workflow["33"]["inputs"]["lora_04"] = "None"
        workflow["33"]["inputs"]["strength_04"] = 0.1
        
        # 设置启用的LoRA
        for i, lora in enumerate(processed_loras):
            if i >= 4:  # 限制最多4个LoRA
                break
                
            lora_key = f"lora_{i+1:02d}"
            strength_key = f"strength_{i+1:02d}"
            
            workflow["33"]["inputs"][lora_key] = lora["name"]
            workflow["33"]["inputs"][strength_key] = lora["strength_model"]
            print(f"✅ 设置LoRA {i+1}: {lora['name']} (强度: {lora['strength_model']})")
        
        print(f"✅ LoRA配置完成: {len(processed_loras)} 个LoRA")
        return workflow
