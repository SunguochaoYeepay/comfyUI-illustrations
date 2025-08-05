<template>
  <div class="image-generator">
    

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 上方：历史图片展示区域 -->
      <div class="gallery-section">
       
        <!-- 生成状态 -->
        <div v-if="isGenerating" class="generating-state">
          <div class="task-card">
            <!-- 任务信息头部 -->
            <div class="task-header">
              <div class="task-info">
                <p class="task-prompt">{{ prompt || '正在生成图片...' }}</p>
                <p class="task-meta">{{ imageCount }}张图片 · 正在生成中...</p>
              </div>
            </div>
            
            <!-- 图片占位符网格 -->
            <div class="images-grid" :data-count="imageCount">
              <div
                v-for="index in imageCount"
                :key="index"
                class="image-item"
              >
                <div class="image-container loading-placeholder">
                  <div class="loading-content">
                    <a-spin size="large" />
                    <p>生成中...</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 图像展示网格 -->
        <div v-else-if="allImages.length > 0" class="image-gallery">
          <div
            v-for="(group, groupIndex) in imageGroups"
            :key="groupIndex"
            class="task-card"
          >
            <!-- 任务信息头部 -->
            <div class="task-header">
              <div class="task-info">
                <p class="task-prompt">{{ group[0]?.prompt || '无提示词' }}</p>
                <p class="task-meta">{{ group.length }}张图片 · {{ new Date(group[0]?.createdAt).toLocaleString() }}</p>
              </div>
              <div class="task-actions">
                <!-- 图片组导航按钮 -->
                <div v-if="group.length > 1" class="image-nav-controls">
                  <span class="image-counter">{{ getCurrentImageIndex(groupIndex) + 1 }} / {{ group.length }}</span>
                  <a-button type="text" size="small" @click.stop="showPrevImage(groupIndex)" class="nav-btn" title="上一张" :disabled="getCurrentImageIndex(groupIndex) === 0">
                    ←
                  </a-button>
                  <a-button type="text" size="small" @click.stop="showNextImage(groupIndex)" class="nav-btn" title="下一张" :disabled="getCurrentImageIndex(groupIndex) === group.length - 1">
                    →
                  </a-button>
                </div>
                
                <!-- 操作按钮 -->
                <div class="action-buttons">
                  <a-button type="text" size="small" @click.stop="regenerateImage(group[0])" class="action-btn" title="重新生成">
                    <template #icon><ReloadOutlined /></template>
                  </a-button>
                  <a-button type="text" size="small" @click.stop="deleteImage(group[0])" class="action-btn delete-btn" title="删除">
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </div>
              </div>
            </div>
            
            <!-- 图片网格 -->
            <div class="images-grid" :data-count="group.length > 1 ? 1 : group.length">
              <!-- 当有多张图片时，只显示当前选中的图片 -->
              <template v-if="group.length > 1">
                <div class="image-item">
                  <!-- 图像容器 -->
                  <div class="image-container">
                    <img :src="group[getCurrentImageIndex(groupIndex)].url" :alt="group[getCurrentImageIndex(groupIndex)].prompt" class="gallery-image" />
                  </div>
                </div>
              </template>
              
              <!-- 当只有一张图片时，正常显示 -->
              <template v-else>
                <div
                  v-for="(image, index) in group"
                  :key="index"
                  class="image-item"
                >
                  <!-- 图像容器 -->
                  <div class="image-container">
                    <img :src="image.url" :alt="image.prompt" class="gallery-image" />
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-gallery">
          <div class="empty-content">
            <PictureOutlined class="empty-icon" />
            <h3>还没有生成图像</h3>
            <p>输入您的创意提示词，开始创作第一张图像吧！</p>
          </div>
        </div>
      </div>

      <!-- 下方：对话框和参数设置 -->
      <div class="control-section">
        <a-card class="control-card">
          <div class="control-layout">
            <!-- 主要输入区域 -->
            <div class="main-input-row">
              <!-- 参考图片区域 -->
              <div class="reference-section">
                 <a-upload
                  v-model:file-list="referenceImages"
                  name="reference"
                  list-type="picture-card"
                  class="reference-upload"
                  :show-upload-list="true"
                  :before-upload="beforeUpload"
                  @preview="handlePreview"
                  @remove="handleRemove"
                  :style="{ '--ant-upload-border': 'none !important' }"
                >
                  <div v-if="referenceImages.length < 1">
                    <plus-outlined />
                    <div style="margin-top: 8px">上传参考图</div>
                  </div>
                </a-upload>
              </div>

              <!-- 提示词和生成按钮区域 -->
              <div class="input-group">
                <div class="prompt-generate-row">
                  <a-textarea
                    v-model:value="prompt"
                    placeholder="请详细描述您想要生成的图像，例如：一只可爱的橙色小猫坐在花园里，阳光明媚，高清摄影风格"
                    :rows="2"
                    class="prompt-input"
                  />
                  
                  <a-button
                    type="primary"
                    size="large"
                    :loading="isGenerating"
                    @click="generateImage"
                    class="generate-btn"
                  >
                    <template #icon>
                      <span v-if="!isGenerating">✨</span>
                    </template>
                    {{ isGenerating ? '生成中...' : '生成' }}
                  </a-button>
                </div>
              </div>
            </div>
          </div>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { DownloadOutlined, ShareAltOutlined, EditOutlined, PictureOutlined, PlusOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons-vue'

// API基础URL
const API_BASE = 'http://localhost:9000'

// 响应式数据
const prompt = ref('')
const negativePrompt = ref('blurry, low quality, distorted, deformed, ugly, bad anatomy, extra limbs, missing limbs, watermark, text, signature')
const imageSize = ref('512x512')
const imageCount = ref(parseInt(localStorage.getItem('imageCount')) || 4) // 默认生成4张图片，支持持久化
const isGenerating = ref(false)
const progress = ref(0)
const estimatedTime = ref(30)
const generatedImages = ref([])
const history = ref([])
const referenceImages = ref([])
const previewVisible = ref(false)
const previewImage = ref('')
const currentImageIndexes = ref(new Map()) // 存储每个图片组当前显示的图片索引

// 计算属性：合并所有图像用于展示
const allImages = computed(() => {
  return [...generatedImages.value, ...history.value.flatMap(h => h.images || [])]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, 20) // 最多显示20张图片
})

