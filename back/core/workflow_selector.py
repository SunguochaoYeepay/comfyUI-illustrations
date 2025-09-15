#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流选择器
负责根据模型选择工作流、工作流参数配置、工作流验证
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

from core.model_manager import get_model_config, ModelType

logger = logging.getLogger(__name__)


class WorkflowSelector:
    """工作流选择器"""
    
    def __init__(self):
        """初始化工作流选择器"""
        self._config_client = None
        self._workflow_cache = {}
    
    def _get_config_client(self):
        """获取配置客户端"""
        if self._config_client is None:
            try:
                from core.config_client import get_config_client
                self._config_client = get_config_client()
            except ImportError:
                return None
        return self._config_client
    
    async def select_workflow_for_model(self, model_name: str, 
                                      workflow_type: Optional[str] = None,
                                      parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        为指定模型选择最适合的工作流
        
        Args:
            model_name: 模型名称
            workflow_type: 工作流类型（可选）
            parameters: 生成参数（可选）
            
        Returns:
            选中的工作流配置
        """
        try:
            # 获取模型配置
            model_config = get_model_config(model_name)
            if not model_config:
                logger.error(f"模型 {model_name} 不存在")
                return None
            
            # 从配置客户端获取工作流
            config_client = self._get_config_client()
            if config_client:
                config = await config_client.get_workflows_config()
                workflows = config.get("workflows", [])
                
                # 查找匹配的工作流
                selected_workflow = self._find_best_workflow(workflows, model_name, workflow_type, parameters)
                if selected_workflow:
                    return selected_workflow
            
            # 如果配置客户端不可用或没有找到，使用默认选择逻辑
            return self._select_default_workflow(model_name, workflow_type, parameters)
            
        except Exception as e:
            logger.error(f"选择工作流失败: {e}")
            return self._select_default_workflow(model_name, workflow_type, parameters)
    
    def _find_best_workflow(self, workflows: List[Dict[str, Any]], model_name: str,
                          workflow_type: Optional[str] = None, 
                          parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """从工作流列表中找到最适合的工作流"""
        # 按优先级排序的工作流选择逻辑
        candidates = []
        
        for workflow in workflows:
            if not workflow.get("available", True):
                continue
            
            # 基础模型类型匹配
            if workflow.get("base_model_type") != model_name:
                continue
            
            # 工作流类型匹配
            if workflow_type and workflow.get("workflow_type") != workflow_type:
                continue
            
            # 计算匹配分数
            score = self._calculate_workflow_score(workflow, model_name, workflow_type, parameters)
            candidates.append((score, workflow))
        
        # 按分数排序，选择最高分的工作流
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        
        return None
    
    def _calculate_workflow_score(self, workflow: Dict[str, Any], model_name: str,
                                workflow_type: Optional[str] = None,
                                parameters: Optional[Dict[str, Any]] = None) -> int:
        """计算工作流匹配分数"""
        score = 0
        
        # 基础模型类型匹配
        if workflow.get("base_model_type") == model_name:
            score += 100
        
        # 工作流类型匹配
        if workflow_type and workflow.get("workflow_type") == workflow_type:
            score += 50
        
        # 可用性
        if workflow.get("available", True):
            score += 25
        
        # 根据参数进行额外评分
        if parameters:
            # 多图融合模式
            reference_image_paths = parameters.get("reference_image_paths", [])
            if len(reference_image_paths) >= 2:
                if workflow.get("workflow_type") == "image_fusion":
                    score += 30
            else:
                if workflow.get("workflow_type") == "image_generation":
                    score += 30
        
        return score
    
    def _select_default_workflow(self, model_name: str, workflow_type: Optional[str] = None,
                               parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """选择默认工作流（降级方法）"""
        model_config = get_model_config(model_name)
        if not model_config:
            return None
        
        # 根据模型类型和参数选择默认工作流
        if model_config.model_type == ModelType.QWEN:
            # 检查是否是多图融合模式
            if parameters:
                reference_image_paths = parameters.get("reference_image_paths", [])
                if len(reference_image_paths) >= 2:
                    return {
                        "id": 2,
                        "name": "qwen_image_fusion",
                        "display_name": "Qwen图像融合",
                        "base_model_type": "qwen",
                        "workflow_type": "image_fusion",
                        "template_path": "workflows/qwen_image_fusion_workflow.json",
                        "available": True,
                        "description": "Qwen多图融合工作流"
                    }
            
            return {
                "id": 1,
                "name": "qwen_image_generation",
                "display_name": "Qwen图像生成",
                "base_model_type": "qwen",
                "workflow_type": "image_generation",
                "template_path": "workflows/qwen_image_generation_workflow.json",
                "available": True,
                "description": "Qwen单图生成工作流"
            }
        
        elif model_config.model_type == ModelType.FLUX1:
            return {
                "id": 3,
                "name": "flux1_workflow",
                "display_name": "Flux1工作流",
                "base_model_type": "flux1",
                "workflow_type": "image_generation",
                "template_path": "workflows/flux1_vector_workflow.json",
                "available": True,
                "description": "Flux1基础模型工作流"
            }
        
        elif model_config.model_type == ModelType.FLUX:
            return {
                "id": 4,
                "name": "flux_kontext_workflow",
                "display_name": "Flux Kontext工作流",
                "base_model_type": "flux",
                "workflow_type": "image_generation",
                "template_path": "flux_kontext_dev_basic.json",
                "available": True,
                "description": "Flux Kontext开发版本工作流"
            }
        
        elif model_config.model_type == ModelType.WAN:
            return {
                "id": 5,
                "name": "wan_video_workflow",
                "display_name": "Wan视频生成",
                "base_model_type": "wan",
                "workflow_type": "video_generation",
                "template_path": "workflows/wan2.2_video_generation_workflow.json",
                "available": True,
                "description": "Wan2.2视频生成工作流"
            }
        
        elif model_config.model_type == ModelType.GEMINI:
            return {
                "id": 6,
                "name": "gemini_workflow",
                "display_name": "Gemini工作流",
                "base_model_type": "gemini",
                "workflow_type": "image_editing",
                "template_path": "workflows/google/api_google_gemini_image.json",
                "available": True,
                "description": "Google Gemini图像编辑工作流"
            }
        
        # 默认返回模型配置中的模板路径
        return {
            "id": 0,
            "name": f"{model_name}_default",
            "display_name": f"{model_config.display_name}默认工作流",
            "base_model_type": model_name,
            "workflow_type": workflow_type or "image_generation",
            "template_path": model_config.template_path,
            "available": True,
            "description": f"{model_config.display_name}的默认工作流"
        }
    
    async def validate_workflow(self, workflow_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证工作流配置
        
        Args:
            workflow_config: 工作流配置
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查必需字段
        required_fields = ["name", "base_model_type", "template_path"]
        for field in required_fields:
            if field not in workflow_config:
                errors.append(f"缺少必需字段: {field}")
        
        # 检查模板文件是否存在
        template_path = workflow_config.get("template_path")
        if template_path:
            template_file = Path(template_path)
            if not template_file.exists():
                errors.append(f"工作流模板文件不存在: {template_path}")
            else:
                # 验证JSON格式
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    errors.append(f"工作流模板JSON格式错误: {e}")
                except Exception as e:
                    errors.append(f"读取工作流模板失败: {e}")
        
        # 检查模型配置
        base_model_type = workflow_config.get("base_model_type")
        if base_model_type:
            model_config = get_model_config(base_model_type)
            if not model_config:
                errors.append(f"基础模型不存在: {base_model_type}")
            elif not model_config.available:
                errors.append(f"基础模型不可用: {base_model_type}")
        
        return len(errors) == 0, errors
    
    async def get_workflow_parameters(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取工作流参数配置
        
        Args:
            workflow_config: 工作流配置
            
        Returns:
            工作流参数配置
        """
        try:
            template_path = workflow_config.get("template_path")
            if not template_path:
                return {}
            
            template_file = Path(template_path)
            if not template_file.exists():
                return {}
            
            with open(template_file, 'r', encoding='utf-8') as f:
                workflow_template = json.load(f)
            
            # 提取参数配置
            parameters = self._extract_workflow_parameters(workflow_template)
            return parameters
            
        except Exception as e:
            logger.error(f"获取工作流参数失败: {e}")
            return {}
    
    def _extract_workflow_parameters(self, workflow_template: Dict[str, Any]) -> Dict[str, Any]:
        """从工作流模板中提取参数配置"""
        parameters = {}
        
        # 这里可以根据具体的工作流结构来提取参数
        # 目前返回基本的参数结构
        parameters.update({
            "width": 1024,
            "height": 1024,
            "steps": 20,
            "cfg": 8.0,
            "seed": -1,
            "batch_size": 1
        })
        
        return parameters
    
    async def customize_workflow_parameters(self, workflow_config: Dict[str, Any], 
                                          user_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        自定义工作流参数
        
        Args:
            workflow_config: 工作流配置
            user_parameters: 用户参数
            
        Returns:
            自定义后的工作流
        """
        try:
            # 直接从工作流配置中获取工作流JSON，不再依赖文件系统
            workflow_template = workflow_config.get("workflow_json")
            if not workflow_template:
                raise ValueError("工作流配置中缺少工作流JSON数据")
            
            # 应用用户参数
            customized_workflow = self._apply_user_parameters(workflow_template, user_parameters)
            
            return customized_workflow
            
        except Exception as e:
            logger.error(f"自定义工作流参数失败: {e}")
            raise
    
    def _apply_user_parameters(self, workflow_template: Dict[str, Any], 
                             user_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """将用户参数应用到工作流模板"""
        # 这里可以根据具体的工作流结构来应用参数
        # 目前先返回原始模板，后续可以根据需要扩展
        customized_workflow = workflow_template.copy()
        
        # 应用基本参数
        if "width" in user_parameters:
            # 这里需要根据具体的工作流结构来设置宽度
            pass
        
        if "height" in user_parameters:
            # 这里需要根据具体的工作流结构来设置高度
            pass
        
        if "steps" in user_parameters:
            # 这里需要根据具体的工作流结构来设置步数
            pass
        
        return customized_workflow


# 全局工作流选择器实例
_workflow_selector: Optional[WorkflowSelector] = None


def get_workflow_selector() -> WorkflowSelector:
    """获取工作流选择器实例"""
    global _workflow_selector
    if _workflow_selector is None:
        _workflow_selector = WorkflowSelector()
    return _workflow_selector


# 便捷函数
async def select_workflow_for_model(model_name: str, workflow_type: Optional[str] = None,
                                  parameters: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """为指定模型选择最适合的工作流"""
    selector = get_workflow_selector()
    return await selector.select_workflow_for_model(model_name, workflow_type, parameters)


async def validate_workflow(workflow_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """验证工作流配置"""
    selector = get_workflow_selector()
    return await selector.validate_workflow(workflow_config)


async def get_workflow_parameters(workflow_config: Dict[str, Any]) -> Dict[str, Any]:
    """获取工作流参数配置"""
    selector = get_workflow_selector()
    return await selector.get_workflow_parameters(workflow_config)


async def customize_workflow_parameters(workflow_config: Dict[str, Any], 
                                      user_parameters: Dict[str, Any]) -> Dict[str, Any]:
    """自定义工作流参数"""
    selector = get_workflow_selector()
    return await selector.customize_workflow_parameters(workflow_config, user_parameters)
