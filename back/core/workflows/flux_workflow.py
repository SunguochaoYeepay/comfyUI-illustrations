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
            reference_image_path: 参考图像路径（可能是字符串或列表的字符串表示）
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
        
        # 处理参考图像路径（兼容单图和多图情况）
        processed_image_path = self._get_processed_image_path(reference_image_path, parameters, width, height)
        
        # 根据是否有参考图像选择不同的工作流模板
        if processed_image_path:
            print("🖼️ 检测到参考图像，使用图生图模式")
            workflow = self._load_flux_kontext_workflow_template("flux_image_to_image_workflow")
        else:
            print("📝 无参考图像，使用文生图模式")
            workflow = self._load_flux_kontext_workflow_template("flux_text_to_image_workflow")
        
        # 处理LoRA配置
        loras = validated_params.get("loras", [])
        workflow = self._configure_lora_stack(workflow, loras)
        
        # 处理模板变量替换
        workflow = self._process_template_variables(workflow, description, validated_params, width, height, processed_image_path)
        
        # 配置保存图像节点
        workflow = self._configure_save_image_node(workflow, validated_params)
        
        print(f"✅ Flux工作流创建完成，包含 {len(workflow)} 个节点")
        return workflow
    
    def _get_processed_image_path(self, reference_image_path: str, parameters: Dict[str, Any], width: int, height: int):
        """获取处理后的图像路径，兼容单图和多图情况
        
        Args:
            reference_image_path: 参考图像路径（可能是字符串或列表的字符串表示）
            parameters: 生成参数
            width: 目标宽度
            height: 目标高度
            
        Returns:
            处理后的图像路径（单图）或None
        """
        # 首先尝试从parameters中获取多图路径
        reference_image_paths = parameters.get("reference_image_paths", [])
        
        if reference_image_paths:
            # 多图情况：取第一张图
            if isinstance(reference_image_paths, list) and len(reference_image_paths) > 0:
                first_image_path = reference_image_paths[0]
                print(f"🖼️ 多图模式：使用第一张图 {first_image_path}")
                return self._process_reference_image(first_image_path, width, height)
        
        # 处理reference_image_path可能是列表字符串的情况
        if reference_image_path and reference_image_path.startswith('[') and reference_image_path.endswith(']'):
            try:
                import json
                image_paths = json.loads(reference_image_path)
                if isinstance(image_paths, list) and len(image_paths) > 0:
                    first_image_path = image_paths[0]
                    print(f"🖼️ 解析列表字符串：使用第一张图 {first_image_path}")
                    return self._process_reference_image(first_image_path, width, height)
            except (json.JSONDecodeError, IndexError):
                print(f"⚠️ 无法解析图像路径列表: {reference_image_path}")
        
        # 单图情况：直接处理
        if reference_image_path and reference_image_path.strip():
            return self._process_reference_image(reference_image_path, width, height)
        
        return None
    
    def _configure_save_image_node(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """配置保存图像节点"""
        # 使用固定的保存路径，与其他工作流保持一致
        filename_prefix = "yeepay/yeepay"
        
        # 更新SaveImage节点（节点9）
        if "9" in workflow:
            workflow["9"]["inputs"]["filename_prefix"] = filename_prefix
            print(f"✅ 配置保存图像文件名前缀: {filename_prefix}")
        
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
    
    def _load_flux_kontext_workflow_template(self, workflow_type: str = "flux_text_to_image_workflow") -> Dict[str, Any]:
        """通过admin API加载flux工作流模板
        
        Args:
            workflow_type: 工作流类型，可选值：
                - "flux_text_to_image_workflow": 文生图工作流
                - "flux_image_to_image_workflow": 图生图工作流
        """
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
            
            # 查找指定类型的flux工作流
            for workflow_data in workflows:
                if workflow_data.get("code") == workflow_type:
                    workflow_json = workflow_data.get("workflow_json")
                    if workflow_json:
                        workflow = json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
                        print(f"✅ 通过admin API加载Flux工作流模板: {workflow_type}")
                        return workflow
            
            raise ValueError(f"admin API中未找到Flux工作流: {workflow_type}")
            
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
    
    def _process_template_variables(self, workflow: Dict[str, Any], description: str, parameters: Dict[str, Any], width: int, height: int, processed_image_path: str = None) -> Dict[str, Any]:
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
                    
                    # 替换参考图像路径
                    if "{{reference_image}}" in value and processed_image_path:
                        # 处理processed_image_path可能是列表的情况
                        if isinstance(processed_image_path, list):
                            # 如果是列表，取第一个元素
                            image_path = processed_image_path[0]
                        else:
                            image_path = processed_image_path
                        
                        # 获取文件名（不包含路径）
                        filename = image_path.split('/')[-1] if '/' in image_path else image_path.split('\\')[-1]
                        # 移除 [output] 后缀
                        if filename.endswith(' [output]'):
                            filename = filename[:-9]  # 移除 " [output]"
                        inputs[key] = value.replace("{{reference_image}}", filename)
                        print(f"✅ 替换参考图像: {node_id}.{key} = {filename}")
                    
                    # 处理LoadImage节点的硬编码图像路径
                    if processed_image_path and node.get("class_type") == "LoadImage" and key == "image":
                        # 处理processed_image_path可能是列表的情况
                        if isinstance(processed_image_path, list):
                            # 如果是列表，取第一个元素
                            image_path = processed_image_path[0]
                        else:
                            image_path = processed_image_path
                        
                        # 获取文件名（不包含路径）
                        filename = image_path.split('/')[-1] if '/' in image_path else image_path.split('\\')[-1]
                        # 移除 [output] 后缀
                        if filename.endswith(' [output]'):
                            filename = filename[:-9]  # 移除 " [output]"
                        inputs[key] = filename
                        print(f"✅ 更新LoadImage节点图像路径: {node_id}.{key} = {filename}")
                    
                    # 替换LoRA配置
                    for i in range(1, 5):
                        lora_key = f"{{lora_{i:02d}}}"
                        strength_key = f"{{strength_{i:02d}}}"
                        
                        if lora_key in value:
                            inputs[key] = value.replace(lora_key, "None")
                        if strength_key in value:
                            inputs[key] = value.replace(strength_key, "1.0")
        
        return workflow
    
