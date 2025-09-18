import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class BackupCreateRequest(BaseModel):
    """创建备份请求"""
    backup_type: str = Field(..., description="备份类型: full, main_service, admin_service")
    backup_name: str = Field(..., description="备份名称")
    description: Optional[str] = Field(None, description="备份描述")
    include_files: bool = Field(True, description="是否包含文件")
    compression_level: int = Field(6, description="压缩级别 1-9")

class BackupRestoreRequest(BaseModel):
    """恢复备份请求"""
    restore_type: str = Field(..., description="恢复类型: full, main_service, admin_service")
    confirm: bool = Field(False, description="确认恢复操作")

class BackupScheduleRequest(BaseModel):
    """自动备份配置请求"""
    enabled: bool = Field(True, description="是否启用自动备份")
    frequency: str = Field("daily", description="备份频率: daily, weekly, monthly")
    schedule_time: str = Field("02:00", description="备份时间 HH:MM格式")
    backup_type: str = Field("full", description="备份类型")
    retention_days: int = Field(30, description="保留天数")

class BackupRecordResponse(BaseModel):
    """备份记录响应"""
    id: int
    backup_id: str
    backup_name: str
    backup_type: str
    backup_size: int
    file_path: str
    status: str
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    checksum: Optional[str]
    created_by: Optional[str]

    class Config:
        from_attributes = True

class BackupTaskResponse(BaseModel):
    """备份任务响应"""
    id: int
    task_id: str
    backup_id: Optional[str]
    task_type: str
    status: str
    progress: int
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True

class BackupScheduleResponse(BaseModel):
    """自动备份配置响应"""
    id: int
    schedule_name: str
    enabled: bool
    frequency: str
    schedule_time: str
    backup_type: str
    retention_days: int
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BackupStatusResponse(BaseModel):
    """备份状态响应"""
    status: str
    message: str
    progress: int
    current_operation: Optional[str]
    estimated_time_remaining: Optional[int]

class BackupListResponse(BaseModel):
    """备份列表响应"""
    backups: List[BackupRecordResponse]
    total: int
    page: int
    limit: int
    has_more: bool
