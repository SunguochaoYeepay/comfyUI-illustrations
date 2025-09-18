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
        
        <div v-if="loraGroupsReactive.length > 0">
          <a-tabs 
            v-model:activeKey="activeLoraTab" 
            type="card"
            class="lora-tabs"
            :tabBarStyle="{ marginBottom: '16px' }"
          >
            <a-tab-pane 
              v-for="group in loraGroupsReactive" 
              :key="group.baseModel"
              :tab="`${group.baseModel} (${group.loras.length})`"
            >
              <div class="lora-group">
                <div class="group-header">
                  <h4 class="group-title">
                    <a-tag color="blue">{{ group.baseModel }}</a-tag>
                    <span class="group-count">{{ group.loras.length }} 个LoRA</span>
                  </h4>
                  <p class="group-desc">拖拽调整LoRA的显示顺序</p>
                </div>
                
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
            </a-tab-pane>
          </a-tabs>
        </div>
        <div v-else class="loading-placeholder">
          <a-spin size="large" />
          <p>加载LoRA数据中...</p>
        </div>
      </div>
    </a-card>


    <a-card title="生图尺寸配置" class="config-card">
      <template #extra>
        <a-tooltip title="配置图片比例选项，支持拖拽排序和像素设置">
          <info-circle-outlined />
        </a-tooltip>
      </template>
      
      <div class="size-config-section">
        <p class="section-desc">配置图片比例选项，第一个比例将作为默认比例。拖拽调整排序，点击编辑设置具体像素值。</p>
        
        <div class="size-ratios-config">
          <div class="ratios-header">
            <span class="header-title">图片比例配置</span>
            <a-button type="primary" size="small" @click="addNewRatio">
              <plus-outlined /> 添加比例
            </a-button>
          </div>
          
          <draggable 
            v-model="sizeRatiosConfig" 
            group="sizeRatios"
            item-key="id"
            :animation="200"
            :force-fallback="false"
            :fallback-tolerance="0"
            @start="onDragStart"
            @end="onSizeRatioDragEnd"
            class="size-ratios-list"
          >
            <template #item="{ element: ratio, index }">
              <div class="size-ratio-item" :class="{ 'is-default': index === 0 }">
                <div class="ratio-drag-handle">
                  <drag-outlined class="drag-icon" />
                  <span class="ratio-index">{{ index + 1 }}</span>
                </div>
                
                <div class="ratio-content">
                  <div class="ratio-info">
                    <div class="ratio-name">
                      <span class="ratio-label">{{ ratio.ratio }}</span>
                      <a-tag v-if="index === 0" color="green" size="small">默认</a-tag>
                    </div>
                    <div class="ratio-pixels">
                      <span class="pixel-info">{{ ratio.width }} × {{ ratio.height }}</span>
                    </div>
                  </div>
                  
                  <div class="ratio-actions">
                    <a-button 
                      type="text" 
                      size="small" 
                      @click="editRatio(ratio)"
                      class="edit-btn"
                    >
                      编辑
                    </a-button>
                    <a-button 
                      type="text" 
                      size="small" 
                      danger
                      @click="removeRatio(ratio)"
                      :disabled="sizeRatiosConfig.length <= 1"
                      class="remove-btn"
                    >
                      删除
                    </a-button>
                  </div>
                </div>
              </div>
            </template>
          </draggable>
        </div>
      </div>
    </a-card>

    <!-- 比例编辑模态框 -->
    <a-modal
      v-model:open="ratioEditModalOpen"
      title="编辑图片比例"
      @ok="saveRatioEdit"
      @cancel="cancelRatioEdit"
      :confirm-loading="ratioEditLoading"
    >
      <a-form :model="editingRatio" layout="vertical">
        <a-form-item label="比例名称" required>
          <a-input v-model:value="editingRatio.ratio" placeholder="如: 1:1, 4:3, 16:9" />
        </a-form-item>
        <a-form-item label="像素尺寸" required>
          <a-row :gutter="8">
            <a-col :span="12">
              <a-input-number 
                v-model:value="editingRatio.width"
                placeholder="宽度"
                :min="64"
                :max="4096"
                style="width: 100%"
              />
            </a-col>
            <a-col :span="12">
              <a-input-number 
                v-model:value="editingRatio.height"
                placeholder="高度"
                :min="64"
                :max="4096"
                style="width: 100%"
              />
            </a-col>
          </a-row>
        </a-form-item>
        <a-form-item label="描述">
          <a-input v-model:value="editingRatio.description" placeholder="可选：比例描述" />
        </a-form-item>
      </a-form>
    </a-modal>
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
    const activeLoraTab = ref('')
    
    // 尺寸比例配置相关
    const sizeRatiosConfig = ref([])
    const ratioEditModalOpen = ref(false)
    const ratioEditLoading = ref(false)
    const editingRatio = ref({})
    const editingRatioIndex = ref(-1)
    
    const config = ref({
      base_model_order: [],
      lora_order: {}, // 改为对象，按基础模型存储排序
      default_size: {
        width: 1024,
        height: 1024
      }
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
            const indexA = customOrder.indexOf(a.code || a.name)
            const indexB = customOrder.indexOf(b.code || b.name)
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
    
    // 响应式的LoRA组数据，用于拖拽
    const loraGroupsReactive = ref([])
    
    // 监听loraGroups变化，更新响应式数据
    watch(loraGroups, (newGroups) => {
      loraGroupsReactive.value = newGroups.map(group => ({
        baseModel: group.baseModel,
        loras: [...group.loras] // 创建副本，避免直接修改计算属性
      }))
    }, { immediate: true, deep: true })

    
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
              
              // 找到对应的组，获取更新后的LoRA顺序
              const group = loraGroupsReactive.value.find(g => g.baseModel === baseModel)
              if (group) {
                const newOrder = group.loras.map(lora => lora.code || lora.name)
                
                // 更新配置
                if (!config.value.lora_order) {
                  config.value.lora_order = {}
                }
                config.value.lora_order[baseModel] = newOrder
                
                console.log(`更新${baseModel}的LoRA排序:`, newOrder)
              }
            }
          }
        }
      } catch (error) {
        console.warn('拖拽结束处理出错:', error)
      }
    }
    
    // 尺寸比例拖拽结束
    const onSizeRatioDragEnd = (evt) => {
      try {
        console.log('尺寸比例拖拽结束', evt)
        // 拖拽后自动更新配置，第一个比例作为默认
        updateSizeRatiosConfig()
      } catch (error) {
        console.warn('尺寸比例拖拽结束处理出错:', error)
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
    
    // 初始化尺寸比例配置
    const initSizeRatiosConfig = (sizeRatios) => {
      const defaultSizes = {
        '1:1': { width: 1024, height: 1024 },
        '4:3': { width: 1024, height: 768 },
        '3:4': { width: 768, height: 1024 },
        '16:9': { width: 1024, height: 576 },
        '9:16': { width: 576, height: 1024 },
        '21:9': { width: 1024, height: 439 },
        '3:2': { width: 1024, height: 683 },
        '2:3': { width: 683, height: 1024 }
      }
      
      // 检查sizeRatios的格式
      if (sizeRatios && sizeRatios.length > 0) {
        if (typeof sizeRatios[0] === 'object' && sizeRatios[0].ratio) {
          // 新格式：已经是对象数组，包含ratio, width, height等字段
          sizeRatiosConfig.value = sizeRatios.map((ratio, index) => ({
            id: Date.now() + index,
            ratio: ratio.ratio,
            width: ratio.width || 1024,
            height: ratio.height || 1024,
            description: ratio.description || ''
          }))
        } else {
          // 旧格式：字符串数组，需要根据比例设置默认尺寸
          sizeRatiosConfig.value = sizeRatios.map((ratio, index) => ({
            id: Date.now() + index,
            ratio: ratio,
            width: defaultSizes[ratio]?.width || 1024,
            height: defaultSizes[ratio]?.height || 1024,
            description: ''
          }))
        }
      } else {
        // 默认配置
        sizeRatiosConfig.value = [
          { id: Date.now(), ratio: '1:1', width: 1024, height: 1024, description: '' },
          { id: Date.now() + 1, ratio: '4:3', width: 1024, height: 768, description: '' },
          { id: Date.now() + 2, ratio: '3:4', width: 768, height: 1024, description: '' },
          { id: Date.now() + 3, ratio: '16:9', width: 1024, height: 576, description: '' },
          { id: Date.now() + 4, ratio: '9:16', width: 576, height: 1024, description: '' }
        ]
      }
      
      // 更新配置
      updateSizeRatiosConfig()
    }
    
    // 更新尺寸比例配置
    const updateSizeRatiosConfig = () => {
      // 将sizeRatiosConfig转换为size_ratios格式，保留所有字段
      config.value.size_ratios = sizeRatiosConfig.value.map(ratio => ({
        ratio: ratio.ratio,
        width: ratio.width,
        height: ratio.height,
        description: ratio.description || ''
      }))
      
      // 更新默认尺寸为第一个比例
      if (sizeRatiosConfig.value.length > 0) {
        const defaultRatio = sizeRatiosConfig.value[0]
        config.value.default_size.width = defaultRatio.width
        config.value.default_size.height = defaultRatio.height
      }
    }
    
    // 添加新比例
    const addNewRatio = () => {
      const newRatio = {
        id: Date.now(),
        ratio: '1:1',
        width: 1024,
        height: 1024,
        description: ''
      }
      editingRatio.value = { ...newRatio }
      editingRatioIndex.value = -1
      ratioEditModalOpen.value = true
    }
    
    // 编辑比例
    const editRatio = (ratio) => {
      editingRatio.value = { ...ratio }
      editingRatioIndex.value = sizeRatiosConfig.value.findIndex(r => r.id === ratio.id)
      ratioEditModalOpen.value = true
    }
    
    // 保存比例编辑
    const saveRatioEdit = async () => {
      try {
        ratioEditLoading.value = true
        
        // 验证输入
        if (!editingRatio.value.ratio || !editingRatio.value.width || !editingRatio.value.height) {
          message.error('请填写完整的比例信息')
          return
        }
        
        // 检查比例名称是否重复
        const existingIndex = sizeRatiosConfig.value.findIndex(r => 
          r.ratio === editingRatio.value.ratio && r.id !== editingRatio.value.id
        )
        if (existingIndex !== -1) {
          message.error('比例名称已存在')
          return
        }
        
        if (editingRatioIndex.value === -1) {
          // 新增
          sizeRatiosConfig.value.push({ ...editingRatio.value })
        } else {
          // 编辑
          sizeRatiosConfig.value[editingRatioIndex.value] = { ...editingRatio.value }
        }
        
        // 更新配置
        updateSizeRatiosConfig()
        
        ratioEditModalOpen.value = false
        message.success(editingRatioIndex.value === -1 ? '添加比例成功' : '编辑比例成功')
      } catch (error) {
        console.error('保存比例失败:', error)
        message.error('保存比例失败')
      } finally {
        ratioEditLoading.value = false
      }
    }
    
    // 取消比例编辑
    const cancelRatioEdit = () => {
      ratioEditModalOpen.value = false
      editingRatio.value = {}
      editingRatioIndex.value = -1
    }
    
    // 删除比例
    const removeRatio = (ratio) => {
      if (sizeRatiosConfig.value.length <= 1) {
        message.warning('至少需要保留一个比例')
        return
      }
      
      const index = sizeRatiosConfig.value.findIndex(r => r.id === ratio.id)
      if (index > -1) {
        sizeRatiosConfig.value.splice(index, 1)
        updateSizeRatiosConfig()
        message.success('删除比例成功')
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
              default_size: { ...(configData.default_size || { width: 1024, height: 1024 }) }
            }
            
            // 一次性更新整个配置对象
            config.value = newConfig
            
            // 初始化尺寸比例配置
            initSizeRatiosConfig(configData.size_ratios || ['1:1', '4:3', '3:4', '16:9', '9:16'])
            
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
    
    // 监听loraGroupsReactive变化，设置默认active tab
    watch(loraGroupsReactive, (newGroups) => {
      if (newGroups.length > 0 && !activeLoraTab.value) {
        activeLoraTab.value = newGroups[0].baseModel
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
        activeLoraTab,
        config,
        baseModels,
        loras,
        loraGroups,
        loraGroupsReactive,
        sizeRatiosConfig,
        ratioEditModalOpen,
        ratioEditLoading,
        editingRatio,
        getModelDisplayName,
        getModelStatus,
        onDragStart,
        onDragEnd,
        onSizeRatioDragEnd,
        onSizeLockChange,
        showInput,
        handleInputConfirm,
        addNewRatio,
        editRatio,
        saveRatioEdit,
        cancelRatioEdit,
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

/* 尺寸比例配置样式 */
.section-desc {
  color: rgba(255, 255, 255, 0.65);
  margin-bottom: 16px;
  font-size: 14px;
  line-height: 1.5;
}

.size-ratios-config {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 16px;
}

.ratios-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.size-ratios-list {
  min-height: 100px;
}

.size-ratio-item {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: move;
  transition: all 0.3s;
}

.size-ratio-item:hover {
  border-color: #40a9ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.08);
}

.size-ratio-item.is-default {
  border-color: #52c41a;
  background: rgba(82, 196, 26, 0.1);
}

.ratio-drag-handle {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 8px;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.drag-icon {
  color: rgba(255, 255, 255, 0.45);
  cursor: grab;
}

.drag-icon:active {
  cursor: grabbing;
}

.ratio-index {
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

.ratio-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
}

.ratio-info {
  flex: 1;
}

.ratio-name {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.ratio-label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  font-size: 16px;
}

.ratio-pixels {
  color: rgba(255, 255, 255, 0.65);
  font-size: 14px;
}

.ratio-actions {
  display: flex;
  gap: 8px;
}

.edit-btn, .remove-btn {
  color: rgba(255, 255, 255, 0.65);
}

.edit-btn:hover {
  color: #40a9ff;
}

.remove-btn:hover {
  color: #ff4d4f;
}

/* LoRA排序样式 */
.lora-tabs {
  margin-top: 16px;
}

.lora-tabs .ant-tabs-tab {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.85);
}

.lora-tabs .ant-tabs-tab:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: #40a9ff;
}

.lora-tabs .ant-tabs-tab-active {
  background: rgba(24, 144, 255, 0.1);
  border-color: #40a9ff;
  color: #40a9ff;
}

.lora-tabs .ant-tabs-content-holder {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-top: none;
  border-radius: 0 0 6px 6px;
  padding: 16px;
}

.group-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.group-desc {
  color: rgba(255, 255, 255, 0.65);
  margin: 8px 0 0 0;
  font-size: 13px;
}

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
