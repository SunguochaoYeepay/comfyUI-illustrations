<template>
  <div class="task-card">
    <!-- 任务信息头部 -->
    <div class="task-header">
      <div class="task-info">
        <p class="task-prompt">
          <span v-if="isVideoTask" class="video-icon">🎬</span>
          <span v-else-if="isUpscaleTask" class="upscale-icon">🔍</span>
          {{ group[0]?.prompt || '无提示词' }} 
          <span class="task-meta">
            <span v-if="group[0]?.status === 'completed'">
              <span v-if="isVideoTask">1个视频</span>
              <span v-else>{{ group.length }}张图片</span>
            </span>
            <span v-else-if="group[0]?.status === 'processing'" class="status-processing">
              <span v-if="isVideoTask">视频生成中...</span>
              <span v-else>生成中...</span>
            </span>
            <span v-else-if="group[0]?.status === 'failed'" class="status-failed">
              <span v-if="isVideoTask">视频生成失败</span>
              <span v-else>生成失败</span>
            </span>
            · {{ new Date(group[0]?.createdAt).toLocaleString() }}
          </span>
        </p>
      </div>
      <div class="task-actions">
        <!-- 操作按钮 -->
        <div class="action-buttons">
          <!-- 只有非放大任务和非视频任务才显示重新编辑和再次生成按钮 -->
          <template v-if="!isUpscaleTask && !isVideoTask">
            <a-button type="text" size="small" @click.stop="$emit('editImage', group[0])" class="action-btn">
              重新编辑
            </a-button>
            <a-button type="text" size="small" @click.stop="$emit('regenerateImage', group[0])" class="action-btn">
              再次生成
            </a-button>
          </template>
          <a-button type="text" size="small" @click.stop="$emit('deleteImage', group[0])" class="action-btn delete-btn">
            删除
          </a-button>
        </div>
      </div>
    </div>
    
    <!-- 图片网格或状态显示 -->
    <div v-if="group.length > 0 && group[0]?.status === 'completed'" class="images-grid" :data-count="group.length">
      <!-- 视频任务特殊显示 -->
      <div v-if="isVideoTask" class="video-display">
        <div class="video-container" @click="$emit('previewImage', group[0])">
          <img 
            :src="group[0].referenceImage || group[0].thumbnail || group[0].url" 
            class="video-preview" 
            alt="视频预览"
          />
          <div class="video-overlay">
            <div class="video-info">
              <span class="video-title">🎬 点击查看视频</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 图片任务正常显示 -->
      <template v-else>
        <!-- 显示所有图片 -->
        <div
          v-for="(image, index) in group"
          :key="index"
          class="image-item"
        >
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
                  <template #icon><HeartOutlined v-if="!image.isFavorited" /><HeartFilled v-else /></template>
                </a-button>
              </a-tooltip>
            </div>
          </div>
        </div>
      </template>
    </div>
    
    <!-- 非完成状态的任务显示 -->
    <div v-else class="status-display">
      <div v-if="group[0]?.status === 'processing'" class="status-card processing">
        <div class="status-icon">⏳</div>
        <div class="status-text">
          <span v-if="isVideoTask">视频生成中，请稍候...</span>
          <span v-else>图像生成中，请稍候...</span>
        </div>
      </div>
      <div v-else-if="group[0]?.status === 'failed'" class="status-card failed">
        <div class="status-icon">❌</div>
        <div class="status-text">
          <span v-if="isVideoTask">视频生成失败，请重试</span>
          <span v-else>生成失败，请重试</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { DownloadOutlined, EyeOutlined, HeartOutlined, HeartFilled } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  group: {
    type: Array,
    required: true
  }
})

// 计算属性：判断是否为放大任务
const isUpscaleTask = computed(() => {
  if (props.group && props.group.length > 0) {
    const firstImage = props.group[0]
    // 通过描述或URL来判断是否为放大任务
    if (firstImage.prompt && firstImage.prompt.includes('图像放大')) {
      return true
    }
    // 也可以通过URL路径判断
    if (firstImage.url && firstImage.url.includes('/api/upscale/')) {
      return true
    }
  }
  return false
})

