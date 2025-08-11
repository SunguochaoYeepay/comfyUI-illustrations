#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务管理器 - 统一依赖注入和服务初始化
避免全局变量和重复初始化问题
"""

from pathlib import Path
from typing import Optional

from core.config_validator import ensure_valid_config
from core.database_manager import DatabaseManager
from core.comfyui_client import ComfyUIClient
from core.workflow_template import WorkflowTemplate
from core.task_manager import TaskManager
from core.upscale_manager import UpscaleManager
from config.settings import (
    COMFYUI_URL, OUTPUT_DIR, DB_PATH
)


class ServiceManager:
    """服务管理器 - 单例模式，统一管理所有服务实例"""
    
    _instance: Optional['ServiceManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            print("🔧 初始化服务管理器...")
            
            # 验证配置
            ensure_valid_config()
            
            self._db_manager: Optional[DatabaseManager] = None
            self._comfyui_client: Optional[ComfyUIClient] = None
            self._task_manager: Optional[TaskManager] = None
            self._upscale_manager: Optional[UpscaleManager] = None
            self._workflow_template: Optional[WorkflowTemplate] = None
            ServiceManager._initialized = True
            print("✅ 服务管理器初始化完成")
    
    @property
    def db_manager(self) -> DatabaseManager:
        """获取数据库管理器（懒加载）"""
        if self._db_manager is None:
            print(f"💾 初始化数据库管理器: {DB_PATH}")
            self._db_manager = DatabaseManager(DB_PATH)
            print("✅ 数据库管理器初始化完成")
        return self._db_manager
    
    @property
    def comfyui_client(self) -> ComfyUIClient:
        """获取ComfyUI客户端（懒加载）"""
        if self._comfyui_client is None:
            print(f"🔌 初始化ComfyUI客户端: {COMFYUI_URL}")
            self._comfyui_client = ComfyUIClient(COMFYUI_URL)
            print("✅ ComfyUI客户端初始化完成")
        return self._comfyui_client
    
    @property
    def workflow_template(self) -> WorkflowTemplate:
        """获取工作流模板（懒加载）"""
        if self._workflow_template is None:
            print("📋 初始化工作流模板...")
            self._workflow_template = WorkflowTemplate("./flux_kontext_dev_basic.json")
            print("✅ 工作流模板初始化完成")
        return self._workflow_template
    
    @property
    def task_manager(self) -> TaskManager:
        """获取任务管理器（懒加载）"""
        if self._task_manager is None:
            print("📋 初始化任务管理器...")
            self._task_manager = TaskManager(
                self.db_manager,
                self.comfyui_client,
                self.workflow_template
            )
            print("✅ 任务管理器初始化完成")
        return self._task_manager
    
    @property
    def upscale_manager(self) -> UpscaleManager:
        """获取放大管理器（懒加载）"""
        if self._upscale_manager is None:
            print("🔍 初始化放大管理器...")
            self._upscale_manager = UpscaleManager(
                self.comfyui_client,
                OUTPUT_DIR,
                self.db_manager
            )
            print("✅ 放大管理器初始化完成")
        return self._upscale_manager
    
    def reset(self):
        """重置所有服务（用于测试）"""
        print("🔄 重置服务管理器...")
        self._db_manager = None
        self._comfyui_client = None
        self._task_manager = None
        self._upscale_manager = None
        self._workflow_template = None
        print("✅ 服务管理器重置完成")


# 全局服务管理器实例
service_manager = ServiceManager()


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器"""
    return service_manager.db_manager


def get_comfyui_client() -> ComfyUIClient:
    """获取ComfyUI客户端"""
    return service_manager.comfyui_client


def get_task_manager() -> TaskManager:
    """获取任务管理器"""
    return service_manager.task_manager


def get_upscale_manager() -> UpscaleManager:
    """获取放大管理器"""
    return service_manager.upscale_manager


def get_workflow_template() -> WorkflowTemplate:
    """获取工作流模板"""
    return service_manager.workflow_template
