<template>
  <div class="gallery-container">
    <!-- 右上角控制按钮 -->
    <div v-if="allImages.length > 0" class="gallery-controls">
      <!-- 刷新按钮 -->
      <div class="refresh-trigger" @click="handleRefresh" title="刷新列表">
        <div class="refresh-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
          </svg>
        </div>
      </div>
      
      <!-- 筛选器触发按钮 -->
      <div class="filter-trigger" @click="toggleFilter">
        <div class="filter-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/>
          </svg>
        </div>
      </div>
      
      <!-- 筛选面板 -->
      <div v-show="filterVisible" class="filter-panel" @click.stop>
        <div class="filter-header">
          <h3>筛选器</h3>
          <button class="clear-filter-btn" @click="clearFilters" title="清空筛选条件">
            清空
          </button>
        </div>
        <div class="filter-content">
          <div class="filter-group">
            <label class="filter-label">收藏状态</label>
            <a-select 
              v-model:value="favoriteFilter" 
              class="filter-select"
              @change="handleFilterChange"
            >
              <a-select-option value="all">全部</a-select-option>
              <a-select-option value="favorited">已收藏</a-select-option>
              <a-select-option value="unfavorited">未收藏</a-select-option>
            </a-select>
          </div>
          <div class="filter-group">
            <label class="filter-label">时间筛选</label>
            <a-select 
              v-model:value="timeFilter" 
              class="filter-select"
              @change="handleFilterChange"
            >
              <a-select-option value="all">全部时间</a-select-option>
              <a-select-option value="today">今天</a-select-option>
              <a-select-option value="week">最近一周</a-select-option>
              <a-select-option value="month">最近一月</a-select-option>
            </a-select>
          </div>
          <div class="filter-stats">
            <p class="stats-item">总计: {{ allImages.length }} 张</p>
            <p class="stats-item">筛选结果: {{ filteredImages.length }} 张</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="gallery-main" ref="galleryRef">

         <!-- 顶部滚动加载触发区域 -->
     <div 
       v-if="hasMore && !isLoadingHistory && filteredImages.length > 0" 
       class="scroll-trigger-top" 
       ref="topTriggerRef"
     >
       <div class="trigger-content">
         <LoadingOutlined class="trigger-icon" />
         <span>加载中</span>
       </div>
     </div>
     
     <!-- 没有更多数据提示 - 移到顶部 -->
     <div v-if="!hasMore && !isLoadingHistory && filteredImages.length > 0" class="no-more-section-top">
       <div class="no-more-content">
         <span class="no-more-text">没有更多了</span>
       </div>
     </div>
     
           <!-- 图像展示区域 -->
      <div v-if="filteredImages.length > 0" class="image-gallery">
        <TaskCard
          v-for="(group, groupIndex) in filteredImageGroups"
          :key="groupIndex"
          :group="group"
          @edit-image="$emit('editImage', $event)"
          @regenerate-image="$emit('regenerateImage', $event)"
          @delete-image="$emit('deleteImage', $event)"
          @download-image="$emit('downloadImage', $event)"
          @preview-image="handlePreviewImage"
          @toggle-favorite="handleToggleFavorite"
          @toggle-video-favorite="handleToggleVideoFavorite"
          @upscale="$emit('upscale', $event)"
        />
      </div>
    
    <!-- 放大状态 - 显示在图片列表底部 -->
    <UpscalingState
      v-if="isUpscaling && !isGenerating"
      :scale-factor="currentScaleFactor"
      :progress="upscalingProgress"
    />
    
    <!-- 空状态 -->
    <div v-if="!isGenerating && !isLoadingHistory && allImages.length === 0" class="empty-gallery">
      <div class="empty-content">
        <PictureOutlined class="empty-icon" />
        <h3>还没有生成图像</h3>
        <p>输入您的创意提示词，开始创作第一张图像吧！</p>
      </div>
    </div>
    
    <!-- 筛选结果为空 -->
    <div v-if="!isGenerating && !isLoadingHistory && allImages.length > 0 && filteredImages.length === 0" class="empty-gallery">
      <div class="empty-content">
        <PictureOutlined class="empty-icon" />
        <h3>没有找到符合条件的图像</h3>
        <p>请尝试调整筛选条件</p>
      </div>
    </div>
    
    <!-- 生成状态 - 始终显示在历史图片下方 -->
    <GeneratingState
      v-if="isGenerating"
      :prompt="prompt"
      :image-count="imageCount"
      :progress="progress"
    />
    
    <!-- 自动加载中状态 -->
    <div v-if="isLoadingHistory" class="loading-section">
      <a-spin size="large">
        <template #indicator>
          <LoadingOutlined style="font-size: 24px" spin />
        </template>
      </a-spin>
      <p>数据加载中...</p>
    </div>
    
    <!-- 缓存状态提示 -->
    <div v-if="cacheStatus" class="cache-status">
      <div class="cache-indicator" :class="cacheStatus.type">
        <span class="cache-icon">{{ cacheStatus.icon }}</span>
        <span class="cache-text">{{ cacheStatus.text }}</span>
      </div>
    </div>
    
    

    <!-- 图片预览组件 -->
    <ImagePreview
      :visible="previewVisible"
      :image-data="selectedImage"
      :image-list="flatImageList"
      :current-index="currentImageIndex"
      :is-upscaling="isUpscaling"
      @close="closePreview"
      @navigate="handleImageNavigate"
      @upscale="handleUpscaleFromPreview"
      @refreshHistory="handleRefreshHistory"
      @video-task-created="handleVideoTaskCreated"
      @navigate-to-canvas="handleNavigateToCanvas"
    />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { PictureOutlined, LoadingOutlined } from '@ant-design/icons-vue'
