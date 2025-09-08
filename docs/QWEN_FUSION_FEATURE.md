# Qwen多图融合功能

## 📋 功能概述

Qwen多图融合功能是基于Qwen图像编辑模型的新能力，支持将2-5张图像进行拼接和编辑，生成融合后的图像。

## 🎯 主要特性

- **多图拼接**: 支持2-5张图像的智能拼接
- **图像编辑**: 基于拼接后的图像进行文本引导的编辑
- **中文支持**: 完全支持中文描述和指令
- **独立API**: 不影响现有的单图生成功能

## 🔧 技术架构

### 工作流结构
```
图像1 → LoadImage
图像2 → LoadImage  → ImageConcatMulti → FluxKontextImageScale
图像3 → LoadImage
                    ↓
            TextEncodeQwenImageEdit → KSampler → VAEDecode → SaveImage
```

### 核心组件
- **QwenFusionWorkflow**: 多图融合工作流创建器
- **qwen_image_fusion_workflow.json**: 多图融合工作流模板
- **qwen-fusion模型配置**: 专门的多图融合模型配置

## 📡 API接口

### 多图融合生成API

**端点**: `POST /api/generate-image-fusion`

**参数**:
- `description` (string, 必需): 融合描述文本
- `reference_images` (file[], 必需): 参考图像文件列表（2-5张）
- `fusion_mode` (string, 可选): 融合模式，默认"concat"
- `steps` (int, 可选): 采样步数，默认20
- `cfg` (float, 可选): CFG值，默认2.5
- `seed` (int, 可选): 随机种子
- `model` (string, 可选): 模型名称，默认"qwen-fusion"
- `loras` (string, 可选): LoRA配置（暂不支持）

**响应**:
```json
{
  "task_id": "uuid",
  "status": "pending",
  "message": "多图融合任务已提交，正在处理中"
}
```

### 使用示例

```python
import requests

# 准备多张图像文件
files = [
    ('reference_images', ('image1.png', open('image1.png', 'rb'), 'image/png')),
    ('reference_images', ('image2.png', open('image2.png', 'rb'), 'image/png')),
    ('reference_images', ('image3.png', open('image3.png', 'rb'), 'image/png'))
]

# 准备请求数据
data = {
    'description': '将三张图像拼接后，让左边的女人手里拎着中间棕色的包，坐在白色沙发上',
    'fusion_mode': 'concat',
    'steps': 20,
    'cfg': 2.5,
    'model': 'qwen-fusion'
}

# 发送请求
response = requests.post(
    'http://localhost:9000/api/generate-image-fusion',
    files=files,
    data=data
)

result = response.json()
print(f"任务ID: {result['task_id']}")
```

## 🎨 融合模式

### concat (拼接模式)
- 将多张图像水平拼接
- 支持2-5张图像
- 自动调整图像尺寸

### 未来支持的模式
- `blend` (混合模式): 图像混合融合
- `edit` (编辑模式): 基于多图进行编辑

## 🔄 工作流程

1. **图像上传**: 用户上传2-5张参考图像
2. **图像处理**: 系统自动保存和验证图像
3. **工作流创建**: 根据图像数量动态创建工作流
4. **图像拼接**: 使用ImageConcatMulti节点拼接图像
5. **文本编辑**: 基于拼接图像进行文本引导编辑
6. **结果生成**: 输出融合后的最终图像

## 📁 文件结构

```
back/
├── workflows/
│   └── qwen_image_fusion_workflow.json    # 多图融合工作流模板
├── core/
│   ├── workflows/
│   │   └── qwen_fusion_workflow.py        # 多图融合工作流类
│   ├── model_manager.py                   # 模型配置管理
│   ├── task_manager.py                    # 任务管理
│   └── workflow_template.py               # 工作流模板管理
├── models/
│   └── schemas.py                         # 数据模型
└── main.py                                # API接口
```

## 🧪 测试

使用提供的测试脚本进行功能测试：

```bash
cd back
python test_fusion_api.py
```

测试脚本会：
1. 检查模型可用性
2. 发送多图融合请求
3. 轮询任务状态
4. 显示最终结果

## ⚠️ 注意事项

1. **图像数量限制**: 支持2-5张图像，超出范围会返回错误
2. **LoRA支持**: 多图融合功能暂不支持LoRA配置
3. **图像格式**: 支持JPG/PNG格式，文件大小限制2MB
4. **处理时间**: 多图融合比单图生成需要更长的处理时间

## 🔮 未来规划

- [ ] 支持更多融合模式（blend, edit）
- [ ] 添加LoRA支持
- [ ] 优化图像拼接算法
- [ ] 支持自定义拼接方向
- [ ] 添加批量处理功能

## 🐛 故障排除

### 常见问题

1. **"多图融合至少需要2张图像"**
   - 确保上传了至少2张图像

2. **"多图融合最多支持5张图像"**
   - 减少上传的图像数量到5张以内

3. **"模型不可用"**
   - 检查qwen-fusion模型是否正确配置
   - 确认ComfyUI服务正常运行

4. **任务执行失败**
   - 检查图像文件是否损坏
   - 查看后端日志获取详细错误信息

### 日志查看

```bash
# 查看后端日志
tail -f logs/backend.log

# 查看ComfyUI日志
tail -f logs/comfyui.log
```
