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
        :is-upscaling="isUpscaling"
        :upscaling-progress="upscalingProgress"
        :current-scale-factor="currentScaleFactor"
        :upscaling-prompt="upscalingPrompt"
        :has-more="hasMore"
        :is-loading-history="isLoadingHistory"
        :total-count="totalCount"
        @edit-image="editImage"
        @regenerate-image="regenerateImage"
        @delete-image="deleteImage"
        @download-image="downloadImage"
        @load-more="loadMoreHistory"
        @toggle-favorite="toggleFavorite"
        @filter-change="handleFilterChange"
        @upscale="handleUpscale"
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
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import ImageGallery from './ImageGallery.vue'
import ImageControlPanel from './ImageControlPanel.vue'

// API基础URL - 自动检测环境
const API_BASE = (() => {
  // 开发环境：使用代理
  if (import.meta.env.DEV) {
    return ''
  }
  // 生产环境：使用环境变量或默认空字符串（通过nginx代理）
  return import.meta.env.VITE_API_BASE_URL || ''
})()





// 响应式数据
const prompt = ref('')
const negativePrompt = ref('blurry, low quality, distorted, deformed, ugly, bad anatomy, extra limbs, missing limbs, watermark, text, signature')
const imageSize = ref('512x512')
const imageCount = ref(parseInt(localStorage.getItem('imageCount')) || 4) // 默认生成4张图片，支持持久化
const isGenerating = ref(false)
const progress = ref(0)
const estimatedTime = ref(30)
const generatedImages = ref([])
// 历史记录和分页状态
const history = ref([])
const currentPage = ref(1)
const pageSize = ref(10) // 改为10个任务组一页，便于测试翻页功能
const totalCount = ref(0)
const hasMore = ref(false)
const isLoadingHistory = ref(false)
const referenceImages = ref([])
const previewVisible = ref(false)
const previewImage = ref('')

// 放大状态管理
const isUpscaling = ref(false)
const upscalingProgress = ref(0)
const currentScaleFactor = ref(2)
const upscalingPrompt = ref('')
// 移除了图片索引存储变量

