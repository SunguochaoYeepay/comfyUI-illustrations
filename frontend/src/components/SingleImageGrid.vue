<template>
  <div class="single-image-grid">
    <!-- 网格容器 -->
    <div class="grid-container">
      <SingleImageCard
        v-for="(image, index) in images"
        :key="`${image.task_id}-${image.image_index || index}`"
        :image="image"
        @preview-image="$emit('previewImage', $event)"
        @toggle-favorite="$emit('toggleFavorite', $event)"
        @download-image="$emit('downloadImage', $event)"
      />
    </div>
    
    <!-- 空状态 -->
    <div v-if="images.length === 0" class="empty-state">
      <div class="empty-icon">🖼️</div>
      <div class="empty-text">暂无图片</div>
    </div>
  </div>
</template>

<script setup>
import SingleImageCard from './SingleImageCard.vue'

// Props
defineProps({
  images: {
    type: Array,
    default: () => []
  }
})

// Emits
defineEmits([
  'previewImage',
  'toggleFavorite',
  'downloadImage'
])
</script>

<style scoped>
.single-image-grid {
  width: 100%;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  padding: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.6);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 1.1rem;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .grid-container {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 12px;
    padding: 12px;
  }
}

@media (max-width: 480px) {
  .grid-container {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 8px;
    padding: 8px;
  }
}
</style>
