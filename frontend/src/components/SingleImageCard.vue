<template>
  <div class="single-image-card">
    <!-- 图像容器 -->
    <div class="image-container" @click="$emit('previewImage', image)">
      <img :src="image.directUrl || image.url" :alt="image.prompt" class="gallery-image" />
      
      <!-- 图片操作悬浮层 -->
      <div class="image-overlay">
        <a-tooltip title="预览图片">
          <a-button 
            type="text" 
            shape="circle" 
            class="overlay-btn preview-btn" 
            @click.stop="$emit('previewImage', image)"
          >
            <template #icon><EyeOutlined /></template>
          </a-button>
        </a-tooltip>
        <a-tooltip :title="image.isFavorited ? '取消收藏' : '收藏图片'">
          <a-button 
            type="text" 
            shape="circle" 
            :class="['overlay-btn', 'favorite-btn', { 'favorited': image.isFavorited }]" 
            @click.stop="$emit('toggleFavorite', image)"
          >
            <template #icon>
              <HeartOutlined v-if="!image.isFavorited" />
              <HeartFilled v-else />
            </template>
          </a-button>
        </a-tooltip>
        <a-tooltip title="下载图片">
          <a-button 
            type="text" 
            shape="circle" 
            class="overlay-btn download-btn" 
            @click.stop="$emit('downloadImage', image)"
          >
            <template #icon><DownloadOutlined /></template>
          </a-button>
        </a-tooltip>
      </div>
    </div>
    
    <!-- 图片信息 -->
    <div class="image-info">
      <div class="image-prompt" :title="image.prompt">
        {{ image.prompt || '无提示词' }}
      </div>
      <div class="image-meta">
        <span class="image-time">{{ formatTime(image.createdAt || image.timestamp) }}</span>
        <span v-if="image.isFavorited" class="favorite-indicator">❤️</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { EyeOutlined, HeartOutlined, HeartFilled, DownloadOutlined } from '@ant-design/icons-vue'

// Props
defineProps({
  image: {
    type: Object,
    required: true
  }
})

// Emits
defineEmits([
  'previewImage',
  'toggleFavorite',
  'downloadImage'
])

// 格式化时间
const formatTime = (date) => {
  if (!date) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(date))
}
</script>

<style scoped>
.single-image-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  cursor: pointer;
}

.single-image-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.image-container {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  margin-bottom: 8px;
}

.gallery-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 12px;
}

.image-container:hover .image-overlay {
  opacity: 1;
}

.overlay-btn {
  color: white;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
  transition: all 0.2s ease;
}

.overlay-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  color: white;
  transform: scale(1.1);
}

.preview-btn {
  background: rgba(64, 169, 255, 0.3);
  border-color: rgba(64, 169, 255, 0.5);
}

.preview-btn:hover {
  background: rgba(64, 169, 255, 0.5);
  border-color: rgba(64, 169, 255, 0.7);
}

.favorite-btn {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
}

.favorite-btn:hover {
  background: rgba(255, 107, 107, 0.3);
  border-color: rgba(255, 107, 107, 0.5);
}

.favorite-btn.favorited {
  background: rgba(255, 107, 107, 0.4);
  border-color: rgba(255, 107, 107, 0.6);
  color: #ff6b6b;
}

.favorite-btn.favorited:hover {
  background: rgba(255, 107, 107, 0.6);
  border-color: rgba(255, 107, 107, 0.8);
}

.download-btn {
  background: rgba(82, 196, 26, 0.3);
  border-color: rgba(82, 196, 26, 0.5);
}

.download-btn:hover {
  background: rgba(82, 196, 26, 0.5);
  border-color: rgba(82, 196, 26, 0.7);
}

.image-info {
  padding: 0 4px;
}

.image-prompt {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.3;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-word;
}

.image-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.image-time {
  flex: 1;
}

.favorite-indicator {
  font-size: 0.875rem;
  margin-left: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .single-image-card {
    padding: 8px;
  }
  
  .image-prompt {
    font-size: 0.8rem;
    -webkit-line-clamp: 1;
  }
  
  .image-meta {
    font-size: 0.7rem;
  }
}
</style>