// 计算属性：只从历史记录获取图像用于展示
const allImages = computed(() => {
  const hist = history.value || []
  
  // 将历史记录中的图片展开（后端按时间降序排列，最新的在前面）
  const historyImages = hist.flatMap(item => 
    (item.images || []).map(img => ({
      ...img,
      prompt: item.prompt,
      timestamp: item.timestamp,
      status: item.status
    }))
  )
  
  // 反转数组，让最新的内容显示在底部
  return historyImages.reverse()
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
  
  // 将每个任务组转换为数组（后端按时间降序排列，最新的在前面）
  Array.from(taskGroups.values()).forEach(group => {
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
    if (referenceImages.value.length > 0 && referenceImages.value[0].originFileObj) {
      const fileObj = referenceImages.value[0].originFileObj
      // 验证文件对象是否有效
      if (fileObj instanceof File) {
        formData.append('reference_image', fileObj)
      } else {
        console.error('参考图片文件对象无效:', fileObj)
        message.error('参考图片文件无效，请重新选择')
        return
      }
    }
    // 如果没有参考图片，不添加任何文件，让后端处理无参考图的情况

    // 调用后端API
    const response = await fetch(`${API_BASE}/api/generate-image`, {
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
          const statusResponse = await fetch(`${API_BASE}/api/task/${taskId}`)
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
                createdAt: new Date(),
                referenceImage: referenceImages.value.length > 0 ? referenceImages.value[0].url || referenceImages.value[0].preview : null,
                isFavorited: statusData.is_favorited === 1 || statusData.is_favorited === true  // 使用后端返回的收藏状态
              }))
              
              // 重新加载第一页历史记录以显示最新生成的图像
              console.log('🔄 开始刷新历史记录...')
              
              // 等待一下确保数据库更新
              await new Promise(resolve => setTimeout(resolve, 500))
              
              // 强制刷新历史记录，添加时间戳避免缓存
              await loadHistory(1, false)
              
              // 再次检查是否成功刷新
              console.log('📊 刷新后历史记录数量:', history.value.length)
              console.log('📋 刷新后历史记录内容:', history.value.map(item => ({
                id: item.id,
                task_id: item.task_id,
                status: item.status,
                image_count: item.images?.length || 0
              })))
              
              // 检查是否包含新生成的任务
              const hasNewTask = history.value.some(item => 
                item.images && item.images.some(img => img.task_id === taskId)
              )
              
              if (!hasNewTask && history.value.length > 0) {
                console.log('⚠️ 刷新后没有找到新任务，等待后再次尝试...')
                await new Promise(resolve => setTimeout(resolve, 1000))
                await loadHistory(1, false)
                
                // 再次检查
                const hasNewTaskAfterRetry = history.value.some(item => 
                  item.images && item.images.some(img => img.task_id === taskId)
                )
                console.log('📊 重试后是否找到新任务:', hasNewTaskAfterRetry)
              }
              
                             // 历史记录已由后端数据库管理
              
              isGenerating.value = false
              progress.value = 100
              message.success('图像生成成功！')
              
              // 滚动到页面底部显示新生成的内容，使用直接设置滚动位置避免触发滚动事件
              setTimeout(() => {
                // 临时禁用滚动监听器，避免触发翻页
                const originalScrollHandler = window.onscroll
                window.onscroll = null
                
                // 直接设置滚动位置到底部，不触发滚动事件
                window.scrollTo(0, document.documentElement.scrollHeight)
                
                // 恢复滚动监听器
                setTimeout(() => {
                  window.onscroll = originalScrollHandler
                }, 100)
              }, 500)
              
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
      // 重置分页状态
      currentPage.value = 1
      totalCount.value = 0
      hasMore.value = false
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
const editImage = async (image) => {
  if (!image.prompt) {
    message.warning('该图像没有提示词，无法编辑')
    return
  }
  
  // 使用原图像的提示词
  prompt.value = image.prompt
  
  // 回显参考图
  if (image.referenceImage) {
    try {
      // 从URL获取图片文件
      const response = await fetch(image.referenceImage)
      
      // 检查响应状态
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const blob = await response.blob()
      
      // 检查blob是否为空或无效
      if (blob.size === 0) {
        throw new Error('图片文件为空')
      }
      
      // 检查blob是否过小（可能是错误信息）
      if (blob.size < 100) {
        throw new Error('图片文件过小，可能损坏')
      }
      
      // 创建File对象
      const file = new File([blob], 'reference.png', { type: blob.type || 'image/png' })
      
      referenceImages.value = [{
        uid: Date.now(),
        name: 'reference.png',
        status: 'done',
        url: image.referenceImage,
        preview: image.referenceImage,
        originFileObj: file  // 添加originFileObj属性
      }]
    } catch (error) {
      console.error('获取参考图失败:', error, 'URL:', image.referenceImage)
      message.warning('无法获取原参考图，将不显示参考图')
      referenceImages.value = []
    }
  } else {
    referenceImages.value = []
  }
  
  // 滚动到输入区域
  document.querySelector('.control-section')?.scrollIntoView({ behavior: 'smooth' })
  
  message.success('已将提示词和参考图回填到输入框，您可以进行编辑')
}

// 重新生成图像
const regenerateImage = async (image) => {
  if (!image.prompt) {
    message.warning('该图像没有提示词，无法重新生成')
    return
  }
  
  // 使用原图像的提示词
  prompt.value = image.prompt
  
  // 回显参考图
  if (image.referenceImage) {
    try {
      // 从URL获取图片文件
      const response = await fetch(image.referenceImage)
      
      // 检查响应状态
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const blob = await response.blob()
      
      // 检查blob是否为空或无效
      if (blob.size === 0) {
        throw new Error('图片文件为空')
      }
      
      // 检查blob是否过小（可能是错误信息）
      if (blob.size < 100) {
        throw new Error('图片文件过小，可能损坏')
      }
      
      // 创建File对象
      const file = new File([blob], 'reference.png', { type: blob.type || 'image/png' })
      
      referenceImages.value = [{
        uid: Date.now(),
        name: 'reference.png',
        status: 'done',
        url: image.referenceImage,
        preview: image.referenceImage,
        originFileObj: file  // 添加originFileObj属性
      }]
    } catch (error) {
      console.error('获取参考图失败:', error, 'URL:', image.referenceImage)
      message.warning('无法获取原参考图，将不使用参考图重新生成')
      referenceImages.value = []
    }
  } else {
    referenceImages.value = []
  }
  
  // 开始生成
  await generateImage()
}

// 删除图像
const deleteImage = async (image) => {
  try {
    // 调用后端删除API
    const response = await fetch(`${API_BASE}/api/task/${image.task_id}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      // 从当前历史记录中移除被删除的任务，而不是重新加载整个第一页
      const taskIdToDelete = image.task_id
      history.value = history.value.filter(item => item.task_id !== taskIdToDelete)
      
      // 更新总数
      totalCount.value = Math.max(0, totalCount.value - 1)
      
      message.success('图像已删除')
    } else {
      throw new Error('删除失败')
    }
  } catch (error) {
    console.error('删除图像失败:', error)
    message.error('删除失败，请重试')
  }
}



// 更新所有图片的收藏状态
const updateImageFavoriteStatus = async () => {
  try {
    // 遍历所有历史记录中的图片，确保收藏状态正确
    for (const historyItem of history.value) {
      if (historyItem.images && Array.isArray(historyItem.images)) {
        for (const image of historyItem.images) {
          // 如果图片没有收藏状态，设置为false
          if (typeof image.isFavorited === 'undefined') {
            image.isFavorited = false
          }
        }
      }
    }
    
    // 同时更新allImages中的收藏状态
    for (const image of allImages.value) {
      if (typeof image.isFavorited === 'undefined') {
        image.isFavorited = false
      }
    }
    
    console.log('图片收藏状态更新完成')
  } catch (error) {
    console.error('更新图片收藏状态失败:', error)
  }
}

// 切换收藏状态
const toggleFavorite = async (image) => {
  try {
    // 调用后端API切换单张图片收藏状态
    const response = await fetch(`${API_BASE}/api/image/${image.task_id}/${image.imageIndex || 0}/favorite`, {
      method: 'POST'
    })
    
    if (response.ok) {
      const result = await response.json()
      
      // 在allImages中找到对应的图片并更新收藏状态
      const targetImage = allImages.value.find(img => 
        img.url === image.url && img.task_id === image.task_id && img.imageIndex === image.imageIndex
      )
      
      if (targetImage) {
        targetImage.isFavorited = result.is_favorited
        
        // 显示提示信息
        if (targetImage.isFavorited) {
          message.success('已添加到收藏')
        } else {
          message.success('已取消收藏')
        }
      }
    } else {
      throw new Error('切换收藏状态失败')
    }
  } catch (error) {
    console.error('切换收藏状态失败:', error)
    message.error('操作失败，请重试')
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

// 处理放大请求
const handleUpscale = async (imageData, scaleFactor) => {
  try {
    isUpscaling.value = true
    upscalingProgress.value = 10
    currentScaleFactor.value = scaleFactor
    upscalingPrompt.value = `放大图片 - ${scaleFactor}倍`
    
    // 获取图片数据
    const response = await fetch(imageData.url)
    const blob = await response.blob()
    
    // 创建FormData
    const formData = new FormData()
    formData.append('image', blob, 'image.png')
    formData.append('scale_factor', scaleFactor.toString())
    formData.append('algorithm', 'ultimate')
    
    upscalingProgress.value = 20
    
    // 调用放大API
    const upscaleResponse = await fetch(`${API_BASE}/api/upscale/`, {
      method: 'POST',
      body: formData
    })
    
    if (!upscaleResponse.ok) {
      throw new Error(`放大请求失败: ${upscaleResponse.status}`)
    }
    
    const result = await upscaleResponse.json()
    
    if (result.status === 'processing') {
      upscalingProgress.value = 30
      message.success(`开始${scaleFactor}倍放大，正在处理中...`)
      
      // 轮询检查任务状态
      await pollUpscaleStatus(result.task_id)
    } else {
      throw new Error('放大任务提交失败')
    }
    
  } catch (error) {
    console.error('放大失败:', error)
    message.error(`放大失败: ${error.message}`)
    // 只有在出错时才重置状态
    isUpscaling.value = false
  }
  // 移除finally块，让pollUpscaleStatus函数来控制状态重置
}

// 轮询放大任务状态
const pollUpscaleStatus = async (taskId) => {
  const maxAttempts = 60
  let attempts = 0
  
  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/upscale/${taskId}`)
      const status = await response.json()
      
      // 更新进度
      const progress = Math.min(30 + (attempts / maxAttempts) * 60, 90)
      upscalingProgress.value = progress
      
      if (status.status === 'completed') {
        upscalingProgress.value = 100
        
        // 将放大结果添加到历史记录
        if (status.result && status.result.upscaled_images && status.result.upscaled_images.length > 0) {
          const upscaledImageUrl = status.result.upscaled_images[0]
          
          // 确保URL格式正确，参考文字生成图片的处理方式
          let finalImageUrl = upscaledImageUrl
          // 如果URL不是以http开头，说明是相对路径，需要添加API_BASE前缀
          if (upscaledImageUrl && !upscaledImageUrl.startsWith('http')) {
            // 如果已经是完整的API路径（以/api开头），直接添加API_BASE
            if (upscaledImageUrl.startsWith('/api/')) {
              finalImageUrl = `${API_BASE}${upscaledImageUrl}`
            } else {
              // 如果是相对路径，添加API_BASE
              finalImageUrl = `${API_BASE}/${upscaledImageUrl}`
            }
          }
          
          // 创建新的历史记录项
          const upscaleHistoryItem = {
            task_id: `upscale_${Date.now()}`,
            prompt: upscalingPrompt.value,
            images: [{
              url: finalImageUrl,
              prompt: upscalingPrompt.value,
              task_id: `upscale_${Date.now()}`,
              timestamp: new Date().toISOString(),
              status: 'completed'
            }],
            timestamp: new Date().toISOString(),
            status: 'completed'
          }
          
          // 添加到历史记录开头
          history.value.unshift(upscaleHistoryItem)
          
          // 显示成功消息
          message.success('图片放大完成！')
        }
        
        // 重置放大状态
        isUpscaling.value = false
        return
      } else if (status.status === 'failed') {
        message.error('图片放大失败')
        // 重置放大状态
        isUpscaling.value = false
        return
      }
      
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 2000)
      } else {
        message.warning('放大任务超时，请稍后查看结果')
        // 重置放大状态
        isUpscaling.value = false
      }
    } catch (error) {
      console.error('检查放大状态失败:', error)
      message.error('检查放大状态失败')
      // 重置放大状态
      isUpscaling.value = false
    }
  }
  
  await checkStatus()
}

