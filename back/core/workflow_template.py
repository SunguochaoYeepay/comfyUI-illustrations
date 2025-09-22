#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模板管理器
负责创建和自定义多种模型的工作流
集成配置客户端，支持动态工作流选择
"""

import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.model_manager import get_model_config, ModelType
from core.workflows import FluxWorkflow, QwenWorkflow
from core.workflows import WanWorkflow
from core.workflows.seedream4_workflow import Seedream4Workflow
from core.workflows.joycaption_workflow import JoyCaptionWorkflow


class WorkflowTemplate:
    """工作流模板管理器，负责创建和自定义多种模型的工作流"""
    
    def __init__(self, template_path: str = None):
        """初始化工作流模板
        
        Args:
            template_path: 模板文件路径（可选，保留兼容性）
        """
        self.template_path = template_path
        self.template = self._load_template() if template_path else {}
        self._config_client = None
    
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
    
    async def customize_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any], model_name: str):
        """自定义工作流参数 - 支持多种模型
        
        Args:
            reference_image_path: 参考图像路径
            description: 图像描述
            parameters: 生成参数
            model_name: 模型名称（必填）
        """
        # 获取模型配置 - 使用配置客户端
        model_config = await self._get_model_config_from_client(model_name)
        if not model_config:
            raise ValueError(f"模型 {model_name} 不可用或未配置")
        
        print(f"🎯 使用模型: {model_config.get('display_name', model_name)}")
        
        # 根据模型类型选择对应的工作流创建器
        model_type = model_config.get("model_type", "unknown")
        if model_type == "flux":
            # 根据模型名称选择不同的工作流
            model_config_obj = self._convert_dict_to_model_config(model_config)
            # flux1-standard模型已移除，直接使用Flux工作流
            workflow_creator = FluxWorkflow(model_config_obj)
        elif model_type == "qwen":
            # 根据图片数量选择不同的Qwen工作流
            # 检查是否是多图融合模式
            reference_image_paths = parameters.get("reference_image_paths", [])
            model_config_obj = self._convert_dict_to_model_config(model_config)
            if len(reference_image_paths) >= 2:
                from core.workflows import QwenFusionWorkflow
                workflow_creator = QwenFusionWorkflow(model_config_obj)
            else:
                workflow_creator = QwenWorkflow(model_config_obj)
        elif model_type == "wan":
            model_config_obj = self._convert_dict_to_model_config(model_config)
            workflow_creator = WanWorkflow(model_config_obj)
        # flux1模型已移除，只保留FLUX.1 Kontext
        elif model_type == "gemini":
            from core.workflows import GeminiWorkflow
            model_config_obj = self._convert_dict_to_model_config(model_config)
            workflow_creator = GeminiWorkflow(model_config_obj)
        elif model_type == "seedream4":
            model_config_obj = self._convert_dict_to_model_config(model_config)
            workflow_creator = Seedream4Workflow(model_config_obj)
        elif model_type == "joycaption":
            model_config_obj = self._convert_dict_to_model_config(model_config)
            workflow_creator = JoyCaptionWorkflow(model_config_obj)
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        # 创建工作流
        # 检查是否是多图融合模式
        reference_image_paths = parameters.get("reference_image_paths", [])
        if model_type == ModelType.QWEN and len(reference_image_paths) >= 2:
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
    
    def _get_config_client(self):
        """获取配置客户端"""
        # 每次都重新获取配置客户端，确保使用最新的配置
        try:
            from core.config_client import get_config_client
            self._config_client = get_config_client()
            return self._config_client
        except ImportError:
            # 如果配置客户端不可用，返回None
            return None
    
    async def _get_model_config_from_client(self, model_name: str) -> Optional[Dict[str, Any]]:
        """从配置客户端获取模型配置"""
        try:
            config_client = self._get_config_client()
            if config_client:
                models_config = await config_client.get_models_config()
                models = models_config.get("models", [])
                for model in models:
                    # 优先使用code字段匹配，如果没有则使用name字段
                    model_code = model.get("code")
                    model_name_field = model.get("name")
                    if model_code == model_name or model_name_field == model_name:
                        return model
            return None
        except Exception as e:
            print(f"⚠️ 从配置客户端获取模型配置失败: {e}")
            return None
    
    def _convert_dict_to_model_config(self, model_dict: Dict[str, Any]):
        """将字典转换为ModelConfig对象 - 移除template_path依赖"""
        from core.model_manager import ModelConfig, ModelType
        
        # 模型类型映射
        type_mapping = {
            "qwen": ModelType.QWEN,
            "flux": ModelType.FLUX,
            "wan": ModelType.WAN,
            "gemini": ModelType.GEMINI,
            "joycaption": ModelType.JOYCAPTION
        }
        
        model_type = type_mapping.get(model_dict.get("model_type", "unknown"), ModelType.FLUX)
        model_name = model_dict.get("name", "unknown")
        
        return ModelConfig(
            model_type=model_type,
            name=model_name,
            display_name=model_dict.get("display_name", "Unknown Model"),
            unet_file=self._extract_filename(model_dict.get("unet_file", "")),
            clip_file=self._extract_filename(model_dict.get("clip_file", "")),
            vae_file=self._extract_filename(model_dict.get("vae_file", "")),
            template_path="",  # 不再使用模板路径，完全数据库化
            description=model_dict.get("description", "")
        )
    
    def _extract_filename(self, file_path: str) -> str:
        """从完整路径中提取文件名"""
        if not file_path:
            return ""
        
        # 处理Windows和Unix路径分隔符
        import os
        return os.path.basename(file_path)
    
    async def get_workflow_by_model(self, model_name: str, workflow_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """根据模型获取工作流配置"""
        try:
            config_client = self._get_config_client()
            if config_client:
                config = await config_client.get_workflows_config()
                workflows = config.get("workflows", [])
                print(f"🔍 查找模型 {model_name} 的工作流，可用工作流数量: {len(workflows)}")
                
                # 查找匹配的工作流
                for workflow in workflows:
                    print(f"🔍 检查工作流: {workflow.get('name')}, base_model_type: {workflow.get('base_model_type')}, available: {workflow.get('available')}")
                    # 优先使用code字段匹配，如果没有则使用name字段
                    workflow_code = workflow.get("code") or workflow.get("name")
                    if (workflow.get("base_model_type") == model_name and 
                        workflow.get("available", True)):
                        print(f"✅ 找到匹配的工作流: {workflow.get('name')} (code: {workflow_code})")
                        if workflow_type is None or workflow.get("workflow_type") == workflow_type:
                            return workflow
                
                # 如果没有找到，返回第一个可用的工作流
                for workflow in workflows:
                    if workflow.get("available", True):
                        return workflow
            else:
                # 配置客户端不可用，使用本地配置
                return self._get_local_workflow_by_model(model_name, workflow_type)
        except Exception as e:
            print(f"从配置获取工作流失败: {e}")
            # 降级到本地配置
            return self._get_local_workflow_by_model(model_name, workflow_type)
    
    def _get_local_workflow_by_model(self, model_name: str, workflow_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """从本地配置获取工作流（降级方法）- 不再使用template_path"""
        # 获取模型配置
        model_config = get_model_config(model_name)
        if not model_config:
            return None
        
        # 根据模型类型返回默认工作流配置
        workflow_config = {
            "id": 1,
            "name": f"{model_name}_workflow",
            "display_name": f"{model_config.display_name}工作流",
            "base_model_type": model_name,
            "workflow_type": workflow_type or "image_generation",
            "workflow_json": {},  # 空的工作流JSON，需要从其他地方获取
            "available": True,
            "description": f"{model_config.display_name}的默认工作流"
        }
        
        return workflow_config
    
    async def apply_workflow_config(self, workflow_config: Dict[str, Any], parameters: Dict[str, Any], model_name: str = None) -> Dict[str, Any]:
        """应用工作流配置 - 完全数据库化，不再依赖文件系统"""
        try:
            # 直接从工作流配置中获取工作流JSON
            workflow_template = workflow_config.get("workflow_json")
            
            if not workflow_template:
                raise ValueError("工作流配置中缺少工作流JSON数据")
            
            # 应用参数配置
            customized_workflow = self._apply_parameters_to_workflow(workflow_template, parameters)
            
            return customized_workflow
        except Exception as e:
            print(f"应用工作流配置失败: {e}")
            raise
    
    def _apply_parameters_to_workflow(self, workflow_template: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """将参数应用到工作流模板"""
        try:
            workflow = workflow_template.copy()
            
            # 获取参数
            description = parameters.get("description", "")
            size = parameters.get("size", "1024x1024")
            steps = parameters.get("steps", 20)
            seed = parameters.get("seed")
            model_name = parameters.get("model", "")
            
            # 解析尺寸
            if "x" in size:
                width, height = map(int, size.split("x"))
            else:
                width = height = int(size)
            
            print(f"🔧 应用参数到工作流: 描述={description[:50]}..., 尺寸={width}x{height}, 步数={steps}, 种子={seed}")
            
            # 先显示所有节点类型
            print(f"🔍 工作流节点类型:")
            for node_id, node in workflow.items():
                if isinstance(node, dict):
                    class_type = node.get("class_type", "unknown")
                    print(f"  节点 {node_id}: {class_type}")
            
            # 遍历工作流节点，应用参数
            for node_id, node in workflow.items():
                if not isinstance(node, dict):
                    continue
                    
                class_type = node.get("class_type", "")
                inputs = node.get("inputs", {})
                
                # 更新文本节点 - 支持更多节点类型
                if class_type in ["CLIPTextEncode", "CLIPTextEncodeAdvanced"]:
                    if "text" in inputs:
                        old_text = inputs["text"]
                        inputs["text"] = description
                        print(f"✅ 更新文本节点 {node_id}: '{old_text[:30]}...' -> '{description[:30]}...'")
                    else:
                        print(f"⚠️ 文本节点 {node_id} 没有text字段")
                elif "text" in inputs:
                    # 检查其他可能包含文本的节点
                    old_text = inputs["text"]
                    inputs["text"] = description
                    print(f"✅ 更新其他文本节点 {node_id} ({class_type}): '{old_text[:30]}...' -> '{description[:30]}...'")
                
                # 更新采样器节点 - 支持更多节点类型
                elif class_type in ["KSampler", "KSamplerAdvanced", "SamplerCustom", "ModelSamplingAuraFlow"]:
                    if "steps" in inputs:
                        inputs["steps"] = steps
                    if "seed" in inputs and seed is not None:
                        inputs["seed"] = seed
                    print(f"✅ 更新采样器节点 {node_id}: 步数={steps}, 种子={seed}")
                
                # 更新尺寸节点
                elif class_type in ["EmptyLatentImage", "LatentUpscale", "LatentFromBatch"]:
                    if "width" in inputs:
                        inputs["width"] = width
                    if "height" in inputs:
                        inputs["height"] = height
                    print(f"✅ 更新尺寸节点 {node_id}: {width}x{height}")
                
                # 更新模型加载器节点
                elif class_type in ["CheckpointLoaderSimple", "UNETLoader", "CLIPLoader", "VAELoader", "DualCLIPLoader"]:
                    # 这里可以根据模型名称更新模型文件
                    print(f"✅ 保持模型节点 {node_id} 不变")
                
                # 特殊处理：Google-Gemini节点
                elif class_type == "Google-Gemini":
                    # Gemini节点可能有不同的参数结构
                    if "prompt" in inputs:
                        inputs["prompt"] = description
                        print(f"✅ 更新Gemini节点 {node_id} prompt: '{description[:30]}...'")
                    elif "text" in inputs:
                        inputs["text"] = description
                        print(f"✅ 更新Gemini节点 {node_id} text: '{description[:30]}...'")
                    if "seed" in inputs and seed is not None:
                        inputs["seed"] = seed
                        print(f"✅ 更新Gemini节点 {node_id} seed: {seed}")
                    if "steps" in inputs:
                        inputs["steps"] = steps
                        print(f"✅ 更新Gemini节点 {node_id} steps: {steps}")
            
            print(f"✅ 参数应用完成")
            return workflow
            
        except Exception as e:
            print(f"❌ 应用参数失败: {e}")
            return workflow_template.copy()
    
    async def customize_workflow_from_config(self, reference_image_path: str, description: str, 
                                           parameters: Dict[str, Any], model_name: str,
                                           workflow_type: Optional[str] = None) -> Dict[str, Any]:
        """从配置自定义工作流参数"""
        try:
            # 获取工作流配置
            workflow_config = await self.get_workflow_by_model(model_name, workflow_type)
            if not workflow_config:
                # 如果没有找到配置，使用默认方法
                return await self.customize_workflow(reference_image_path, description, parameters, model_name)
            
            # 将description添加到parameters中
            parameters_with_description = parameters.copy()
            parameters_with_description["description"] = description
            print(f"🔍 调试: description参数值='{description[:50]}...'")
            print(f"🔍 调试: parameters_with_description['description']='{parameters_with_description['description'][:50]}...'")
            
            # 应用工作流配置，直接返回admin配置的工作流
            workflow_template = await self.apply_workflow_config(workflow_config, parameters_with_description, model_name)
            print(f"✅ 使用admin配置的工作流: {workflow_config.get('name')}")
            return workflow_template
        except Exception as e:
            print(f"从配置自定义工作流失败: {e}")
            # 降级到默认方法
            return await self.customize_workflow(reference_image_path, description, parameters, model_name)
    
    async def get_available_workflows(self, base_model_type: Optional[str] = None, 
                                    workflow_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取可用的工作流列表"""
        try:
            config_client = self._get_config_client()
            if config_client:
                config = await config_client.get_workflows_config()
                workflows = config.get("workflows", [])
                
                # 应用过滤条件
                filtered_workflows = []
                for workflow in workflows:
                    if not workflow.get("available", True):
                        continue
                    
                    if base_model_type and workflow.get("base_model_type") != base_model_type:
                        continue
                    
                    if workflow_type and workflow.get("workflow_type") != workflow_type:
                        continue
                    
                    filtered_workflows.append(workflow)
                
                return filtered_workflows
            else:
                # 配置客户端不可用，返回默认工作流
                return self._get_default_workflows(base_model_type, workflow_type)
        except Exception as e:
            print(f"获取可用工作流失败: {e}")
            return self._get_default_workflows(base_model_type, workflow_type)
    
    def _get_default_workflows(self, base_model_type: Optional[str] = None, 
                             workflow_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取默认工作流列表（降级方法）- 不再使用template_path"""
        default_workflows = [
            {
                "id": 1,
                "name": "qwen_image_generation",
                "display_name": "Qwen图像生成",
                "base_model_type": "qwen",
                "workflow_type": "image_generation",
                "workflow_json": {},  # 空的工作流JSON，需要从数据库获取
                "available": True,
                "description": "Qwen单图生成工作流"
            },
            # flux1工作流已移除，只保留FLUX.1 Kontext
        ]
        
        # 应用过滤条件
        filtered_workflows = []
        for workflow in default_workflows:
            if base_model_type and workflow.get("base_model_type") != base_model_type:
                continue
            
            if workflow_type and workflow.get("workflow_type") != workflow_type:
                continue
            
            filtered_workflows.append(workflow)
        
        return filtered_workflows
    

