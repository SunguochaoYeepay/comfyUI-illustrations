#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI翻译客户端
使用Ollama的qianwen模型进行中文到英文的翻译
"""

import json
import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from config.settings import OLLAMA_URL

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TranslationClient:
    """AI翻译客户端"""
    
    def __init__(self, ollama_url: str = None):
        """初始化翻译客户端
        
        Args:
            ollama_url: Ollama服务地址，默认为 http://localhost:11434
        """
        self.ollama_url = ollama_url or OLLAMA_URL or "http://localhost:11434"
        self.model_name = "qwen2.5:7b"  # 使用已安装的qwen2.5:7b模型
        self.timeout = 30  # 30秒超时
        
        logger.info(f"🔧 翻译客户端初始化完成")
        logger.info(f"   Ollama URL: {self.ollama_url}")
        logger.info(f"   模型名称: {self.model_name}")
        logger.info(f"   超时时间: {self.timeout}秒")
    
    async def translate_to_english(self, chinese_text: str) -> Optional[str]:
        """将中文文本翻译成英文
        
        Args:
            chinese_text: 中文文本
            
        Returns:
            翻译后的英文文本，如果失败返回None
        """
        start_time = datetime.now()
        logger.info(f"🔄 开始翻译任务")
        logger.info(f"   原文: {chinese_text}")
        logger.info(f"   开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 构建翻译提示词
            prompt = self._build_translation_prompt(chinese_text)
            logger.debug(f"   提示词: {prompt}")
            
            # 调用Ollama API
            response = await self._call_ollama(prompt)
            
            if response:
                # 提取翻译结果
                english_text = self._extract_translation(response)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                logger.info(f"✅ 翻译成功")
                logger.info(f"   译文: {english_text}")
                logger.info(f"   耗时: {duration:.2f}秒")
                logger.info(f"   结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                return english_text
            else:
                logger.error(f"❌ 翻译失败: Ollama返回空响应")
                return None
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.error(f"❌ 翻译异常: {str(e)}")
            logger.error(f"   耗时: {duration:.2f}秒")
            logger.error(f"   异常类型: {type(e).__name__}")
            return None
    
    def _build_translation_prompt(self, chinese_text: str) -> str:
        """构建翻译提示词
        
        Args:
            chinese_text: 中文文本
            
        Returns:
            翻译提示词
        """
        prompt = f"""你是一个专业的中英翻译专家，请将以下中文文本翻译成英文。

翻译要求：
1. 保持原意完全准确，不添加或删除任何信息
2. 使用自然流畅的英文表达，符合英语语法规范
3. 如果是图像生成提示词，请保持艺术性和描述性，使用专业的艺术术语
4. 如果是技术术语，请使用标准的英文表达
5. 只返回英文翻译结果，不要添加任何解释、注释或额外文本
6. 保持原文的语气和风格

中文文本：{chinese_text}

英文翻译："""
        
        logger.debug(f"📝 构建翻译提示词完成，长度: {len(prompt)}字符")
        return prompt
    
    async def _call_ollama(self, prompt: str) -> Optional[str]:
        """调用Ollama API
        
        Args:
            prompt: 提示词
            
        Returns:
            Ollama的响应文本
        """
        logger.debug(f"🌐 开始调用Ollama API")
        logger.debug(f"   请求URL: {self.ollama_url}/api/generate")
        
        try:
            # 构建请求数据
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 更低的温度，保证翻译准确性
                    "top_p": 0.8,
                    "max_tokens": 1000,  # 增加token限制
                    "repeat_penalty": 1.1  # 避免重复
                }
            }
            
            logger.debug(f"   请求参数: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
            
            # 发送请求
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    logger.debug(f"   响应状态: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        logger.debug(f"   原始响应: {response_text}")
                        logger.info(f"✅ Ollama API调用成功")
                        
                        return response_text
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Ollama API请求失败")
                        logger.error(f"   状态码: {response.status}")
                        logger.error(f"   错误信息: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error(f"❌ Ollama API请求超时")
            logger.error(f"   超时时间: {self.timeout}秒")
            return None
        except Exception as e:
            logger.error(f"❌ 调用Ollama API失败: {str(e)}")
            logger.error(f"   异常类型: {type(e).__name__}")
            return None
    
    def _extract_translation(self, response: str) -> str:
        """从Ollama响应中提取翻译结果
        
        Args:
            response: Ollama的响应文本
            
        Returns:
            提取的翻译结果
        """
        logger.debug(f"🔍 开始提取翻译结果")
        logger.debug(f"   原始响应: {response}")
        
        try:
            # 清理响应文本
            cleaned_response = response.strip()
            
            # 如果响应包含"英文翻译："，提取后面的内容
            if "英文翻译：" in cleaned_response:
                parts = cleaned_response.split("英文翻译：")
                if len(parts) > 1:
                    result = parts[1].strip()
                    logger.debug(f"   提取结果 (中文标记): {result}")
                    return result
            
            # 如果响应包含"English translation:"，提取后面的内容
            if "English translation:" in cleaned_response:
                parts = cleaned_response.split("English translation:")
                if len(parts) > 1:
                    result = parts[1].strip()
                    logger.debug(f"   提取结果 (英文标记): {result}")
                    return result
            
            # 如果响应包含"Translation:"，提取后面的内容
            if "Translation:" in cleaned_response:
                parts = cleaned_response.split("Translation:")
                if len(parts) > 1:
                    result = parts[1].strip()
                    logger.debug(f"   提取结果 (Translation标记): {result}")
                    return result
            
            # 直接返回清理后的响应
            logger.debug(f"   直接返回清理后响应: {cleaned_response}")
            return cleaned_response
            
        except Exception as e:
            logger.error(f"❌ 提取翻译结果失败: {str(e)}")
            logger.error(f"   原始响应: {response}")
            return response.strip()
    
    async def check_ollama_health(self) -> bool:
        """检查Ollama服务是否可用
        
        Returns:
            服务是否可用
        """
        logger.info(f"🏥 开始检查Ollama服务健康状态")
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    is_healthy = response.status == 200
                    logger.info(f"   Ollama服务状态: {'✅ 正常' if is_healthy else '❌ 异常'}")
                    logger.info(f"   响应状态码: {response.status}")
                    return is_healthy
        except Exception as e:
            logger.error(f"❌ Ollama健康检查失败: {str(e)}")
            return False
    
    async def check_model_available(self) -> bool:
        """检查qwen2.5:7b模型是否可用
        
        Returns:
            模型是否可用
        """
        logger.info(f"🔍 开始检查模型可用性")
        logger.info(f"   目标模型: {self.model_name}")
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        models = result.get("models", [])
                        
                        logger.info(f"   可用模型列表:")
                        for model in models:
                            model_name = model.get("name", "")
                            logger.info(f"     - {model_name}")
                        
                        # 检查是否有qwen2.5:7b模型
                        for model in models:
                            if self.model_name in model.get("name", ""):
                                logger.info(f"✅ 目标模型可用: {self.model_name}")
                                return True
                        
                        logger.warning(f"⚠️ 目标模型不可用: {self.model_name}")
                        return False
                    else:
                        logger.error(f"❌ 获取模型列表失败: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ 检查模型可用性失败: {str(e)}")
            return False


# 全局翻译客户端实例
translation_client: TranslationClient = None


def get_translation_client() -> TranslationClient:
    """获取翻译客户端实例"""
    global translation_client
    if translation_client is None:
        translation_client = TranslationClient()
        logger.info(f"🔄 创建新的翻译客户端实例")
    return translation_client
