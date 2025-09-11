<template>
  <!-- 自定义弹窗 - 完全不用Ant Design -->
  <div v-if="visible" class="custom-modal-overlay" @click="closeModal">
    <div class="custom-modal" @click.stop>
      <div class="detail-content" v-if="item">
      <!-- 左右布局容器 -->
      <div class="content-layout">
        <!-- 左侧图片/视频区域 -->
        <div class="image-section">
          <!-- 视频显示 -->
          <video 
            v-if="item.type === 'video'" 
            :src="item.videoUrl" 
            class="detail-video"
            controls
            preload="metadata"
          />
          <!-- 图片显示 -->
          <template v-else>
            <!-- 图片加载骨架屏 -->
            <div v-if="imageLoading" class="detail-image-skeleton">
              <div class="skeleton-shimmer"></div>
            </div>
            <!-- 实际图片 -->
            <img 
              v-show="!imageLoading"
              :src="item.imageUrl" 
              :alt="item.title" 
              class="detail-image"
              @load="handleImageLoad"
              @error="handleImageError"
            />
          </template>
        </div>
        
        <!-- 右侧信息区域 -->
        <div class="detail-info">
          <!-- 标题 -->
          <div class="modal-title">
            <h3>生成信息</h3>
            
          </div>
          
          <!-- 操作按钮 -->
          <div class="action-buttons">
            <!-- 图片类型：显示再次生成和下载按钮 -->
            <template v-if="!item.type || item.type !== 'video'">
              <button class="action-btn regenerate-btn" @click="regenerateImage">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M11.534 7h3.932a.25.25 0 0 1 .192.41l-1.966 2.36a.25.25 0 0 1-.384 0l-1.966-2.36a.25.25 0 0 1 .192-.41zm-11 2h3.932a.25.25 0 0 0 .192-.41L2.69 6.23a.25.25 0 0 0-.384 0L.342 8.59A.25.25 0 0 0 .534 9z"/>
                  <path fill-rule="evenodd" d="M8 3c-1.552 0-2.94.707-3.857 1.818a.5.5 0 1 1-.771-.636A6.002 6.002 0 0 1 13.917 7H12.9A5.002 5.002 0 0 0 8 3zM3.1 9a5.002 5.002 0 0 0 8.757 2.182.5.5 0 1 1 .771.636A6.002 6.002 0 0 1 2.083 9H3.1z"/>
                </svg>
                再次生成
              </button>
              <button @click="downloadImage" class="action-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 10.5L4.5 7h2V2h3v5h2L8 10.5zM2 12v2h12v-2H2z"/>
                </svg>
                下载
              </button>
              <button @click="removeFavorite" class="action-btn remove-favorite-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                  <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                </svg>
                取消收藏
              </button>
            </template>
            
            <!-- 视频类型：显示下载和取消收藏按钮 -->
            <template v-else>
              <button @click="downloadVideo" class="action-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 10.5L4.5 7h2V2h3v5h2L8 10.5zM2 12v2h12v-2H2z"/>
                </svg>
                下载视频
              </button>
              <button @click="removeFavorite" class="action-btn remove-favorite-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                  <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                </svg>
                取消收藏
              </button>
            </template>
          </div>
        <!-- 参考图 -->
        <div class="info-row">
          <span class="info-label">参考图:</span>
          <div class="reference-image-container">
            <div v-if="getReferenceImageUrl()" class="reference-image">
              <img :src="getReferenceImageUrl()" :alt="'参考图'" class="reference-img" />
            </div>
            <div v-else class="reference-image no-image">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
              </svg>
              <span>无参考图</span>
            </div>
          </div>
        </div>
        
        <!-- 提示词 -->
        <div class="info-row">
          <span class="info-label">提示词:</span>
          <div class="prompt-display">{{ item.prompt || 'Landing page, B-end product landing page, technolog' }}</div>
        </div>
        
        <!-- 生成时间 -->
        <div class="info-row">
          <span class="info-label">生成时间:</span>
          <span class="info-value">{{ formatDate(item.createdAt) }}</span>
        </div>
        
        <!-- 图片尺寸 -->
        <div class="info-row">
          <span class="info-label">图片尺寸:</span>
          <span class="info-value">{{ getImageSize() }}</span>
        </div>
        
        <!-- 任务ID -->
        <div class="info-row">
          <span class="info-label">任务ID:</span>
          <span class="info-value task-id">{{ item.task_id }}</span>
        </div>
        
        <!-- 使用模型 -->
        <div class="info-row">
          <span class="info-label">使用模型:</span>
          <span class="info-value">{{ getModelDescription() }}</span>
        </div>
        
        <!-- 使用LoRA -->
        <div class="info-row" v-if="hasLoRA()">
          <span class="info-label">使用LoRA:</span>
          <span class="info-value">{{ getLoRAName() }} (强度:{{ getLoRAStrength() }})</span>
        </div>
        
        <!-- 其他参数 -->
        <div class="info-row" v-if="hasOtherParams()">
          <span class="info-label">其他参数:</span>
          <span class="info-value"></span>
        </div>
        
        <!-- 步数 -->
        <div class="info-row" v-if="item.parameters?.steps">
          <span class="info-label">步数:</span>
          <span class="info-value">{{ item.parameters.steps }}</span>
        </div>
        </div>
      </div>
      </div>
      
      <!-- 关闭按钮 -->
      <button class="custom-modal-close" @click="closeModal">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8 8.707l3.646 3.647.708-.707L8.707 8l3.647-3.646-.707-.708L8 7.293 4.354 3.646l-.707.708L7.293 8l-3.646 3.646.707.708L8 8.707z"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
