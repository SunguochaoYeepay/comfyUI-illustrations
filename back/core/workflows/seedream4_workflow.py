#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seedream4 Volcano Engine工作流实现
专门处理Seedream4模型的图像融合工作流创建
"""

import json
import random
from typing import Any, Dict, List, Optional

from .base_workflow import BaseWorkflow
from config.settings import ADMIN_BACKEND_URL


class Seedream4Workflow(BaseWorkflow):
    """Seedream4 Volcano Engine工作流创建器"""
    
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建Seedream4图像融合工作流
        
        Args:
            reference_image_path: 参考图像路径（第一张图）
            description: 图像融合描述
            parameters: 生成参数，包含：
                - reference_image_paths: 图像路径列表（最多2张）
                - prompt: 融合提示词
                - size_preset: 尺寸预设
                - width: 图像宽度
                - height: 图像高度
                - seed: 随机种子
        
        Returns:
            Seedream4工作流字典
        """
        print(f"🎨 创建Seedream4图像融合工作流: {self.model_config.display_name}")
        
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 获取图像路径列表
        image_paths = self._get_image_paths(reference_image_path, parameters)
        
        # 加载工作流模板
        workflow = self._load_workflow_template()
        
        # 更新图像输入
        workflow = self._update_image_inputs(workflow, image_paths)
        
        # 更新提示词
        workflow = self._update_prompt(workflow, description, validated_params)
        
        # 更新尺寸参数
        workflow = self._update_size_parameters(workflow, validated_params)
        
        # 更新种子
        workflow = self._update_seed(workflow, validated_params)
        
        # 更新保存路径
        workflow = self._update_save_path(workflow)
        
        print(f"✅ Seedream4图像融合工作流创建完成，处理 {len(image_paths)} 张图像")
        return workflow
    
    def _get_image_paths(self, reference_image_path: str, parameters: Dict[str, Any]) -> List[str]:
        """获取图像路径列表
        
        Args:
            reference_image_path: 参考图像路径
            parameters: 生成参数
            
        Returns:
            图像路径列表
        """
        image_paths = []
        
        # 从参数中获取图像路径列表
        reference_image_paths = parameters.get("reference_image_paths", [])
        
        # 添加第一张图（reference_image_path）
        if reference_image_path and reference_image_path.strip():
            processed_path = self._process_reference_image(reference_image_path)
            if processed_path:
                image_paths.append(processed_path)
        
        # 添加其他图像
        for path in reference_image_paths:
            if path and path.strip() and path not in image_paths:
                processed_path = self._process_reference_image(path)
                if processed_path:
                    image_paths.append(processed_path)
        
        # 限制最多2张图像
        if len(image_paths) > 2:
            print(f"⚠️ Seedream4只支持2张图像融合，将使用前2张图像")
            image_paths = image_paths[:2]
        
        # Seedream4是图像融合模型，如果没有图像输入，返回空列表
        if len(image_paths) == 0:
            print("📝 无图像输入，Seedream4将使用纯文本模式")
        
        return image_paths
    
    def _load_workflow_template(self) -> Dict[str, Any]:
        """从admin数据库加载Seedream4工作流模板"""
        try:
            # 尝试从配置客户端获取工作流模板
            from core.config_client import get_config_client
            config_client = get_config_client()
            if config_client:
                # 检查缓存中是否有工作流配置
                if hasattr(config_client, '_cache') and 'workflows' in config_client._cache:
                    config = config_client._cache['workflows']
                    print("✅ 从配置客户端缓存加载工作流模板")
                else:
                    # 如果没有缓存，尝试直接调用admin API
                    print("⚠️ 配置客户端无缓存，直接调用admin API...")
                    try:
                        import requests
                        admin_url = f"{ADMIN_BACKEND_URL}/api/admin/config-sync/workflows"
                        response = requests.get(admin_url, timeout=5)
                        if response.status_code == 200:
                            config = response.json()
                            print("✅ 直接调用admin API成功")
                        else:
                            print(f"⚠️ admin API调用失败: {response.status_code}，使用默认模板")
                            return self._get_default_workflow_template()
                    except Exception as api_error:
                        print(f"⚠️ admin API调用异常: {api_error}，使用默认模板")
                        return self._get_default_workflow_template()
                
                workflows = config.get("workflows", [])
                print(f"📋 找到 {len(workflows)} 个工作流配置")
                
                # 查找Seedream4工作流
                for workflow in workflows:
                    if (workflow.get("base_model_type") == "seedream4" and 
                        workflow.get("available", True)):
                        workflow_json = workflow.get("workflow_json")
                        if workflow_json:
                            print("✅ 从admin数据库加载Seedream4工作流模板")
                            return json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
                
                print("⚠️ 未找到Seedream4工作流配置，使用默认模板")
        except Exception as e:
            print(f"❌ 从admin数据库加载工作流模板失败: {e}")
        
        # 如果加载失败，使用默认模板
        print("📋 使用默认Seedream4工作流模板")
        return self._get_default_workflow_template()
    
    def _get_default_workflow_template(self) -> Dict[str, Any]:
        """获取默认的Seedream4工作流模板"""
        return {
            "11": {
                "inputs": {
                    "image": "generated-image-1758020573908.png"
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            },
            "12": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": [
                        "22",
                        0
                    ]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "保存图像"
                }
            },
            "22": {
                "inputs": {
                    "prompt": "图1与图2合并，坐在一起由歌和福吉",
                    "size_preset": "2304x1728 (4:3)",
                    "width": 2048,
                    "height": 2048,
                    "seed": 559718440,
                    "image_input": [
                        "24",
                        0
                    ]
                },
                "class_type": "Seedream4_VolcEngine",
                "_meta": {
                    "title": "Seedream4 Volcano Engine"
                }
            },
            "24": {
                "inputs": {
                    "image1": [
                        "11",
                        0
                    ],
                    "image2": [
                        "25",
                        0
                    ]
                },
                "class_type": "ImageBatch",
                "_meta": {
                    "title": "图像组合批处理"
                }
            },
            "25": {
                "inputs": {
                    "image": "generated-image-1758020573908.png"
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            }
        }
    
    def _update_image_inputs(self, workflow: Dict[str, Any], image_paths: List[str]) -> Dict[str, Any]:
        """更新工作流中的图像输入
        
        Args:
            workflow: 工作流字典
            image_paths: 图像路径列表
            
        Returns:
            更新后的工作流字典
        """
        if len(image_paths) == 0:
            # 无图像模式：不连接图像节点，直接连接Seedream4节点
            print("📝 无图像模式：跳过图像节点连接")
            # 移除ImageBatch节点的图像输入连接
            if "24" in workflow:
                workflow["24"]["inputs"]["image1"] = None
                workflow["24"]["inputs"]["image2"] = None
            # 移除Seedream4节点的图像输入连接
            if "22" in workflow:
                workflow["22"]["inputs"]["image_input"] = None
        else:
            # 有图像模式：正常连接图像节点
            # 更新第一张图像（节点11）
            if len(image_paths) > 0:
                workflow["11"]["inputs"]["image"] = image_paths[0]
            
            # 更新第二张图像（节点25）
            if len(image_paths) > 1:
                workflow["25"]["inputs"]["image"] = image_paths[1]
            else:
                # 只有一张图像时，第二张也使用第一张图像
                workflow["25"]["inputs"]["image"] = image_paths[0]
            
            print(f"📸 已更新图像输入: {image_paths}")
        
        return workflow
    
    def _update_prompt(self, workflow: Dict[str, Any], description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新工作流中的提示词
        
        Args:
            workflow: 工作流字典
            description: 图像描述
            parameters: 生成参数
            
        Returns:
            更新后的工作流字典
        """
        # 从参数中获取提示词，如果没有则使用description
        prompt = parameters.get("prompt", description)
        
        # 更新节点22的提示词
        workflow["22"]["inputs"]["prompt"] = prompt
        
        print(f"📝 已更新提示词: {prompt}")
        return workflow
    
    def _update_size_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新工作流中的尺寸参数
        
        Args:
            workflow: 工作流字典
            parameters: 生成参数
            
        Returns:
            更新后的工作流字典
        """
        # 获取尺寸参数
        size_preset = parameters.get("size_preset", "2304x1728 (4:3)")
        width = parameters.get("width", 2048)
        height = parameters.get("height", 2048)
        
        # 更新节点22的尺寸参数
        workflow["22"]["inputs"]["size_preset"] = size_preset
        workflow["22"]["inputs"]["width"] = width
        workflow["22"]["inputs"]["height"] = height
        
        print(f"📐 已更新尺寸参数: {size_preset}, {width}x{height}")
        return workflow
    
    def _update_seed(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新工作流中的种子
        
        Args:
            workflow: 工作流字典
            parameters: 生成参数
            
        Returns:
            更新后的工作流字典
        """
        seed = parameters.get("seed", random.randint(1, 2**31 - 1))  # 限制在int32范围内
        
        # 更新节点22的种子
        workflow["22"]["inputs"]["seed"] = seed
        
        print(f"🎲 已更新种子: {seed}")
        return workflow
    
    def _update_save_path(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新工作流中的保存路径
        
        Args:
            workflow: 工作流字典
            
        Returns:
            更新后的工作流字典
        """
        # 生成唯一的文件名前缀
        import time
        timestamp = int(time.time() * 1000)
        filename_prefix = f"Seedream4_{timestamp}"
        
        # 更新节点12的文件名前缀
        workflow["12"]["inputs"]["filename_prefix"] = filename_prefix
        
        print(f"💾 已更新保存路径: {filename_prefix}")
        return workflow
