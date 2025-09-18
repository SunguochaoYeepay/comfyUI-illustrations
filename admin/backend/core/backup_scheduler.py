#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动备份调度器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import SessionLocal
from core.backup_manager import BackupManager
import models

class BackupScheduler:
    """自动备份调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.backup_manager = BackupManager()
        self.is_running = False
    
    async def start(self):
        """启动调度器"""
        if self.is_running:
            print("⚠️ 备份调度器已在运行")
            return
        
        print("🔄 启动自动备份调度器...")
        
        try:
            # 加载现有的调度配置
            await self._load_schedules()
            
            # 启动调度器
            self.scheduler.start()
            self.is_running = True
            
            print("✅ 自动备份调度器启动成功")
            
        except Exception as e:
            print(f"❌ 启动备份调度器失败: {e}")
            raise e
    
    async def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        print("⏹️ 停止自动备份调度器...")
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            print("✅ 自动备份调度器已停止")
            
        except Exception as e:
            print(f"❌ 停止备份调度器失败: {e}")
    
    async def _load_schedules(self):
        """加载调度配置"""
        db = SessionLocal()
        try:
            schedules = db.query(models.BackupSchedule).filter(
                models.BackupSchedule.enabled == True
            ).all()
            
            for schedule in schedules:
                await self._add_schedule(schedule)
                
            print(f"📅 已加载 {len(schedules)} 个备份调度")
            
        finally:
            db.close()
    
    async def _add_schedule(self, schedule: models.BackupSchedule):
        """添加调度任务"""
        try:
            # 创建触发器
            trigger = self._create_trigger(schedule)
            
            # 添加任务
            job_id = f"backup_schedule_{schedule.id}"
            
            self.scheduler.add_job(
                func=self._execute_scheduled_backup,
                trigger=trigger,
                args=[schedule.id],
                id=job_id,
                name=f"自动备份-{schedule.schedule_name}",
                replace_existing=True,
                max_instances=1
            )
            
            print(f"📅 已添加调度任务: {schedule.schedule_name}")
            
        except Exception as e:
            print(f"❌ 添加调度任务失败: {e}")
    
    def _create_trigger(self, schedule: models.BackupSchedule) -> CronTrigger:
        """创建定时触发器"""
        if schedule.frequency == "daily":
            # 每日执行
            hour, minute = schedule.schedule_time.split(":")
            return CronTrigger(hour=int(hour), minute=int(minute))
        
        elif schedule.frequency == "weekly":
            # 每周执行（周一）
            hour, minute = schedule.schedule_time.split(":")
            return CronTrigger(day_of_week=0, hour=int(hour), minute=int(minute))
        
        elif schedule.frequency == "monthly":
            # 每月执行（1号）
            hour, minute = schedule.schedule_time.split(":")
            return CronTrigger(day=1, hour=int(hour), minute=int(minute))
        
        else:
            raise ValueError(f"不支持的调度频率: {schedule.frequency}")
    
    async def _execute_scheduled_backup(self, schedule_id: int):
        """执行定时备份"""
        db = SessionLocal()
        try:
            # 获取调度配置
            schedule = db.query(models.BackupSchedule).filter(
                models.BackupSchedule.id == schedule_id
            ).first()
            
            if not schedule or not schedule.enabled:
                print(f"⚠️ 调度配置不存在或已禁用: {schedule_id}")
                return
            
            print(f"🔄 开始执行定时备份: {schedule.schedule_name}")
            
            # 生成备份名称
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"auto_{schedule.schedule_name}_{timestamp}"
            
            # 创建备份记录
            backup_id = str(uuid.uuid4())
            backup_record = models.BackupRecord(
                backup_id=backup_id,
                backup_name=backup_name,
                backup_type=schedule.backup_type,
                backup_size=0,
                file_path="",
                status="pending",
                description=f"自动备份 - {schedule.schedule_name}",
                created_by="system"
            )
            
            db.add(backup_record)
            db.commit()
            db.refresh(backup_record)
            
            try:
                # 执行备份
                backup_record.status = "running"
                db.commit()
                
                actual_backup_id = await self.backup_manager.create_backup(
                    backup_type=schedule.backup_type,
                    backup_name=backup_name,
                    description=f"自动备份 - {schedule.schedule_name}",
                    include_files=True  # 自动备份默认包含文件
                )
                
                # 更新备份记录
                backup_file = self.backup_manager._find_backup_file(actual_backup_id)
                if backup_file:
                    backup_record.backup_size = backup_file.stat().st_size
                    backup_record.file_path = str(backup_file)
                    backup_record.status = "completed"
                    backup_record.completed_at = datetime.now()
                    backup_record.checksum = await self.backup_manager._calculate_checksum(backup_file)
                
                # 更新调度记录
                schedule.last_run = datetime.now()
                schedule.next_run = self._calculate_next_run(schedule)
                
                # 清理过期备份
                await self.backup_manager.cleanup_old_backups(schedule.retention_days)
                
                db.commit()
                
                print(f"✅ 定时备份完成: {schedule.schedule_name}")
                
            except Exception as e:
                print(f"❌ 定时备份失败: {e}")
                backup_record.status = "failed"
                backup_record.completed_at = datetime.now()
                db.commit()
                raise e
                
        finally:
            db.close()
    
    def _calculate_next_run(self, schedule: models.BackupSchedule) -> datetime:
        """计算下次运行时间"""
        now = datetime.now()
        
        if schedule.frequency == "daily":
            # 明天同一时间
            hour, minute = schedule.schedule_time.split(":")
            next_run = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif schedule.frequency == "weekly":
            # 下周一同一时间
            hour, minute = schedule.schedule_time.split(":")
            days_ahead = 0 - now.weekday()  # 0是周一
            if days_ahead <= 0:  # 如果今天是周一或之后
                days_ahead += 7
            next_run = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0) + timedelta(days=days_ahead)
            return next_run
        
        elif schedule.frequency == "monthly":
            # 下个月1号同一时间
            hour, minute = schedule.schedule_time.split(":")
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1, hour=int(hour), minute=int(minute), second=0, microsecond=0)
            else:
                next_month = now.replace(month=now.month + 1, day=1, hour=int(hour), minute=int(minute), second=0, microsecond=0)
            return next_month
        
        return now + timedelta(days=1)
    
    async def create_schedule(self, schedule_data: dict) -> models.BackupSchedule:
        """创建新的调度配置"""
        db = SessionLocal()
        try:
            schedule = models.BackupSchedule(
                schedule_name=schedule_data["schedule_name"],
                enabled=schedule_data["enabled"],
                frequency=schedule_data["frequency"],
                schedule_time=schedule_data["schedule_time"],
                backup_type=schedule_data["backup_type"],
                retention_days=schedule_data["retention_days"]
            )
            
            db.add(schedule)
            db.commit()
            db.refresh(schedule)
            
            # 如果调度器正在运行且调度已启用，添加任务
            if self.is_running and schedule.enabled:
                await self._add_schedule(schedule)
            
            return schedule
            
        finally:
            db.close()
    
    async def update_schedule(self, schedule_id: int, schedule_data: dict) -> models.BackupSchedule:
        """更新调度配置"""
        db = SessionLocal()
        try:
            schedule = db.query(models.BackupSchedule).filter(
                models.BackupSchedule.id == schedule_id
            ).first()
            
            if not schedule:
                raise ValueError(f"调度配置不存在: {schedule_id}")
            
            # 更新字段
            for key, value in schedule_data.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)
            
            schedule.updated_at = datetime.now()
            db.commit()
            db.refresh(schedule)
            
            # 重新加载调度任务
            if self.is_running:
                job_id = f"backup_schedule_{schedule.id}"
                self.scheduler.remove_job(job_id)
                
                if schedule.enabled:
                    await self._add_schedule(schedule)
            
            return schedule
            
        finally:
            db.close()
    
    async def delete_schedule(self, schedule_id: int) -> bool:
        """删除调度配置"""
        db = SessionLocal()
        try:
            schedule = db.query(models.BackupSchedule).filter(
                models.BackupSchedule.id == schedule_id
            ).first()
            
            if not schedule:
                return False
            
            # 移除调度任务
            if self.is_running:
                job_id = f"backup_schedule_{schedule.id}"
                self.scheduler.remove_job(job_id)
            
            # 删除数据库记录
            db.delete(schedule)
            db.commit()
            
            return True
            
        finally:
            db.close()
    
    async def get_schedules(self) -> List[models.BackupSchedule]:
        """获取所有调度配置"""
        db = SessionLocal()
        try:
            return db.query(models.BackupSchedule).all()
        finally:
            db.close()

# 全局调度器实例
backup_scheduler = BackupScheduler()

# 导入必要的模块
import uuid