// 计算属性：将图像按任务分组，每组四张图片
const imageGroups = computed(() => {
  const groups = []
  const taskGroups = new Map()
  
  // 按task_id分组
  allImages.value.forEach(image => {
    const taskId = image.task_id || 'unknown'
    if (!taskGroups.has(taskId)) {
      taskGroups.set(taskId, [])
    }
    taskGroups.get(taskId).push(image)
  })
  
  // 将每个任务组转换为数组，并按时间排序
  Array.from(taskGroups.values())
    .sort((a, b) => new Date(b[0].createdAt) - new Date(a[0].createdAt))
    .forEach(group => {
      groups.push(group)
    })
  
  return groups
})

// 监听imageCount变化，保存到localStorage
watch(imageCount, (newValue) => {
  localStorage.setItem('imageCount', newValue.toString())
})

// 生成图像
const generateImage = async () => {
  if (!prompt.value.trim()) {
    message.warning('请输入图像描述')
    return
  }

  isGenerating.value = true
  progress.value = 0
  
  try {
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (progress.value < 90) {
        progress.value += Math.random() * 10
      }
    }, 1000)

    // 准备FormData
    const formData = new FormData()
    formData.append('description', prompt.value)
    formData.append('count', imageCount.value)
    formData.append('size', imageSize.value)
    formData.append('steps', 20)
    
    // 添加参考图片（如果有的话）
    if (referenceImages.value.length > 0) {
      formData.append('reference_image', referenceImages.value[0].originFileObj)
    } else {
      // 如果没有参考图片，创建一个空白图片
      const canvas = document.createElement('canvas')
      canvas.width = 512
      canvas.height = 512
      const ctx = canvas.getContext('2d')
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, 512, 512)
      const blob = await new Promise(resolve => canvas.toBlob(resolve))
      formData.append('reference_image', blob, 'blank.png')
    }

    // 调用后端API
    const response = await fetch('http://localhost:9000/api/generate-image', {
      method: 'POST',
      body: formData
    })

    clearInterval(progressInterval)

    if (response.ok) {
      const result = await response.json()
      const taskId = result.task_id
      
      // 轮询任务状态
      const pollStatus = async () => {
        try {
          const statusResponse = await fetch(`http://localhost:9000/api/task/${taskId}`)
          if (statusResponse.ok) {
            const statusData = await statusResponse.json()
            progress.value = statusData.progress || 0
            
            if (statusData.status === 'completed' && statusData.result) {
              // 任务完成，获取图像
              const imageUrls = statusData.result.image_urls
              const newImages = imageUrls.map((imageUrl, index) => ({
                id: Date.now() + index,
                task_id: taskId,  // 添加task_id用于删除操作
                url: `http://localhost:9000${imageUrl}`,
                prompt: prompt.value,
                size: imageSize.value,
                createdAt: new Date()
              }))
              
              generatedImages.value = newImages
              
              // 刷新历史记录（从后端获取最新数据）
              await loadHistory()
              
              // 同时保存到本地存储作为备份
              saveHistory()
              
              isGenerating.value = false
              progress.value = 100
              message.success('图像生成成功！')
              return
            } else if (statusData.status === 'failed') {
              isGenerating.value = false
              progress.value = 0
              message.error(statusData.error || '生成失败')
              return
            }
            
            // 继续轮询
            setTimeout(pollStatus, 2000)
          } else {
            isGenerating.value = false
            progress.value = 0
            message.error('查询任务状态失败')
          }
        } catch (error) {
          console.error('轮询错误:', error)
          isGenerating.value = false
          progress.value = 0
          message.error('生成过程中出现错误，请重试')
        }
      }
      
      // 开始轮询
      setTimeout(pollStatus, 1000)
      message.success('任务已提交，正在生成中...')
    } else {
      throw new Error('提交任务失败')
    }
  } catch (error) {
    console.error('生成错误:', error)
    message.error('生成失败，请稍后重试')
    isGenerating.value = false
    progress.value = 0
  }
}



