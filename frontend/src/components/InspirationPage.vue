<template>
  <div class="inspiration-page">
    <div class="page-header">
      <h2>我的灵感</h2>
      <p>收藏的精彩作品</p>
    </div>
    
    <div class="loading-state" v-if="loading">
      <a-spin size="large" />
      <p>加载收藏中...</p>
    </div>
    
    <div class="inspiration-grid" v-else-if="favorites.length > 0">
      <div 
        v-for="item in favorites" 
        :key="item.id"
        class="inspiration-item"
        @click="showDetail(item)"
      >
        <div class="item-image">
          <!-- 视频显示 -->
          <video 
            v-if="item.type === 'video'" 
            :src="item.videoUrl" 
            class="item-video"
            preload="metadata"
            muted
          />
          <!-- 图片显示 -->
          <template v-else>
            <!-- 骨架屏 -->
            <div v-if="getImageLoading(item.id)" class="image-skeleton">
              <div class="skeleton-shimmer"></div>
            </div>
            <!-- 实际图片 -->
            <img 
              v-show="!getImageLoading(item.id)"
              :src="item.thumbnailUrl || item.imageUrl" 
              :alt="item.title"
              @load="handleImageLoad(item.id)"
              @error="handleImageError(item.id)"
            />
          </template>
          <div class="item-overlay">
            <EyeOutlined class="view-icon" />
            <span v-if="item.type === 'video'" class="video-badge">🎬</span>
          </div>
        </div>
        <div class="item-info">
          <h4>{{ item.title }}</h4>
          <div class="item-meta">
            <span class="date">{{ formatDate(item.createdAt) }}</span>
            <button 
              class="remove-favorite-btn" 
              @click.stop="removeFavorite(item)"
              title="取消收藏"
            >
              <HeartFilled class="favorite-icon" />
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div class="empty-state" v-else>
      <div class="empty-icon">
        <StarOutlined />
      </div>
      <h3>还没有收藏的作品</h3>
      <p>去生图页面创建一些精彩作品吧</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { EyeOutlined, HeartFilled, StarOutlined } from '@ant-design/icons-vue'

const emit = defineEmits(['show-detail'])

const favorites = ref([])
const loading = ref(false)
const imageLoadingStates = ref(new Map()) // 存储每个图片的加载状态

// API基础URL - 自动检测环境
const API_BASE = (() => {
  // 开发环境：指向后端9000端口
  if (import.meta.env.DEV) {
    return 'http://localhost:9000'
  }
  // 生产环境：使用环境变量或默认空字符串（通过nginx代理）
  return import.meta.env.VITE_API_BASE_URL || ''
})()

const loadFavorites = async () => {
  loading.value = true
  try {
    // 使用专门的收藏API
    const response = await fetch(`${API_BASE}/api/favorites`)
    if (response.ok) {
      const data = await response.json()
      favorites.value = data.favorites || []
      
      // 初始化所有图片的加载状态
      favorites.value.forEach(item => {
        if (item.type !== 'video') {
          imageLoadingStates.value.set(item.id, true)
        }
      })
    } else {
      console.error('获取收藏列表失败:', response.statusText)
      favorites.value = []
    }
  } catch (error) {
    console.error('获取收藏列表出错:', error)
    favorites.value = []
  } finally {
    loading.value = false
  }
}

// 获取图片加载状态
const getImageLoading = (itemId) => {
  return imageLoadingStates.value.get(itemId) || false
}

// 处理图片加载完成
const handleImageLoad = (itemId) => {
  imageLoadingStates.value.set(itemId, false)
}

// 处理图片加载错误
const handleImageError = (itemId) => {
  imageLoadingStates.value.set(itemId, false)
  console.warn('灵感页面图片加载失败:', itemId)
}

const showDetail = (item) => {
  emit('show-detail', item)
}

const removeFavorite = async (item) => {
  try {
    console.log('🗑️ 灵感页面取消收藏:', item)
    
    if (item.type === 'video') {
      // 取消视频收藏
      const response = await fetch(`${API_BASE}/api/favorites/videos/${item.task_id}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        throw new Error('取消视频收藏失败')
      }
    } else {
      // 取消图片收藏
      const response = await fetch(`${API_BASE}/api/favorites/images/${item.task_id}/${item.image_index}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        throw new Error('取消图片收藏失败')
      }
    }
    
    // 重新加载收藏列表
    await loadFavorites()
    
  } catch (error) {
    console.error('取消收藏失败:', error)
    alert(`取消收藏失败: ${error.message}`)
  }
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadFavorites()
  
  // 监听取消收藏事件，重新加载收藏列表
  window.addEventListener('refresh-favorites', loadFavorites)
})

onUnmounted(() => {
  window.removeEventListener('refresh-favorites', loadFavorites)
})
</script>

<style scoped>
.inspiration-page {
  padding: 24px;
  background: #0f0f0f;
  min-height: 100vh;
  width: 80%;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h2 {
  color: #fff;
  font-size: 24px;
  margin: 0 0 8px 0;
}

.page-header p {
  color: #888;
  margin: 0;
}

.inspiration-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}

.inspiration-item {
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.inspiration-item:hover {
  transform: translateY(-4px);
}

.item-image {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
}

.item-image img,
.item-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-skeleton {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0.1) 0%, 
    rgba(255, 255, 255, 0.2) 50%, 
    rgba(255, 255, 255, 0.1) 100%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: 12px;
  position: relative;
}

.skeleton-shimmer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.1) 50%, 
    transparent 100%);
  animation: shimmer 2s infinite;
}

@keyframes skeleton-loading {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.item-video {
  background: #000;
}

.item-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.inspiration-item:hover .item-overlay {
  opacity: 1;
}

.view-icon {
  font-size: 24px;
  color: #fff;
}

.video-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.item-info {
  padding: 12px;
}

.item-info h4 {
  color: #fff;
  margin: 0 0 6px 0;
  font-size: 14px;
}

.item-info p {
  color: #888;
  margin: 0 0 12px 0;
  font-size: 14px;
  line-height: 1.4;
}

.item-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.date {
  color: #666;
  font-size: 12px;
}

.favorite-icon {
  color: #ff4757;
  font-size: 16px;
}

.remove-favorite-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-favorite-btn:hover {
  background: rgba(255, 71, 87, 0.1);
  transform: scale(1.1);
}

.remove-favorite-btn:hover .favorite-icon {
  color: #ff3742;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  font-size: 64px;
  color: #333;
  margin-bottom: 24px;
}

.empty-state h3 {
  color: #fff;
  margin: 0 0 12px 0;
  font-size: 20px;
}

.empty-state p {
  color: #888;
  margin: 0;
}

.loading-state {
  text-align: center;
  padding: 80px 20px;
}

.loading-state p {
  color: #888;
  margin-top: 16px;
}
</style>
