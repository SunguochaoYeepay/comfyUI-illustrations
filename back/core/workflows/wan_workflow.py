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
from config.settings import TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT, ADMIN_BACKEND_URL


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
        print(f"🎬 创建Wan2.2视频工作流: {self.model_config.display_name}")
        
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 从数据库加载工作流模板
        workflow = self._load_workflow_template()
        
        # 更新文本描述
        workflow = self._update_text_description(workflow, description)
        
        # 更新采样参数
        workflow = self._update_sampling_parameters(workflow, validated_params)
        
        # 更新视频参数
        workflow = self._update_video_parameters(workflow, validated_params)
        
        # 更新保存路径
        workflow = self._update_save_path(workflow)
        
        # 处理参考图像
        if reference_image_path:
            workflow = self._add_reference_image_nodes(workflow, reference_image_path)
            print(f"📸 已添加参考图支持: {reference_image_path}")
        else:
            # 无图模式：清除默认图像节点
            workflow = self._clear_reference_image_nodes(workflow)
            print("📸 无参考图，使用无参考图模式")
        
        # 处理LoRA配置
        loras = validated_params.get("loras", [])
        if loras:
            workflow = self._update_lora_config(workflow, loras)
        
        print(f"✅ Wan2.2视频工作流创建完成")
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
            
            # 查找WAN工作流
            for workflow_data in workflows:
                if workflow_data.get("code") == "wan2.2_video_generation_workflow":
                    workflow_json = workflow_data.get("workflow_json")
                    if workflow_json:
                        workflow = json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
                        print(f"✅ 通过admin API加载WAN工作流模板: wan2.2_video_generation_workflow")
                        return workflow
            
            print(f"⚠️ admin API中未找到WAN工作流，使用内置模板")
            return self._get_builtin_template()
            
        except Exception as e:
            print(f"❌ 通过admin API加载WAN工作流失败: {e}，使用内置模板")
            return self._get_builtin_template()
    
    def _get_builtin_template(self) -> Dict[str, Any]:
        """获取内置模板（降级方案）"""
        print("⚠️ 使用WAN工作流内置模板")
        # 返回一个简化的模板，避免与admin模板冲突
        return {
            "6": {
                "inputs": {"text": "{{description}}", "clip": ["38", 0]},
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP文本编码器"}
            },
            "7": {
                "inputs": {"text": "blurry, low quality, worst quality", "clip": ["38", 0]},
                "class_type": "CLIPTextEncode", 
                "_meta": {"title": "CLIP文本编码器"}
            },
            "37": {
                "inputs": {"unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"},
                "class_type": "UNETLoader",
                "_meta": {"title": "UNET加载器"}
            },
            "38": {
                "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"},
                "class_type": "CLIPLoader",
                "_meta": {"title": "CLIP加载器"}
            },
            "39": {
                "inputs": {"vae_name": "wan_2.1_vae.safetensors"},
                "class_type": "VAELoader",
                "_meta": {"title": "VAE加载器"}
            },
            "54": {
                "inputs": {"shift": 5, "model": ["91", 0]},
                "class_type": "ModelSamplingSD3",
                "_meta": {"title": "模型采样算法SD3"}
            },
            "55": {
                "inputs": {"shift": 5, "model": ["92", 0]},
                "class_type": "ModelSamplingSD3",
                "_meta": {"title": "模型采样算法SD3"}
            },
            "56": {
                "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"},
                "class_type": "UNETLoader",
                "_meta": {"title": "UNET加载器"}
            },
            "8": {
                "inputs": {"samples": ["58", 0], "vae": ["39", 0]},
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE解码"}
            },
            "57": {
                "inputs": {"add_noise": "enable", "noise_seed": 57936518952277, "steps": 4, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "start_at_step": 0, "end_at_step": 2, "return_with_leftover_noise": "enable", "model": ["54", 0], "positive": ["67", 0], "negative": ["67", 1], "latent_image": ["67", 2]},
                "class_type": "KSamplerAdvanced",
                "_meta": {"title": "K采样器(高级)"}
            },
            "58": {
                "inputs": {"add_noise": "disable", "noise_seed": 788333148344562, "steps": 4, "cfg": 1, "sampler_name": "euler", "scheduler": "simple", "start_at_step": 2, "end_at_step": 10000, "return_with_leftover_noise": "disable", "model": ["55", 0], "positive": ["67", 0], "negative": ["67", 1], "latent_image": ["57", 0]},
                "class_type": "KSamplerAdvanced",
                "_meta": {"title": "K采样器(高级)"}
            },
            "60": {
                "inputs": {"fps": 16, "images": ["8", 0]},
                "class_type": "CreateVideo",
                "_meta": {"title": "创建视频"}
            },
            "62": {
                "inputs": {"image": "generated-image-1758020573908.png"},
                "class_type": "LoadImage",
                "_meta": {"title": "结束图"}
            },
            "68": {
                "inputs": {"image": "generated-image-1757490119660.png"},
                "class_type": "LoadImage",
                "_meta": {"title": "开始图"}
            },
            "61": {
                "inputs": {"filename_prefix": "video/ComfyUI", "format": "auto", "codec": "auto", "video": ["60", 0]},
                "class_type": "SaveVideo",
                "_meta": {"title": "保存视频"}
            },
            "67": {
                "inputs": {"width": 640, "height": 640, "length": 81, "batch_size": 1, "positive": ["6", 0], "negative": ["7", 0], "vae": ["39", 0], "start_image": ["68", 0], "end_image": ["62", 0]},
                "class_type": "WanFirstLastFrameToVideo",
                "_meta": {"title": "WanFirstLastFrameToVideo"}
            },
            "91": {
                "inputs": {"lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors", "strength_model": 1, "model": ["37", 0]},
                "class_type": "LoraLoaderModelOnly",
                "_meta": {"title": "LoRA加载器(仅模型)"}
            },
            "92": {
                "inputs": {"lora_name": "wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors", "strength_model": 1, "model": ["56", 0]},
                "class_type": "LoraLoaderModelOnly",
                "_meta": {"title": "LoRA加载器(仅模型)"}
            }
        }
    
    
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
    
    def _add_reference_image_nodes(self, workflow: Dict[str, Any], image_path) -> Dict[str, Any]:
        """添加参考图像节点"""
        # 处理单个路径或路径列表
        print(f"🔍 原始image_path类型: {type(image_path)}")
        print(f"🔍 原始image_path内容: {image_path}")
        
        if isinstance(image_path, list):
            image_paths = image_path
        else:
            image_paths = [image_path]
        
        print(f"🔍 处理后的image_paths: {image_paths}")
        
        # 清理路径，移除可能的引号和括号
        cleaned_paths = []
        for path in image_paths:
            if isinstance(path, str):
                # 移除可能的引号和括号，包括所有可能的字符
                cleaned_path = path.strip("'\"[](){} ")
                # 如果路径包含逗号，说明是多个路径拼接的，需要分割
                if ',' in cleaned_path:
                    # 分割路径并清理每个路径
                    sub_paths = [p.strip("'\"[](){} ") for p in cleaned_path.split(',')]
                    cleaned_paths.extend(sub_paths)
                else:
                    cleaned_paths.append(cleaned_path)
            else:
                cleaned_paths.append(str(path))
        image_paths = cleaned_paths
        
        # 复制参考图像到ComfyUI的input目录
        try:
            from config.settings import COMFYUI_INPUT_DIR
            import shutil
            
            for path in image_paths:
                source_path = Path(path)
                if source_path.exists():
                    # 复制到ComfyUI的input目录
                    dest_path = COMFYUI_INPUT_DIR / source_path.name
                    shutil.copy2(source_path, dest_path)
                    print(f"✅ 参考图像已复制到ComfyUI input目录: {dest_path}")
                else:
                    print(f"⚠️ 参考图像不存在: {path}")
        except Exception as e:
            print(f"❌ 复制参考图像失败: {e}")
        
        # 配置开始图和结束图节点
        print(f"🔍 处理图像路径数量: {len(image_paths)}")
        for i, path in enumerate(image_paths):
            print(f"🔍 图像路径{i+1}: {path}")
        
        # 新模型只需要开始图，不需要结束图
        if len(image_paths) >= 1:
            # 使用第一个图像作为开始图
            start_image = Path(image_paths[0]).name
            
            # 更新节点68（开始图）
            if "68" in workflow:
                workflow["68"]["inputs"]["image"] = start_image
                print(f"✅ 开始图配置: {start_image}")
            else:
                print("⚠️ 工作流中未找到节点68（开始图）")
            
            # 检查是否有结束图节点（旧模型）
            if "62" in workflow:
                print("ℹ️ 检测到旧模型工作流，配置结束图")
                if len(image_paths) >= 2:
                    end_image = Path(image_paths[-1]).name
                    workflow["62"]["inputs"]["image"] = end_image
                    print(f"✅ 结束图配置: {end_image}")
                else:
                    # 如果只有一个图像，同时作为结束图
                    workflow["62"]["inputs"]["image"] = start_image
                    print(f"✅ 结束图配置: {start_image}")
            else:
                print("ℹ️ 新模型工作流，无需配置结束图")
        
        return workflow
    
    def _update_text_description(self, workflow: Dict[str, Any], description: str) -> Dict[str, Any]:
        """更新文本描述"""
        # 更新正面提示词
        if "6" in workflow:
            workflow["6"]["inputs"]["text"] = description
        
        print(f"✅ WAN文本描述更新完成: {description[:50]}...")
        return workflow
    
    def _update_sampling_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新采样参数"""
        # 更新采样器参数
        if "57" in workflow:
            workflow["57"]["inputs"]["noise_seed"] = parameters.get("seed", random.randint(1, 2**31 - 1))  # 限制在int32范围内
        if "58" in workflow:
            workflow["58"]["inputs"]["noise_seed"] = parameters.get("seed", random.randint(1, 2**31 - 1))  # 限制在int32范围内
        
        print("✅ WAN采样参数更新完成")
        return workflow
    
    def _clear_reference_image_nodes(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """清除参考图像节点（无图模式）"""
        # 清除节点68（开始图）
        if "68" in workflow:
            workflow["68"]["inputs"]["image"] = ""
            print("✅ 已清除开始图节点68")
        
        # 清除节点62（结束图）
        if "62" in workflow:
            workflow["62"]["inputs"]["image"] = ""
            print("✅ 已清除结束图节点62")
        
        # 清除节点67中的图像连接
        if "67" in workflow:
            # 清除start_image连接
            if "start_image" in workflow["67"]["inputs"]:
                workflow["67"]["inputs"]["start_image"] = ["", 0]
            
            # 清除end_image连接（如果存在）
            if "end_image" in workflow["67"]["inputs"]:
                workflow["67"]["inputs"]["end_image"] = ["", 0]
            
            print("✅ 已清除节点67中的图像连接")
        
        print("📸 无图模式配置完成")
        return workflow
    
    def _update_video_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新视频参数"""
        fps = parameters.get("fps", 16)
        duration = parameters.get("duration", 5)
        total_frames = fps * duration
        
        # 更新视频创建节点
        if "60" in workflow:
            workflow["60"]["inputs"]["fps"] = fps
        
        # 更新WanFirstLastFrameToVideo节点
        if "67" in workflow:
            workflow["67"]["inputs"]["fps"] = fps
            workflow["67"]["inputs"]["length"] = total_frames
        
        print(f"✅ WAN视频参数更新完成: fps={fps}, duration={duration}s, frames={total_frames}")
        return workflow
    
    def _update_save_path(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新保存路径"""
        # 更新视频保存节点
        if "61" in workflow:
            workflow["61"]["inputs"]["filename_prefix"] = "video/ComfyUI"
        
        print("✅ WAN保存路径更新完成")
        return workflow
    
    def _update_lora_config(self, workflow: Dict[str, Any], loras: List[Dict[str, Any]]) -> Dict[str, Any]:
        """更新LoRA配置（WAN模型使用固定LoRA）"""
        # WAN2.2模型使用固定的LoRA配置，这里可以扩展支持自定义LoRA
        print("ℹ️ WAN2.2模型使用固定LoRA配置")
        return workflow
