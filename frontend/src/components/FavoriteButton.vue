<template>
  <div class="favorite-button" @click="toggleFavorite">
    <HeartFilled v-if="isFavorited" class="favorited" />
    <HeartOutlined v-else class="not-favorited" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { HeartFilled, HeartOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['favorite-changed'])

const isFavorited = ref(false)

const checkFavoriteStatus = () => {
  const favorites = JSON.parse(localStorage.getItem('favorites') || '[]')
  isFavorited.value = favorites.some(fav => fav.id === props.item.id)
}

const toggleFavorite = () => {
  const favorites = JSON.parse(localStorage.getItem('favorites') || '[]')
  
  if (isFavorited.value) {
    // 取消收藏
    const updated = favorites.filter(fav => fav.id !== props.item.id)
    localStorage.setItem('favorites', JSON.stringify(updated))
    isFavorited.value = false
    message.success('已取消收藏')
  } else {
    // 添加收藏
    const favoriteItem = {
      id: props.item.id,
      title: props.item.title || '未命名作品',
      description: props.item.description || '暂无描述',
      imageUrl: props.item.imageUrl,
      prompt: props.item.prompt,
      parameters: props.item.parameters,
      createdAt: new Date().toISOString()
    }
    
    favorites.push(favoriteItem)
    localStorage.setItem('favorites', JSON.stringify(favorites))
    isFavorited.value = true
    message.success('已添加到收藏')
  }
  
  emit('favorite-changed', isFavorited.value)
}

watch(() => props.item, () => {
  checkFavoriteStatus()
}, { immediate: true })
</script>

<style scoped>
.favorite-button {
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.favorite-button:hover {
  background: rgba(255, 255, 255, 0.1);
}

.favorited {
  color: #ff4757;
  font-size: 18px;
}

.not-favorited {
  color: #888;
  font-size: 18px;
}

.favorite-button:hover .not-favorited {
  color: #ff4757;
}
</style>
