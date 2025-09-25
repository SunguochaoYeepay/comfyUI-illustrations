#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen扩图工作流实现
专门处理Qwen模型的扩图功能
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_workflow import BaseWorkflow
from config.settings import ADMIN_BACKEND_URL


class QwenOutpaintingWorkflow:
    """Qwen扩图工作流创建器 - 直接使用内置工作流文件"""
    
    def __init__(self, model_config=None):
        """初始化，不需要模型配置"""
        self.model_config = model_config
        print(f"🎨 Qwen扩图工作流初始化完成")
    
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """实现抽象基类的create_workflow方法
        
        Args:
            reference_image_path: 参考图像路径
            description: 扩图描述
            parameters: 生成参数，包含扩图尺寸等
            
        Returns:
            Qwen扩图工作流字典
        """
        return self.create_outpainting_workflow(reference_image_path, description, parameters)
    
    def create_outpainting_workflow(self, image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建Qwen扩图工作流
        
        Args:
            image_path: 原始图像路径
            description: 扩图描述
            parameters: 生成参数
            
        Returns:
            Qwen扩图工作流字典
        """
        print(f"🖼️ 创建Qwen扩图工作流")
        
        # 加载工作流模板
        workflow = self._load_qwen_outpainting_template()
        
        # 更新图像路径
        workflow = self._update_image_path(workflow, image_path)
        
        # 更新文本描述（提示词）
        workflow = self._update_text_description(workflow, description)
        
        # 更新扩图参数
        workflow = self._update_outpainting_parameters(workflow, parameters)
        
        # 更新保存路径
        workflow = self._update_save_path(workflow)
        
        # 验证工作流配置
        print(f"🔍 验证扩图工作流配置:")
        if "15" in workflow:
            print(f"   节点15 (LoadImage): {workflow['15']['inputs']['image']}")
        if "28" in workflow:
            print(f"   节点28 (正面提示词): {workflow['28']['inputs']['text'][:50]}...")
        if "3" in workflow:
            print(f"   节点3 (负面提示词): {workflow['3']['inputs']['text']}")
        if "12" in workflow:
            print(f"   节点12 (外补画板): left={workflow['12']['inputs']['left']}, top={workflow['12']['inputs']['top']}")
        if "21" in workflow:
            print(f"   节点21 (SaveImage): {workflow['21']['inputs']['filename_prefix']}")
        
        print(f"✅ Qwen扩图工作流创建完成")
        return workflow
    
    def _load_qwen_outpainting_template(self) -> Dict[str, Any]:
        """加载Qwen扩图工作流模板"""
        try:
            # 使用专门的扩图工作流模板
            template_path = Path(__file__).parent.parent.parent / "workflows" / "qwen_outpainting_workflow.json"
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    workflow = json.load(f)
                print(f"✅ 加载扩图工作流模板成功: {template_path}")
                return workflow
            else:
                print(f"❌ 扩图工作流模板文件不存在: {template_path}")
                raise FileNotFoundError(f"扩图工作流模板文件不存在: {template_path}")
                
        except Exception as e:
            print(f"❌ 加载扩图工作流模板失败: {e}")
            raise
    
    def _update_image_path(self, workflow: Dict[str, Any], image_path: str) -> Dict[str, Any]:
        """更新图像路径"""
        try:
            # 将图像复制到ComfyUI的input目录
            comfyui_image_path = self._copy_to_comfyui_input(image_path)
            
            # 更新LoadImage节点
            if "15" in workflow:
                workflow["15"]["inputs"]["image"] = comfyui_image_path
                print(f"✅ 更新图像路径: {os.path.basename(image_path)} -> {comfyui_image_path}")
            else:
                print(f"⚠️ 未找到LoadImage节点15")
            
            return workflow
            
        except Exception as e:
            print(f"❌ 更新图像路径失败: {e}")
            raise
    
    def _update_text_description(self, workflow: Dict[str, Any], description: str) -> Dict[str, Any]:
        """更新文本描述"""
        try:
            # 更新正面提示词
            if "28" in workflow:
                # 如果提示词为空，使用工作流模板的默认值（空字符串）
                final_description = description if description.strip() else ""
                workflow["28"]["inputs"]["text"] = final_description
                if final_description:
                    print(f"✅ 更新正面提示词: {final_description[:50]}...")
                else:
                    print(f"✅ 使用默认正面提示词: 空字符串（基于原图生成）")
            else:
                print(f"⚠️ 未找到正面提示词节点28")
            
            # 负面提示词保持默认
            if "3" in workflow:
                workflow["3"]["inputs"]["text"] = " "
                print(f"✅ 更新负面提示词: 空白")
            
            return workflow
            
        except Exception as e:
            print(f"❌ 更新文本描述失败: {e}")
            raise
    
    
    def _update_outpainting_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新扩图参数"""
        try:
            # 获取扩图参数
            original_width = parameters.get("original_width", 512)
            original_height = parameters.get("original_height", 512)
            expansion_width = parameters.get("expansion_width", 1024)
            expansion_height = parameters.get("expansion_height", 1024)
            expansion_x = parameters.get("expansion_x", 0)
            expansion_y = parameters.get("expansion_y", 0)
            
            print(f"🔧 扩图参数: 原图({original_width}x{original_height}), 扩图区域({expansion_width}x{expansion_height}), 位置({expansion_x},{expansion_y})")
            
            # 更新外补画板节点12（ImagePadForOutpaint）
            if "12" in workflow:
                # 计算扩图区域的边界
                # expansion_x, expansion_y 是扩图区域相对于原图的位置
                # 需要计算left, top, right, bottom
                
                # 扩图区域在原图中的位置
                left = expansion_x
                top = expansion_y
                right = expansion_x + expansion_width - original_width
                bottom = expansion_y + expansion_height - original_height
                
                # 确保边界值不为负数
                left = max(0, left)
                top = max(0, top)
                right = max(0, right)
                bottom = max(0, bottom)
                
                # 更新外补画板参数
                workflow["12"]["inputs"]["left"] = left
                workflow["12"]["inputs"]["top"] = top
                workflow["12"]["inputs"]["right"] = right
                workflow["12"]["inputs"]["bottom"] = bottom
                
                print(f"✅ 更新外补画板参数: left={left}, top={top}, right={right}, bottom={bottom}")
            else:
                print(f"⚠️ 未找到外补画板节点12")
            
            # 图像缩放节点31使用工作流默认配置，不需要动态修改
            
            return workflow
            
        except Exception as e:
            print(f"❌ 更新扩图参数失败: {e}")
            raise
    
    def _update_save_path(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新保存路径"""
        try:
            # 更新SaveImage节点（使用VAE解码的输出节点21）
            if "21" in workflow:
                import time
                timestamp = int(time.time() * 1000)
                workflow["21"]["inputs"]["filename_prefix"] = f"outpainting-{timestamp}"
                print(f"✅ 更新保存路径: outpainting-{timestamp}")
            else:
                print(f"⚠️ 未找到SaveImage节点21")
            
            return workflow
            
        except Exception as e:
            print(f"❌ 更新保存路径失败: {e}")
            raise
    
    def _copy_to_comfyui_input(self, image_path: str) -> str:
        """将图像文件复制到ComfyUI的input目录
        
        Args:
            image_path: 原始图像路径
            
        Returns:
            ComfyUI中的图像文件名
        """
        try:
            # ComfyUI输入目录路径
            comfyui_input_dir = Path("E:/AI-Image/ComfyUI-aki-v1.4/input")
            
            # 确保目录存在
            comfyui_input_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取文件名
            filename = Path(image_path).name
            
            # 目标路径
            target_path = comfyui_input_dir / filename
            
            # 复制文件
            shutil.copy2(image_path, target_path)
            
            print(f"✅ 图像已复制到ComfyUI输入目录: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 复制图像到ComfyUI输入目录失败: {e}")
            # 返回原始文件名作为降级方案
            return Path(image_path).name
