#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen-Edit局部重绘工作流实现
专门处理Qwen-Edit模型的局部重绘功能
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_workflow import BaseWorkflow
from config.settings import ADMIN_BACKEND_URL


class QwenEditWorkflow(BaseWorkflow):
    """Qwen-Edit局部重绘工作流创建器"""
    
    def create_workflow(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """实现抽象基类的create_workflow方法
        
        Args:
            reference_image_path: 参考图像路径
            description: 重绘描述
            parameters: 生成参数，包含mask_path等
            
        Returns:
            Qwen-Edit局部重绘工作流字典
        """
        # 从parameters中获取遮罩路径
        mask_path = parameters.get("mask_path")
        if not mask_path:
            raise ValueError("局部重绘需要提供mask_path参数")
        
        return self.create_inpainting_workflow(reference_image_path, mask_path, description, parameters)
    
    def create_inpainting_workflow(self, image_path: str, mask_path: str, description: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """创建Qwen-Edit局部重绘工作流
        
        Args:
            image_path: 原始图像路径
            mask_path: 遮罩图像路径
            description: 重绘描述
            parameters: 生成参数
            
        Returns:
            Qwen-Edit局部重绘工作流字典
        """
        print(f"🎨 创建Qwen-Edit局部重绘工作流: {self.model_config.display_name}")
        
        # 验证参数
        validated_params = self._validate_parameters(parameters)
        
        # 加载工作流模板
        workflow = self._load_qwen_edit_template()
        
        # 更新图像和遮罩路径
        workflow = self._update_image_and_mask_paths(workflow, image_path, mask_path)
        
        # 更新文本描述
        workflow = self._update_text_description(workflow, description)
        
        print(f"✅ Qwen-Edit局部重绘工作流创建完成")
        return workflow
    
    def _load_qwen_edit_template(self) -> Dict[str, Any]:
        """通过admin API加载Qwen-Edit工作流模板"""
        try:
            import requests
            import json
            
            print(f"🔍 通过admin API加载Qwen-Edit工作流模板")
            
            # 通过admin API获取工作流配置
            admin_url = f"{ADMIN_BACKEND_URL}/api/admin/config-sync/workflows"
            response = requests.get(admin_url, timeout=5)
            
            if response.status_code != 200:
                raise Exception(f"admin API调用失败: {response.status_code}")
            
            data = response.json()
            workflows = data.get("workflows", [])
            
            # 查找Qwen-Edit工作流
            for workflow_data in workflows:
                if workflow_data.get("code") == "qwen_edit_inpainting":
                    workflow_json = workflow_data.get("workflow_json")
                    if workflow_json:
                        workflow = json.loads(workflow_json) if isinstance(workflow_json, str) else workflow_json
                        print(f"✅ 通过admin API加载Qwen-Edit工作流模板")
                        return workflow
            
            # 如果admin API中没有找到，使用本地模板
            print(f"⚠️ admin API中未找到Qwen-Edit工作流，使用本地模板")
            return self._load_local_template()
            
        except Exception as e:
            print(f"❌ 通过admin API加载Qwen-Edit工作流失败: {e}")
            print(f"🔄 尝试使用本地模板")
            return self._load_local_template()
    
    def _load_local_template(self) -> Dict[str, Any]:
        """加载本地Qwen-Edit工作流模板"""
        try:
            print(f"📁 加载本地Qwen-Edit工作流模板")
            
            # 完全使用用户提供的准确JSON工作流
            workflow = {
                "3": {
                    "inputs": {
                        "seed": 117645373250617,
                        "steps": 8,
                        "cfg": 2.5,
                        "sampler_name": "euler",
                        "scheduler": "simple",
                        "denoise": 1,
                        "model": ["75", 0],
                        "positive": ["76", 0],
                        "negative": ["77", 0],
                        "latent_image": ["88", 0]
                    },
                    "class_type": "KSampler",
                    "_meta": {
                        "title": "K采样器"
                    }
                },
                "8": {
                    "inputs": {
                        "samples": ["3", 0],
                        "vae": ["39", 0]
                    },
                    "class_type": "VAEDecode",
                    "_meta": {
                        "title": "VAE解码"
                    }
                },
                "37": {
                    "inputs": {
                        "unet_name": "qwen_image_edit_fp8_e4m3fn.safetensors",
                        "weight_dtype": "default"
                    },
                    "class_type": "UNETLoader",
                    "_meta": {
                        "title": "UNET加载器"
                    }
                },
                "38": {
                    "inputs": {
                        "clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
                        "type": "qwen_image",
                        "device": "default"
                    },
                    "class_type": "CLIPLoader",
                    "_meta": {
                        "title": "CLIP加载器"
                    }
                },
                "39": {
                    "inputs": {
                        "vae_name": "qwen_image_vae.safetensors"
                    },
                    "class_type": "VAELoader",
                    "_meta": {
                        "title": "VAE加载器"
                    }
                },
                "60": {
                    "inputs": {
                        "filename_prefix": "pl-qwen-edit",
                        "images": ["8", 0]
                    },
                    "class_type": "SaveImage",
                    "_meta": {
                        "title": "保存图像"
                    }
                },
                "66": {
                    "inputs": {
                        "shift": 3,
                        "model": ["129", 0]
                    },
                    "class_type": "ModelSamplingAuraFlow",
                    "_meta": {
                        "title": "模型采样算法AuraFlow"
                    }
                },
                "75": {
                    "inputs": {
                        "strength": 1,
                        "model": ["66", 0]
                    },
                    "class_type": "CFGNorm",
                    "_meta": {
                        "title": "CFGNorm"
                    }
                },
                "76": {
                    "inputs": {
                        "prompt": ["106", 0],
                        "clip": ["38", 0],
                        "vae": ["39", 0],
                        "image": ["109", 0]
                    },
                    "class_type": "TextEncodeQwenImageEdit",
                    "_meta": {
                        "title": "TextEncodeQwenImageEdit"
                    }
                },
                "77": {
                    "inputs": {
                        "prompt": "",
                        "clip": ["38", 0],
                        "vae": ["39", 0],
                        "image": ["109", 0]
                    },
                    "class_type": "TextEncodeQwenImageEdit",
                    "_meta": {
                        "title": "TextEncodeQwenImageEdit"
                    }
                },
                "88": {
                    "inputs": {
                        "pixels": ["126", 0],
                        "vae": ["39", 0]
                    },
                    "class_type": "VAEEncode",
                    "_meta": {
                        "title": "VAE编码"
                    }
                },
                "106": {
                    "inputs": {
                        "text": "换成毛毛虫"
                    },
                    "class_type": "Text Multiline",
                    "_meta": {
                        "title": "多行文本"
                    }
                },
                "109": {
                    "inputs": {
                        "size": 1024,
                        "mode": True,
                        "images": ["122", 0]
                    },
                    "class_type": "ImageScaleDownToSize",
                    "_meta": {
                        "title": "Scale Down To Size"
                    }
                },
                "139": {
                    "inputs": {
                        "image": "clipspace/clipspace-painted-masked-14995060.png [input]",
                        "channel": "alpha"
                    },
                    "class_type": "LoadImageMask",
                    "_meta": {
                        "title": "加载图像遮罩"
                    }
                },
                "141": {
                    "inputs": {
                        "image": "clipspace/clipspace-painted-masked-15089264.png [input]"
                    },
                    "class_type": "LoadImage",
                    "_meta": {
                        "title": "加载图像"
                    }
                },
                "122": {
                    "inputs": {
                        "mask_opacity": 1,
                        "mask_color": "0,255,0",
                        "pass_through": True,
                        "image": ["141", 0],
                        "mask": ["139", 0]
                    },
                    "class_type": "ImageAndMaskPreview",
                    "_meta": {
                        "title": "图像与遮罩预览"
                    }
                },
                "126": {
                    "inputs": {
                        "upscale_method": "nearest-exact",
                        "width": 1024,
                        "height": 1024,
                        "crop": "center",
                        "image": ["109", 0]
                    },
                    "class_type": "ImageScale",
                    "_meta": {
                        "title": "图像缩放"
                    }
                },
                "129": {
                    "inputs": {
                        "lora_01": "Qwen-Image-Lightning-8steps-V1.0.safetensors",
                        "strength_01": 1,
                        "lora_02": "None",
                        "strength_02": 1,
                        "lora_03": "None",
                        "strength_03": 1,
                        "lora_04": "None",
                        "strength_04": 1,
                        "model": ["37", 0],
                        "clip": ["38", 0]
                    },
                    "class_type": "Lora Loader Stack (rgthree)",
                    "_meta": {
                        "title": "LoRA堆加载器"
                    }
                },
                "130": {
                    "inputs": {
                        "images": ["122", 0]
                    },
                    "class_type": "PreviewImage",
                    "_meta": {
                        "title": "预览图像"
                    }
                }
            }
            
            print(f"✅ 本地Qwen-Edit工作流模板加载完成")
            return workflow
            
        except Exception as e:
            print(f"❌ 加载本地Qwen-Edit工作流模板失败: {e}")
            raise
    
    def _update_model_config(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新模型配置"""
        # 更新UNET模型 (节点37) - 只使用文件名，不包含路径
        if "37" in workflow:
            unet_filename = os.path.basename(self.model_config.unet_file)
            workflow["37"]["inputs"]["unet_name"] = unet_filename
            print(f"✅ 更新UNETLoader: {unet_filename}")
        
        # 更新CLIP模型 (节点38) - 只使用文件名，不包含路径
        if "38" in workflow:
            clip_filename = os.path.basename(self.model_config.clip_file)
            workflow["38"]["inputs"]["clip_name"] = clip_filename
            print(f"✅ 更新CLIPLoader: {clip_filename}")
        
        # 更新VAE模型 (节点39) - 只使用文件名，不包含路径
        if "39" in workflow:
            vae_filename = os.path.basename(self.model_config.vae_file)
            workflow["39"]["inputs"]["vae_name"] = vae_filename
            print(f"✅ 更新VAELoader: {vae_filename}")
        
        return workflow
    
    def _update_image_and_mask_paths(self, workflow: Dict[str, Any], image_path: str, mask_path: str) -> Dict[str, Any]:
        """更新图像和遮罩路径"""
        print(f"📸 更新Qwen-Edit工作流的图像和遮罩路径")
        
        # ComfyUI的正确方式：分别传递图像和遮罩文件
        if "141" in workflow and "139" in workflow:
            try:
                # 分别复制图像和遮罩到ComfyUI的input目录
                comfyui_image_path = self._copy_to_comfyui_input(image_path)
                comfyui_mask_path = self._copy_to_comfyui_input(mask_path)
                
                # 设置LoadImage节点的图像输入 (节点141)
                workflow["141"]["inputs"]["image"] = comfyui_image_path
                
                # 设置LoadImageMask节点的遮罩输入 (节点139)
                workflow["139"]["inputs"]["image"] = comfyui_mask_path
                
                print(f"✅ 分别设置图像和遮罩: {os.path.basename(image_path)} + {os.path.basename(mask_path)}")
                print(f"   图像路径 (节点141): {comfyui_image_path}")
                print(f"   遮罩路径 (节点139): {comfyui_mask_path}")
                
            except Exception as e:
                print(f"❌ 设置图像和遮罩路径失败: {e}")
                # 降级：只使用原始图像
                comfyui_image_path = self._copy_to_comfyui_input(image_path)
                workflow["141"]["inputs"]["image"] = comfyui_image_path
                print(f"⚠️ 降级使用原始图像: {comfyui_image_path}")
        
        return workflow
    
    def _create_composite_image(self, image_path: str, mask_path: str) -> str:
        """创建包含图像和遮罩的复合文件，模拟ComfyUI手工绘制的格式"""
        try:
            from PIL import Image
            import os
            from pathlib import Path
            
            # 读取原始图像和遮罩
            with Image.open(image_path) as img:
                with Image.open(mask_path) as mask:
                    # 确保图像和遮罩尺寸一致
                    if img.size != mask.size:
                        mask = mask.resize(img.size, Image.Resampling.LANCZOS)
                        print(f"⚠️ 遮罩尺寸已调整: {mask.size}")
                    
                    # 确保遮罩是单通道的
                    if mask.mode != 'L':
                        mask = mask.convert('L')
                    
                    # 创建复合图像：将遮罩作为Alpha通道
                    # 白色区域（要重绘）= 透明，黑色区域（保持原样）= 不透明
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # 创建新的RGBA图像
                    composite = Image.new('RGBA', img.size, (0, 0, 0, 0))
                    
                    # 将原始图像复制到复合图像
                    composite.paste(img, (0, 0))
                    
                    # 将遮罩作为Alpha通道
                    # 白色区域（要重绘）= 透明（Alpha=0）
                    # 黑色区域（保持原样）= 不透明（Alpha=255）
                    mask_data = mask.getdata()
                    composite_data = []
                    
                    for i, pixel in enumerate(mask_data):
                        # 获取原始图像的RGBA值
                        r, g, b, a = img.getdata()[i]
                        
                        # 根据遮罩设置Alpha值
                        if pixel > 128:  # 白色区域（要重绘）
                            alpha = 0  # 完全透明
                        else:  # 黑色区域（保持原样）
                            alpha = 255  # 完全不透明
                        
                        composite_data.append((r, g, b, alpha))
                    
                    composite.putdata(composite_data)
                    
                    # 保存复合图像
                    composite_filename = f"qwen_edit_{Path(image_path).stem}.png"
                    composite_path = Path(image_path).parent / composite_filename
                    composite.save(composite_path, 'PNG')
                    
                    print(f"✅ 复合图像创建成功: {composite_path}")
                    print(f"   图像尺寸: {img.size}, 遮罩尺寸: {mask.size}")
                    return str(composite_path)
                    
        except Exception as e:
            print(f"❌ 创建复合图像时出错: {e}")
            raise
    
    def _update_text_description(self, workflow: Dict[str, Any], description: str) -> Dict[str, Any]:
        """更新文本描述"""
        # 更新正面提示词 (节点106)
        if "106" in workflow:
            workflow["106"]["inputs"]["text"] = description
            print(f"✅ 更新重绘描述文本: {description[:50]}...")
        
        # 更新负面提示词 (节点77)
        if "77" in workflow:
            workflow["77"]["inputs"]["prompt"] = ""  # 负面提示词，通常为空
            print(f"✅ 更新负面提示词")
        
        return workflow
    
    def _update_sampling_parameters(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新采样参数"""
        if "3" in workflow:
            if parameters.get("steps"):
                workflow["3"]["inputs"]["steps"] = parameters["steps"]
            if parameters.get("cfg"):
                workflow["3"]["inputs"]["cfg"] = parameters["cfg"]
            if parameters.get("denoise"):
                workflow["3"]["inputs"]["denoise"] = parameters["denoise"]
            if parameters.get("seed"):
                # 如果种子值为-1，生成随机种子；否则使用提供的种子值
                if parameters["seed"] == -1:
                    import random
                    seed_value = random.randint(1, 2**31 - 1)
                else:
                    seed_value = max(0, parameters["seed"])
                workflow["3"]["inputs"]["seed"] = seed_value
            print(f"✅ 更新KSampler参数: 步数={parameters.get('steps', 8)}, CFG={parameters.get('cfg', 2.5)}, 去噪={parameters.get('denoise', 1.0)}, 种子={workflow['3']['inputs']['seed']}")
        
        # 更新LoRA强度 (节点129)
        if "129" in workflow and parameters.get("lora_strength"):
            workflow["129"]["inputs"]["strength_01"] = parameters["lora_strength"]
            print(f"✅ 更新LoRA强度: {parameters['lora_strength']}")
        
        return workflow
    
    def _update_image_dimensions(self, workflow: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """更新图像尺寸"""
        # 从参数中获取尺寸
        target_size = parameters.get("target_size", 1024)
        
        # 更新节点109 (ImageScaleDownToSize)
        if "109" in workflow:
            workflow["109"]["inputs"]["size"] = target_size
            print(f"✅ 更新图像缩放尺寸: {target_size}")
        
        # 更新节点126 (ImageScale)
        if "126" in workflow:
            workflow["126"]["inputs"]["width"] = target_size
            workflow["126"]["inputs"]["height"] = target_size
            print(f"✅ 更新最终图像尺寸: {target_size}x{target_size}")
        
        return workflow
    
    def _update_save_path(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """更新保存路径"""
        # 查找保存节点并更新路径
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "SaveImage":
                node_data["inputs"]["filename_prefix"] = "pl-qwen-edit"
                print(f"✅ 更新保存路径: pl-qwen-edit")
                break
        
        return workflow
    
    def _update_lora_config(self, workflow: Dict[str, Any], loras: list) -> Dict[str, Any]:
        """更新LoRA配置"""
        # 查找LoRA节点
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "LoraLoader":
                processed_loras = self._process_loras(loras)
                
                if not processed_loras:
                    print("ℹ️ 未检测到LoRA配置，使用默认设置")
                    return workflow
                
                print(f"🎨 检测到 {len(processed_loras)} 个LoRA配置")
                
                # 设置LoRA配置
                if len(processed_loras) > 0:
                    node_data["inputs"]["lora_name"] = processed_loras[0]["name"]
                    node_data["inputs"]["strength_model"] = processed_loras[0]["strength_model"]
                    node_data["inputs"]["strength_clip"] = processed_loras[0]["strength_clip"]
                    print(f"✅ 设置LoRA: {processed_loras[0]['name']} (强度: {processed_loras[0]['strength_model']})")
                
                break
        
        return workflow
    
    def _copy_to_comfyui_input(self, image_path: str) -> str:
        """将图像文件复制到ComfyUI的input目录
        
        Args:
            image_path: 原始图像路径
            
        Returns:
            ComfyUI兼容的文件名格式
        """
        import shutil
        from config.settings import COMFYUI_INPUT_DIR
        
        # 获取文件名（不包含路径）
        filename = os.path.basename(image_path)
        
        # 目标路径
        dest_path = COMFYUI_INPUT_DIR / filename
        
        try:
            # 复制文件到ComfyUI的input目录
            shutil.copy2(image_path, dest_path)
            print(f"✅ 文件复制成功: {image_path} -> {dest_path}")
            
            # 返回ComfyUI期望的格式：filename [input]
            return f"{filename} [input]"
        except Exception as e:
            print(f"❌ 文件复制失败: {e}")
            # 如果复制失败，返回文件名（假设文件已经在正确位置）
            return f"{filename} [input]"
    
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