// 移除所有Ant Design图标导入
import { message } from 'ant-design-vue'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:9000'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  item: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:open', 'remove-favorite', 'regenerate'])

const visible = ref(false)
const imageLoading = ref(true)

watch(() => props.open, (newVal) => {
  visible.value = newVal
  if (newVal && props.item && props.item.type !== 'video') {
    // 弹窗打开时重置图片加载状态
    imageLoading.value = true
  }
})

watch(visible, (newVal) => {
  emit('update:open', newVal)
})

// 处理图片加载完成
const handleImageLoad = () => {
  imageLoading.value = false
}

// 处理图片加载错误
const handleImageError = () => {
  imageLoading.value = false
  console.warn('详情弹窗图片加载失败:', props.item?.imageUrl)
}

const closeModal = () => {
  visible.value = false
}

// ESC键关闭弹窗
const handleKeydown = (event) => {
  if (event.key === 'Escape' && visible.value) {
    closeModal()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

const regenerateImage = () => {
  // 构建回填数据
  let referenceImages = []
  
  if (props.item?.referenceImage) {
    // 如果是JSON字符串数组（多图融合）
    if (typeof props.item.referenceImage === 'string' && props.item.referenceImage.startsWith('[') && props.item.referenceImage.endsWith(']')) {
      try {
        const imageUrls = JSON.parse(props.item.referenceImage)
        // 从URL中提取文件路径
        referenceImages = imageUrls.map(url => {
          // 从完整URL中提取路径部分
          const match = url.match(/\/api\/image\/upload\/(.+)$/)
          return match ? match[1] : url
        })
      } catch (error) {
        console.error('解析参考图JSON失败:', error)
      }
    } else if (typeof props.item.referenceImage === 'string') {
      // 单图情况，从URL中提取路径
      const match = props.item.referenceImage.match(/\/api\/image\/upload\/(.+)$/)
      referenceImages = match ? [match[1]] : []
    }
  }
  
  const regenerateData = {
    prompt: props.item.prompt || '',
    model: props.item.model || '',
    referenceImages: referenceImages,
    loras: props.item.loras || [],
    parameters: props.item.parameters || {}
  }
  
  console.log('🔄 再次生成数据:', regenerateData)
  console.log('🔄 原始item数据:', props.item)
  console.log('🔄 所有字段:', Object.keys(props.item || {}))
  
  // 发送事件给父组件
  emit('regenerate', regenerateData)
  
  // 关闭当前弹窗
  closeModal()
}

const downloadImage = () => {
  if (props.item?.imageUrl) {
    const link = document.createElement('a')
    link.href = props.item.imageUrl
    link.download = `${props.item.title || 'image'}.png`
    link.click()
    message.success('图片下载已开始')
  }
}

const downloadVideo = () => {
  if (props.item?.videoUrl) {
    const link = document.createElement('a')
    link.href = props.item.videoUrl
    link.download = `${props.item.title || 'video'}.mp4`
    link.click()
    message.success('视频下载已开始')
  }
}

const removeFavorite = () => {
  emit('remove-favorite', props.item)
  closeModal()
  message.success('已取消收藏')
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const getImageSize = () => {
  if (props.item?.parameters?.width && props.item?.parameters?.height) {
    return `${props.item.parameters.width} × ${props.item.parameters.height}`
  }
  return '512 × 512' // 默认尺寸
}

const getModelName = () => {
  if (props.item?.parameters?.model) {
    return props.item.parameters.model
  }
  return 'flux1'
}

const getModelDescription = () => {
  const model = getModelName()
  if (model === 'flux1') {
    return 'Flux模型- 更精确控制'
  } else if (model === 'qwen-image') {
    return 'Qwen模型- 支持多图融合'
  }
  return 'AI图像生成模型'
}

const hasLoRA = () => {
  return props.item?.parameters?.loras && props.item.parameters.loras.length > 0
}

const getLoRAName = () => {
  if (hasLoRA()) {
    return props.item.parameters.loras[0].name || 'FLUX-文创品牌设计_品牌LOGO_v1.0'
  }
  return 'FLUX-文创品牌设计_品牌LOGO_v1.0'
}

const getLoRAStrength = () => {
  if (hasLoRA()) {
    return props.item.parameters.loras[0].strength_model || 1
  }
  return 1
}

const hasOtherParams = () => {
  return props.item?.parameters?.steps || props.item?.parameters?.cfg
}

const getReferenceImageUrl = () => {
  console.log('🔍 检查参考图数据:', props.item)
  console.log('🔍 所有字段:', Object.keys(props.item || {}))
  console.log('🔍 参考图路径 (referenceImage):', props.item?.referenceImage)
  console.log('🔍 参考图路径类型:', typeof props.item?.referenceImage)
  console.log('🔍 参考图是否为null:', props.item?.referenceImage === null)
  console.log('🔍 参考图是否为undefined:', props.item?.referenceImage === undefined)
  
  // 检查参考图是否存在且不为null/undefined/空字符串
  if (!props.item?.referenceImage || 
      props.item?.referenceImage === null || 
      props.item?.referenceImage === undefined ||
      props.item?.referenceImage === '' ||
      props.item?.referenceImage === 'null') {
    console.log('❌ 没有参考图路径或为null/undefined/空')
    return null
  }
  
  // 如果是JSON字符串数组（多图融合）
  if (typeof props.item.referenceImage === 'string' && props.item.referenceImage.startsWith('[') && props.item.referenceImage.endsWith(']')) {
    try {
      const imageUrls = JSON.parse(props.item.referenceImage)
      console.log('📁 参考图是JSON数组:', imageUrls)
      if (imageUrls.length > 0) {
        // 将相对路径转换为完整的后端URL
        let imageUrl = imageUrls[0]
        if (imageUrl.startsWith('/api/')) {
          imageUrl = `${API_BASE}${imageUrl}`
        }
        console.log('✅ 使用第一张参考图:', imageUrl)
        return imageUrl
      }
      console.log('❌ 参考图数组为空')
      return null
    } catch (error) {
      console.error('解析参考图JSON失败:', error)
      return null
    }
  }
  
  // 如果是字符串（单图）
  if (typeof props.item.referenceImage === 'string') {
    // 将相对路径转换为完整的后端URL
    let imageUrl = props.item.referenceImage
    if (imageUrl.startsWith('/api/')) {
      imageUrl = `${API_BASE}${imageUrl}`
    }
    console.log('✅ 单张参考图:', imageUrl)
    return imageUrl
  }
  
  console.log('❌ 参考图路径类型未知:', typeof props.item.referenceImage)
  return null
}
</script>

<style scoped>
/* 自定义弹窗 - 完全不用Ant Design */
.custom-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.custom-modal {
  background: #1a1a1a;
  border-radius: 12px;
  width: 90vw;
  max-width: 1400px;
  min-width: 800px;
  max-height: 90vh;
  overflow: hidden;
  position: relative;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.custom-modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  background: transparent;
  border: none;
  color: #ffffff;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
  z-index: 10;
}

.custom-modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .custom-modal {
    width: 95vw;
    min-width: 320px;
    max-height: 95vh;
  }
  
  .custom-modal-overlay {
    padding: 10px;
  }
}

.detail-content {
  display: flex;
  flex-direction: column;
}

.content-layout {
  display: flex;
  gap: 20px;
  flex: 1;
  height: 100%;
}

.action-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.image-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000000;
  border-radius: 8px;
  position: relative;
}

.detail-image-skeleton {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0.1) 0%, 
    rgba(255, 255, 255, 0.2) 50%, 
    rgba(255, 255, 255, 0.1) 100%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 8px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.detail-image-skeleton .skeleton-shimmer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.1) 50%, 
    transparent 100%);
  animation: shimmer 2s infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.detail-image {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  object-fit: contain;
}

