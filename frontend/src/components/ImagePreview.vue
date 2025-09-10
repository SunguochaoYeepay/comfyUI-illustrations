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
            <!-- 视频播放器 -->
            <video 
              v-if="isVideoTask"
              :src="imageData.url" 
              class="preview-video"
              controls
              preload="metadata"
              @click.stop
            />
            <!-- 图片显示 -->
            <img 
              v-else
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
               <DownloadOutlined /> {{ isVideoTask ? '下载视频' : '下载' }}
             </a-button>
             <!-- 收藏按钮 -->
             <a-button 
               type="default" 
               :class="['action-btn', 'favorite-btn', { 'favorited': imageData.isFavorited }]" 
               @click="toggleFavorite"
             >
               {{ imageData.isFavorited ? '取消收藏' : '收藏' }}
             </a-button>
             <!-- 图片任务才显示放大和生成视频按钮 -->
             <template v-if="!isVideoTask">
               <a-dropdown :disabled="isUpscaling">
                 <a-button type="primary" ghost :loading="isUpscaling">
                   <ZoomInOutlined /> 高清放大
                   <DownOutlined />
                 </a-button>
                 <template #overlay>
                   <a-menu @click="handleUpscaleSelect">
                     <a-menu-item key="2" :disabled="isUpscaling">
                       <ZoomInOutlined /> 2倍放大 (1024×1024)
                     </a-menu-item>
                     <a-menu-item key="3" :disabled="isUpscaling">
                       <ZoomInOutlined /> 3倍放大 (1536×1536)
                     </a-menu-item>
                     <a-menu-item key="4" :disabled="isUpscaling">
                       <ZoomInOutlined /> 4倍放大 (2048×2048)
                     </a-menu-item>
                   </a-menu>
                 </template>
               </a-dropdown>
               <a-button type="primary" ghost @click="showVideoGenerator">
                 <VideoCameraOutlined /> 生成视频
               </a-button>
             </template>
           </div>
          
          
          
          <div class="info-content">
            <!-- 参考图 -->
            <div class="info-item" v-if="processedReferenceImage">
              <label>参考图:</label>
              <div class="info-value reference-image">
                <!-- 多图融合时显示多张参考图 -->
                <div v-if="Array.isArray(processedReferenceImage)" class="reference-images-grid">
                  <div 
                    v-for="(imageUrl, index) in processedReferenceImage" 
                    :key="index"
                    class="reference-image-item"
                  >
                    <img 
                      :src="imageUrl" 
                      :alt="`参考图 ${index + 1}`"
                      class="reference-img"
                      @click="viewReferenceImage(imageUrl)"
                      @error="handleReferenceImageError"
                    />
                    <span class="reference-image-label">{{ index + 1 }}</span>
                  </div>
                </div>
                <!-- 单图时显示一张参考图 -->
                <div v-else>
                  <img 
                    :src="processedReferenceImage" 
                    alt="参考图"
                    class="reference-img"
                    @click="viewReferenceImage(processedReferenceImage)"
                    @error="handleReferenceImageError"
                    v-show="!referenceImageError"
                  />
                  <div v-if="referenceImageError" class="reference-image-error">
                    <span class="error-icon">⚠️</span>
                    <span class="error-text">参考图加载失败</span>
                  </div>
                </div>
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
            
            <!-- 使用的模型 -->
            <div class="info-item" v-if="imageData.parameters?.model">
              <label>使用模型:</label>
              <div class="info-value model-info">
                <span class="model-name">{{ getModelDisplayName(imageData.parameters.model) }}</span>
                <span class="model-type">{{ getModelType(imageData.parameters.model) }}</span>
              </div>
            </div>
            
            <!-- 使用的LoRA -->
            <div class="info-item" v-if="imageData.parameters?.loras && imageData.parameters.loras.length > 0">
              <label>使用LoRA:</label>
              <div class="info-value lora-list">
                <div 
                  v-for="(lora, index) in imageData.parameters.loras" 
                  :key="index"
                  class="lora-item"
                >
                  <span class="lora-name">{{ lora.name.replace('.safetensors', '') }}</span>
                  <span class="lora-strength" v-if="lora.strength_model !== undefined">
                    (强度: {{ lora.strength_model }})
                  </span>
                </div>
              </div>
            </div>
            
            <!-- 其他生成参数 -->
            <div class="info-item" v-if="imageData.parameters">
              <label>其他参数:</label>
              <div class="info-value parameters">
                <div class="param-item" v-if="imageData.parameters.steps">
                  <span class="param-label">步数:</span>
                  <span class="param-value">{{ imageData.parameters.steps }}</span>
                </div>
                <div class="param-item" v-if="imageData.parameters.seed">
                  <span class="param-label">种子:</span>
                  <span class="param-value">{{ imageData.parameters.seed }}</span>
                </div>
                <div class="param-item" v-if="imageData.parameters.size">
                  <span class="param-label">尺寸:</span>
                  <span class="param-value">{{ imageData.parameters.size }}</span>
                </div>
                <div class="param-item" v-if="imageData.parameters.count">
                  <span class="param-label">数量:</span>
                  <span class="param-value">{{ imageData.parameters.count }}</span>
                </div>
              </div>
            </div>
                     </div>
         </div>
       </div>
     </div>
     
     
   </div>
   
   
   <!-- 视频生成器底部面板 -->
   <VideoGenerator 
     v-if="videoGeneratorVisible"
     :reference-image="props.imageData.url"
     :is-in-modal="true"
     @task-created="handleVideoTaskCreated"
     @close="closeVideoGenerator"
   />
 </template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { CloseOutlined, DownloadOutlined, ZoomInOutlined, LeftOutlined, RightOutlined, DownOutlined, VideoCameraOutlined, HeartOutlined, HeartFilled } from '@ant-design/icons-vue'
