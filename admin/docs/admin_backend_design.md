# YeePay AI - 后台管理系统设计文档

## 1. 引言

为了增强 YeePay AI 图像生成平台的管理和监控能力，需要一个专门的后台管理系统。该系统将为管理员提供监控系统状态、管理用户生成的内容和任务、控制 AI 模型以及配置应用程序的工具。本文档概述了此后台管理系统的建议功能和高级设计。

## 2. 核心功能

后台管理系统将是一个独立于主用户界面的应用，并包含以下模块：

### 2.1. 首页 (Dashboard)
一个用于快速浏览系统监控信息的中心枢纽。

- **系统概况:** FastAPI 后端的实时状态，以及与 ComfyUI 引擎的连接状态。
- **任务队列:** 队列中当前的任务数量（待处理、处理中），以及平均任务完成时间。
- **核心统计:** 生成的图像总数、处理的任务总数、存储使用情况等关键指标。

### 2.2. 任务管理 (Task Management)
对所有图像和视频生成任务的全面控制。

- **任务列表:** 查看提交到系统的所有任务的分页列表，包含任务ID、状态、创建时间、提示等关键信息。
- **筛选和搜索:** 按状态筛选任务，或按任务ID、提示中的关键字进行搜索。
- **操作:** 取消待处理或正在运行的任务，重试失败的任务，并查看详细的任务信息（包括工作流JSON和错误日志）。

### 2.3. 图片管理 (Image Management)
用于管理所有AI生成内容的工具。

- **图片浏览器:** 所有生成输出的图库视图。
- **操作:** 删除选定的图像以释放存储空间，并查看每个文件的元数据（如提示、种子等）。

### 2.4. 灵感管理 (Inspiration Management)
管理用户收藏的图片（即“灵感”）。

- **收藏列表:** 查看所有被用户标记为“灵感”或“收藏”的图片。
- **信息展示:** 显示图片、收藏者以及收藏时间。
- **操作:** 管理员可以移除某个图片的收藏状态。

### 2.5. 模型管理 (Model Management)
对核心的Checkpoint模型进行集中管理。

- **模型列表:** 列出所有可用的Checkpoint模型。
- **操作:** 上传新的Checkpoint模型，或删除现有模型。
- **元数据:** 显示模型的文件名、大小等信息。

### 2.6. LoRA管理 (Lora Management)

专门用于管理LoRA模型。

- **LoRA列表:** 列出所有可用的LoRA模型（`.safetensors` 文件）。
- **操作:** 上传新的LoRA模型，或删除现有模型。
- **元数据:** 显示LoRA模型的元数据。

### 2.7. 生图流管理 (Workflow Management)
管理和配置 ComfyUI 工作流。

- **工作流列表:** 展示所有已上传的 ComfyUI 工作流（JSON 文件）。
- **操作:** 上传新的工作流，下载或删除现有的工作流。
- **配置:** 允许对工作流的特定节点参数进行配置和保存。

### 2.8. 提示词管理 (Prompt Management)
用于管理常用的正面和负面提示词。

- **提示词列表:** 分别展示正面和负面提示词。
- **操作:** 添加、编辑或删除提示词。
- **分类:** 支持对提示词进行分类管理。

### 2.9. 日志管理 (Log Management)
提供一个界面，用于查看管理员的活动日志。

- **审计日志:** 查看所有管理员执行的关键操作记录（例如，删除模型、取消任务等）。
- **筛选与搜索:** 按管理员或操作类型筛选日志。

## 3. 高级 API 设计

为了支持后台管理前端，将向 FastAPI 后端添加新的 API 端点。必须保护这些端点，以确保只有授权的管理员才能访问它们。

- **认证:** 将实施一种新的认证机制（例如，单独的管理员登录，或用于管理路由的静态 API 密钥）。
- **端点前缀:** 所有与管理相关的端点都将以 `/api/admin` 为前缀。

**端点示例:**

