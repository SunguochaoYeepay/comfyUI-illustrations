<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import NavigationSidebar from './components/NavigationSidebar.vue'
import ImageGenerator from './components/ImageGenerator.vue'
import InspirationPage from './components/InspirationPage.vue'
import DetailModal from './components/DetailModal.vue'
import CanvasDemo from './components/CanvasDemo.vue'

const activeTab = ref('generate')
const detailModalOpen = ref(false)
const selectedItem = ref(null)

const handleTabChange = (tab) => {
  activeTab.value = tab
}

const handleShowDetail = (item) => {
  selectedItem.value = item
  detailModalOpen.value = true
}

const handleRemoveFavorite = async (item) => {
  try {
    const API_BASE = import.meta.env.DEV ? (import.meta.env.VITE_BACKEND_URL || 'http://localhost:9000') : ''
    
    console.log('🗑️ 取消收藏项目:', item)
    console.log('🗑️ 项目类型:', item.type)
    console.log('🗑️ 任务ID:', item.task_id)
    console.log('🗑️ 图片索引:', item.image_index)
    
    if (item.type === 'video') {
      // 取消视频收藏
      console.log('🗑️ 取消视频收藏:', `${API_BASE}/api/favorites/videos/${item.task_id}`)
      const response = await fetch(`${API_BASE}/api/favorites/videos/${item.task_id}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        const errorText = await response.text()
        console.error('取消视频收藏失败:', response.status, errorText)
        throw new Error(`取消视频收藏失败: ${response.status}`)
      }
    } else {
      // 取消图片收藏
      console.log('🗑️ 取消图片收藏:', `${API_BASE}/api/favorites/images/${item.task_id}/${item.image_index}`)
      const response = await fetch(`${API_BASE}/api/favorites/images/${item.task_id}/${item.image_index}`, {
        method: 'DELETE'
      })
      if (!response.ok) {
        const errorText = await response.text()
        console.error('取消图片收藏失败:', response.status, errorText)
        throw new Error(`取消图片收藏失败: ${response.status}`)
      }
    }
    
    // 重新加载收藏列表
    window.dispatchEvent(new CustomEvent('refresh-favorites'))
    
  } catch (error) {
    console.error('取消收藏失败:', error)
    message.error(`取消收藏失败: ${error.message}`)
  }
}

const handleRegenerate = (regenerateData) => {
  console.log('处理再次生成:', regenerateData)
  
  // 切换到生图标签
  activeTab.value = 'generate'
  
  // 将回填数据存储到localStorage，供ImageGenerator组件使用
  localStorage.setItem('regenerateData', JSON.stringify(regenerateData))
  
  // 显示提示信息
  setTimeout(() => {
    // 这里可以添加一个提示，告诉用户参数已回填
    console.log('参数已回填到生图页面')
  }, 100)
}
</script>

<template>
  <div id="app">
    <div class="app-layout">
      <NavigationSidebar @tab-change="handleTabChange" />
      
      <div class="main-content">
        <InspirationPage 
          v-if="activeTab === 'inspiration'"
          @show-detail="handleShowDetail"
        />
        <CanvasDemo 
          v-else-if="activeTab === 'canvas'"
        />
        <ImageGenerator v-else />
      </div>
    </div>
    
    <DetailModal
      :open="detailModalOpen"
      :item="selectedItem"
      @update:open="detailModalOpen = $event"
      @remove-favorite="handleRemoveFavorite"
      @regenerate="handleRegenerate"
    />
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  margin: 0 !important;
  padding: 0 !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  overflow-x: hidden;
  height: auto !important;
  min-height: 100vh;
}

#app {
  min-height: 100vh;
  margin: 0 !important;
  padding: 0 !important;
}

.app-layout {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  background: #0f0f0f;
  margin-left: 0px;
}

/* 强制重置可能的全局样式 */
body > div:first-child {
  margin: 0 !important;
  padding: 0 !important;
  transform: none !important;
}
</style>
