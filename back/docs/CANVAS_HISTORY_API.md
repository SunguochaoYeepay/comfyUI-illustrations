# 画布历史记录API文档

## 概述

画布历史记录API提供了完整的画布操作历史管理功能，支持云端存储、离线同步和批量操作。

## 数据库表结构

### canvas_history 表

```sql
CREATE TABLE canvas_history (
    id TEXT PRIMARY KEY,                    -- 历史记录ID
    task_id TEXT NOT NULL,                  -- 任务ID
    prompt TEXT,                            -- 提示词
    original_image_url TEXT,                -- 原始图片URL
    result_image_url TEXT NOT NULL,         -- 结果图片URL
    parameters TEXT,                        -- 参数(JSON格式)
    timestamp INTEGER NOT NULL,             -- 时间戳
    type TEXT DEFAULT 'inpainting',         -- 类型
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 创建时间
);
```

## API接口

### 1. 创建历史记录

**POST** `/api/canvas/history`

**请求体:**
```json
{
    "id": "uuid-string",
    "task_id": "task-uuid",
    "prompt": "提示词",
    "original_image_url": "/api/image/upload/original.jpg",
    "result_image_url": "/api/image/result/result.jpg",
    "parameters": {
        "brush_size": 20,
        "opacity": 0.8,
        "mode": "inpainting"
    },
    "timestamp": 1640995200000,
    "type": "inpainting"
}
```

**响应:**
```json
{
    "id": "uuid-string",
    "task_id": "task-uuid",
    "prompt": "提示词",
    "original_image_url": "/api/image/upload/original.jpg",
    "result_image_url": "/api/image/result/result.jpg",
    "parameters": {
        "brush_size": 20,
        "opacity": 0.8,
        "mode": "inpainting"
    },
    "timestamp": 1640995200000,
    "type": "inpainting",
    "created_at": "2024-01-01T00:00:00"
}
```

### 2. 获取历史记录列表

**GET** `/api/canvas/history`

**查询参数:**
- `limit`: 每页记录数 (默认: 50, 范围: 1-100)
- `offset`: 偏移量 (默认: 0)
- `order`: 排序方式 (asc/desc, 默认: desc)

**响应:**
```json
{
    "records": [
        {
            "id": "uuid-string",
            "task_id": "task-uuid",
            "prompt": "提示词",
            "original_image_url": "/api/image/upload/original.jpg",
            "result_image_url": "/api/image/result/result.jpg",
            "parameters": {...},
            "timestamp": 1640995200000,
            "type": "inpainting",
            "created_at": "2024-01-01T00:00:00"
        }
    ],
    "total": 100,
    "limit": 50,
    "offset": 0
}
```

### 3. 获取单个历史记录

**GET** `/api/canvas/history/{record_id}`

**响应:**
```json
{
    "id": "uuid-string",
    "task_id": "task-uuid",
    "prompt": "提示词",
    "original_image_url": "/api/image/upload/original.jpg",
    "result_image_url": "/api/image/result/result.jpg",
    "parameters": {...},
    "timestamp": 1640995200000,
    "type": "inpainting",
    "created_at": "2024-01-01T00:00:00"
}
```

### 4. 更新历史记录

**PUT** `/api/canvas/history/{record_id}`

**请求体:**
```json
{
    "prompt": "更新后的提示词",
    "parameters": {
        "brush_size": 30,
        "opacity": 0.9
    }
}
```

**响应:**
```json
{
    "id": "uuid-string",
    "task_id": "task-uuid",
    "prompt": "更新后的提示词",
    "original_image_url": "/api/image/upload/original.jpg",
    "result_image_url": "/api/image/result/result.jpg",
    "parameters": {
        "brush_size": 30,
        "opacity": 0.9
    },
    "timestamp": 1640995200000,
    "type": "inpainting",
    "created_at": "2024-01-01T00:00:00"
}
```

### 5. 删除历史记录

**DELETE** `/api/canvas/history/{record_id}`

**响应:**
```json
{
    "id": "uuid-string",
    "message": "History record deleted successfully"
}
```

### 6. 批量创建历史记录

**POST** `/api/canvas/history/batch`

