<template>
  <div class="parameter-panel">
    <div class="panel-content">
      <div class="prompt-row">
        <input
          v-model="localPrompt"
          class="prompt-input"
          placeholder="描述想要重新绘制的内容,不填将基于原图生成"
          @input="updatePrompt"
          @keydown="handleKeydown"
        />
        <button 
          class="generate-btn"
          :disabled="!canExecute"
          @click="handleExecute"
        >
          <span class="btn-text">局部重绘</span>
          <span class="btn-number">1</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'

export default {
  name: 'CanvasParameterPanel',
  props: {
    prompt: {
      type: String,
      default: ''
    }
  },
  emits: ['update:prompt', 'execute'],
  setup(props, { emit }) {
    // 本地数据
    const localPrompt = ref(props.prompt)
    
    // 计算属性
    const canExecute = computed(() => {
      return localPrompt.value.trim().length > 0
    })
    
    // 更新方法
    const updatePrompt = () => {
      emit('update:prompt', localPrompt.value)
    }
    
    // 处理键盘事件
    const handleKeydown = (e) => {
      // Enter 执行
      if (e.key === 'Enter') {
        e.preventDefault()
        handleExecute()
      }
    }
    
    
    // 执行
    const handleExecute = () => {
      if (canExecute.value) {
        emit('execute')
      }
    }
    
    // 监听props变化
    watch(() => props.prompt, (newVal) => {
      localPrompt.value = newVal
    })
    
    return {
      localPrompt,
      canExecute,
      updatePrompt,
      handleKeydown,
      handleExecute
    }
  }
}
</script>

<style scoped>
.parameter-panel {
  background: #2a2a2a;
  border-top: 1px solid #333;
  color: white;
  max-width: 800px;
  margin: 0 auto;
}

.panel-content {
  padding: 8px 12px;
  max-height: 52px;
  overflow: hidden;
}

/* 提示词行布局 */
.prompt-row {
  display: flex;
  gap: 12px;
  align-items: center;
  height: 36px;
  max-width: 800px; /* 限制最大宽度 */
  margin: 0 auto; /* 居中显示 */
}

.prompt-input {
  flex: 1;
  min-width: 400px; /* 设置最小宽度 */
  height: 36px;
  padding: 0 16px; /* 增加内边距 */
  border: none;
  border-radius: 6px; /* 稍微增加圆角 */
  background: #2a2a2a;
  color: #fff;
  font-size: 14px; /* 稍微增加字体大小 */
  font-family: inherit;
  transition: background-color 0.2s ease;
}

.prompt-input:focus {
  outline: none;
  background: #333;
}

.prompt-input::placeholder {
  color: #888;
  font-size: 14px; /* 与输入框字体大小保持一致 */
}

.generate-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 16px; /* 增加内边距 */
  border: none;
  border-radius: 6px; /* 与输入框保持一致 */
  background: #007bff;
  color: white;
  font-size: 14px; /* 与输入框保持一致 */
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-width: 120px; /* 设置按钮最小宽度 */
}

.generate-btn:hover:not(:disabled) {
  background: #0056b3;
}

.generate-btn:disabled {
  background: #444;
  color: #666;
  cursor: not-allowed;
}

.btn-text {
  font-size: 13px;
}

.btn-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  font-size: 11px;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .parameter-panel {
    max-width: 100%;
  }
  
  .panel-content {
    padding: 6px 8px;
  }
  
  .prompt-row {
    gap: 16px;
    height: 32px;
  }
  
  .prompt-input {
    height: 32px;
    font-size: 12px;
  }
  
  .generate-btn {
    height: 32px;
    padding: 0 8px;
    font-size: 12px;
  }
  
  .btn-text {
    display: none;
  }
  
  .btn-number {
    width: 16px;
    height: 16px;
    font-size: 10px;
  }
}
</style>