import VideoGenerator from './VideoGenerator.vue'

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
  },
  isUpscaling: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['close', 'navigate', 'upscale', 'refreshHistory', 'video-task-created'])

// 计算属性：判断是否为视频任务
const isVideoTask = computed(() => {
  const { prompt, url, result_path, model } = props.imageData
  return (
    (prompt && prompt.includes('视频生成')) ||
    (url && (url.includes('/api/generate-video') || /\.(mp4|avi|mov|webm)$/i.test(url))) ||
    (result_path && (result_path.includes('video') || /\.(mp4|avi|mov|webm)$/i.test(result_path))) ||
    (model && model.includes('wan'))
  )
})

// 响应式数据
const referenceImageError = ref(false)
const videoGeneratorVisible = ref(false)

// 处理参考图URL，支持多图融合的情况
const processedReferenceImage = computed(() => {
  if (!props.imageData.referenceImage) return null
  
  let imageUrl = props.imageData.referenceImage
  
  // 如果是数组字符串，解析为数组
  if (typeof imageUrl === 'string' && imageUrl.startsWith('[') && imageUrl.endsWith(']')) {
    try {
      const imageArray = JSON.parse(imageUrl)
      // 多图融合时，返回所有图片的数组
      if (Array.isArray(imageArray) && imageArray.length > 1) {
        return imageArray.map(url => {
          if (typeof url === 'string') {
            // 处理双斜杠问题（但保留协议部分的://）
            if (url.includes('://')) {
              const [protocol, rest] = url.split('://', 2)
              const cleanedRest = rest.replace(/\/\//g, '/')
              return `${protocol}://${cleanedRest}`
            } else {
              return url.replace(/\/\//g, '/')
            }
          }
          return url
        })
      }
      // 单图或数组只有一个元素时，取第一个
      imageUrl = imageArray[0] || imageUrl
    } catch (e) {
      console.warn('解析参考图URL失败:', e)
    }
  }
  
  // 处理双斜杠问题（但保留协议部分的://）
  if (typeof imageUrl === 'string') {
    // 先处理协议部分，避免影响http://
    if (imageUrl.includes('://')) {
      const [protocol, rest] = imageUrl.split('://', 2)
      const cleanedRest = rest.replace(/\/\//g, '/')
      imageUrl = `${protocol}://${cleanedRest}`
    } else {
      imageUrl = imageUrl.replace(/\/\//g, '/')
    }
  }
  
  return imageUrl
})

// 移除本地的isUpscaling状态，使用props中的isUpscaling

// 显示视频生成器
const showVideoGenerator = () => {
  console.log('显示视频生成器')
  videoGeneratorVisible.value = true
}

// 关闭视频生成器
const closeVideoGenerator = () => {
  videoGeneratorVisible.value = false
}

// 处理参考图加载错误
const handleReferenceImageError = () => {
  console.warn('参考图加载失败:', processedReferenceImage.value)
  referenceImageError.value = true
}

// 监听图片数据变化，重置错误状态
watch(() => props.imageData, () => {
  referenceImageError.value = false
}, { deep: true })

// 关闭预览
const closePreview = () => {
  // 同时关闭视频生成器
  videoGeneratorVisible.value = false
  emit('close')
}

// 点击遮罩层关闭
const handleOverlayClick = (e) => {
  if (e.target === e.currentTarget) {
    closePreview()
  }
}

// 下载图片或视频
const downloadImage = async () => {
  try {
    const response = await fetch(props.imageData.url)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 根据任务类型设置文件名
    if (isVideoTask.value) {
      link.download = `generated-video-${Date.now()}.mp4`
    } else {
      link.download = `generated-image-${Date.now()}.png`
    }
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success(isVideoTask.value ? '视频下载成功' : '图片下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    message.error(isVideoTask.value ? '视频下载失败' : '图片下载失败')
  }
}

// 切换收藏状态
const toggleFavorite = async () => {
  try {
    let response
    if (isVideoTask.value) {
      // 视频收藏
      response = await fetch(`/api/video/${props.imageData.task_id}/favorite`, {
        method: 'POST'
      })
    } else {
      // 图片收藏
      response = await fetch(`/api/image/${props.imageData.task_id}/${props.imageData.image_index || 0}/favorite`, {
        method: 'POST'
      })
    }
    
    if (response.ok) {
      const result = await response.json()
      
      // 更新本地状态
      props.imageData.isFavorited = result.is_favorited
      
      // 显示提示信息
      if (result.is_favorited) {
        message.success('已添加到收藏')
      } else {
        message.success('已取消收藏')
      }
      
      // 通知父组件刷新历史记录
      emit('refreshHistory')
    } else {
      throw new Error('切换收藏状态失败')
    }
  } catch (error) {
    console.error('切换收藏状态失败:', error)
    message.error('操作失败，请重试')
  }
}

// 处理放大倍数选择
const handleUpscaleSelect = async (e) => {
  const scaleFactor = parseInt(e.key)
  console.log('选择放大倍数:', scaleFactor)
  // 触发放大事件，传递给父组件处理
  emit('upscale', props.imageData, scaleFactor)
}

// 处理视频任务创建
const handleVideoTaskCreated = (taskId) => {
  console.log('视频生成任务已创建，任务ID:', taskId)
  message.success('视频生成任务已创建，请在任务列表中查看进度')
  videoGeneratorVisible.value = false
  
  // 通知父组件开始轮询视频任务状态
  emit('video-task-created', taskId)
  
  // 同时刷新历史记录
  emit('refreshHistory')
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

// 获取模型显示名称
const getModelDisplayName = (modelName) => {
  const modelMap = {
    'flux1-dev': 'Flux Kontext',
    'qwen-image': 'Qwen Image'
  }
  return modelMap[modelName] || modelName
}

// 获取模型类型
const getModelType = (modelName) => {
  if (modelName.includes('flux')) {
    return 'Flux模型 - 更精确控制'
  } else if (modelName.includes('qwen')) {
    return 'Qwen模型 - 支持中文较好'
  }
  return '未知模型'
}

// 查看参考图
const viewReferenceImage = (imageUrl = null) => {
  const url = imageUrl || processedReferenceImage.value
  if (url) {
    window.open(url, '_blank')
  }
}



// 防抖标志
let isNavigating = false

// 导航到下一张图片
const navigateNext = () => {
  // 防抖处理
  if (isNavigating) {
    console.log('导航正在进行中，跳过此次调用')
    return
  }
  
  console.log('=== ImagePreview navigateNext 调试 ===')
  console.log('当前索引:', props.currentIndex)
  console.log('图片列表长度:', props.imageList.length)
  console.log('是否可以导航:', props.currentIndex < props.imageList.length - 1)
  
  if (props.currentIndex < props.imageList.length - 1) {
    isNavigating = true
    const nextIndex = props.currentIndex + 1
    console.log('发出navigate事件，目标索引:', nextIndex)
    emit('navigate', nextIndex)
    
    // 重置防抖标志
    setTimeout(() => {
      isNavigating = false
    }, 100)
  } else {
    console.log('已经是最后一张图片，无法导航')
  }
}

// 导航到上一张图片
const navigatePrev = () => {
  // 防抖处理
  if (isNavigating) {
    console.log('导航正在进行中，跳过此次调用')
    return
  }
  
  if (props.currentIndex > 0) {
    isNavigating = true
    emit('navigate', props.currentIndex - 1)
    
    // 重置防抖标志
    setTimeout(() => {
      isNavigating = false
    }, 100)
  }
}

// 键盘事件处理
const handleKeydown = (e) => {
  if (!props.visible) return
  
  switch (e.key) {
    case 'ArrowLeft':
      e.preventDefault()
      e.stopPropagation()
      navigatePrev()
      break
    case 'ArrowRight':
      e.preventDefault()
      e.stopPropagation()
      navigateNext()
      break
    case 'Escape':
      e.preventDefault()
      e.stopPropagation()
      closePreview()
      break
  }
}

// 键盘事件监听器引用
let keydownListener = null

// 生命周期钩子
onMounted(() => {
  // 确保只绑定一次事件监听器
  if (!keydownListener) {
    keydownListener = handleKeydown
    document.addEventListener('keydown', keydownListener)
    console.log('键盘事件监听器已绑定')
  }
})

onUnmounted(() => {
  // 确保移除事件监听器
  if (keydownListener) {
    document.removeEventListener('keydown', keydownListener)
    keydownListener = null
    console.log('键盘事件监听器已移除')
  }
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

.preview-video {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
}

.image-actions {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-bottom: 1px solid #444;
}

.info-panel {
  width: 460px;
  border-left: 1px solid #444;
  display: flex;
  flex-direction: column;
}

.info-header {
  padding: 16px 20px;
}

.info-header h3 {
  margin: 0;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.info-content {
  flex: 1;
  padding: 16px 20px;
  overflow-y: auto;
}

.info-item {
  margin-bottom: 16px;
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

/* 模型信息样式 */
.model-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.model-name {
  font-weight: 600;
  color: #667eea;
  font-size: 16px;
}

.model-type {
  font-size: 12px;
  color: #999;
  font-style: italic;
}

/* LoRA信息样式 */
.lora-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lora-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.lora-item:hover {
  border-color: #667eea;
  background: #333;
}

.lora-name {
  font-weight: 500;
  color: #fff;
  flex: 1;
}

.lora-strength {
  font-size: 12px;
  color: #999;
  background: #444;
  padding: 2px 6px;
  border-radius: 4px;
}

/* 参数项样式 */
.param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid #444;
}

.param-item:last-child {
  border-bottom: none;
}

.param-label {
  color: #999;
  font-size: 12px;
  font-weight: 500;
}

.param-value {
  color: #fff;
  font-weight: 600;
  font-family: 'Courier New', monospace;
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

/* 多图参考图网格样式 */
.reference-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 8px;
  max-width: 300px;
}

.reference-image-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.reference-image-item .reference-img {
  max-width: 80px;
  max-height: 80px;
  width: 100%;
  height: auto;
  object-fit: cover;
}

.reference-image-label {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  border: 2px solid #333;
}

.reference-image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 120px;
  height: 120px;
  background: #333;
  border: 2px dashed #666;
  border-radius: 6px;
  color: #999;
  font-size: 12px;
  text-align: center;
}

.error-icon {
  font-size: 24px;
  margin-bottom: 4px;
}

.error-text {
  font-size: 10px;
  line-height: 1.2;
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

/* 图标样式 */
.action-icon {
  width: 16px;
  height: 16px;
  transition: all 0.2s ease;
}

.action-icon.favorited {
  color: #ff4757;
}

/* 收藏按钮样式 */
.favorite-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
}

.favorite-btn:hover {
  background: rgba(255, 107, 107, 0.2);
  border-color: rgba(255, 107, 107, 0.4);
  color: #ff6b6b;
}

.favorite-btn.favorited {
  background: rgba(255, 107, 107, 0.3);
  border-color: rgba(255, 107, 107, 0.5);
  color: #ff6b6b;
}

.favorite-btn.favorited:hover {
  background: rgba(255, 107, 107, 0.4);
  border-color: rgba(255, 107, 107, 0.6);
}





</style>