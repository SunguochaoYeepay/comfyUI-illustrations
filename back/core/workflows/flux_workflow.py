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
        
        # 从数据库加载基础工作流
        workflow = self._load_workflow_template()
        
        # 更新基础模型
        workflow = self._update_base_model(workflow, validated_params)
        
        # 清理无效的图像引用节点
        workflow = self._clean_invalid_image_nodes(workflow)
        
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
    
    def _update_base_model(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新基础模型"""
        base_model = parameters.get("base_model", self.model_config.unet_file)
        
        if "37" in workflow:  # UNETLoader节点
            workflow["37"]["inputs"]["unet_name"] = base_model
            print(f"🔄 更新基础模型: {base_model}")
        
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
        comfyui_path = self._convert_path_for_comfyui(image_path)
        workflow["142"] = {
            "inputs": {
                "image": comfyui_path,
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
        """更新最终参数（安全更新，检查节点是否存在）"""
        # 更新生成参数 - 检查节点31是否存在
        if "31" in workflow:
            if parameters.get("steps"):
                workflow["31"]["inputs"]["steps"] = parameters["steps"]
            
            if parameters.get("cfg"):
                workflow["31"]["inputs"]["cfg"] = parameters["cfg"]
            
            # 处理生成数量
            count = parameters.get("count", 1)
            workflow["31"]["inputs"]["batch_size"] = count
        
        # 更新引导参数 - 检查节点35是否存在
        if "35" in workflow and parameters.get("guidance"):
            workflow["35"]["inputs"]["guidance"] = parameters["guidance"]
        
        # 处理生成数量 - 检查节点136是否存在
        count = parameters.get("count", 1)
        if count > 1 and "136" in workflow:
            workflow["136"]["inputs"]["save_all"] = True
            print(f"设置batch_size为: {count}")
        
        # 设置种子 - 检查节点31是否存在
        if "31" in workflow:
            if parameters.get("seed"):
                workflow["31"]["inputs"]["seed"] = parameters["seed"]
                print(f"使用指定种子: {parameters['seed']}")
            else:
                seed = random.randint(1, 2**32 - 1)
                workflow["31"]["inputs"]["seed"] = seed
                print(f"使用随机种子: {seed}")
        
        # 更新图像尺寸
        size_str = parameters.get("size", "1024x1024")
        try:
            width, height = map(int, size_str.split('x'))
        except (ValueError, AttributeError):
            # 如果解析失败，使用默认尺寸
            width, height = 1024, 1024
            print(f"⚠️ 尺寸解析失败，使用默认尺寸: {width}x{height}")
        
        # 更新节点42（FluxKontextImageScale）的尺寸配置
        if "42" in workflow:
            workflow["42"]["inputs"]["width"] = width
            workflow["42"]["inputs"]["height"] = height
            print(f"✅ 更新Flux图像尺寸: {width}x{height}")
        
        # 安全地打印参数信息
        steps_info = workflow["31"]["inputs"]["steps"] if "31" in workflow else "N/A"
        cfg_info = workflow["31"]["inputs"]["cfg"] if "31" in workflow else "N/A"
        guidance_info = workflow["35"]["inputs"]["guidance"] if "35" in workflow else "N/A"
        print(f"工作流参数更新完成: 步数={steps_info}, CFG={cfg_info}, 引导={guidance_info}, 尺寸={width}x{height}")
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
    
    def _load_workflow_template(self) -> Dict[str, Any]:
        """从数据库加载工作流模板"""
        import sqlite3
        import json
        from pathlib import Path
        
        # 数据库路径
        db_path = Path(__file__).parent.parent.parent.parent / "admin" / "admin.db"
        
        if not db_path.exists():
            print(f"⚠️ 数据库文件不存在，使用内置模板: {db_path}")
            return self._create_base_workflow("", {})
        
        # 从数据库加载工作流
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT workflow_json FROM workflows WHERE name = ?", ("flux1_flux_kontext_dev_basic_2",))
            result = cursor.fetchone()
            
            if not result:
                print(f"⚠️ 数据库中未找到Flux工作流，使用内置模板")
                return self._create_base_workflow("", {})
            
            workflow = json.loads(result[0])
            print(f"✅ 从数据库加载Flux工作流模板: flux1_flux_kontext_dev_basic_2")
            return workflow
            
        except Exception as e:
            print(f"❌ 从数据库加载Flux工作流失败: {e}，使用内置模板")
            return self._create_base_workflow("", {})
        finally:
            conn.close()
    
    def _clean_invalid_image_nodes(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """清理无效的图像引用节点（保守清理策略）"""
        # 需要清理的节点ID列表
        invalid_nodes = ["142", "147"]  # 根据错误信息中的节点ID
        
        # 只删除无效的图像引用节点，不删除依赖节点
        for node_id in invalid_nodes:
            if node_id in workflow:
                node = workflow[node_id]
                # 检查是否是LoadImageOutput节点且引用了无效文件
                if (node.get("class_type") == "LoadImageOutput" and 
                    "image" in node.get("inputs", {})):
                    image_path = node["inputs"]["image"]
                    # 如果引用了不存在的输出文件，移除这个节点
                    if "[output]" in image_path:
                        print(f"🧹 清理无效的图像引用节点 {node_id}: {image_path}")
                        del workflow[node_id]
        
        # 清理引用已删除节点的输入，但不删除节点本身
        for node_id, node in workflow.items():
            if "inputs" in node:
                for input_name, input_value in node["inputs"].items():
                    # 检查是否引用了已删除的节点
                    if isinstance(input_value, list) and len(input_value) >= 1:
                        referenced_node = str(input_value[0])
                        if referenced_node in invalid_nodes:
                            print(f"🧹 清理节点 {node_id} 中对已删除节点 {referenced_node} 的引用")
                            # 将引用设置为None或空值，而不是删除整个节点
                            node["inputs"][input_name] = None
        
        # 修复节点42的连接 - FluxKontextImageScale需要一个图像输入
        if "42" in workflow:
            # 检查节点42的类型
            if workflow["42"].get("class_type") == "FluxKontextImageScale":
                # 检查节点42是否已经有有效的图像输入
                if "image" not in workflow["42"]["inputs"] or workflow["42"]["inputs"]["image"] is None:
                    # 添加一个新的EmptyImage节点
                    workflow["200"] = {
                        "inputs": {
                            "width": 1024,
                            "height": 1024,
                            "batch_size": 1,
                            "color": 0
                        },
                        "class_type": "EmptyImage",
                        "_meta": {"title": "空图像"}
                    }
                    # 将节点42连接到新的EmptyImage节点
                    workflow["42"]["inputs"]["image"] = ["200", 0]
                    print("✅ 为节点42添加EmptyImage输入")
        
        # 删除节点146（ImageStitch），因为它的输入已经被删除
        if "146" in workflow:
            del workflow["146"]
            print("✅ 删除节点146（ImageStitch）")
        
        # 修复其他节点对节点146的引用
        for node_id, node in workflow.items():
            if "inputs" in node:
                for input_name, input_value in node["inputs"].items():
                    if isinstance(input_value, list) and len(input_value) >= 1:
                        referenced_node = str(input_value[0])
                        if referenced_node == "146":
                            # 将引用重定向到节点42
                            node["inputs"][input_name] = ["42", 0]
                            print(f"✅ 将节点 {node_id} 的 {input_name} 引用重定向到节点42")
        
        return workflow
