#!/usr/bin/env python3
"""
后端服务启动脚本
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 设置工作目录为当前脚本所在目录
os.chdir(current_dir)

if __name__ == "__main__":
    import uvicorn
    from main import app
    
    print("🚀 启动 Flux Kontext 后端服务...")
    print(f"📁 工作目录: {current_dir}")
    
    # 启动服务
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=True,
        reload_dirs=[str(current_dir)]
    )