// 处理任务图片数据的辅助函数
const processTaskImages = (task) => {
  try {
    if (!task || !task.task_id) {
      console.warn('无效的任务数据:', task)
      return []
    }
    
    // 对于失败的任务，返回一个表示失败状态的图片对象
    if (task.status === 'failed') {
      return [{
        url: null, // 失败的任务没有图片URL
        directUrl: null,
        filename: `failed_${task.task_id}.png`,
        task_id: task.task_id,
        prompt: task.description || '',
        createdAt: new Date(task.created_at || Date.now()),
                    referenceImage: task.reference_image_path ? `${API_BASE}/api/image/upload/${task.reference_image_path}` : null,
        isFavorited: task.is_favorited === 1 || task.is_favorited === true,
        status: 'failed',
        error: task.error || '生成失败'
      }]
    }
    
    // 对于其他非完成状态，也返回一个状态对象
    if (task.status !== 'completed') {
      return [{
        url: null,
        directUrl: null,
        filename: `${task.status}_${task.task_id}.png`,
        task_id: task.task_id,
        prompt: task.description || '',
        createdAt: new Date(task.created_at || Date.now()),
                    referenceImage: task.reference_image_path ? `${API_BASE}/api/image/upload/${task.reference_image_path}` : null,
        isFavorited: task.is_favorited === 1 || task.is_favorited === true,
        status: task.status,
        error: task.error || `状态: ${task.status}`
      }]
    }
    
    // 检查是否有image_urls数组
    if (!task.image_urls || !Array.isArray(task.image_urls) || task.image_urls.length === 0) {
      console.warn('任务没有有效的image_urls:', task)
      return []
    }
    
    // 获取参考图信息
    let referenceImageUrl = null
    if (task.reference_image_path && task.reference_image_path !== 'uploads/blank.png' && task.reference_image_path !== 'uploads\\blank.png') {
      // 统一处理参考图片路径，支持Windows和Unix路径分隔符
      let cleanPath = task.reference_image_path
      
      // 处理uploads/或uploads\前缀
      if (cleanPath.startsWith('uploads/') || cleanPath.startsWith('uploads\\')) {
        // 去掉uploads/或uploads\前缀
        cleanPath = cleanPath.replace(/^uploads[\/\\]/, '')
      }
      
      // 将Windows路径分隔符转换为URL路径分隔符
      cleanPath = cleanPath.replace(/\\/g, '/')
      
                referenceImageUrl = `${API_BASE}/api/image/upload/${cleanPath}`
    }
    
    // 处理image_urls数组，使用后端提供的收藏状态
    const images = task.image_urls.map((imageUrl, index) => {
      try {
        // 从后端提供的images数组中获取收藏状态
        let isFavorited = false
        if (task.images && Array.isArray(task.images)) {
          const imageData = task.images.find(img => img.image_index === index)
          if (imageData) {
            isFavorited = imageData.isFavorited || false
          }
        }
        
        return {
          url: imageUrl,
          directUrl: null,
          filename: `generated_${task.task_id}_${index + 1}.png`,
          task_id: task.task_id,
          imageIndex: index, // 添加图片索引
          prompt: task.description || '',
          createdAt: new Date(task.created_at || Date.now()),
          referenceImage: referenceImageUrl,
          isFavorited: isFavorited  // 使用后端提供的收藏状态
        }
      } catch (imageError) {
        console.error('处理单个图片数据失败:', imageError, { imageUrl, index, task })
        return null
      }
    }).filter(img => img !== null) // 过滤掉处理失败的图片
    
    return images
  } catch (error) {
    console.error('processTaskImages 函数执行失败:', error, task)
    return []
  }
}

