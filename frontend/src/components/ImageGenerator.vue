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
        :cache-status="cacheStatus"
        @edit-image="editImage"
        @regenerate-image="regenerateImage"
        @delete-image="deleteImageWrapper"
        @download-image="downloadImageWrapper"
        @load-more="loadMoreHistory"
        @toggle-favorite="toggleFavoriteWrapper"
        @toggle-video-favorite="toggleVideoFavoriteWrapper"
        @filter-change="handleFilterChange"
        @upscale="handleUpscale"
        @refreshHistory="(options) => loadHistoryWrapper(1, false, {}, options)"
        @video-task-created="handleVideoTaskCreated"
        @navigate-to-canvas="handleNavigateToCanvas"
      />

      <!-- 控制面板 -->
      <ImageControlPanel
        v-model:prompt="prompt"
        v-model:reference-images="referenceImages"
        v-model:loras="selectedLoras"
        v-model:model="selectedModel"
        v-model:size="imageSize"
        v-model:count="imageCount"
        :is-generating="isGenerating"
        @generate="generateImageWrapper"
        @preview="handlePreview"
        @upload-complete="handleUploadComplete"
      />
    </div>
    
    <!-- 图片预览模态框 -->
    <ImagePreviewModal
      :visible="previewVisible"
      :image-url="previewImage"
      title="图片预览"
      @update:visible="previewVisible = $event"
      @use-prompt="handleUsePrompt"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import ImageGallery from './ImageGallery.vue'
import ImageControlPanel from './ImageControlPanel.vue'
import ImagePreviewModal from './ImagePreviewModal.vue'
import cacheManager from '../utils/cacheManager.js'
import modelManager from '../utils/modelManager.js'
// 导入提取的工具函数和服务
import { convertPathsToFiles, processTaskImages, downloadImage, downloadAllImages, shareImage } from '../utils/imageUtils.js'
import { formatTime, debounce, scrollToNewContent, safeScrollTo, scrollToBottom, maintainScrollPosition } from '../utils/formatUtils.js'
import { pollUpscaleStatus, pollVideoStatus, pollTaskStatus } from '../services/pollingService.js'
import { generateImage, loadHistory, deleteImage, toggleFavorite, toggleVideoFavorite, clearHistory } from '../services/imageService.js'

// API基础URL - 自动检测环境
const API_BASE = (() => {
  // 开发环境：指向后端9000端口
  if (import.meta.env.DEV) {
    return import.meta.env.VITE_BACKEND_URL || 'http://localhost:9000'
  }
  // 生产环境：使用环境变量或默认空字符串（通过nginx代理）
  return import.meta.env.VITE_API_BASE_URL || ''
})()

// convertPathsToFiles 函数已提取到 utils/imageUtils.js





// 响应式数据
const prompt = ref('')
const negativePrompt = ref('blurry, low quality, worst quality, low resolution, pixelated, grainy, distorted, deformed, ugly, bad anatomy, extra limbs, missing limbs, extra fingers, bad hands, bad face, malformed, disfigured, mutated, fused fingers, cluttered background, extra legs, overexposed, oversaturated, static, motionless, watermark, text, signature, jpeg artifacts, compression artifacts, noise, artifacts, poorly drawn, amateur, sketch, draft')
const imageSize = ref('1024x1024')
const imageCount = ref(parseInt(localStorage.getItem('imageCount')) || 1) // 默认生成1张图片，支持持久化，将从API获取
const isGenerating = ref(false)
const progress = ref(0)
const estimatedTime = ref(30)
const generatedImages = ref([])
// 历史记录和分页状态
const history = ref([])
const currentPage = ref(1)
const pageSize = ref(20) // 改为20个任务组一页，提高加载效率
const totalCount = ref(0)
const hasMore = ref(false)
const isLoadingHistory = ref(false)
const referenceImages = ref([])

