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
        @toggle-video-favorite="toggleVideoFavorite"
        @filter-change="handleFilterChange"
        @upscale="handleUpscale"
        @refreshHistory="loadHistory(1, false)"
        @video-task-created="handleVideoTaskCreated"
      />

      <!-- 控制面板 -->
      <ImageControlPanel
        v-model:prompt="prompt"
        v-model:reference-images="referenceImages"
        v-model:loras="selectedLoras"
        v-model:model="selectedModel"
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
  // 开发环境：指向后端9000端口
  if (import.meta.env.DEV) {
    return 'http://localhost:9000'
  }
  // 生产环境：使用环境变量或默认空字符串（通过nginx代理）
  return import.meta.env.VITE_API_BASE_URL || ''
})()





// 响应式数据
const prompt = ref('')
const negativePrompt = ref('blurry, low quality, worst quality, low resolution, pixelated, grainy, distorted, deformed, ugly, bad anatomy, extra limbs, missing limbs, extra fingers, bad hands, bad face, malformed, disfigured, mutated, fused fingers, cluttered background, extra legs, overexposed, oversaturated, static, motionless, watermark, text, signature, jpeg artifacts, compression artifacts, noise, artifacts, poorly drawn, amateur, sketch, draft')
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
const selectedLoras = ref([]) // 新增：选择的LoRA配置
const selectedModel = ref('flux1-dev') // 新增：选择的模型
const previewVisible = ref(false)
const previewImage = ref('')

// 放大状态管理
const isUpscaling = ref(false)
const upscalingProgress = ref(0)
const currentScaleFactor = ref(2)
const upscalingPrompt = ref('')
const currentUpscaleTaskId = ref(null) // 当前放大任务ID
// 移除了图片索引存储变量

// 视频生成状态管理
const isVideoGenerating = ref(false)
const videoGeneratingProgress = ref(0)
const currentVideoTaskId = ref(null) // 当前视频生成任务ID

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

// 保存放大状态到localStorage
const saveUpscaleState = () => {
  if (isUpscaling.value && currentUpscaleTaskId.value) {
    const upscaleState = {
      isUpscaling: true,
      taskId: currentUpscaleTaskId.value,
      scaleFactor: currentScaleFactor.value,
      progress: upscalingProgress.value,
      timestamp: Date.now()
    }
    localStorage.setItem('upscaleState', JSON.stringify(upscaleState))
    console.log('💾 保存放大状态:', upscaleState)
  } else {
    localStorage.removeItem('upscaleState')
    console.log('🧹 清除放大状态')
  }
}

// 从localStorage恢复放大状态
const restoreUpscaleState = async () => {
  try {
    const savedState = localStorage.getItem('upscaleState')
    if (!savedState) return false
    
    const upscaleState = JSON.parse(savedState)
    console.log('🔄 尝试恢复放大状态:', upscaleState)
    
    // 检查状态是否过期（超过10分钟）
    const now = Date.now()
    if (now - upscaleState.timestamp > 10 * 60 * 1000) {
      console.log('⏰ 放大状态已过期，清除')
      localStorage.removeItem('upscaleState')
      return false
    }
    
    // 检查任务是否仍在进行中
    const response = await fetch(`${API_BASE}/api/upscale/${upscaleState.taskId}`)
    if (!response.ok) {
      console.log('❌ 任务不存在，清除状态')
      localStorage.removeItem('upscaleState')
      return false
    }
    
    const taskStatus = await response.json()
    console.log('📊 任务当前状态:', taskStatus)
    
    if (taskStatus.status === 'completed') {
      console.log('✅ 任务已完成，清除状态并刷新历史')
      localStorage.removeItem('upscaleState')
      await loadHistory(1, false)
      return false
    } else if (taskStatus.status === 'failed') {
      console.log('❌ 任务已失败，清除状态')
      localStorage.removeItem('upscaleState')
      return false
    } else if (taskStatus.status === 'processing') {
      console.log('🔄 恢复放大状态，继续轮询')
      isUpscaling.value = true
      currentUpscaleTaskId.value = upscaleState.taskId
      currentScaleFactor.value = upscaleState.scaleFactor
      upscalingProgress.value = taskStatus.progress || upscaleState.progress
      upscalingPrompt.value = `放大图片 - ${upscaleState.scaleFactor}倍`
      
      // 重新开始轮询
      await pollUpscaleStatus(upscaleState.taskId)
      return true
    }
    
    return false
  } catch (error) {
    console.error('恢复放大状态失败:', error)
    localStorage.removeItem('upscaleState')
    return false
  }
}

