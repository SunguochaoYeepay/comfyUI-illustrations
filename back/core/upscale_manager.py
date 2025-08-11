#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像高清放大管理器
基于ComfyUI工作流实现图像放大功能
"""

import json
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from core.comfyui_client import ComfyUIClient
from core.workflow_template import WorkflowTemplate
from config.settings import COMFYUI_INPUT_DIR


class UpscaleManager:
    """图像高清放大管理器"""
    
    def __init__(self, comfyui_client: ComfyUIClient, output_dir: Path, db_manager=None):
        """初始化放大管理器
        
        Args:
            comfyui_client: ComfyUI客户端实例
            output_dir: 输出目录
            db_manager: 数据库管理器实例
        """
        self.comfyui_client = comfyui_client
        self.output_dir = output_dir
        self.db_manager = db_manager
        # 使用UltimateSDUpscale工作流
        self.workflow_template = WorkflowTemplate("flux_upscale_workflow.json")
        # 存储任务信息的内存字典 {task_id: {"prompt_id": str, "status": str}}
        self.tasks = {}
    
    async def upscale_image(
        self, 
        image_path: str, 
        scale_factor: int = 2,
        algorithm: str = "realesrgan"
    ) -> Dict[str, Any]:
        """放大单张图像
        
        Args:
            image_path: 输入图像路径
            scale_factor: 放大倍数 (2, 3, 4)
            algorithm: 放大算法 (realesrgan, swinir, lanczos)
            
        Returns:
            包含任务ID和状态的字典
        """
        try:
            # 验证输入图像
            input_path = Path(image_path)
            if not input_path.exists():
                raise FileNotFoundError(f"输入图像不存在: {image_path}")
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 准备输出目录
            task_output_dir = self.output_dir / task_id
            task_output_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查环境，在Docker环境中直接使用本地文件
            from config.settings import ENVIRONMENT
            
            if ENVIRONMENT == "production":
                # Docker环境：直接使用本地文件路径
                task_image_path = input_path
                print(f"🐳 Docker环境：直接使用本地文件路径: {task_image_path}")
            else:
                # 本地环境：复制到ComfyUI输入目录
                comfyui_input_path = COMFYUI_INPUT_DIR / input_path.name
                print(f"📁 复制图片到ComfyUI输入目录: {input_path} -> {comfyui_input_path}")
                shutil.copy2(input_path, comfyui_input_path)
                
                # 验证复制是否成功
                if not comfyui_input_path.exists():
                    raise FileNotFoundError(f"复制到ComfyUI输入目录失败: {comfyui_input_path}")
                print(f"✅ 图片复制成功，大小: {comfyui_input_path.stat().st_size} 字节")
                
                # 也复制到任务目录作为备份
                task_image_path = task_output_dir / input_path.name
                print(f"📁 复制图片到任务目录: {input_path} -> {task_image_path}")
                shutil.copy2(input_path, task_image_path)
                
                # 验证任务目录复制是否成功
                if not task_image_path.exists():
                    raise FileNotFoundError(f"复制到任务目录失败: {task_image_path}")
                print(f"✅ 任务目录复制成功，大小: {task_image_path.stat().st_size} 字节")
            
            # 自定义工作流
            workflow = self._customize_upscale_workflow(
                str(task_image_path), 
                scale_factor, 
                algorithm
            )
            
            # 提交到ComfyUI
            prompt_id = await self.comfyui_client.submit_workflow(workflow)
            
            # 存储任务信息到内存
            self.tasks[task_id] = {
                "prompt_id": prompt_id,
                "status": "processing",
                "input_path": str(task_image_path),
                "scale_factor": scale_factor,
                "algorithm": algorithm
            }
            
            # 如果有数据库管理器，保存到数据库
            if self.db_manager:
                description = f"图像放大 - {scale_factor}倍 ({algorithm})"
                parameters = {
                    "scale_factor": scale_factor,
                    "algorithm": algorithm,
                    "input_image": str(task_image_path)
                }
                
                # 放大任务不需要参考图片
                self.db_manager.create_task(
                    task_id=task_id,
                    description=description,
                    reference_image_path=None,  # 放大任务不需要参考图片
                    parameters=parameters,
                    task_type="upscale"
                )
            
            return {
                "task_id": task_id,
                "prompt_id": prompt_id,
                "status": "processing",
                "input_path": str(task_image_path),
                "scale_factor": scale_factor,
                "algorithm": algorithm
            }
            
        except Exception as e:
            print(f"❌ 放大任务创建失败: {str(e)}")
            import traceback
            print(f"❌ 详细错误信息: {traceback.format_exc()}")
            raise Exception(f"放大任务创建失败: {str(e)}")
    
    def _customize_upscale_workflow(
        self, 
        image_path: str, 
        scale_factor: int, 
        algorithm: str
    ) -> Dict[str, Any]:
        """自定义UltimateSDUpscale工作流
        
        Args:
            image_path: 图像路径
            scale_factor: 放大倍数
            algorithm: 放大算法（兼容性保留）
            
        Returns:
            自定义后的工作流字典
        """
        # 加载工作流模板
        workflow = self.workflow_template.template.copy()
        
        # 检查环境，在Docker环境中使用完整路径
        from config.settings import ENVIRONMENT
        
        if ENVIRONMENT == "production":
            # Docker环境：复制图像到ComfyUI输入目录，然后使用文件名
            from config.settings import COMFYUI_INPUT_DIR
            import shutil
            
            # 复制图像到ComfyUI输入目录
            input_image_path = COMFYUI_INPUT_DIR / Path(image_path).name
            print(f"🐳 Docker环境：复制图像到ComfyUI输入目录: {image_path} -> {input_image_path}")
            shutil.copy2(image_path, input_image_path)
            
            # 使用文件名，ComfyUI会在其输入目录中查找
            workflow["14"]["inputs"]["image"] = Path(image_path).name
            print(f"🐳 Docker环境：使用图像文件名: {Path(image_path).name}")
        else:
            # 本地环境：使用文件名，ComfyUI会在其输入目录中查找
            workflow["14"]["inputs"]["image"] = Path(image_path).name
            print(f"📁 本地环境：使用图像文件名: {Path(image_path).name}")
        
        # 根据放大倍数调整参数
        if scale_factor == 2:
            # 2倍放大 - 快速模式
            workflow["10"]["inputs"]["upscale_by"] = 2
            workflow["10"]["inputs"]["steps"] = 12
            workflow["10"]["inputs"]["cfg"] = 2.5
            workflow["10"]["inputs"]["denoise"] = 0.12
        elif scale_factor == 3:
            # 3倍放大 - 平衡模式
            workflow["10"]["inputs"]["upscale_by"] = 3
            workflow["10"]["inputs"]["steps"] = 15
            workflow["10"]["inputs"]["cfg"] = 3.0
            workflow["10"]["inputs"]["denoise"] = 0.15
        elif scale_factor == 4:
            # 4倍放大 - 高质量模式
            workflow["10"]["inputs"]["upscale_by"] = 4
            workflow["10"]["inputs"]["steps"] = 20
            workflow["10"]["inputs"]["cfg"] = 3.5
            workflow["10"]["inputs"]["denoise"] = 0.18
        else:
            # 默认2倍放大
            workflow["10"]["inputs"]["upscale_by"] = 2
            workflow["10"]["inputs"]["steps"] = 12
            workflow["10"]["inputs"]["cfg"] = 2.5
            workflow["10"]["inputs"]["denoise"] = 0.12
        
        # 更新输出文件名
        workflow["9"]["inputs"]["filename_prefix"] = f"ultimate_upscaled_{scale_factor}x"
        
        return workflow
    
    async def get_upscale_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取放大结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            放大结果信息，如果未完成则返回None
        """
        task_output_dir = self.output_dir / task_id
        
        if not task_output_dir.exists():
            return None
        
        # 首先检查ComfyUI的输出目录
        from config.settings import COMFYUI_MAIN_OUTPUT_DIR
        comfyui_output_dir = COMFYUI_MAIN_OUTPUT_DIR
        
        print(f"🔍 检查ComfyUI输出目录: {comfyui_output_dir}")
        
        # 获取任务信息以确定放大倍数
        scale_factor = 2  # 默认值
        if task_id in self.tasks:
            scale_factor = self.tasks[task_id].get("scale_factor", 2)
        elif self.db_manager:
            # 从数据库中获取任务信息
            task_info = self.db_manager.get_task(task_id)
            if task_info and task_info.get('parameters'):
                import json
                try:
                    parameters = json.loads(task_info['parameters'])
                    scale_factor = parameters.get('scale_factor', 2)
                except (json.JSONDecodeError, KeyError):
                    scale_factor = 2
        
        # 先检查是否有对应的prompt_id，通过ComfyUI历史API获取真正的输出文件
        latest_file = None
        
        if task_id in self.tasks:
            task_info = self.tasks[task_id]
            prompt_id = task_info.get("prompt_id")
            
            if prompt_id:
                try:
                    print(f"🔍 通过prompt_id查询ComfyUI历史: {prompt_id}")
                    comfyui_history = await self.comfyui_client.get_task_status(prompt_id)
                    
                    # 从ComfyUI历史中提取输出文件
                    if prompt_id in comfyui_history and comfyui_history[prompt_id].get("status", {}).get("completed", False):
                        outputs = comfyui_history[prompt_id].get("outputs", {})
                        print(f"📋 ComfyUI任务输出: {outputs}")
                        
                        # 查找图片输出节点的结果
                        found_file = False
                        for node_id, node_output in outputs.items():
                            if "images" in node_output:
                                for image_info in node_output["images"]:
                                    filename = image_info.get("filename")
                                    if filename and "upscaled" in filename.lower():
                                        # 找到放大后的文件
                                        latest_file = comfyui_output_dir / filename
                                        print(f"✅ 通过prompt_id找到放大文件: {latest_file}")
                                        
                                        if latest_file.exists():
                                            found_file = True
                                            break
                            if found_file:
                                break
                        
                        if not found_file:
                            print(f"❌ 在prompt_id {prompt_id} 的输出中没有找到放大文件")
                            return None
                            
                    else:
                        print(f"⏳ prompt_id {prompt_id} 的任务还没有完成")
                        return None
                        
                except Exception as e:
                    print(f"⚠️ 查询ComfyUI历史失败: {e}")
                    # 如果ComfyUI历史查询失败，回退到文件系统查找（但更加谨慎）
                    print(f"🔄 回退到文件系统查找...")
                    
                    # 查找最近几分钟内创建的放大文件，避免获取太旧的文件
                    import time
                    current_time = time.time()
                    recent_threshold = current_time - 300  # 5分钟内
                    
                    upscaled_files = list(comfyui_output_dir.glob(f"ultimate_upscaled_{scale_factor}x_*.png"))
                    recent_files = [f for f in upscaled_files if f.stat().st_mtime > recent_threshold]
                    
                    print(f"📁 找到最近5分钟内的{scale_factor}倍放大文件: {recent_files}")
                    
                    if recent_files:
                        # 按修改时间排序，获取最新的文件
                        recent_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                        latest_file = recent_files[0]
                        print(f"✅ 使用最新的放大文件: {latest_file.name} (时间: {latest_file.stat().st_mtime})")
                    else:
                        print(f"❌ 没有找到最近的放大文件")
                        return None
            else:
                print(f"❌ 任务 {task_id} 没有prompt_id")
                return None
        else:
            # 任务不在内存中，尝试从数据库获取
            print(f"⚠️ 任务 {task_id} 不在内存中，尝试从数据库获取...")
            if self.db_manager:
                db_task_info = self.db_manager.get_task(task_id)
                if db_task_info and db_task_info.get('status') == 'completed':
                    # 如果数据库中显示已完成，直接返回结果
                    result_path = db_task_info.get('result_path')
                    if result_path and Path(result_path).exists():
                        print(f"✅ 从数据库找到已完成的放大任务: {result_path}")
                        return {
                            "task_id": task_id,
                            "status": "completed", 
                            "original_image": str(task_output_dir / "input_image.png"),
                            "upscaled_images": [f"/api/upscale/image/{task_id}/{Path(result_path).name}"],
                            "output_dir": str(task_output_dir)
                        }
                        
            print(f"❌ 任务 {task_id} 不在内存中且数据库中无有效结果")
            return None
        
        if latest_file and latest_file.exists():
            
            # 找到放大文件，任务完成
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = "completed"
            
            # 将最新的放大文件复制到任务目录，使用任务ID作为文件名前缀
            task_upscaled_filename = f"task_{task_id}_{latest_file.name}"
            task_upscaled_file = task_output_dir / task_upscaled_filename
            shutil.copy2(latest_file, task_upscaled_file)
            print(f"📁 复制放大文件到任务目录: {latest_file} -> {task_upscaled_file}")
            
            # 更新数据库状态
            if self.db_manager:
                self.db_manager.update_task_status(
                    task_id=task_id,
                    status="completed",
                    result_path=str(task_upscaled_file)
                )
            
            return {
                "task_id": task_id,
                "status": "completed",
                "original_image": str(task_output_dir / "input_image.png"),
                "upscaled_images": [f"/api/upscale/image/{task_id}/{task_upscaled_filename}"],
                "output_dir": str(task_output_dir)
            }
        
        # 如果没有找到放大后的文件，检查ComfyUI任务状态
        if task_id in self.tasks:
            task_info = self.tasks[task_id]
            prompt_id = task_info.get("prompt_id")
            
            if prompt_id:
                try:
                    print(f"🔍 检查ComfyUI任务状态: {prompt_id}")
                    # 检查ComfyUI任务状态
                    comfyui_status = await self.comfyui_client.get_task_status(prompt_id)
                    print(f"📊 ComfyUI状态: {comfyui_status}")
                    
                    # 如果ComfyUI任务失败，更新状态
                    if comfyui_status.get("status") == "failed":
                        print(f"❌ ComfyUI任务失败: {comfyui_status}")
                        self.tasks[task_id]["status"] = "failed"
                        
                        # 更新数据库状态
                        if self.db_manager:
                            self.db_manager.update_task_status(
                                task_id=task_id,
                                status="failed",
                                error="ComfyUI任务执行失败"
                            )
                        
                        return {
                            "task_id": task_id,
                            "status": "failed",
                            "error": "ComfyUI任务执行失败"
                        }
                    
                    # 如果ComfyUI任务完成但文件还没生成，等待一下
                    if comfyui_status.get("status") == "completed":
                        print(f"✅ ComfyUI任务完成，检查输出文件...")
                        # 再次检查文件
                        upscaled_files = list(comfyui_output_dir.glob(f"ultimate_upscaled_{scale_factor}x_*.png"))
                        print(f"📁 找到的放大文件: {upscaled_files}")
                        if upscaled_files:
                            # 按修改时间排序，获取最新的文件
                            upscaled_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                            latest_file = upscaled_files[0]
                            
                            # 将最新的放大文件复制到任务目录，使用任务ID作为文件名前缀
                            task_upscaled_filename = f"task_{task_id}_{latest_file.name}"
                            task_upscaled_file = task_output_dir / task_upscaled_filename
                            shutil.copy2(latest_file, task_upscaled_file)
                            
                            self.tasks[task_id]["status"] = "completed"
                            return {
                                "task_id": task_id,
                                "status": "completed",
                                "original_image": str(task_output_dir / "input_image.png"),
                                "upscaled_images": [f"/api/upscale/image/{task_id}/{task_upscaled_filename}"],
                                "output_dir": str(task_output_dir)
                            }
                        else:
                            print(f"⚠️ ComfyUI任务完成但未找到输出文件")
                
                except Exception as e:
                    print(f"❌ 检查ComfyUI任务状态失败: {e}")
                    import traceback
                    print(f"详细错误: {traceback.format_exc()}")
        else:
            print(f"⚠️ 任务 {task_id} 不在任务列表中")
        
        # 任务仍在处理中
        return None
    
    async def cleanup_task(self, task_id: str) -> bool:
        """清理任务文件
        
        Args:
            task_id: 任务ID
            
        Returns:
            清理是否成功
        """
        try:
            task_output_dir = self.output_dir / task_id
            if task_output_dir.exists():
                shutil.rmtree(task_output_dir)
            return True
        except Exception as e:
            print(f"清理任务失败: {e}")
            return False
