#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入工作流脚本
快速从主服务导入所有工作流到管理后台
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow_file_manager import WorkflowFileManager

def main():
    """主函数"""
    print("🚀 YeePay AI 工作流批量导入工具")
    print("=" * 50)
    
    # 创建工作流文件管理器
    manager = WorkflowFileManager()
    
    # 步骤1: 从主服务同步工作流文件
    print("\n📥 步骤1: 从主服务同步工作流文件...")
    manager.sync_from_main_service()
    
    # 步骤2: 导入所有工作流到数据库
    print("\n💾 步骤2: 导入工作流到数据库...")
    manager.import_all_workflows_from_dir()
    
    # 步骤3: 显示结果
    print("\n📊 步骤3: 显示导入结果...")
    manager.list_workflow_files()
    
    print("\n✨ 批量导入完成!")
    print("现在可以通过管理后台查看和管理这些工作流了。")

if __name__ == "__main__":
    main()
