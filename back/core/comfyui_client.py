#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI客户端
负责与ComfyUI服务进行通信
"""

import aiohttp
from typing import Any, Dict
from fastapi import HTTPException


class ComfyUIClient:
    """ComfyUI客户端，负责与ComfyUI服务进行通信"""
    
    def __init__(self, base_url: str):
        """初始化ComfyUI客户端
        
        Args:
            base_url: ComfyUI服务的基础URL
        """
        self.base_url = base_url
    
    async def submit_workflow(self, workflow: Dict[str, Any]) -> str:
        """提交工作流到ComfyUI
        
        Args:
            workflow: 要提交的工作流字典
            
        Returns:
            prompt_id: 提交后返回的prompt_id
            
        Raises:
            HTTPException: 当提交失败时抛出
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/prompt",
                json={"prompt": workflow}
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Failed to submit workflow to ComfyUI")
                result = await response.json()
                return result["prompt_id"]
    
    async def get_task_status(self, prompt_id: str) -> Dict[str, Any]:
        """查询任务状态
        
        Args:
            prompt_id: 任务ID
            
        Returns:
            任务状态信息字典
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/history/{prompt_id}"
            ) as response:
                if response.status != 200:
                    return {"status": "unknown"}
                return await response.json()
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态
        
        Returns:
            队列状态信息字典
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/queue"
            ) as response:
                if response.status != 200:
                    return {"queue_running": [], "queue_pending": []}
                return await response.json()
    
    async def check_health(self) -> bool:
        """检查ComfyUI服务健康状态
        
        Returns:
            True表示服务正常，False表示服务异常
        """
        try:
            timeout = aiohttp.ClientTimeout(total=5)  # 5秒超时
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.base_url}/") as response:
                    return response.status == 200
        except Exception as e:
            print(f"ComfyUI健康检查失败: {e}")
            return False
