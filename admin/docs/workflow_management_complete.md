# 工作流管理完整功能说明

## 功能概述

YeePay AI 工作流管理系统提供了完整的工作流管理功能，支持从文件系统导入、数据库存储、Web界面管理，以及文件导出等功能。

## 🎯 核心功能

### 1. 工作流导入
- **从主服务导入**: 自动扫描主服务的 `back/workflows` 目录
- **文件批量导入**: 支持批量导入JSON工作流文件
- **智能命名**: 根据文件路径自动生成工作流名称
- **重复检测**: 自动跳过已存在的工作流

### 2. 工作流管理
- **Web界面管理**: 完整的前端管理界面
- **CRUD操作**: 创建、读取、更新、删除工作流
- **文件上传**: 支持直接上传JSON文件
- **实时预览**: 查看工作流JSON内容
- **搜索过滤**: 按名称搜索工作流

### 3. 工作流导出
- **单文件导出**: 导出单个工作流为JSON文件
- **批量导出**: 导出所有工作流到文件系统
- **文件同步**: 与主服务工作流目录同步

## 📁 文件结构

```
admin/
├── backend/
│   ├── init_workflows.py              # 初始化脚本
│   ├── workflow_file_manager.py       # 文件管理器
│   ├── batch_import_workflows.py      # 批量导入脚本
│   ├── routers/workflows.py           # API路由
│   ├── models.py                      # 数据模型
│   └── workflows/                     # 工作流文件存储目录
│       ├── qwen/                      # Qwen工作流
│       ├── flux/                      # Flux工作流
│       # flux1/ 目录已移除，只保留FLUX.1 Kontext
│       ├── gemini/                    # Gemini工作流
│       ├── wan/                       # Wan工作流
│       └── fusion/                    # 融合工作流
└── frontend/
    ├── src/api/workflow.js            # API接口
    └── src/views/WorkflowManagement.vue  # 管理界面
```

## 🚀 使用方法

### 1. 初始化工作流

```bash
# 进入管理后台目录
cd admin/backend

# 运行初始化脚本
python init_workflows.py
```

### 2. 批量导入工作流

```bash
# 运行批量导入脚本
python batch_import_workflows.py
```

### 3. 使用文件管理器

```bash
# 运行交互式文件管理器
python workflow_file_manager.py
```

### 4. 启动管理界面

```bash
# 启动后端服务
python main.py

# 启动前端服务 (另一个终端)
cd admin/frontend
npm run dev
```

## 📊 已导入的工作流

当前系统已导入 **13个工作流**，包括：

### Qwen工作流 (4个)
- `qwen_image_fusion_workflow` - Qwen图像融合工作流
- `qwen_image_generation_workflow` - Qwen图像生成工作流
- `qwen_fusion_2image_fusion` - 2图融合工作流
- `qwen_fusion_3image_fusion` - 3图融合工作流

### Flux Kontext工作流 (4个)
- `flux1_flux_kontext_dev_basic_2` - Flux Kontext基础工作流
- `flux1_flux_redux_model_1_backup` - Flux Kontext单图风格迁移
- `flux1_flux_redux_model_2_backup` - Flux Kontext多图风格融合
- `flux1_flux_redux_model_multilora` - Flux Kontext多图多LoRA工作流

### Gemini工作流 (2个)
- `gemini_api_google_gemini_image` - Gemini API图像生成
- `gemini_gemini_no_image_workflow` - Gemini无图工作流

### 其他工作流 (3个)
- `wan2.2_video_generation_workflow` - Wan视频生成工作流
- `qwen_fusion_2image_fusion_test` - Qwen融合测试工作流
- `qwen_fusion_2image_fusion_test (1)` - Qwen融合测试工作流2

## 🔧 API接口

### 工作流管理API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/admin/workflows/` | 获取工作流列表 |
| POST | `/api/admin/workflows/` | 创建工作流 |
| GET | `/api/admin/workflows/{id}` | 获取单个工作流 |
| PUT | `/api/admin/workflows/{id}` | 更新工作流 |
| DELETE | `/api/admin/workflows/{id}` | 删除工作流 |
| POST | `/api/admin/workflows/upload` | 上传工作流文件 |
| GET | `/api/admin/workflows/{id}/download` | 下载工作流文件 |

### 请求示例

```javascript
// 获取工作流列表
const response = await fetch('/api/admin/workflows/');
const workflows = await response.json();

// 创建工作流
const newWorkflow = {
  name: "测试工作流",
  description: "这是一个测试工作流",
  workflow_json: {
    "1": {
      "inputs": {"text": "test prompt"},
      "class_type": "CLIPTextEncode"
    }
  }
};

const response = await fetch('/api/admin/workflows/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(newWorkflow)
});
```

## 🎨 前端界面功能

### 主要特性
- **响应式设计**: 适配各种屏幕尺寸
- **暗色主题**: 与整体管理后台风格一致
- **实时搜索**: 按名称快速搜索工作流
- **JSON编辑器**: 内置JSON格式化和验证
- **文件上传**: 拖拽上传JSON文件
- **批量操作**: 支持批量导入导出

### 操作流程
1. **查看工作流**: 在列表中浏览所有工作流
2. **创建工作流**: 点击"创建工作流"按钮
3. **编辑工作流**: 点击"编辑"按钮修改内容
4. **上传文件**: 点击"上传工作流文件"按钮
5. **下载工作流**: 点击"下载"按钮保存到本地
6. **删除工作流**: 点击"删除"按钮移除工作流

## 🔄 同步机制

### 主服务同步
- 自动扫描 `back/workflows` 目录
- 递归查找所有JSON文件
- 保持目录结构
- 智能命名规则

### 文件管理
- 支持文件系统与数据库双向同步
- 自动检测孤立文件
- 批量导入导出
- 版本控制支持

## 🛠️ 维护工具

### 1. 初始化脚本
```bash
python init_workflows.py
```
- 从主服务导入所有工作流
- 自动创建数据库表
- 生成详细导入报告

### 2. 文件管理器
```bash
python workflow_file_manager.py
```
- 交互式文件管理
- 支持多种操作模式
- 实时状态显示

### 3. 批量导入
```bash
python batch_import_workflows.py
```
- 一键导入所有工作流
- 自动同步文件系统
- 完整的导入流程

## 📈 性能优化

### 数据库优化
- 索引优化
- 分页查询
- 懒加载

### 前端优化
- 虚拟滚动
- 组件缓存
- 异步加载

### 文件处理
- 流式处理
- 内存优化
- 并发控制

## 🔒 安全考虑

### 数据验证
- JSON格式验证
- 文件大小限制
- 恶意代码检测

### 权限控制
- 管理员认证
- 操作日志
- 审计跟踪

## 🚀 未来扩展

### 计划功能
- [ ] 工作流版本管理
- [ ] 工作流模板库
- [ ] 工作流执行历史
- [ ] 工作流分享功能
- [ ] 批量导入导出
- [ ] 工作流可视化编辑器
- [ ] 工作流性能分析
- [ ] 工作流依赖管理

### 技术改进
- [ ] 微服务架构
- [ ] 容器化部署
- [ ] 自动备份
- [ ] 监控告警
- [ ] 负载均衡

## 📞 技术支持

如有问题或建议，请联系开发团队或查看相关文档。

---

**YeePay AI 工作流管理系统** - 让工作流管理更简单、更高效！
