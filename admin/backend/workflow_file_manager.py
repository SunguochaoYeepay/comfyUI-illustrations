#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流文件管理器
支持从文件系统同步工作流到数据库，以及从数据库导出工作流到文件
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

class WorkflowFileManager:
    """工作流文件管理器"""
    
    def __init__(self, workflows_dir: str = None):
        """
        初始化工作流文件管理器
        
        Args:
            workflows_dir: 工作流文件存储目录，默认为当前目录下的workflows文件夹
        """
        self.workflows_dir = Path(workflows_dir) if workflows_dir else Path("workflows")
        self.workflows_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        self.subdirs = {
            'qwen': self.workflows_dir / 'qwen',
            'flux': self.workflows_dir / 'flux',
            'flux1': self.workflows_dir / 'flux1',
            'gemini': self.workflows_dir / 'gemini',
            'wan': self.workflows_dir / 'wan',
            'fusion': self.workflows_dir / 'fusion',
            'templates': self.workflows_dir / 'templates'
        }
        
        for subdir in self.subdirs.values():
            subdir.mkdir(exist_ok=True)
    
    def sync_from_main_service(self, main_workflows_dir: str = "../../back/workflows"):
        """
        从主服务同步工作流文件
        
        Args:
            main_workflows_dir: 主服务工作流目录路径
        """
        print("🔄 从主服务同步工作流文件...")
        
        main_dir = Path(main_workflows_dir)
        if not main_dir.exists():
            print(f"❌ 主服务工作流目录不存在: {main_dir}")
            return
        
        # 清空目标目录
        if self.workflows_dir.exists():
            shutil.rmtree(self.workflows_dir)
            self.workflows_dir.mkdir(exist_ok=True)
            for subdir in self.subdirs.values():
                subdir.mkdir(exist_ok=True)
        
        # 复制所有JSON文件
        copied_count = 0
        for json_file in main_dir.rglob("*.json"):
            if json_file.is_file():
                # 计算相对路径
                relative_path = json_file.relative_to(main_dir)
                
                # 创建目标路径
                target_path = self.workflows_dir / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件
                shutil.copy2(json_file, target_path)
                print(f"📄 复制: {relative_path}")
                copied_count += 1
        
        print(f"✅ 同步完成，共复制 {copied_count} 个文件")
    
    def export_workflow_to_file(self, workflow_id: int, target_dir: str = None):
        """
        将数据库中的工作流导出为JSON文件
        
        Args:
            workflow_id: 工作流ID
            target_dir: 目标目录，默认为workflows目录
        """
        db = SessionLocal()
        try:
            workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
            if not workflow:
                print(f"❌ 工作流不存在: ID {workflow_id}")
                return None
            
            # 确定目标目录
            if target_dir:
                target_path = Path(target_dir)
            else:
                target_path = self.workflows_dir
            
            target_path.mkdir(exist_ok=True)
            
            # 生成文件名
            filename = f"{workflow.name}.json"
            file_path = target_path / filename
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(workflow.workflow_json, f, indent=2, ensure_ascii=False)
            
            print(f"📄 导出工作流: {workflow.name} -> {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ 导出工作流失败: {e}")
            return None
        finally:
            db.close()
    
    def export_all_workflows(self, target_dir: str = None):
        """
        导出所有工作流到文件
        
        Args:
            target_dir: 目标目录，默认为workflows目录
        """
        print("📤 导出所有工作流到文件...")
        
        db = SessionLocal()
        try:
            workflows = db.query(models.Workflow).all()
            
            if not workflows:
                print("❌ 数据库中没有工作流")
                return
            
            # 确定目标目录
            if target_dir:
                target_path = Path(target_dir)
            else:
                target_path = self.workflows_dir
            
            target_path.mkdir(exist_ok=True)
            
            exported_count = 0
            for workflow in workflows:
                filename = f"{workflow.name}.json"
                file_path = target_path / filename
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(workflow.workflow_json, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ 导出: {workflow.name}")
                    exported_count += 1
                    
                except Exception as e:
                    print(f"❌ 导出失败 {workflow.name}: {e}")
            
            print(f"🎉 导出完成，共导出 {exported_count} 个工作流")
            
        except Exception as e:
            print(f"❌ 导出过程中发生错误: {e}")
        finally:
            db.close()
    
    def import_workflow_from_file(self, file_path: str, name: str = None, description: str = None):
        """
        从JSON文件导入工作流到数据库
        
        Args:
            file_path: JSON文件路径
            name: 工作流名称，默认为文件名
            description: 工作流描述
        """
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"❌ 文件不存在: {file_path}")
            return None
        
        try:
            # 加载JSON内容
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_json = json.load(f)
            
            # 确定名称和描述
            if not name:
                name = file_path.stem
            
            if not description:
                description = f"从文件 {file_path.name} 导入的工作流"
            
            # 保存到数据库
            db = SessionLocal()
            try:
                # 检查是否已存在
                existing = db.query(models.Workflow).filter(models.Workflow.name == name).first()
                if existing:
                    print(f"⏭️  工作流已存在: {name}")
                    return existing
                
                # 创建新工作流
                workflow = models.Workflow(
                    name=name,
                    description=description,
                    workflow_json=workflow_json
                )
                
                db.add(workflow)
                db.commit()
                db.refresh(workflow)
                
                print(f"✅ 导入成功: {name} (ID: {workflow.id})")
                return workflow
                
            except Exception as e:
                print(f"❌ 保存到数据库失败: {e}")
                db.rollback()
                return None
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ 加载文件失败: {e}")
            return None
    
    def import_all_workflows_from_dir(self, source_dir: str = None):
        """
        从目录导入所有工作流文件
        
        Args:
            source_dir: 源目录，默认为workflows目录
        """
        if source_dir:
            source_path = Path(source_dir)
        else:
            source_path = self.workflows_dir
        
        if not source_path.exists():
            print(f"❌ 目录不存在: {source_path}")
            return
        
        print(f"📥 从目录导入工作流: {source_path}")
        
        imported_count = 0
        skipped_count = 0
        
        # 查找所有JSON文件
        for json_file in source_path.rglob("*.json"):
            if json_file.is_file():
                print(f"\n📄 处理文件: {json_file}")
                
                # 生成名称和描述
                relative_path = json_file.relative_to(source_path)
                name = str(relative_path).replace("/", "_").replace("\\", "_").replace(".json", "")
                description = f"从 {relative_path} 导入的工作流"
                
                # 导入工作流
                workflow = self.import_workflow_from_file(json_file, name, description)
                if workflow:
                    imported_count += 1
                else:
                    skipped_count += 1
        
        print(f"\n🎉 导入完成!")
        print(f"📊 统计信息:")
        print(f"   - 成功导入: {imported_count} 个工作流")
        print(f"   - 跳过: {skipped_count} 个工作流")
    
    def list_workflow_files(self):
        """列出工作流文件"""
        print("📋 工作流文件列表:")
        
        if not self.workflows_dir.exists():
            print("   (目录不存在)")
            return
        
        file_count = 0
        for json_file in self.workflows_dir.rglob("*.json"):
            if json_file.is_file():
                relative_path = json_file.relative_to(self.workflows_dir)
                file_size = json_file.stat().st_size
                print(f"   - {relative_path} ({file_size} bytes)")
                file_count += 1
        
        if file_count == 0:
            print("   (没有找到JSON文件)")
        else:
            print(f"\n   总计: {file_count} 个文件")
    
    def cleanup_orphaned_files(self):
        """清理孤立的文件（数据库中没有对应记录的文件）"""
        print("🧹 清理孤立的工作流文件...")
        
        db = SessionLocal()
        try:
            # 获取数据库中所有工作流名称
            workflows = db.query(models.Workflow).all()
            db_names = {wf.name for wf in workflows}
            
            # 检查文件系统中的文件
            orphaned_files = []
            for json_file in self.workflows_dir.rglob("*.json"):
                if json_file.is_file():
                    file_name = json_file.stem
                    if file_name not in db_names:
                        orphaned_files.append(json_file)
            
            if orphaned_files:
                print(f"发现 {len(orphaned_files)} 个孤立文件:")
                for file_path in orphaned_files:
                    print(f"   - {file_path}")
                
                # 询问是否删除
                response = input("\n是否删除这些孤立文件? (y/N): ")
                if response.lower() == 'y':
                    for file_path in orphaned_files:
                        file_path.unlink()
                        print(f"🗑️  删除: {file_path}")
                    print("✅ 清理完成")
                else:
                    print("⏭️  跳过清理")
            else:
                print("✅ 没有发现孤立文件")
                
        except Exception as e:
            print(f"❌ 清理过程中发生错误: {e}")
        finally:
            db.close()

