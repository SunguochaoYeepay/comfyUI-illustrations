#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen工作流实现
专门处理Qwen模型的工作流创建
"""

import json
from typing import Any, Dict

from .base_workflow import BaseWorkflow
from config.settings import ADMIN_BACKEND_URL


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
        
        # 处理参考图像
        processed_image_path = self._process_reference_image(reference_image_path)
        
        # 加载工作流模板
        workflow = self._load_workflow_template()
        
        # 更新模型配置
        workflow = self._update_model_config(workflow)
        
        # 更新文本描述
        workflow = self._update_text_description(workflow, description)
        
        # 更新采样参数
        workflow = self._update_sampling_parameters(workflow, validated_params)
        
        # 更新图像尺寸
        workflow = self._update_image_dimensions(workflow, validated_params)
        
        # 更新保存路径
        workflow = self._update_save_path(workflow)
        
        # 处理参考图像
        if processed_image_path:
            workflow = self._add_reference_image_nodes(workflow, processed_image_path)
            print(f"📸 已添加参考图支持: {processed_image_path}")
        else:
            print("📸 无参考图，使用无参考图模式")
        
        # 处理LoRA配置
        loras = validated_params.get("loras", [])
        if loras:
            workflow = self._update_lora_config(workflow, loras)
        
        print(f"✅ Qwen工作流创建完成，使用标准ComfyUI格式")
        return workflow
    
    def _add_reference_image_nodes(self, workflow: Dict[str, Any], image_path: str) -> Dict[str, Any]:
        """添加参考图像节点到Qwen工作流
        
        Args:
            workflow: 工作流字典
            image_path: 处理后的图像路径
            
        Returns:
            更新后的工作流字典
        """
        print("📸 为Qwen工作流添加参考图支持")
        
        # 从工作流中获取目标尺寸（应该已经被_update_image_dimensions设置）
        target_width = 1024  # 默认值
        target_height = 1024  # 默认值
        
        if "27" in workflow and "inputs" in workflow["27"]:
            target_width = workflow["27"]["inputs"].get("width", 1024)
            target_height = workflow["27"]["inputs"].get("height", 1024)
            print(f"🔄 使用工作流目标尺寸: {target_width}x{target_height}")
        
        # 添加LoadImage节点
        comfyui_path = self._convert_path_for_comfyui(image_path)
        workflow["100"] = {
            "inputs": {
                "image": comfyui_path,
                "choose file to upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {"title": "加载参考图像"}
        }
        
        # 添加ImageScale节点
        workflow["101"] = {
            "inputs": {
                "image": ["100", 0],
                "width": target_width,
                "height": target_height,
                "crop": "disabled",
                "upscale_method": "lanczos",
                "downscale_method": "area"
            },
            "class_type": "ImageScale",
            "_meta": {"title": "缩放参考图像"}
        }
        
        # 创建VAEEncode节点用于参考图处理
        workflow["103"] = {
            "inputs": {
                "pixels": ["101", 0],  # 连接到ImageScale节点
                "vae": ["22", 0]
            },
            "class_type": "VAEEncode",
            "_meta": {"title": "VAE编码"}
        }
        print("✅ 创建VAEEncode节点用于参考图处理")
        
        # 更新KSampler的latent_image输入
        if "20" in workflow:
            workflow["20"]["inputs"]["latent_image"] = ["103", 0]
            print(f"✅ 更新KSampler节点，使用参考图VAEEncode作为latent_image")
            
            # 设置图生图模式的降噪值
            workflow["20"]["inputs"]["denoise"] = 0.6
            print("🎨 图生图模式：设置降噪为0.6")
        
        print(f"✅ Qwen参考图节点配置完成")
        return workflow
    
    def _load_workflow_template(self) -> Dict[str, Any]:
        """通过admin API加载工作流模板"""
        try:
            import requests
            import json
            
            # 通过admin API获取工作流配置
            admin_url = f"{ADMIN_BACKEND_URL}/api/admin/config-sync/workflows"
            response = requests.get(admin_url, timeout=5)
            
            if response.status_code != 200:
                print(f"⚠️ admin API调用失败: {response.status_code}，使用内置模板")
                return self._get_builtin_template()
            
            data = response.json()
            workflows = data.get("workflows", [])
            
            # 查找Qwen工作流
            for workflow_data in workflows:
                if workflow_data.get("name") == "qwen_image_generation":
                    workflow_json = workflow_data.get("workflow_json")
                    if workflow_json:
                        workflow = json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
                        print(f"✅ 通过admin API加载Qwen工作流模板: qwen_image_generation")
                        return workflow
            
            print(f"⚠️ admin API中未找到Qwen工作流，使用内置模板")
            return self._get_builtin_template()
            
        except Exception as e:
            print(f"❌ 通过admin API加载Qwen工作流失败: {e}，使用内置模板")
            return self._get_builtin_template()
    
    def _get_builtin_template(self) -> Dict[str, Any]:
        """获取内置模板"""
        from config.settings import TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT
        
        return {
            "20": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 287237245922212,
                    "steps": 8,
                    "cfg": 3,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1
                }
            },
            "22": {
                "class_type": "VAELoader", 
                "inputs": {
                    "vae_name": "qwen_image_vae.safetensors"
                }
            },
            "23": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": "Qwen-Image_1.0",
                    "weight_dtype": "default"
                }
            },
            "24": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                    "clip_type": "qwen_image",
                    "weight_dtype": "default"
                }
            },
            "25": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "{{description}}"
                }
            },
            "27": {
                "class_type": "CR SDXL Aspect Ratio",
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
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "yeepay/yeepay"
                }
            },
            "33": {
                "class_type": "Lora Loader Stack (rgthree)",
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
            print(f"✅ 更新KSampler参数: 步数={parameters.get('steps', 8)}, 种子={parameters.get('seed', 'random')}")
        
        # 图像尺寸更新已移到单独的步骤
        
        # 默认设置为文生图模式（完全降噪）
        if "20" in workflow:
            workflow["20"]["inputs"]["denoise"] = 1.0
            print("🎨 默认文生图模式：设置降噪为1.0")
        
        # 文生图模式：KSampler直接连接到CR SDXL Aspect Ratio的输出端口4
        if "20" in workflow:
            workflow["20"]["inputs"]["latent_image"] = ["27", 4]
            print("✅ 文生图模式：KSampler直接连接到CR SDXL Aspect Ratio")
        
        return workflow
    
    def _update_image_dimensions(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """动态更新图像尺寸配置"""
        # 从参数中获取尺寸
        size_str = parameters.get("size", "1024x1024")
        try:
            width, height = map(int, size_str.split('x'))
        except (ValueError, AttributeError):
            # 如果解析失败，使用默认尺寸
            width, height = 1024, 1024
            print(f"⚠️ 尺寸解析失败，使用默认尺寸: {width}x{height}")
        
        # 更新节点27（CR SDXL Aspect Ratio）的尺寸配置
        if "27" in workflow:
            workflow["27"]["inputs"]["width"] = width
            workflow["27"]["inputs"]["height"] = height
            # 使用custom选项，通过width和height参数控制尺寸
            workflow["27"]["inputs"]["aspect_ratio"] = "custom"
            print(f"✅ 动态更新图像尺寸: {width}x{height} (自定义)")
        
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
        
        # 保留默认的8步生图LoRA，前端LoRA从lora_02开始
        # lora_01 保持默认的 Qwen-Image-Lightning-8steps-V1.0.safetensors
        workflow["33"]["inputs"]["lora_02"] = "None"
        workflow["33"]["inputs"]["strength_02"] = 0.1
        workflow["33"]["inputs"]["lora_03"] = "None"
        workflow["33"]["inputs"]["strength_03"] = 0.1
        workflow["33"]["inputs"]["lora_04"] = "None"
        workflow["33"]["inputs"]["strength_04"] = 0.1
        
        # 设置前端选择的LoRA（从lora_02开始）
        for i, lora in enumerate(processed_loras):
            if i >= 3:  # 限制最多3个额外LoRA（lora_02, lora_03, lora_04）
                break
                
            lora_key = f"lora_{i+2:02d}"  # 从lora_02开始
            strength_key = f"strength_{i+2:02d}"
            
            workflow["33"]["inputs"][lora_key] = lora["name"]
            workflow["33"]["inputs"][strength_key] = lora["strength_model"]
            print(f"✅ 设置LoRA {i+2}: {lora['name']} (强度: {lora['strength_model']})")
        
        print(f"✅ LoRA配置完成: 1个默认LoRA + {len(processed_loras)} 个用户LoRA")
        return workflow
    
    def _convert_path_for_comfyui(self, image_path: str) -> str:
        """转换Windows路径为ComfyUI兼容的路径格式
        
        Args:
            image_path: 原始图像路径
            
        Returns:
            ComfyUI兼容的路径格式
        """
        import os
        from config.settings import COMFYUI_INPUT_DIR
        
        # 获取文件名（不包含路径）
        filename = os.path.basename(image_path)
        
        # ComfyUI期望的是相对于输入目录的文件名
        comfyui_path = filename
        
        print(f"🔄 路径转换: {image_path} -> {comfyui_path}")
        print(f"📁 ComfyUI输入目录: {COMFYUI_INPUT_DIR}")
        return comfyui_path
