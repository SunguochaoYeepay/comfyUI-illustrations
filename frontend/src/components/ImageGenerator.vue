<template>
  <div class="image-generator main-container">
    <!-- 主要内容区域 -->
    <div class="main-content">
     
      <!-- 图片展示区域 -->
      <ImageGallery
        :all-images="allImages"
        :is-generating="isGenerating"
        :prompt="prompt"
        :image-count="imageCount"
        :progress="progress"
        @edit-image="editImage"
        @regenerate-image="regenerateImage"
        @delete-image="deleteImage"
        @download-image="downloadImage"
      />

      <!-- 控制面板 -->
      <ImageControlPanel
        v-model:prompt="prompt"
        v-model:reference-images="referenceImages"
        :is-generating="isGenerating"
        @generate="generateImage"
        @preview="handlePreview"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import ImageGallery from './ImageGallery.vue'
import ImageControlPanel from './ImageControlPanel.vue'

// API基础URL - 使用相对路径，通过Vite代理转发
const API_BASE = ''





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
// 移除了图片索引存储变量

// 计算属性：合并所有图像用于展示
const allImages = computed(() => {
  const generated = generatedImages.value || []
  const hist = history.value || []
  
  // 将历史记录中的图片展开
  const historyImages = hist.flatMap(item => 
    (item.images || []).map(img => ({
      ...img,
      prompt: item.prompt,
      timestamp: item.timestamp,
      status: item.status
    }))
  )
  
  // 按时间正序排列，确保最新生成的图片显示在最后面
  const result = [...generated, ...historyImages]
    .sort((a, b) => new Date(a.createdAt || a.timestamp) - new Date(b.createdAt || b.timestamp))
  
  return result
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
  
  // 将每个任务组转换为数组，并按时间正序排序（最新的在后面）
  Array.from(taskGroups.values())
    .sort((a, b) => new Date(a[0].createdAt) - new Date(b[0].createdAt))
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
    const response = await fetch('/api/generate-image', {
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
          const statusResponse = await fetch(`/api/task/${taskId}`)
          if (statusResponse.ok) {
            const statusData = await statusResponse.json()
            progress.value = statusData.progress || 0
            
            if (statusData.status === 'completed' && statusData.result) {
              // 任务完成，获取图像
              const imageUrls = statusData.result.image_urls
              const filenames = statusData.result.filenames || []
              const directUrls = statusData.result.direct_urls || []
              
              const newImages = imageUrls.map((imageUrl, index) => ({
                id: Date.now() + index,
                task_id: taskId,  // 添加task_id用于删除操作
                url: imageUrl,
           directUrl: directUrls[index] ? directUrls[index] : null,
                filename: filenames[index] || `generated_${taskId}_${index + 1}.png`,
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
const downloadImage = async (image) => {
  try {
    // 使用直接URL或常规URL
    const imageUrl = image.directUrl || image.url
    const filename = image.filename || `ai-generated-${Date.now()}.png`
    
    // 创建一个临时链接
    const link = document.createElement('a')
    link.href = imageUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    message.success(`图片 ${filename} 下载已开始`)
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败，请重试')
  }
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

// 移除了图片切换相关函数

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

// 重新编辑图像
const editImage = (image) => {
  if (!image.prompt) {
    message.warning('该图像没有提示词，无法编辑')
    return
  }
  
  // 使用原图像的提示词
  prompt.value = image.prompt
  
  // 如果有参考图，可以尝试回填
  // 这里需要根据实际情况处理参考图的回填
  // 由于原始参考图可能已不可用，这里只回填提示词
  
  // 滚动到输入区域
  document.querySelector('.input-section')?.scrollIntoView({ behavior: 'smooth' })
  
  message.success('已将提示词回填到输入框，您可以进行编辑')
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

// 处理参考图预览
const handlePreview = (file) => {
  previewImage.value = file.url || file.preview
  previewVisible.value = true
}

// 处理任务图片数据的辅助函数
const processTaskImages = (task) => {
  if (!task.result_url || task.status !== 'completed') {
    return []
  }
  
  // 获取文件名和直接URL（如果有）
  let filenames = []
  let directUrls = []
  
  if (task.filenames) {
    try {
      filenames = JSON.parse(task.filenames)
    } catch (e) {
      console.warn('解析文件名失败:', e)
    }
  }
  
  if (task.direct_urls) {
    try {
      directUrls = JSON.parse(task.direct_urls)
    } catch (e) {
      console.warn('解析直接URL失败:', e)
    }
  }
  
  // 如果有文件名信息，说明是多张图片
  if (filenames.length > 0) {
    const images = filenames.map((filename, index) => {
      const imageUrl = directUrls[index] || `${task.result_url}?index=${index}`
      return {
        url: imageUrl,
        directUrl: directUrls[index] || null,
        filename: filename,
        task_id: task.task_id,
        prompt: task.description,
        createdAt: new Date(task.created_at)
      }
    })
    return images
  } else {
    // 单张图片或没有详细信息
    const imageUrl = task.result_url
    
    return [{
      url: imageUrl,
      directUrl: null,
      filename: `generated_${task.task_id}.png`,
      task_id: task.task_id,
      prompt: task.description,
      createdAt: new Date(task.created_at)
    }]
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
        history.value = data.tasks.map(task => {
          const processedImages = processTaskImages(task)
          return {
            id: task.task_id,
            task_id: task.task_id,  // 保持task_id字段用于删除操作
            prompt: task.description,
            timestamp: task.created_at,
            status: task.status,
            images: processedImages
          }
        })
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

.main-content {
  display: flex;
  flex-direction: column;
  margin: 0 auto;
  width: 60%;
  max-width: 80%;
  padding: 0 20px;
  padding-bottom: 120px;
}

.main-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
  padding: 20px;
  padding-bottom: 200px;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: 30px;
}


/* 参考图片上传样式 */
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

/* 图片缩略图样式 */
.reference-upload .ant-upload-list-picture-card .ant-upload-list-item img {
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
  border-radius: 6px !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  background: none !important;
}

/* 媒体查询 */
@media (max-width: 768px) {
  .main-content {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .title {
    font-size: 2rem;
  }
  
  .main-container {
    padding: 10px;
    padding-bottom: 200px;
  }
}
































</style>

<style>
/* 全局Ant Design组件样式覆盖 */
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

/* 全局强制覆盖上传图片预览项样式 */
.ant-upload-list-picture-card .ant-upload-list-item {
  width: 80px !important;
  height: 80px !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
  border-radius: 6px !important;
  overflow: hidden !important;
}

/* 强制覆盖上传列表项容器 */
.ant-upload-wrapper.ant-upload-picture-card-wrapper .ant-upload-list.ant-upload-list-picture-card .ant-upload-list-item-container {
  width: 80px !important;
  height: 80px !important;
  margin: 0 !important;
  display: inline-block !important;
}

.ant-upload-list-picture-card .ant-upload-list-item img {
  width: 80px !important;
  height: 80px !important;
  object-fit: cover !important;
  border-radius: 6px !important;
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
}

.ant-upload-list-picture-card .ant-upload-list-item-info {
  width: 80px !important;
  height: 80px !important;
  padding: 0 !important;
  margin: 0 !important;
  border-radius: 6px !important;
}

.ant-upload-list-picture-card .ant-upload-list-item-thumbnail {
  width: 80px !important;
  height: 80px !important;
  padding: 0 !important;
  margin: 0 !important;
  border-radius: 6px !important;
  overflow: hidden !important;
}

.ant-upload-list-picture-card .ant-upload-list-item-image {
  width: 80px !important;
  height: 80px !important;
  object-fit: cover !important;
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