// 缓存状态
const cacheStatus = ref(null)
const selectedLoras = ref([]) // 新增：选择的LoRA配置
const selectedModel = ref('') // 动态选择的模型，将从配置中获取
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

// 手动清除缓存功能
const clearCache = () => {
  cacheManager.clearCache()
  message.success('缓存已清除')
  console.log('🧹 用户手动清除缓存')
}

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
      await pollUpscaleStatus(upscaleState.taskId, API_BASE, {
        onProgress: (progress) => {
          upscalingProgress.value = progress
          saveUpscaleState()
        },
        onSuccess: async (status) => {
          upscalingProgress.value = 100
          message.success('图片放大完成！')
          
          // 等待一下确保数据库更新
          await new Promise(resolve => setTimeout(resolve, 500))
          
          // 重新加载历史记录以显示最新的放大结果
          cacheManager.clearCache()
          await loadHistoryWrapper(1, false, {}, { forceRefresh: true, silent: true })
          
          // 重置放大状态
          isUpscaling.value = false
          currentUpscaleTaskId.value = null
          saveUpscaleState()
        },
        onError: (error) => {
          message.error(error)
          isUpscaling.value = false
          currentUpscaleTaskId.value = null
          saveUpscaleState()
        },
        onTimeout: async () => {
          message.warning('放大任务超时，请稍后查看结果')
          await loadHistoryWrapper(1, false)
          isUpscaling.value = false
          currentUpscaleTaskId.value = null
          saveUpscaleState()
        }
      })
      return true
    }
    
    return false
  } catch (error) {
    console.error('恢复放大状态失败:', error)
    localStorage.removeItem('upscaleState')
    return false
  }
}

// 生成图像 - 使用提取的服务
const generateImageWrapper = async (options = {}) => {
  const { mode = 'single', videoConfig } = options
  
  // 准备生成选项
  const generateOptions = {
    prompt: prompt.value,
    model: selectedModel.value,
    size: imageSize.value,
    count: imageCount.value,
    referenceImages: referenceImages.value,
    loras: selectedLoras.value,
    mode,
    videoConfig
  }
  
  // 准备回调函数
  const callbacks = {
    onStart: () => {
      isGenerating.value = true
      progress.value = 0
    },
    onProgress: (progressValue) => {
      progress.value = progressValue
    },
    onTaskCreated: (taskId) => {
      message.success('任务已提交，正在生成中...')
    },
    onSuccess: async (statusData, taskId) => {
      // 任务完成，立即清除缓存确保获取最新数据
      cacheManager.clearCache()
      console.log('🧹 生图完成，已清除缓存')
      
      // 等待一下确保数据库更新
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 强制刷新历史记录，清除缓存确保获取最新数据
      cacheManager.clearCache() // 先清除缓存
      await loadHistoryWrapper(1, false, {}, { forceRefresh: true, silent: true })
      
      isGenerating.value = false
      progress.value = 100
      message.success('图像生成成功！')
      
      // 滚动到页面底部显示新生成的内容
      setTimeout(() => {
        scrollToBottom()
      }, 500)
    },
    onError: (error) => {
      isGenerating.value = false
      progress.value = 0
      message.error(error)
    }
  }
  
  // 调用提取的服务
  await generateImage(generateOptions, API_BASE, callbacks)
}



// 选择历史记录
const selectHistoryItem = (item) => {
  prompt.value = item.prompt
}

// 清空历史记录 - 使用提取的服务
const clearHistoryWrapper = async () => {
  const callbacks = {
    onSuccess: () => {
      history.value = []
      // 重置分页状态
      currentPage.value = 1
      totalCount.value = 0
      hasMore.value = false
      // 清空本地存储
      localStorage.removeItem('imageGeneratorHistory')
      message.success('历史记录已清空')
    },
    onError: (error) => {
      message.error('清空失败，请重试')
    }
  }
  
  await clearHistory(API_BASE, callbacks)
}

