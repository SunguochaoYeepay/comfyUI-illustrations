<template>
  <div class="gallery-section" ref="galleryRef">
    <!-- 顶部滚动加载触发区域 -->
    <div 
      v-if="hasMore && !isLoadingHistory && allImages.length > 0" 
      class="scroll-trigger-top" 
      ref="topTriggerRef"
    >
      <div class="trigger-content">
        <LoadingOutlined class="trigger-icon" />
        <span>向上滑动加载更多</span>
      </div>
    </div>
    
    <!-- 图像展示网格 - 历史图片始终显示 -->
    <div v-if="allImages.length > 0" class="image-gallery">
      <TaskCard
        v-for="(group, groupIndex) in imageGroups"
        :key="groupIndex"
        :group="group"
        @edit-image="$emit('editImage', $event)"
        @regenerate-image="$emit('regenerateImage', $event)"
        @delete-image="$emit('deleteImage', $event)"
        @download-image="$emit('downloadImage', $event)"
        @preview-image="handlePreviewImage"
      />
    </div>
    
    <!-- 空状态 -->
    <div v-if="!isGenerating && allImages.length === 0" class="empty-gallery">
      <div class="empty-content">
        <PictureOutlined class="empty-icon" />
        <h3>还没有生成图像</h3>
        <p>输入您的创意提示词，开始创作第一张图像吧！</p>
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
      <p>正在加载更多历史记录...</p>
    </div>
    
    <!-- 没有更多数据提示 -->
    <div v-if="!hasMore && !isLoadingHistory && allImages.length > 0" class="no-more-section">
      <div class="no-more-content">
        <span class="no-more-text">已加载全部历史记录</span>
        <div class="no-more-divider"></div>
      </div>
    </div>

    <!-- 图片预览组件 -->
    <ImagePreview
      :visible="previewVisible"
      :image-data="selectedImage"
      @close="closePreview"
    />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, nextTick } from 'vue'
import { PictureOutlined, LoadingOutlined } from '@ant-design/icons-vue'
import TaskCard from './TaskCard.vue'
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
  }
})

// Emits
const emit = defineEmits([
  'editImage',
  'regenerateImage', 
  'deleteImage',
  'downloadImage',
  'loadMore'
])

// 图片预览相关状态
const previewVisible = ref(false)
const selectedImage = ref({})

// 滚动监听相关
const galleryRef = ref(null)
const topTriggerRef = ref(null)
let isAutoLoading = false

// 处理图片预览
const handlePreviewImage = (image) => {
  selectedImage.value = {
    ...image,
    url: image.directUrl || image.url,
    createdAt: image.createdAt || image.timestamp
  }
  previewVisible.value = true
}

// 关闭预览
const closePreview = () => {
  previewVisible.value = false
  selectedImage.value = {}
}

// 计算属性：将图像按任务分组，每组四张图片
const imageGroups = computed(() => {
  const groups = []
  const taskGroups = new Map()
  
  // 按task_id分组
  props.allImages.forEach(image => {
    const taskId = image.task_id || 'unknown'
    if (!taskGroups.has(taskId)) {
      taskGroups.set(taskId, [])
    }
    taskGroups.get(taskId).push(image)
  })
  
  // 将每个任务组转换为数组，并按时间正序排序（最新的在后面）
  Array.from(taskGroups.values())
    .sort((a, b) => {
      const timeA = new Date(a[0].createdAt || a[0].timestamp)
      const timeB = new Date(b[0].createdAt || b[0].timestamp)
      return timeA - timeB
    })
    .forEach(group => {
      groups.push(group)
    })
  
  return groups
})

// 滚动监听函数 - 改为监听滚动到顶部（作为备用机制）
const handleScroll = () => {
  if (isAutoLoading || !props.hasMore || props.isLoadingHistory) {
    return
  }

  const scrollTop = window.pageYOffset || document.documentElement.scrollTop
  
  // 当滚动到距离顶部30px时触发加载
  if (scrollTop <= 30) {
    isAutoLoading = true
    emit('loadMore')
    
    // 减少延迟时间
    setTimeout(() => {
      isAutoLoading = false
    }, 300)
  }
}

// 使用Intersection Observer监听顶部滚动触发区域
let observer = null

const setupIntersectionObserver = () => {
  if (!topTriggerRef.value) return
  
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && props.hasMore && !props.isLoadingHistory && !isAutoLoading) {
          isAutoLoading = true
          emit('loadMore')
          
          // 减少延迟时间，提高响应速度
          setTimeout(() => {
            isAutoLoading = false
          }, 300)
        }
      })
    },
    {
      rootMargin: '100px' // 增加触发范围
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
  
  // 设置Intersection Observer
  nextTick(() => {
    setupIntersectionObserver()
    // 页面加载时滚动到底部
    scrollToBottom()
  })
})

onUnmounted(() => {
  // 移除滚动监听
  window.removeEventListener('scroll', handleScroll)
  
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
  text-align: center;
  margin: 40px 0;
  color: #666;
}

.loading-section p {
  margin-top: 16px;
  font-size: 14px;
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
</style>