- `GET /api/admin/stats`: 获取仪表盘统计信息。
- `GET /api/admin/tasks`: 获取所有任务的列表。
- `POST /api/admin/tasks/{task_id}/cancel`: 取消任务。
- `GET /api/admin/images`: 获取图片列表。
- `GET /api/admin/inspirations`: 获取收藏列表。
- `DELETE /api/admin/inspirations/{favorite_id}`: 移除收藏。
- `GET /api/admin/models/checkpoints`: 列出所有Checkpoint模型。
- `POST /api/admin/models/checkpoints`: 上传新的Checkpoint模型。
- `GET /api/admin/models/loras`: 列出所有LoRA模型。
- `POST /api/admin/models/loras`: 上传新的LoRA模型。
- `GET /api/admin/workflows`: 获取工作流列表。
- `POST /api/admin/workflows`: 上传新的工作流。
- `GET /api/admin/prompts`: 获取提示词列表。
- `POST /api/admin/prompts`: 创建新的提示词。
- `GET /api/admin/logs`: 获取审计日志列表。

## 4. 技术栈与实施建议

- **前端:**
  - 使用现有的 **Ant Design Vue** 组件库构建管理界面，以加快开发速度。
  - 在 `admin/frontend` 目录下进行开发。
- **后端:**
  - 新的管理API端点将添加到 `admin/backend` 的FastAPI应用中。
  - 使用JWT或API密钥等认证方案来保护管理端点。

## 5. 系统架构

管理后台将作为一套独立的服务运行在 `admin/` 目录下，与主应用解耦，确保开发和部署的独立性。

### 5.1. 架构图

'''
+----------------------+        +-----------------------+
|   Admin Frontend     |        |   Main Frontend       |
| (Vue.js, Ant Design) |        | (Vue.js, Ant Design)  |
+----------------------+        +-----------------------+
           |                              |
           | (REST API via /api/admin/*)  | (REST API via /api/*)
           v                              v
+----------------------+        +-----------------------+
|    Admin Backend     |        |     Main Backend      |
|      (FastAPI)       |        |       (FastAPI)       |
+----------------------+        +-----------------------+
           |                              |
           | (DB Access)                  | (DB Access & ComfyUI)
           |                              |
           '------------------------------'
                          |
                          v
                 +----------------+
                 |    Database    |
                 | (e.g., SQLite) |
                 +----------------+
'''

### 5.2. 组件说明

- **Admin Frontend**: 位于 `admin/frontend`，是一个独立的Vue.js单页应用，负责提供管理员交互界面。
- **Admin Backend**: 位于 `admin/backend`，是一个独立的FastAPI应用，为管理前端提供RESTful API，并负责处理所有管理相关的业务逻辑。
- **Database**: 管理后台将与主应用共享同一个数据库，但会创建独立的表来存储管理员账户、审计日志等信息。它也会直接访问和管理主应用的数据表（如任务、内容等）。

## 6. 数据库设计

为了支持管理功能，将在现有数据库中添加以下表。

### 6.1. `admin_users`

存储管理员账户信息。

| 字段名          | 类型         | 约束                | 描述           |
| --------------- | ------------ | ------------------- | -------------- |
| `id`            | Integer      | Primary Key, Auto-Inc | 用户唯一标识   |
| `username`      | String(50)   | Unique, Not Null    | 管理员用户名   |
| `hashed_password` | String(255)  | Not Null            | 加密后的密码   |
| `created_at`    | DateTime     | Not Null            | 创建时间       |
| `last_login`    | DateTime     | Nullable            | 最后登录时间   |

### 6.2. `admin_audit_log`

记录管理员的关键操作，用于审计和追踪。

