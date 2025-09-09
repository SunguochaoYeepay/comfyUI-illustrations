<script setup>
import { ref } from 'vue'
import NavigationSidebar from './components/NavigationSidebar.vue'
import ImageGenerator from './components/ImageGenerator.vue'
import InspirationPage from './components/InspirationPage.vue'
import DetailModal from './components/DetailModal.vue'

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

const handleRemoveFavorite = (item) => {
  const favorites = JSON.parse(localStorage.getItem('favorites') || '[]')
  const updated = favorites.filter(fav => fav.id !== item.id)
  localStorage.setItem('favorites', JSON.stringify(updated))
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
        <ImageGenerator v-else />
      </div>
    </div>
    
    <DetailModal
      :open="detailModalOpen"
      :item="selectedItem"
      @update:open="detailModalOpen = $event"
      @remove-favorite="handleRemoveFavorite"
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
  margin-left: 60px;
}

/* 强制重置可能的全局样式 */
body > div:first-child {
  margin: 0 !important;
  padding: 0 !important;
  transform: none !important;
}
</style>
