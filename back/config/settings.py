#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
包含所有全局配置、常量定义和路径设置
"""

import os
from pathlib import Path

# =============================================================================
# ComfyUI服务配置
# =============================================================================
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")

# =============================================================================
# 工作流目录配置
# =============================================================================
# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
WORKFLOWS_DIR = PROJECT_ROOT / "workflows"

# =============================================================================
# Ollama服务配置
# =============================================================================
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# =============================================================================
# 路径配置 - 支持Docker和本地环境
# =============================================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

if ENVIRONMENT == "local":
    # 本地开发环境
    COMFYUI_OUTPUT_DIR = Path(os.getenv("COMFYUI_OUTPUT_DIR", "E:/AI-Image/ComfyUI-aki-v1.4/output/yeepay"))
    COMFYUI_MAIN_OUTPUT_DIR = Path(os.getenv("COMFYUI_MAIN_OUTPUT_DIR", "E:/AI-Image/ComfyUI-aki-v1.4/output"))
    COMFYUI_INPUT_DIR = Path(os.getenv("COMFYUI_INPUT_DIR", "E:/AI-Image/ComfyUI-aki-v1.4/input"))
    COMFYUI_MODELS_DIR = Path(os.getenv("COMFYUI_MODELS_DIR", "E:/AI-Image/ComfyUI-aki-v1.4/models"))
    COMFYUI_LORAS_DIR = Path(os.getenv("COMFYUI_LORAS_DIR", "E:/AI-Image/ComfyUI-aki-v1.4/models/loras"))
else:
    # Docker环境
    COMFYUI_OUTPUT_DIR = Path(os.getenv("COMFYUI_OUTPUT_DIR", "/app/comfyui/output/yeepay"))
    COMFYUI_MAIN_OUTPUT_DIR = Path(os.getenv("COMFYUI_MAIN_OUTPUT_DIR", "/app/comfyui/output"))
    COMFYUI_INPUT_DIR = Path(os.getenv("COMFYUI_INPUT_DIR", "/app/comfyui/input"))
    COMFYUI_MODELS_DIR = Path(os.getenv("COMFYUI_MODELS_DIR", "/app/comfyui/models"))
    COMFYUI_LORAS_DIR = Path(os.getenv("COMFYUI_LORAS_DIR", "/app/comfyui/models/loras"))

# =============================================================================
# 应用目录配置
# =============================================================================
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")

# 数据库路径配置
if ENVIRONMENT == "local":
    DB_PATH = "tasks.db"
else:
    # Docker环境使用数据卷
    DB_PATH = "/app/data/tasks.db"

# =============================================================================
# 应用常量
# =============================================================================
DEFAULT_IMAGE_SIZE = "512x512"
DEFAULT_STEPS = 20
DEFAULT_COUNT = 1
MAX_WAIT_TIME = 300  # 秒
MIN_FILE_SIZE = 100  # 字节
TARGET_IMAGE_WIDTH = 1024
TARGET_IMAGE_HEIGHT = 1024

# =============================================================================
# 初始化目录
# =============================================================================
def init_directories():
    """初始化必要的目录"""
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

# 自动初始化目录
init_directories()