.detail-video {
  max-width: 100%;
  max-height: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  object-fit: contain;
}

.action-btn {
  background: #2a2a2a;
  border: 1px solid #444;
  color: #fff;
  border-radius: 6px;
  height: 32px;
  padding: 0 12px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:hover {
  background: #333;
  border-color: #555;
  color: #fff;
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-width: 320px;
  max-width: 400px;
  border-left:1px solid #1a1a1a;
  padding: 24px;
}

.modal-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.modal-title h3 {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  padding: 0;
}

.action-btn.regenerate-btn {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
}

.action-btn.regenerate-btn:hover {
  background: linear-gradient(135deg, #764ba2, #667eea);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.action-btn.remove-favorite-btn {
  background: #dc3545;
  border-color: #dc3545;
  color: #fff;
}

.action-btn.remove-favorite-btn:hover {
  background: #c82333;
  border-color: #bd2130;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0;
}

.info-label {
  color: #888;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 2px;
}

.info-value {
  color: #fff;
  font-size: 14px;
  flex: 1;
}

.task-id {
  font-family: monospace;
  font-size: 12px;
  color: #666;
  word-break: break-all;
}

.reference-image-container {
  flex: 1;
}

.reference-image {
  display: flex;
  align-items: center;
  gap: 8px;
}

.reference-image.no-image {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  padding: 12px;
  color: #888;
  font-size: 14px;
}

.reference-img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #333;
  background: #2a2a2a;
}

.prompt-display {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  padding: 12px;
  color: #ccc;
  font-size: 14px;
  flex: 1;
  min-height: 40px;
  line-height: 1.4;
  word-break: break-word;
}
</style>
