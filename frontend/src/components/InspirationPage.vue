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
          <img 
            v-else
            :src="item.imageUrl" 
            :alt="item.title" 
          />
          <div class="item-overlay">
            <EyeOutlined class="view-icon" />
            <span v-if="item.type === 'video'" class="video-badge">🎬</span>
          </div>
        </div>
        <div class="item-info">
          <h4>{{ item.title }}</h4>
          <p>{{ item.description }}</p>
          <div class="item-meta">
            <span class="date">{{ formatDate(item.createdAt) }}</span>
            <HeartFilled class="favorite-icon" />
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
import { ref, onMounted } from 'vue'
import { EyeOutlined, HeartFilled, StarOutlined } from '@ant-design/icons-vue'

const emit = defineEmits(['show-detail'])

const favorites = ref([])
const loading = ref(false)

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

const showDetail = (item) => {
  emit('show-detail', item)
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadFavorites()
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
