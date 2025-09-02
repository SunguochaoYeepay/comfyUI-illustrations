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
            reference_image_path: 参考图像路径（此工作流不需要）
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
        
        # 加载基础工作流模板
        workflow = self._load_base_workflow()
        
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
        
        print(f"✅ Flux1矢量工作流创建完成，包含 {len(workflow)} 个节点")
        return workflow
    
    def _load_base_workflow(self) -> Dict[str, Any]:
        """加载基础工作流模板"""
        template_path = Path("workflows/flux1_vector_workflow.json")
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
                # 将节点13的model和clip直接连接到节点12和11
                if "13" in workflow:
                    workflow["13"]["inputs"]["model"] = ["12", 0]
                    workflow["13"]["inputs"]["clip"] = ["11", 0]
                
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
        if "6" in workflow:  # CLIPTextEncode节点
            workflow["6"]["inputs"]["text"] = description
            print(f"🔄 更新提示词: {description[:50]}...")
        
        return workflow
    
    def _update_seed(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新随机种子"""
        seed = parameters.get("seed", random.randint(1, 2**32 - 1))
        
        if "25" in workflow:  # RandomNoise节点
            workflow["25"]["inputs"]["noise_seed"] = seed
            print(f"🎲 更新随机种子: {seed}")
        
        return workflow
    
    def _update_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新其他参数"""
        # 更新图像尺寸
        width = parameters.get("width", 512)
        height = parameters.get("height", 512)
        
        if "5" in workflow:  # EmptyLatentImage节点
            workflow["5"]["inputs"]["width"] = width
            workflow["5"]["inputs"]["height"] = height
            print(f"🔄 更新图像尺寸: {width}x{height}")
        
        # 更新采样步数
        steps = parameters.get("steps", 20)
        
        if "17" in workflow:  # BasicScheduler节点
            workflow["17"]["inputs"]["steps"] = steps
            print(f"🔄 更新采样步数: {steps}")
        
        return workflow
