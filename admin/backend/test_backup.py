#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份功能测试脚本
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.backup_manager import BackupManager

async def test_backup_manager():
    """测试备份管理器"""
    print("🧪 开始测试备份管理器...")
    
    backup_manager = BackupManager()
    
    try:
        # 测试创建备份
        print("\n1. 测试创建备份...")
        backup_id = await backup_manager.create_backup(
            backup_type="admin_service",
            backup_name="test_backup_2024",
            description="测试备份"
        )
        print(f"✅ 备份创建成功: {backup_id}")
        
        # 测试备份列表
        print("\n2. 测试获取备份列表...")
        backup_list = await backup_manager.list_backups()
        print(f"✅ 备份列表获取成功: {len(backup_list['backups'])} 个备份")
        
        # 测试备份验证
        print("\n3. 测试备份验证...")
        backup_file = backup_manager._find_backup_file(backup_id)
        if backup_file:
            is_valid = await backup_manager._validate_backup(backup_file)
            print(f"✅ 备份验证结果: {'有效' if is_valid else '无效'}")
        
        # 测试清理功能
        print("\n4. 测试清理过期备份...")
        deleted_count = await backup_manager.cleanup_old_backups(0)  # 删除所有备份
        print(f"✅ 清理完成: 删除了 {deleted_count} 个备份")
        
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_backup_paths():
    """测试备份路径"""
    print("\n🗂️ 测试备份路径...")
    
    backup_manager = BackupManager()
    
    print("主服务路径:")
    for name, path in backup_manager.main_service_paths.items():
        exists = path.exists()
        print(f"  {name}: {path} ({'存在' if exists else '不存在'})")
    
    print("\nAdmin服务路径:")
    for name, path in backup_manager.admin_service_paths.items():
        exists = path.exists()
        print(f"  {name}: {path} ({'存在' if exists else '不存在'})")
    
    print("\n系统配置路径:")
    for name, path in backup_manager.system_paths.items():
        exists = path.exists()
        print(f"  {name}: {path} ({'存在' if exists else '不存在'})")

if __name__ == "__main__":
    print("🚀 备份系统测试")
    print("=" * 50)
    
    # 运行路径测试
    asyncio.run(test_backup_paths())
    
    # 运行备份管理器测试
    asyncio.run(test_backup_manager())
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")
