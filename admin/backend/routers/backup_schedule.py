#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动备份调度API路由
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from dependencies import get_current_user
from schemas.backup_schemas import BackupScheduleRequest, BackupScheduleResponse
from core.backup_scheduler import backup_scheduler
import models
import schemas_legacy as schemas

router = APIRouter()

@router.post("/backup/schedule", response_model=BackupScheduleResponse)
async def create_backup_schedule(
    request: BackupScheduleRequest,
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """创建自动备份调度"""
    try:
        schedule_data = {
            "schedule_name": f"自动备份_{request.backup_type}",
            "enabled": request.enabled,
            "frequency": request.frequency,
            "schedule_time": request.schedule_time,
            "backup_type": request.backup_type,
            "retention_days": request.retention_days
        }
        
        schedule = await backup_scheduler.create_schedule(schedule_data)
        
        return BackupScheduleResponse(
            id=schedule.id,
            schedule_name=schedule.schedule_name,
            enabled=schedule.enabled,
            frequency=schedule.frequency,
            schedule_time=schedule.schedule_time,
            backup_type=schedule.backup_type,
            retention_days=schedule.retention_days,
            last_run=schedule.last_run,
            next_run=schedule.next_run,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
        
    except Exception as e:
        print(f"❌ 创建备份调度失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建备份调度失败: {str(e)}")

@router.get("/backup/schedule", response_model=List[BackupScheduleResponse])
async def get_backup_schedules(
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """获取自动备份调度列表"""
    try:
        schedules = await backup_scheduler.get_schedules()
        
        return [
            BackupScheduleResponse(
                id=schedule.id,
                schedule_name=schedule.schedule_name,
                enabled=schedule.enabled,
                frequency=schedule.frequency,
                schedule_time=schedule.schedule_time,
                backup_type=schedule.backup_type,
                retention_days=schedule.retention_days,
                last_run=schedule.last_run,
                next_run=schedule.next_run,
                created_at=schedule.created_at,
                updated_at=schedule.updated_at
            )
            for schedule in schedules
        ]
        
    except Exception as e:
        print(f"❌ 获取备份调度失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取备份调度失败: {str(e)}")

@router.put("/backup/schedule/{schedule_id}", response_model=BackupScheduleResponse)
async def update_backup_schedule(
    schedule_id: int,
    request: BackupScheduleRequest,
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """更新自动备份调度"""
    try:
        schedule_data = {
            "enabled": request.enabled,
            "frequency": request.frequency,
            "schedule_time": request.schedule_time,
            "backup_type": request.backup_type,
            "retention_days": request.retention_days
        }
        
        schedule = await backup_scheduler.update_schedule(schedule_id, schedule_data)
        
        return BackupScheduleResponse(
            id=schedule.id,
            schedule_name=schedule.schedule_name,
            enabled=schedule.enabled,
            frequency=schedule.frequency,
            schedule_time=schedule.schedule_time,
            backup_type=schedule.backup_type,
            retention_days=schedule.retention_days,
            last_run=schedule.last_run,
            next_run=schedule.next_run,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at
        )
        
    except Exception as e:
        print(f"❌ 更新备份调度失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新备份调度失败: {str(e)}")

@router.delete("/backup/schedule/{schedule_id}")
async def delete_backup_schedule(
    schedule_id: int,
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """删除自动备份调度"""
    try:
        success = await backup_scheduler.delete_schedule(schedule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="调度配置不存在")
        
        return {
            "schedule_id": schedule_id,
            "message": "调度配置已删除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除备份调度失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除备份调度失败: {str(e)}")

@router.post("/backup/scheduler/start")
async def start_backup_scheduler(
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """启动备份调度器"""
    try:
        await backup_scheduler.start()
        
        return {
            "message": "备份调度器已启动"
        }
        
    except Exception as e:
        print(f"❌ 启动备份调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动备份调度器失败: {str(e)}")

@router.post("/backup/scheduler/stop")
async def stop_backup_scheduler(
    db: Session = Depends(get_db)
    # current_user: schemas.AdminUser = Depends(get_current_user)  # 暂时移除认证
):
    """停止备份调度器"""
    try:
        await backup_scheduler.stop()
        
        return {
            "message": "备份调度器已停止"
        }
        
    except Exception as e:
        print(f"❌ 停止备份调度器失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止备份调度器失败: {str(e)}")

@router.get("/backup/scheduler/status")
async def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: schemas.AdminUser = Depends(get_current_user)
):
    """获取调度器状态"""
    try:
        return {
            "is_running": backup_scheduler.is_running,
            "active_jobs": len(backup_scheduler.scheduler.get_jobs()) if backup_scheduler.is_running else 0,
            "message": "调度器运行正常" if backup_scheduler.is_running else "调度器已停止"
        }
        
    except Exception as e:
        print(f"❌ 获取调度器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取调度器状态失败: {str(e)}")
