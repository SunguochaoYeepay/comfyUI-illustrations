# 🎨 LoRA 集成使用指南

## 概述

YeePay现在支持在Flux Kontext工作流中集成LoRA（Low-Rank Adaptation）模型，最多支持同时使用2个LoRA，为图像生成提供更丰富的风格控制。

## 功能特性

### ✅ 支持的功能
- **双LoRA支持**: 最多同时使用2个LoRA模型
- **独立强度控制**: 每个LoRA可独立设置UNET和CLIP权重强度
- **触发词支持**: 支持为每个LoRA设置触发词
- **Web界面管理**: 通过前端界面选择和管理LoRA
- **文件上传**: 支持上传.safetensors格式的LoRA文件
- **实时预览**: 显示LoRA文件大小和修改时间

### 🎯 技术实现
- **工作流集成**: 在ComfyUI工作流中动态添加LoRA节点
- **节点连接**: 自动处理UNET和CLIP的连接关系
- **参数传递**: 支持强度参数和触发词的自动处理
- **错误处理**: 完善的错误处理和用户提示

## 使用方法

### 1. 前端界面操作

#### 选择LoRA
1. 在控制面板中找到"🎨 LoRA 风格模型"卡片
2. 点击"刷新"按钮获取可用的LoRA列表
3. 从列表中选择需要的LoRA（最多2个）
4. 调整每个LoRA的UNET和CLIP强度（0.0-2.0）
5. 可选：为LoRA设置触发词

#### 上传LoRA
1. 点击"上传LoRA文件"按钮
2. 选择.safetensors格式的LoRA文件
3. 文件大小限制：最大100MB
4. 上传成功后会自动刷新列表

### 2. API接口使用

#### 生成图像时包含LoRA
```bash
curl -X POST "http://localhost:9001/api/generate-image" \
  -F "description=一只可爱的橙色小猫" \
  -F "count=1" \
  -F "steps=20" \
  -F "loras=[{\"name\":\"anime_style.safetensors\",\"strength_model\":0.8,\"strength_clip\":0.7,\"trigger_word\":\"anime style\",\"enabled\":true}]"
```

#### 获取LoRA列表
```bash
curl "http://localhost:9001/api/loras"
```

#### 上传LoRA文件
```bash
curl -X POST "http://localhost:9001/api/loras/upload" \
  -F "file=@your_lora.safetensors"
```

#### 删除LoRA文件
```bash
curl -X DELETE "http://localhost:9001/api/loras/anime_style.safetensors"
```

## 配置说明

### LoRA配置参数

```json
{
  "name": "anime_style.safetensors",     // LoRA文件名
  "strength_model": 0.8,                 // UNET权重强度 (0.0-2.0)
  "strength_clip": 0.7,                  // CLIP权重强度 (0.0-2.0)
  "trigger_word": "anime style",         // 触发词（可选）
  "enabled": true                        // 是否启用
}
```

### 工作流节点结构

```
UNETLoader (37) → LoRALoader1 (50) → LoRALoader2 (51) → KSampler (31)
DualCLIPLoader (38) → LoRALoader1 (50) → LoRALoader2 (51) → CLIPTextEncode (6)
```

## 文件结构

### LoRA文件存放
```
ComfyUI/
├── models/
│   └── loras/
│       ├── anime_style.safetensors
│       ├── realistic_style.safetensors
│       └── ...
```

### 后端代码结构
```
back/
├── core/
│   └── workflow_template.py    # LoRA工作流集成
├── models/
│   └── schemas.py              # LoRA数据模型
├── main.py                     # LoRA API接口
└── README_LoRA.md             # 本文档
```

### 前端代码结构
```
frontend/src/components/
├── LoRASelector.vue           # LoRA选择组件
├── ImageControlPanel.vue      # 集成LoRA选择器
└── ImageGenerator.vue         # 主生成器组件
```

## 最佳实践

### 1. LoRA强度设置
- **UNET强度**: 控制图像生成的整体风格，建议0.5-1.2
- **CLIP强度**: 控制文本理解的方向，建议0.3-1.0
- **组合使用**: 两个LoRA时，建议总强度不超过2.0

### 2. 触发词使用
- 为每个LoRA设置合适的触发词
- 触发词会自动添加到描述文本中
- 避免触发词冲突

### 3. 文件管理
- 定期清理不需要的LoRA文件
- 使用有意义的文件名
- 注意文件大小，避免影响性能

## 故障排除

### 常见问题

#### 1. LoRA文件不显示
- 检查文件是否在正确的目录
- 确认文件格式为.safetensors
- 刷新LoRA列表

#### 2. 上传失败
- 检查文件大小是否超过100MB
- 确认文件格式正确
- 检查磁盘空间

#### 3. 生成效果不理想
- 调整LoRA强度参数
- 检查触发词设置
- 尝试不同的LoRA组合

#### 4. 工作流错误
- 检查ComfyUI日志
- 确认LoRA文件完整性
- 重启服务

## 开发说明

### 扩展更多LoRA
如需支持更多LoRA，需要修改以下文件：
1. `workflow_template.py`: 增加更多LoRA节点
2. `schemas.py`: 修改最大LoRA数量限制
3. `LoRASelector.vue`: 更新UI限制

### 自定义LoRA处理
可以在`workflow_template.py`中添加自定义的LoRA处理逻辑，如：
- 特殊权重计算
- 条件加载
- 动态参数调整

## 更新日志

### v1.0.0 (当前版本)
- ✅ 支持双LoRA集成
- ✅ 完整的Web界面管理
- ✅ API接口支持
- ✅ 文件上传功能
- ✅ 强度参数控制
- ✅ 触发词支持

---

**注意**: 使用LoRA时请确保ComfyUI已正确安装并运行，且LoRA文件格式兼容。
