#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流初始化脚本
从主服务的workflows目录导入所有工作流JSON文件到管理后台数据库
"""

import json
import os
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_workflow_files():
    """获取所有工作流JSON文件"""
    # 主服务的workflows目录路径
    main_workflows_dir = Path("../../back/workflows")
    
    if not main_workflows_dir.exists():
        print(f"❌ 主服务workflows目录不存在: {main_workflows_dir}")
        return []
    
    workflow_files = []
    
    # 递归查找所有JSON文件
    for json_file in main_workflows_dir.rglob("*.json"):
        if json_file.is_file():
            workflow_files.append(json_file)
    
    print(f"📁 找到 {len(workflow_files)} 个工作流文件")
    return workflow_files

def load_workflow_json(file_path):
    """加载工作流JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载工作流文件失败 {file_path}: {e}")
        return None

def create_workflow_name(file_path):
    """根据文件路径创建工作流名称"""
    # 获取相对路径
    relative_path = file_path.relative_to(Path("../../back/workflows"))
    
    # 移除.json扩展名
    name = relative_path.stem
    
    # 替换路径分隔符为下划线
    name = str(relative_path.parent / name).replace("/", "_").replace("\\", "_")
    
    # 如果名称太长，截取
    if len(name) > 80:
        name = name[:80]
    
    return name

def create_workflow_description(file_path, workflow_json):
    """创建工作流描述"""
    # 获取相对路径
    relative_path = file_path.relative_to(Path("../../back/workflows"))
    
    # 基础描述
    description = f"从 {relative_path} 导入的工作流"
    
    # 尝试从工作流中提取更多信息
    if isinstance(workflow_json, dict):
        node_count = len(workflow_json)
        description += f"，包含 {node_count} 个节点"
        
        # 检查是否有特定的节点类型
        node_types = set()
        for node_data in workflow_json.values():
            if isinstance(node_data, dict) and "class_type" in node_data:
                node_types.add(node_data["class_type"])
        
        if node_types:
            description += f"，主要节点类型: {', '.join(list(node_types)[:3])}"
    
    return description

def import_workflows():
    """导入所有工作流到数据库"""
    print("🚀 开始导入工作流...")
    
    # 创建数据库表
    models.Base.metadata.create_all(bind=engine)
    
    # 获取数据库会话
    db = SessionLocal()
    
    try:
        # 获取所有工作流文件
        workflow_files = get_workflow_files()
        
        if not workflow_files:
            print("❌ 没有找到工作流文件")
            return
        
        imported_count = 0
        skipped_count = 0
        
        for file_path in workflow_files:
            print(f"\n📄 处理文件: {file_path}")
            
            # 加载JSON内容
            workflow_json = load_workflow_json(file_path)
            if workflow_json is None:
                skipped_count += 1
                continue
            
            # 创建工作流名称和描述
            name = create_workflow_name(file_path)
            description = create_workflow_description(file_path, workflow_json)
            
            # 检查是否已存在同名工作流
            existing_workflow = db.query(models.Workflow).filter(models.Workflow.name == name).first()
            if existing_workflow:
                print(f"⏭️  跳过已存在的工作流: {name}")
                skipped_count += 1
                continue
            
            # 创建工作流记录
            workflow = models.Workflow(
                name=name,
                description=description,
                workflow_json=workflow_json
            )
            
            db.add(workflow)
            db.commit()
            db.refresh(workflow)
            
            print(f"✅ 导入成功: {name} (ID: {workflow.id})")
            imported_count += 1
        
        print(f"\n🎉 导入完成!")
        print(f"📊 统计信息:")
        print(f"   - 成功导入: {imported_count} 个工作流")
        print(f"   - 跳过: {skipped_count} 个工作流")
        print(f"   - 总计处理: {len(workflow_files)} 个文件")
        
    except Exception as e:
        print(f"❌ 导入过程中发生错误: {e}")
        db.rollback()
    finally:
        db.close()

def list_imported_workflows():
    """列出已导入的工作流"""
    print("\n📋 已导入的工作流列表:")
    
    db = SessionLocal()
    try:
        workflows = db.query(models.Workflow).all()
        
        if not workflows:
            print("   (暂无工作流)")
            return
        
        for workflow in workflows:
            node_count = len(workflow.workflow_json) if workflow.workflow_json else 0
            print(f"   - ID: {workflow.id}, 名称: {workflow.name}")
            print(f"     描述: {workflow.description}")
            print(f"     节点数: {node_count}, 创建时间: {workflow.created_at}")
            print()
            
    except Exception as e:
        print(f"❌ 查询工作流列表失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 YeePay AI 工作流初始化工具")
    print("=" * 50)
    
    # 导入工作流
    import_workflows()
    
    # 列出已导入的工作流
    list_imported_workflows()
    
    print("\n✨ 初始化完成!")
