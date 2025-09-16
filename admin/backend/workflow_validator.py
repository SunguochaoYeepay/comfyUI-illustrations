#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流验证器
负责验证工作流JSON格式和节点结构，识别配置项
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    node_analysis: Optional[Dict[str, Any]] = None
    config_items: Optional[Dict[str, Any]] = None
    config_template: Optional[Dict[str, Any]] = None


@dataclass
class NodeInfo:
    """节点信息"""
    node_id: str
    class_type: str
    inputs: Dict[str, Any]
    configurable_params: List[str]
    is_key_node: bool = False
    node_category: str = ""


class WorkflowValidator:
    """工作流验证器"""
    
    def __init__(self):
        self.node_types = self._load_node_types()
        self.parameter_mappings = self._load_parameter_mappings()
        self.key_node_types = self._load_key_node_types()
    
    def validate_and_analyze_workflow(self, workflow_json: Dict[str, Any]) -> ValidationResult:
        """验证工作流并分析配置项"""
        errors = []
        warnings = []
        
        # 1. 验证JSON格式
        format_errors = self._validate_json_format(workflow_json)
        errors.extend(format_errors)
        
        if errors:
            return ValidationResult(valid=False, errors=errors, warnings=warnings)
        
        # 2. 分析节点结构
        node_analysis = self._analyze_nodes(workflow_json)
        
        # 3. 识别配置项
        config_items = self._identify_config_items(workflow_json, node_analysis)
        
        # 4. 生成配置模板
        config_template = self._generate_config_template(config_items)
        
        # 5. 生成警告
        warnings = self._generate_warnings(workflow_json, node_analysis)
        
        return ValidationResult(
            valid=True,
            errors=[],
            warnings=warnings,
            node_analysis=node_analysis,
            config_items=config_items,
            config_template=config_template
        )
    
    def _validate_json_format(self, workflow_json: Dict[str, Any]) -> List[str]:
        """验证JSON格式"""
        errors = []
        
        # 检查是否为ComfyUI工作流格式
        # ComfyUI有两种格式：
        # 1. 标准格式：{"nodes": {...}, "connections": [...]}
        # 2. 导出格式：直接是节点字典，没有connections字段
        
        nodes = None
        connections = None
        
        if "nodes" in workflow_json and "connections" in workflow_json:
            # 标准格式
            nodes = workflow_json["nodes"]
            connections = workflow_json["connections"]
        elif self._is_node_dict_format(workflow_json):
            # 导出格式：顶层直接是节点
            nodes = workflow_json
            connections = []  # 导出格式没有connections，从节点连接推断
        else:
            errors.append("不是有效的ComfyUI工作流格式")
            return errors
        
        # 检查节点格式
        if nodes is not None:
            if not isinstance(nodes, dict):
                errors.append("节点数据必须是字典类型")
            else:
                for node_id, node in nodes.items():
                    if not isinstance(node, dict):
                        errors.append(f"节点{node_id}必须是字典类型")
                        continue
                    
                    if "class_type" not in node:
                        errors.append(f"节点{node_id}缺少class_type字段")
                    
                    if "inputs" not in node:
                        errors.append(f"节点{node_id}缺少inputs字段")
                    
                    # 检查节点ID格式
                    if not self._is_valid_node_id(node_id):
                        errors.append(f"节点ID格式无效: {node_id}")
        
        return errors
    
    def _is_node_dict_format(self, workflow_json: Dict[str, Any]) -> bool:
        """检查是否为节点字典格式（ComfyUI导出格式）"""
        if not isinstance(workflow_json, dict):
            return False
        
        # 检查是否所有值都是节点格式
        for key, value in workflow_json.items():
            if not isinstance(value, dict):
                return False
            if "class_type" not in value or "inputs" not in value:
                return False
        
        return len(workflow_json) > 0
    
    def _analyze_nodes(self, workflow_json: Dict[str, Any]) -> Dict[str, Any]:
        """分析节点结构"""
        # 处理两种格式
        if "nodes" in workflow_json:
            nodes = workflow_json["nodes"]
        elif self._is_node_dict_format(workflow_json):
            nodes = workflow_json
        else:
            nodes = {}
        
        analysis = {
            "total_nodes": len(nodes),
            "node_types": {},
            "key_nodes": {},
            "configurable_nodes": [],
            "workflow_type": "unknown",
            "complexity": "medium"
        }
        
        for node_id, node in nodes.items():
            class_type = node.get("class_type", "")
            
            # 统计节点类型
            if class_type not in analysis["node_types"]:
                analysis["node_types"][class_type] = 0
            analysis["node_types"][class_type] += 1
            
            # 识别关键节点
            key_node_info = self._identify_key_node(class_type, node_id)
            if key_node_info:
                analysis["key_nodes"][key_node_info["category"]] = {
                    "node_id": node_id,
                    "class_type": class_type,
                    "info": key_node_info
                }
            
            # 识别可配置节点
            if self._is_configurable_node(class_type, node):
                configurable_params = self._get_configurable_params(node)
                analysis["configurable_nodes"].append({
                    "node_id": node_id,
                    "class_type": class_type,
                    "configurable_params": configurable_params,
                    "category": self._get_node_category(class_type)
                })
        
        # 确定工作流类型
        analysis["workflow_type"] = self._determine_workflow_type(analysis)
        
        # 确定复杂度
        analysis["complexity"] = self._determine_complexity(analysis)
        
        return analysis
    
    def _identify_config_items(self, workflow_json: Dict[str, Any], node_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """识别配置项"""
        config_items = {
            "core_config": {},
            "advanced_config": {},
            "system_config": {}
        }
        
        # 处理两种格式
        if "nodes" in workflow_json:
            nodes = workflow_json["nodes"]
        elif self._is_node_dict_format(workflow_json):
            nodes = workflow_json
        else:
            nodes = {}
        
        # 识别核心配置项
        config_items["core_config"] = self._identify_core_config(nodes, node_analysis)
        
        # 识别高级配置项
        config_items["advanced_config"] = self._identify_advanced_config(nodes, node_analysis)
        
        # 识别系统配置项
        config_items["system_config"] = self._identify_system_config(nodes, node_analysis)
        
        return config_items
    
    def _identify_core_config(self, nodes: Dict[str, Any], node_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """识别核心配置项"""
        core_config = {}
        
        # 识别提示词配置 - 遍历所有文本编码器
        text_encoders = []
        for node_id, node in nodes.items():
            if node.get("class_type") == "CLIPTextEncode":
                text_value = node.get("inputs", {}).get("text", "")
                text_encoders.append({
                    "node_id": node_id,
                    "text_value": text_value,
                    "node": node
                })
        
        # 按文本长度排序，有内容的在前
        text_encoders.sort(key=lambda x: len(x["text_value"]), reverse=True)
        
        # 第一个（最长的）作为正面提示词
        if text_encoders and text_encoders[0]["text_value"].strip():
            encoder = text_encoders[0]
            core_config["positive_prompt"] = {
                "node_id": encoder["node_id"],
                "parameter": "text",
                "current_value": encoder["text_value"],
                "is_template": "{{" in str(encoder["text_value"]),
                "node_type": encoder["node"].get("class_type", "")
            }
        
        # 第二个（较短的）作为负面提示词
        if len(text_encoders) > 1:
            encoder = text_encoders[1]
            core_config["negative_prompt"] = {
                "node_id": encoder["node_id"],
                "parameter": "text",
                "current_value": encoder["text_value"],
                "is_template": "{{" in str(encoder["text_value"]),
                "node_type": encoder["node"].get("class_type", "")
            }
        
        # 识别图像尺寸配置
        latent_processor_info = node_analysis["key_nodes"].get("latent_processor")
        if latent_processor_info:
            node_id = latent_processor_info["node_id"]
            if node_id in nodes:
                latent_node = nodes[node_id]
                if "width" in latent_node.get("inputs", {}):
                    core_config["image_width"] = {
                        "node_id": node_id,
                        "parameter": "width",
                        "current_value": latent_node["inputs"]["width"],
                        "node_type": latent_node.get("class_type", "")
                    }
                if "height" in latent_node.get("inputs", {}):
                    core_config["image_height"] = {
                        "node_id": node_id,
                        "parameter": "height",
                        "current_value": latent_node["inputs"]["height"],
                        "node_type": latent_node.get("class_type", "")
                    }
                if "batch_size" in latent_node.get("inputs", {}):
                    core_config["batch_size"] = {
                        "node_id": node_id,
                        "parameter": "batch_size",
                        "current_value": latent_node["inputs"]["batch_size"],
                        "node_type": latent_node.get("class_type", "")
                    }
        
        # 识别基础模型配置
        model_loader_info = node_analysis["key_nodes"].get("model_loader")
        if model_loader_info:
            node_id = model_loader_info["node_id"]
            if node_id in nodes:
                model_node = nodes[node_id]
                model_param = self._get_model_parameter(model_node)
                if model_param:
                    core_config["base_model"] = {
                        "node_id": node_id,
                        "parameter": model_param["name"],
                        "current_value": model_param["value"],
                        "node_type": model_node.get("class_type", ""),
                        "model_type": self._infer_model_type(model_param["value"])
                    }
                
                # 如果是UNETLoader，也识别weight_dtype参数
                if model_node.get("class_type") == "UNETLoader":
                    weight_dtype = model_node.get("inputs", {}).get("weight_dtype", "")
                    if weight_dtype:
                        core_config["weight_dtype"] = {
                            "node_id": node_id,
                            "parameter": "weight_dtype",
                            "current_value": weight_dtype,
                            "node_type": model_node.get("class_type", "")
                        }
        
        # 识别VAE配置
        vae_loader_info = node_analysis["key_nodes"].get("vae_loader")
        if vae_loader_info:
            node_id = vae_loader_info["node_id"]
            if node_id in nodes:
                vae_node = nodes[node_id]
                if "vae_name" in vae_node.get("inputs", {}):
                    core_config["vae_model"] = {
                        "node_id": node_id,
                        "parameter": "vae_name",
                        "current_value": vae_node["inputs"]["vae_name"],
                        "node_type": vae_node.get("class_type", "")
                    }
        
        # 识别CLIP配置
        clip_loader_info = node_analysis["key_nodes"].get("clip_loader")
        if clip_loader_info:
            node_id = clip_loader_info["node_id"]
            if node_id in nodes:
                clip_node = nodes[node_id]
                if "clip_name" in clip_node.get("inputs", {}):
                    core_config["clip_model"] = {
                        "node_id": node_id,
                        "parameter": "clip_name",
                        "current_value": clip_node["inputs"]["clip_name"],
                        "node_type": clip_node.get("class_type", "")
                    }
        
        return core_config
    
    def _identify_advanced_config(self, nodes: Dict[str, Any], node_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """识别高级配置项"""
        advanced_config = {}
        
        # 识别LoRA配置
        lora_loader_info = node_analysis["key_nodes"].get("lora_loader")
        if lora_loader_info:
            node_id = lora_loader_info["node_id"]
            if node_id in nodes:
                lora_node = nodes[node_id]
                advanced_config["loras"] = {
                    "node_id": node_id,
                    "class_type": lora_node.get("class_type", ""),
                    "parameters": self._extract_lora_parameters(lora_node)
                }
        
        # 识别采样参数
        sampler_info = node_analysis["key_nodes"].get("sampler")
        if sampler_info:
            node_id = sampler_info["node_id"]
            if node_id in nodes:
                sampler_node = nodes[node_id]
                advanced_config["sampling"] = {
                    "node_id": node_id,
                    "class_type": sampler_node.get("class_type", ""),
                    "parameters": self._extract_sampling_parameters(sampler_node)
                }
        
        # 识别参考图配置
        image_loader_info = node_analysis["key_nodes"].get("image_loader")
        if image_loader_info:
            node_id = image_loader_info["node_id"]
            if node_id in nodes:
                image_node = nodes[node_id]
                advanced_config["reference_images"] = {
                    "node_id": node_id,
                    "class_type": image_node.get("class_type", ""),
                    "parameters": self._extract_image_parameters(image_node)
                }
        
        # 识别模型采样算法配置
        for node_id, node in nodes.items():
            if node.get("class_type") == "ModelSamplingAuraFlow":
                advanced_config["model_sampling"] = {
                    "node_id": node_id,
                    "class_type": node.get("class_type", ""),
                    "parameters": {
                        "shift": node.get("inputs", {}).get("shift", 0)
                    }
                }
                break
        
        return advanced_config
    
    def _identify_system_config(self, nodes: Dict[str, Any], node_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """识别系统配置项"""
        system_config = {}
        
        # 识别负面提示词
        negative_prompt_info = node_analysis["key_nodes"].get("negative_prompt")
        if negative_prompt_info:
            node_id = negative_prompt_info["node_id"]
            if node_id in nodes:
                negative_node = nodes[node_id]
                if "text" in negative_node.get("inputs", {}):
                    system_config["negative_prompt"] = {
                        "node_id": node_id,
                        "parameter": "text",
                        "current_value": negative_node["inputs"]["text"],
                        "node_type": negative_node.get("class_type", "")
                    }
        
        return system_config
    
    def _generate_config_template(self, config_items: Dict[str, Any]) -> Dict[str, Any]:
        """生成配置模板"""
        template = {
            "core_config": {},
            "advanced_config": {},
            "system_config": {}
        }
        
        # 生成核心配置模板
        for key, config in config_items["core_config"].items():
            template["core_config"][key] = {
                "type": self._get_parameter_type(config),
                "required": True,
                "default_value": config.get("current_value"),
                "description": self._get_parameter_description(key),
                "node_id": config.get("node_id"),
                "parameter": config.get("parameter"),
                "node_type": config.get("node_type", "")
            }
        
        # 生成高级配置模板
        for key, config in config_items["advanced_config"].items():
            template["advanced_config"][key] = {
                "type": "object",
                "required": False,
                "default_value": config,
                "description": self._get_parameter_description(key),
                "node_id": config.get("node_id"),
                "class_type": config.get("class_type", "")
            }
        
        return template
    
    def _load_node_types(self) -> Dict[str, Any]:
        """加载节点类型定义"""
        return {
            "CLIPTextEncode": {"category": "text", "configurable": True},
            "CLIPTextEncodeAdvanced": {"category": "text", "configurable": True},
            "KSampler": {"category": "sampling", "configurable": True},
            "KSamplerAdvanced": {"category": "sampling", "configurable": True},
            "UNETLoader": {"category": "model", "configurable": True},
            "CheckpointLoader": {"category": "model", "configurable": True},
            "LoraLoader": {"category": "lora", "configurable": True},
            "LoraLoaderStack": {"category": "lora", "configurable": True},
            "Lora Loader Stack (rgthree)": {"category": "lora", "configurable": True},
            "LoadImage": {"category": "image", "configurable": True},
            "LoadImageBatch": {"category": "image", "configurable": True},
            "EmptyLatentImage": {"category": "latent", "configurable": True},
            "LatentUpscale": {"category": "latent", "configurable": True},
            "SaveImage": {"category": "output", "configurable": False},
            "PreviewImage": {"category": "output", "configurable": False}
        }
    
    def _load_parameter_mappings(self) -> Dict[str, Any]:
        """加载参数映射"""
        return {
            "positive_prompt": ["text", "prompt"],
            "negative_prompt": ["text", "negative"],
            "image_width": ["width"],
            "image_height": ["height"],
            "base_model": ["ckpt_name", "unet_name", "model_name"],
            "lora_name": ["lora_name"],
            "steps": ["steps"],
            "seed": ["seed"],
            "cfg": ["cfg", "cfg_scale"]
        }
    
    def _load_key_node_types(self) -> Dict[str, List[str]]:
        """加载关键节点类型"""
        return {
            "text_encoder": ["CLIPTextEncode", "CLIPTextEncodeAdvanced"],
            "sampler": ["KSampler", "KSamplerAdvanced"],
            "model_loader": ["UNETLoader", "CheckpointLoader"],
            "lora_loader": ["LoraLoader", "LoraLoaderStack", "LoraLoaderModelOnly", "Lora Loader Stack (rgthree)"],
            "image_loader": ["LoadImage", "LoadImageBatch"],
            "latent_processor": ["EmptyLatentImage", "LatentUpscale", "EmptySD3LatentImage"],
            "negative_prompt": ["CLIPTextEncode", "CLIPTextEncodeAdvanced"],
            "vae_loader": ["VAELoader"],
            "clip_loader": ["CLIPLoader"],
            "vae_decode": ["VAEDecode"],
            "save_image": ["SaveImage"]
        }
    
    def _is_valid_node_id(self, node_id: str) -> bool:
        """验证节点ID格式"""
        # 节点ID应该是数字字符串
        return node_id.isdigit()
    
    def _identify_key_node(self, class_type: str, node_id: str) -> Optional[Dict[str, Any]]:
        """识别关键节点"""
        for category, node_types in self.key_node_types.items():
            if class_type in node_types:
                return {
                    "category": category,
                    "class_type": class_type,
                    "node_id": node_id
                }
        return None
    
    def _is_configurable_node(self, class_type: str, node: Dict[str, Any]) -> bool:
        """判断节点是否可配置"""
        if class_type in self.node_types:
            return self.node_types[class_type].get("configurable", False)
        return False
    
    def _get_configurable_params(self, node: Dict[str, Any]) -> List[str]:
        """获取可配置参数"""
        inputs = node.get("inputs", {})
        configurable_params = []
        
        for param_name, param_value in inputs.items():
            if self._is_configurable_parameter(param_name, param_value):
                configurable_params.append(param_name)
        
        return configurable_params
    
    def _is_configurable_parameter(self, param_name: str, param_value: Any) -> bool:
        """判断参数是否可配置"""
        # 排除连接参数
        if isinstance(param_value, list) and len(param_value) == 2:
            return False
        
        # 排除固定值
        if param_name in ["seed", "steps", "cfg", "width", "height"]:
            return True
        
        # 排除文本参数（模板变量除外）
        if isinstance(param_value, str):
            return "{{" in param_value or param_name in ["text", "prompt"]
        
        return True
    
    def _get_node_category(self, class_type: str) -> str:
        """获取节点分类"""
        if class_type in self.node_types:
            return self.node_types[class_type].get("category", "unknown")
        return "unknown"
    
    def _determine_workflow_type(self, analysis: Dict[str, Any]) -> str:
        """确定工作流类型"""
        node_types = analysis["node_types"]
        
        if "KSampler" in node_types or "KSamplerAdvanced" in node_types:
            if "LoadImage" in node_types or "LoadImageBatch" in node_types:
                return "image_generation_with_reference"
            else:
                return "image_generation"
        elif "LoadImage" in node_types and "SaveImage" in node_types:
            return "image_processing"
        else:
            return "unknown"
    
    def _determine_complexity(self, analysis: Dict[str, Any]) -> str:
        """确定复杂度"""
        total_nodes = analysis["total_nodes"]
        
        if total_nodes < 10:
            return "simple"
        elif total_nodes < 20:
            return "medium"
        else:
            return "complex"
    
    def _get_model_parameter(self, model_node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取模型参数"""
        inputs = model_node.get("inputs", {})
        
        for param_name in ["ckpt_name", "unet_name", "model_name"]:
            if param_name in inputs:
                return {
                    "name": param_name,
                    "value": inputs[param_name]
                }
        
        return None
    
    def _infer_model_type(self, model_name: str) -> str:
        """推断模型类型"""
        model_name_lower = model_name.lower()
        
        if "qwen" in model_name_lower:
            return "qwen"
        elif "flux" in model_name_lower:
            return "flux"
        elif "wan" in model_name_lower:
            return "wan"
        else:
            return "unknown"
    
    def _extract_lora_parameters(self, lora_node: Dict[str, Any]) -> Dict[str, Any]:
        """提取LoRA参数"""
        inputs = lora_node.get("inputs", {})
        class_type = lora_node.get("class_type", "")
        
        if class_type == "Lora Loader Stack (rgthree)":
            # 多LoRA模式
            lora_params = {}
            for i in range(1, 5):  # lora_01 到 lora_04
                lora_name = inputs.get(f"lora_{i:02d}", "None")
                strength = inputs.get(f"strength_{i:02d}", 1.0)
                if lora_name and lora_name != "None":
                    lora_params[f"lora_{i:02d}"] = {
                        "name": lora_name,
                        "strength": strength
                    }
            return lora_params
        else:
            # 单LoRA模式
            return {
                "lora_name": inputs.get("lora_name", ""),
                "strength_model": inputs.get("strength_model", 1.0),
                "strength_clip": inputs.get("strength_clip", 1.0)
            }
    
    def _extract_sampling_parameters(self, sampler_node: Dict[str, Any]) -> Dict[str, Any]:
        """提取采样参数"""
        inputs = sampler_node.get("inputs", {})
        return {
            "steps": inputs.get("steps", 20),
            "seed": inputs.get("seed", "random"),
            "cfg": inputs.get("cfg", 7.0),
            "sampler_name": inputs.get("sampler_name", "euler"),
            "scheduler": inputs.get("scheduler", "normal")
        }
    
    def _extract_image_parameters(self, image_node: Dict[str, Any]) -> Dict[str, Any]:
        """提取图像参数"""
        inputs = image_node.get("inputs", {})
        return {
            "image": inputs.get("image", ""),
            "upload": inputs.get("upload", "")
        }
    
    def _get_parameter_type(self, config: Dict[str, Any]) -> str:
        """获取参数类型"""
        current_value = config.get("current_value")
        
        if isinstance(current_value, int):
            return "integer"
        elif isinstance(current_value, float):
            return "float"
        elif isinstance(current_value, bool):
            return "boolean"
        elif isinstance(current_value, str):
            return "string"
        else:
            return "object"
    
    def _get_parameter_description(self, key: str) -> str:
        """获取参数描述"""
        descriptions = {
            "positive_prompt": "正面提示词，描述想要生成的内容",
            "negative_prompt": "负面提示词，描述不想要的内容",
            "image_width": "生成图像的宽度",
            "image_height": "生成图像的高度",
            "base_model": "基础模型文件",
            "loras": "LoRA模型配置",
            "sampling": "采样参数配置",
            "reference_images": "参考图像配置"
        }
        return descriptions.get(key, f"{key}配置")
    
    def _generate_warnings(self, workflow_json: Dict[str, Any], node_analysis: Dict[str, Any]) -> List[str]:
        """生成警告"""
        warnings = []
        
        # 处理两种格式
        if "nodes" in workflow_json:
            nodes = workflow_json["nodes"]
            connections = workflow_json.get("connections", [])
        elif self._is_node_dict_format(workflow_json):
            nodes = workflow_json
            connections = []  # 导出格式没有connections
        else:
            nodes = {}
            connections = []
        
        # 检查是否有未连接的节点
        connected_nodes = set()
        for connection in connections:
            connected_nodes.add(connection.get("from"))
            connected_nodes.add(connection.get("to"))
        
        for node_id in nodes:
            if node_id not in connected_nodes and connections:  # 只有在有connections时才检查
                warnings.append(f"节点{node_id}未连接到工作流中")
        
        # 检查关键节点是否存在
        key_nodes = node_analysis["key_nodes"]
        if "text_encoder" not in key_nodes:
            warnings.append("未找到文本编码器节点")
        if "sampler" not in key_nodes:
            warnings.append("未找到采样器节点")
        if "model_loader" not in key_nodes:
            warnings.append("未找到模型加载器节点")
        
        # 检查UNET节点配置
        unet_warnings = self._check_unet_configurations(nodes)
        warnings.extend(unet_warnings)
        
        return warnings
    
    def _check_unet_configurations(self, nodes: Dict[str, Any]) -> List[str]:
        """检查UNET节点配置"""
        warnings = []
        
        for node_id, node in nodes.items():
            if node.get("class_type") == "UNETLoader":
                inputs = node.get("inputs", {})
                unet_name = inputs.get("unet_name", "")
                weight_dtype = inputs.get("weight_dtype", "")
                
                # 检查UNET模型名称
                if not unet_name:
                    warnings.append(f"节点{node_id} (UNETLoader): 缺少unet_name配置")
                else:
                    # 检查模型名称格式
                    if not unet_name.endswith(('.safetensors', '.ckpt', '.pt')):
                        warnings.append(f"节点{node_id} (UNETLoader): unet_name格式可能不正确: {unet_name}")
                    
                    # 检查常见的错误配置
                    if unet_name == "flux1-standard":
                        warnings.append(f"节点{node_id} (UNETLoader): 检测到错误的模型配置 'flux1-standard'，建议使用 'flux-dev.safetensors'")
                    
                    # 检查模型类型一致性
                    if "flux" in unet_name.lower() and weight_dtype not in ["fp8_e4m3fn", "fp16", "fp32"]:
                        warnings.append(f"节点{node_id} (UNETLoader): Flux模型建议使用fp8_e4m3fn精度，当前配置: {weight_dtype}")
                
                # 检查权重数据类型
                if not weight_dtype:
                    warnings.append(f"节点{node_id} (UNETLoader): 缺少weight_dtype配置")
                elif weight_dtype not in ["fp8_e4m3fn", "fp16", "fp32", "bf16"]:
                    warnings.append(f"节点{node_id} (UNETLoader): 不支持的权重数据类型: {weight_dtype}")
                
                # 检查配置组合的合理性
                if unet_name and weight_dtype:
                    if "flux" in unet_name.lower() and weight_dtype == "fp32":
                        warnings.append(f"节点{node_id} (UNETLoader): Flux模型使用fp32精度会占用大量显存，建议使用fp16或fp8_e4m3fn")
        
        return warnings
