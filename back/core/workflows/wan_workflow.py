#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wan2.2视频工作流创建器
基于Wan2.2模型实现图像到视频的生成
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List

from .base_workflow import BaseWorkflow
from config.settings import TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT


class WanWorkflow(BaseWorkflow):
    """Wan2.2视频工作流创建器"""
    
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建Wan2.2视频生成工作流
        
        Args:
            reference_image_path: 参考图像路径
            description: 视频描述
            parameters: 生成参数
            
        Returns:
            工作流字典
        """
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 创建基础工作流
        workflow = self._create_base_workflow(description, validated_params, reference_image_path)
        
        # 添加参考图像节点
        workflow = self._add_reference_image_nodes(workflow, reference_image_path)
        
        # 添加LoRA节点（如果配置了）
        loras = validated_params.get("loras", [])
        if loras:
            workflow = self._add_lora_nodes(workflow, loras, description)
        
        print(f"✅ Wan2.2视频工作流创建完成")
        return workflow
    
    def _create_base_workflow(self, description: str, parameters: Dict[str, Any], reference_image_path: str = None) -> Dict[str, Any]:
        """创建基础工作流结构"""
        # 获取视频参数
        fps = parameters.get("fps", 16)
        duration = parameters.get("duration", 5)  # 秒
        total_frames = fps * duration
        
        # 基础工作流模板
        workflow = {
            # CLIP加载器
            "84": {
                "inputs": {
                    "clip_name": self.model_config.clip_file,
                    "type": "wan",
                    "device": "default"
                },
                "class_type": "CLIPLoader",
                "_meta": {"title": "CLIP加载器"}
            },
            
            # 正面提示词编码
            "93": {
                "inputs": {
                    "text": description,
                    "speak_and_recognation": True,
                    "clip": ["84", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "正面提示词编码"}
            },
            
            # 负面提示词编码
            "89": {
                "inputs": {
                    "text": "blurry, low quality, worst quality, low resolution, pixelated, grainy, distorted, deformed, ugly, bad anatomy, extra limbs, missing limbs, extra fingers, bad hands, bad face, malformed, disfigured, mutated, fused fingers, cluttered background, extra legs, overexposed, oversaturated, static, motionless, watermark, text, signature, jpeg artifacts, compression artifacts, noise, artifacts, poorly drawn, amateur, sketch, draft",
                    "speak_and_recognation": True,
                    "clip": ["84", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "负面提示词编码"}
            },
            
            # VAE加载器
            "90": {
                "inputs": {
                    "vae_name": self.model_config.vae_file
                },
                "class_type": "VAELoader",
                "_meta": {"title": "VAE加载器"}
            },
            
            # 高噪声UNET加载器
            "95": {
                "inputs": {
                    "unet_name": self.model_config.unet_file,
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "高噪声UNET加载器"}
            },
            
            # 低噪声UNET加载器
            "96": {
                "inputs": {
                    "unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "低噪声UNET加载器"}
            },
            
            # 图像加载器
            "97": {
                "inputs": {
                    "image": Path(reference_image_path).name if reference_image_path else "input_image.png"
                },
                "class_type": "LoadImage",
                "_meta": {"title": "加载参考图像"}
            },
            
            # Wan图像到视频节点
            "98": {
                "inputs": {
                    "width": 640,
                    "height": 640,
                    "length": total_frames,
                    "batch_size": 1,
                    "positive": ["93", 0],
                    "negative": ["89", 0],
                    "vae": ["90", 0],
                    "start_image": ["97", 0]
                },
                "class_type": "WanImageToVideo",
                "_meta": {"title": "Wan图像到视频"}
            },
            
            # 高噪声LoRA加载器
            "101": {
                "inputs": {
                    "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors",
                    "strength_model": 1.0,
                    "model": ["95", 0]
                },
                "class_type": "LoraLoaderModelOnly",
                "_meta": {"title": "高噪声LoRA加载器"}
            },
            
            # 低噪声LoRA加载器
            "102": {
                "inputs": {
                    "lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors",
                    "strength_model": 1.0,
                    "model": ["96", 0]
                },
                "class_type": "LoraLoaderModelOnly",
                "_meta": {"title": "低噪声LoRA加载器"}
            },
            
            # 高噪声采样器
            "104": {
                "inputs": {
                    "shift": 5.0,
                    "model": ["101", 0]
                },
                "class_type": "ModelSamplingSD3",
                "_meta": {"title": "高噪声模型采样"}
            },
            
            # 低噪声采样器
            "103": {
                "inputs": {
                    "shift": 5.0,
                    "model": ["102", 0]
                },
                "class_type": "ModelSamplingSD3",
                "_meta": {"title": "低噪声模型采样"}
            },
            
            # 第二阶段采样器（去噪）
            "85": {
                "inputs": {
                    "add_noise": "disable",
                    "noise_seed": 0,
                    "steps": 4,
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "start_at_step": 2,
                    "end_at_step": 4,
                    "return_with_leftover_noise": "disable",
                    "model": ["103", 0],
                    "positive": ["98", 0],  # WanImageToVideo的输出端口0是positive
                    "negative": ["98", 1],  # WanImageToVideo的输出端口1是negative
                    "latent_image": ["86", 0]
                },
                "class_type": "KSamplerAdvanced",
                "_meta": {"title": "第二阶段采样器"}
            },
            
            # 第一阶段采样器（添加噪声）
            "86": {
                "inputs": {
                    "add_noise": "enable",
                    "noise_seed": random.randint(1, 2**32 - 1),
                    "steps": 4,
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "start_at_step": 0,
                    "end_at_step": 2,
                    "return_with_leftover_noise": "enable",
                    "model": ["104", 0],
                    "positive": ["98", 0],  # WanImageToVideo的输出端口0是positive
                    "negative": ["98", 1],  # WanImageToVideo的输出端口1是negative
                    "latent_image": ["98", 2]  # WanImageToVideo的输出端口2是latent_image
                },
                "class_type": "KSamplerAdvanced",
                "_meta": {"title": "第一阶段采样器"}
            },
            
            # VAE解码
            "87": {
                "inputs": {
                    "samples": ["85", 0],
                    "vae": ["90", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE解码"}
            },
            
            # 创建视频
            "94": {
                "inputs": {
                    "fps": fps,
                    "images": ["87", 0]
                },
                "class_type": "CreateVideo",
                "_meta": {"title": "创建视频"}
            },
            
            # 保存视频
            "108": {
                "inputs": {
                    "filename_prefix": "video/yeepay_video",
                    "format": "auto",
                    "codec": "auto",
                    "video": ["94", 0]
                },
                "class_type": "SaveVideo",
                "_meta": {"title": "保存视频"}
            }
        }
        
        return workflow
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证和标准化视频参数"""
        validated = super()._validate_parameters(parameters)
        
        # 验证FPS
        if 'fps' in validated:
            if not isinstance(validated['fps'], int) or validated['fps'] < 1 or validated['fps'] > 60:
                validated['fps'] = 16
        else:
            validated['fps'] = 16
        
        # 验证视频时长
        if 'duration' in validated:
            if not isinstance(validated['duration'], int) or validated['duration'] < 1 or validated['duration'] > 30:
                validated['duration'] = 5
        else:
            validated['duration'] = 5
        
        return validated
    
    def _add_lora_nodes(self, workflow: Dict[str, Any], loras: List[Dict[str, Any]], description: str) -> Dict[str, Any]:
        """添加LoRA节点（Wan2.2视频模型暂不支持LoRA，预留接口）"""
        # Wan2.2视频模型目前使用固定的LoRA配置
        # 这里可以扩展支持自定义LoRA
        print("ℹ️ Wan2.2视频模型使用固定LoRA配置")
        return workflow
    
    def _add_reference_image_nodes(self, workflow: Dict[str, Any], image_path: str) -> Dict[str, Any]:
        """添加参考图像节点"""
        # 复制参考图像到ComfyUI的input目录
        try:
            from config.settings import COMFYUI_INPUT_DIR
            import shutil
            
            source_path = Path(image_path)
            if source_path.exists():
                # 复制到ComfyUI的input目录
                dest_path = COMFYUI_INPUT_DIR / source_path.name
                shutil.copy2(source_path, dest_path)
                print(f"✅ 参考图像已复制到ComfyUI input目录: {dest_path}")
            else:
                print(f"⚠️ 参考图像不存在: {image_path}")
        except Exception as e:
            print(f"❌ 复制参考图像失败: {e}")
        
        # 图像加载节点已在基础工作流中配置
        print(f"✅ 参考图像配置完成: {Path(image_path).name}")
        return workflow
