<template>
  <div class="parameter-panel">
    <div class="panel-content">
      <div class="prompt-row">
        <input
          v-model="localPrompt"
          class="prompt-input"
          placeholder="描述想要扩展的内容,不填将基于原图生成"
          @input="updatePrompt"
          @keydown="handleKeydown"
        />
        <button 
          class="generate-btn"
          :disabled="!canExecute"
          @click="handleExecute"
        >
          <span class="btn-text">扩图</span>
          
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'

export default {
  name: 'OutpaintingParameterPanel',
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
    
    // 计算属性 - 扩图不需要强制要求提示词
    const canExecute = computed(() => {
      return true // 扩图功能总是可以执行，即使没有提示词
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
      emit('execute') // 扩图功能总是可以执行
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
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #2a2a2a;
  border-top: 1px solid #333;
  color: white;
  z-index: 1000;
  backdrop-filter: blur(10px);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
}

.panel-content {
  padding: 8px 12px;
  max-width: 800px;
  margin: 0 auto;
}

.prompt-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prompt-input {
  flex: 1;
  padding: 8px 12px;
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 4px;
  color: white;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.prompt-input:focus {
  border-color: #00ff88;
}

.prompt-input::placeholder {
  color: #666;
}

.generate-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #00ff88, #00cc6a);
  border: none;
  border-radius: 4px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.generate-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #00cc6a, #00aa55);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 255, 136, 0.3);
}

.generate-btn:disabled {
  background: #444;
  color: #666;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-text {
  font-weight: 500;
}

.btn-number {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}
</style>
