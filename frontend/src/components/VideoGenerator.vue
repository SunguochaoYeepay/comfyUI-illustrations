<template>
  <div class="video-generator-panel" :class="{ 'in-modal': props.isInModal }">
    <div class="video-control-card">
      <div class="video-control-layout">
        <!-- 主要输入区域 -->
        <div class="video-main-input-row">
          <!-- 参考图像预览 -->
          <div class="video-reference-section">
            <div v-if="props.referenceImage" class="video-reference-preview">
              <img :src="props.referenceImage" alt="参考图像" class="video-reference-img" />
              <div class="video-reference-label">参考图像</div>
            </div>
          </div>

          <!-- 视频描述输入区域 -->
          <div class="video-input-group">
            <div class="video-prompt-input-group">
              <a-textarea
                v-model:value="videoForm.description"
                placeholder="请描述您想要的视频效果（如：镜头缓慢推进，人物微笑，背景模糊）"
                :rows="2"
                class="video-prompt-input"
              />
            </div>
          </div>
        </div>

        <!-- 视频参数和生成按钮行 -->
        <div class="video-controls-row">
          <!-- 左侧：视频参数 -->
          <div class="video-params-group">
            <!-- 视频时长 -->
            <div class="video-param-item">
              <label class="video-param-label">时长(秒)</label>
              <a-input-number
                v-model:value="videoForm.duration"
                :min="1"
                :max="30"
                :step="1"
                class="video-duration-input"
              />
            </div>
            
            <!-- 帧率 -->
            <div class="video-param-item">
              <label class="video-param-label">帧率</label>
              <a-select
                v-model:value="videoForm.fps"
                class="video-fps-select"
              >
                <a-select-option :value="16">16 FPS</a-select-option>
                <a-select-option :value="24">24 FPS</a-select-option>
                <a-select-option :value="30">30 FPS</a-select-option>
              </a-select>
            </div>
          </div>

          <!-- 右侧：生成按钮 -->
          <div class="video-generate-section">
            <a-button
              type="primary"
              size="large"
              :loading="generating"
              :disabled="!canGenerate"
              @click="generateVideo"
              class="video-generate-btn"
            >
              <template #icon>
                <video-camera-outlined />
              </template>
              {{ generating ? '生成中...' : '生成视频' }}
            </a-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, VideoCameraOutlined, CloseOutlined } from '@ant-design/icons-vue'

// API基础URL - 自动检测环境
const API_BASE = (() => {
  // 开发环境：指向后端9000端口
  if (import.meta.env.DEV) {
    return 'http://localhost:9000'
  }
  // 生产环境：使用环境变量或默认空字符串（通过nginx代理）
  return import.meta.env.VITE_API_BASE_URL || ''
})()

// Props
const props = defineProps({
  referenceImage: {
    type: String,
    default: ''
  },
  isInModal: {
    type: Boolean,
    default: false
  }
})

// 响应式数据
const videoForm = ref({
  description: '',
  duration: 5,
  fps: 16
})

const fileList = ref([])
const generating = ref(false)

// 计算属性
const canGenerate = computed(() => {
  return videoForm.value.description.trim() && (fileList.value.length > 0 || props.referenceImage)
})

// 方法
const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    message.error('只能上传图片文件！')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('图片大小不能超过10MB！')
    return false
  }
  
  return false // 阻止自动上传
}