import { Select as ASelect, SelectOption as ASelectOption } from 'ant-design-vue'
import UpscalingState from './UpscalingState.vue'
import TaskCard from './TaskCard.vue'
import SingleImageGrid from './SingleImageGrid.vue'
import GeneratingState from './GeneratingState.vue'
import ImagePreview from './ImagePreview.vue'

// Props
const props = defineProps({
  allImages: {
    type: Array,
    default: () => []
  },
  isGenerating: {
    type: Boolean,
    default: false
  },
  prompt: {
    type: String,
    default: ''
  },
  imageCount: {
    type: Number,
    default: 4
  },
  progress: {
    type: Number,
    default: 0
  },
  isUpscaling: {
    type: Boolean,
    default: false
  },
  upscalingProgress: {
    type: Number,
    default: 0
  },
  currentScaleFactor: {
    type: Number,
    default: 2
  },
  upscalingPrompt: {
    type: String,
    default: ''
  },
  hasMore: {
    type: Boolean,
    default: false
  },
  isLoadingHistory: {
    type: Boolean,
    default: false
  },
  totalCount: {
    type: Number,
    default: 0
  },
  cacheStatus: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits([
  'editImage',
  'regenerateImage',
  'deleteImage',
  'downloadImage',
  'loadMore',
  'toggleFavorite',
  'filterChange',
  'upscale',
  'refreshHistory',
  'video-task-created',
  'navigate-to-canvas'
])

// 筛选器相关
const favoriteFilter = ref('all') // all, favorited, unfavorited
const timeFilter = ref('all') // all, today, week, month
const filterVisible = ref(false) // 控制悬浮筛选器显示
let filterTimer = null // 延迟隐藏定时器

// 图片预览相关
const previewVisible = ref(false)
const selectedImage = ref({})
const currentImageIndex = ref(0)
const flatImageList = ref([])

// 滚动监听相关
const galleryRef = ref(null)
const topTriggerRef = ref(null)
let isAutoLoading = false
let lastScrollTime = 0
let scrollTimeout = null
let lastLoadTime = 0 // 记录上次加载时间
let isInitialized = false // 标记是否已完成初始化

// 获取图片尺寸的公共函数
const getImageDimensions = (url) => {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      resolve({ width: img.naturalWidth, height: img.naturalHeight })
    }
    img.onerror = () => {
      resolve({ width: null, height: null })
    }
    img.src = url
  })
}