// 加载历史记录（支持分页，从最新开始）
const loadHistory = async (page = 1, prepend = false, filterParams = {}) => {
  if (isLoadingHistory.value) return
  
  const startTime = performance.now()
  console.log(`[性能监控] 开始加载历史记录，页面: ${page}, 模式: ${prepend ? 'prepend' : 'replace'}`)
  
  try {
    isLoadingHistory.value = true
    const offset = (page - 1) * pageSize.value
    
    // 记录加载前的历史记录数量，用于计算新内容位置
    const beforeCount = history.value.length
    
    // 使用AbortController来支持请求取消
    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      console.log('请求超时，取消请求')
      controller.abort()
    }, 15000) // 减少到15秒超时
    
    console.log('开始加载历史记录，页面:', page, '偏移量:', offset, '筛选参数:', filterParams)
    
    // 构建查询参数
            const queryParams = new URLSearchParams({
          limit: pageSize.value.toString(),
          offset: offset.toString(),
          order: 'desc', // 降序排列，最新的任务在第一页
          _t: Date.now().toString() // 添加时间戳避免缓存
        })
    
    // 添加筛选参数
    if (filterParams.favoriteFilter && filterParams.favoriteFilter !== 'all') {
      queryParams.append('favorite_filter', filterParams.favoriteFilter)
    }
    if (filterParams.timeFilter && filterParams.timeFilter !== 'all') {
      queryParams.append('time_filter', filterParams.timeFilter)
    }
    const response = await fetch(`${API_BASE}/api/history?${queryParams.toString()}`, {
      signal: controller.signal,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    clearTimeout(timeoutId)
    console.log('API响应状态:', response.status)
    
    if (response.ok) {
      const data = await response.json()
      
      // 更新分页状态
      totalCount.value = data.total || 0
      hasMore.value = data.has_more || false
      currentPage.value = page
      
      if (data.tasks && data.tasks.length > 0) {
        // 使用nextTick优化DOM更新
        await nextTick()
        
        try {
          const newHistoryItems = data.tasks.map(task => {
            try {
              const processedImages = processTaskImages(task)
              return {
                id: task.task_id,
                task_id: task.task_id,  // 保持task_id字段用于删除操作
                prompt: task.description,
                timestamp: task.created_at,
                status: task.status,
                images: processedImages
              }
            } catch (taskError) {
              console.error('处理单个任务数据失败:', taskError, task)
              return null
            }
          }).filter(item => item !== null) // 过滤掉处理失败的项目
          
                          if (prepend) {
                  // 前置模式：添加到现有历史记录前面（用于加载更早的数据）
                  // 由于后端返回的是降序排列，新加载的内容是更早的数据，应该放在现有内容的后面
                  history.value = [...history.value, ...newHistoryItems]
                } else {
                  // 替换模式：替换现有历史记录（首次加载）
                  history.value = newHistoryItems
                }
          
          const endTime = performance.now()
          console.log(`[性能监控] 数据处理完成，历史记录数量: ${history.value.length}, 耗时: ${(endTime - startTime).toFixed(2)}ms`)
          
          // 获取所有图片的收藏状态
          await updateImageFavoriteStatus()
        } catch (error) {
          console.error('处理历史数据时出错:', error)
          // 即使处理失败也要清除loading状态
          isLoadingHistory.value = false
          return
        }
        
        // 立即清除loading状态
        isLoadingHistory.value = false
        console.log('数据处理完成，立即清除loading状态')
      } else {
        // 如果没有数据需要处理，直接清除loading状态
        if (!prepend) {
          history.value = []
        }
        isLoadingHistory.value = false
        console.log('无数据需要处理，清除loading状态')
      }
    } else {
      // API响应不成功，清除loading状态
      isLoadingHistory.value = false
      console.log('API响应失败，清除loading状态')
      throw new Error(`API响应失败: ${response.status}`)
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('请求被取消')
    } else {
      console.error('加载历史记录失败:', error)
      // 如果API失败且是第一页，显示错误信息
      if (page === 1) {
        console.error('无法从后端加载历史记录，请检查网络连接')
      }
      message.error('加载历史记录失败')
    }
    // 在catch块中也要清除loading状态
    isLoadingHistory.value = false
    console.log('异常情况，清除loading状态')
  }
}

