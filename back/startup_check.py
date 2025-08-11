#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动验证脚本 - 在应用启动前验证所有依赖和配置
确保不会出现运行时初始化错误
"""

import sys
import asyncio
from pathlib import Path

def run_startup_checks():
    """运行启动检查"""
    print("🚀 开始启动验证...")
    
    # 1. 配置验证
    try:
        from core.config_validator import ensure_valid_config
        config_result = ensure_valid_config()
        print("✅ 配置验证通过")
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False
    
    # 2. 服务管理器初始化验证
    try:
        from core.service_manager import service_manager
        print("✅ 服务管理器初始化成功")
    except Exception as e:
        print(f"❌ 服务管理器初始化失败: {e}")
        return False
    
    # 3. 数据库连接验证
    try:
        db_manager = service_manager.db_manager
        # 尝试简单查询
        db_manager.get_task("test")
        print("✅ 数据库连接正常")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    
    # 4. ComfyUI连接验证（异步）
    async def check_comfyui():
        try:
            comfyui_client = service_manager.comfyui_client
            is_healthy = await comfyui_client.check_health()
            if is_healthy:
                print("✅ ComfyUI连接正常")
            else:
                print("⚠️ ComfyUI连接异常，但不影响启动")
            return True
        except Exception as e:
            print(f"⚠️ ComfyUI连接检查失败: {e}，但不影响启动")
            return True
    
    # 运行异步检查
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(check_comfyui())
    finally:
        loop.close()
    
    # 5. 关键文件存在性验证
    critical_files = [
        "flux_kontext_dev_basic.json",
        "flux_upscale_workflow.json"
    ]
    
    for file_path in critical_files:
        if not Path(file_path).exists():
            print(f"❌ 关键文件缺失: {file_path}")
            return False
    print("✅ 关键文件检查通过")
    
    print("🎉 启动验证完成，所有检查通过")
    return True

if __name__ == "__main__":
    if not run_startup_checks():
        print("❌ 启动验证失败，退出")
        sys.exit(1)
    else:
        print("✅ 启动验证成功，可以启动应用")