// 处理图片预览
const handlePreviewImage = async (image) => {
  try {
    if (!image || !image.url) {
      console.warn('无效的图片数据:', image)
      return
    }
    
         console.log('=== 图片预览调试信息 ===')
     console.log('点击的图片:', image)
     console.log('filteredImageGroups数量:', filteredImageGroups.value.length)
     
     // 创建扁平化的图片列表（基于filteredImageGroups的顺序）
     flatImageList.value = []
     filteredImageGroups.value.forEach((group, groupIndex) => {
       console.log(`第${groupIndex}组图片数量:`, group.length)
       group.forEach((img, imgIndex) => {
         console.log(`  组${groupIndex}-图片${imgIndex}:`, {
           url: img.url,
           directUrl: img.directUrl,
           id: img.id,
           task_id: img.task_id,
           createdAt: img.createdAt || img.timestamp
         })
         flatImageList.value.push(img)
       })
     })
     
     console.log('flatImageList总数量:', flatImageList.value.length)
    
         // 找到当前图片在列表中的索引 - 使用更精确的匹配
     currentImageIndex.value = flatImageList.value.findIndex(img => {
       // 优先使用文件名匹配，因为文件名是唯一的
       if (img.filename === image.filename && img.task_id === image.task_id) {
         return true
       }
       // 备用匹配：URL匹配
       if (img.url === image.url || img.directUrl === image.url) {
         return true
       }
       // 最后备用：对象引用匹配
       if (img === image) {
         return true
       }
       return false
     })
    
         console.log('计算出的currentImageIndex:', currentImageIndex.value)
     console.log('匹配的图片:', flatImageList.value[currentImageIndex.value])
     console.log('点击的图片文件名:', image.filename)
     console.log('点击的图片task_id:', image.task_id)
     console.log('匹配的图片文件名:', flatImageList.value[currentImageIndex.value]?.filename)
     console.log('匹配的图片task_id:', flatImageList.value[currentImageIndex.value]?.task_id)
    
    // 获取图片尺寸
    const getImageDimensions = (url) => {
      return new Promise((resolve) => {
        const img = new Image()
        img.onload = () => {
          resolve({ width: img.naturalWidth, height: img.naturalHeight })
        }
        img.onerror = () => {
          console.warn('获取图片尺寸失败:', url)
          resolve({ width: null, height: null })
        }
        img.src = url
      })
    }

    const imageUrl = image.directUrl || image.url
    
    // 先设置基本信息并立即显示预览窗口
    selectedImage.value = {
      ...image,
      url: imageUrl,
      createdAt: image.createdAt || image.timestamp || new Date(),
      width: null, // 先设为null，后续异步获取
      height: null // 先设为null，后续异步获取
    }
    previewVisible.value = true
    
    // 异步获取图片尺寸（不阻塞预览窗口显示）
    const dimensions = await getImageDimensions(imageUrl)
    selectedImage.value = {
      ...selectedImage.value,
      width: dimensions.width,
      height: dimensions.height
    }
  } catch (error) {
    console.error('处理图片预览时出错:', error, image)
  }
}

// 关闭预览
const closePreview = () => {
  previewVisible.value = false
  selectedImage.value = {}
  currentImageIndex.value = 0
  flatImageList.value = []
}

 // 处理图片导航
 const handleImageNavigate = async (newIndex) => {
   console.log('=== 图片导航调试信息 ===')
   console.log('请求导航到索引:', newIndex)
   console.log('当前索引:', currentImageIndex.value)
   console.log('flatImageList长度:', flatImageList.value.length)
   console.log('flatImageList前5张图片:', flatImageList.value.slice(0, 5).map((img, idx) => ({
     index: idx,
     filename: img.filename,
     task_id: img.task_id,
     url: img.url
   })))
   
   if (newIndex >= 0 && newIndex < flatImageList.value.length) {
     currentImageIndex.value = newIndex
     const newImage = flatImageList.value[newIndex]
     console.log('导航到的图片:', newImage)
    
    const imageUrl = newImage.directUrl || newImage.url
    
    // 获取图片尺寸
    const getImageDimensions = (url) => {
      return new Promise((resolve) => {
        const img = new Image()
        img.onload = () => {
          resolve({ width: img.naturalWidth, height: img.naturalHeight })
        }
        img.onerror = () => {
          console.warn('获取图片尺寸失败:', url)
          resolve({ width: null, height: null })
        }
        img.src = url
      })
    }
    
    const dimensions = await getImageDimensions(imageUrl)
    
    selectedImage.value = {
      ...newImage,
      url: imageUrl,
      createdAt: newImage.createdAt || newImage.timestamp,
      width: dimensions.width,
      height: dimensions.height
    }
  }
}

