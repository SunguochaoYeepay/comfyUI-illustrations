<template>
  <div class="control-section">
    <a-card class="control-card">
      <div class="control-layout">
        <!-- 主要输入区域 -->
        <div class="main-input-row">
          <!-- 参考图片区域 -->
          <div class="reference-section">
            <ReferenceUpload
              v-model:file-list="localReferenceImages"
              @preview="$emit('preview', $event)"
            />
          </div>

          <!-- 提示词和生成按钮区域 -->
          <div class="input-group">
            <div class="prompt-generate-row">
              <a-textarea
                v-model:value="localPrompt"
                placeholder="请详细描述您想要生成的图像，例如：一只可爱的橙色小猫坐在花园里，阳光明媚，高清摄影风格"
                :rows="2"
                class="prompt-input"
              />
              
              <a-button
                type="primary"
                size="large"
                :loading="isGenerating"
                @click="handleGenerate"
                class="generate-btn"
              >
                <template #icon>
                  <span v-if="!isGenerating">✨</span>
                </template>
                {{ isGenerating ? '生成中...' : '生成' }}
              </a-button>
            </div>
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import ReferenceUpload from './ReferenceUpload.vue'

// Props
const props = defineProps({
  prompt: {
    type: String,
    default: ''
  },
  referenceImages: {
    type: Array,
    default: () => []
  },
  isGenerating: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits([
  'update:prompt',
  'update:referenceImages',
  'generate',
  'preview'
])

// 双向绑定的计算属性
const localPrompt = computed({
  get: () => props.prompt,
  set: (value) => emit('update:prompt', value)
})

const localReferenceImages = computed({
  get: () => props.referenceImages,
  set: (value) => emit('update:referenceImages', value)
})

// 处理生成按钮点击
const handleGenerate = () => {
  emit('generate')
}
</script>

<style scoped>
.control-section {
  position: fixed;
  bottom: 0px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  padding: 10px;
  max-width: 800px;
  width: 90%;
}

.control-card {
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  background: #1a1a1a;
  border: 1px solid #333;
}

.control-card :deep(.ant-card-body) {
  background: #1a1a1a;
  color: #fff;
}

.control-card :deep(.ant-card-head) {
  background: #1a1a1a;
  border-bottom: 1px solid #333;
}

.control-card :deep(.ant-card-head-title) {
  color: #fff;
}

.control-layout {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0 auto;
}

.main-input-row {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.reference-section {
  flex-shrink: 0;
}

.input-group {
  flex: 1;
  min-width: 0;
}

.prompt-generate-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.prompt-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #fff;
  resize: none;
}

.prompt-input:deep(.ant-input) {
  background: transparent;
  border: none;
  color: #fff;
  padding: 12px;
}

.prompt-input:deep(.ant-input::placeholder) {
  color: rgba(255, 255, 255, 0.5);
}

.prompt-input:focus,
.prompt-input:deep(.ant-input:focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.generate-btn {
  height: auto;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
  min-width: 100px;
}

.generate-btn:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.generate-btn:active {
  transform: translateY(0);
}

.generate-btn:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  transform: none;
  box-shadow: none;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .control-section {
    left: 5%;
    right: 5%;
    max-width: 90%;
  }
  
  .main-input-row {
    flex-direction: column;
    gap: 12px;
  }
  
  .prompt-generate-row {
    flex-direction: column;
    gap: 8px;
  }
  
  .generate-btn {
    width: 100%;
  }
}
</style>