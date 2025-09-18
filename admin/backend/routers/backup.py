#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份管理API路由
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import asyncio

from database import get_db
from dependencies import get_current_user
from schemas.backup_schemas import (
    BackupCreateRequest, BackupRestoreRequest, BackupScheduleRequest,
    BackupRecordResponse, BackupListResponse, BackupStatusResponse
)
from core.backup_manager import BackupManager
import models
import schemas_legacy as schemas

router = APIRouter()

# 全局备份管理器实例
backup_manager = BackupManager()

@router.post("/backup/create")
async def create_backup(
    request: BackupCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """创建备份"""
    try:
        print(f"🔄 收到备份请求: {request.backup_name}")
        print(f"📋 备份类型: {request.backup_type}")
        
        # 创建备份记录
        backup_id = str(uuid.uuid4())
        backup_record = models.BackupRecord(
            backup_id=backup_id,
            backup_name=request.backup_name,
            backup_type=request.backup_type,
            backup_size=0,  # 稍后更新
            file_path="",   # 稍后更新
            status="pending",
            description=request.description,
            created_by="admin",  # 暂时使用固定用户
            backup_metadata=f'{{"compression_level": {request.compression_level}, "include_files": {request.include_files}}}'
        )
        
        db.add(backup_record)
        db.commit()
        db.refresh(backup_record)
        
        # 在后台执行备份
        background_tasks.add_task(
            execute_backup_task,
            backup_id,
            request.backup_type,
            request.backup_name,
            request.description,
            request.compression_level,
            request.include_files,
            db
        )
        
        return {
            "backup_id": backup_id,
            "status": "pending",
            "message": "备份任务已创建，正在后台执行"
        }
        
    except Exception as e:
        print(f"❌ 创建备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")

async def execute_backup_task(
    backup_id: str,
    backup_type: str,
    backup_name: str,
    description: str,
    compression_level: int,
    include_files: bool,
    db: Session
):
    """执行备份任务"""
    try:
        print(f"🔄 开始执行备份任务: {backup_id}")
        
        # 更新任务状态为运行中
        backup_record = db.query(models.BackupRecord).filter(
            models.BackupRecord.backup_id == backup_id
        ).first()
        
        if backup_record:
            backup_record.status = "running"
            db.commit()
        
        # 执行备份
        actual_backup_id = await backup_manager.create_backup(
            backup_type=backup_type,
            backup_name=backup_name,
            description=description,
            compression_level=compression_level,
            include_files=include_files
        )
        
        # 更新备份记录
        backup_file = backup_manager._find_backup_file(actual_backup_id)
        if backup_file and backup_record:
            backup_record.backup_size = backup_file.stat().st_size
            backup_record.file_path = str(backup_file)
            backup_record.status = "completed"
            backup_record.completed_at = datetime.now()
            backup_record.checksum = await backup_manager._calculate_checksum(backup_file)
            db.commit()
            
            print(f"✅ 备份任务完成: {backup_id}")
        else:
            raise Exception("备份文件未找到")
            
    except Exception as e:
        print(f"❌ 备份任务失败: {e}")
        # 更新任务状态为失败
        if backup_record:
            backup_record.status = "failed"
            backup_record.completed_at = datetime.now()
            db.commit()

@router.get("/backup/list", response_model=BackupListResponse)
async def list_backups(
    page: int = 1,
    limit: int = 20,
    backup_type: str = "all",
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """获取备份列表"""
    try:
        # 从文件系统获取备份列表
        backup_list = await backup_manager.list_backups(page, limit, backup_type)
        
        # 转换为响应格式
        backups = []
        for backup_info in backup_list["backups"]:
            backup_response = BackupRecordResponse(
                id=0,  # 文件系统备份没有数据库ID
                backup_id=backup_info["backup_id"],
                backup_name=backup_info["backup_name"],
                backup_type=backup_info["backup_type"],
                backup_size=backup_info["backup_size"],
                file_path=backup_info["file_path"],
                status=backup_info["status"],
                description=backup_info["description"],
                created_at=datetime.fromisoformat(backup_info["created_at"].replace('Z', '+00:00')),
                completed_at=None,
                checksum=backup_info["checksum"],
                created_by=None
            )
            backups.append(backup_response)
        
        return BackupListResponse(
            backups=backups,
            total=backup_list["total"],
            page=backup_list["page"],
            limit=backup_list["limit"],
            has_more=backup_list["has_more"]
        )
        
    except Exception as e:
        print(f"❌ 获取备份列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")

@router.get("/backup/download/{backup_id}")
async def download_backup(
    backup_id: str,
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """下载备份文件"""
    try:
        backup_file = backup_manager._find_backup_file(backup_id)
        if not backup_file or not backup_file.exists():
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 生成下载文件名
        download_filename = f"backup_{backup_id}.zip"
        
        return FileResponse(
            path=str(backup_file),
            filename=download_filename,
            media_type='application/zip'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 下载备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载备份失败: {str(e)}")

@router.post("/backup/restore/{backup_id}")
async def restore_backup(
    backup_id: str,
    request: BackupRestoreRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """恢复备份"""
    try:
        if not request.confirm:
            raise HTTPException(status_code=400, detail="必须确认恢复操作")
        
        print(f"🔄 收到恢复请求: {backup_id}")
        print(f"📋 恢复类型: {request.restore_type}")
        
        # 验证备份文件是否存在
        backup_file = backup_manager._find_backup_file(backup_id)
        if not backup_file:
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        # 创建恢复任务记录
        task_id = str(uuid.uuid4())
        restore_task = models.BackupTask(
            task_id=task_id,
            backup_id=backup_id,
            task_type="restore",
            status="pending"
        )
        
        db.add(restore_task)
        db.commit()
        
        # 在后台执行恢复
        background_tasks.add_task(
            execute_restore_task,
            task_id,
            backup_id,
            request.restore_type,
            db
        )
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "恢复任务已创建，正在后台执行"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 恢复备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"恢复备份失败: {str(e)}")

async def execute_restore_task(
    task_id: str,
    backup_id: str,
    restore_type: str,
    db: Session
):
    """执行恢复任务"""
    try:
        print(f"🔄 开始执行恢复任务: {task_id}")
        
        # 更新任务状态
        restore_task = db.query(models.BackupTask).filter(
            models.BackupTask.task_id == task_id
        ).first()
        
        if restore_task:
            restore_task.status = "running"
            db.commit()
        
        # 执行恢复
        success = await backup_manager.restore_backup(backup_id, restore_type)
        
        # 更新任务状态
        if restore_task:
            restore_task.status = "completed" if success else "failed"
            restore_task.completed_at = datetime.now()
            db.commit()
            
            print(f"✅ 恢复任务完成: {task_id}")
        
    except Exception as e:
        print(f"❌ 恢复任务失败: {e}")
        # 更新任务状态为失败
        if restore_task:
            restore_task.status = "failed"
            restore_task.error_message = str(e)
            restore_task.completed_at = datetime.now()
            db.commit()

@router.delete("/backup/{backup_id}")
async def delete_backup(
    backup_id: str,
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """删除备份"""
    try:
        success = await backup_manager.delete_backup(backup_id)
        if not success:
            raise HTTPException(status_code=404, detail="备份不存在")
        
        return {
            "backup_id": backup_id,
            "message": "备份已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除备份失败: {str(e)}")

@router.get("/backup/status")
async def get_backup_status(
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """获取备份状态"""
    try:
        # 获取正在进行的备份任务
        running_backups = db.query(models.BackupRecord).filter(
            models.BackupRecord.status.in_(["pending", "running"])
        ).all()
        
        # 获取正在进行的恢复任务
        running_restores = db.query(models.BackupTask).filter(
            models.BackupTask.status.in_(["pending", "running"])
        ).all()
        
        status_info = {
            "backup_system_ready": True,
            "running_backups": len(running_backups),
            "running_restores": len(running_restores),
            "backup_directory": str(backup_manager.backup_dir),
            "backup_count": len(list(backup_manager.backup_dir.glob("backup_*.zip")))
        }
        
        return BackupStatusResponse(
            status="healthy",
            message="备份系统运行正常",
            progress=0,
            current_operation=None,
            estimated_time_remaining=None
        )
        
    except Exception as e:
        print(f"❌ 获取备份状态失败: {e}")
        return BackupStatusResponse(
            status="error",
            message=f"获取备份状态失败: {str(e)}",
            progress=0,
            current_operation=None,
            estimated_time_remaining=None
        )

@router.post("/backup/cleanup")
async def cleanup_old_backups(
    retention_days: int = 30,
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """清理过期备份"""
    try:
        deleted_count = await backup_manager.cleanup_old_backups(retention_days)
        
        return {
            "deleted_count": deleted_count,
            "retention_days": retention_days,
            "message": f"已清理 {deleted_count} 个过期备份"
        }
        
    except Exception as e:
        print(f"❌ 清理备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理备份失败: {str(e)}")

# 导入必要的模块
import uuid
from datetime import datetime
