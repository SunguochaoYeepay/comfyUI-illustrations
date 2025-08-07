#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流模板管理器
负责创建和自定义Flux Kontext工作流
"""

import json
import random
from pathlib import Path
from typing import Any, Dict

from config.settings import (
    TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT, 
    DEFAULT_STEPS, DEFAULT_COUNT, COMFYUI_MAIN_OUTPUT_DIR
)


class WorkflowTemplate:
    """工作流模板管理器，负责创建和自定义Flux Kontext工作流"""
    
    def __init__(self, template_path: str):
        """初始化工作流模板
        
        Args:
            template_path: 模板文件路径
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                self.template = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"工作流模板文件不存在: {template_path}")
        except json.JSONDecodeError:
            raise ValueError(f"工作流模板文件格式错误: {template_path}")
    
    def customize_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]):
        """自定义工作流参数"""
        # 创建一个简化的Flux Kontext工作流，避免原始模板的复杂节点连接问题
        
        workflow = {
            "6": {
                "inputs": {
                    "text": description,
                    "clip": ["38", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP文本编码器"}
            },
            "8": {
                "inputs": {
                    "samples": ["31", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "VAE解码"}
            },
            "31": {
                "inputs": {
                    "seed": parameters.get("seed", random.randint(1, 2**32 - 1)),
                    "steps": parameters.get("steps", DEFAULT_STEPS),
                    "cfg": 1,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "denoise": 1,
                    "batch_size": parameters.get("count", DEFAULT_COUNT),
                    "model": ["37", 0],
                    "positive": ["35", 0],
                    "negative": ["135", 0],
                    "latent_image": ["124", 0]
                },
                "class_type": "KSampler",
                "_meta": {"title": "K采样器"}
            },
            "35": {
                "inputs": {
                    "guidance": 2.5,
                    "conditioning": ["177", 0]
                },
                "class_type": "FluxGuidance",
                "_meta": {"title": "Flux引导"}
            },
            "37": {
                "inputs": {
                    "unet_name": "flux1-dev-kontext_fp8_scaled.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "UNET加载器"}
            },
            "38": {
                "inputs": {
                    "clip_name1": "clip_l.safetensors",
                    "clip_name2": "t5xxl_fp8_e4m3fn_scaled.safetensors",
                    "type": "flux",
                    "device": "default"
                },
                "class_type": "DualCLIPLoader",
                "_meta": {"title": "双CLIP加载器"}
            },
            "39": {
                "inputs": {
                    "vae_name": "ae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {"title": "VAE加载器"}
            },
            "42": {
                "inputs": {
                    "width": TARGET_IMAGE_WIDTH,
                    "height": TARGET_IMAGE_HEIGHT,
                    "batch_size": 1,
                    "color": 0
                },
                "class_type": "EmptyImage",
                "_meta": {"title": "空图像"}
            },
            "124": {
                "inputs": {
                    "pixels": ["42", 0],
                    "vae": ["39", 0]
                },
                "class_type": "VAEEncode",
                "_meta": {"title": "VAE编码"}
            },
            "135": {
                "inputs": {
                    "conditioning": ["6", 0]
                },
                "class_type": "ConditioningZeroOut",
                "_meta": {"title": "条件零化"}
            },
            "136": {
                "inputs": {
                    "filename_prefix": "yeepay/yeepay",
                    "images": ["8", 0],
                    "save_all": True
                },
                "class_type": "SaveImage",
                "_meta": {"title": "保存图像"}
            },
            "177": {
                "inputs": {
                    "conditioning": ["6", 0],
                    "latent": ["124", 0]
                },
                "class_type": "ReferenceLatent",
                "_meta": {"title": "ReferenceLatent"}
            }
        }
        
        print(f"✅ 创建简化工作流，包含 {len(workflow)} 个节点")
        print(f"📋 工作流节点: {list(workflow.keys())}")
        
        # 检查是否有参考图
        has_reference_image = reference_image_path and reference_image_path.strip() and not reference_image_path.endswith('blank.png') and reference_image_path != ""
        
        if has_reference_image:
            print("检测到参考图，使用参考图模式")
            # 更新参考图像路径 - 将上传的图像复制到ComfyUI输出目录并使用[output]后缀
            container_path = Path(reference_image_path)
            # 统一路径分隔符，确保能正确匹配
            normalized_path = str(container_path).replace('\\', '/')
            if normalized_path.startswith('uploads/'):
                # 将上传的图像压缩到512x512并复制到ComfyUI输出目录
                import shutil
                from PIL import Image
                import io
                
                source_file = Path(reference_image_path)
                dest_file = COMFYUI_MAIN_OUTPUT_DIR / source_file.name
                
                try:
                    # 使用PIL压缩图像到512x512
                    with Image.open(source_file) as img:
                        # 转换为RGB模式（如果需要）
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # 压缩到512x512，保持宽高比
                        img.thumbnail((TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT), Image.Resampling.LANCZOS)
                        
                        # 创建512x512的白色背景
                        background = Image.new('RGB', (TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT), (255, 255, 255))
                        
                        # 将压缩后的图像居中放置
                        offset = ((TARGET_IMAGE_WIDTH - img.width) // 2, (TARGET_IMAGE_HEIGHT - img.height) // 2)
                        background.paste(img, offset)
                        
                        # 保存压缩后的图像
                        background.save(dest_file, 'PNG')
                    
                    print(f"✅ 参考图压缩到512x512并保存成功: {source_file} -> {dest_file}")
                except Exception as e:
                    print(f"❌ 参考图压缩失败: {e}")
                    print(f"📁 源文件: {source_file}")
                    print(f"📁 目标文件: {dest_file}")
                    raise Exception(f"无法压缩参考图像到{TARGET_IMAGE_WIDTH}x{TARGET_IMAGE_HEIGHT}: {e}")
                
                # 使用文件名加上[output]后缀
                image_filename = f"{source_file.name} [output]"
                print(f"设置LoadImageOutput图像路径: {image_filename}")
                
                # 添加LoadImageOutput节点
                workflow["142"] = {
                    "inputs": {
                        "image": image_filename,
                        "refresh": "refresh"
                    },
                    "class_type": "LoadImageOutput",
                    "_meta": {"title": "加载图像（来自输出）"}
                }
                
                # 使用ImageScale节点替代FluxKontextImageScale，强制固定尺寸
                workflow["42"] = {
                    "inputs": {
                        "image": ["142", 0],
                        "width": TARGET_IMAGE_WIDTH,
                        "height": TARGET_IMAGE_HEIGHT,
                        "crop": "disabled",
                        "upscale_method": "lanczos",
                        "downscale_method": "area"
                    },
                    "class_type": "ImageScale",
                    "_meta": {"title": "图像缩放"}
                }
                
                # 更新VAEEncode节点使用FluxKontextImageScale的输出
                workflow["124"]["inputs"]["pixels"] = ["42", 0]
                
                print(f"✅ 配置参考图模式工作流")
            else:
                print(f"使用原始路径: {reference_image_path}")
        else:
            print("未检测到参考图，使用无参考图模式")
            print(f"✅ 配置无参考图模式工作流")
        
        # 更新生成参数
        if parameters.get("steps"):
            workflow["31"]["inputs"]["steps"] = parameters["steps"]
        
        # 更新CFG参数（如果提供）
        if parameters.get("cfg"):
            workflow["31"]["inputs"]["cfg"] = parameters["cfg"]
        
        # 更新Guidance参数（如果提供）
        if parameters.get("guidance"):
            workflow["35"]["inputs"]["guidance"] = parameters["guidance"]
        
        # 处理图像尺寸 - 永远使用512x512
        target_width = TARGET_IMAGE_WIDTH
        target_height = TARGET_IMAGE_HEIGHT
        
        # 无论是否有参考图，都使用固定的512x512尺寸
        if "42" in workflow and "inputs" in workflow["42"]:
            workflow["42"]["inputs"]["width"] = target_width
            workflow["42"]["inputs"]["height"] = target_height
            print(f"设置生成图片尺寸为: {target_width}x{target_height} (固定尺寸)")
        
        # 处理生成数量
        count = parameters.get("count", 1)
        print(f"生成数量: {count}")
        # 设置KSampler的batch_size参数
        if count > 1:
            workflow["31"]["inputs"]["batch_size"] = count
            print(f"设置batch_size为: {count}")
            # 确保SaveImage节点的save_all参数为true
            if "136" in workflow and "inputs" in workflow["136"]:
                workflow["136"]["inputs"]["save_all"] = True
                print(f"设置SaveImage节点的save_all参数为true，确保保存所有批次图片")
        else:
            # 确保单张图片时batch_size为1
            workflow["31"]["inputs"]["batch_size"] = 1
        
        # 设置SaveImage节点的文件名前缀为yeepay，用于区分项目
        if "136" in workflow and "inputs" in workflow["136"]:
            workflow["136"]["inputs"]["filename_prefix"] = "yeepay/yeepay"
            print(f"设置SaveImage文件名前缀为: yeepay/yeepay")
        
        # 处理种子参数
        if parameters.get("seed"):
            workflow["31"]["inputs"]["seed"] = parameters["seed"]
            print(f"使用指定种子: {parameters['seed']}")
        else:
            # 生成随机种子
            seed = random.randint(1, 2**32 - 1)
            workflow["31"]["inputs"]["seed"] = seed
            print(f"使用随机种子: {seed}")
        
        print(f"工作流参数更新完成: 描述='{description[:50]}...', 步数={workflow['31']['inputs']['steps']}, CFG={workflow['31']['inputs']['cfg']}, 引导={workflow['35']['inputs']['guidance']}")
        
        return workflow
