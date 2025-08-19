#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器模块
负责任务的创建、执行和状态管理
"""

import asyncio
import json
import random
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import MAX_WAIT_TIME, COMFYUI_MAIN_OUTPUT_DIR, OUTPUT_DIR
from core.database_manager import DatabaseManager
from core.comfyui_client import ComfyUIClient
from core.workflow_template import WorkflowTemplate
from core.translation_client import get_translation_client


class TaskManager:
    """任务管理器，负责任务的创建、执行和状态管理"""
    
    def __init__(self, db_manager: DatabaseManager, comfyui_client: ComfyUIClient, workflow_template: WorkflowTemplate):
        """初始化任务管理器
        
        Args:
            db_manager: 数据库管理器
            comfyui_client: ComfyUI客户端
            workflow_template: 工作流模板
        """
        self.db = db_manager
        self.comfyui = comfyui_client
        self.workflow_template = workflow_template
    
    async def create_task(self, reference_image_path: str, description: str, parameters: Dict[str, Any]) -> str:
        """创建新任务
        
        Args:
            reference_image_path: 参考图像路径
            description: 任务描述
            parameters: 任务参数
            
        Returns:
            任务ID
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        # 保存任务到数据库
        self.db.create_task(task_id, description, reference_image_path, parameters)
        
        # 异步执行任务
        asyncio.create_task(self.execute_task(task_id, reference_image_path, description, parameters))
        
        return task_id
    
    async def execute_task(self, task_id: str, reference_image_path: str, description: str, parameters: Dict[str, Any]):
        """执行任务
        
        Args:
            task_id: 任务ID
            reference_image_path: 参考图像路径
            description: 任务描述
            parameters: 任务参数
        """
        try:
            print(f"🚀 开始执行任务: {task_id}")
            print(f"   描述: {description}")
            print(f"   参数: {parameters}")
            print(f"   参考图像: {reference_image_path}")
            
            # 更新状态为处理中
            self.db.update_task_status(task_id, "processing")
            
            # 翻译中文描述为英文
            translated_description = description
            if self._is_chinese_text(description):
                print(f"🌐 检测到中文描述，开始翻译...")
                translation_client = get_translation_client()
                
                # 检查Ollama服务是否可用
                if await translation_client.check_ollama_health():
                    if await translation_client.check_model_available():
                        translated_description = await translation_client.translate_to_english(description)
                        if translated_description:
                            print(f"✅ 翻译成功: {description} -> {translated_description}")
                        else:
                            print(f"⚠️ 翻译失败，使用原描述: {description}")
                    else:
                        print(f"⚠️ qianwen模型不可用，使用原描述: {description}")
                else:
                    print(f"⚠️ Ollama服务不可用，使用原描述: {description}")
            else:
                print(f"✅ 描述已经是英文，无需翻译: {description}")
            
            # 获取生成数量
            count = int(parameters.get("count", 1))
            result_paths = []
            
            print(f"🎯 开始生成 {count} 张图片...")
            
            # 循环生成每张图片
            for i in range(count):
                print(f"📸 正在生成第 {i+1}/{count} 张图片...")
                
                try:
                    # 为每次生成创建独立的参数副本
                    current_params = parameters.copy()
                    current_params["count"] = 1  # 每次只生成一张
                    
                    # 如果没有指定种子，为每张图片生成不同的随机种子
                    if not parameters.get("seed"):
                        current_params["seed"] = random.randint(1, 2**32 - 1)
                        print(f"🎲 使用随机种子: {current_params['seed']}")
                    
                    # 准备工作流
                    print(f"🔧 准备工作流...")
                    model_name = current_params.get("model", "flux1-dev")
                    workflow = self.workflow_template.customize_workflow(
                        reference_image_path, translated_description, current_params, model_name
                    )
                    print(f"✅ 工作流准备完成")
                    
                    # 提交到ComfyUI
                    print(f"📤 提交工作流到ComfyUI...")
                    prompt_id = await self.comfyui.submit_workflow(workflow)
                    print(f"✅ 已提交工作流，prompt_id: {prompt_id}")
                    
                    # 等待完成
                    print(f"⏳ 等待任务完成...")
                    batch_result = await self.wait_for_completion(task_id, prompt_id)
                    
                    if batch_result:
                        result_paths.extend(batch_result)
                        print(f"✅ 第 {i+1} 张图片生成完成: {batch_result}")
                    else:
                        print(f"❌ 第 {i+1} 张图片生成失败")
                        raise Exception(f"第 {i+1} 张图片生成失败，没有返回结果")
                        
                except Exception as e:
                    print(f"❌ 生成第 {i+1} 张图片时出错: {str(e)}")
                    raise Exception(f"生成第 {i+1} 张图片失败: {str(e)}")
                
                # 更新进度
                progress = int((i + 1) / count * 100)
                self.db.update_task_progress(task_id, progress)
                
                # 如果不是最后一张，稍微等待一下避免过快请求
                if i < count - 1:
                    await asyncio.sleep(1)
            
            # 处理结果
            if result_paths:
                print(f"🔍 最终结果: count={count}, result_paths数量={len(result_paths)}, paths={result_paths}")
                
                if len(result_paths) == 1:
                    # 单张图片，直接存储路径
                    print(f"💾 保存单张图片: {result_paths[0]}")
                    self.db.update_task_status(task_id, "completed", result_path=result_paths[0])
                else:
                    # 多张图片，将路径合并为JSON字符串存储
                    result_data = json.dumps(result_paths)
                    print(f"💾 保存多张图片JSON: {result_data}")
                    self.db.update_task_status(task_id, "completed", result_path=result_data)
            else:
                error_msg = "No output generated"
                print(f"❌ {error_msg}")
                self.db.update_task_status(task_id, "failed", error=error_msg)
                
        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            print(f"详细错误信息:")
            print(traceback.format_exc())
            self.db.update_task_status(task_id, "failed", error=error_msg)
    
    async def wait_for_completion(self, task_id: str, prompt_id: str, max_wait_time: int = MAX_WAIT_TIME) -> Optional[list]:
        """等待任务完成
        
        Args:
            task_id: 任务ID
            prompt_id: ComfyUI的prompt_id
            max_wait_time: 最大等待时间（秒）
            
        Returns:
            结果文件路径列表，如果失败返回None
        """
        start_time = datetime.now()
        print(f"⏰ 开始等待任务完成，最大等待时间: {max_wait_time}秒")
        
        while (datetime.now() - start_time).seconds < max_wait_time:
            try:
                print(f"🔍 检查任务状态: {prompt_id}")
                history = await self.comfyui.get_task_status(prompt_id)
                
                if prompt_id in history:
                    task_info = history[prompt_id]
                    print(f"✅ 找到任务信息")
                    
                    if "outputs" in task_info:
                        print(f"🎉 任务完成，开始处理输出")
                        # 任务完成，查找输出图像
                        outputs = task_info["outputs"]
                        result_paths = []
                        
                        print(f"📁 ComfyUI输出目录: {COMFYUI_MAIN_OUTPUT_DIR}")
                        print(f"📁 本地输出目录: {OUTPUT_DIR}")
                        
                        # 首先尝试从节点输出获取图片
                        for node_id, output in outputs.items():
                            if "images" in output:
                                print(f"🖼️ 找到图像输出节点 {node_id}，包含 {len(output['images'])} 张图片")
                                for image_info in output["images"]:
                                    filename = image_info['filename']
                                    # 检查图片是否在yeepay子目录中
                                    source_path = COMFYUI_MAIN_OUTPUT_DIR / "yeepay" / filename
                                    if not source_path.exists():
                                        # 如果不在yeepay子目录，尝试直接在输出目录中查找
                                        source_path = COMFYUI_MAIN_OUTPUT_DIR / filename
                                    
                                    dest_path = OUTPUT_DIR / filename
                                    
                                    print(f"📄 处理图片: {filename}")
                                    print(f"   源路径: {source_path}")
                                    print(f"   目标路径: {dest_path}")
                                    
                                    if source_path.exists():
                                        shutil.copy2(source_path, dest_path)
                                        result_paths.append(f"outputs/{filename}")
                                        print(f"✅ 复制图片成功: {filename}")
                                    else:
                                        print(f"❌ 源文件不存在: {source_path}")
                        
                        print(f"📊 总共处理了 {len(result_paths)} 张图片: {result_paths}")
                        
                        # 如果没有从ComfyUI输出中找到图片，尝试从文件系统中查找最新的图片
                        if not result_paths:
                            print("🔍 尝试从文件系统中查找最新生成的图片...")
                            try:
                                # 查找yeepay目录中最新的图片文件
                                yeepay_dir = COMFYUI_MAIN_OUTPUT_DIR / "yeepay"
                                if yeepay_dir.exists():
                                    # 获取所有png文件并按修改时间排序
                                    png_files = list(yeepay_dir.glob("*.png"))
                                    if png_files:
                                        # 按修改时间排序，获取最新的文件
                                        latest_file = max(png_files, key=lambda f: f.stat().st_mtime)
                                        print(f"📄 找到最新图片文件: {latest_file.name}")
                                        
                                        # 复制到输出目录
                                        dest_path = OUTPUT_DIR / latest_file.name
                                        shutil.copy2(latest_file, dest_path)
                                        result_paths.append(f"outputs/{latest_file.name}")
                                        print(f"✅ 复制图片成功: {latest_file.name}")
                                        
                                        return result_paths
                                    else:
                                        print("❌ yeepay目录中没有找到png文件")
                                else:
                                    print("❌ yeepay目录不存在")
                            except Exception as e:
                                print(f"❌ 从文件系统查找图片时出错: {e}")
                        
                        if result_paths:
                            return result_paths
                        else:
                            print(f"❌ 没有找到任何输出图片")
                            return None
                    else:
                        print(f"⏳ 任务还在处理中，等待...")
                
                # 检查是否还在队列中
                queue_status = await self.comfyui.get_queue_status()
                queue_running = queue_status.get("queue_running", [])
                queue_pending = queue_status.get("queue_pending", [])
                
                # 检查任务是否还在队列中
                in_queue = any(item[1] == prompt_id for item in queue_running + queue_pending)
                if not in_queue and prompt_id not in history:
                    # 任务不在队列中也不在历史中，可能失败了
                    print(f"❌ 任务不在队列中也不在历史中，可能失败了")
                    break
                
                await asyncio.sleep(2)  # 等待2秒后再检查
                
            except Exception as e:
                print(f"❌ 检查任务状态时出错: {e}")
                await asyncio.sleep(5)
        
        print(f"⏰ 等待超时，任务可能失败")
        return None
    
    def _is_chinese_text(self, text: str) -> bool:
        """检测文本是否包含中文字符
        
        Args:
            text: 要检测的文本
            
        Returns:
            是否包含中文字符
        """
        if not text:
            return False
        
        # 检查是否包含中文字符（Unicode范围：4E00-9FFF）
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息字典，如果不存在返回None
        """
        return self.db.get_task(task_id)
