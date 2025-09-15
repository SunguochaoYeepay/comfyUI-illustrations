<template>
  <div class="image-gen-config">
    <div class="header-bar">
      <h1>生图配置</h1>
      <div class="header-actions">
        <a-button type="primary" @click="saveConfig" :loading="saving">
          <save-outlined /> 保存配置
        </a-button>
      </div>
    </div>

    <a-card title="基础模型排序" class="config-card">
      <template #extra>
        <a-tooltip title="拖拽调整基础模型的显示顺序">
          <info-circle-outlined />
        </a-tooltip>
      </template>
      
      <div class="model-order-section">
        <p class="section-desc">调整基础模型在生图界面中的显示顺序</p>
        
        <div v-if="baseModels.length > 0">
          <draggable 
            v-model="config.base_model_order" 
            group="baseModels"
            item-key="model"
            :animation="200"
            :force-fallback="false"
            :fallback-tolerance="0"
            @start="onDragStart"
            @end="onDragEnd"
            class="draggable-list"
          >
            <template #item="{ element: model, index }">
              <div class="draggable-item">
                <div class="item-content">
                  <drag-outlined class="drag-handle" />
                  <span class="item-index">{{ index + 1 }}</span>
                  <span class="item-name">{{ getModelDisplayName(model) }}</span>
                  <a-tag :color="getModelStatus(model) ? 'green' : 'red'">
                    {{ getModelStatus(model) ? '可用' : '不可用' }}
                  </a-tag>
                </div>
              </div>
            </template>
          </draggable>
        </div>
        <div v-else class="loading-placeholder">
          <a-spin size="large" />
          <p>加载基础模型数据中...</p>
        </div>
      </div>
    </a-card>

    <a-card title="LoRA排序配置" class="config-card">
      <template #extra>
        <a-tooltip title="按基础模型分组，手工拖拽调整LoRA显示顺序">
          <info-circle-outlined />
        </a-tooltip>
      </template>
      
      <div class="lora-order-section">
        <p class="section-desc">按基础模型分组，手工拖拽调整LoRA在生图界面中的显示顺序</p>
        
        <div v-if="loraGroups.length > 0">
          <div 
            v-for="group in loraGroups" 
            :key="group.baseModel"
            class="lora-group"
          >
            <h4 class="group-title">
              <a-tag color="blue">{{ group.baseModel }}</a-tag>
              <span class="group-count">({{ group.loras.length }} 个LoRA)</span>
            </h4>
            
            <draggable 
              v-model="group.loras" 
              :group="`lora-${group.baseModel}`"
              item-key="name"
              :animation="200"
              :force-fallback="false"
              :fallback-tolerance="0"
              @start="onDragStart"
              @end="onDragEnd"
              class="lora-draggable-list"
            >
              <template #item="{ element: lora, index }">
                <div class="lora-draggable-item">
                  <div class="lora-item-content">
                    <drag-outlined class="drag-handle" />
                    <span class="lora-index">{{ index + 1 }}</span>
                    <span class="lora-name">{{ lora.display_name }}</span>
                    <a-tag size="small" color="green">{{ lora.name }}</a-tag>
                  </div>
                </div>
              </template>
            </draggable>
          </div>
        </div>
        <div v-else class="loading-placeholder">
          <a-spin size="large" />
          <p>加载LoRA数据中...</p>
        </div>
      </div>
    </a-card>

    <a-card title="生图尺寸配置" class="config-card">
      <template #extra>
        <a-tooltip title="配置默认生图尺寸和比例选项">
          <info-circle-outlined />
        </a-tooltip>
      </template>
      
      <div class="size-config-section">
        <p class="section-desc">设置默认生图尺寸和可用的比例选项</p>
        
        <a-form layout="vertical">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="默认尺寸">
                <a-row :gutter="8">
                  <a-col :span="12">
                    <a-input-number 
                      v-model:value="config.default_size.width"
                      placeholder="宽度"
                      :min="256"
                      :max="4096"
                      style="width: 100%"
                    />
                  </a-col>
                  <a-col :span="12">
                    <a-input-number 
                      v-model:value="config.default_size.height"
                      placeholder="高度"
                      :min="256"
                      :max="4096"
                      style="width: 100%"
                    />
                  </a-col>
                </a-row>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="比例锁定">
                <a-switch 
                  v-model:checked="sizeLocked"
                  @change="onSizeLockChange"
                />
                <span class="switch-label">锁定宽高比</span>
              </a-form-item>
            </a-col>
          </a-row>
          
          <a-form-item label="支持的图片比例">
            <div class="ratio-tags">
              <a-tag 
                v-for="ratio in config.size_ratios" 
                :key="ratio"
                :closable="config.size_ratios.length > 1"
                @close="removeRatio(ratio)"
                class="ratio-tag"
              >
                {{ ratio }}
              </a-tag>
              <a-input
                v-if="inputVisible"
                ref="inputRef"
                v-model:value="inputValue"
                type="text"
                size="small"
                style="width: 78px; margin-right: 8px; vertical-align: bottom;"
                @blur="handleInputConfirm"
                @keyup.enter="handleInputConfirm"
              />
              <a-tag v-else @click="showInput" style="background: #fff; border-style: dashed;">
                <plus-outlined /> 添加比例
              </a-tag>
            </div>
          </a-form-item>
        </a-form>
      </div>
    </a-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { message } from 'ant-design-vue'
