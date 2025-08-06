<template>
  <div class="gallery-section">
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
    
    <!-- 加载更多按钮 -->
    <div v-if="hasMore && !isLoadingHistory" class="load-more-section">
      <a-button 
        type="primary" 
        size="large" 
        @click="$emit('loadMore')"
        class="load-more-btn"
      >
        加载更多历史记录
      </a-button>
    </div>
    
    <!-- 加载中状态 -->
    <div v-if="isLoadingHistory" class="loading-section">
      <a-spin size="large">
        <template #indicator>
          <LoadingOutlined style="font-size: 24px" spin />
        </template>
      </a-spin>
      <p>正在加载历史记录...</p>
    </div>
    
    <!-- 分页信息 -->
    <div v-if="totalCount > 0" class="pagination-info">
      <p>共 {{ totalCount }} 条记录，已显示 {{ allImages.length }} 条</p>
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
import { computed, ref } from 'vue'
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
defineEmits([
  'editImage',
  'regenerateImage', 
  'deleteImage',
  'downloadImage',
  'loadMore'
])

// 图片预览相关状态
const previewVisible = ref(false)
const selectedImage = ref({})

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

/* 分页相关样式 */
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

.pagination-info {
  text-align: center;
  margin: 20px 0;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
  color: #666;
  font-size: 14px;
}

.pagination-info p {
  margin: 0;
}
</style>