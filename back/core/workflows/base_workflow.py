#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础工作流抽象类
定义工作流创建器的公共接口和方法
"""

import json
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import (
    TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT, 
    DEFAULT_STEPS, DEFAULT_COUNT, COMFYUI_MAIN_OUTPUT_DIR
)


class BaseWorkflow(ABC):
    """基础工作流抽象类"""
    
    def __init__(self, model_config):
        """初始化工作流创建器
        
        Args:
            model_config: 模型配置对象
        """
        self.model_config = model_config
    
    @abstractmethod
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建工作流
        
        Args:
            reference_image_path: 参考图像路径
            description: 图像描述
            parameters: 生成参数
            
        Returns:
            工作流字典
        """
        pass
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证和标准化参数
        
        Args:
            parameters: 原始参数
            
        Returns:
            标准化后的参数
        """
        validated = parameters.copy()
        
        # 验证步数
        if 'steps' in validated:
            if not isinstance(validated['steps'], int) or validated['steps'] < 1:
                validated['steps'] = DEFAULT_STEPS
        else:
            validated['steps'] = DEFAULT_STEPS
        
        # 验证生成数量
        if 'count' in validated:
            if not isinstance(validated['count'], int) or validated['count'] < 1:
                validated['count'] = DEFAULT_COUNT
        else:
            validated['count'] = DEFAULT_COUNT
        
        # 验证种子
        if 'seed' in validated:
            if not isinstance(validated['seed'], int):
                validated['seed'] = random.randint(1, 2**31 - 1)  # 限制在int32范围内
        else:
            validated['seed'] = random.randint(1, 2**31 - 1)  # 限制在int32范围内
        
        return validated
    
    def _process_loras(self, loras: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理LoRA配置
        
        Args:
            loras: LoRA配置列表
            
        Returns:
            处理后的LoRA配置
        """
        if not loras:
            return []
        
        # 限制最多4个LoRA
        loras = loras[:4]
        
        # 验证每个LoRA配置
        processed_loras = []
        for lora in loras:
            if not isinstance(lora, dict):
                continue
                
            processed_lora = {
                'name': lora.get('name', ''),
                'enabled': lora.get('enabled', True),
                'strength_model': lora.get('strength_model', 1.0),
                'strength_clip': lora.get('strength_clip', 1.0),
                'trigger_word': lora.get('trigger_word', '')
            }
            
            if processed_lora['name'] and processed_lora['enabled']:
                # 检查LoRA兼容性
                if self._is_lora_compatible(processed_lora['name']):
                    processed_loras.append(processed_lora)
                else:
                    print(f"⚠️ LoRA不兼容，已跳过: {processed_lora['name']}")
        
        return processed_loras
    
    def _is_lora_compatible(self, lora_name: str) -> bool:
        """检查LoRA是否与当前模型兼容
        
        Args:
            lora_name: LoRA文件名
            
        Returns:
            是否兼容
        """
        lora_name_lower = lora_name.lower()
        
        if self.model_config.model_type.value == 'flux':
            # Flux模型：排除Qwen相关的LoRA
            return not any(keyword in lora_name_lower for keyword in ['qwen', '千问', 'qwen2'])
        elif self.model_config.model_type.value == 'qwen':
            # Qwen模型：排除明确为Flux的LoRA
            return not any(keyword in lora_name_lower for keyword in ['flux', 'kontext', 'sdxl'])
        
        return True
    
    def _process_reference_image(self, reference_image_path: str, target_width: int = None, target_height: int = None) -> Optional[str]:
        """处理参考图像
        
        Args:
            reference_image_path: 参考图像路径
            target_width: 目标宽度，如果为None则使用默认值
            target_height: 目标高度，如果为None则使用默认值
            
        Returns:
            处理后的图像路径，如果没有参考图则返回None
        """
        if not reference_image_path or not reference_image_path.strip():
            return None
            
        if reference_image_path.endswith('blank.png') or reference_image_path == "":
            return None
        
        # 检查是否为uploads目录下的文件
        container_path = Path(reference_image_path)
        normalized_path = str(container_path).replace('\\', '/')
        
        if not normalized_path.startswith('uploads/'):
            return reference_image_path
        
        # 处理uploads目录下的图像
        try:
            from PIL import Image
            
            source_file = Path(reference_image_path)
            dest_file = COMFYUI_MAIN_OUTPUT_DIR / source_file.name
            
            # 使用传入的尺寸参数，如果没有则使用默认值
            width = target_width if target_width is not None else TARGET_IMAGE_WIDTH
            height = target_height if target_height is not None else TARGET_IMAGE_HEIGHT
            
            # 压缩图像到目标尺寸
            with Image.open(source_file) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
                
                background = Image.new('RGB', (width, height), (255, 255, 255))
                offset = ((width - img.width) // 2, (height - img.height) // 2)
                background.paste(img, offset)
                background.save(dest_file, 'PNG')
            
            print(f"✅ 参考图压缩到{width}x{height}并保存成功: {source_file} -> {dest_file}")
            return f"{source_file.name} [output]"
            
        except Exception as e:
            print(f"❌ 参考图处理失败: {e}")
            return None
    
    def _get_image_dimensions(self, parameters: Dict[str, Any]) -> tuple:
        """获取图像尺寸
        
        Args:
            parameters: 生成参数
            
        Returns:
            (width, height) 元组
        """
        # 从参数中解析尺寸
        size_str = parameters.get("size", "1024x1024")
        try:
            width, height = map(int, size_str.split('x'))
            return width, height
        except (ValueError, AttributeError):
            # 如果解析失败，使用默认尺寸
            return TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT
    
    def _add_common_metadata(self, workflow: Dict[str, Any], description: str, parameters: Dict[str, Any]):
        """添加公共元数据
        
        Args:
            workflow: 工作流字典
            description: 图像描述
            parameters: 生成参数
        """
        # 这里可以添加一些公共的元数据设置
        # 比如版本信息、创建时间等
        pass