| 字段名             | 类型         | 约束             | 描述                               |
| ------------------ | ------------ | ---------------- | ---------------------------------- |
| `id`               | Integer      | Primary Key, Auto-Inc | 日志唯一标识                       |
| `admin_id`         | Integer      | Foreign Key      | 执行操作的管理员ID (`admin_users.id`) |
| `action`           | String(100)  | Not Null         | 操作类型 (如 `delete_task`)        |
| `target_resource_id` | String(255)  | Nullable         | 操作对象的ID (如任务ID)            |
| `timestamp`        | DateTime     | Not Null         | 操作发生的时间                     |
| `details`          | JSON/Text    | Nullable         | 操作的详细信息（如请求参数）       |

### 6.3. `inspirations`
存储用户收藏的图片。

| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-Inc | 唯一标识 |
| `user_id` | Integer | Foreign Key (to a user table) | 收藏该图片的用户ID |
| `image_id` | Integer | Foreign Key (to an image table) | 被收藏的图片ID |
| `created_at` | DateTime | Not Null | 收藏时间 |

### 6.4. `workflows`
存储 ComfyUI 工作流。

| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-Inc | 唯一标识 |
| `name` | String(100) | Not Null | 工作流名称 |
| `description` | Text | Nullable | 工作流描述 |
| `workflow_json` | JSON/Text | Not Null | 工作流的JSON定义 |
| `created_at` | DateTime | Not Null | 创建时间 |

### 6.5. `prompts`
存储正面和负面提示词。

| 字段名 | 类型 | 约束 | 描述 |
|---|---|---|---|
| `id` | Integer | Primary Key, Auto-Inc | 唯一标识 |
| `name` | String(100) | Not Null | 提示词名称/标题 |
| `type` | String(20) | Not Null | 类型（如 `positive`, `negative`） |
| `content` | Text | Not Null | 提示词内容 |
| `created_at` | DateTime | Not Null | 创建时间 |

*注：任务、模型、内容等数据将直接使用主应用已有的数据表，管理后台通过API对其进行增删改查操作。*

## 7. 开发实施步骤

### 7.1. 阶段一：后端基础建设

1.  **认证模块**:
    - 在 `admin/backend` 中，定义 `admin_users` 和 `admin_audit_log` 的数据模型。
    - 创建API端点 `/api/admin/login`，实现基于JWT的登录认证。
    - 创建一个FastAPI依赖项，用于验证后续请求中的JWT，保护所有管理API。
2.  **数据库集成**:
    - 配置数据库连接，确保 `admin/backend` 服务可以访问到主数据库。
    - 创建数据库迁移脚本（如使用Alembic），用于创建新表。

### 7.2. 阶段二：后端核心功能开发

1.  **仪表盘API**: 实现 `GET /api/admin/stats` 端点。
2.  **任务管理API**: 实现任务的增删改查API。
3.  **图片与灵感管理API**: 实现对图片和收藏的增删改查API。
4.  **模型与LoRA管理API**: 实现文件上传、删除和列表接口。
5.  **生图流与提示词管理API**: 实现对工作流和提示词的增删改查API。
6.  **审计日志**: 创建一个中间件或装饰器，自动记录关键操作的审计日志。

### 7.3. 阶段三：前端开发

1.  **项目初始化**:
    - 在 `admin/frontend` 中，安装 `vue-router`, `pinia`, `axios` 和 `ant-design-vue`。
    - 配置Vue Router，定义登录页和后台主布局的路由。
    - 创建Pinia store，用于管理用户认证状态。
2.  **UI开发**:
    - 创建登录页面和后台主布局。
    - 使用路由守卫，确保未登录用户无法访问后台页面。
3.  **功能模块开发**:
    - 为每个模块（首页、任务管理、生图流、提示词等）创建对应的页面组件。
    - 在组件中调用后端API，并使用Ant Design Vue组件进行渲染。

### 7.4. 阶段四：联调、测试与部署

1.  **联调**: 前后端并行开发完成后，进行接口联调。
2.  **测试**: 编写必要的单元测试和端到端测试。
3.  **部署**:
    - 更新项目的 `docker-compose.yml` 和 `Dockerfile`，将管理服务加入容器化流程。
    - 编写部署文档，说明如何启动和访问管理后台。