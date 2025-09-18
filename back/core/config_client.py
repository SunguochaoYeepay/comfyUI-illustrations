#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置客户端核心模块
负责从后台管理服务获取配置，实现配置的统一管理和服务的容错机制
"""

import json
import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigSource(Enum):
    """配置来源枚举"""
    BACKEND = "backend"  # 后台管理服务
    CACHE = "cache"      # 本地缓存
    LOCAL = "local"      # 本地配置文件
    ERROR = "error"      # 配置错误


class ConfigClient:
    """配置客户端核心类"""
    
    def __init__(self):
        """初始化配置客户端"""
        # 智能检测Docker环境中的admin backend URL
        admin_backend_url = os.getenv("BACKEND_CONFIG_URL", os.getenv('ADMIN_BACKEND_URL'))
        if not admin_backend_url:
            # 如果在Docker环境中且没有设置环境变量，尝试常见的Docker容器名
            if os.path.exists('/.dockerenv'):  # Docker环境检测
                admin_backend_url = 'http://yeepay-admin-backend:8888'
                logger.info(f"检测到Docker环境，使用admin backend URL: {admin_backend_url}")
            else:
                admin_backend_url = 'http://localhost:8888'
                logger.info(f"本地环境，使用admin backend URL: {admin_backend_url}")
        
        self.backend_url = admin_backend_url
        self.cache_ttl = int(os.getenv("CONFIG_CACHE_TTL", "300"))  # 5分钟缓存
        self.sync_interval = int(os.getenv("CONFIG_SYNC_INTERVAL", "60"))  # 1分钟同步间隔
        
        # 配置缓存
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # 本地配置文件路径
        self.local_config_path = Path(__file__).parent.parent / "config" / "local_config.yaml"
        
        # 健康状态
        self._backend_healthy = True
        self._last_health_check = None
        
        # 启动后台同步任务
        self._sync_task = None
        # 暂时禁用后台同步任务，避免在Docker环境中产生连接错误
        # self._start_sync_task()
    
    def _start_sync_task(self):
        """启动后台同步任务"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._sync_task = asyncio.create_task(self._background_sync())
            else:
                # 如果事件循环未运行，延迟启动
                asyncio.run_coroutine_threadsafe(self._background_sync(), loop)
        except Exception as e:
            logger.warning(f"启动后台同步任务失败: {e}")
    
    async def _background_sync(self):
        """后台配置同步任务"""
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                await self._sync_all_configs()
            except Exception as e:
                logger.error(f"后台同步任务错误: {e}")
                await asyncio.sleep(30)  # 错误时等待30秒再重试
    
    async def _sync_all_configs(self):
        """同步所有配置"""
        try:
            # 检查后台服务健康状态
            await self.check_backend_health()
            
            if self._backend_healthy:
                # 同步各种配置
                await self._sync_models_config()
                await self._sync_loras_config()
                await self._sync_workflows_config()
                await self._sync_image_gen_config()
                logger.info("配置同步完成")
            else:
                logger.warning("后台服务不可用，跳过配置同步")
        except Exception as e:
            logger.error(f"配置同步失败: {e}")
    
    async def _make_request(self, endpoint: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """发起HTTP请求"""
        try:
            url = f"{self.backend_url.rstrip('/')}/{endpoint.lstrip('/')}"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"请求失败: {url}, 状态码: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"请求异常: {url}, 错误: {e}")
            return None
    
    async def check_backend_health(self) -> bool:
        """检查后台服务健康状态"""
        try:
            result = await self._make_request("/")
            if result:
                self._backend_healthy = True
                self._last_health_check = datetime.now()
                logger.info("后台服务健康检查通过")
                return True
            else:
                self._backend_healthy = False
                logger.warning("后台服务健康检查失败")
                return False
        except Exception as e:
            self._backend_healthy = False
            logger.error(f"后台服务健康检查异常: {e}")
            return False
    
    def _is_cache_valid(self, config_type: str) -> bool:
        """检查缓存是否有效"""
        if config_type not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[config_type]
        return datetime.now() - cache_time < timedelta(seconds=self.cache_ttl)
    
    def _get_config_with_fallback(self, config_type: str, backend_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取配置，只使用后台配置和缓存"""
        # 1. 优先使用后台配置
        if backend_data and self._backend_healthy:
            self._cache[config_type] = backend_data
            self._cache_timestamps[config_type] = datetime.now()
            # 保持原有的config_source，不要覆盖
            if "config_source" not in backend_data:
                backend_data["config_source"] = ConfigSource.BACKEND.value
            if "last_updated" not in backend_data:
                backend_data["last_updated"] = datetime.now().isoformat()
            return backend_data
        
        # 2. 使用缓存配置
        if self._is_cache_valid(config_type) and config_type in self._cache:
            cached_data = self._cache[config_type].copy()
            cached_data["config_source"] = ConfigSource.CACHE.value
            return cached_data
        
        # 3. 如果都没有，返回空配置
        return {
            "config_source": ConfigSource.ERROR.value,
            "error": "无法获取配置，admin后端不可用",
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_local_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """加载本地配置文件"""
        try:
            if not self.local_config_path.exists():
                return None
            
            import yaml
            with open(self.local_config_path, 'r', encoding='utf-8') as f:
                local_config = yaml.safe_load(f)
            
            return local_config.get(config_type)
        except Exception as e:
            logger.error(f"加载本地配置失败: {e}")
            return None
    
    def _get_default_config(self, config_type: str) -> Dict[str, Any]:
        """获取默认配置"""
        default_configs = {
            "models": {
                "models": [
                    {
                        "name": "qwen-image",
                        "display_name": "Qwen",
                        "model_type": "qwen",
                        "available": True,
                        "sort_order": 1
                    },
                    {
                        "name": "flux1-dev",
                        "display_name": "Flux Kontext",
                        "model_type": "flux",
                        "available": True,
                        "sort_order": 2
                    }
                ],
                "config_source": "default",
                "last_updated": datetime.now().isoformat()
            },
            "loras": {
                "loras": [],
                "grouped_by_model": {},
                "config_source": "default"
            },
            "workflows": {
                "workflows": [],
                "config_source": "default"
            },
            "image_gen": {
                "default_size": {"width": 1024, "height": 1024},
                "size_ratios": ["1:1", "4:3", "3:4", "16:9", "9:16"],
                "default_steps": 20,
                "config_source": "default"
            }
        }
        
        return default_configs.get(config_type, {"config_source": "default"})
    
    async def get_models_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        try:
            # 尝试从admin后端获取基础模型列表
            backend_data = await self._make_request("/api/admin/image-gen-config/base-models")
            if backend_data and "models" in backend_data:
                # 转换admin后端的格式到主服务需要的格式
                models_data = {
                    "models": backend_data["models"],
                    "config_source": "admin_backend",
                    "last_updated": datetime.now().isoformat()
                }
                return self._get_config_with_fallback("models", models_data)
            else:
                raise Exception("admin后端返回的模型数据格式不正确")
        except Exception as e:
            logger.error(f"获取模型配置失败: {e}")
            return self._get_config_with_fallback("models")
    
    async def get_loras_config(self) -> Dict[str, Any]:
        """获取LoRA配置"""
        try:
            # 尝试从后台获取所有LoRA数据（设置大的page_size）
            backend_data = await self._make_request("/api/loras?page=1&page_size=100")
            return self._get_config_with_fallback("loras", backend_data)
        except Exception as e:
            logger.error(f"获取LoRA配置失败: {e}")
            return self._get_config_with_fallback("loras")
    
    async def get_workflows_config(self) -> Dict[str, Any]:
        """获取工作流配置"""
        try:
            # 尝试从后台获取
            backend_data = await self._make_request("/workflows")
            return self._get_config_with_fallback("workflows", backend_data)
        except Exception as e:
            logger.error(f"获取工作流配置失败: {e}")
            return self._get_config_with_fallback("workflows")
    
    async def get_image_gen_config(self) -> Dict[str, Any]:
        """获取生图配置"""
        try:
            logger.info(f"尝试从admin后端获取生图配置: {self.backend_url}/api/admin/image-gen-config")
            # 尝试从admin后端获取生图配置
            backend_data = await self._make_request("/api/admin/image-gen-config")
            if backend_data:
                logger.info(f"成功从admin后端获取生图配置: {backend_data}")
                # 处理新的尺寸比例配置格式
                size_ratios_data = backend_data.get("size_ratios", [])
                supported_ratios = []
                
                # 默认尺寸映射
                default_sizes = {
                    '1:1': {'width': 1024, 'height': 1024},
                    '4:3': {'width': 1024, 'height': 768},
                    '3:4': {'width': 768, 'height': 1024},
                    '16:9': {'width': 1024, 'height': 576},
                    '9:16': {'width': 576, 'height': 1024},
                    '21:9': {'width': 1024, 'height': 439},
                    '3:2': {'width': 1024, 'height': 683},
                    '2:3': {'width': 683, 'height': 1024}
                }
                
                if isinstance(size_ratios_data, list) and len(size_ratios_data) > 0:
                    # 新格式：每个比例包含ratio, width, height等信息
                    if isinstance(size_ratios_data[0], dict):
                        supported_ratios = [ratio.get("ratio", "1:1") for ratio in size_ratios_data]
                    else:
                        # 旧格式：直接是比例字符串列表，需要转换为对象数组
                        converted_ratios = []
                        for ratio in size_ratios_data:
                            if isinstance(ratio, str):
                                default_size = default_sizes.get(ratio, {'width': 1024, 'height': 1024})
                                converted_ratios.append({
                                    'ratio': ratio,
                                    'width': default_size['width'],
                                    'height': default_size['height'],
                                    'description': ''
                                })
                        size_ratios_data = converted_ratios
                        supported_ratios = [ratio['ratio'] for ratio in converted_ratios]
                else:
                    # 默认配置
                    supported_ratios = ["1:1", "4:3", "3:4", "16:9", "9:16"]
                
                # 转换admin后端的格式到主服务需要的格式
                image_gen_data = {
                    "default_size": backend_data.get("default_size", {"width": 1024, "height": 1024}),
                    "size_ratios": size_ratios_data,  # 保持原始格式，供前端使用
                    "supported_ratios": supported_ratios,  # 兼容旧格式的字段
                    "base_model_order": backend_data.get("base_model_order", []),  # 添加基础模型顺序
                    "lora_order": backend_data.get("lora_order", {}),  # 添加LoRA排序配置
                    "default_steps": 20,
                    "default_count": 1,
                    "config_source": "admin_backend",
                    "last_updated": datetime.now().isoformat()
                }
                logger.info(f"转换后的生图配置: {image_gen_data}")
                return self._get_config_with_fallback("image_gen", image_gen_data)
            else:
                logger.warning("admin后端返回的生图配置数据为空")
                raise Exception("admin后端返回的生图配置数据为空")
        except Exception as e:
            logger.error(f"获取生图配置失败: {e}")
            return self._get_config_with_fallback("image_gen")
    
    async def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        try:
            # 尝试从后台获取所有配置
            backend_data = await self._make_request("/all")
            if backend_data:
                return backend_data
            
            # 如果后台获取失败，分别获取各种配置
            models_config = await self.get_models_config()
            loras_config = await self.get_loras_config()
            workflows_config = await self.get_workflows_config()
            image_gen_config = await self.get_image_gen_config()
            
            return {
                "models": models_config,
                "loras": loras_config,
                "workflows": workflows_config,
                "image_gen": image_gen_config,
                "config_source": "mixed",
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取所有配置失败: {e}")
            return {
                "models": self._get_default_config("models"),
                "loras": self._get_default_config("loras"),
                "workflows": self._get_default_config("workflows"),
                "image_gen": self._get_default_config("image_gen"),
                "config_source": "default",
                "last_updated": datetime.now().isoformat()
            }
    
    async def _sync_models_config(self):
        """同步模型配置"""
        try:
            config = await self.get_models_config()
            self._cache["models"] = config
            self._cache_timestamps["models"] = datetime.now()
        except Exception as e:
            logger.error(f"同步模型配置失败: {e}")
    
    async def _sync_loras_config(self):
        """同步LoRA配置"""
        try:
            config = await self.get_loras_config()
            self._cache["loras"] = config
            self._cache_timestamps["loras"] = datetime.now()
        except Exception as e:
            logger.error(f"同步LoRA配置失败: {e}")
    
    async def _sync_workflows_config(self):
        """同步工作流配置"""
        try:
            config = await self.get_workflows_config()
            self._cache["workflows"] = config
            self._cache_timestamps["workflows"] = datetime.now()
        except Exception as e:
            logger.error(f"同步工作流配置失败: {e}")
    
    async def _sync_image_gen_config(self):
        """同步生图配置"""
        try:
            config = await self.get_image_gen_config()
            self._cache["image_gen"] = config
            self._cache_timestamps["image_gen"] = datetime.now()
        except Exception as e:
            logger.error(f"同步生图配置失败: {e}")
    
    def refresh_cache(self):
        """刷新缓存"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("配置缓存已刷新")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        status = {
            "backend_healthy": self._backend_healthy,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "cache_status": {}
        }
        
        for config_type in ["models", "loras", "workflows", "image_gen"]:
            cache_status = {
                "cached": config_type in self._cache,
                "valid": self._is_cache_valid(config_type),
                "last_updated": self._cache_timestamps.get(config_type).isoformat() if config_type in self._cache_timestamps else None
            }
            status["cache_status"][config_type] = cache_status
        
        return status
    
    def save_local_config(self, config_type: str, config_data: Dict[str, Any]):
        """保存本地配置"""
        try:
            # 确保配置目录存在
            self.local_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 加载现有配置
            local_config = {}
            if self.local_config_path.exists():
                import yaml
                with open(self.local_config_path, 'r', encoding='utf-8') as f:
                    local_config = yaml.safe_load(f) or {}
            
            # 更新配置
            local_config[config_type] = config_data
            
            # 保存配置
            import yaml
            with open(self.local_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(local_config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"本地配置已保存: {config_type}")
        except Exception as e:
            logger.error(f"保存本地配置失败: {e}")
    
    def load_local_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """加载本地配置"""
        return self._load_local_config(config_type)


# 全局配置客户端实例
_config_client: Optional[ConfigClient] = None


def get_config_client() -> ConfigClient:
    """获取配置客户端实例"""
    global _config_client
    # 每次都重新创建配置客户端，确保使用最新的配置
    _config_client = ConfigClient()
    return _config_client


# 便捷函数
async def get_models_config() -> Dict[str, Any]:
    """获取模型配置"""
    client = get_config_client()
    return await client.get_models_config()


async def get_loras_config() -> Dict[str, Any]:
    """获取LoRA配置"""
    client = get_config_client()
    return await client.get_loras_config()


async def get_workflows_config() -> Dict[str, Any]:
    """获取工作流配置"""
    client = get_config_client()
    return await client.get_workflows_config()


async def get_image_gen_config() -> Dict[str, Any]:
    """获取生图配置"""
    client = get_config_client()
    return await client.get_image_gen_config()


async def get_all_configs() -> Dict[str, Any]:
    """获取所有配置"""
    client = get_config_client()
    return await client.get_all_configs()


def get_cache_status() -> Dict[str, Any]:
    """获取缓存状态"""
    client = get_config_client()
    return client.get_cache_status()


def refresh_config_cache():
    """刷新配置缓存"""
    client = get_config_client()
    client.refresh_cache()