// 处理从预览组件触发的放大请求
const handleUpscaleFromPreview = (imageData, scaleFactor) => {
  emit('upscale', imageData, scaleFactor)
}

// 处理视频任务创建
const handleVideoTaskCreated = (taskId) => {
  console.log('🎬 ImageGallery 接收到视频任务创建事件:', taskId)
  emit('video-task-created', taskId)
}

// 处理刷新历史记录
const handleRefreshHistory = () => {
  emit('refreshHistory')
}

// 处理跳转到画布页面
const handleNavigateToCanvas = (data) => {
  console.log('🎨 跳转到画布页面:', data)
  // 发送事件到父组件，跳转到画布页面
  emit('navigate-to-canvas', data)
}

// 处理手动刷新
const handleRefresh = () => {
  console.log('🔄 用户手动刷新列表')
  emit('refreshHistory', { forceRefresh: true })
}

// 处理收藏切换
const handleToggleFavorite = (image) => {
  emit('toggleFavorite', image)
}

// 处理视频收藏切换
const handleToggleVideoFavorite = (video) => {
  emit('toggleVideoFavorite', video)
}

// 处理筛选条件变化
const handleFilterChange = () => {
  // 发出筛选条件变化事件
  const filterParams = {
    favoriteFilter: favoriteFilter.value,
    timeFilter: timeFilter.value
  }
  emit('filterChange', filterParams)
}

// 切换筛选器显示状态
const toggleFilter = () => {
  filterVisible.value = !filterVisible.value
}

// 清空筛选条件
const clearFilters = () => {
  favoriteFilter.value = 'all'
  timeFilter.value = 'all'
  handleFilterChange()
}

// 点击外部关闭筛选面板
const handleClickOutside = (event) => {
  const filterTrigger = document.querySelector('.filter-trigger')
  if (filterVisible.value && filterTrigger && !filterTrigger.contains(event.target)) {
    filterVisible.value = false
  }
}

// 时间筛选辅助函数
const isInTimeRange = (imageDate, timeRange) => {
  const now = new Date()
  const imgDate = new Date(imageDate)
  
  switch (timeRange) {
    case 'today':
      return imgDate.toDateString() === now.toDateString()
    case 'week':
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      return imgDate >= weekAgo
    case 'month':
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      return imgDate >= monthAgo
    default:
      return true
  }
}

// 计算属性：筛选后的图像
const filteredImages = computed(() => {
  if (!props.allImages || props.allImages.length === 0) {
    return []
  }
  
  return props.allImages.filter(image => {
    // 收藏状态筛选
    if (favoriteFilter.value === 'favorited' && !image.isFavorited) {
      return false
    }
    if (favoriteFilter.value === 'unfavorited' && image.isFavorited) {
      return false
    }
    
    // 时间筛选
    if (timeFilter.value !== 'all') {
      const imageDate = image.createdAt || image.timestamp
      if (!isInTimeRange(imageDate, timeFilter.value)) {
        return false
      }
    }
    
    return true
  })
})

// 计算属性：筛选后的图像按任务分组
const filteredImageGroups = computed(() => {
  // 如果筛选后的数据为空，直接返回空数组
  if (!filteredImages.value || filteredImages.value.length === 0) {
    return []
  }
  
  const groups = []
  const taskGroups = new Map()
  
  // 按task_id分组
  filteredImages.value.forEach(image => {
    try {
      const taskId = image.task_id || 'unknown'
      if (!taskGroups.has(taskId)) {
        taskGroups.set(taskId, [])
      }
      taskGroups.get(taskId).push(image)
    } catch (error) {
      console.error('处理图片分组时出错:', error, image)
    }
  })
  
  // 将每个任务组转换为数组（后端已经按时间降序排列，前端不需要再排序）
  Array.from(taskGroups.values()).forEach(group => {
    groups.push(group)
  })
  
  return groups
})



