<template>
  <div v-if="visible" class="image-preview-overlay" @click="handleOverlayClick">
    <div class="image-preview-container">
      <!-- 关闭按钮 -->
      <button class="close-btn" @click="closePreview">
        <CloseOutlined />
      </button>
      
      <!-- 主要内容区域 -->
      <div class="preview-content">
        <!-- 左侧图片区域 -->
        <div class="image-section">
          <!-- 上一张按钮 -->
          <button 
            v-if="imageList.length > 1"
            class="nav-btn nav-btn-prev"
            :class="{ disabled: currentIndex <= 0 }"
            @click="navigatePrev"
            :disabled="currentIndex <= 0"
            title="上一张 (←)"
          >
            <LeftOutlined />
          </button>
          
          <div class="image-container">
            <img 
              :src="imageData.url" 
              :alt="imageData.prompt || '生成的图片'"
              class="preview-image"
              @click.stop
            />
          </div>
          
          <!-- 下一张按钮 -->
          <button 
            v-if="imageList.length > 1"
            class="nav-btn nav-btn-next"
            :class="{ disabled: currentIndex >= imageList.length - 1 }"
            @click="navigateNext"
            :disabled="currentIndex >= imageList.length - 1"
            title="下一张 (→)"
          >
            <RightOutlined />
          </button>
          
          <!-- 图片计数器 -->
          <div v-if="imageList.length > 1" class="image-counter">
            {{ currentIndex + 1 }} / {{ imageList.length }}
          </div>
        </div>
        
        <!-- 右侧信息面板 -->
        <div class="info-panel">
          <div class="info-header">
            <h3>生成信息</h3>
          </div>
          
          <!-- 图片操作按钮 -->
          <div class="image-actions">
            <a-button type="primary" @click="downloadImage">
              <DownloadOutlined /> 下载
            </a-button>
            <a-button @click="copyImageUrl">
              <CopyOutlined /> 复制链接
            </a-button>
          </div>
          
          <div class="info-content">
            <!-- 参考图 -->
            <div class="info-item" v-if="imageData.referenceImage">
              <label>参考图:</label>
              <div class="info-value reference-image">
                <img 
                  :src="imageData.referenceImage" 
                  alt="参考图"
                  class="reference-img"
                  @click="viewReferenceImage"
                />
              </div>
            </div>
            
            <!-- 提示词 -->
            <div class="info-item">
              <label>提示词:</label>
              <div class="info-value prompt-text">
                {{ imageData.prompt || '无' }}
              </div>
            </div>
            
            <!-- 生成时间 -->
            <div class="info-item">
              <label>生成时间:</label>
              <div class="info-value">
                {{ formatDate(imageData.createdAt) }}
              </div>
            </div>
            
            <!-- 图片尺寸 -->
            <div class="info-item">
              <label>图片尺寸:</label>
              <div class="info-value">
                {{ imageData.width || '未知' }} × {{ imageData.height || '未知' }}
              </div>
            </div>
            
            <!-- 任务ID -->
            <div class="info-item">
              <label>任务ID:</label>
              <div class="info-value">
                {{ imageData.task_id || '未知' }}
              </div>
            </div>
            
            <!-- 文件大小 -->
            <div class="info-item" v-if="imageData.fileSize">
              <label>文件大小:</label>
              <div class="info-value">
                {{ formatFileSize(imageData.fileSize) }}
              </div>
            </div>
            
            <!-- 生成参数 -->
            <div class="info-item" v-if="imageData.parameters">
              <label>生成参数:</label>
              <div class="info-value parameters">
                <pre>{{ JSON.stringify(imageData.parameters, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { CloseOutlined, DownloadOutlined, CopyOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  imageData: {
    type: Object,
    default: () => ({})
  },
  imageList: {
    type: Array,
    default: () => []
  },
  currentIndex: {
    type: Number,
    default: 0
  }
})

// Emits
const emit = defineEmits(['close', 'navigate'])

// 关闭预览
const closePreview = () => {
  emit('close')
}

// 点击遮罩层关闭
const handleOverlayClick = (e) => {
  if (e.target === e.currentTarget) {
    closePreview()
  }
}

// 下载图片
const downloadImage = async () => {
  try {
    const response = await fetch(props.imageData.url)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `generated-image-${Date.now()}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success('图片下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('图片下载失败')
  }
}

// 复制图片链接
const copyImageUrl = async () => {
  try {
    await navigator.clipboard.writeText(props.imageData.url)
    message.success('链接已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    message.error('复制链接失败')
  }
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '未知'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

// 查看参考图
const viewReferenceImage = () => {
  if (props.imageData.referenceImage) {
    window.open(props.imageData.referenceImage, '_blank')
  }
}

// 导航到上一张图片
const navigatePrev = () => {
  if (props.currentIndex > 0) {
    emit('navigate', props.currentIndex - 1)
  }
}

// 导航到下一张图片
const navigateNext = () => {
  if (props.currentIndex < props.imageList.length - 1) {
    emit('navigate', props.currentIndex + 1)
  }
}

// 键盘事件处理
const handleKeydown = (e) => {
  if (!props.visible) return
  
  switch (e.key) {
    case 'ArrowLeft':
      e.preventDefault()
      navigatePrev()
      break
    case 'ArrowRight':
      e.preventDefault()
      navigateNext()
      break
    case 'Escape':
      e.preventDefault()
      closePreview()
      break
  }
}

// 生命周期钩子
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.image-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.nav-btn {
  position: absolute;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
  z-index: 1000;
  font-size: 16px;
}

.nav-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.8);
}

.nav-btn:disabled,
.nav-btn.disabled {
  opacity: 0.3;
  cursor: not-allowed;
  pointer-events: none;
}

.nav-btn:disabled:hover,
.nav-btn.disabled:hover {
  transform: none;
  background: rgba(0, 0, 0, 0.6);
}

.nav-btn-prev {
  top: 50%;
  left: 10px;
  transform: translateY(-50%);
  transition: all 0.2s ease;
}

.nav-btn-prev:hover:not(:disabled) {
  transform: translateY(-50%) scale(1.05);
}

.nav-btn-next {
  top: 50%;
  right: 10px;
  transform: translateY(-50%);
  transition: all 0.2s ease;
}

.nav-btn-next:hover:not(:disabled) {
  transform: translateY(-50%) scale(1.05);
}

.image-counter {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  backdrop-filter: blur(4px);
  z-index: 5;
}

.image-preview-container {
  position: relative;
  width: 90vw;
  height: 90vh;
  max-height: 900px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  transform: scale(1.1);
}

.preview-content {
  display: flex;
  height: 100%;
}

.image-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  min-width: 0;
  position: relative;
}

.image-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  margin-bottom: 16px;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

.image-actions {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid #444;
}

.info-panel {
  width: 400px;
  border-left: 1px solid #444;
  display: flex;
  flex-direction: column;
}

.info-header {
  padding: 20px;
}

.info-header h3 {
  margin: 0;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.info-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.info-item {
  margin-bottom: 20px;
}

.info-item label {
  display: block;
  color: #999;
  font-size: 14px;
  margin-bottom: 6px;
  font-weight: 500;
}

.info-value {
  color: #fff;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-all;
}

.prompt-text {
  background: #333;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #667eea;
  white-space: pre-wrap;
}

.parameters {
  background: #333;
  padding: 12px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.parameters pre {
  margin: 0;
  color: #fff;
}

.reference-image {
  margin-top: 8px;
}

.reference-img {
  max-width: 120px;
  max-height: 120px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #444;
}

.reference-img:hover {
  border-color: #667eea;
  transform: scale(1.05);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .image-preview-container {
    width: 95vw;
    height: 95vh;
  }
  
  .preview-content {
    flex-direction: column;
  }
  
  .info-panel {
    width: 100%;
    height: 300px;
    border-left: none;
    border-top: 1px solid #444;
  }
  
  .image-section {
    flex: 1;
    min-height: 0;
  }
}

/* 滚动条样式 */
.info-content::-webkit-scrollbar,
.parameters::-webkit-scrollbar {
  width: 6px;
}

.info-content::-webkit-scrollbar-track,
.parameters::-webkit-scrollbar-track {
  background: #333;
  border-radius: 3px;
}

.info-content::-webkit-scrollbar-thumb,
.parameters::-webkit-scrollbar-thumb {
  background: #666;
  border-radius: 3px;
}

.info-content::-webkit-scrollbar-thumb:hover,
.parameters::-webkit-scrollbar-thumb:hover {
  background: #888;
}
</style>