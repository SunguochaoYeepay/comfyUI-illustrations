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
        >
          <a-select-option value="qwen-image">Qwen图像生成模型</a-select-option>
          <a-select-option value="flux-dev">Flux开发版</a-select-option>
          <a-select-option value="flux1-standard">Flux1标准版</a-select-option>
          <a-select-option value="wan-video">WAN视频生成模型</a-select-option>
        </a-select>
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
