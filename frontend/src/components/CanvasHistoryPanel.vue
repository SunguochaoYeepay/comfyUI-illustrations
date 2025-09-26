<template>
  <div class="history-panel">
    <div class="history-header">
      <h3 class="history-title">变更历史</h3>
      <button class="close-btn" @click="$emit('close')" title="关闭">
        ×
      </button>
    </div>
    
    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      <div class="error-icon">⚠️</div>
      <div class="error-text">{{ error }}</div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <div class="loading-text">加载历史记录中...</div>
    </div>
    
    <div class="history-list" v-else>
      <div 
        v-for="(record, index) in historyRecords" 
        :key="record.id"
        :class="['history-item', { active: index === currentIndex, offline: record.offline }]"
        @click="switchToHistory(index)"
      >
        <div class="history-preview">
          <img :src="fixImageUrl(record.resultImageUrl)" :alt="`历史记录 ${index + 1}`" />
        </div>
        <div class="history-info">
          <div class="history-prompt">{{ record.prompt }}</div>
        </div>
        <div class="history-actions">
          <button 
            @click.stop="deleteHistory(index)"
            class="delete-btn"
            title="删除"
          >
            ×
          </button>
        </div>
      </div>
      
      <div v-if="historyRecords.length === 0" class="empty-history">
        <div class="empty-icon">📝</div>
        <div class="empty-text">暂无历史记录</div>
        <div class="empty-hint">开始局部重绘后，历史记录将显示在这里</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick } from 'vue'

export default {
  name: 'CanvasHistoryPanel',
  props: {
    modelValue: {
      type: Array,
      default: () => []
    },
    currentIndex: {
      type: Number,
      default: -1
    },
    isLoading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    },
    isOnline: {
      type: Boolean,
      default: true
    }
  },
  emits: ['update:modelValue', 'update:currentIndex', 'switch-history', 'undo', 'redo', 'delete-history', 'close'],
  setup(props, { emit }) {
    const historyRecords = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })
    
    
    // 修复图片URL，确保是完整的绝对路径
    const fixImageUrl = (url) => {
      if (!url) return url
      if (url.startsWith('/') && !url.startsWith('//')) {
        return window.location.origin + url
      }
      return url
    }
    
    const switchToHistory = (index) => {
      emit('update:currentIndex', index)
      emit('switch-history', historyRecords.value[index])
    }
    
    
    const deleteHistory = async (index) => {
      const record = historyRecords.value[index]
      if (!record) return
      
      try {
        // 发送删除事件给父组件
        await emit('delete-history', record.id)
        
        // 使用 nextTick 确保DOM更新完成后再进行数组操作
        await nextTick()
        
        // 从本地列表中移除 - 使用 filter 而不是 splice，更安全
        const newHistory = historyRecords.value.filter((_, i) => i !== index)
        
        // 调整当前索引
        let newCurrentIndex = props.currentIndex
        if (index < props.currentIndex) {
          newCurrentIndex = props.currentIndex - 1
        } else if (index === props.currentIndex) {
          newCurrentIndex = Math.max(0, props.currentIndex - 1)
        }
        
        // 使用 nextTick 确保状态更新完成
        await nextTick()
        emit('update:modelValue', newHistory)
        emit('update:currentIndex', newCurrentIndex)
      } catch (error) {
        console.error('删除历史记录失败:', error)
        // 可以在这里显示错误提示
      }
    }
    
    
    return {
      historyRecords,
      switchToHistory,
      deleteHistory,
      fixImageUrl
    }
  }
}
</script>

<style scoped>
.history-panel {
  position: fixed;
  top: 52px;
  right: 0;
  width: 220px;
  height: 100vh;
  background: var(--bg-color, #f8f9fa);
  border-left: 1px solid var(--border-color, #e9ecef);
  display: flex;
  flex-direction: column;
  z-index: 1000;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
}

.history-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color, #e9ecef);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg, rgba(255, 255, 255, 0.8));
  backdrop-filter: blur(10px);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-title {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color, #333);
}

.close-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--text-color, #666);
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--button-hover-bg, #f0f0f0);
  color: var(--text-color, #333);
}

.history-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}



.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: var(--item-bg, white);
  border: 1px solid var(--border-color, #e9ecef);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  border-color: var(--primary-color, #007bff);
  box-shadow: 0 2px 8px var(--primary-shadow, rgba(0, 123, 255, 0.1));
}

.history-item.active {
  border-color: var(--primary-color, #007bff);
  background: var(--active-bg, #f8f9ff);
}

.history-item.offline {
  border-color: #ffc107;
  background: #fff8e1;
}

.history-item.offline::after {
  content: '📱';
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 12px;
  background: #ffc107;
  color: #333;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-preview {
  width: 48px;
  height: 48px;
  margin-right: 12px;
  border-radius: 4px;
  overflow: hidden;
  flex-shrink: 0;
}

.history-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-prompt {
  font-size: 14px;
  color: var(--text-color, #333);
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}


.history-actions {
  margin-left: 8px;
}

.delete-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: #ff4757;
  color: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  line-height: 1;
  transition: all 0.2s;
}

.delete-btn:hover {
  background: #ff3742;
  transform: scale(1.1);
}

.empty-history {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-text {
  color: var(--text-color, #333);
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.empty-hint {
  color: var(--text-secondary, #666);
  font-size: 12px;
  line-height: 1.4;
  max-width: 200px;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  margin: 8px;
  background: #ffebee;
  border: 1px solid #ffcdd2;
  border-radius: 6px;
  color: #c62828;
}

.error-icon {
  font-size: 16px;
}

.error-text {
  font-size: 12px;
  flex: 1;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #e0e0e0;
  border-top: 2px solid var(--primary-color, #007bff);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  color: var(--text-secondary, #666);
  font-size: 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 暗色主题适配 */
@media (prefers-color-scheme: dark) {
  .history-panel {
    --bg-color: #1a1a1a;
    --border-color: #333;
    --header-bg: rgba(26, 26, 26, 0.9);
    --text-color: #e0e0e0;
    --text-secondary: #999;
    --button-bg: #2a2a2a;
    --button-hover-bg: #3a3a3a;
    --border-hover-color: #555;
    --item-bg: #2a2a2a;
    --primary-color: #4a9eff;
    --primary-shadow: rgba(74, 158, 255, 0.2);
    --active-bg: #1a2332;
  }
}

/* 自定义暗色主题变量 */
:root[data-theme="dark"] {
  --bg-color: #1a1a1a;
  --border-color: #333;
  --header-bg: rgba(26, 26, 26, 0.9);
  --text-color: #e0e0e0;
  --text-secondary: #999;
  --button-bg: #2a2a2a;
  --button-hover-bg: #3a3a3a;
  --border-hover-color: #555;
  --item-bg: #2a2a2a;
  --primary-color: #4a9eff;
  --primary-shadow: rgba(74, 158, 255, 0.2);
  --active-bg: #1a2332;
}
</style>