// 使用图像的提示词
const useImagePrompt = (image) => {
  prompt.value = image.prompt
  message.success('已复制提示词到输入框')
}

// 下载图像 - 使用提取的工具函数
const downloadImageWrapper = async (image) => {
  const result = await downloadImage(image)
  if (result.success) {
    message.success(`图片 ${result.filename} 下载已开始`)
  } else {
    message.error('下载失败，请重试')
  }
}


// 分享图像 - 使用提取的工具函数
const shareImageWrapper = (image) => {
  const result = shareImage(image)
  if (result && result.method === 'clipboard') {
    message.success('图像链接已复制到剪贴板')
  }
}

// 移除了图片切换相关函数

// 下载全部图片 - 使用提取的工具函数
const downloadAllImagesWrapper = async (group) => {
  const result = await downloadAllImages(group)
  if (result.success) {
    message.success(`开始下载 ${result.count} 张图片`)
  } else {
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
  
  // 回显尺寸信息
  if (image.parameters?.size) {
    imageSize.value = image.parameters.size
    console.log('✅ 回填尺寸:', image.parameters.size)
  } else if (image.parameters?.width && image.parameters?.height) {
    // 如果没有size字段，但有width和height，则组合成size
    const size = `${image.parameters.width}x${image.parameters.height}`
    imageSize.value = size
    console.log('✅ 从宽高回填尺寸:', size)
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
  
  // 回显尺寸信息
  if (image.parameters?.size) {
    imageSize.value = image.parameters.size
    console.log('✅ 回填尺寸:', image.parameters.size)
  } else if (image.parameters?.width && image.parameters?.height) {
    // 如果没有size字段，但有width和height，则组合成size
    const size = `${image.parameters.width}x${image.parameters.height}`
    imageSize.value = size
    console.log('✅ 从宽高回填尺寸:', size)
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

// 删除图像 - 使用提取的服务
const deleteImageWrapper = async (image) => {
  const callbacks = {
    onSuccess: (taskId) => {
      // 从当前历史记录中移除被删除的任务，而不是重新加载整个第一页
      history.value = history.value.filter(item => item.task_id !== taskId)
      
      // 更新总数
      totalCount.value = Math.max(0, totalCount.value - 1)
      
      // 从缓存中移除该任务，而不是完全清除缓存
      cacheManager.removeTaskFromCache(taskId)
      console.log('🧹 删除任务后已从缓存中移除')
      
      message.success('图像已删除')
    },
    onError: (error) => {
      message.error('删除失败，请重试')
    }
  }
  
  await deleteImage(image, API_BASE, callbacks)
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

// 切换收藏状态 - 使用提取的服务
const toggleFavoriteWrapper = async (image) => {
  const callbacks = {
    onSuccess: (result, imageData) => {
      // 在allImages中找到对应的图片并更新收藏状态
      const targetImage = allImages.value.find(img => 
        img.url === imageData.url && img.task_id === imageData.task_id && img.image_index === imageData.image_index
      )
      
      if (targetImage) {
        targetImage.isFavorited = result.is_favorited
        
        // 显示提示信息
        if (targetImage.isFavorited) {
          message.success('已添加到收藏')
        } else {
          message.success('已取消收藏')
          // 通知灵感页面刷新收藏列表
          window.dispatchEvent(new CustomEvent('refresh-favorites'))
        }
      }
    },
    onError: (error) => {
      message.error('操作失败，请重试')
    }
  }
  
  await toggleFavorite(image, API_BASE, callbacks)
}

// 切换视频收藏状态 - 使用提取的服务
const toggleVideoFavoriteWrapper = async (video) => {
  const callbacks = {
    onSuccess: (result, videoData) => {
      // 在history中找到对应的视频并更新收藏状态
      for (const historyItem of history.value) {
        if (historyItem.id === videoData.task_id) {
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
        // 通知灵感页面刷新收藏列表
        window.dispatchEvent(new CustomEvent('refresh-favorites'))
      }
    },
    onError: (error) => {
      message.error('操作失败，请重试')
    }
  }
  
  await toggleVideoFavorite(video, API_BASE, callbacks)
}

// formatTime 函数已提取到 utils/formatUtils.js

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

// 处理图片上传完成事件
const handleUploadComplete = (file) => {
  console.log('📸 参考图上传完成，准备显示智能参考弹窗:', file)
  
  // 获取图片URL
  let imageUrl = file.url || file.preview
  
  // 如果是blob URL，需要上传到服务器获取真实URL
  if (imageUrl.startsWith('blob:')) {
    // 上传图片到服务器
    uploadReferenceImage(file.originFileObj).then(uploadedUrl => {
      if (uploadedUrl) {
        // 显示智能参考弹窗
        showSmartReferenceModal(uploadedUrl)
      }
    }).catch(error => {
      console.error('上传参考图失败:', error)
      message.error('上传参考图失败，无法进行智能分析')
    })
  } else {
    // 直接显示智能参考弹窗
    showSmartReferenceModal(imageUrl)
  }
}

// 上传参考图到服务器
const uploadReferenceImage = async (file) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${API_BASE}/api/image/upload`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`上传失败: ${response.status}`)
    }
    
    const result = await response.json()
    return result.url
  } catch (error) {
    console.error('上传参考图失败:', error)
    throw error
  }
}


// 显示智能参考弹窗
const showSmartReferenceModal = (imageUrl) => {
  console.log('🔍 显示智能参考弹窗，图片URL:', imageUrl)
  
  // 设置预览图片和显示弹窗
  previewImage.value = imageUrl
  previewVisible.value = true
}

// 处理使用提示词
const handleUsePrompt = (promptText) => {
  console.log('📝 使用反推提示词:', promptText)
  
  // 将提示词回填到生图界面的提示词输入框
  prompt.value = promptText
  
  // 显示成功消息
  message.success('提示词已应用到生图界面')
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
      await pollUpscaleStatus(result.task_id, API_BASE, {
        onProgress: (progress) => {
          upscalingProgress.value = progress
          saveUpscaleState()
        },
        onSuccess: async (status) => {
          upscalingProgress.value = 100
          message.success('图片放大完成！')
          
          // 等待一下确保数据库更新
          await new Promise(resolve => setTimeout(resolve, 500))
          
          // 重新加载历史记录以显示最新的放大结果
          cacheManager.clearCache()
          await loadHistoryWrapper(1, false, {}, { forceRefresh: true, silent: true })
          
          // 重置放大状态
          isUpscaling.value = false
          currentUpscaleTaskId.value = null
          saveUpscaleState()
        },
        onError: (error) => {
          message.error(error)
          isUpscaling.value = false
          currentUpscaleTaskId.value = null
          saveUpscaleState()
        },
        onTimeout: async () => {
          message.warning('放大任务超时，请稍后查看结果')
          await loadHistoryWrapper(1, false)
          isUpscaling.value = false
          currentUpscaleTaskId.value = null
          saveUpscaleState()
        }
      })
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
    await pollVideoStatus(taskId, API_BASE, {
      onSuccess: async (status) => {
        console.log('✅ 视频生成完成！')
        message.success('视频生成完成！')
        
        // 等待数据库更新
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // 重新加载历史记录以显示最新的视频结果
        cacheManager.clearCache()
        await loadHistoryWrapper(1, false, {}, { forceRefresh: true })
        
        // 重置视频生成状态
        isVideoGenerating.value = false
        currentVideoTaskId.value = null
      },
      onError: (error) => {
        message.error(error)
        isVideoGenerating.value = false
        currentVideoTaskId.value = null
      },
      onTimeout: async () => {
        message.warning('视频生成任务超时，请稍后查看结果')
        await loadHistoryWrapper(1, false)
        isVideoGenerating.value = false
        currentVideoTaskId.value = null
      }
    })
  } catch (error) {
    console.error('❌ 视频任务处理失败:', error)
    message.error('视频任务处理失败')
    isVideoGenerating.value = false
    currentVideoTaskId.value = null
  }
}

// 处理跳转到画布页面
const handleNavigateToCanvas = (data) => {
  console.log('🎨 跳转到画布页面:', data)
  
  // 将画布数据存储到localStorage，供CanvasDemo组件使用
  localStorage.setItem('canvasData', JSON.stringify(data))
  
  // 切换到画布标签
  // 这里需要访问父组件的activeTab，但由于没有emit，我们需要使用其他方式
  // 可以通过window事件或者直接操作父组件
  window.dispatchEvent(new CustomEvent('navigate-to-canvas', { detail: data }))
}

// pollUpscaleStatus 函数已提取到 services/pollingService.js

// pollVideoStatus 函数已提取到 services/pollingService.js

// processTaskImages 函数已提取到 utils/imageUtils.js

// 加载历史记录 - 使用提取的服务
const loadHistoryWrapper = async (page = 1, prepend = false, filterParams = {}, options = {}) => {
  const startTime = performance.now()
  console.log(`[性能监控] 开始加载历史记录，页面: ${page}, 模式: ${prepend ? 'prepend' : 'replace'}`)
  
  // 准备回调函数
  const callbacks = {
    isLoadingHistory: isLoadingHistory,
    setLoadingHistory: (loading) => { isLoadingHistory.value = loading },
    setTotalCount: (count) => { totalCount.value = count },
    setHasMore: (hasMoreValue) => { hasMore.value = hasMoreValue },
    setCurrentPage: (pageValue) => { currentPage.value = pageValue },
    setHistory: (historyData) => { history.value = historyData },
    onDataLoaded: async (data, prependMode, currentScrollTop, currentScrollHeight) => {
      // 使用nextTick优化DOM更新
      await nextTick()
      
      try {
        if (prependMode) {
          // 前置模式：添加到现有历史记录前面（用于加载更早的数据）
          history.value = [...history.value, ...data]
        } else {
          // 替换模式：替换现有历史记录（首次加载）
          history.value = data
        }
        
        const endTime = performance.now()
        console.log(`[性能监控] 数据处理完成，历史记录数量: ${history.value.length}, 耗时: ${(endTime - startTime).toFixed(2)}ms`)
        
        // 获取所有图片的收藏状态
        await updateImageFavoriteStatus()
        
        // 如果是翻页加载（prepend模式），保持滚动位置
        if (prependMode) {
          maintainScrollPosition(currentScrollTop, currentScrollHeight)
        }
      } catch (error) {
        console.error('处理历史数据时出错:', error)
        isLoadingHistory.value = false
        return
      }
    },
    onError: (error) => {
      message.error(error)
    }
  }
  
  // 调用提取的服务
  await loadHistory(page, prepend, filterParams, { ...options, pageSize: pageSize.value }, API_BASE, callbacks)
}

// scrollToNewContent 和 debounce 函数已提取到 utils/formatUtils.js

// 当前筛选参数
const currentFilterParams = ref({})

// 防抖版本的loadMoreHistory
const debouncedLoadMore = debounce(async () => {
  console.log('debouncedLoadMore被调用，hasMore:', hasMore.value, 'isLoadingHistory:', isLoadingHistory.value)
  
  if (hasMore.value && !isLoadingHistory.value) {
    console.log('开始加载下一页，当前页:', currentPage.value)
    await loadHistoryWrapper(currentPage.value + 1, true, currentFilterParams.value)
  } else if (!hasMore.value) {
    console.log('没有更多数据，hasMore:', hasMore.value)
  } else if (isLoadingHistory.value) {
    console.log('正在加载中，跳过重复请求')
  }
}, 1000) // 1秒防抖

// 加载更多历史记录（加载更早的数据）
const loadMoreHistory = async () => {
  console.log('loadMoreHistory被调用，hasMore:', hasMore.value, 'isLoadingHistory:', isLoadingHistory.value)
  
  // 直接调用防抖函数，让防抖函数内部处理状态检查
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
  await loadHistoryWrapper(1, false, filterParams)
}

// 历史记录现在由后端数据库管理，无需本地存储

// 初始化默认模型和配置
const initializeDefaultModel = async () => {
  try {
    console.log('🔍 正在获取默认模型配置...')
    
    // 使用全局模型管理器
    await modelManager.fetchModels()
    const defaultModel = modelManager.getDefaultModel()
    
    if (defaultModel) {
      selectedModel.value = defaultModel.name
      console.log('✅ 默认模型已设置:', defaultModel.display_name)
    } else {
      console.warn('⚠️ 没有可用的模型配置')
      selectedModel.value = 'qwen-image' // 最后的降级方案
    }
    
    // 获取默认生图数量配置
    try {
      const response = await fetch('/api/config/image-gen')
      if (response.ok) {
        const config = await response.json()
        const defaultCount = config.default_count || 1
        if (!localStorage.getItem('imageCount')) {
          imageCount.value = defaultCount
          console.log('✅ 默认生图数量已设置:', defaultCount)
        }
      }
    } catch (error) {
      console.warn('⚠️ 获取默认生图数量失败，使用默认值1:', error)
    }
  } catch (error) {
    console.error('❌ 初始化默认模型失败:', error)
    selectedModel.value = 'qwen-image' // 降级方案
  }
}

// 组件挂载时加载历史记录
onMounted(async () => {
  // 立即设置加载状态，避免显示空状态
  isLoadingHistory.value = true
  
  // 首先获取默认模型
  await initializeDefaultModel()
  await loadHistoryWrapper(1, false, {}, { forceRefresh: true })
  
  // 检查是否有回填数据
  const regenerateData = localStorage.getItem('regenerateData')
  if (regenerateData) {
    try {
      const data = JSON.parse(regenerateData)
      console.log('🔄 发现回填数据，正在回填参数...', data)
      
      // 回填提示词
      if (data.prompt) {
        prompt.value = data.prompt
      }
      
      // 回填模型
      if (data.model) {
        selectedModel.value = data.model
      }
      
      // 回填尺寸
      if (data.size) {
        imageSize.value = data.size
        console.log('✅ 回填尺寸:', data.size)
      }
      
      // 回填参考图
      if (data.referenceImages && data.referenceImages.length > 0) {
        try {
          // 将文件路径转换为文件对象
          const referenceImageFiles = await convertPathsToFiles(data.referenceImages)
          referenceImages.value = referenceImageFiles
          console.log('✅ 参考图回填成功:', referenceImageFiles.length, '张')
        } catch (error) {
          console.error('参考图回填失败:', error)
          message.warning('参考图回填失败，请手动重新上传')
        }
      }
      
      // 回填LoRA
      if (data.loras && data.loras.length > 0) {
        selectedLoras.value = data.loras
      }
      
      // 回填其他参数
      if (data.parameters) {
        if (data.parameters.steps) {
          // 这里需要根据实际的参数结构来设置
          console.log('回填步数:', data.parameters.steps)
        }
        if (data.parameters.cfg) {
          console.log('回填CFG:', data.parameters.cfg)
        }
      }
      
      // 清除回填数据
      localStorage.removeItem('regenerateData')
      console.log('✅ 参数回填完成')
      
      // 显示提示
      message.success('参数已回填，可以开始生成')
      
    } catch (error) {
      console.error('回填数据解析失败:', error)
      localStorage.removeItem('regenerateData')
    }
  }
  
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
  padding: 0 0 180px 0; /* 为底部固定控制面板预留空间 */
}

/* 确保控制面板始终在最上层 */
.control-section {
  position: fixed !important;
  bottom: 0px !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  z-index: 1999 !important;
  pointer-events: auto !important;
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