**请求体:**
```json
{
    "records": [
        {
            "id": "uuid-1",
            "task_id": "task-uuid-1",
            "prompt": "批量记录1",
            "original_image_url": "/api/image/upload/1.jpg",
            "result_image_url": "/api/image/result/1.jpg",
            "parameters": {...},
            "timestamp": 1640995200000,
            "type": "inpainting"
        },
        {
            "id": "uuid-2",
            "task_id": "task-uuid-2",
            "prompt": "批量记录2",
            "original_image_url": "/api/image/upload/2.jpg",
            "result_image_url": "/api/image/result/2.jpg",
            "parameters": {...},
            "timestamp": 1640995201000,
            "type": "outpainting"
        }
    ]
}
```

**响应:**
```json
{
    "message": "Successfully created 2 out of 2 records",
    "success_count": 2,
    "total_count": 2,
    "failed_count": 0
}
```

### 7. 清空所有历史记录

**DELETE** `/api/canvas/history`

**响应:**
```json
{
    "message": "Successfully deleted 50 history records",
    "deleted_count": 50
}
```

## 错误处理

所有API接口都遵循统一的错误响应格式:

```json
{
    "detail": "错误描述信息"
}
```

常见HTTP状态码:
- `200`: 成功
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

## 使用示例

### Python客户端示例

```python
import requests
import uuid
import time

BASE_URL = "http://localhost:8000/api/canvas"

# 创建历史记录
def create_history_record():
    record_data = {
        "id": str(uuid.uuid4()),
        "task_id": str(uuid.uuid4()),
        "prompt": "测试提示词",
        "original_image_url": "/api/image/upload/test.jpg",
        "result_image_url": "/api/image/result/test.jpg",
        "parameters": {
            "brush_size": 20,
            "opacity": 0.8
        },
        "timestamp": int(time.time() * 1000),
        "type": "inpainting"
    }
    
    response = requests.post(f"{BASE_URL}/history", json=record_data)
    return response.json()

# 获取历史记录列表
def get_history_records():
    response = requests.get(f"{BASE_URL}/history?limit=10&offset=0")
    return response.json()

# 删除历史记录
def delete_history_record(record_id):
    response = requests.delete(f"{BASE_URL}/history/{record_id}")
    return response.json()
```

### JavaScript客户端示例

```javascript
const BASE_URL = 'http://localhost:8000/api/canvas';

// 创建历史记录
async function createHistoryRecord() {
    const recordData = {
        id: crypto.randomUUID(),
        task_id: crypto.randomUUID(),
        prompt: '测试提示词',
        original_image_url: '/api/image/upload/test.jpg',
        result_image_url: '/api/image/result/test.jpg',
        parameters: {
            brush_size: 20,
            opacity: 0.8
        },
        timestamp: Date.now(),
        type: 'inpainting'
    };
    
    const response = await fetch(`${BASE_URL}/history`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(recordData)
    });
    
    return await response.json();
}

// 获取历史记录列表
async function getHistoryRecords() {
    const response = await fetch(`${BASE_URL}/history?limit=10&offset=0`);
    return await response.json();
}
```

## 测试

运行测试脚本:

```bash
cd back
python test_canvas_history_api.py
```

测试脚本会验证所有API接口的功能，包括:
- 创建历史记录
- 获取历史记录列表
- 获取单个历史记录
- 更新历史记录
- 批量创建历史记录
- 删除历史记录

## 注意事项

1. **ID唯一性**: 每个历史记录必须有唯一的ID
2. **时间戳格式**: 使用毫秒级时间戳
3. **参数存储**: parameters字段存储为JSON格式
4. **批量操作**: 批量创建时，重复ID会被跳过
5. **分页查询**: 建议使用分页查询避免一次性加载过多数据
6. **错误处理**: 客户端应妥善处理各种错误情况

## 前端集成

前端已实现完整的画布历史记录功能，包括:
- 云端存储和离线同步
- 网络状态检测
- 自动重试机制
- 用户友好的错误提示

相关文件:
- `frontend/src/services/canvasHistoryService.js`
- `frontend/src/components/CanvasEditor.vue`
- `frontend/src/components/CanvasHistoryPanel.vue`