const generateVideo = async () => {
  if (!canGenerate.value) {
    message.warning('请填写视频描述并上传参考图像')
    return
  }
  
  try {
    generating.value = true
    
    // 创建FormData
    const formData = new FormData()
    formData.append('description', videoForm.value.description)
    formData.append('duration', videoForm.value.duration)
    formData.append('fps', videoForm.value.fps)
    formData.append('model', 'wan2.2-video')
    
    // 添加参考图像
    if (fileList.value.length > 0) {
      formData.append('reference_image', fileList.value[0].originFileObj)
    } else if (props.referenceImage) {
      // 如果有传入的参考图像URL，需要先下载再上传
      try {
        const response = await fetch(props.referenceImage)
        const blob = await response.blob()
        const file = new File([blob], 'reference_image.png', { type: 'image/png' })
        formData.append('reference_image', file)
      } catch (error) {
        console.error('下载参考图像失败:', error)
        message.error('参考图像处理失败')
        return
      }
    }
    
    // 发送请求
    const response = await fetch(`${API_BASE}/api/generate-video`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const result = await response.json()
    
    if (result.status === 'created') {
      message.success('视频生成任务已创建，请等待处理完成')
      // 触发父组件的事件来更新任务列表
      emit('task-created', result.task_id)
    } else {
      throw new Error(result.message || '创建任务失败')
    }
    
  } catch (error) {
    console.error('生成视频失败:', error)
    message.error(`生成视频失败: ${error.message}`)
  } finally {
    generating.value = false
  }
}



// 定义事件
const emit = defineEmits(['task-created'])
</script>

<style scoped>
.video-generator-panel {
  position: fixed;
  bottom: 0px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 800px;
  width: 90%;
  border-radius: 16px;
  overflow: hidden;
}

.video-generator-panel.in-modal {
  position: fixed;
  bottom: 20px;
  left: 40%;
  transform: translateX(-50%);
  width: 98%;
  max-width: 700px;
  height: auto;
  z-index: 2100;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.video-generator-panel.in-modal .video-control-card {
  height: auto;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

.video-generator-panel.in-modal .video-control-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 16px;
  gap: 12px;
}

.video-control-card {
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  background: #1a1a1a;
  border: 0px solid #333;
}

.video-control-card :deep(.ant-card-body) {
  background: #1a1a1a;
  color: #fff;
  padding: 16px;
}

.video-control-layout {
  display: flex;
  flex-direction: column;
}

.video-main-input-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.video-reference-section {
  flex-shrink: 0;
  width: 80px;
}

.video-reference-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px;
  border: 2px dashed #444;
  border-radius: 8px;
  background: #2a2a2a;
}

.video-reference-img {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 4px;
}

.video-reference-label {
  color: #ccc;
  font-size: 11px;
  text-align: center;
}

.video-input-group {
  flex: 1;
  min-width: 0;
}

.video-prompt-input-group {
  width: 100%;
}

.video-prompt-input {
  background: #2a2a2a;
  border: 1px solid #444;
  color: #fff;
  border-radius: 8px;
  resize: vertical;
  width: 100%;
  min-height: 80px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.5;
  transition: border-color 0.3s;
}

.video-prompt-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  outline: none;
}

.video-controls-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.video-params-group {
  display: flex;
  gap: 12px;
  align-items: center;
  flex: 1;
}

.video-param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.video-param-label {
  font-size: 12px;
  font-weight: 500;
  color: #ccc;
  margin: 0;
}

.video-duration-input,
.video-fps-select {
  width: 80px;
  height: 32px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  color: #fff;
  font-size: 12px;
}

.video-duration-input:focus,
.video-fps-select:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  outline: none;
}

.video-generate-section {
  flex-shrink: 0;
}

.video-generate-btn {
  border-radius: 8px;
  background: linear-gradient(135deg, #1890ff, #096dd9);
  border: none;
  font-weight: 600;
  min-width: 120px;
  height: 40px;
  color: #fff;
}

.video-generate-btn:hover {
  background: linear-gradient(135deg, #40a9ff, #1890ff);
  transform: translateY(-1px);
}

.video-generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .video-generator-panel {
    width: 95%;
  }
  
  .video-main-input-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .video-reference-section {
    width: 100%;
  }
  
  .video-reference-preview {
    flex-direction: row;
    justify-content: center;
    gap: 12px;
  }
  
  .video-controls-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .video-params-group {
    width: 100%;
    justify-content: space-between;
  }
  
  .video-generate-section {
    width: 100%;
  }
  
  .video-generate-btn {
    width: 100%;
  }
}
</style>
