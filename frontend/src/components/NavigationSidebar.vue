<template>
  <div class="navigation-sidebar">
    <div class="nav-items">
      <div 
        class="nav-item" 
        :class="{ active: activeTab === 'inspiration' }"
        @click="setActiveTab('inspiration')"
      >
        <div class="nav-icon">
          <StarOutlined />
        </div>
        <span class="nav-label">灵感</span>
      </div>
      
      <div 
        class="nav-item" 
        :class="{ active: activeTab === 'generate' }"
        @click="setActiveTab('generate')"
      >
        <div class="nav-icon">
          <PictureOutlined />
        </div>
        <span class="nav-label">生图</span>
      </div>
      
      <div 
        class="nav-item" 
        :class="{ active: activeTab === 'canvas' }"
        @click="setActiveTab('canvas')"
      >
        <div class="nav-icon">
          <EditOutlined />
        </div>
        <span class="nav-label">画布</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { StarOutlined, PictureOutlined, EditOutlined } from '@ant-design/icons-vue'

const emit = defineEmits(['tab-change'])

const activeTab = ref('generate')

const setActiveTab = (tab) => {
  activeTab.value = tab
  emit('tab-change', tab)
}
</script>

<style scoped>
.navigation-sidebar {
  width: 60px;
  height: 80vh;
  background: #1a1a1a;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1000;
}

.nav-items {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 56px;
}

.nav-item:hover {
  background: #2a2a2a;
}

.nav-item.active .nav-icon,.nav-item.active .nav-label{
  color: #667eea;
}

.nav-icon {
  font-size: 20px;
  color: #fff;
  margin-bottom: 4px;
}

.nav-label {
  font-size: 12px;
  color: #fff;
  text-align: center;
}
</style>