// 滚动监听函数 - 改为监听滚动到顶部（作为备用机制）
const handleScroll = () => {
  // 如果还未初始化完成，不处理滚动事件
  if (!isInitialized) {
    return
  }
  
  if (isAutoLoading || !props.hasMore || props.isLoadingHistory) {
    return
  }

  const now = Date.now()
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop
  
  // 当滚动到距离顶部50px时触发加载（增加触发距离）
  if (scrollTop <= 50) {
    // 防止频繁触发：至少间隔3秒，且距离上次加载至少5秒
    if (now - lastScrollTime < 3000 || now - lastLoadTime < 5000) {
      return
    }
    
    // 清除之前的定时器
    if (scrollTimeout) {
      clearTimeout(scrollTimeout)
    }
    
    // 设置新的定时器，延迟触发
    scrollTimeout = setTimeout(() => {
      if (!isAutoLoading && !props.isLoadingHistory) {
        isAutoLoading = true
        lastScrollTime = now
        lastLoadTime = now
        emit('loadMore')
        
        // 增加延迟时间，避免频繁触发
        setTimeout(() => {
          isAutoLoading = false
        }, 3000) // 增加到3秒延迟
      }
    }, 800) // 800ms延迟触发
  }
}

// 使用Intersection Observer监听顶部滚动触发区域
let observer = null

const setupIntersectionObserver = () => {
  if (!topTriggerRef.value) return
  
  // 清理之前的observer
  if (observer) {
    observer.disconnect()
  }
  
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        // 如果还未初始化完成，不处理滚动事件
        if (!isInitialized) {
          return
        }
        
        if (entry.isIntersecting && props.hasMore && !props.isLoadingHistory && !isAutoLoading) {
          const now = Date.now()
          
          // 防止频繁触发：至少间隔3秒，且距离上次加载至少5秒
          if (now - lastScrollTime < 3000 || now - lastLoadTime < 5000) {
            return
          }
          
          isAutoLoading = true
          lastScrollTime = now
          lastLoadTime = now
          emit('loadMore')
          
          // 增加延迟时间，避免频繁触发
          setTimeout(() => {
            isAutoLoading = false
          }, 3000) // 增加到3秒延迟
        }
      })
    },
    {
      rootMargin: '150px', // 增加触发范围
      threshold: 0.3 // 降低触发阈值
    }
  )
  
  observer.observe(topTriggerRef.value)
}

// 滚动到底部的函数
const scrollToBottom = () => {
  nextTick(() => {
    window.scrollTo({
      top: document.documentElement.scrollHeight,
      behavior: 'smooth'
    })
  })
}

// 生命周期钩子
onMounted(() => {
  // 添加滚动监听
  window.addEventListener('scroll', handleScroll, { passive: true })
  
  // 添加点击外部关闭筛选面板的监听器
  document.addEventListener('click', handleClickOutside)
  
  // 设置Intersection Observer
  nextTick(() => {
    setupIntersectionObserver()
    
    // 延迟标记初始化完成，避免页面加载时的滚动触发翻页
    setTimeout(() => {
      isInitialized = true
    }, 2000) // 2秒后启用滚动监听
  })
})

onUnmounted(() => {
  // 移除滚动监听
  window.removeEventListener('scroll', handleScroll)
  
  // 移除点击外部关闭筛选面板的监听器
  document.removeEventListener('click', handleClickOutside)
  
  // 清理定时器
  if (scrollTimeout) {
    clearTimeout(scrollTimeout)
    scrollTimeout = null
  }
  
  // 清理Intersection Observer
  if (observer) {
    observer.disconnect()
    observer = null
  }
})


</script>

<style scoped>
.gallery-section {
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
  padding: 0 20px;
}

.image-gallery {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-gallery {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 2px dashed rgba(255, 255, 255, 0.1);
}

.empty-content {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 20px;
  opacity: 0.3;
}

.empty-content h3 {
  font-size: 1.5rem;
  margin-bottom: 10px;
  color: rgba(255, 255, 255, 0.8);
}

.empty-content p {
  font-size: 1rem;
  opacity: 0.7;
}

/* 加载相关样式 */
.load-more-section {
  text-align: center;
  margin: 40px 0;
}

.load-more-btn {
  padding: 12px 32px;
  height: auto;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
}

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #888;
}

