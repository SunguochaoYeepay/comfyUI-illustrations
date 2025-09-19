#!/usr/bin/env python3
"""
同步LoRA预览图片从admin后端到主服务
"""
import os
import shutil
from pathlib import Path
import time

def sync_lora_previews():
    """同步LoRA预览图片"""
    admin_previews_dir = Path("admin/backend/uploads/lora_previews")
    main_previews_dir = Path("back/uploads/lora_previews")
    
    if not admin_previews_dir.exists():
        print("❌ Admin预览图片目录不存在")
        return
    
    # 确保主服务预览图片目录存在
    main_previews_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取admin目录中的所有文件
    admin_files = {f.name: f for f in admin_previews_dir.iterdir() if f.is_file()}
    main_files = {f.name: f for f in main_previews_dir.iterdir() if f.is_file()} if main_previews_dir.exists() else {}
    
    # 同步文件
    synced_count = 0
    for filename, admin_file in admin_files.items():
        main_file = main_previews_dir / filename
        
        # 如果文件不存在或admin文件更新，则复制
        if not main_file.exists() or admin_file.stat().st_mtime > main_file.stat().st_mtime:
            shutil.copy2(admin_file, main_file)
            synced_count += 1
            print(f"✅ 同步: {filename}")
    
    # 删除主服务中不存在于admin的文件
    removed_count = 0
    for filename in main_files:
        if filename not in admin_files:
            (main_previews_dir / filename).unlink()
            removed_count += 1
            print(f"🗑️ 删除: {filename}")
    
    if synced_count > 0 or removed_count > 0:
        print(f"📊 同步完成: 新增/更新 {synced_count} 个文件, 删除 {removed_count} 个文件")
    else:
        print("✅ 预览图片已是最新状态")

if __name__ == "__main__":
    sync_lora_previews()
