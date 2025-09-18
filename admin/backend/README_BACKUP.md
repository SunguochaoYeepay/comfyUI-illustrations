# YeePay Admin 数据备份系统

## 📋 功能概述

YeePay Admin 数据备份系统提供了完整的数据备份、恢复和管理功能，支持：

- **手动备份** - 管理员可随时创建备份
- **自动备份** - 定时自动备份系统数据
- **数据恢复** - 从备份文件恢复系统数据
- **备份管理** - 备份文件的查看、下载、删除

## 🚀 快速开始

### 1. 启动服务

```bash
# 启动Admin后端服务
cd admin/backend
python main.py

# 启动前端服务
cd admin/frontend
npm run dev
```

### 2. 访问备份管理

1. 打开浏览器访问 `http://localhost:5173`
2. 登录Admin系统
3. 点击左侧菜单的"数据备份"
4. 进入备份管理页面

### 3. 创建备份

1. 在"创建备份"卡片中：
   - 输入备份名称
   - 选择备份类型（全量/主服务/Admin服务）
   - 设置压缩级别
   - 点击"创建备份"

2. 系统将在后台执行备份任务
3. 备份完成后会显示在"备份列表"中

### 4. 恢复备份

1. 在"恢复备份"卡片中：
   - 选择要恢复的备份
   - 选择恢复类型
   - 点击"开始恢复"
   - 确认恢复操作

2. 系统将在后台执行恢复任务

### 5. 自动备份设置

1. 在"自动备份设置"卡片中：
   - 点击"添加自动备份"
   - 设置备份频率（每日/每周/每月）
   - 设置执行时间
   - 设置保留天数
   - 启用调度

## 🔧 技术架构

### 后端组件

```
admin/backend/
├── routers/
│   ├── backup.py              # 备份API路由
│   └── backup_schedule.py     # 自动备份API路由
├── core/
│   ├── backup_manager.py      # 核心备份管理器
│   └── backup_scheduler.py    # 自动备份调度器
├── models/
│   └── backup_models.py       # 备份数据模型
└── schemas/
    └── backup_schemas.py      # 备份API模型
```

### 前端组件

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

## 📡 API 接口

### 备份管理接口

- `POST /api/admin/backup/create` - 创建备份
- `GET /api/admin/backup/list` - 获取备份列表
- `GET /api/admin/backup/download/{backup_id}` - 下载备份
- `POST /api/admin/backup/restore/{backup_id}` - 恢复备份
- `DELETE /api/admin/backup/{backup_id}` - 删除备份
- `GET /api/admin/backup/status` - 获取备份状态

### 自动备份接口

- `POST /api/admin/backup/schedule` - 创建自动备份调度
- `GET /api/admin/backup/schedule` - 获取调度列表
- `PUT /api/admin/backup/schedule/{id}` - 更新调度配置
- `DELETE /api/admin/backup/schedule/{id}` - 删除调度配置

## 🗂️ 备份数据范围

### 主服务数据
- `tasks.db` - 任务记录、收藏数据
- `uploads/` - 用户上传的图片
- `outputs/` - 生成的图片/视频
- `workflows/` - 工作流配置文件
- `thumbnails/` - 缩略图缓存

### Admin服务数据
- `admin.db` - 用户、工作流、模型、LoRA配置
- `uploads/` - 管理端上传文件
- `outputs/` - 管理端输出文件

### 系统配置
- `docker-compose.yml` - Docker编排文件
- `env.production` - 环境变量
- `nginx/` - Nginx配置

## 🔒 安全特性

- **权限控制** - 基于角色的备份权限管理
- **数据验证** - SHA-256校验和验证
- **操作确认** - 恢复操作需要二次确认
- **服务停止** - 恢复前自动停止相关服务

## 🧪 测试

### 运行测试脚本

```bash
cd admin/backend
python test_backup.py
```

### 手动测试

1. 创建测试备份
2. 验证备份文件完整性
3. 测试恢复功能
4. 验证数据一致性

## 📊 监控和日志

### 备份监控

- 备份成功率
- 备份完成时间
- 备份文件大小
- 存储空间使用率

### 日志记录

```python
# 备份操作日志
logger.info(f"Backup started: {backup_id}")
logger.info(f"Backup completed: {backup_id}")
logger.error(f"Backup failed: {backup_id}")

# 恢复操作日志
logger.info(f"Restore started: {backup_id}")
logger.info(f"Restore completed: {backup_id}")
logger.error(f"Restore failed: {backup_id}")
```

## 🚨 故障排除

### 常见问题

1. **备份失败**
   - 检查磁盘空间
   - 检查文件权限
   - 查看错误日志

2. **恢复失败**
   - 验证备份文件完整性
   - 检查服务状态
   - 确认恢复类型

3. **自动备份不执行**
   - 检查调度器状态
   - 验证调度配置
   - 查看调度器日志

### 日志位置

- 备份日志：控制台输出
- 错误日志：FastAPI错误日志
- 调度器日志：控制台输出

## 🔄 维护操作

### 清理过期备份

```bash
# 通过API清理
curl -X POST "http://localhost:8888/api/admin/backup/cleanup?retention_days=30"

# 手动清理
rm -rf backups/backup_*.zip
```

### 启动调度器服务

```bash
cd admin/backend
python start_backup_scheduler.py
```

## 📞 技术支持

如有问题，请查看：

1. 备份系统文档：`admin/docs/data_backup_system.md`
2. 错误日志输出
3. API响应状态码

---

*YeePay Admin 数据备份系统 v1.0.0*