// 计算属性：判断是否为视频生成任务
const isVideoTask = computed(() => {
  if (props.group && props.group.length > 0) {
    const firstImage = props.group[0]
    
    // 调试信息
    console.log('🔍 检查任务类型:', {
      prompt: firstImage.prompt,
      url: firstImage.url,
      result_path: firstImage.result_path,
      model: firstImage.model
    })
    
    // 通过描述来判断是否为视频生成任务
    if (firstImage.prompt && firstImage.prompt.includes('视频生成')) {
      console.log('✅ 通过描述识别为视频任务')
      return true
    }
    
    // 通过URL路径判断
    if (firstImage.url && firstImage.url.includes('/api/generate-video')) {
      console.log('✅ 通过URL路径识别为视频任务')
      return true
    }
    
    // 通过文件扩展名判断
    if (firstImage.url && (firstImage.url.endsWith('.mp4') || firstImage.url.endsWith('.avi') || firstImage.url.endsWith('.mov'))) {
      console.log('✅ 通过URL扩展名识别为视频任务')
      return true
    }
    
    // 通过文件名判断（包含video关键词）
    if (firstImage.url && firstImage.url.toLowerCase().includes('video')) {
      console.log('✅ 通过URL关键词识别为视频任务')
      return true
    }
    
    // 通过result_path判断（后端返回的路径）
    if (firstImage.result_path && (firstImage.result_path.endsWith('.mp4') || firstImage.result_path.endsWith('.avi') || firstImage.result_path.endsWith('.mov'))) {
      console.log('✅ 通过result_path扩展名识别为视频任务')
      return true
    }
    
    // 通过result_path判断（包含video关键词）
    if (firstImage.result_path && firstImage.result_path.toLowerCase().includes('video')) {
      console.log('✅ 通过result_path关键词识别为视频任务')
      return true
    }
    
    console.log('❌ 未识别为视频任务')
  }
  return false
})

// Emits
defineEmits([
  'editImage',
  'regenerateImage',
  'deleteImage', 
  'downloadImage',
  'previewImage',
  'toggleFavorite',
  'upscale'
])
</script>

<style scoped>
.task-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.task-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.task-info {
  flex: 1;
}

.task-prompt {
  font-size: 1rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
  line-height: 1.4;
  word-wrap: break-word;
}

.task-meta {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 400;
  margin-left: 8px;
  white-space: nowrap;
}

.task-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  color: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.1);
}

.delete-btn:hover {
  color: #ff4d4f;
  border-color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}

.images-grid {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(4, 1fr);
}

.image-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.image-container {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s ease;
  cursor: pointer;
}

.image-container:hover {
  transform: scale(1.02);
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

/* 状态显示样式 */
.status-display {
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.status-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  border-radius: 12px;
  min-height: 120px;
  width: 100%;
  text-align: center;
}

.status-card.processing {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: 1px solid #2196f3;
}

.status-card.failed {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  border: 1px solid #f44336;
}

.status-icon {
  font-size: 32px;
  margin-bottom: 12px;
}

.status-text {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.status-processing {
  color: #2196f3;
  font-weight: 500;
}

.status-failed {
  color: #f44336;
  font-weight: 500;
}

/* 视频任务特殊样式 */
.video-display {
  aspect-ratio: 1; /* 改为1:1，与图片任务保持一致 */
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.video-container {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
}

.video-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 12px;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 12px;
}

.video-container:hover .video-overlay {
  opacity: 1;
}

.video-info {
  text-align: center;
}

.video-title {
  font-size: 18px;
  font-weight: 600;
  color: white;
}

/* 任务类型图标样式 */
.video-icon, .upscale-icon {
  margin-right: 8px;
  font-size: 16px;
}
</style>