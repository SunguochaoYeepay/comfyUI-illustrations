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
            workflow_creator = FluxWorkflow(model_config)
        elif model_config.model_type == ModelType.QWEN:
            workflow_creator = QwenWorkflow(model_config)
        elif model_config.model_type == ModelType.WAN:
            workflow_creator = WanWorkflow(model_config)
        else:
            print(f"❌ 不支持的模型类型: {model_config.model_type}")
            workflow_creator = FluxWorkflow(model_config)
        
        # 创建工作流
        return workflow_creator.create_workflow(reference_image_path, description, parameters)
    