// 滚动到新内容位置的函数
const scrollToNewContent = (newContentCount) => {
  try {
    // 等待DOM完全更新
    setTimeout(() => {
      // 查找新加载的内容元素
      const taskCards = document.querySelectorAll('.task-card')
      if (taskCards.length >= newContentCount) {
        // 滚动到第一个新内容的顶部，留出一些空间
        const targetElement = taskCards[newContentCount - 1]
        if (targetElement) {
          const targetPosition = targetElement.offsetTop - 100 // 留出100px的空间
          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          })
          console.log(`已滚动到新内容位置，新内容数量: ${newContentCount}`)
        }
      }
    }, 200) // 增加延迟确保DOM完全更新
  } catch (error) {
    console.error('滚动到新内容位置失败:', error)
  }
}

// 防抖函数
const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// 当前筛选参数
const currentFilterParams = ref({})

// 防抖版本的loadMoreHistory
const debouncedLoadMore = debounce(async () => {
  console.log('loadMoreHistory被调用，hasMore:', hasMore.value, 'isLoadingHistory:', isLoadingHistory.value)
  
  if (hasMore.value && !isLoadingHistory.value) {
    await loadHistory(currentPage.value + 1, true, currentFilterParams.value)
  } else if (!hasMore.value && isLoadingHistory.value) {
    // 如果没有更多数据但加载状态仍为true，清除加载状态
    isLoadingHistory.value = false
    console.log('没有更多数据，强制清除loading状态')
  } else if (isLoadingHistory.value) {
    // 如果正在加载中，强制清除状态（防止卡住）
    console.log('检测到loading状态异常，强制清除')
    isLoadingHistory.value = false
  }
}, 1000) // 增加到1秒防抖