// 选择历史记录
const selectHistoryItem = (item) => {
  prompt.value = item.prompt
}

// 清空历史记录
const clearHistory = async () => {
  try {
    // 调用后端清空API
    const response = await fetch(`${API_BASE}/api/history`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      history.value = []
      generatedImages.value = []
      // 清空本地存储
      localStorage.removeItem('imageGeneratorHistory')
      message.success('历史记录已清空')
    } else {
      throw new Error('清空失败')
    }
  } catch (error) {
    console.error('清空历史记录失败:', error)
    message.error('清空失败，请重试')
  }
}

// 使用图像的提示词
const useImagePrompt = (image) => {
  prompt.value = image.prompt
  message.success('已复制提示词到输入框')
}

// 下载图像
const downloadImage = (image) => {
  const link = document.createElement('a')
  link.href = image.url
  link.download = `ai-generated-${Date.now()}.png`
  link.click()
  message.success('开始下载图像')
}

// 分享图像
const shareImage = (image) => {
  if (navigator.share) {
    navigator.share({
      title: 'AI生成的图像',
      text: image.prompt,
      url: image.url
    })
  } else {
    navigator.clipboard.writeText(image.url)
    message.success('图像链接已复制到剪贴板')
  }
}

// 获取当前图片组显示的图片索引
const getCurrentImageIndex = (groupIndex) => {
  return currentImageIndexes.value.get(groupIndex) || 0
}

// 显示上一张图片
const showPrevImage = (groupIndex) => {
  const currentIndex = getCurrentImageIndex(groupIndex)
  if (currentIndex > 0) {
    currentImageIndexes.value.set(groupIndex, currentIndex - 1)
  }
}

