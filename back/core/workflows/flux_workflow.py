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
    DEFAULT_STEPS, DEFAULT_COUNT, ADMIN_BACKEND_URL
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
        width, height = self._get_image_dimensions(parameters)
        
        # 检查是否是多图融合模式
        reference_image_paths = parameters.get("reference_image_paths", [])
        if reference_image_paths and len(reference_image_paths) >= 2:
            # 多图融合模式（ImageStitch只支持2张图）
            if len(reference_image_paths) > 2:
                print(f"⚠️ ImageStitch节点只支持2张图，将使用前2张图像")
                reference_image_paths = reference_image_paths[:2]
            
            print(f"🖼️ 检测到2图融合模式，处理 {len(reference_image_paths)} 张图像")
            processed_image_paths = []
            for path in reference_image_paths:
                processed_path = self._process_reference_image(path, width, height)
                if processed_path:
                    processed_image_paths.append(processed_path)
            
            if processed_image_paths:
                workflow = self._load_image_to_image_workflow_template()
            else:
                print("📝 多图处理失败，使用文生图工作流")
                workflow = self._load_text_to_image_workflow_template()
        else:
            # 单图模式
            processed_image_path = self._process_reference_image(reference_image_path, width, height)
            
            # 根据是否有参考图选择不同的工作流模板
            if processed_image_path:
                print("🖼️ 检测到参考图像，使用图生图工作流")
                workflow = self._load_image_to_image_workflow_template()
            else:
                print("📝 无参考图像，使用文生图工作流")
                workflow = self._load_text_to_image_workflow_template()
        
        # 基础模型已在工作流模板中配置，无需强制更新
        
        # 处理LoRA配置和文本描述更新
        loras = validated_params.get("loras", [])
        workflow = self._add_lora_nodes(workflow, loras, description)
        
        # 处理参考图像
        if reference_image_paths and len(reference_image_paths) >= 2:
            # 多图融合模式
            workflow = self._add_reference_image_nodes(workflow, processed_image_paths)
        elif processed_image_path:
            # 单图模式
            workflow = self._add_reference_image_nodes(workflow, processed_image_path)
        
        # 更新最终参数
        workflow = self._update_final_parameters(workflow, validated_params, description)
        
        # 处理模板变量（如{{description}}）
        workflow = self._process_template_variables(workflow, description, validated_params)
        
        print(f"✅ Flux工作流创建完成，包含 {len(workflow)} 个节点")
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
        """添加参考图像节点到Flux工作流"""
        print("📸 为Flux工作流添加参考图支持")
        
        # 检查是否是多图融合模式
        image_paths = []
        if isinstance(image_path, list):
            image_paths = image_path
        else:
            image_paths = [image_path]
        
        # ImageStitch只支持2张图，限制数量
        if len(image_paths) > 2:
            print(f"⚠️ ImageStitch节点只支持2张图，将使用前2张图像")
            image_paths = image_paths[:2]
        
        print(f"📸 处理 {len(image_paths)} 张参考图像")
        
        # 添加LoadImage节点
        load_image_nodes = []
        for i, path in enumerate(image_paths):
            node_id = str(142 + i)  # 142, 143
            comfyui_path = self._convert_path_for_comfyui(path)
            workflow[node_id] = {
                "inputs": {
                    "image": comfyui_path,
                    "upload": "image"
                },
                "class_type": "LoadImage",
                "_meta": {"title": f"加载参考图像{i+1}"}
            }
            load_image_nodes.append([node_id, 0])
        
        # 添加ImageStitch节点（只支持image1和image2）
        stitch_inputs = {
            "direction": "right",
            "match_image_size": True,
            "spacing_width": 0,
            "spacing_color": "white",
            "image1": load_image_nodes[0]
        }
        
        # 如果有第二张图，添加image2输入
        if len(load_image_nodes) > 1:
            stitch_inputs["image2"] = load_image_nodes[1]
        
        workflow["146"] = {
            "inputs": stitch_inputs,
            "class_type": "ImageStitch",
            "_meta": {"title": "Image Stitch"}
        }
        
        # 添加FluxKontextImageScale节点（尺寸将在_update_final_parameters中更新）
        workflow["42"] = {
            "inputs": {
                "image": ["146", 0],
                "width": 1024,  # 临时值，会被_update_final_parameters覆盖
                "height": 1024,  # 临时值，会被_update_final_parameters覆盖
                "crop": "disabled"
            },
            "class_type": "FluxKontextImageScale",
            "_meta": {"title": "FluxKontextImageScale"}
        }
        
        # 添加VAEEncode节点
        workflow["124"] = {
            "inputs": {
                "pixels": ["42", 0],
                "vae": ["39", 0]
            },
            "class_type": "VAEEncode",
            "_meta": {"title": "VAE编码"}
        }
        
        # 更新KSampler的latent_image输入
        if "31" in workflow:
            workflow["31"]["inputs"]["latent_image"] = ["124", 0]
            print("✅ 更新KSampler的latent_image输入为VAEEncode输出")
        
        if len(image_paths) > 1:
            print(f"✅ 2图融合节点添加完成: {len(image_paths)}个LoadImage -> ImageStitch -> FluxKontextImageScale -> VAEEncode")
        else:
            print(f"✅ 参考图节点添加完成: LoadImage -> ImageStitch -> FluxKontextImageScale -> VAEEncode")
        return workflow
    
    def _convert_path_for_comfyui(self, image_path: str) -> str:
        """将图像路径转换为ComfyUI可用的路径"""
        from config.settings import COMFYUI_INPUT_DIR
        
        # 获取文件名
        filename = image_path.split('/')[-1] if '/' in image_path else image_path.split('\\')[-1]
        
        # ComfyUI期望的是相对于输入目录的文件名
        comfyui_path = filename
        
        print(f"🔄 路径转换: {image_path} -> {comfyui_path}")
        print(f"📁 ComfyUI输入目录: {COMFYUI_INPUT_DIR}")
        return comfyui_path
    
    def _load_text_to_image_workflow_template(self) -> Dict[str, Any]:
        """加载文生图工作流模板"""
        try:
            import requests
            import json
            
            # 通过admin API获取工作流配置
            admin_url = f"{ADMIN_BACKEND_URL}/api/admin/config-sync/workflows"
            response = requests.get(admin_url, timeout=5)
            
            if response.status_code != 200:
                raise Exception(f"admin API调用失败: {response.status_code}")
            
            data = response.json()
            workflows = data.get("workflows", [])
            
            # 查找文生图工作流
            for workflow_data in workflows:
                if workflow_data.get("code") == "flux_text_to_image_workflow":
                    workflow_json = workflow_data.get("workflow_json")
                    if workflow_json:
                        workflow = json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
                        print(f"✅ 通过admin API加载Flux工作流模板: flux_text_to_image_workflow")
                        return workflow
            
            raise ValueError(f"admin API中未找到文生图工作流: flux_text_to_image_workflow")
            
        except Exception as e:
            print(f"❌ 通过admin API加载文生图工作流失败: {e}")
            raise
    
    def _load_image_to_image_workflow_template(self) -> Dict[str, Any]:
        """加载图生图工作流模板"""
        try:
            import requests
            import json
            
            # 通过admin API获取工作流配置
            admin_url = f"{ADMIN_BACKEND_URL}/api/admin/config-sync/workflows"
            response = requests.get(admin_url, timeout=5)
            
            if response.status_code != 200:
                raise Exception(f"admin API调用失败: {response.status_code}")
            
            data = response.json()
            workflows = data.get("workflows", [])
            
            # 查找图生图工作流
            for workflow_data in workflows:
                if workflow_data.get("code") == "flux_image_to_image_workflow":
                    workflow_json = workflow_data.get("workflow_json")
                    if workflow_json:
                        workflow = json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
                        print(f"✅ 通过admin API加载Flux工作流模板: flux_image_to_image_workflow")
                        return workflow
            
            raise ValueError(f"admin API中未找到图生图工作流: flux_image_to_image_workflow")
            
        except Exception as e:
            print(f"❌ 通过admin API加载图生图工作流失败: {e}")
            raise
    
    def _update_final_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any], description: str = "") -> Dict[str, Any]:
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
                seed = random.randint(1, 2**31 - 1)  # 限制在int32范围内
                workflow["31"]["inputs"]["seed"] = seed
                print(f"使用随机种子: {seed}")
        
        # 获取图像尺寸（使用基类方法）
        width, height = self._get_image_dimensions(parameters)
        
        # 更新节点42（FluxKontextImageScale）的尺寸配置
        if "42" in workflow:
            workflow["42"]["inputs"]["width"] = width
            workflow["42"]["inputs"]["height"] = height
            print(f"✅ 更新Flux图像尺寸: {width}x{height}")
        
        # 更新节点188（EmptySD3LatentImage）的尺寸配置（文生图工作流）
        if "188" in workflow:
            workflow["188"]["inputs"]["width"] = width
            workflow["188"]["inputs"]["height"] = height
            print(f"✅ 更新EmptySD3LatentImage尺寸: {width}x{height}")
        
        # 更新节点178（EmptySD3LatentImage）的尺寸配置（图生图工作流）
        if "178" in workflow:
            workflow["178"]["inputs"]["width"] = width
            workflow["178"]["inputs"]["height"] = height
            print(f"✅ 更新图生图EmptySD3LatentImage尺寸: {width}x{height}")
        
        # 安全地打印参数信息
        steps = parameters.get("steps", 20)
        cfg = parameters.get("cfg", 1)
        guidance = parameters.get("guidance", 2.5)
        
        print(f"工作流参数更新完成: 步数={steps}, CFG={cfg}, 引导={guidance}, 尺寸={width}x{height}")
        return workflow
    
    def _process_template_variables(self, workflow: Dict[str, Any], description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """处理模板变量（如{{description}}）"""
        # 遍历工作流节点，处理模板变量
        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue
                
            inputs = node.get("inputs", {})
            
            # 处理文本字段中的模板变量
            for key, value in inputs.items():
                if isinstance(value, str) and "{{description}}" in value:
                    # 替换{{description}}为实际描述
                    inputs[key] = value.replace("{{description}}", description)
                    print(f"✅ 处理模板变量 {node_id}.{key}: {{description}} -> {description[:30]}...")
        
        return workflow