def main():
    """主函数"""
    print("🔧 YeePay AI 工作流文件管理器")
    print("=" * 50)
    
    manager = WorkflowFileManager()
    
    while True:
        print("\n📋 可用操作:")
        print("1. 从主服务同步工作流文件")
        print("2. 从文件导入工作流到数据库")
        print("3. 从数据库导出工作流到文件")
        print("4. 导出所有工作流")
        print("5. 列出工作流文件")
        print("6. 清理孤立文件")
        print("7. 退出")
        
        choice = input("\n请选择操作 (1-7): ").strip()
        
        if choice == '1':
            manager.sync_from_main_service()
        elif choice == '2':
            source_dir = input("请输入源目录路径 (回车使用默认): ").strip()
            if not source_dir:
                source_dir = None
            manager.import_all_workflows_from_dir(source_dir)
        elif choice == '3':
            workflow_id = input("请输入工作流ID: ").strip()
            try:
                workflow_id = int(workflow_id)
                manager.export_workflow_to_file(workflow_id)
            except ValueError:
                print("❌ 无效的工作流ID")
        elif choice == '4':
            manager.export_all_workflows()
        elif choice == '5':
            manager.list_workflow_files()
        elif choice == '6':
            manager.cleanup_orphaned_files()
        elif choice == '7':
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")

if __name__ == "__main__":
    main()