// 显示下一张图片
const showNextImage = (groupIndex) => {
  const group = imageGroups.value[groupIndex]
  const currentIndex = getCurrentImageIndex(groupIndex)
  if (currentIndex < group.length - 1) {
    currentImageIndexes.value.set(groupIndex, currentIndex + 1)
  }
}

// 下载全部图片
const downloadAllImages = async (group) => {
  try {
    for (let i = 0; i < group.length; i++) {
      const image = group[i]
      const response = await fetch(image.url)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `ai-generated-${image.task_id}-${i + 1}.png`
      link.click()
      window.URL.revokeObjectURL(url)
      
      // 添加延迟避免浏览器阻止多个下载
      if (i < group.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }
    }
    message.success(`开始下载 ${group.length} 张图片`)
  } catch (error) {
    console.error('批量下载失败:', error)
    message.error('批量下载失败，请重试')
  }
}

// 重新生成图像
const regenerateImage = async (image) => {
  if (!image.prompt) {
    message.warning('该图像没有提示词，无法重新生成')
    return
  }
  
  // 使用原图像的提示词
  prompt.value = image.prompt
  
  // 开始生成
  await generateImage()
  
  message.info('正在使用原提示词重新生成图像...')
}

// 删除图像
const deleteImage = async (image) => {
  try {
    // 调用后端删除API
    const response = await fetch(`${API_BASE}/api/history/${image.task_id}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      // 从本地历史记录中移除
      const historyIndex = history.value.findIndex(item => item.task_id === image.task_id)
      if (historyIndex > -1) {
        history.value.splice(historyIndex, 1)
      }
      
      // 从生成的图像中移除
      const generatedIndex = generatedImages.value.findIndex(item => item.task_id === image.task_id)
      if (generatedIndex > -1) {
        generatedImages.value.splice(generatedIndex, 1)
      }
      
      // 更新本地存储
      saveHistory()
      
      message.success('图像已删除')
    } else {
      throw new Error('删除失败')
    }
  } catch (error) {
    console.error('删除图像失败:', error)
    message.error('删除失败，请重试')
  }
}

// 格式化时间
const formatTime = (date) => {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

// 参考图上传相关方法
const beforeUpload = (file) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png'
  if (!isJpgOrPng) {
    message.error('只能上传 JPG/PNG 格式的图片!')
    return false
  }
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB!')
    return false
  }
  return false // 阻止自动上传，手动处理
}

const handlePreview = (file) => {
  previewImage.value = file.url || file.preview
  previewVisible.value = true
}

const handleRemove = (file) => {
  const index = referenceImages.value.indexOf(file)
  if (index > -1) {
    referenceImages.value.splice(index, 1)
  }
}

// 加载历史记录
const loadHistory = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/history`)
    if (response.ok) {
      const data = await response.json()
      if (data.tasks && data.tasks.length > 0) {
        // 转换后端数据格式为前端格式
        history.value = data.tasks.map(task => ({
          id: task.task_id,
          task_id: task.task_id,  // 保持task_id字段用于删除操作
          prompt: task.description,
          timestamp: task.created_at,
          status: task.status,
          images: task.result_url ? (() => {
            try {
              // 尝试解析JSON格式的多张图片路径
              const paths = JSON.parse(task.result_url)
              if (Array.isArray(paths)) {
                // 多张图片
                return paths.map((path, index) => ({
                  url: `${API_BASE}/${path}`,
                  filename: `generated_${task.task_id}_${index + 1}.png`,
                  task_id: task.task_id,
                  createdAt: new Date(task.created_at)
                }))
              } else {
                // 单张图片，但是JSON格式
                return [{
                  url: `${API_BASE}/${paths}`,
                  filename: `generated_${task.task_id}.png`,
                  task_id: task.task_id,
                  createdAt: new Date(task.created_at)
                }]
              }
            } catch (e) {
              // 不是JSON格式，按单张图片处理
              return [{
                url: `${API_BASE}${task.result_url}`,
                filename: `generated_${task.task_id}.png`,
                task_id: task.task_id,
                createdAt: new Date(task.created_at)
              }]
            }
          })() : []
        }))
      } else {
        history.value = []
      }
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
    // 如果API失败，尝试从localStorage加载
    try {
      const savedHistory = localStorage.getItem('imageGeneratorHistory')
      if (savedHistory) {
        history.value = JSON.parse(savedHistory)
      }
    } catch (localError) {
      console.error('从本地存储加载历史记录也失败:', localError)
    }
  }
}

// 保存历史记录到本地存储（作为备份）
const saveHistory = () => {
  try {
    localStorage.setItem('imageGeneratorHistory', JSON.stringify(history.value))
  } catch (error) {
    console.error('保存历史记录失败:', error)
  }
}

// 组件挂载时加载历史记录
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.image-generator {
  min-height: 100vh;
  padding: 40px 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
  color: white;
}

.title {
  font-size: 2.5rem;
  font-weight: bold;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.icon {
  font-size: 2rem;
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.7;
  margin: 10px 0 0 0;
  color: #999;
}

.main-content {
  display: flex;
  flex-direction: column;
  margin: 0 auto;
  width: 60%;
  max-width: 80%;
  padding: 0 20px;
  padding-bottom: 120px;
}

.gallery-section {
  flex: 1;
  overflow: hidden;
  margin-bottom: 20px;
}

.gallery-card {
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  min-height: 400px;
}

.control-section {
  position: fixed;
  bottom: 0;
  left: 10%;
  right: 10%;
  z-index: 1000;
  padding: 10px 20px;
  max-width: 50%;
  margin: 0 auto;
}

.control-card {
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  background: #1a1a1a;
  border: 1px solid #333;
}

.control-card .ant-card-body {
  background: #1a1a1a;
  color: #fff;
}

.control-card .ant-card-head {
  background: #1a1a1a;
  border-bottom: 1px solid #333;
}

.control-card .ant-card-head-title {
  color: #fff;
}

.control-layout {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0 auto;
}

.main-input-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 8px;
}

.reference-section {
  flex-shrink: 0;
  height: 80px;
}
.reference-section div.ant-upload-wrapper.ant-upload-picture-card-wrapper .ant-upload.ant-upload-select{
  height: 80px !important;
  width: 80px !important;
  border: none !important;
  background: #2a2a2a !important;
  border-radius: 6px !important;
}

.input-group {
  flex: 1;
}

/* 提示词和生成按钮单行布局 */
.prompt-generate-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.prompt-input {
  flex: 1;
}

.prompt-input .ant-input {
  height: 80px !important;
  resize: none !important;
}

.generate-btn {
  height: 80px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 6px;
  flex-shrink: 0;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .main-input-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .prompt-generate-row {
    flex-direction: column;
    gap: 10px;
  }
   
  .generate-btn {
    width: 100%;
    height: 48px;
  }
}

/* 卡片内边距调整 */
:deep(.ant-card .ant-card-body) {
  padding: 12px !important;
}

/* 图像画廊样式 */
.gallery-section {
  border-radius: 8px;
  padding: 10px;
}

.image-gallery {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 10px 0;
}

/* 任务卡片容器 */
.task-card {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #444;
}

/* 任务头部 */
.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #444;
}