import { SaveOutlined, InfoCircleOutlined, DragOutlined, PlusOutlined } from '@ant-design/icons-vue'
import draggable from 'vuedraggable'
import { getImageGenConfig, updateImageGenConfig, getBaseModelsForConfig, getLorasForConfig } from '@/api/imageGenConfig'

export default {
  name: 'ImageGenConfig',
  components: {
    SaveOutlined,
    InfoCircleOutlined,
    DragOutlined,
    PlusOutlined,
    draggable
  },
  setup() {
    const saving = ref(false)
    const sizeLocked = ref(true)
    const inputVisible = ref(false)
    const inputValue = ref('')
    const inputRef = ref(null)
    
    const config = ref({
      base_model_order: [],
      lora_order: {}, // 改为对象，按基础模型存储排序
      default_size: {
        width: 1024,
        height: 1024
      },
      size_ratios: ['1:1', '4:3', '3:4', '16:9', '9:16']
    })
    
    const baseModels = ref([])
    const loras = ref([])
    // 计算按基础模型分组的LoRA列表
    const loraGroups = computed(() => {
      if (!loras.value.length) return []
      
      // 按基础模型分组
      const groups = {}
      loras.value.forEach(lora => {
        if (!groups[lora.base_model]) {
          groups[lora.base_model] = []
        }
        groups[lora.base_model].push(lora)
      })
      
      // 转换为数组格式，并应用排序
      return Object.keys(groups).map(baseModel => {
        let sortedLoras = [...groups[baseModel]]
        
        // 如果有自定义排序，应用它
        if (config.value.lora_order[baseModel]) {
          const customOrder = config.value.lora_order[baseModel]
          sortedLoras.sort((a, b) => {
            const indexA = customOrder.indexOf(a.name)
            const indexB = customOrder.indexOf(b.name)
            if (indexA === -1 && indexB === -1) return 0
            if (indexA === -1) return 1
            if (indexB === -1) return -1
            return indexA - indexB
          })
        } else {
          // 默认按名称排序
          sortedLoras.sort((a, b) => a.display_name.localeCompare(b.display_name))
        }
        
        return {
          baseModel,
          loras: sortedLoras
        }
      })
    })
    
    // 获取模型显示名称
    const getModelDisplayName = (modelName) => {
      try {
        const model = baseModels.value.find(m => m.name === modelName)
        return model ? model.display_name : modelName
      } catch (error) {
        console.warn('获取模型显示名称失败:', error)
        return modelName
      }
    }
    
    // 获取模型状态
    const getModelStatus = (modelName) => {
      try {
        const model = baseModels.value.find(m => m.name === modelName)
        return model ? model.available : false
      } catch (error) {
        console.warn('获取模型状态失败:', error)
        return false
      }
    }
    
    // 拖拽开始
    const onDragStart = () => {
      console.log('开始拖拽')
    }
    
    // 拖拽结束
    const onDragEnd = (evt) => {
      try {
        console.log('拖拽结束', evt)
        
        // 如果是LoRA拖拽，更新排序
        if (evt.to && evt.to.classList.contains('lora-draggable-list')) {
          const groupElement = evt.to.closest('.lora-group')
          if (groupElement) {
            const baseModelTag = groupElement.querySelector('.group-title .ant-tag')
            if (baseModelTag) {
              const baseModel = baseModelTag.textContent
              const newOrder = Array.from(evt.to.children).map(item => {
                const nameTag = item.querySelector('.ant-tag')
                return nameTag ? nameTag.textContent : null
              }).filter(Boolean)
              
              // 更新配置
              if (!config.value.lora_order) {
                config.value.lora_order = {}
              }
              config.value.lora_order[baseModel] = newOrder
              
              console.log(`更新${baseModel}的LoRA排序:`, newOrder)
            }
          }
        }
      } catch (error) {
        console.warn('拖拽结束处理出错:', error)
      }
    }
    
    
    // 尺寸锁定变化
    const onSizeLockChange = (checked) => {
      if (checked) {
        // 锁定比例，保持当前比例
        const ratio = config.default_size.width / config.default_size.height
        // 可以在这里添加比例锁定逻辑
      }
    }
    
    // 显示输入框
    const showInput = () => {
      inputVisible.value = true
      nextTick(() => {
        inputRef.value?.focus()
      })
    }
    
    // 确认输入
    const handleInputConfirm = () => {
      if (inputValue.value && !config.value.size_ratios.includes(inputValue.value)) {
        config.value.size_ratios.push(inputValue.value)
      }
      inputVisible.value = false
      inputValue.value = ''
    }
    
    // 移除比例
    const removeRatio = (ratio) => {
      const index = config.value.size_ratios.indexOf(ratio)
      if (index > -1) {
        config.value.size_ratios.splice(index, 1)
      }
    }
    
    // 加载配置
    const loadConfig = async () => {
      try {
        const [configData, baseModelsData, lorasData] = await Promise.all([
          getImageGenConfig(),
          getBaseModelsForConfig(),
          getLorasForConfig()
        ])
        
        // 先设置基础数据
        baseModels.value = baseModelsData.models || []
        loras.value = lorasData.loras || []
        
        // 使用setTimeout确保在下一个事件循环中设置配置数据
        setTimeout(() => {
          try {
            // 创建新的配置对象，避免直接修改响应式数据
            const newConfig = {
              base_model_order: [...(configData.base_model_order || [])],
              lora_order: configData.lora_order || {},
              default_size: { ...(configData.default_size || { width: 1024, height: 1024 }) },
              size_ratios: [...(configData.size_ratios || ['1:1', '4:3', '3:4', '16:9', '9:16'])]
            }
            
            // 一次性更新整个配置对象
            config.value = newConfig
            
            message.success('配置加载成功')
          } catch (error) {
            console.error('设置配置数据失败:', error)
            message.error('设置配置数据失败')
          }
        }, 100)
        
      } catch (error) {
        console.error('加载配置失败:', error)
        message.error('加载配置失败')
      }
    }
    
    // 保存配置
    const saveConfig = async () => {
      try {
        saving.value = true
        
        await updateImageGenConfig({
          base_model_order: config.value.base_model_order,
          lora_order: config.value.lora_order,
          default_size: config.value.default_size,
          size_ratios: config.value.size_ratios
        })
        
        message.success('配置保存成功')
      } catch (error) {
        console.error('保存配置失败:', error)
        message.error('保存配置失败')
      } finally {
        saving.value = false
      }
    }
    
    // 监听基础模型数据变化，确保draggable组件能正确处理
    watch(() => baseModels.value, (newVal) => {
      if (newVal.length > 0) {
        console.log('基础模型数据已加载:', newVal.length)
      }
    }, { immediate: true })
    
    // 监听LoRA数据变化
    watch(() => loras.value, (newVal) => {
      if (newVal.length > 0) {
        console.log('LoRA数据已加载:', newVal.length)
      }
    }, { immediate: true })
    
    onMounted(() => {
      loadConfig()
    })
    
      return {
        saving,
        sizeLocked,
        inputVisible,
        inputValue,
        inputRef,
        config,
        baseModels,
        loras,
        loraGroups,
        getModelDisplayName,
        getModelStatus,
        onDragStart,
        onDragEnd,
        onSizeLockChange,
        showInput,
        handleInputConfirm,
        removeRatio,
        saveConfig
      }
  }
}
</script>