// 生成图像
const generateImage = async (options = {}) => {
  const { mode = 'single', videoConfig } = options
  
  if (!prompt.value.trim()) {
    message.warning('请输入图像描述')
    return
  }

  // 图片数量验证 - Qwen模型支持无图片生成
  if (referenceImages.value.length === 0 && selectedModel.value !== 'qwen-image') {
    message.warning('请上传至少1张图片')
    return
  }
  if (referenceImages.value.length > 3) {
    message.warning('最多支持3张图片')
    return
  }
  
  // 多图融合模式特殊验证
  if (mode === 'fusion' && referenceImages.value.length < 2) {
    message.warning('多图融合至少需要2张图片')
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
    formData.append('steps', 20)
    formData.append('model', selectedModel.value)
    
    // 如果是视频生成，添加视频配置
    if (videoConfig) {
      formData.append('duration', videoConfig.duration)
      formData.append('fps', videoConfig.fps)
      console.log(`🎬 视频生成配置: 时长=${videoConfig.duration}秒, 帧率=${videoConfig.fps}FPS`)
    }
    
    // 根据模式设置不同的参数
    if (mode === 'fusion') {
      // 多图融合模式
      formData.append('fusion_mode', 'concat')
      formData.append('cfg', 2.5)
      
      // 添加多张参考图片
      referenceImages.value.forEach((imageFile, index) => {
        if (imageFile.originFileObj instanceof File) {
          formData.append('reference_images', imageFile.originFileObj)
        } else {
          console.error(`参考图片${index + 1}文件对象无效:`, imageFile)
          message.error(`参考图片${index + 1}文件无效，请重新选择`)
          return
        }
      })
      
      console.log(`🎨 多图融合模式: 上传${referenceImages.value.length}张图片`)
    } else {
      // 单图生成模式
      formData.append('count', imageCount.value)
      formData.append('size', imageSize.value)
      
      // 添加LoRA配置
      if (selectedLoras.value.length > 0) {
        formData.append('loras', JSON.stringify(selectedLoras.value))
        console.log('🎨 添加LoRA配置:', selectedLoras.value)
      }
      
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
    }

    // 调用后端API
    const apiEndpoint = mode === 'fusion' ? '/api/generate-image-fusion' : '/api/generate-image'
    const response = await fetch(`${API_BASE}${apiEndpoint}`, {
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
  
  // 回显模型信息
  if (image.parameters?.model) {
    selectedModel.value = image.parameters.model
  }
  
  // 回显LoRA信息
  if (image.parameters?.loras && image.parameters.loras.length > 0) {
    const lorasToSet = image.parameters.loras.map(lora => ({
      name: lora.name,
      enabled: lora.enabled !== false, // 默认为true
      strength_model: lora.strength_model || 1.0,
      strength_clip: lora.strength_clip || 1.0,
      trigger_word: lora.trigger_word || ''
    }))
    
    // 使用nextTick确保DOM更新完成
    await nextTick()
    selectedLoras.value = lorasToSet
  } else {
    await nextTick()
    selectedLoras.value = []
  }
  
  // 回显参考图
  if (image.referenceImage) {
    try {
      let imageUrls = []
      
      // 处理多图融合的情况
      if (typeof image.referenceImage === 'string' && image.referenceImage.startsWith('[') && image.referenceImage.endsWith(']')) {
        // 解析JSON字符串数组
        try {
          imageUrls = JSON.parse(image.referenceImage)
        } catch (parseError) {
          console.warn('解析参考图URL数组失败:', parseError)
          imageUrls = [image.referenceImage]
        }
      } else {
        // 单图情况
        imageUrls = [image.referenceImage]
      }
      
      // 处理所有参考图
      const referenceImageFiles = []
      
      for (let i = 0; i < imageUrls.length; i++) {
        const imageUrl = imageUrls[i]
        
        try {
          // 从URL获取图片文件
          const response = await fetch(imageUrl)
          
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
          const file = new File([blob], `reference_${i + 1}.png`, { type: blob.type || 'image/png' })
          
          referenceImageFiles.push({
            uid: Date.now() + i,
            name: `reference_${i + 1}.png`,
            status: 'done',
            url: imageUrl,
            preview: imageUrl,
            originFileObj: file
          })
        } catch (error) {
          console.error(`获取第${i + 1}张参考图失败:`, error, 'URL:', imageUrl)
          // 继续处理其他图片，不中断整个流程
        }
      }
      
      referenceImages.value = referenceImageFiles
      
      if (referenceImageFiles.length === 0) {
        message.warning('无法获取任何参考图，将不显示参考图')
      } else if (referenceImageFiles.length < imageUrls.length) {
        message.warning(`成功加载${referenceImageFiles.length}张参考图，${imageUrls.length - referenceImageFiles.length}张加载失败`)
      }
      
    } catch (error) {
      console.error('处理参考图失败:', error, 'referenceImage:', image.referenceImage)
      message.warning('无法获取原参考图，将不显示参考图')
      referenceImages.value = []
    }
  } else {
    referenceImages.value = []
  }
  
  // 等待DOM更新完成后再滚动
  await nextTick()
  
  // 滚动到输入区域
  document.querySelector('.control-section')?.scrollIntoView({ behavior: 'smooth' })
  
  message.success('已将提示词、模型、LoRA和参考图回填到输入框，您可以进行编辑')
}

// 重新生成图像
const regenerateImage = async (image) => {
  if (!image.prompt) {
    message.warning('该图像没有提示词，无法重新生成')
    return
  }
  
  // 使用原图像的提示词
  prompt.value = image.prompt
  
  // 回显模型信息
  if (image.parameters?.model) {
    selectedModel.value = image.parameters.model
  }
  
  // 回显LoRA信息
  if (image.parameters?.loras && image.parameters.loras.length > 0) {
    const lorasToSet = image.parameters.loras.map(lora => ({
      name: lora.name,
      enabled: lora.enabled !== false, // 默认为true
      strength_model: lora.strength_model || 1.0,
      strength_clip: lora.strength_clip || 1.0,
      trigger_word: lora.trigger_word || ''
    }))
    
    // 使用nextTick确保DOM更新完成
    await nextTick()
    selectedLoras.value = lorasToSet
  } else {
    await nextTick()
    selectedLoras.value = []
  }
  
  // 回显参考图
  if (image.referenceImage) {
    try {
      let imageUrls = []
      
      // 处理多图融合的情况
      if (typeof image.referenceImage === 'string' && image.referenceImage.startsWith('[') && image.referenceImage.endsWith(']')) {
        // 解析JSON字符串数组
        try {
          imageUrls = JSON.parse(image.referenceImage)
        } catch (parseError) {
          console.warn('解析参考图URL数组失败:', parseError)
          imageUrls = [image.referenceImage]
        }
      } else {
        // 单图情况
        imageUrls = [image.referenceImage]
      }
      
      // 处理所有参考图
      const referenceImageFiles = []
      
      for (let i = 0; i < imageUrls.length; i++) {
        const imageUrl = imageUrls[i]
        
        try {
          // 从URL获取图片文件
          const response = await fetch(imageUrl)
          
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
          const file = new File([blob], `reference_${i + 1}.png`, { type: blob.type || 'image/png' })
          
          referenceImageFiles.push({
            uid: Date.now() + i,
            name: `reference_${i + 1}.png`,
            status: 'done',
            url: imageUrl,
            preview: imageUrl,
            originFileObj: file
          })
        } catch (error) {
          console.error(`获取第${i + 1}张参考图失败:`, error, 'URL:', imageUrl)
          // 继续处理其他图片，不中断整个流程
        }
      }
      
      referenceImages.value = referenceImageFiles
      
      if (referenceImageFiles.length === 0) {
        message.warning('无法获取任何参考图，将不使用参考图重新生成')
      } else if (referenceImageFiles.length < imageUrls.length) {
        message.warning(`成功加载${referenceImageFiles.length}张参考图，${imageUrls.length - referenceImageFiles.length}张加载失败`)
      }
      
    } catch (error) {
      console.error('处理参考图失败:', error, 'referenceImage:', image.referenceImage)
      message.warning('无法获取原参考图，将不使用参考图重新生成')
      referenceImages.value = []
    }
  } else {
    referenceImages.value = []
  }
  
  // 等待DOM更新完成后再开始生成
  await nextTick()
  
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
    } else if (response.status === 404) {
      // 任务已不存在，直接从前端移除
      console.warn(`任务 ${image.task_id} 在数据库中不存在，从前端移除`)
      const taskIdToDelete = image.task_id
      history.value = history.value.filter(item => item.task_id !== taskIdToDelete)
      totalCount.value = Math.max(0, totalCount.value - 1)
      message.warning('该图像记录已过期，已从列表中移除')
    } else {
      throw new Error(`删除失败 (状态码: ${response.status})`)
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

// 切换视频收藏状态
const toggleVideoFavorite = async (video) => {
  try {
    // 调用后端API切换视频收藏状态
    const response = await fetch(`${API_BASE}/api/video/${video.task_id}/favorite`, {
      method: 'POST'
    })
    
    if (response.ok) {
      const result = await response.json()
      
      // 在history中找到对应的视频并更新收藏状态
      for (const historyItem of history.value) {
        if (historyItem.id === video.task_id) {
          if (historyItem.images && historyItem.images.length > 0) {
            historyItem.images[0].isFavorited = result.is_favorited
          }
          break
        }
      }
      
      // 显示提示信息
      if (result.is_favorited) {
        message.success('已添加到收藏')
      } else {
        message.success('已取消收藏')
      }
    } else {
      throw new Error('切换收藏状态失败')
    }
  } catch (error) {
    console.error('切换视频收藏状态失败:', error)
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
  // 处理多图上传的情况
  let imageUrl = file.url || file.preview
  
  // 如果是数组字符串，取第一个元素
  if (typeof imageUrl === 'string' && imageUrl.startsWith('[') && imageUrl.endsWith(']')) {
    try {
      const imageArray = JSON.parse(imageUrl)
      imageUrl = imageArray[0] || imageUrl
    } catch (e) {
      console.warn('解析图片URL失败:', e)
    }
  }
  
  previewImage.value = imageUrl
  previewVisible.value = true
}

// 处理放大请求
const handleUpscale = async (imageData, scaleFactor) => {
  try {
    isUpscaling.value = true
    upscalingProgress.value = 10
    currentScaleFactor.value = scaleFactor
    upscalingPrompt.value = `放大图片 - ${scaleFactor}倍`
    
    console.log('🔍 放大请求 - 图片数据:', imageData)
    console.log('🔍 放大倍数:', scaleFactor)
    console.log('🔍 图片URL:', imageData.url)
    console.log('🔍 图片directUrl:', imageData.directUrl)
    console.log('🔍 图片task_id:', imageData.task_id)
    console.log('🔍 图片filename:', imageData.filename)
    
    // 使用图片的直接URL或URL作为路径
    const imagePath = imageData.directUrl || imageData.url
    
    // 创建FormData，使用新的路径接口
    const formData = new FormData()
    formData.append('image_path', imagePath)
    formData.append('scale_factor', scaleFactor.toString())
    formData.append('algorithm', 'ultimate')
    
    upscalingProgress.value = 20
    
    console.log('📤 发送放大请求:', {
      image_path: imagePath,
      scale_factor: scaleFactor,
      algorithm: 'ultimate'
    })
    
    // 调用新的路径放大API
    const upscaleResponse = await fetch(`${API_BASE}/api/upscale/by-path`, {
      method: 'POST',
      body: formData
    })
    
    if (!upscaleResponse.ok) {
      const errorText = await upscaleResponse.text()
      console.error('❌ 放大API响应错误:', upscaleResponse.status, errorText)
      throw new Error(`放大请求失败: ${upscaleResponse.status} - ${errorText}`)
    }
    
    const result = await upscaleResponse.json()
    console.log('✅ 放大任务创建成功:', result)
    
    if (result.status === 'processing') {
      upscalingProgress.value = 30
      currentUpscaleTaskId.value = result.task_id  // 保存任务ID
      message.success(`开始${scaleFactor}倍放大，正在处理中...`)
      
      // 保存状态到localStorage
      saveUpscaleState()
      
      // 轮询检查任务状态
      await pollUpscaleStatus(result.task_id)
    } else {
      throw new Error('放大任务提交失败')
    }
    
  } catch (error) {
    console.error('❌ 放大失败:', error)
    message.error(`放大失败: ${error.message}`)
    // 只有在出错时才重置状态
    isUpscaling.value = false
    currentUpscaleTaskId.value = null
    saveUpscaleState() // 清除localStorage中的状态
  }
  // 移除finally块，让pollUpscaleStatus函数来控制状态重置
}

// 处理视频任务创建
const handleVideoTaskCreated = async (taskId) => {
  console.log('🎬 ImageGenerator 接收到视频任务创建事件:', taskId)
  try {
    console.log('🎬 视频任务已创建，开始轮询状态:', taskId)
    isVideoGenerating.value = true
    currentVideoTaskId.value = taskId
    
    // 开始轮询视频任务状态
    await pollVideoStatus(taskId)
  } catch (error) {
    console.error('❌ 视频任务处理失败:', error)
    message.error('视频任务处理失败')
    isVideoGenerating.value = false
    currentVideoTaskId.value = null
  }
}

// 轮询放大任务状态 - 强化版
const pollUpscaleStatus = async (taskId) => {
  const maxAttempts = 180  // 增加到180次（6分钟）
  let attempts = 0
  let consecutiveErrors = 0
  
  console.log(`🚀 开始轮询任务状态: ${taskId}`)
  
  const checkStatus = async () => {
    try {
      console.log(`🔍 检查任务状态 (${attempts + 1}/${maxAttempts}): ${taskId}`)
      
      const response = await fetch(`${API_BASE}/api/upscale/${taskId}`, {
        cache: 'no-cache',  // 强制不使用缓存
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const status = await response.json()
      consecutiveErrors = 0  // 重置错误计数
      
      console.log(`📊 任务状态: ${JSON.stringify(status)}`)
      
      // 使用后端返回的真实进度，而不是自己计算
      upscalingProgress.value = status.progress || 50
      
      // 更新进度时保存状态
      saveUpscaleState()
      
      if (status.status === 'completed') {
        upscalingProgress.value = 100
        console.log('✅ 任务完成！')
        
        // 显示成功消息
        message.success('图片放大完成！')
        
        // 等待一下确保数据库更新
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // 重新加载历史记录以显示最新的放大结果
        await loadHistory(1, false)
        
        // 强制刷新一次，确保显示最新状态
        setTimeout(async () => {
          await loadHistory(1, false)
        }, 1000)
        
        // 第三次刷新确保万无一失
        setTimeout(async () => {
          await loadHistory(1, false)
        }, 3000)
        
        // 重置放大状态
        isUpscaling.value = false
        currentUpscaleTaskId.value = null
        saveUpscaleState() // 清除localStorage中的状态
        return
      } else if (status.status === 'failed') {
        console.log('❌ 任务失败')
        message.error('图片放大失败')
        isUpscaling.value = false
        currentUpscaleTaskId.value = null
        saveUpscaleState() // 清除localStorage中的状态
        return
      }
      
      // 任务仍在处理中
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 1000) // 1秒轮询
      } else {
        console.log('⏰ 轮询超时')
        message.warning('放大任务超时，请稍后查看结果')
        // 超时时也尝试刷新一次历史记录
        await loadHistory(1, false)
        isUpscaling.value = false
        currentUpscaleTaskId.value = null
        saveUpscaleState() // 清除localStorage中的状态
      }
    } catch (error) {
      consecutiveErrors++
      console.error(`❌ 检查放大状态失败 (连续错误: ${consecutiveErrors}):`, error)
      
      // 如果连续错误太多，可能是严重问题
      if (consecutiveErrors >= 5) {
        console.log('❌ 连续错误过多，终止轮询')
        message.error('网络连接异常，请检查网络后手动刷新页面')
        isUpscaling.value = false
        currentUpscaleTaskId.value = null
        saveUpscaleState() // 清除localStorage中的状态
        return
      }
      
      // 网络错误或临时问题，继续重试
      attempts++
      if (attempts < maxAttempts) {
        console.log(`🔄 网络错误重试 (${attempts}/${maxAttempts})，${consecutiveErrors} 连续错误`)
        setTimeout(checkStatus, 2000) // 网络错误时等待2秒再重试
      } else {
        console.log('❌ 重试次数用尽')
        message.error('放大任务检查超时，请手动刷新页面查看结果')
        isUpscaling.value = false
        currentUpscaleTaskId.value = null
        saveUpscaleState() // 清除localStorage中的状态
      }
    }
  }
  
  await checkStatus()
}

// 轮询视频生成任务状态
const pollVideoStatus = async (taskId) => {
  const maxAttempts = 300  // 5分钟轮询
  let attempts = 0
  let consecutiveErrors = 0
  
  
  const checkStatus = async () => {
    try {
      
      const response = await fetch(`${API_BASE}/api/task/${taskId}`, {
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const status = await response.json()
      consecutiveErrors = 0
      
      
      if (status.status === 'completed') {
        console.log('✅ 视频生成完成！')
        message.success('视频生成完成！')
        
        // 等待数据库更新
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // 重新加载历史记录以显示最新的视频结果
        await loadHistory(1, false)
        
        // 强制刷新一次，确保显示最新状态
        setTimeout(async () => {
          await loadHistory(1, false)
        }, 1000)
        
        // 第三次刷新确保万无一失
        setTimeout(async () => {
          await loadHistory(1, false)
        }, 3000)
        
        // 重置视频生成状态
        isVideoGenerating.value = false
        currentVideoTaskId.value = null
        return
      } else if (status.status === 'failed') {
        console.log('❌ 视频生成失败')
        message.error('视频生成失败')
        isVideoGenerating.value = false
        currentVideoTaskId.value = null
        return
      }
      
      // 任务仍在处理中
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 2000) // 2秒轮询
      } else {
        console.log('⏰ 视频轮询超时')
        message.warning('视频生成任务超时，请稍后查看结果')
        // 超时时也尝试刷新一次历史记录
        await loadHistory(1, false)
        isVideoGenerating.value = false
        currentVideoTaskId.value = null
      }
    } catch (error) {
      consecutiveErrors++
      console.error(`❌ 检查视频状态失败 (连续错误: ${consecutiveErrors}):`, error)
      
      // 如果连续错误太多，可能是严重问题
      if (consecutiveErrors >= 5) {
        console.log('❌ 连续错误过多，终止视频轮询')
        message.error('网络连接异常，请检查网络后手动刷新页面')
        isVideoGenerating.value = false
        currentVideoTaskId.value = null
        return
      }
      
      // 网络错误或临时问题，继续重试
      attempts++
      if (attempts < maxAttempts) {
        console.log(`🔄 网络错误重试 (${attempts}/${maxAttempts})，${consecutiveErrors} 连续错误`)
        setTimeout(checkStatus, 2000) // 网络错误时等待2秒再重试
      } else {
        console.log('❌ 重试次数用尽')
        message.error('视频任务检查超时，请手动刷新页面查看结果')
        isVideoGenerating.value = false
        currentVideoTaskId.value = null
      }
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
        referenceImage: task.reference_image_path ? (Array.isArray(task.reference_image_path) ? JSON.stringify(task.reference_image_path.map(path => `${API_BASE}/api/image/upload/${path.replace(/^uploads[\/\\]/, '').replace(/\\/g, '/').replace(/\/\//g, '/')}`)) : `${API_BASE}/api/image/upload/${task.reference_image_path.replace(/^uploads[\/\\]/, '').replace(/\\/g, '/').replace(/\/\//g, '/')}`) : null,
        isFavorited: task.is_favorited === 1 || task.is_favorited === true,
        status: 'failed',
        error: task.error || '生成失败',
        parameters: task.parameters || {},  // 添加任务参数信息
        result_path: task.result_path  // 保留result_path字段
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
        referenceImage: task.reference_image_path ? (Array.isArray(task.reference_image_path) ? JSON.stringify(task.reference_image_path.map(path => `${API_BASE}/api/image/upload/${path.replace(/^uploads[\/\\]/, '').replace(/\\/g, '/').replace(/\/\//g, '/')}`)) : `${API_BASE}/api/image/upload/${task.reference_image_path.replace(/^uploads[\/\\]/, '').replace(/\\/g, '/').replace(/\/\//g, '/')}`) : null,
        isFavorited: task.is_favorited === 1 || task.is_favorited === true,
        status: task.status,
        error: task.error || `状态: ${task.status}`,
        parameters: task.parameters || {},  // 添加任务参数信息
        result_path: task.result_path  // 保留result_path字段
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
      // 处理多图融合的情况，reference_image_path可能是数组
      let referencePath = task.reference_image_path
      if (Array.isArray(referencePath)) {
        // 多图融合时，处理所有参考图路径
        const cleanPaths = referencePath.map(path => {
          let cleanPath = path
          
          // 处理uploads/或uploads\前缀
          if (cleanPath.startsWith('uploads/') || cleanPath.startsWith('uploads\\')) {
            // 去掉uploads/或uploads\前缀
            cleanPath = cleanPath.replace(/^uploads[\/\\]/, '')
          }
          
          // 将Windows路径分隔符转换为URL路径分隔符
          cleanPath = cleanPath.replace(/\\/g, '/')
          
          // 处理双斜杠问题
          cleanPath = cleanPath.replace(/\/\//g, '/')
          
          return `${API_BASE}/api/image/upload/${cleanPath}`
        })
        
        // 多图融合时，将完整的URL数组作为JSON字符串传递
        referenceImageUrl = JSON.stringify(cleanPaths)
      } else {
        // 单图情况，保持原有逻辑
        let cleanPath = referencePath
        
        // 处理uploads/或uploads\前缀
        if (cleanPath.startsWith('uploads/') || cleanPath.startsWith('uploads\\')) {
          // 去掉uploads/或uploads\前缀
          cleanPath = cleanPath.replace(/^uploads[\/\\]/, '')
        }
        
        // 将Windows路径分隔符转换为URL路径分隔符
        cleanPath = cleanPath.replace(/\\/g, '/')
        
        // 处理双斜杠问题
        cleanPath = cleanPath.replace(/\/\//g, '/')
        
        referenceImageUrl = `${API_BASE}/api/image/upload/${cleanPath}`
      }
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
          isFavorited: isFavorited,  // 使用后端提供的收藏状态
          parameters: task.parameters || {},  // 添加任务参数信息
          result_path: task.result_path  // 保留result_path字段
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
                images: processedImages,
                result_path: task.result_path,  // 保留result_path字段
                model: task.parameters?.model,  // 保留model字段
                parameters: task.parameters  // 保留完整参数
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
      } else {
        // 如果没有数据需要处理，直接清除loading状态
        if (!prepend) {
          history.value = []
        }
        isLoadingHistory.value = false
      }
    } else {
      // API响应不成功，清除loading状态
      isLoadingHistory.value = false
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
  
  // 尝试恢复放大状态
  console.log('🔄 检查是否有进行中的放大任务...')
  const restored = await restoreUpscaleState()
  if (restored) {
    console.log('✅ 放大状态已恢复，继续轮询')
  } else {
    console.log('ℹ️ 没有需要恢复的放大任务')
  }
  
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
  background: #1a1a1a !important;
  border-color: #444 !important;
  color: #fff !important;
  border: none !important;
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