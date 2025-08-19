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
    """工作流模板管理器，负责创建和自定义多种模型的工作流"""
    
    def __init__(self, template_path: str = None):
        """初始化工作流模板
        
        Args:
            template_path: 模板文件路径（可选，如果不提供则使用默认Flux模板）
        """
        self.template_path = template_path
        if template_path:
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    self.template = json.load(f)
            except FileNotFoundError:
                raise FileNotFoundError(f"工作流模板文件不存在: {template_path}")
            except json.JSONDecodeError:
                raise ValueError(f"工作流模板文件格式错误: {template_path}")
        else:
            # 使用默认Flux模板
            self.template = None
    
    def customize_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any], model_name: str = "flux1-dev"):
        """自定义工作流参数 - 支持多种模型
        
        Args:
            reference_image_path: 参考图像路径
            description: 图像描述
            parameters: 生成参数
            model_name: 模型名称（默认flux1-dev）
        """
        # 根据模型类型选择工作流模板
        from core.model_manager import get_model_config, ModelType
        
        model_config = get_model_config(model_name)
        if not model_config or not model_config.available:
            print(f"⚠️ 模型 {model_name} 不可用，使用默认Flux模型")
            model_config = get_model_config("flux1-dev")
        
        print(f"🎯 使用模型: {model_config.display_name}")
        
        if model_config.model_type == ModelType.FLUX:
            return self._create_flux_workflow(reference_image_path, description, parameters, model_config)
        elif model_config.model_type == ModelType.QWEN:
            return self._create_qwen_workflow(reference_image_path, description, parameters, model_config)
        else:
            print(f"❌ 不支持的模型类型: {model_config.model_type}")
            return self._create_flux_workflow(reference_image_path, description, parameters, model_config)
    
    def _create_flux_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any], model_config):
        """创建Flux工作流"""
        # 创建一个优化的Flux Kontext工作流，参考Qwen工作流的设计
        
        workflow = {
            "6": {
                "inputs": {
                    "text": description,
                    "clip": ["38", 0]  # 默认连接到DualCLIPLoader
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
                    "model": ["37", 0],  # 默认连接到UNETLoader
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
                    "unet_name": model_config.unet_file,
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
        
        print(f"✅ 创建优化工作流，包含 {len(workflow)} 个节点")
        print(f"📋 工作流节点: {list(workflow.keys())}")
        
        # 处理LoRA配置 - 参考Qwen工作流的优化设计
        loras = parameters.get("loras", [])
        if loras and len(loras) > 0:
            print(f"🎨 检测到 {len(loras)} 个LoRA配置")
            
            # 限制最多4个LoRA
            loras = loras[:4]
            
            # 检查是否可以使用Lora Loader Stack (rgthree)
            use_lora_stack = False
            try:
                # 尝试使用Lora Loader Stack，如果可用的话
                # 这里我们先使用传统的LoraLoader方式，但结构更优化
                use_lora_stack = False  # 暂时不使用，确保兼容性
            except:
                use_lora_stack = False
            
            if use_lora_stack:
                # 使用Lora Loader Stack (rgthree) - 参考Qwen工作流
                print("🎨 使用Lora Loader Stack (rgthree) 节点")
                # TODO: 实现Lora Loader Stack逻辑
            else:
                # 使用优化的传统LoraLoader方式
                print("🎨 使用优化的传统LoraLoader方式")
                
                current_model_node = "37"  # UNETLoader
                current_clip_node = "38"   # DualCLIPLoader
                
                for i, lora_config in enumerate(loras):
                    if not lora_config.get("enabled", True):
                        print(f"⏭️ 跳过禁用的LoRA {i+1}: {lora_config.get('name', 'unknown')}")
                        continue
                    
                    lora_node_id = str(50 + i)  # 50, 51, 52, 53
                    lora_name = lora_config.get("name", "")
                    strength_model = lora_config.get("strength_model", 1.0)
                    strength_clip = lora_config.get("strength_clip", 1.0)
                    trigger_word = lora_config.get("trigger_word", "")
                    
                    print(f"🎨 添加LoRA {i+1}: {lora_name} (UNET: {strength_model}, CLIP: {strength_clip})")
                    
                    # 添加LoRA节点 - 优化连接方式
                    workflow[lora_node_id] = {
                        "inputs": {
                            "model": [current_model_node, 0],
                            "clip": [current_clip_node, 0],  # DualCLIPLoader的CLIP输出是端口0
                            "lora_name": lora_name,
                            "strength_model": strength_model,
                            "strength_clip": strength_clip
                        },
                        "class_type": "LoraLoader",
                        "_meta": {"title": f"LoRA加载器{i+1}"}
                    }
                    
                    # 更新当前节点引用
                    current_model_node = lora_node_id
                    current_clip_node = lora_node_id
                    
                    # 如果有触发词，添加到描述中
                    if trigger_word and trigger_word not in description:
                        description = f"{trigger_word}, {description}"
                        print(f"🔤 添加触发词: {trigger_word}")
                
                # 更新KSampler和CLIPTextEncode的连接 - 优化端口连接
                workflow["31"]["inputs"]["model"] = [current_model_node, 0]
                workflow["6"]["inputs"]["clip"] = [current_clip_node, 1]  # LoraLoader的CLIP输出是端口1
                workflow["6"]["inputs"]["text"] = description
                
                print(f"✅ LoRA节点连接完成: UNET -> {current_model_node}, CLIP -> {current_clip_node}")
        else:
            print("ℹ️ 未检测到LoRA配置，使用默认工作流")
        
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
    
    def _create_qwen_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any], model_config):
        """创建Qwen工作流"""
        print(f"🎨 创建Qwen工作流: {model_config.display_name}")
        
        # 加载Qwen工作流模板
        if self.template_path and self.template:
            workflow = self.template.copy()
        else:
            # 使用内置的Qwen工作流模板
            workflow = self._get_qwen_template()
        
        # 更新模型文件路径
        workflow["23"]["widgets_values"][0] = model_config.unet_file  # UNETLoader
        workflow["24"]["widgets_values"][0] = model_config.clip_file  # CLIPLoader
        workflow["22"]["widgets_values"][0] = model_config.vae_file   # VAELoader
        
        # 更新描述文本
        workflow["25"]["widgets_values"][0] = description
        
        # 更新生成参数
        if parameters.get("steps"):
            workflow["20"]["widgets_values"][2] = parameters["steps"]
        
        if parameters.get("seed"):
            workflow["20"]["widgets_values"][0] = parameters["seed"]
        
        # 处理LoRA配置
        loras = parameters.get("loras", [])
        if loras and len(loras) > 0:
            print(f"🎨 检测到 {len(loras)} 个LoRA配置")
            loras = loras[:4]  # 限制最多4个LoRA
            
            # 构建LoRA配置数组
            lora_config = []
            for lora in loras:
                if lora.get("enabled", True):
                    lora_config.extend([
                        lora.get("name", ""),
                        lora.get("strength_model", 1.0)
                    ])
            
            workflow["33"]["widgets_values"] = lora_config
            print(f"✅ LoRA配置完成: {len(lora_config)//2} 个LoRA")
        
        # 更新保存路径
        workflow["28"]["widgets_values"][0] = "yeepay/yeepay"
        
        print(f"✅ Qwen工作流创建完成")
        return workflow
    
    def _get_qwen_template(self):
        """获取Qwen工作流模板"""
        # 这里返回内置的Qwen工作流模板
        # 实际使用时可以从文件加载
        return {
            # 简化的Qwen工作流模板
            "20": {
                "type": "KSampler",
                "widgets_values": [287237245922212, "randomize", 20, 3, "euler", "normal", 1]
            },
            "22": {
                "type": "VAELoader", 
                "widgets_values": ["qwen_image_vae.safetensors"]
            },
            "23": {
                "type": "UNETLoader",
                "widgets_values": ["Qwen-Image_1.0", "default"]
            },
            "24": {
                "type": "CLIPLoader",
                "widgets_values": ["qwen_2.5_vl_7b_fp8_scaled.safetensors", "qwen_image", "default"]
            },
            "25": {
                "type": "CLIPTextEncode",
                "widgets_values": ["{{description}}"]
            },
            "28": {
                "type": "SaveImage",
                "widgets_values": ["yeepay/yeepay"]
            },
            "33": {
                "type": "Lora Loader Stack (rgthree)",
                "widgets_values": []
            }
        }
