<template>
  <a-form layout="vertical">
    <a-form-item label="工作流名称" required>
      <a-input 
        :value="name" 
        @update:value="$emit('update:name', $event)"
        placeholder="输入工作流名称" 
      />
    </a-form-item>
    <a-form-item label="描述">
      <a-textarea 
        :value="description" 
        @update:value="$emit('update:description', $event)"
        :rows="4" 
        placeholder="输入工作流描述" 
      />
    </a-form-item>
    <a-form-item label="基础模型">
      <a-select 
        :value="baseModelType" 
        @update:value="$emit('update:baseModelType', $event)"
        placeholder="选择基础模型类型"
        allow-clear
      >
        <a-select-option value="">未设置</a-select-option>
        <a-select-option value="qwen-image">Qwen</a-select-option>
        <a-select-option value="flux">Flux</a-select-option>
        <a-select-option value="wan2.2-video">Wan2.2</a-select-option>
        <a-select-option value="seedream4">Seedream4</a-select-option>
        <a-select-option value="gemini-image">Gemini</a-select-option>
      </a-select>
      <div style="margin-top: 4px; font-size: 12px; color: #666;">
        选择此工作流关联的基础模型类型，用于工作流分类和过滤
      </div>
    </a-form-item>
  </a-form>
</template>

<script setup>
defineProps({
  name: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  baseModelType: {
    type: String,
    default: ''
  }
})

defineEmits(['update:name', 'update:description', 'update:baseModelType'])
</script>
