<template>
  <div class="history-panel">
    <div class="history-header">
      <h3>变更历史</h3>
      <div class="history-controls">
        <button 
          @click="undo" 
          :disabled="!canUndo"
          class="control-btn"
          title="撤销"
        >
          ↶
        </button>
        <button 
          @click="redo" 
          :disabled="!canRedo"
          class="control-btn"
          title="重做"
        >
          ↷
        </button>
      </div>
    </div>
    
    <div class="history-list">
      <div 
        v-for="(record, index) in historyRecords" 
        :key="record.id"
        :class="['history-item', { active: index === currentIndex }]"
        @click="switchToHistory(index)"
      >
        <div class="history-preview">
          <img :src="record.resultImageUrl" :alt="`历史记录 ${index + 1}`" />
        </div>
        <div class="history-info">
          <div class="history-prompt">{{ record.prompt }}</div>
          <div class="history-time">{{ formatTime(record.timestamp) }}</div>
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
import { ref, computed, watch } from 'vue'

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
    }
  },
  emits: ['update:modelValue', 'update:currentIndex', 'switch-history', 'undo', 'redo'],
  setup(props, { emit }) {
    const historyRecords = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })
    
    const canUndo = computed(() => props.currentIndex > 0)
    const canRedo = computed(() => props.currentIndex < historyRecords.value.length - 1)
    
    const switchToHistory = (index) => {
      emit('update:currentIndex', index)
      emit('switch-history', historyRecords.value[index])
    }
    
    const undo = () => {
      if (canUndo.value) {
        const newIndex = props.currentIndex - 1
        switchToHistory(newIndex)
        emit('undo')
      }
    }
    
    const redo = () => {
      if (canRedo.value) {
        const newIndex = props.currentIndex + 1
        switchToHistory(newIndex)
        emit('redo')
      }
    }
    
    const deleteHistory = (index) => {
      const newHistory = [...historyRecords.value]
      newHistory.splice(index, 1)
      
      // 调整当前索引
      let newCurrentIndex = props.currentIndex
      if (index < props.currentIndex) {
        newCurrentIndex = props.currentIndex - 1
      } else if (index === props.currentIndex) {
        newCurrentIndex = Math.max(0, props.currentIndex - 1)
      }
      
      emit('update:modelValue', newHistory)
      emit('update:currentIndex', newCurrentIndex)
    }
    
    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    }
    
    return {
      historyRecords,
      canUndo,
      canRedo,
      switchToHistory,
      undo,
      redo,
      deleteHistory,
      formatTime
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

.history-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color, #333);
}

.history-controls {
  display: flex;
  gap: 8px;
}

.control-btn {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border-color, #ddd);
  background: var(--button-bg, white);
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: var(--text-color, #666);
  transition: all 0.2s;
}

.control-btn:hover:not(:disabled) {
  background: var(--button-hover-bg, #f0f0f0);
  border-color: var(--border-hover-color, #999);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.history-time {
  font-size: 12px;
  color: var(--text-secondary, #666);
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
