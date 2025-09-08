#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen多图融合工作流实现
专门处理Qwen模型的多图融合功能
"""

import json
import os
from typing import Any, Dict, List

from .base_workflow import BaseWorkflow


class QwenFusionWorkflow(BaseWorkflow):
    """Qwen多图融合工作流创建器"""
    
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """实现抽象基类的create_workflow方法
        
        Args:
            reference_image_path: 参考图像路径（多图融合时忽略此参数）
            description: 融合描述
            parameters: 生成参数，包含reference_image_paths列表
            
        Returns:
            Qwen多图融合工作流字典
        """
        # 从parameters中获取多图路径
        image_paths = parameters.get("reference_image_paths", [])
        if not image_paths:
            raise ValueError("多图融合需要提供reference_image_paths参数")
        
        return self.create_fusion_workflow(image_paths, description, parameters)
    
    def create_fusion_workflow(self, image_paths: List[str], description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建Qwen多图融合工作流
        
        Args:
            image_paths: 图像路径列表（2-5张图像）
            description: 融合描述
            parameters: 生成参数
            
        Returns:
            Qwen多图融合工作流字典
        """
        print(f"🎨 创建Qwen多图融合工作流: {self.model_config.display_name}")
        
        # 验证图像数量
        if len(image_paths) < 2:
            raise ValueError("多图融合至少需要2张图像")
        if len(image_paths) > 5:
            raise ValueError("多图融合最多支持5张图像")
        
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 加载工作流模板
        workflow = self._load_fusion_template()
        
        # 更新模型配置
        workflow = self._update_model_config(workflow)
        
        # 更新文本描述
        workflow = self._update_text_description(workflow, description)
        
        # 更新采样参数
        workflow = self._update_sampling_parameters(workflow, validated_params)
        
        # 更新保存路径
        workflow = self._update_save_path(workflow)
        
        # 处理多图输入
        workflow = self._add_multi_image_nodes(workflow, image_paths)
        
        # 处理LoRA配置
        loras = validated_params.get("loras", [])
        if loras:
            workflow = self._update_lora_config(workflow, loras)
        
        print(f"✅ Qwen多图融合工作流创建完成，处理 {len(image_paths)} 张图像")
        return workflow
    
    def _load_fusion_template(self) -> Dict[str, Any]:
        """加载多图融合工作流模板"""
        try:
            workflow_path = "workflows/qwen_image_fusion_workflow.json"
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            print(f"✅ 加载Qwen多图融合工作流模板: {workflow_path}")
            return workflow
        except FileNotFoundError:
            print(f"⚠️ Qwen多图融合工作流模板文件不存在，使用内置模板")
            return self._get_builtin_fusion_template()
        except json.JSONDecodeError as e:
            print(f"❌ Qwen多图融合工作流模板文件格式错误: {str(e)}")
            return self._get_builtin_fusion_template()
    
    def _get_builtin_fusion_template(self) -> Dict[str, Any]:
        """获取内置多图融合模板"""
        from config.settings import TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT
        
        return {
            "149": {
                "class_type": "ImageConcatMulti",
                "inputs": {
                    "inputcount": 3,
                    "direction": "right",
                    "match_image_size": False,
                    "image_1": ["152", 0],
                    "image_2": ["151", 0],
                    "image_3": ["150", 0]
                },
                "_meta": {"title": "Image Concatenate Multi"}
            },
            "150": {
                "class_type": "LoadImage",
                "inputs": {"image": "{{image_1_path}}"},
                "_meta": {"title": "加载图像1"}
            },
            "151": {
                "class_type": "LoadImage", 
                "inputs": {"image": "{{image_2_path}}"},
                "_meta": {"title": "加载图像2"}
            },
            "152": {
                "class_type": "LoadImage",
                "inputs": {"image": "{{image_3_path}}"},
                "_meta": {"title": "加载图像3"}
            },
            "153": {
                "class_type": "FluxKontextImageScale",
                "inputs": {"image": ["149", 0]},
                "_meta": {"title": "FluxKontextImageScale"}
            },
            "156": {
                "class_type": "VAELoader",
                "inputs": {"vae_name": "qwen_image_vae.safetensors"},
                "_meta": {"title": "VAE加载器"}
            },
            "157": {
                "class_type": "TextEncodeQwenImageEdit",
                "inputs": {
                    "prompt": "色调艳丽，过曝，静态，细节模糊不清，风格，作品，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，杂乱的背景，三条腿，",
                    "speak_and_recognation": True,
                    "clip": ["165", 0],
                    "vae": ["156", 0],
                    "image": ["153", 0]
                },
                "_meta": {"title": "TextEncodeQwenImageEdit"}
            },
            "158": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 745159675686423,
                    "steps": 20,
                    "cfg": 2.5,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "model": ["160", 0],
                    "positive": ["169", 0],
                    "negative": ["157", 0],
                    "latent_image": ["164", 0]
                },
                "_meta": {"title": "K采样器"}
            },
            "160": {
                "class_type": "ModelSamplingAuraFlow",
                "inputs": {
                    "shift": 3.1000000000000005,
                    "model": ["167", 0]
                },
                "_meta": {"title": "模型采样算法AuraFlow"}
            },
            "161": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["158", 0],
                    "vae": ["156", 0]
                },
                "_meta": {"title": "VAE解码"}
            },
            "162": {
                "class_type": "VAEEncode",
                "inputs": {
                    "pixels": ["153", 0],
                    "vae": ["156", 0]
                },
                "_meta": {"title": "VAE编码"}
            },
            "164": {
                "class_type": "LatentUpscale",
                "inputs": {
                    "upscale_method": "nearest-exact",
                    "width": 640,
                    "height": 360,
                    "crop": "disabled",
                    "samples": ["162", 0]
                },
                "_meta": {"title": "Latent缩放"}
            },
            "165": {
                "class_type": "CLIPLoader",
                "inputs": {
                    "clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                    "type": "qwen_image",
                    "device": "default"
                },
                "_meta": {"title": "CLIP加载器"}
            },
            "166": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "yeepay/yeepay",
                    "images": ["161", 0]
                },
                "_meta": {"title": "保存图像"}
            },
            "167": {
                "class_type": "UNETLoader",
                "inputs": {
                    "unet_name": "qwen_image_edit_fp8_e4m3fn.safetensors",
                    "weight_dtype": "default"
                },
                "_meta": {"title": "UNET加载器"}
            },
            "169": {
                "class_type": "TextEncodeQwenImageEdit",
                "inputs": {
                    "prompt": "{{description}}",
                    "speak_and_recognation": True,
                    "clip": ["165", 0],
                    "vae": ["156", 0],
                    "image": ["153", 0]
                },
                "_meta": {"title": "TextEncodeQwenImageEdit"}
            }
        }
    
    def _add_multi_image_nodes(self, workflow: Dict[str, Any], image_paths: List[str]) -> Dict[str, Any]:
        """添加多图输入节点到工作流
        
        Args:
            workflow: 工作流字典
            image_paths: 图像路径列表
            
        Returns:
            更新后的工作流字典
        """
        print(f"📸 为Qwen多图融合工作流添加 {len(image_paths)} 张图像")
        
        # 动态调整ImageConcatMulti节点的inputcount
        if "149" in workflow:
            workflow["149"]["inputs"]["inputcount"] = len(image_paths)
            print(f"✅ 设置图像拼接数量: {len(image_paths)}")
        
        # 为每张图像创建LoadImage节点
        for i, image_path in enumerate(image_paths):
            node_id = str(150 + i)  # 从150开始
            # 转换Windows路径为ComfyUI兼容的路径格式
            comfyui_path = self._convert_path_for_comfyui(image_path)
            workflow[node_id] = {
                "inputs": {
                    "image": comfyui_path
                },
                "class_type": "LoadImage",
                "_meta": {"title": f"加载图像{i+1}"}
            }
            print(f"✅ 创建LoadImage节点 {node_id}: {os.path.basename(image_path)} -> {comfyui_path}")
        
        # 更新ImageConcatMulti节点的图像连接
        if "149" in workflow:
            for i in range(len(image_paths)):
                image_key = f"image_{i+1}"
                node_id = str(150 + i)
                workflow["149"]["inputs"][image_key] = [node_id, 0]
                print(f"✅ 连接图像 {i+1} 到拼接节点: {node_id}")
        
        # 如果图像数量少于3张，禁用多余的图像输入
        for i in range(len(image_paths), 5):  # 最多支持5张
            image_key = f"image_{i+1}"
            if image_key in workflow.get("149", {}).get("inputs", {}):
                workflow["149"]["inputs"][image_key] = ["150", 0]  # 连接到第一张图像
                print(f"✅ 禁用多余图像输入: {image_key}")
        
        print(f"✅ Qwen多图融合节点配置完成，处理 {len(image_paths)} 张图像")
        return workflow
    
    def _update_model_config(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新模型配置"""
        if "167" in workflow:
            workflow["167"]["inputs"]["unet_name"] = self.model_config.unet_file
            print(f"✅ 更新UNETLoader: {self.model_config.unet_file}")
        
        if "165" in workflow:
            workflow["165"]["inputs"]["clip_name"] = self.model_config.clip_file
            print(f"✅ 更新CLIPLoader: {self.model_config.clip_file}")
        
        if "156" in workflow:
            workflow["156"]["inputs"]["vae_name"] = self.model_config.vae_file
            print(f"✅ 更新VAELoader: {self.model_config.vae_file}")
        
        return workflow
    
    def _update_text_description(self, workflow: Dict[str, Any], description: str) -> Dict[str, Any]:
        """更新文本描述"""
        if "169" in workflow:
            workflow["169"]["inputs"]["prompt"] = description
            print(f"✅ 更新融合描述文本: {description[:50]}...")
        
        return workflow
    
    def _update_sampling_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新采样参数"""
        if "158" in workflow:
            if parameters.get("steps"):
                workflow["158"]["inputs"]["steps"] = parameters["steps"]
            if parameters.get("seed"):
                workflow["158"]["inputs"]["seed"] = parameters["seed"]
            if parameters.get("cfg"):
                workflow["158"]["inputs"]["cfg"] = parameters["cfg"]
            print(f"✅ 更新KSampler参数: 步数={parameters.get('steps', 20)}, 种子={parameters.get('seed', 'random')}")
        
        # 动态更新图像尺寸配置
        workflow = self._update_image_dimensions(workflow)
        
        return workflow
    
    def _update_image_dimensions(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """动态更新图像尺寸配置"""
        # 更新节点164（LatentUpscale）的尺寸配置
        if "164" in workflow:
            workflow["164"]["inputs"]["width"] = 640
            workflow["164"]["inputs"]["height"] = 360
            print(f"✅ 动态更新多图融合图像尺寸: 640x360")
        
        return workflow
    
    def _update_save_path(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新保存路径"""
        if "166" in workflow:
            workflow["166"]["inputs"]["filename_prefix"] = "yeepay/yeepay"
            print(f"✅ 更新保存路径: yeepay/yeepay")
        
        return workflow
    
    def _update_lora_config(self, workflow: Dict[str, Any], loras: list) -> Dict[str, Any]:
        """更新LoRA配置（多图融合工作流暂不支持LoRA）"""
        print("ℹ️ 多图融合工作流暂不支持LoRA配置")
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
