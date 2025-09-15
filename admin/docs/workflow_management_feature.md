# 工作流管理功能

## 功能概述

工作流管理功能允许管理员创建、编辑、删除和下载ComfyUI工作流JSON文件。这个功能完全集成到YeePay AI管理后台中。

## 后端API

### 端点列表

- `POST /api/admin/workflows/` - 创建工作流
- `GET /api/admin/workflows/` - 获取工作流列表
- `GET /api/admin/workflows/{id}` - 获取单个工作流
- `PUT /api/admin/workflows/{id}` - 更新工作流
- `DELETE /api/admin/workflows/{id}` - 删除工作流
- `POST /api/admin/workflows/upload` - 上传工作流JSON文件
- `GET /api/admin/workflows/{id}/download` - 下载工作流JSON文件

### 数据模型

```sql
CREATE TABLE workflows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    workflow_json JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 前端功能

### 主要特性

1. **工作流列表展示**
   - 显示工作流ID、名称、描述、节点数量、创建时间
   - 支持按名称搜索
   - 分页显示

2. **创建工作流**
   - 手动输入工作流名称、描述和JSON内容
   - JSON格式验证和格式化
   - 实时JSON语法检查

3. **编辑工作流**
   - 修改工作流名称、描述和JSON内容
   - 保持原有数据完整性

4. **文件上传**
   - 支持上传JSON格式的工作流文件
   - 自动解析JSON内容
   - 可选择自定义名称和描述

5. **工作流查看**
   - 模态框展示完整工作流信息
   - 格式化显示JSON内容
   - 支持复制和查看

6. **工作流下载**
   - 一键下载工作流为JSON文件
   - 自动命名文件

7. **删除工作流**
   - 确认删除机制
   - 安全删除操作

### 用户界面

- **响应式设计**: 适配不同屏幕尺寸
- **暗色主题**: 与整体管理后台风格一致
- **直观操作**: 清晰的按钮和操作流程
- **错误处理**: 友好的错误提示和验证

## 使用流程

### 创建工作流

1. 点击"创建工作流"按钮
2. 输入工作流名称和描述
3. 在JSON编辑器中输入或粘贴工作流JSON
4. 点击"确定"保存

### 上传工作流文件

1. 点击"上传工作流文件"按钮
2. 选择JSON文件
3. 可选：输入自定义名称和描述
4. 点击"确定"上传

### 编辑工作流

1. 在工作流列表中点击"编辑"
2. 修改名称、描述或JSON内容
3. 点击"确定"保存更改

### 下载工作流

1. 在工作流列表中点击"下载"
2. 文件将自动下载到本地

## 技术实现

### 后端技术栈
- FastAPI
- SQLAlchemy ORM
- SQLite数据库
- Pydantic数据验证

### 前端技术栈
- Vue 3 Composition API
- Ant Design Vue 4.x
- Vue Router
- Axios HTTP客户端

### 文件结构

```
admin/
├── backend/
│   ├── routers/workflows.py      # 工作流API路由
│   ├── crud.py                   # 数据库操作
│   ├── models.py                 # 数据模型
│   └── schemas_legacy.py         # 数据验证模式
└── frontend/
    ├── src/
    │   ├── api/workflow.js       # API接口
    │   ├── views/WorkflowManagement.vue  # 主页面组件
    │   ├── router/index.js       # 路由配置
    │   └── layouts/BasicLayout.vue  # 布局组件
```

## 测试

### 后端测试
- 完整的CRUD操作测试
- 文件上传下载测试
- API响应验证

### 前端测试
- 组件渲染测试
- 用户交互测试
- API集成测试

## 部署说明

1. 确保后端服务运行在端口8888
2. 前端开发服务器运行在端口5173
3. 数据库自动创建workflows表
4. 所有API端点已注册到主应用

## 注意事项

- JSON格式验证：确保上传的JSON文件格式正确
- 文件大小限制：建议工作流JSON文件不超过10MB
- 权限控制：当前版本未启用认证，生产环境需要添加权限验证
- 数据备份：建议定期备份工作流数据

## 未来扩展

- 工作流版本管理
- 工作流模板库
- 工作流执行历史
- 工作流分享功能
- 批量导入导出
