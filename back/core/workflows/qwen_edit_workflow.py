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
        
        # 从parameters中获取任务ID
        task_id = parameters.get("task_id")
        
        return self.create_inpainting_workflow(reference_image_path, mask_path, description, parameters, task_id)
    
    def create_inpainting_workflow(self, image_path: str, mask_path: str, description: str, parameters: Dict[str, Any], task_id: str = None) -> Dict[str, Any]:
        """创建Qwen-Edit局部重绘工作流
        
        Args:
            image_path: 原始图像路径
            mask_path: 遮罩图像路径
            description: 重绘描述
            parameters: 生成参数
            task_id: 任务ID，用于文件命名
            
        Returns:
            Qwen-Edit局部重绘工作流字典
        """
        print(f"🎨 创建Qwen-Edit局部重绘工作流: {self.model_config.display_name}")
        
        # 加载工作流模板
        workflow = self._load_qwen_edit_template()
        
        # 更新图像和遮罩路径（必需）
        workflow = self._update_image_and_mask_paths(workflow, image_path, mask_path)
        
        # 更新文本描述（提示词）
        workflow = self._update_text_description(workflow, description)
        
        # 更新采样参数
        workflow = self._update_sampling_parameters(workflow, parameters)
        
        # 更新保存路径
        workflow = self._update_save_path(workflow, task_id)
        
        # 验证工作流配置
        print(f"🔍 验证工作流配置:")
        if "76" in workflow:
            print(f"   节点76 (LoadImage): {workflow['76']['inputs']['image']}")
        if "92" in workflow:
            print(f"   节点92 (LoadImageMask): {workflow['92']['inputs']['image']}")
        if "6" in workflow:
            print(f"   节点6 (正面提示词): {workflow['6']['inputs']['text'][:50]}...")
        if "7" in workflow:
            print(f"   节点7 (负面提示词): {workflow['7']['inputs']['text']}")
        if "3" in workflow:
            print(f"   节点3 (KSampler): 步数={workflow['3']['inputs']['steps']}, CFG={workflow['3']['inputs']['cfg']}")
        if "60" in workflow:
            print(f"   节点60 (SaveImage): {workflow['60']['inputs']['filename_prefix']}")
        
        print(f"✅ Qwen-Edit局部重绘工作流创建完成（全动态配置）")
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
            
            # 加载CG迷工作流模板
            workflow_file = Path(__file__).parent.parent.parent / "workflows" / "cgmi_qwen_inpainting_workflow.json"
            if workflow_file.exists():
                print(f"✅ 找到CG迷工作流模板: {workflow_file}")
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow = json.load(f)
                print(f"✅ 成功加载CG迷工作流模板")
                return workflow
            else:
                raise Exception(f"❌ CG迷工作流模板不存在: {workflow_file}")
            
        except Exception as e:
            print(f"❌ 加载本地Qwen-Edit工作流模板失败: {e}")
            raise
    
    
    def _update_image_path_only(self, workflow: Dict[str, Any], image_path: str) -> Dict[str, Any]:
        """只更新图像路径，不更新遮罩路径"""
        print(f"📸 只更新Qwen-Edit工作流的图像路径")
        
        # 检查新工作流的节点结构 (CG迷工作流)
        if "76" in workflow:
            try:
                # 只复制图像到ComfyUI的input目录
                comfyui_image_path = self._copy_to_comfyui_input(image_path, is_mask=False)
                
                # 设置LoadImage节点的图像输入 (节点76)
                workflow["76"]["inputs"]["image"] = comfyui_image_path
                
                print(f"✅ 设置图像路径: {os.path.basename(image_path)}")
                print(f"   图像路径 (节点76): {comfyui_image_path}")
                
            except Exception as e:
                print(f"❌ 设置图像路径失败: {e}")
        
        # 兼容旧工作流的节点结构
        elif "141" in workflow:
            try:
                # 只复制图像到ComfyUI的input目录
                comfyui_image_path = self._copy_to_comfyui_input(image_path)
                
                # 设置LoadImage节点的图像输入 (节点141)
                workflow["141"]["inputs"]["image"] = comfyui_image_path
                
                print(f"✅ 设置图像路径: {os.path.basename(image_path)}")
                print(f"   图像路径 (节点141): {comfyui_image_path}")
                
            except Exception as e:
                print(f"❌ 设置图像路径失败: {e}")
        
        return workflow
    
    def _update_image_and_mask_paths(self, workflow: Dict[str, Any], image_path: str, mask_path: str) -> Dict[str, Any]:
        """更新图像和遮罩路径"""
        print(f"📸 更新Qwen-Edit工作流的图像和遮罩路径")
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图像文件不存在: {image_path}")
        if not os.path.exists(mask_path):
            raise FileNotFoundError(f"遮罩文件不存在: {mask_path}")
        
        # 检查新工作流的节点结构 (CG迷工作流)
        if "76" in workflow and "92" in workflow:
            try:
                # 分别复制图像和遮罩到ComfyUI的input目录
                comfyui_image_path = self._copy_to_comfyui_input(image_path, is_mask=False)
                comfyui_mask_path = self._copy_to_comfyui_input(mask_path, is_mask=True)
                
                # 设置LoadImage节点的图像输入 (节点76)
                workflow["76"]["inputs"]["image"] = comfyui_image_path
                
                # 设置LoadImageMask节点的遮罩输入 (节点92)
                workflow["92"]["inputs"]["image"] = comfyui_mask_path
                
                print(f"✅ 设置图像和遮罩路径完成")
                print(f"   图像: {os.path.basename(image_path)} -> {comfyui_image_path}")
                print(f"   遮罩: {os.path.basename(mask_path)} -> {comfyui_mask_path}")
                
            except Exception as e:
                print(f"❌ 设置图像和遮罩路径失败: {e}")
                # 降级：只使用原始图像
                comfyui_image_path = self._copy_to_comfyui_input(image_path, is_mask=False)
                workflow["76"]["inputs"]["image"] = comfyui_image_path
                print(f"⚠️ 降级使用原始图像: {comfyui_image_path}")
        
        # 兼容旧工作流的节点结构
        elif "141" in workflow and "139" in workflow:
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
        """创建包含图像和遮罩的复合文件，模拟ComfyUI手工绘制的格式
        
        新的遮罩格式：
        - 原图作为背景
        - 要重绘的区域为透明（Alpha=0）
        - 保持原样的区域为不透明（Alpha=255）
        """
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
                    
                    # 如果遮罩是RGBA格式，直接使用
                    if mask.mode == 'RGBA':
                        print(f"✅ 遮罩已经是RGBA格式，直接使用")
                        composite = mask.copy()
                        
                        # 将原图内容复制到遮罩的RGB通道
                        if img.mode != 'RGB':
                            img_rgb = img.convert('RGB')
                        else:
                            img_rgb = img
                        
                        # 创建新的RGBA图像，使用原图的RGB和遮罩的Alpha
                        composite = Image.new('RGBA', img.size)
                        composite.paste(img_rgb, (0, 0))
                        
                        # 使用遮罩的Alpha通道
                        if mask.mode == 'RGBA':
                            composite.putalpha(mask.split()[-1])  # 使用遮罩的Alpha通道
                        else:
                            # 如果遮罩不是RGBA，转换为Alpha通道
                            if mask.mode != 'L':
                                mask = mask.convert('L')
                            composite.putalpha(mask)
                        
                    else:
                        # 传统处理方式：将遮罩转换为Alpha通道
                        if mask.mode != 'L':
                            mask = mask.convert('L')
                        
                        # 创建RGBA图像
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')
                        
                        composite = img.copy()
                        
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
                    print(f"   复合图像模式: {composite.mode}")
                    return str(composite_path)
                    
        except Exception as e:
            print(f"❌ 创建复合图像时出错: {e}")
            raise
    
    def _update_text_description(self, workflow: Dict[str, Any], description: str) -> Dict[str, Any]:
        """更新文本描述"""
        # 检查新工作流的节点结构 (CG迷工作流)
        if "6" in workflow and "7" in workflow:
            # 更新正面提示词 (节点6)
            workflow["6"]["inputs"]["text"] = description
            print(f"✅ 更新重绘描述文本 (节点6): {description[:50]}...")
            
            # 更新负面提示词 (节点7)
            workflow["7"]["inputs"]["text"] = ""  # 负面提示词，通常为空
            print(f"✅ 更新负面提示词 (节点7)")
        
        # 兼容旧工作流的节点结构
        elif "106" in workflow and "77" in workflow:
            # 更新正面提示词 (节点106)
            workflow["106"]["inputs"]["text"] = description
            print(f"✅ 更新重绘描述文本 (节点106): {description[:50]}...")
            
            # 更新负面提示词 (节点77)
            workflow["77"]["inputs"]["prompt"] = ""  # 负面提示词，通常为空
            print(f"✅ 更新负面提示词 (节点77)")
        
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
        
        # 更新LoRA强度 (节点70 - 新工作流)
        if "70" in workflow and parameters.get("lora_strength"):
            workflow["70"]["inputs"]["strength_model"] = parameters["lora_strength"]
            print(f"✅ 更新LoRA强度 (节点70): {parameters['lora_strength']}")
        
        # 兼容旧工作流的LoRA强度 (节点129)
        elif "129" in workflow and parameters.get("lora_strength"):
            workflow["129"]["inputs"]["strength_01"] = parameters["lora_strength"]
            print(f"✅ 更新LoRA强度 (节点129): {parameters['lora_strength']}")
        
        return workflow
    
    
    
    def _update_save_path(self, workflow: Dict[str, Any], task_id: str = None) -> Dict[str, Any]:
        """更新保存路径"""
        print(f"🔧 开始更新保存路径，任务ID: {task_id}")
        
        # 查找保存节点并更新路径
        save_image_found = False
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "SaveImage":
                save_image_found = True
                print(f"📁 找到SaveImage节点: {node_id}")
                print(f"📋 当前filename_prefix: {node_data.get('inputs', {}).get('filename_prefix', '未设置')}")
                
                if task_id:
                    # 使用任务ID作为文件名前缀，确保唯一性
                    filename_prefix = f"qwen-edit-{task_id[:8]}"  # 使用任务ID的前8位
                    node_data["inputs"]["filename_prefix"] = filename_prefix
                    print(f"✅ 更新保存路径为: {filename_prefix}")
                else:
                    # 如果没有任务ID，使用默认前缀
                    node_data["inputs"]["filename_prefix"] = "pl-qwen-edit"
                    print(f"✅ 更新保存路径为: pl-qwen-edit")
                break
        
        if not save_image_found:
            print(f"⚠️ 未找到SaveImage节点")
        
        return workflow
    
    
    def _copy_to_comfyui_input(self, image_path: str, is_mask: bool = False) -> str:
        """将图像文件复制到ComfyUI的input目录
        
        Args:
            image_path: 原始图像路径
            is_mask: 是否为遮罩文件
            
        Returns:
            ComfyUI兼容的文件名格式
        """
        import shutil
        import uuid
        from config.settings import COMFYUI_INPUT_DIR
        
        # 获取原始文件名和扩展名
        original_filename = os.path.basename(image_path)
        name, ext = os.path.splitext(original_filename)
        
        # 使用固定的文件名，避免缓存问题
        unique_filename = f"{name}_latest{ext}"
        
        if is_mask:
            # 遮罩文件复制到clipspace目录
            clipspace_dir = COMFYUI_INPUT_DIR / "clipspace"
            clipspace_dir.mkdir(exist_ok=True)
            dest_path = clipspace_dir / unique_filename
            comfyui_path = f"clipspace/{unique_filename}"
        else:
            # 图像文件复制到input根目录
            dest_path = COMFYUI_INPUT_DIR / unique_filename
            comfyui_path = unique_filename
        
        try:
            # 复制文件到ComfyUI的input目录
            shutil.copy2(image_path, dest_path)
            print(f"✅ 文件复制: {os.path.basename(image_path)} -> {comfyui_path}")
            
            # 返回ComfyUI期望的格式
            return comfyui_path
        except Exception as e:
            print(f"❌ 文件复制失败: {e}")
            # 如果复制失败，返回文件名（假设文件已经在正确位置）
            return comfyui_path
    
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
    
    def _validate_workflow_json(self, workflow: Dict[str, Any]) -> None:
        """验证工作流JSON的完整性"""
        try:
            print(f"🔍 验证工作流JSON完整性...")
            
            # 检查关键节点是否存在
            required_nodes = ["3", "6", "7", "8", "37", "38", "39", "60", "66", "70", "71", "72", "74", "76", "80", "92"]
            missing_nodes = []
            
            for node_id in required_nodes:
                if node_id not in workflow:
                    missing_nodes.append(node_id)
            
            if missing_nodes:
                print(f"❌ 工作流缺少关键节点: {missing_nodes}")
                raise Exception(f"工作流缺少关键节点: {missing_nodes}")
            
            # 检查关键节点的输入
            if "76" in workflow:
                image_input = workflow["76"].get("inputs", {}).get("image")
                if not image_input:
                    print(f"❌ 节点76缺少图像输入")
                    raise Exception("节点76缺少图像输入")
                print(f"✅ 节点76图像输入: {image_input}")
            
            if "92" in workflow:
                mask_input = workflow["92"].get("inputs", {}).get("image")
                if not mask_input:
                    print(f"❌ 节点92缺少遮罩输入")
                    raise Exception("节点92缺少遮罩输入")
                print(f"✅ 节点92遮罩输入: {mask_input}")
            
            if "6" in workflow:
                text_input = workflow["6"].get("inputs", {}).get("text")
                print(f"✅ 节点6文本输入: {text_input}")
            
            print(f"✅ 工作流JSON验证通过")
            
        except Exception as e:
            print(f"❌ 工作流JSON验证失败: {e}")
            raise
