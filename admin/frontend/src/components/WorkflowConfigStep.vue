<template>
  <div>
    <h4>核心配置</h4>
    <a-form :model="workflowConfig" layout="vertical" style="margin-bottom: 24px;">
      <a-form-item v-if="validationResult.config_items?.core_config?.positive_prompt" label="正面提示词">
        <a-textarea 
          :value="workflowConfig.core_config.positive_prompt" 
          @update:value="updateCoreConfig('positive_prompt', $event)"
          :rows="3" 
          placeholder="输入正面提示词"
        />
      </a-form-item>
      
      <a-form-item v-if="validationResult.config_items?.core_config?.base_model" label="基础模型">
        <a-select 
          :value="workflowConfig.core_config.base_model" 
          @update:value="updateCoreConfig('base_model', $event)"
          style="width: 100%"
          placeholder="选择基础模型"
          :loading="baseModelsLoading"
          show-search
          :filter-option="(input, option) => option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0"
        >
          <a-select-option 
            v-for="model in baseModels" 
            :key="model.name" 
            :value="model.name"
          >
            {{ model.display_name }} ({{ model.name }})
          </a-select-option>
        </a-select>
        <div style="margin-top: 4px; font-size: 12px; color: #666;">
          选择此工作流主要关联的基础模型类型
        </div>
      </a-form-item>
    </a-form>
    
    <h4>高级配置</h4>
    <a-form :model="workflowConfig" layout="vertical">
      <div v-if="validationResult.config_items?.advanced_config?.sampling">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="采样步数">
              <a-input-number 
                :value="workflowConfig.advanced_config.sampling?.steps" 
                @update:value="updateAdvancedConfig('sampling', 'steps', $event)"
                :min="1" 
                :max="100" 
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="CFG值">
              <a-input-number 
                :value="workflowConfig.advanced_config.sampling?.cfg" 
                @update:value="updateAdvancedConfig('sampling', 'cfg', $event)"
                :min="1" 
                :max="20" 
                :step="0.1" 
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="随机种子">
              <a-input-number 
                :value="workflowConfig.advanced_config.sampling?.seed" 
                @update:value="updateAdvancedConfig('sampling', 'seed', $event)"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </div>
    </a-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getBaseModels } from '@/api/baseModel'

const props = defineProps({
  workflowConfig: {
    type: Object,
    required: true
  },
  validationResult: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:workflowConfig'])

// 基础模型数据
const baseModels = ref([])
const baseModelsLoading = ref(false)

// 加载基础模型列表
const loadBaseModels = async () => {
  try {
    baseModelsLoading.value = true
    const response = await getBaseModels({ page: 1, pageSize: 1000 })
    baseModels.value = response.models || []
  } catch (error) {
    console.error('加载基础模型失败:', error)
  } finally {
    baseModelsLoading.value = false
  }
}

// 组件挂载时加载基础模型
onMounted(() => {
  loadBaseModels()
})

// 更新核心配置
const updateCoreConfig = (key, value) => {
  const newConfig = { ...props.workflowConfig }
  newConfig.core_config[key] = value
  emit('update:workflowConfig', newConfig)
}

// 更新高级配置
const updateAdvancedConfig = (category, key, value) => {
  const newConfig = { ...props.workflowConfig }
  if (!newConfig.advanced_config[category]) {
    newConfig.advanced_config[category] = {}
  }
  newConfig.advanced_config[category][key] = value
  emit('update:workflowConfig', newConfig)
}
</script>
