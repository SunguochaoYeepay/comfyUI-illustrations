# YeePay Admin 数据备份系统设计方案

## 📋 项目概述

YeePay Admin 数据备份系统是一个完整的自动化备份解决方案，提供主服务和Admin服务的数据备份、恢复和管理功能。系统支持自动定时备份和手动备份两种模式，确保系统数据的安全性和可恢复性。

## 🎯 功能目标

### 核心功能
- **自动备份** - 定时自动备份系统数据
- **手动备份** - 管理员手动触发备份
- **数据恢复** - 从备份文件恢复系统数据
- **备份管理** - 备份文件的查看、下载、删除
- **完整性验证** - 备份数据完整性检查
- **增量备份** - 支持增量备份减少存储空间

### 业务价值
- 数据安全保障
- 灾难恢复能力
- 系统迁移支持
- 版本回滚能力

## 🗂️ 备份数据范围

### 主服务数据 (back/)
```
back/
├── tasks.db                    # 任务记录、收藏数据
├── uploads/                    # 用户上传的图片文件
├── outputs/                    # 生成的图片/视频文件
├── workflows/                  # 工作流配置文件
├── thumbnails/                 # 缩略图缓存
└── config/                     # 配置文件
```

### Admin服务数据 (admin/backend/)
```
admin/backend/
├── admin.db                    # 用户、工作流、模型、LoRA配置
├── uploads/                    # 管理端上传文件
├── outputs/                    # 管理端输出文件
└── config/                     # Admin配置
```

### 系统配置文件
```
├── docker-compose.yml          # Docker编排文件
├── docker-compose.prod.yml     # 生产环境配置
├── env.production              # 环境变量
└── nginx/                      # Nginx配置
```

## 🏗️ 技术架构

### 后端架构
```
admin/backend/
├── routers/
│   └── backup.py              # 备份API路由
├── core/
│   ├── backup_manager.py      # 核心备份管理器
│   ├── backup_scheduler.py    # 自动备份调度器
│   └── backup_validator.py    # 备份验证器
├── models/
│   └── backup_models.py       # 备份数据模型
└── schemas/
    └── backup_schemas.py      # 备份API模型
```

### 前端架构
```
admin/frontend/src/
├── views/
│   └── BackupManagement.vue   # 备份管理主页面
├── components/
│   ├── BackupCreate.vue       # 创建备份组件
│   ├── BackupList.vue         # 备份列表组件
│   ├── BackupRestore.vue      # 恢复备份组件
│   └── BackupSettings.vue     # 备份设置组件
└── utils/
    └── backupApi.js           # 备份API调用
```

## 📡 API 接口设计

### 备份管理接口

#### 创建备份
```http
POST /api/backup/create
Content-Type: application/json

{
  "backup_type": "full|main_service|admin_service",
  "backup_name": "backup_2024_01_15",
  "description": "手动备份描述",
  "include_files": true,
  "compression_level": 6
}
```

#### 获取备份列表
```http
GET /api/backup/list?page=1&limit=20&type=all&status=all
```

#### 下载备份
```http
GET /api/backup/download/{backup_id}
```

#### 恢复备份
```http
POST /api/backup/restore/{backup_id}
Content-Type: application/json

{
  "restore_type": "full|main_service|admin_service",
  "confirm": true
}
```

#### 删除备份
```http
DELETE /api/backup/{backup_id}
```

#### 获取备份状态
```http
GET /api/backup/status
```

### 自动备份接口

#### 设置自动备份
```http
POST /api/backup/schedule
Content-Type: application/json

{
  "enabled": true,
  "frequency": "daily|weekly|monthly",
  "time": "02:00",
  "retention_days": 30,
  "backup_type": "full"
}
```

#### 获取自动备份配置
```http
GET /api/backup/schedule
```

## 🗄️ 数据库设计

### 备份记录表 (backup_records)
```sql
CREATE TABLE backup_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_id VARCHAR(36) UNIQUE NOT NULL,
    backup_name VARCHAR(255) NOT NULL,
    backup_type VARCHAR(50) NOT NULL,
    backup_size BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    checksum VARCHAR(64),
    created_by VARCHAR(50),
    metadata JSON
);
```