.task-info {
  flex: 1;
  min-width: 0;
  word-wrap: break-word;
  overflow-wrap: break-word;
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-prompt {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
  word-break: break-word;
  white-space: normal;
}

.task-meta {
  color: #999;
  font-size: 14px;
  margin: 0;
  white-space: nowrap;
}

.task-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

/* 操作按钮容器 */
.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 图片组导航控件 */
.image-nav-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #444;
}

.image-counter {
  color: #ccc;
  font-size: 12px;
  font-weight: 500;
  min-width: 40px;
  text-align: center;
}

.nav-btn {
  color: #fff !important;
  border: 1px solid #555 !important;
  background: rgba(255, 255, 255, 0.1) !important;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-weight: bold;
  transition: all 0.2s;
}

.nav-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: #777 !important;
  transform: scale(1.05);
}

.nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}



/* 图片网格 - 根据图片数量动态调整列数 */
.images-grid {
  display: grid;
  gap: 10px;
  width: 100%;
}

/* 1张图片 */
.images-grid[data-count="1"] {
  grid-template-columns: 400px;
  justify-content: center;
}

/* 2张图片 */
.images-grid[data-count="2"] {
  grid-template-columns: repeat(2, 1fr);
}

/* 4张图片 */
.images-grid[data-count="4"] {
  grid-template-columns: repeat(4, 1fr);
}

