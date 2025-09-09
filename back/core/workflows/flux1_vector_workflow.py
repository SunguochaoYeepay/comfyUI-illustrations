#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flux1矢量工作流实现
支持可选基础模型和多个LoRA
"""

import random
import json
from pathlib import Path
from typing import Any, Dict, List

from .base_workflow import BaseWorkflow


class Flux1VectorWorkflow(BaseWorkflow):
    """Flux1矢量工作流创建器"""
    
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建Flux1矢量工作流
        
        Args:
            reference_image_path: 参考图像路径（字符串或列表）
            description: 图像描述
            parameters: 生成参数，包括：
                - base_model: 基础模型名称
                - loras: LoRA列表，每个包含name, strength_model, strength_clip
                - seed: 随机种子
                - steps: 采样步数
                - width: 图像宽度
                - height: 图像高度
                
        Returns:
            Flux1矢量工作流字典
        """
        print(f"🎨 创建Flux1矢量工作流: {self.model_config.display_name}")
        
        # 根据参考图数量选择工作流模板
        workflow = self._load_workflow_template(reference_image_path)
        
        # 更新参考图像路径
        workflow = self._update_reference_images(workflow, reference_image_path)
        
        # 更新基础模型
        workflow = self._update_base_model(workflow, parameters)
        
        # 更新LoRA配置
        workflow = self._update_lora_config(workflow, parameters)
        
        # 更新提示词
        workflow = self._update_prompt(workflow, description)
        
        # 更新随机种子
        workflow = self._update_seed(workflow, parameters)
        
        # 更新其他参数
        workflow = self._update_parameters(workflow, parameters)
        
        # 更新保存路径
        workflow = self._update_save_path(workflow)
        
        print(f"✅ Flux1矢量工作流创建完成，包含 {len(workflow)} 个节点")
        return workflow
    
    def _update_save_path(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新保存路径"""
        if "9" in workflow:
            workflow["9"]["inputs"]["filename_prefix"] = "yeepay/yeepay"
            print(f"✅ 更新保存路径: yeepay/yeepay")
        
        return workflow
    
    def _load_workflow_template(self, reference_image_path) -> Dict[str, Any]:
        """根据参考图数量选择工作流模板"""
        from config.settings import WORKFLOWS_DIR
        
        if reference_image_path:
            if isinstance(reference_image_path, list):
                if len(reference_image_path) == 1:
                    # 1张参考图 - 风格迁移
                    template_path = WORKFLOWS_DIR / "flux1" / "flux_redux_model_1.json"
                    print(f"📁 加载单图风格迁移工作流: {template_path}")
                elif len(reference_image_path) == 2:
                    # 2张参考图 - 风格融合
                    template_path = WORKFLOWS_DIR / "flux1" / "flux_redux_model_2.json"
                    print(f"📁 加载多图风格融合工作流: {template_path}")
                else:
                    raise ValueError("Flux1 Redux最多支持2张参考图")
            else:
                # 单张参考图 - 风格迁移
                template_path = WORKFLOWS_DIR / "flux1" / "flux_redux_model_1.json"
                print(f"📁 加载单图风格迁移工作流: {template_path}")
        else:
            # 无参考图 - 纯文本生成
            template_path = WORKFLOWS_DIR / "flux1_vector_workflow.json"
            print(f"📁 加载纯文本生成工作流: {template_path}")
        
        if not template_path.exists():
            raise FileNotFoundError(f"工作流模板文件不存在: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        return workflow
    
    def _update_reference_images(self, workflow: Dict[str, Any], reference_image_path) -> Dict[str, Any]:
        """更新参考图像路径"""
        if not reference_image_path:
            return workflow
        
        if isinstance(reference_image_path, list):
            if len(reference_image_path) == 1:
                # 单图风格迁移
                if "40" in workflow:
                    comfyui_path = self._convert_path_for_comfyui(reference_image_path[0])
                    workflow["40"]["inputs"]["image"] = comfyui_path
                    print(f"✅ 更新参考图1: {reference_image_path[0]} -> {comfyui_path}")
            elif len(reference_image_path) == 2:
                # 多图风格融合
                if "40" in workflow:
                    comfyui_path = self._convert_path_for_comfyui(reference_image_path[0])
                    workflow["40"]["inputs"]["image"] = comfyui_path
                    print(f"✅ 更新参考图1: {reference_image_path[0]} -> {comfyui_path}")
                if "47" in workflow:
                    comfyui_path = self._convert_path_for_comfyui(reference_image_path[1])
                    workflow["47"]["inputs"]["image"] = comfyui_path
                    print(f"✅ 更新参考图2: {reference_image_path[1]} -> {comfyui_path}")
        else:
            # 单张参考图
            if "40" in workflow:
                comfyui_path = self._convert_path_for_comfyui(reference_image_path)
                workflow["40"]["inputs"]["image"] = comfyui_path
                print(f"✅ 更新参考图: {reference_image_path} -> {comfyui_path}")
        
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
    
    def _load_base_workflow(self) -> Dict[str, Any]:
        """加载基础工作流模板（已废弃，使用_load_workflow_template）"""
        from config.settings import WORKFLOWS_DIR
        template_path = WORKFLOWS_DIR / "flux1" / "flux1_vector_workflow.json"
        if not template_path.exists():
            raise FileNotFoundError(f"工作流模板文件不存在: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        print(f"📁 加载工作流模板: {template_path}")
        return workflow
    
    def _update_base_model(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新基础模型"""
        base_model = parameters.get("base_model", self.model_config.unet_file)
        
        if "12" in workflow:  # UNETLoader节点
            workflow["12"]["inputs"]["unet_name"] = base_model
            print(f"🔄 更新基础模型: {base_model}")
        
        return workflow
    
    def _update_lora_config(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新LoRA配置"""
        loras = parameters.get("loras", [])
        
        if not loras:
            # 如果没有LoRA，移除LoRA节点，直接连接
            if "31" in workflow and "12" in workflow and "11" in workflow:
                # 更新所有引用节点31的节点，让它们直接连接到基础模型
                # 节点6 (CLIPTextEncode) 的clip连接到节点11
                if "6" in workflow:
                    workflow["6"]["inputs"]["clip"] = ["11", 0]
                
                # 节点13 (KSampler) 的model连接到节点12
                if "13" in workflow:
                    workflow["13"]["inputs"]["model"] = ["12", 0]
                
                # 节点17 (BasicScheduler) 的model连接到节点12
                if "17" in workflow:
                    workflow["17"]["inputs"]["model"] = ["12", 0]
                
                # 节点22 (BasicGuider) 的model连接到节点12
                if "22" in workflow:
                    workflow["22"]["inputs"]["model"] = ["12", 0]
                
                # 移除节点31 (LoRA节点)
                if "31" in workflow:
                    del workflow["31"]
                
                print("🔄 移除LoRA节点，直接使用基础模型")
        else:
            # 更新第一个LoRA
            lora = loras[0]  # 目前只支持一个LoRA
            if "31" in workflow:
                workflow["31"]["inputs"]["lora_name"] = lora.get("name", "F.1-矢量卡通风格LOGO_V1.safetensors")
                workflow["31"]["inputs"]["strength_model"] = lora.get("strength_model", 1.0)
                workflow["31"]["inputs"]["strength_clip"] = lora.get("strength_clip", 1.0)
                print(f"🔄 更新LoRA: {lora.get('name', 'default')}")
        
        return workflow
    
    def _update_prompt(self, workflow: Dict[str, Any], description: str) -> Dict[str, Any]:
        """更新提示词"""
        print(f"🔍 查找CLIPTextEncode节点...")
        
        # 查找所有CLIPTextEncode节点
        clip_nodes = []
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "CLIPTextEncode":
                clip_nodes.append(node_id)
                print(f"📝 找到CLIPTextEncode节点: {node_id}")
        
        if clip_nodes:
            # 更新第一个找到的CLIPTextEncode节点
            node_id = clip_nodes[0]
            old_text = workflow[node_id]["inputs"].get("text", "")
            workflow[node_id]["inputs"]["text"] = description
            print(f"🔄 更新节点 {node_id} 提示词:")
            print(f"   原文: {old_text}")
            print(f"   新文: {description}")
        else:
            print("⚠️ 未找到CLIPTextEncode节点")
        
        return workflow
    
    def _update_seed(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新随机种子"""
        seed = parameters.get("seed")
        if seed is None:
            seed = random.randint(1, 2**32 - 1)
        
        if "25" in workflow:  # RandomNoise节点
            workflow["25"]["inputs"]["noise_seed"] = seed
            print(f"🎲 更新随机种子: {seed}")
        
        return workflow
    
    def _update_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新其他参数"""
        # 更新图像尺寸
        width = parameters.get("width", 512)
        height = parameters.get("height", 512)
        
        # 处理不同的Latent节点
        if "5" in workflow:  # EmptyLatentImage节点 (原始工作流)
            workflow["5"]["inputs"]["width"] = width
            workflow["5"]["inputs"]["height"] = height
            print(f"🔄 更新图像尺寸: {width}x{height}")
        elif "27" in workflow:  # EmptySD3LatentImage节点 (Redux工作流)
            workflow["27"]["inputs"]["width"] = width
            workflow["27"]["inputs"]["height"] = height
            print(f"🔄 更新图像尺寸: {width}x{height}")
        
        # 更新采样步数
        steps = parameters.get("steps", 20)
        
        if "17" in workflow:  # BasicScheduler节点
            workflow["17"]["inputs"]["steps"] = steps
            print(f"🔄 更新采样步数: {steps}")
        
        return workflow
