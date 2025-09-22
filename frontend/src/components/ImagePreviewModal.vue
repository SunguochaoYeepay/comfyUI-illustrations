<template>
  <div v-if="visible" class="image-preview-overlay" @click="closeModal">
    <div class="image-preview-container" @click.stop>
      <!-- 关闭按钮 -->
      <button class="close-btn" @click="closeModal">
        <CloseOutlined />
      </button>
      
      <!-- 主要内容区域 -->
      <div class="preview-content">
        <!-- 左侧图片区域 -->
        <div class="preview-image-container">
          <!-- 图片加载骨架屏 -->
          <div v-if="imageLoading" class="preview-image-skeleton">
            <div class="skeleton-shimmer"></div>
          </div>
          <!-- 实际图片 -->
          <img 
            v-show="!imageLoading"
            :src="imageUrl" 
            :alt="title"
            class="preview-image"
            @load="handleImageLoad"
            @error="handleImageError"
          />
        </div>
        
        <!-- 右侧反推面板 -->
        <div class="reverse-panel">
          <ImageReverse :image-url="imageUrl" @use-prompt="handleUsePrompt" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { CloseOutlined } from '@ant-design/icons-vue'
import ImageReverse from './ImageReverse.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  imageUrl: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: '图片预览'
  }
})

const emit = defineEmits(['update:visible', 'use-prompt'])

const imageLoading = ref(true)

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (newVal) {
    imageLoading.value = true
  }
})

// 处理图片加载完成
const handleImageLoad = () => {
  imageLoading.value = false
}

// 处理图片加载错误
const handleImageError = () => {
  imageLoading.value = false
  console.warn('预览图片加载失败:', props.imageUrl)
}

// 关闭模态框
const closeModal = () => {
  emit('update:visible', false)
}

// 处理使用提示词
const handleUsePrompt = (prompt) => {
  emit('use-prompt', prompt)
  closeModal() // 使用提示词后关闭弹窗
}

// ESC键关闭
const handleKeydown = (event) => {
  if (event.key === 'Escape' && props.visible) {
    closeModal()
  }
}

// 添加键盘事件监听
import { onMounted, onUnmounted } from 'vue'
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.image-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.image-preview-container {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-content {
  display: flex;
  gap: 20px;
  align-items: flex-start; /* 保持顶部对齐 */
  max-width: 100%;
  max-height: 100%;
}

.preview-image-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 60%;
  max-height: 80vh; /* 限制图片最大高度 */
}

.reverse-panel {
  width: 320px; /* 稍微增加宽度 */
  min-height: 400px; /* 改为最小高度 */
  max-height: 80vh; /* 设置最大高度，避免超出视窗 */
  background: #1a1a1a;
  border-radius: 8px;
  border: 1px solid #333;
  overflow: visible; /* 允许内容溢出显示 */
  display: flex;
  flex-direction: column;
}

.close-btn {
  position: absolute;
  top: -50px;
  right: 0;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.3s ease;
  z-index: 10;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.1);
}


.preview-image-skeleton {
  width: 400px;
  height: 400px;
  background: #2a2a2a;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.skeleton-shimmer {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    left: -100%;
  }
  100% {
    left: 100%;
  }
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .image-preview-overlay {
    padding: 10px;
  }
  
  .close-btn {
    top: -40px;
    width: 35px;
    height: 35px;
    font-size: 16px;
  }
  
  .preview-content {
    flex-direction: column;
    gap: 15px;
  }
  
  .preview-image-container {
    max-width: 100%;
  }
  
  .reverse-panel {
    width: 100%;
    height: 300px;
  }
  
  .preview-image-skeleton {
    width: 300px;
    height: 300px;
  }
}
</style>
