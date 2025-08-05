#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - Flux Kontext 图像生成服务

使用方法:
1. 确保已安装依赖: pip install -r requirements.txt
2. 确保ComfyUI正在运行: python ComfyUI/main.py --api-only
3. 运行此脚本: python start_server.py
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        sys.exit(1)
    print(f"✅ Python版本: {sys.version}")

def check_dependencies():
    """检查依赖是否已安装"""
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn', 
        'aiohttp': 'aiohttp',
        'aiofiles': 'aiofiles',
        'python-multipart': 'multipart',
        'pillow': 'PIL',
        'pydantic': 'pydantic'
    }
    
    missing_packages = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def check_comfyui_connection(url="http://127.0.0.1:8188"):
    """检查ComfyUI连接"""
    try:
        response = requests.get(f"{url}/system_stats", timeout=5)
        if response.status_code == 200:
            print("✅ ComfyUI连接正常")
            return True
    except requests.exceptions.RequestException:
        pass
    
    print("❌ 无法连接到ComfyUI")
    print("请确保ComfyUI正在运行:")
    print("  cd ComfyUI")
    print("  python main.py --api-only")
    return False

def check_workflow_file():
    """检查工作流文件是否存在"""
    workflow_file = Path("./flux_kontext_dev_basic.json")
    if workflow_file.exists():
        print("✅ 工作流文件存在")
        return True
    else:
        print("❌ 工作流文件不存在: ./flux_kontext_dev_basic.json")
        return False

def create_directories():
    """创建必要的目录"""
    directories = ['uploads', 'outputs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ 目录结构已创建")

def start_server(host="0.0.0.0", port=9000):
    """启动FastAPI服务器"""
    print(f"🚀 启动服务器 http://{host}:{port}")
    print(f"📱 前端页面: http://localhost:{port}/frontend.html")
    print(f"📚 API文档: http://localhost:{port}/docs")
    print("\n按 Ctrl+C 停止服务器\n")
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app", 
            host=host, 
            port=port, 
            reload=True,
            log_level="warning"
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")

def main():
    """主函数"""
    print("🎨 Flux Kontext 图像生成服务启动器")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 检查依赖
    if not check_dependencies():
        return
    
    # 检查工作流文件
    if not check_workflow_file():
        return
    
    # 创建目录
    create_directories()
    
    # 检查ComfyUI连接
    check_comfyui_connection()
    
    print("\n" + "=" * 50)
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main()