### 备份任务表 (backup_tasks)
```sql
CREATE TABLE backup_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id VARCHAR(36) UNIQUE NOT NULL,
    backup_id VARCHAR(36),
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    progress INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (backup_id) REFERENCES backup_records(backup_id)
);
```

### 自动备份配置表 (backup_schedules)
```sql
CREATE TABLE backup_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    frequency VARCHAR(20) NOT NULL,
    schedule_time VARCHAR(10) NOT NULL,
    backup_type VARCHAR(50) NOT NULL,
    retention_days INTEGER DEFAULT 30,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 核心组件实现

### 备份管理器 (BackupManager)

```python
class BackupManager:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.temp_dir = Path("temp_backups")
        
    async def create_backup(self, backup_type: str, backup_name: str) -> str:
        """创建备份"""
        backup_id = str(uuid.uuid4())
        
        # 1. 验证备份类型
        if backup_type not in ["full", "main_service", "admin_service"]:
            raise ValueError("Invalid backup type")
            
        # 2. 创建备份目录
        backup_path = self.backup_dir / f"{backup_name}_{backup_id}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 3. 执行备份
        if backup_type == "full":
            await self._backup_main_service(backup_path)
            await self._backup_admin_service(backup_path)
        elif backup_type == "main_service":
            await self._backup_main_service(backup_path)
        elif backup_type == "admin_service":
            await self._backup_admin_service(backup_path)
            
        # 4. 压缩备份
        archive_path = await self._compress_backup(backup_path, backup_id)
        
        # 5. 验证备份完整性
        checksum = await self._calculate_checksum(archive_path)
        
        # 6. 清理临时文件
        shutil.rmtree(backup_path)
        
        return backup_id
    
    async def restore_backup(self, backup_id: str, restore_type: str) -> bool:
        """恢复备份"""
        # 1. 验证备份文件
        backup_path = await self._validate_backup(backup_id)
        
        # 2. 停止相关服务
        await self._stop_services()
        
        # 3. 执行恢复
        try:
            await self._extract_backup(backup_path)
            await self._restore_databases(restore_type)
            await self._restore_files(restore_type)
            
            # 4. 重启服务
            await self._restart_services()
            
            return True
        except Exception as e:
            # 恢复失败，回滚
            await self._rollback_restore()
            raise e
```

### 自动备份调度器 (BackupScheduler)

```python
class BackupScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def start_scheduler(self):
        """启动自动备份调度器"""
        schedules = await self._get_active_schedules()
        
        for schedule in schedules:
            self.scheduler.add_job(
                func=self._execute_scheduled_backup,
                trigger=self._get_trigger(schedule),
                args=[schedule.id],
                id=f"backup_{schedule.id}",
                replace_existing=True
            )
        
        self.scheduler.start()
    
    async def _execute_scheduled_backup(self, schedule_id: int):
        """执行定时备份"""
        schedule = await self._get_schedule(schedule_id)
        
        try:
            backup_manager = BackupManager()
            backup_name = f"auto_{schedule.schedule_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_id = await backup_manager.create_backup(
                backup_type=schedule.backup_type,
                backup_name=backup_name
            )
            
            # 清理过期备份
            await self._cleanup_old_backups(schedule.retention_days)
            
        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")
