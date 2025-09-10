<template>
  <div class="model-selector">
    <!-- 模型选择下拉菜单 -->
          <a-dropdown 
        :trigger="['click']" 
        placement="bottomLeft"
        @openChange="handleDropdownVisibleChange"
      >
      <div class="model-dropdown-trigger">
        <div class="model-trigger-content">
          <div class="model-trigger-icon">🤖</div>
          <div class="model-trigger-info">
            <div class="model-trigger-name">{{ currentModel.display_name || 'Qwen' }}</div>
          </div>
          <!-- 移除状态显示 -->
        </div>
        <div class="model-trigger-arrow">
          <DownOutlined />
        </div>
      </div>
      
      <template #overlay>
        <div class="model-dropdown-menu">
          <div class="model-dropdown-header">
            <span class="model-dropdown-title">选择基础模型</span>
            <a-button 
              type="link" 
              size="small" 
              @click="fetchModels"
              :loading="loading"
            >
              <template #icon>
                <ReloadOutlined />
              </template>
              刷新
            </a-button>
          </div>
          
          <div class="model-dropdown-list">
            <div 
              v-for="model in availableModels" 
              :key="model.name"
              class="model-dropdown-item"
              :class="{ 'model-dropdown-selected': model.name === currentModel.name }"
              @click="selectModel(model)"
            >
              <div class="model-dropdown-item-icon">
                <span class="model-icon">🤖</span>
              </div>
              <div class="model-dropdown-item-info">
                <div class="model-dropdown-item-name">{{ model.display_name }}</div>
                <div class="model-dropdown-item-desc">{{ getModelDescription(model.name) }}</div>
              </div>
              <div class="model-dropdown-item-status">
                <div v-if="model.name === currentModel.name" class="model-dropdown-selected-icon">
                  ✅
                </div>
              </div>
            </div>
            
            <div v-if="availableModels.length === 0" class="model-dropdown-empty">
              <a-empty description="没有可用的基础模型" size="small" />
            </div>
          </div>
        </div>
      </template>
    </a-dropdown>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined, DownOutlined } from '@ant-design/icons-vue'

// API基础URL
const API_BASE = (() => {
  if (import.meta.env.DEV) {
    return 'http://localhost:9000'
  }
  return import.meta.env.VITE_API_BASE_URL || ''
})()

// Props
const props = defineProps({
  model: {
    type: String,
    default: 'qwen-image'
  }
})

// Emits
const emit = defineEmits(['update:model'])

// 状态
const availableModels = ref([])
const loading = ref(false)

  // 当前选择的模型
  const currentModel = computed({
    get: () => {
      const model = availableModels.value.find(m => m.name === props.model)
      return model || {
        name: 'qwen-image',
        display_name: 'Qwen',
        description: 'Qwen支持中文较好，适合中文描述生成',
        available: true
      }
    },
    set: (value) => emit('update:model', value.name)
  })

// 获取可用模型列表
const fetchModels = async () => {
  try {
    loading.value = true
    const response = await fetch(`${API_BASE}/api/models`)
    if (response.ok) {
      const data = await response.json()
      availableModels.value = data.models || []
      console.log('🤖 获取到模型列表:', availableModels.value)
    } else {
      console.error('❌ 获取模型列表失败:', response.status)
      message.error('获取模型列表失败')
    }
  } catch (error) {
    console.error('❌ 获取模型列表出错:', error)
    message.error('获取模型列表出错')
  } finally {
    loading.value = false
  }
}

// 获取模型说明
const getModelDescription = (modelName) => {
  if (modelName.includes('flux')) {
    return 'Flux模型更精确控制，适合专业图像生成'
  } else if (modelName.includes('qwen')) {
    return 'Qwen支持中文较好，适合中文描述生成'
  }
  return 'AI图像生成模型'
}

// 选择模型
const selectModel = (model) => {
  emit('update:model', model.name)
  console.log('✅ 选择模型:', model.display_name)
  message.success(`已选择模型: ${model.display_name}`)
}

// 处理下拉菜单显示状态变化
const handleDropdownVisibleChange = (visible) => {
  if (visible && availableModels.value.length === 0) {
    fetchModels()
  }
}

// 组件挂载时加载模型列表
onMounted(() => {
  fetchModels()
})
</script>

<style scoped>
.model-selector {
  width: 100%;
}

.model-dropdown-trigger {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: #2a2a2a;
  border: 0px solid #444;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 36px;
}

.model-dropdown-trigger:hover {
  background: #3a3a3a;
  border-color: #555;
}

.model-trigger-content {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 6px;
}

.model-trigger-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.model-trigger-info {
  flex: 1;
  min-width: 0;
}

.model-trigger-name {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-trigger-status {
  flex-shrink: 0;
}

.model-trigger-arrow {
  color: #ccc;
  margin-left: 8px;
  transition: transform 0.2s;
}

.model-dropdown-trigger:hover .model-trigger-arrow {
  color: #fff;
}

/* 下拉菜单样式 */
.model-dropdown-menu {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  min-width: 320px;
  max-width: 400px;
}

.model-dropdown-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #444;
}

.model-dropdown-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.model-dropdown-list {
  max-height: 300px;
  overflow-y: auto;
}

.model-dropdown-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #333;
}

.model-dropdown-item:hover {
  background: #3a3a3a;
}

.model-dropdown-item:last-child {
  border-bottom: none;
}

.model-dropdown-item.model-dropdown-selected {
  background: #1890ff;
  color: #fff;
}

.model-dropdown-item-icon {
  position: relative;
  flex-shrink: 0;
  margin-right: 12px;
}

.model-icon {
  font-size: 24px;
}

.model-badge {
  position: absolute;
  top: -4px;
  right: -8px;
  background: #ff4d4f;
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 600;
}

.model-dropdown-item-info {
  flex: 1;
  min-width: 0;
}

  .model-dropdown-item-name {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
    color: #fff;
  }

  .model-dropdown-item-desc {
    font-size: 11px;
    color: #ccc;
    line-height: 1.3;
    margin-top: 2px;
  }

  .model-dropdown-item.model-dropdown-selected .model-dropdown-item-desc {
    color: rgba(255, 255, 255, 0.7);
  }

.model-dropdown-item-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  margin-left: 12px;
  flex-shrink: 0;
}

.model-dropdown-selected-icon {
  font-size: 16px;
}

.model-dropdown-empty {
  padding: 20px;
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .model-dropdown-menu {
    min-width: 280px;
  }
  
  .model-dropdown-item {
    flex-direction: column;
    gap: 8px;
  }
  
  .model-dropdown-item-status {
    align-items: flex-start;
    margin-left: 0;
  }
}
</style>