// 加载更多历史记录（加载更早的数据）
const loadMoreHistory = async () => {
  // 添加额外的状态检查
  if (isLoadingHistory.value) {
    console.log('正在加载中，跳过重复请求')
    return
  }
  
  debouncedLoadMore()
}

// 处理筛选条件变化
const handleFilterChange = async (filterParams) => {
  console.log('筛选条件变化:', filterParams)
  currentFilterParams.value = filterParams
  
  // 重置分页状态
  currentPage.value = 1
  hasMore.value = true
  
  // 直接使用后端API进行筛选
  await loadHistory(1, false, filterParams)
}

// 历史记录现在由后端数据库管理，无需本地存储

// 组件挂载时加载历史记录
onMounted(async () => {
  await loadHistory()
  // 页面加载完成后直接定位到底部显示最新内容，不触发滚动事件
  setTimeout(() => {
    // 临时禁用滚动监听器，避免触发翻页
    const originalScrollHandler = window.onscroll
    window.onscroll = null
    
    // 直接设置滚动位置到底部，不触发滚动事件
    window.scrollTo(0, document.documentElement.scrollHeight)
    
    // 恢复滚动监听器
    setTimeout(() => {
      window.onscroll = originalScrollHandler
    }, 100)
  }, 500) // 延迟500ms确保DOM渲染完成
})
</script>

<style scoped>
.image-generator {
  min-height: 100vh;
}

/* 移除重复的main-content样式定义 */

.main-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
  padding: 10px;
  position: relative;
}

.main-content {
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 30px;
  position: relative;
  z-index: 1;
  padding: 0 0 140px 0; /* 为底部固定控制面板预留空间 */
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
  padding:10px !important;
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