<style scoped>
.image-gen-config {
  padding: 24px;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-bar h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.config-card {
  margin-bottom: 24px;
}

.section-desc {
  color: rgba(255, 255, 255, 0.65);
  margin-bottom: 16px;
  font-size: 14px;
}

/* 基础模型排序样式 */
.draggable-list {
  min-height: 100px;
}

.draggable-item {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: move;
  transition: all 0.3s;
}

.draggable-item:hover {
  border-color: #40a9ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.08);
}

.item-content {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
}

.drag-handle {
  color: rgba(255, 255, 255, 0.45);
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}

.item-index {
  background: #1890ff;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.item-name {
  flex: 1;
  font-weight: 500;
}

/* LoRA排序样式 */
.preview-section {
  margin-top: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 6px;
}

.preview-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
}

.lora-preview-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  gap: 12px;
}

.lora-preview-item:last-child {
  border-bottom: none;
}

.preview-index {
  background: #52c41a;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
}

.preview-name {
  flex: 1;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
}

.more-items {
  text-align: center;
  color: rgba(255, 255, 255, 0.45);
  font-size: 12px;
  padding: 8px 0;
}

/* 尺寸配置样式 */
.switch-label {
  margin-left: 8px;
  color: rgba(255, 255, 255, 0.65);
}

.ratio-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.ratio-tag {
  margin: 0;
}

/* 加载占位符样式 */
.loading-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.45);
}

.loading-placeholder p {
  margin-top: 16px;
  margin-bottom: 0;
}

/* LoRA分组样式 */
.lora-group {
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.04);
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.group-count {
  color: rgba(255, 255, 255, 0.65);
  font-size: 14px;
  font-weight: normal;
}

.lora-draggable-list {
  min-height: 60px;
}

.lora-draggable-item {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: move;
  transition: all 0.3s;
}

.lora-draggable-item:hover {
  border-color: #40a9ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.12);
}

.lora-item-content {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
}

.lora-index {
  background: #52c41a;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.lora-name {
  flex: 1;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
}
</style>