/* 6张图片 */
.images-grid[data-count="6"] {
  grid-template-columns: repeat(3, 1fr);
}

/* 生成状态下保持相同布局 */
.generating-state .images-grid {
  /* 继承上面的布局规则 */
}

/* 单张图片项 */
.image-item {
  position: relative;
}

/* Loading占位符样式 */
.loading-placeholder {
  background: #2a2a2a !important;
  border: 2px dashed #444;
  border-radius: 8px;
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.loading-placeholder::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #2a2a2a;
  z-index: 1;
}

.loading-placeholder .loading-content {
  position: relative;
  z-index: 2;
}

/* 确保生成状态下的图片项正确显示 */
.generating-state .image-item {
  min-width: 0;
  width: 100%;
}

.loading-content {
  text-align: center;
  color: #999;
}

.loading-content p {
  margin: 10px 0 0 0;
  font-size: 14px;
}

/* 移动端响应式 */
@media (max-width: 1024px) {
  .images-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
}

@media (max-width: 768px) {
  .images-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .task-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .task-actions {
    align-self: flex-start;
  }
}

.gallery-item {
  border-radius: 12px;
  overflow: hidden;
  background: #2a2a2a;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
  display: flex;
  flex-direction: column;
}

.gallery-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* 提示词头部 */
.image-prompt-header {
  padding: 8px 10px;
  background: #333;
  border-bottom: 1px solid #444;
}