```

## 🎨 用户界面设计

### 主备份页面布局
```
┌─────────────────────────────────────────────────────────┐
│  数据备份管理                                           │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  创建备份   │  │  备份列表   │  │  恢复备份   │    │
│  │             │  │             │  │             │    │
│  │ [手动备份]  │  │ [查看历史]  │  │ [选择恢复]  │    │
│  │ [自动备份]  │  │ [下载备份]  │  │ [确认恢复]  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├─────────────────────────────────────────────────────────┤
│  备份设置                                               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 自动备份: [开启] [关闭]                             │ │
│  │ 备份频率: [每日] [每周] [每月]                       │ │
│  │ 备份时间: [02:00]                                   │ │
│  │ 保留天数: [30天]                                    │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 备份进度显示
```
┌─────────────────────────────────────────────────────────┐
│  备份进度                                               │
├─────────────────────────────────────────────────────────┤
│  备份ID: backup_2024_01_15_140523                       │
│  备份类型: 全量备份                                      │
│  进度: ████████████████████ 85%                         │
│  状态: 正在备份文件...                                   │
│  预计剩余时间: 2分钟                                     │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ 当前操作: 压缩备份文件                               │ │
│  │ 已处理: 1,245 个文件                                 │ │
│  │ 已压缩: 2.3 GB                                       │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 🔒 安全考虑

### 数据安全
- **备份加密** - 使用AES-256加密备份文件
- **访问控制** - 基于角色的备份权限管理
- **完整性验证** - SHA-256校验和验证
- **安全传输** - HTTPS传输备份文件

### 操作安全
- **服务停止** - 备份前停止相关服务防止数据不一致
- **原子操作** - 备份和恢复操作的原子性保证
- **回滚机制** - 恢复失败时的自动回滚
- **操作日志** - 详细的备份和恢复操作日志

### 存储安全
- **多副本存储** - 支持本地和远程存储
- **定期清理** - 自动清理过期备份文件
- **存储验证** - 定期验证备份文件完整性

## 📊 监控和日志

### 备份监控指标
- 备份成功率
- 备份完成时间
- 备份文件大小
- 存储空间使用率
- 恢复成功率

### 日志记录
```python
# 备份操作日志
logger.info(f"Backup started: {backup_id}, type: {backup_type}")
logger.info(f"Backup completed: {backup_id}, size: {backup_size}")
logger.error(f"Backup failed: {backup_id}, error: {error_message}")

# 恢复操作日志
logger.info(f"Restore started: {backup_id}, type: {restore_type}")
logger.info(f"Restore completed: {backup_id}")
logger.error(f"Restore failed: {backup_id}, error: {error_message}")
```

## 🚀 部署和配置

### 环境变量配置
```bash
# 备份配置
BACKUP_DIR=/app/backups
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESSION_LEVEL=6
BACKUP_ENCRYPTION_KEY=your_encryption_key

# 自动备份配置
AUTO_BACKUP_ENABLED=true
AUTO_BACKUP_FREQUENCY=daily
AUTO_BACKUP_TIME=02:00
AUTO_BACKUP_TYPE=full
```

### Docker配置
```yaml
# docker-compose.yml
services:
  admin-backend:
    volumes:
      - ./backups:/app/backups
      - ./temp_backups:/app/temp_backups
    environment:
      - BACKUP_DIR=/app/backups
      - AUTO_BACKUP_ENABLED=true
```

## 📈 性能优化

### 备份性能优化
- **并行备份** - 多线程并行处理文件
- **增量备份** - 只备份变更的文件
- **压缩优化** - 选择合适的压缩级别
- **流式处理** - 大文件流式处理避免内存溢出

### 存储优化
- **去重存储** - 相同文件只存储一次
- **分层存储** - 热数据和冷数据分层存储
- **压缩存储** - 高效压缩算法
- **清理策略** - 智能清理过期备份

## 🔄 维护和升级

### 定期维护任务
- 备份文件完整性检查
- 过期备份文件清理
- 存储空间监控
- 性能指标分析

### 升级策略
- 向后兼容的备份格式
- 平滑的升级路径
- 数据迁移工具
- 回滚机制

## 📋 实施计划

### 第一阶段：基础功能 (2周)
- [ ] 备份管理器核心功能
- [ ] 基础API接口
- [ ] 手动备份功能
- [ ] 备份列表和下载

### 第二阶段：自动备份 (1周)
- [ ] 自动备份调度器
- [ ] 定时任务管理
- [ ] 备份设置页面
- [ ] 备份历史管理

### 第三阶段：恢复功能 (1周)
- [ ] 备份恢复功能
- [ ] 恢复确认机制
- [ ] 服务停止和重启
- [ ] 恢复进度显示

### 第四阶段：优化和完善 (1周)
- [ ] 性能优化
- [ ] 安全加固
- [ ] 监控和日志
- [ ] 文档完善

## 📞 技术支持

### 常见问题
1. **备份失败** - 检查磁盘空间和权限
2. **恢复失败** - 验证备份文件完整性
3. **自动备份不执行** - 检查调度器配置
4. **备份文件过大** - 调整压缩级别或清理策略

### 联系信息
- 技术支持：admin@yeepay.com
- 文档更新：2024-01-15
- 版本：v1.0.0

---

*本文档详细描述了YeePay Admin数据备份系统的设计方案，包括技术架构、功能实现、安全考虑和部署方案。*
