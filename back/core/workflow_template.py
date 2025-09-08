#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模板管理器
负责创建和自定义多种模型的工作流
"""

import json
from pathlib import Path
from typing import Any, Dict

from core.model_manager import get_model_config, ModelType
from core.workflows import FluxWorkflow, QwenWorkflow
from core.workflows import WanWorkflow


class WorkflowTemplate:
    """工作流模板管理器，负责创建和自定义多种模型的工作流"""
    
    def __init__(self, template_path: str = None):
        """初始化工作流模板
        
        Args:
            template_path: 模板文件路径（可选，保留兼容性）
        """
        self.template_path = template_path
        self.template = self._load_template() if template_path else {}
    
    def _load_template(self) -> Dict[str, Any]:
        """加载工作流模板文件"""
        try:
            if self.template_path:
                template_file = Path(self.template_path)
                if template_file.exists():
                    with open(template_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    print(f"⚠️ 模板文件不存在: {self.template_path}")
            return {}
        except Exception as e:
            print(f"❌ 加载模板文件失败: {e}")
            return {}
    
    def customize_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any], model_name: str = "flux1-dev"):
        """自定义工作流参数 - 支持多种模型
        
        Args:
            reference_image_path: 参考图像路径
            description: 图像描述
            parameters: 生成参数
            model_name: 模型名称（默认flux1-dev）
        """
        # 获取模型配置
        model_config = get_model_config(model_name)
        if not model_config or not model_config.available:
            print(f"⚠️ 模型 {model_name} 不可用，使用默认Flux模型")
            model_config = get_model_config("flux1-dev")
        
        print(f"🎯 使用模型: {model_config.display_name}")
        
        # 根据模型类型选择对应的工作流创建器
        if model_config.model_type == ModelType.FLUX:
            # 根据模型名称选择不同的工作流
            if model_config.name == "flux1-standard":
                from core.workflows import Flux1Workflow
                workflow_creator = Flux1Workflow(model_config)
            else:
                workflow_creator = FluxWorkflow(model_config)
        elif model_config.model_type == ModelType.QWEN:
            # 根据图片数量选择不同的Qwen工作流
            # 检查是否是多图融合模式
            reference_image_paths = parameters.get("reference_image_paths", [])
            if len(reference_image_paths) >= 2:
                from core.workflows import QwenFusionWorkflow
                workflow_creator = QwenFusionWorkflow(model_config)
            else:
                workflow_creator = QwenWorkflow(model_config)
        elif model_config.model_type == ModelType.WAN:
            workflow_creator = WanWorkflow(model_config)
        elif model_config.model_type == ModelType.FLUX1:  # 新增
            from core.workflows import Flux1VectorWorkflow
            workflow_creator = Flux1VectorWorkflow(model_config)
        else:
            raise ValueError(f"不支持的模型类型: {model_config.model_type}")
        
        # 创建工作流
        # 检查是否是多图融合模式
        reference_image_paths = parameters.get("reference_image_paths", [])
        if model_config.model_type == ModelType.QWEN and len(reference_image_paths) >= 2:
            # 多图融合工作流需要特殊处理
            return self.customize_fusion_workflow(reference_image_path, description, parameters, model_name)
        else:
            return workflow_creator.create_workflow(reference_image_path, description, parameters)
    
    def customize_fusion_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any], model_name: str = "qwen-fusion"):
        """自定义多图融合工作流参数
        
        Args:
            reference_image_path: 第一张参考图像路径（用于获取图像路径列表）
            description: 图像描述
            parameters: 生成参数
            model_name: 模型名称
        """
        # 获取模型配置
        model_config = get_model_config(model_name)
        if not model_config or not model_config.available:
            print(f"⚠️ 模型 {model_name} 不可用，使用默认Qwen模型")
            model_config = get_model_config("qwen-image")
        
        print(f"🎯 使用多图融合模型: {model_config.display_name}")
        
        # 从参数中获取图像路径列表
        image_paths = parameters.get("reference_image_paths", [])
        if not image_paths:
            # 如果没有提供路径列表，尝试从reference_image_path获取
            if reference_image_path:
                image_paths = [reference_image_path]
            else:
                raise ValueError("多图融合需要提供图像路径列表")
        
        # 创建Qwen融合工作流
        from core.workflows import QwenFusionWorkflow
        workflow_creator = QwenFusionWorkflow(model_config)
        
        # 将图像路径列表添加到参数中
        parameters["reference_image_paths"] = image_paths
        
        # 创建工作流（调用标准的create_workflow方法）
        return workflow_creator.create_workflow(reference_image_path, description, parameters)
    

