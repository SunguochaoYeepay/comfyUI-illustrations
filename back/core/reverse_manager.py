#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片反推管理器
负责处理图片内容反推任务
"""

import asyncio
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import COMFYUI_MAIN_OUTPUT_DIR, OUTPUT_DIR, COMFYUI_INPUT_DIR
from core.database_manager import DatabaseManager
from core.comfyui_client import ComfyUIClient
from core.workflow_template import WorkflowTemplate
from core.model_manager import ModelConfig, ModelType


class ReverseManager:
    """图片反推管理器"""
    
    def __init__(self, comfyui_client: ComfyUIClient, output_dir: Path, db_manager: DatabaseManager = None):
        """初始化图片反推管理器
        
        Args:
            comfyui_client: ComfyUI客户端
            output_dir: 输出目录
            db_manager: 数据库管理器（可选）
        """
        self.comfyui_client = comfyui_client
        self.output_dir = output_dir
        self.db_manager = db_manager
        self.workflow_template = WorkflowTemplate()
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 存储任务信息
        self.tasks = {}
    
    async def reverse_image(
        self, 
        image_path: str, 
        caption_type: str = "Descriptive",
        caption_length: str = "very long",
        max_new_tokens: int = 2048,
        temperature: float = 0.6,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """反推图片内容
        
        Args:
            image_path: 图片路径
            caption_type: 描述类型
            caption_length: 描述长度
            max_new_tokens: 最大token数
            temperature: 温度参数
            top_p: top_p参数
            
        Returns:
            反推结果字典
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        try:
            print(f"🔍 开始图片反推任务: {task_id}")
            print(f"   图片路径: {image_path}")
            print(f"   描述类型: {caption_type}")
            print(f"   描述长度: {caption_length}")
            
            # 创建任务输出目录
            task_output_dir = self.output_dir / task_id
            task_output_dir.mkdir(parents=True, exist_ok=True)
            
            # 处理图片路径
            processed_image_path = await self._process_image_path(image_path, task_output_dir)
            
            # 创建JoyCaption模型配置
            model_config = ModelConfig(
                model_type=ModelType.JOYCAPTION,
                name="joycaption-beta",
                display_name="JoyCaption Beta",
                unet_file="",
                clip_file="",
                vae_file="",
                description="JoyCaption图片内容反推模型"
            )
            
            # 直接创建JoyCaption工作流
            from core.workflows.joycaption_workflow import JoyCaptionWorkflow
            joycaption_workflow = JoyCaptionWorkflow(model_config)
            
            # 准备参数
            parameters = {
                "caption_type": caption_type,
                "caption_length": caption_length,
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
            
            # 创建工作流
            workflow = joycaption_workflow.create_workflow(processed_image_path, "", parameters)
            
            # 提交到ComfyUI
            print(f"📤 提交反推工作流到ComfyUI...")
            prompt_id = await self.comfyui_client.submit_workflow(workflow)
            print(f"✅ 已提交反推工作流，prompt_id: {prompt_id}")
            
            # 等待完成
            print(f"⏳ 等待反推任务完成...")
            result = await self._wait_for_completion(task_id, prompt_id)
            
            if result:
                print(f"✅ 图片反推完成: {task_id}")
                return {
                    "success": True,
                    "task_id": task_id,
                    "prompt": result.get("prompt", ""),
                    "confidence": result.get("confidence", 0.8),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"❌ 图片反推失败: {task_id}")
                return {
                    "success": False,
                    "task_id": task_id,
                    "error": "反推任务执行失败",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ 图片反推异常: {e}")
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _process_image_path(self, image_path: str, task_output_dir: Path) -> str:
        """处理图片路径"""
        from config.settings import ENVIRONMENT
        import requests
        import aiohttp
        
        # 检查是否是HTTP URL
        if image_path.startswith(('http://', 'https://')):
            print(f"🌐 检测到HTTP URL，需要下载图片: {image_path}")
            
            # 从URL中提取文件名
            filename = image_path.split('/')[-1]
            if not filename or '.' not in filename:
                filename = f"image_{int(time.time())}.png"
            
            # 下载图片到任务目录
            task_image_path = task_output_dir / filename
            
            try:
                # 使用aiohttp异步下载
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_path) as response:
                        if response.status == 200:
                            with open(task_image_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)
                            print(f"✅ 图片下载完成: {task_image_path}")
                        else:
                            raise Exception(f"下载图片失败，状态码: {response.status}")
            except Exception as e:
                print(f"❌ 下载图片失败: {e}")
                raise Exception(f"下载图片失败: {str(e)}")
            
            # 复制到ComfyUI输入目录（如果目标文件不存在或不同）
            comfyui_input_path = COMFYUI_INPUT_DIR / filename
            
            # 检查是否需要复制
            if not comfyui_input_path.exists() or comfyui_input_path != task_image_path:
                shutil.copy2(task_image_path, comfyui_input_path)
                print(f"📁 复制图片到ComfyUI输入目录: {task_image_path} -> {comfyui_input_path}")
            else:
                print(f"📁 图片已存在于ComfyUI输入目录: {comfyui_input_path}")
            
            return str(comfyui_input_path)
        
        # 检查是否是API路径（如 /api/image/upload/filename.png）
        if image_path.startswith('/api/image/upload/'):
            print(f"🔗 检测到API路径，转换为本地文件路径: {image_path}")
            
            # 从API路径中提取文件名
            filename = image_path.split('/')[-1]
            if not filename or '.' not in filename:
                raise ValueError(f"无效的API路径: {image_path}")
            
            # 构建本地文件路径
            from config.settings import UPLOAD_DIR
            local_file_path = UPLOAD_DIR / filename
            
            if not local_file_path.exists():
                raise FileNotFoundError(f"图片文件不存在: {local_file_path}")
            
            print(f"✅ 找到本地图片文件: {local_file_path}")
            
            # 复制到ComfyUI输入目录
            comfyui_input_path = COMFYUI_INPUT_DIR / filename
            
            # 检查是否需要复制到ComfyUI输入目录
            if not comfyui_input_path.exists() or comfyui_input_path != local_file_path:
                shutil.copy2(local_file_path, comfyui_input_path)
                print(f"📁 复制图片到ComfyUI输入目录: {local_file_path} -> {comfyui_input_path}")
            else:
                print(f"📁 图片已存在于ComfyUI输入目录: {comfyui_input_path}")
            
            # 复制到任务目录作为备份
            task_image_path = task_output_dir / filename
            if not task_image_path.exists() or task_image_path != local_file_path:
                shutil.copy2(local_file_path, task_image_path)
                print(f"📁 复制图片到任务目录: {local_file_path} -> {task_image_path}")
            else:
                print(f"📁 图片已存在于任务目录: {task_image_path}")
            
            return str(comfyui_input_path)
        
        # 处理本地文件路径
        input_path = Path(image_path)
        if not input_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        if ENVIRONMENT == "production":
            # Docker环境：直接使用本地文件路径
            return str(input_path)
        else:
            # 本地环境：复制到ComfyUI输入目录
            comfyui_input_path = COMFYUI_INPUT_DIR / input_path.name
            
            # 检查是否需要复制到ComfyUI输入目录
            if not comfyui_input_path.exists() or comfyui_input_path != input_path:
                shutil.copy2(input_path, comfyui_input_path)
                print(f"📁 复制图片到ComfyUI输入目录: {input_path} -> {comfyui_input_path}")
            else:
                print(f"📁 图片已存在于ComfyUI输入目录: {comfyui_input_path}")
            
            # 复制到任务目录作为备份
            task_image_path = task_output_dir / input_path.name
            if not task_image_path.exists() or task_image_path != input_path:
                shutil.copy2(input_path, task_image_path)
                print(f"📁 复制图片到任务目录: {input_path} -> {task_image_path}")
            else:
                print(f"📁 图片已存在于任务目录: {task_image_path}")
            
            return str(comfyui_input_path)
    
    async def _wait_for_completion(self, task_id: str, prompt_id: str, max_wait_time: int = 300) -> Optional[Dict[str, Any]]:
        """等待反推任务完成"""
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # 获取任务状态
                history_response = await self.comfyui_client.get_task_status(prompt_id)
                print(f"🔍 ComfyUI历史响应: {history_response}")
                
                # ComfyUI的history API返回格式是 {prompt_id: {status: ..., outputs: ...}}
                if prompt_id in history_response:
                    task_data = history_response[prompt_id]
                    status = task_data.get("status", {})
                    outputs = task_data.get("outputs", {})
                    
                    print(f"🔍 任务状态: {status}")
                    print(f"🔍 任务输出: {outputs}")
                    
                    # 检查任务是否完成
                    if status.get("status_str") == "success":
                        # 任务成功完成，获取结果
                        result = await self._extract_reverse_result(task_data)
                        return result
                    elif status.get("status_str") == "error":
                        print(f"❌ 反推任务失败: {status.get('error', 'Unknown error')}")
                        return None
                    else:
                        print(f"⏳ 任务状态: {status.get('status_str', 'unknown')}")
                else:
                    print(f"⏳ 任务尚未开始或仍在队列中...")
                
                # 等待一段时间后重试
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"⚠️ 获取任务状态失败: {e}")
                await asyncio.sleep(2)
        
        print(f"⏰ 反推任务超时: {task_id}")
        return None
    
    async def _extract_reverse_result(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """从ComfyUI状态中提取反推结果"""
        try:
            # 从ComfyUI的输出中提取文本结果
            # 根据JoyCaption工作流，结果应该在节点15和20的ShowText输出中
            
            print(f"🔍 开始提取反推结果...")
            print(f"🔍 ComfyUI任务数据: {task_data}")
            
            # 获取ComfyUI的输出数据
            outputs = task_data.get("outputs", {})
            print(f"🔍 ComfyUI输出: {outputs}")
            
            # 查找ShowText节点的输出
            # 节点15和20都是ShowText节点，包含反推结果
            caption_text = ""
            
            # 根据JoyCaption工作流，节点15包含真实的反推结果，节点20包含提示词
            # 优先从节点15获取结果（这是主要的反推结果）
            if "15" in outputs:
                node_15_output = outputs["15"]
                if "text" in node_15_output:
                    text_value = node_15_output["text"]
                    # 处理text字段可能是数组的情况
                    if isinstance(text_value, list) and len(text_value) > 0:
                        caption_text = text_value[0]
                        print(f"✅ 从节点15获取反推结果: {caption_text[:100]}...")
                    elif isinstance(text_value, str):
                        caption_text = text_value
                        print(f"✅ 从节点15获取反推结果: {caption_text[:100]}...")
                    else:
                        print(f"⚠️ 节点15的text字段格式异常: {text_value}")
                else:
                    print(f"⚠️ 节点15没有text字段: {node_15_output}")
            
            # 如果节点15没有结果，尝试节点20（但节点20通常是提示词，不是反推结果）
            if not caption_text and "20" in outputs:
                node_20_output = outputs["20"]
                if "text" in node_20_output:
                    text_value = node_20_output["text"]
                    if isinstance(text_value, list) and len(text_value) > 0:
                        caption_text = text_value[0]
                    elif isinstance(text_value, str):
                        caption_text = text_value
                    print(f"⚠️ 从节点20获取结果（可能是提示词）: {caption_text[:100]}...")
                else:
                    print(f"⚠️ 节点20没有text字段: {node_20_output}")
            
            # 如果还是没有找到，尝试从其他可能的输出节点获取
            if not caption_text:
                for node_id, node_output in outputs.items():
                    if isinstance(node_output, dict):
                        # 查找包含文本的字段
                        for key, value in node_output.items():
                            if isinstance(value, str) and len(value) > 50:  # 假设反推结果比较长
                                caption_text = value
                                print(f"✅ 从节点{node_id}的{key}字段获取反推结果: {caption_text[:100]}...")
                                break
                        if caption_text:
                            break
            
            # 如果仍然没有找到结果，返回默认信息
            if not caption_text:
                print("⚠️ 未找到反推结果，可能ComfyUI输出格式与预期不符")
                caption_text = "Unable to extract caption from ComfyUI output"
            
            # 尝试将英文结果翻译成中文
            chinese_caption = await self._translate_to_chinese(caption_text)
            
            result = {
                "prompt": chinese_caption if chinese_caption else caption_text,
                "original_prompt": caption_text,  # 保留原始英文结果
                "confidence": 0.85  # 可以后续根据实际需要调整
            }
            
            print(f"✅ 反推结果提取完成: {result['prompt'][:100]}...")
            return result
            
        except Exception as e:
            print(f"❌ 提取反推结果失败: {e}")
            return {
                "prompt": f"Failed to extract result: {str(e)}",
                "confidence": 0.0
            }
    
    async def _translate_to_chinese(self, english_text: str) -> Optional[str]:
        """将英文文本翻译成中文"""
        try:
            from core.translation_client import get_translation_client
            
            print(f"🌐 开始翻译英文反推结果到中文...")
            print(f"   原文长度: {len(english_text)}字符")
            
            # 如果文本太长，截断到合理长度（保留前2000字符）
            if len(english_text) > 2000:
                truncated_text = english_text[:2000] + "..."
                print(f"   文本过长，截断到2000字符进行翻译")
                english_text = truncated_text
            
            translation_client = get_translation_client()
            
            # 检查Ollama服务是否可用
            if await translation_client.check_ollama_health():
                if await translation_client.check_model_available():
                    chinese_text = await translation_client.translate_to_chinese(english_text)
                    if chinese_text:
                        print(f"✅ 翻译成功: {english_text[:50]}... -> {chinese_text[:50]}...")
                        return chinese_text
                    else:
                        print(f"⚠️ 翻译失败，返回英文原文")
                        return None
                else:
                    print(f"⚠️ 翻译模型不可用，返回英文原文")
                    return None
            else:
                print(f"⚠️ Ollama服务不可用，返回英文原文")
                return None
                
        except Exception as e:
            print(f"❌ 翻译过程异常: {e}")
            return None