.image-prompt-text {
  color: #fff;
  font-size: 14px;
  line-height: 1.4;
  margin: 0;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 图像容器 */
.image-container {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
}

.gallery-image {
  width: 100%;
  height: auto;
  aspect-ratio: 1;
  object-fit: cover;
  transition: transform 0.3s;
  border-radius: 8px;
}

.image-container:hover .gallery-image {
  transform: scale(1.05);
}

/* 底部操作按钮 */
.image-actions {
  padding: 6px;
  background: #333;
  display: flex;
  justify-content: center;
  gap: 2px;
  border-top: 1px solid #444;
}

.action-btn {
  color: #fff !important;
  border: none !important;
  background: rgba(255, 255, 255, 0.1) !important;
  backdrop-filter: blur(10px);
  border-radius: 4px;
  transition: all 0.2s;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  transform: scale(1.1);
}

.delete-btn:hover {
  background: rgba(255, 77, 77, 0.3) !important;
  color: #ff6b6b !important;
}

.empty-gallery {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #666;
}

.empty-content {
  text-align: center;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
  color: #444;
}

.empty-content h3 {
  color: #999;
  margin-bottom: 10px;
}

.empty-content p {
  color: #666;
  margin: 0;
}

/* 控制区域样式 */
.prompt-area {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.prompt-section,
.negative-prompt-section,
.example-section {
  margin-bottom: 0;
}

.settings-area {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-grid {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #fff;
  font-size: 0.9rem;
}

.prompt-input,
.negative-prompt-input {
  border-radius: 8px;
  font-size: 0.9rem;
}

.prompt-input textarea.ant-input {
  height: 80px !important;
  min-height: 80px !important;
  max-height: 80px !important;
  resize: none !important;
}

.setting-select {
  width: 100%;
}

.count-slider {
  margin: 10px 0;
}

.generate-section {
  margin-top: auto;
}

.generate-btn {
  height: 80px;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.example-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-tag {
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.8rem;
}

.example-tag:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.gallery-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
}

.gallery-actions {
  display: flex;
  gap: 10px;
}

.clear-btn {
  color: #ff6b6b !important;
  border-color: #ff6b6b !important;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: #ff6b6b !important;
  color: white !important;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.history-item:hover {
  background-color: #f5f5f5;
}

.history-thumbnail {
  width: 50px;
  height: 50px;
  border-radius: 6px;
  object-fit: cover;
}

.history-info {
  flex: 1;
}

.history-prompt {
  font-size: 0.9rem;
  margin: 0 0 5px 0;
  color: #333;
}

.history-time {
  font-size: 0.8rem;
  margin: 0;
  color: #666;
}

.display-panel {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.generating-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.loading-container {
  text-align: center;
}

.loading-container h3 {
  margin: 20px 0 10px 0;
  color: #333;
}

.loading-container p {
  color: #666;
  margin-bottom: 20px;
}

.progress-bar {
  width: 200px;
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
  margin: 0 auto;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
}

.image-grid {
  display: grid;
  gap: 20px;
  width: 100%;
}

/* 主图片网格布局 - 根据图片数量调整 */
.image-grid[data-count="1"] {
  grid-template-columns: 400px;
}

.image-grid[data-count="2"] {
  grid-template-columns: repeat(2, 1fr);
}

.image-grid[data-count="3"] {
  grid-template-columns: repeat(3, 1fr);
}

.image-grid[data-count="4"] {
  grid-template-columns: repeat(4, 1fr);
}

.image-grid[data-count="5"], .image-grid[data-count="6"] {
  grid-template-columns: repeat(3, 1fr);
}

/* 超过6张图片时使用响应式布局 */
.image-grid:not([data-count="1"]):not([data-count="2"]):not([data-count="3"]):not([data-count="4"]):not([data-count="5"]):not([data-count="6"]) {
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

.image-card {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.image-card:hover {
  transform: translateY(-5px);
}

.image-container {
  position: relative;
  overflow: hidden;
  aspect-ratio: 1;
  border-radius: 8px;
}

.generated-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.image-container:hover .generated-image {
  transform: scale(1.05);
}



.image-info {
  padding: 15px;
}

.image-prompt {
  font-weight: 600;
  margin: 0 0 5px 0;
  color: #333;
}

.image-meta {
  font-size: 0.9rem;
  color: #666;
  margin: 0;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 500px;
}

.empty-container {
  text-align: center;
  max-width: 400px;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
}

.empty-container h3 {
  font-size: 1.5rem;
  margin: 0 0 10px 0;
  color: #333;
}

.empty-container p {
  color: #666;
  margin-bottom: 30px;
  line-height: 1.6;
}

.example-prompts h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.example-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.example-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.example-tag:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
}

@media (max-width: 768px) {
  .main-content {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .image-grid {
    grid-template-columns: 1fr;
  }
}
/* 深色主题全局覆盖 */
.image-generator .ant-input,
.image-generator .ant-input-affix-wrapper,
.image-generator .ant-select-selector,
.image-generator .ant-slider {
  background: #2a2a2a !important;
  border-color: #444 !important;
  color: #fff !important;
}

.image-generator .ant-input::placeholder {
  color: #999 !important;
}

.image-generator .ant-input:focus,
.image-generator .ant-input-affix-wrapper:focus,
.image-generator .ant-input-affix-wrapper-focused {
  border-color: #667eea !important;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
}

.image-generator .ant-select-dropdown {
  background: #2a2a2a !important;
  border: 1px solid #444 !important;
}

.image-generator .ant-select-item {
  color: #fff !important;
}

.image-generator .ant-select-item:hover {
  background: #333 !important;
}

.image-generator .ant-select-item-option-selected {
  background: #667eea !important;
}

.image-generator .ant-slider-rail {
  background: #444 !important;
}

.image-generator .ant-slider-track {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

.image-generator .ant-slider-handle {
  border-color: #667eea !important;
  background: #667eea !important;
}

.image-generator .ant-tag {
  background: #2a2a2a !important;
  border-color: #444 !important;
  color: #fff !important;
}

.image-generator .ant-card {
  background: #1a1a1a !important;
  border-color: #333 !important;
}

.image-generator .ant-card-head {
  background: #1a1a1a !important;
  border-bottom-color: #333 !important;
}

.image-generator .ant-card-head-title {
  color: #fff !important;
}

.image-generator .ant-card-body {
  background: #1a1a1a !important;
  color: #fff !important;
}

/* 参考图上传区域样式 */
.reference-upload {
  background: #1a1a1a;
  border-radius: 8px;
  text-align: center;
  transition: border-color 0.3s;
}

.reference-upload .ant-upload-list-picture-card {
  height: 80px !important;
  width: 80px !important;
}

.reference-upload .ant-upload-select {
  height: 80px !important;
  width: 80px !important;
  border: none !important;
  border-style: none !important;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2a2a2a !important;
  border-radius: 6px !important;
}

/* 强制覆盖Ant Design默认样式 */
.image-generator .reference-upload .ant-upload.ant-upload-select {
  border: none !important;
  border-style: none !important;
  background: #2a2a2a !important;
}

.image-generator .reference-section .ant-upload.ant-upload-select {
  border: none !important;
  border-style: none !important;
  background: #2a2a2a !important;
}

.reference-upload .ant-upload-list-picture-card .ant-upload-list-item {
  border: none !important;
  height: 80px !important;
  width: 80px !important;
}
.reference-upload:hover {
  border-color: #667eea;
}

.reference-upload .ant-upload {
  width: 100%;
}

.reference-upload .ant-upload-drag {
  background: transparent !important;
  border: none !important;
}

.reference-upload .ant-upload-drag:hover {
  background: rgba(102, 126, 234, 0.1) !important;
}

.reference-upload .ant-upload-drag-icon {
  color: #667eea !important;
}

.reference-upload .ant-upload-text {
  color: #fff !important;
}

.reference-upload .ant-upload-hint {
  color: #999 !important;
}

/* 修复上传组件内所有文字颜色 */
.reference-upload .ant-upload-select .ant-upload {
  color: #fff !important;
}

.reference-upload .ant-upload-select .ant-upload * {
  color: #fff !important;
}

.reference-upload .ant-upload-select-picture-card {
  color: #fff !important;
}

.reference-upload .ant-upload-select-picture-card .ant-upload-text {
  color: #fff !important;
}

.reference-upload .ant-upload-select-picture-card .ant-upload-hint {
  color: #999 !important;
}

.reference-images {
  margin-top: 15px;
}

.reference-images .ant-upload-list-item {
  background: #2a2a2a !important;
  border-color: #444 !important;
}

</style>

<style>
/* 全局强制覆盖Ant Design上传组件样式 */
.ant-upload.ant-upload-select {
  border: none !important;
  border-style: none !important;
  width: 80px !important;
  height: 80px !important;
  background: #2a2a2a !important;
  border-radius: 6px !important;
}

.ant-upload-wrapper .ant-upload.ant-upload-select {
  border: none !important;
  border-style: none !important;
  width: 80px !important;
  height: 80px !important;
  background: #2a2a2a !important;
  border-radius: 6px !important;
}

.ant-upload-picture-card-wrapper .ant-upload.ant-upload-select {
  border: none !important;
  border-style: none !important;
  width: 80px !important;
  height: 80px !important;
  background: #2a2a2a !important;
  border-radius: 6px !important;
}

/* 全局强制覆盖Ant Design输入框样式 */
.ant-input {
  height: 80px !important;
  min-height: 80px !important;
  max-height: 80px !important;
}

textarea.ant-input {
  height: 80px !important;
  min-height: 80px !important;
  max-height: 80px !important;
  resize: none !important;
}
</style>