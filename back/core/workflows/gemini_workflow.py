#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Gemini 工作流实现
基于用户提供的 api_google_gemini_image.json 结构
"""

import json
import os
import random
from typing import Any, Dict, List

from .base_workflow import BaseWorkflow
from config.settings import GEMINI_API_KEY


class GeminiWorkflow(BaseWorkflow):
    """Google Gemini 工作流创建器"""
    
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建Gemini工作流
        
        Args:
            reference_image_path: 参考图像路径
            description: 图像描述
            parameters: 生成参数
            
        Returns:
            Gemini工作流字典
        """
        print(f"🎨 创建 Nano Banana 工作流: {self.model_config.display_name}")
        
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 判断工作流模式
        image_paths = parameters.get("reference_image_paths", [])
        
        if len(image_paths) == 0 and not reference_image_path:
            # 无图模式
            workflow = self._create_no_image_workflow(description, validated_params)
            print("📸 无图模式：纯文本生成")
        elif len(image_paths) == 1 or (len(image_paths) == 0 and reference_image_path):
            # 1图模式
            single_image = image_paths[0] if image_paths else reference_image_path
            workflow = self._create_single_image_workflow(single_image, description, validated_params)
            print(f"📸 1图模式：单图处理 - {single_image}")
        elif len(image_paths) == 2:
            # 2图模式
            workflow = self._create_dual_image_workflow(image_paths, description, validated_params)
            print(f"📸 2图模式：双图融合 - {len(image_paths)}张图片")
        else:
            raise ValueError(f"Gemini 工作流不支持 {len(image_paths)} 张图片，最多支持2张")
        
        print(f"✅ Nano Banana 工作流创建完成，包含 {len(workflow)} 个节点")
        return workflow
    
    def _create_no_image_workflow(self, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建无图工作流"""
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 获取API密钥
        if not GEMINI_API_KEY:
            print("⚠️ 警告: GEMINI_API_KEY 环境变量未设置，使用硬编码密钥")
            # 临时使用硬编码密钥进行测试
            api_key = "AIzaSyD3jLviN6sZENUgkDi6riIJzCsx7hCeH8c"
        else:
            print(f"✅ 使用环境变量中的Gemini API密钥: {GEMINI_API_KEY[:10]}...")
            api_key = GEMINI_API_KEY
        
        workflow = {
            "32": {
                "inputs": {
                    "prompt": description,
                    "api_key": api_key,
                    "model": "models/gemini-2.0-flash-preview-image-generation",
                    "aspect_ratio": "Free (自由比例)",
                    "temperature": 1,
                    "seed": validated_params["seed"],
                    "images": None
                },
                "class_type": "Google-Gemini",
                "_meta": {
                    "title": "Gemini 2.0 image"
                }
            },
            "4": {
                "inputs": {
                    "preview": "Empty response from Gemini model...",
                    "source": ["32", 1]
                },
                "class_type": "PreviewAny",
                "_meta": {
                    "title": "预览任意"
                }
            },
            "30": {
                "inputs": {
                    "filename_prefix": "yeepay/yeepay",
                    "images": ["32", 0]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "保存图像"
                }
            }
        }
        return workflow
    
    def _create_single_image_workflow(self, image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建单图工作流"""
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 转换路径为ComfyUI兼容格式
        comfyui_path = self._convert_path_for_comfyui(image_path)
        # 获取API密钥
        if not GEMINI_API_KEY:
            print("⚠️ 警告: GEMINI_API_KEY 环境变量未设置，使用硬编码密钥")
            # 临时使用硬编码密钥进行测试
            api_key = "AIzaSyD3jLviN6sZENUgkDi6riIJzCsx7hCeH8c"
        else:
            print(f"✅ 使用环境变量中的Gemini API密钥: {GEMINI_API_KEY[:10]}...")
            api_key = GEMINI_API_KEY
        
        workflow = {
            "11": {
                "inputs": {
                    "image": comfyui_path
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            },
            "32": {
                "inputs": {
                    "prompt": description,
                    "api_key": api_key,
                    "model": "models/gemini-2.0-flash-preview-image-generation",
                    "aspect_ratio": "Free (自由比例)",
                    "temperature": 1,
                    "seed": validated_params["seed"],
                    "images": ["11", 0]
                },
                "class_type": "Google-Gemini",
                "_meta": {
                    "title": "Gemini 2.0 image"
                }
            },
            "4": {
                "inputs": {
                    "preview": "Empty response from Gemini model...",
                    "source": ["32", 1]
                },
                "class_type": "PreviewAny",
                "_meta": {
                    "title": "预览任意"
                }
            },
            "30": {
                "inputs": {
                    "filename_prefix": "yeepay/yeepay",
                    "images": ["32", 0]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "保存图像"
                }
            }
        }
        return workflow
    
    def _create_dual_image_workflow(self, image_paths: List[str], description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建双图工作流"""
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 转换路径为ComfyUI兼容格式
        comfyui_path1 = self._convert_path_for_comfyui(image_paths[0])
        comfyui_path2 = self._convert_path_for_comfyui(image_paths[1])
        # 获取API密钥
        if not GEMINI_API_KEY:
            print("⚠️ 警告: GEMINI_API_KEY 环境变量未设置，使用硬编码密钥")
            # 临时使用硬编码密钥进行测试
            api_key = "AIzaSyD3jLviN6sZENUgkDi6riIJzCsx7hCeH8c"
        else:
            print(f"✅ 使用环境变量中的Gemini API密钥: {GEMINI_API_KEY[:10]}...")
            api_key = GEMINI_API_KEY
        
        workflow = {
            "11": {
                "inputs": {
                    "image": comfyui_path1
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            },
            "12": {
                "inputs": {
                    "image": comfyui_path2
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "加载图像"
                }
            },
            "10": {
                "inputs": {
                    "image1": ["11", 0],
                    "image2": ["12", 0]
                },
                "class_type": "ImageBatch",
                "_meta": {
                    "title": "图像组合批次"
                }
            },
            "32": {
                "inputs": {
                    "prompt": description,
                    "api_key": api_key,
                    "model": "models/gemini-2.0-flash-preview-image-generation",
                    "aspect_ratio": "Free (自由比例)",
                    "temperature": 1,
                    "seed": validated_params["seed"],
                    "images": ["10", 0]
                },
                "class_type": "Google-Gemini",
                "_meta": {
                    "title": "Gemini 2.0 image"
                }
            },
            "4": {
                "inputs": {
                    "preview": "Empty response from Gemini model...",
                    "source": ["32", 1]
                },
                "class_type": "PreviewAny",
                "_meta": {
                    "title": "预览任意"
                }
            },
            "30": {
                "inputs": {
                    "filename_prefix": "yeepay/yeepay",
                    "images": ["32", 0]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "保存图像"
                }
            }
        }
        return workflow
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """验证和标准化参数"""
        # ComfyUI Google-Gemini节点种子值范围: 0 到 2147483647 (32位有符号整数最大值)
        max_seed = 2147483647
        validated = {
            "seed": parameters.get("seed", random.randint(1, max_seed)),
            "model": parameters.get("model", "gemini-2.5-flash-image-preview")
        }
        
        # Gemini 特定参数验证
        if "seed" in parameters:
            try:
                seed_value = int(parameters["seed"])
                # 确保种子值在有效范围内
                if seed_value < 0 or seed_value > max_seed:
                    print(f"⚠️ 种子值 {seed_value} 超出范围，调整为有效值")
                    seed_value = random.randint(1, max_seed)
                validated["seed"] = seed_value
            except (ValueError, TypeError):
                validated["seed"] = random.randint(1, max_seed)
        else:
            # 如果没有提供种子，生成一个在有效范围内的随机种子
            validated["seed"] = random.randint(1, max_seed)
        
        print(f"🎲 使用种子值: {validated['seed']} (范围: 0-{max_seed})")
        return validated
    
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
