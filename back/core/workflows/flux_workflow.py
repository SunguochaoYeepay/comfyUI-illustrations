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
        
        # 获取图像尺寸
        width, height = self._get_image_dimensions(parameters)
        
        # 处理参考图像
        processed_image_path = self._process_reference_image(reference_image_path, width, height)
        
        # 加载fluxcontext工作流模板
        workflow = self._load_flux_kontext_workflow_template()
        
        # 如果有参考图像，添加参考图像节点
        if processed_image_path:
            print("🖼️ 检测到参考图像，添加参考图像处理节点")
            workflow = self._add_reference_image_nodes(workflow, processed_image_path, width, height)
        
        # 处理LoRA配置
        loras = validated_params.get("loras", [])
        workflow = self._configure_lora_stack(workflow, loras)
        
        # 处理模板变量替换
        workflow = self._process_template_variables(workflow, description, validated_params, width, height)
        
        # 配置保存图像节点
        workflow = self._configure_save_image_node(workflow, validated_params)
        
        print(f"✅ Flux工作流创建完成，包含 {len(workflow)} 个节点")
        return workflow
    
    def _configure_save_image_node(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """配置保存图像节点"""
        # 使用固定的保存路径，与其他工作流保持一致
        filename_prefix = "yeepay/yeepay"
        
        # 更新SaveImage节点（节点9）
        if "9" in workflow:
            workflow["9"]["inputs"]["filename_prefix"] = filename_prefix
            print(f"✅ 配置保存图像文件名前缀: {filename_prefix}")
        
        return workflow
    
    def _add_reference_image_nodes(self, workflow: Dict[str, Any], image_path: str, width: int, height: int) -> Dict[str, Any]:
        """为fluxcontext工作流添加参考图像节点"""
        print("📸 为fluxcontext工作流添加参考图支持")
        
        # 转换图像路径为ComfyUI格式
        comfyui_path = self._convert_path_for_comfyui(image_path)
        
        # 添加LoadImage节点
        workflow["142"] = {
            "inputs": {
                "image": comfyui_path,
                "upload": "image"
            },
            "class_type": "LoadImage",
            "_meta": {"title": "加载参考图像"}
        }
        
        # 添加FluxKontextImageScale节点
        workflow["143"] = {
            "inputs": {
                "image": ["142", 0],
                "width": width,
                "height": height,
                "crop": "disabled"
            },
            "class_type": "FluxKontextImageScale",
            "_meta": {"title": "FluxKontextImageScale"}
        }
        
        # 添加VAEEncode节点
        workflow["144"] = {
            "inputs": {
                "pixels": ["143", 0],
                "vae": ["64", 0]
            },
            "class_type": "VAEEncode",
            "_meta": {"title": "VAE编码"}
        }
        
        # 更新SamplerCustomAdvanced的latent_image输入
        if "13" in workflow:
            workflow["13"]["inputs"]["latent_image"] = ["144", 0]
            print("✅ 更新SamplerCustomAdvanced的latent_image输入为VAEEncode输出")
        
        print(f"✅ 参考图节点添加完成: LoadImage -> FluxKontextImageScale -> VAEEncode")
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
    
    def _load_flux_kontext_workflow_template(self) -> Dict[str, Any]:
        """通过admin API加载flux工作流模板"""
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
            
            # 查找flux工作流
            for workflow_data in workflows:
                if workflow_data.get("code") == "flux_text_to_image_workflow":
                    workflow_json = workflow_data.get("workflow_json")
                    if workflow_json:
                        workflow = json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
                        print(f"✅ 通过admin API加载Flux工作流模板: flux_text_to_image_workflow")
                        return workflow
            
            raise ValueError(f"admin API中未找到Flux工作流: flux_text_to_image_workflow")
            
        except Exception as e:
            print(f"❌ 通过admin API加载Flux工作流失败: {e}")
            raise
    
    
    def _configure_lora_stack(self, workflow: Dict[str, Any], loras: list) -> Dict[str, Any]:
        """配置LoRA堆栈"""
        processed_loras = self._process_loras(loras)
        
        # 初始化LoRA配置
        lora_config = {
            "lora_01": "None",
            "strength_01": 1.0,
            "lora_02": "None", 
            "strength_02": 1.0,
            "lora_03": "None",
            "strength_03": 1.0,
            "lora_04": "None",
            "strength_04": 1.0
        }
        
        # 配置LoRA
        for i, lora in enumerate(processed_loras[:4]):  # 最多4个LoRA
            lora_key = f"lora_{i+1:02d}"
            strength_key = f"strength_{i+1:02d}"
            
            lora_config[lora_key] = lora["name"]
            lora_config[strength_key] = lora["strength_model"]
            
            print(f"🎨 配置LoRA {i+1}: {lora['name']} (强度: {lora['strength_model']})")
        
        # 更新工作流中的LoRA堆栈节点
        if "74" in workflow:
            workflow["74"]["inputs"].update(lora_config)
            print(f"✅ LoRA堆栈配置完成")
        
        return workflow
    
    def _process_template_variables(self, workflow: Dict[str, Any], description: str, parameters: Dict[str, Any], width: int, height: int) -> Dict[str, Any]:
        """处理模板变量替换"""
        # 获取种子
        seed = parameters.get("seed", random.randint(1, 2**31 - 1))
        
        # 遍历工作流节点，处理模板变量
        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue
                
            inputs = node.get("inputs", {})
            
            # 处理文本字段中的模板变量
            for key, value in inputs.items():
                if isinstance(value, str):
                    # 替换描述
                    if "{{description}}" in value:
                        inputs[key] = value.replace("{{description}}", description)
                        print(f"✅ 替换描述: {node_id}.{key}")
                    
                    # 替换种子
                    if "{{seed}}" in value:
                        inputs[key] = value.replace("{{seed}}", str(seed))
                        print(f"✅ 替换种子: {node_id}.{key} = {seed}")
                    
                    # 替换尺寸
                    if "{{width}}" in value:
                        inputs[key] = value.replace("{{width}}", str(width))
                        print(f"✅ 替换宽度: {node_id}.{key} = {width}")
                    
                    if "{{height}}" in value:
                        inputs[key] = value.replace("{{height}}", str(height))
                        print(f"✅ 替换高度: {node_id}.{key} = {height}")
                    
                    # 替换LoRA配置
                    for i in range(1, 5):
                        lora_key = f"{{lora_{i:02d}}}"
                        strength_key = f"{{strength_{i:02d}}}"
                        
                        if lora_key in value:
                            inputs[key] = value.replace(lora_key, "None")
                        if strength_key in value:
                            inputs[key] = value.replace(strength_key, "1.0")
        
        return workflow
    
