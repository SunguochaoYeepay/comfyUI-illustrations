#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JoyCaption工作流实现
专门处理图片内容反推的工作流创建
"""

import json
import os
from typing import Any, Dict
from pathlib import Path

from .base_workflow import BaseWorkflow
from config.settings import COMFYUI_INPUT_DIR


class JoyCaptionWorkflow(BaseWorkflow):
    """JoyCaption图片反推工作流创建器"""
    
    def create_workflow(self, image_path: str, description: str = "", parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建JoyCaption工作流
        
        Args:
            image_path: 要反推的图片路径
            description: 描述（图片反推不需要）
            parameters: 反推参数
            
        Returns:
            JoyCaption工作流字典
        """
        print(f"🔍 创建JoyCaption工作流: {self.model_config.display_name}")
        
        # 验证参数
        if parameters is None:
            parameters = {}
        
        # 处理图片路径
        processed_image_path = self._process_image_path(image_path)
        
        # 加载工作流模板
        workflow = self._load_workflow_template()
        
        # 更新图片输入
        workflow = self._update_image_input(workflow, processed_image_path)
        
        # 更新反推参数
        workflow = self._update_caption_parameters(workflow, parameters)
        
        print(f"✅ JoyCaption工作流创建完成")
        return workflow
    
    def _process_image_path(self, image_path: str) -> str:
        """处理图片路径，确保ComfyUI可以访问"""
        from config.settings import ENVIRONMENT
        
        if ENVIRONMENT == "production":
            # Docker环境：直接使用本地文件路径
            return image_path
        else:
            # 本地环境：检查是否需要复制到ComfyUI输入目录
            import shutil
            from pathlib import Path
            
            input_path = Path(image_path)
            if not input_path.exists():
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            # 检查是否需要复制到ComfyUI输入目录
            comfyui_input_path = COMFYUI_INPUT_DIR / input_path.name
            
            if not comfyui_input_path.exists() or comfyui_input_path != input_path:
                shutil.copy2(input_path, comfyui_input_path)
                print(f"📁 复制图片到ComfyUI输入目录: {input_path} -> {comfyui_input_path}")
            else:
                print(f"📁 图片已存在于ComfyUI输入目录: {comfyui_input_path}")
            
            return str(comfyui_input_path)
    
    def _load_workflow_template(self) -> Dict[str, Any]:
        """加载JoyCaption工作流模板"""
        # 使用提供的JoyCaption工作流作为模板
        workflow_template = {
            "11": {
                "inputs": {
                    "memory_mode": "Default",
                    "caption_type": "Descriptive",
                    "caption_length": "very long",
                    "extra_option1": "Do NOT mention the image's resolution.",
                    "extra_option2": "",
                    "extra_option3": "",
                    "extra_option4": "",
                    "extra_option5": "",
                    "person_name": "",
                    "max_new_tokens": 2048,
                    "temperature": 0.6,
                    "top_p": 0.9,
                    "top_k": 0,
                    "image": [
                        "14",
                        0
                    ]
                },
                "class_type": "JJC_JoyCaption",
                "_meta": {
                    "title": "JoyCaption"
                }
            },
            "14": {
                "inputs": {
                    "image": ""  # 将在_update_image_input中设置
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            },
            "15": {
                "inputs": {
                    "text_0": "This is a screenshot of a computer interface displaying a text editor or code editor window, likely part of a software development environment. The interface has a dark gray background with white and blue text. The top left corner shows a tab labeled \"Untitled 2022-06-01\" with a drop-down menu and various icons, including a \"New File\" option. The top right corner features a toolbar with icons for \"Save,\" \"Undo,\" \"Redo,\" and others.\n\nThe main content area is filled with a long list of code snippets or text lines, each starting with a number followed by a brief description or command. The text is divided into sections by horizontal gray lines, and most lines are written in white text, with some lines highlighted in blue. The code snippets include terms like \"Running Game,\" \"Game Logic,\" \"Game State,\" and \"Game Loop,\" indicating a game development context. The code uses a mix of camel case and underscore notation, typical in programming languages.\n\nOn the right side of the interface, there is a vertical column with a \"In the code\" section, displaying a line of text \"game_state = 0\" in blue. The bottom left corner has a \"Code Editor\" label, and the bottom right corner has a \"To Do\" section with a blue text input field. The overall style is modern and functional, with a focus on readability and efficiency.",
                    "text": [
                        "11",
                        1
                    ]
                },
                "class_type": "ShowText|pysssss",
                "_meta": {
                    "title": "展示文本"
                }
            },
            "20": {
                "inputs": {
                    "text_0": "Write a very long detailed description for this image. Do NOT mention the image's resolution.",
                    "text": [
                        "11",
                        0
                    ]
                },
                "class_type": "ShowText|pysssss",
                "_meta": {
                    "title": "展示文本"
                }
            }
        }
        
        print("✅ 加载JoyCaption工作流模板")
        return workflow_template
    
    def _update_image_input(self, workflow: Dict[str, Any], image_path: str) -> Dict[str, Any]:
        """更新图片输入节点"""
        # 获取文件名（ComfyUI需要相对路径）
        filename = os.path.basename(image_path)
        
        # 更新LoadImage节点
        if "14" in workflow:
            workflow["14"]["inputs"]["image"] = filename
            print(f"✅ 更新图片输入: {filename}")
        
        return workflow
    
    def _update_caption_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新反推参数"""
        if "11" in workflow:
            # 更新caption_type
            caption_type = parameters.get("caption_type", "Descriptive")
            workflow["11"]["inputs"]["caption_type"] = caption_type
            
            # 更新caption_length
            caption_length = parameters.get("caption_length", "very long")
            workflow["11"]["inputs"]["caption_length"] = caption_length
            
            # 更新max_new_tokens
            max_new_tokens = parameters.get("max_new_tokens", 2048)
            workflow["11"]["inputs"]["max_new_tokens"] = max_new_tokens
            
            # 更新temperature
            temperature = parameters.get("temperature", 0.6)
            workflow["11"]["inputs"]["temperature"] = temperature
            
            # 更新top_p
            top_p = parameters.get("top_p", 0.9)
            workflow["11"]["inputs"]["top_p"] = top_p
            
            print(f"✅ 更新反推参数: type={caption_type}, length={caption_length}, tokens={max_new_tokens}")
        
        return workflow
