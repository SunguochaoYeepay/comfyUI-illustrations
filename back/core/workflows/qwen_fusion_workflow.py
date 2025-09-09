#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen多图融合工作流实现
专门处理Qwen模型的多图融合功能
"""

import json
import os
from pathlib import Path
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
            image_paths: 图像路径列表（3张图像）
            description: 融合描述
            parameters: 生成参数
            
        Returns:
            Qwen多图融合工作流字典
        """
        print(f"🎨 创建Qwen多图融合工作流: {self.model_config.display_name}")
        
        # 验证图像数量
        if len(image_paths) < 2:
            raise ValueError("多图融合至少需要2张图像")
        if len(image_paths) > 3:
            raise ValueError("多图融合最多支持3张图像")
        
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 加载工作流模板（根据图片数量选择）
        workflow = self._load_fusion_template(len(image_paths))
        
        # 更新模型配置（多图融合使用编辑版本）
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
    
    def _load_fusion_template(self, image_count: int) -> Dict[str, Any]:
        """根据图片数量加载对应的工作流模板"""
        # 根据图片数量选择对应的工作流模板
        if image_count == 2:
            template_name = "2image_fusion.json"
        elif image_count == 3:
            template_name = "3image_fusion.json"
        else:
            raise ValueError(f"不支持 {image_count} 张图片的融合，目前只支持2-3张图片")
        
        # 使用配置文件中的工作流目录
        from config.settings import WORKFLOWS_DIR
        workflow_path = WORKFLOWS_DIR / "qwen" / "fusion" / template_name
        print(f"🔍 加载工作流模板: {workflow_path}")
        
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        print(f"✅ 加载Qwen多图融合工作流模板: {template_name} (支持{image_count}张图片)")
        return workflow
    
    
    def _add_multi_image_nodes(self, workflow: Dict[str, Any], image_paths: List[str]) -> Dict[str, Any]:
        """更新多图输入节点的图像路径
        
        Args:
            workflow: 工作流字典
            image_paths: 图像路径列表
            
        Returns:
            更新后的工作流字典
        """
        print(f"📸 为Qwen多图融合工作流更新 {len(image_paths)} 张图像路径")
        
        # 动态查找LoadImage节点
        load_image_nodes = []
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "LoadImage":
                load_image_nodes.append(node_id)
        
        # 按节点ID排序，确保顺序一致
        load_image_nodes.sort()
        
        print(f"🔍 找到 {len(load_image_nodes)} 个LoadImage节点: {load_image_nodes}")
        
        if len(load_image_nodes) < len(image_paths):
            raise ValueError(f"工作流中只有 {len(load_image_nodes)} 个LoadImage节点，但需要 {len(image_paths)} 个")
        
        # 更新每个LoadImage节点的图像路径
        for i, image_path in enumerate(image_paths):
            node_id = load_image_nodes[i]
            # 转换Windows路径为ComfyUI兼容的路径格式
            comfyui_path = self._convert_path_for_comfyui(image_path)
            
            if node_id in workflow:
                workflow[node_id]["inputs"]["image"] = comfyui_path
                print(f"✅ 更新LoadImage节点 {node_id}: {os.path.basename(image_path)} -> {comfyui_path}")
            else:
                print(f"⚠️ 节点 {node_id} 不存在于工作流中")
        
        print(f"✅ Qwen多图融合节点配置完成，处理 {len(image_paths)} 张图像")
        return workflow
    
    def _update_model_config(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新模型配置（多图融合使用编辑版本）"""
        if "167" in workflow:
            # 多图融合使用编辑版本
            workflow["167"]["inputs"]["unet_name"] = "qwen_image_edit_fp8_e4m3fn.safetensors"
            print(f"✅ 更新UNETLoader: qwen_image_edit_fp8_e4m3fn.safetensors")
        
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
            print(f"✅ 更新KSampler参数: 步数={parameters.get('steps', 20)}, 种子={workflow['158']['inputs']['seed']}, CFG={parameters.get('cfg', 2.5)}")
        
        # 动态更新图像尺寸配置
        workflow = self._update_image_dimensions(workflow)
        
        return workflow
    
    def _update_image_dimensions(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """动态更新图像尺寸配置"""
        # 更新节点164（LatentUpscale）的尺寸配置
        if "164" in workflow:
            workflow["164"]["inputs"]["width"] = 1024
            workflow["164"]["inputs"]["height"] = 768
            print(f"✅ 动态更新多图融合图像尺寸: 1024x768")
        
        return workflow
    
    def _update_save_path(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新保存路径"""
        if "166" in workflow:
            workflow["166"]["inputs"]["filename_prefix"] = "yeepay/yeepay"
            print(f"✅ 更新保存路径: yeepay/yeepay")
        
        return workflow
    
    def _update_lora_config(self, workflow: Dict[str, Any], loras: list) -> Dict[str, Any]:
        """更新LoRA配置"""
        if "170" not in workflow:
            print("ℹ️ 多图融合工作流未找到LoRA节点，使用默认设置")
            return workflow
        
        processed_loras = self._process_loras(loras)
        
        if not processed_loras:
            print("ℹ️ 未检测到LoRA配置，使用默认设置")
            return workflow
        
        print(f"🎨 检测到 {len(processed_loras)} 个LoRA配置")
        
        # 保留默认的8步生图LoRA，前端LoRA从lora_02开始
        # lora_01 保持默认的 Qwen-Image-Lightning-8steps-V1.0.safetensors
        workflow["170"]["inputs"]["lora_02"] = "None"
        workflow["170"]["inputs"]["strength_02"] = 1
        workflow["170"]["inputs"]["lora_03"] = "None"
        workflow["170"]["inputs"]["strength_03"] = 1
        workflow["170"]["inputs"]["lora_04"] = "None"
        workflow["170"]["inputs"]["strength_04"] = 1
        
        # 设置前端选择的LoRA（从lora_02开始）
        for i, lora in enumerate(processed_loras):
            if i >= 3:  # 限制最多3个额外LoRA（lora_02, lora_03, lora_04）
                break
                
            lora_key = f"lora_{i+2:02d}"  # 从lora_02开始
            strength_key = f"strength_{i+2:02d}"
            
            workflow["170"]["inputs"][lora_key] = lora["name"]
            workflow["170"]["inputs"][strength_key] = lora["strength_model"]
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