.loading-tip {
  font-size: 12px;
  color: #666;
  margin-top: 8px;
}

.loading-count {
  font-size: 12px;
  color: #666;
  margin-top: 10px;
}

.loading-progress {
  font-size: 12px;
  color: #888;
  margin-top: 8px;
  font-style: italic;
}

/* 主容器布局 */
.gallery-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.gallery-main {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  padding: 0 20px;
}

/* 右上角控制按钮样式 */
.gallery-controls {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  display: flex;
  gap: 12px;
  align-items: center;
}



/* 右上角控制按钮样式 */
.refresh-trigger {
  position: relative;
}

.filter-trigger {
  position: relative;
}

.refresh-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.refresh-icon:hover {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 1);
  transform: scale(1.05);
}

.filter-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.filter-icon:hover {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 1);
  transform: scale(1.05);
}

.filter-panel {
  position: absolute;
  right: 0;
  top: 60px;
  width: 280px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.filter-header {
  padding: 20px 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-header h3 {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  font-weight: 600;
}

.clear-filter-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.8);
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(5px);
}

.clear-filter-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 1);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.clear-filter-btn:active {
  transform: translateY(0);
}

.filter-content {
  padding: 20px;
}

.filter-group {
  margin-bottom: 24px;
}

.filter-group:last-of-type {
  margin-bottom: 0;
}

.filter-label {
  display: block;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.filter-select {
  width: 100%;
}

.filter-stats {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.stats-item {
  margin: 0 0 8px 0;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}

.stats-item:last-child {
  margin-bottom: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-trigger {
    right: 10px;
  }
  
  .filter-panel {
    width: 260px;
    right: 50px;
  }
  
  .filter-content {
    padding: 16px;
  }
  
  .filter-group {
    margin-bottom: 16px;
  }
}

@media (max-width: 480px) {
  .filter-panel {
    width: calc(100vw - 80px);
    right: 50px;
  }
}

/* 滚动触发区域样式 */
.scroll-trigger {
  text-align: center;
  padding: 20px;
  min-height: 60px;
}

.scroll-trigger-top {
  margin: 0 0 10px 0;
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(10px);
  background: rgba(26, 26, 26, 0.8);
  border-radius: 8px;
  padding: 8px 16px;
  text-align: center;
  transition: all 0.3s ease;
}

.trigger-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.trigger-icon {
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.scroll-hint {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  padding: 10px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px dashed rgba(255, 255, 255, 0.1);
}

.scroll-hint p {
  margin: 0;
  opacity: 0.7;
}

 /* 没有更多数据提示样式 */
 .no-more-section {
   text-align: center;
   margin: 40px 0;
   padding: 20px;
 }
 
 /* 顶部没有更多数据提示样式 */
 .no-more-section-top {
   text-align: center;
   margin: 0 0 20px 0;
   padding: 15px 20px;
   background: rgba(255, 255, 255, 0.05);
   border-radius: 8px;
   border: 1px solid rgba(255, 255, 255, 0.1);
 }

.no-more-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.no-more-text {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  white-space: nowrap;
}

.no-more-divider {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  max-width: 200px;
}

/* 缓存状态样式 */
.cache-status {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 999;
  animation: slideInRight 0.3s ease;
}

.cache-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.cache-indicator.valid {
  background: rgba(76, 175, 80, 0.2);
  color: #4CAF50;
  border-color: rgba(76, 175, 80, 0.3);
}

.cache-indicator.stale {
  background: rgba(255, 193, 7, 0.2);
  color: #FFC107;
  border-color: rgba(255, 193, 7, 0.3);
}

.cache-indicator.invalid {
  background: rgba(244, 67, 54, 0.2);
  color: #F44336;
  border-color: rgba(244, 67, 54, 0.3);
}

.cache-icon {
  font-size: 14px;
}

.cache-text {
  white-space: nowrap;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>