#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - Flux Kontext 图像生成服务
"""

import os
from pathlib import Path

class Config:
    """应用配置类"""
    
    # 基础配置
    APP_NAME = "Flux Kontext Image Generation API"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 9000))
    
    # ComfyUI配置
    COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
    COMFYUI_TIMEOUT = int(os.getenv("COMFYUI_TIMEOUT", 300))  # 5分钟超时
    
    # 文件路径配置
    BASE_DIR = Path(__file__).parent
    UPLOAD_DIR = BASE_DIR / "uploads"
    OUTPUT_DIR = BASE_DIR / "outputs"
    WORKFLOW_FILE = BASE_DIR / "flux_kontext_dev_basic.json"
    
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", str(BASE_DIR / "tasks.db"))
    
    # 文件上传配置
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "bmp"}
    
    # 生成参数默认值
    DEFAULT_STEPS = 20
    DEFAULT_CFG = 1.0
    DEFAULT_GUIDANCE = 2.5
    
    # 生成参数限制
    MIN_STEPS = 1
    MAX_STEPS = 50
    MIN_CFG = 0.1
    MAX_CFG = 20.0
    MIN_GUIDANCE = 0.1
    MAX_GUIDANCE = 10.0
    
    # 任务配置
    MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", 3))
    TASK_CLEANUP_DAYS = int(os.getenv("TASK_CLEANUP_DAYS", 7))  # 7天后清理任务
    
    # 安全配置
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    API_KEY = os.getenv("API_KEY", None)  # 可选的API密钥
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / "app.log"
    
    # 缓存配置
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # 1小时
    
    @classmethod
    def create_directories(cls):
        """创建必要的目录"""
        cls.UPLOAD_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def validate_config(cls):
        """验证配置"""
        errors = []
        
        # 检查工作流文件
        if not cls.WORKFLOW_FILE.exists():
            errors.append(f"工作流文件不存在: {cls.WORKFLOW_FILE}")
        
        # 检查参数范围
        if cls.MIN_STEPS >= cls.MAX_STEPS:
            errors.append("MIN_STEPS 必须小于 MAX_STEPS")
        
        if cls.MIN_CFG >= cls.MAX_CFG:
            errors.append("MIN_CFG 必须小于 MAX_CFG")
        
        if cls.MIN_GUIDANCE >= cls.MAX_GUIDANCE:
            errors.append("MIN_GUIDANCE 必须小于 MAX_GUIDANCE")
        
        if errors:
            raise ValueError("配置验证失败:\n" + "\n".join(errors))
    
    @classmethod
    def get_env_info(cls):
        """获取环境信息"""
        return {
            "app_name": cls.APP_NAME,
            "version": cls.APP_VERSION,
            "debug": cls.DEBUG,
            "host": cls.HOST,
            "port": cls.PORT,
            "comfyui_url": cls.COMFYUI_URL,
            "upload_dir": str(cls.UPLOAD_DIR),
            "output_dir": str(cls.OUTPUT_DIR),
            "max_file_size": cls.MAX_FILE_SIZE,
            "allowed_extensions": list(cls.ALLOWED_EXTENSIONS)
        }

# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

# 生产环境配置
class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = "WARNING"
    CORS_ORIGINS = ["https://yourdomain.com"]  # 限制CORS源

# 测试环境配置
class TestingConfig(Config):
    DEBUG = True
    DATABASE_URL = ":memory:"  # 使用内存数据库
    UPLOAD_DIR = Path("/tmp/test_uploads")
    OUTPUT_DIR = Path("/tmp/test_outputs")

# 根据环境变量选择配置
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}

ENV = os.getenv("ENVIRONMENT", "development")
config = config_map.get(ENV, DevelopmentConfig)

# 验证配置
if ENV != "testing":
    config.create_directories()
    config.validate_config()