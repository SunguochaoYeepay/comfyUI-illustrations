#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Admin初始化脚本
用于Docker容器启动时初始化数据库和配置
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base
import crud
import models
from schemas import system_config, base_model
from config import settings

def init_admin():
    """初始化admin数据库和配置"""
    
    print("🚀 开始初始化Admin数据库...")
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 初始化系统配置
        print("📋 初始化系统配置...")
        from init_system_config import init_system_config
        init_system_config()
        
        # 初始化基础模型
        print("🤖 初始化基础模型...")
        from init_base_models import init_base_models
        init_base_models()
        
        # 初始化Seedream4
        print("🎨 初始化Seedream4...")
        from init_seedream4 import init_seedream4
        init_seedream4()
        
        # 初始化LoRA
        print("🎭 初始化LoRA...")
        from init_loras import init_loras
        init_loras()
        
        # 初始化工作流
        print("⚙️ 初始化工作流...")
        from init_workflows import init_workflows
        init_workflows()
        
        print("🎉 Admin初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_admin()
