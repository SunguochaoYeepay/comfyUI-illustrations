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
  }
})

defineEmits(['update:name', 'update:description'])
</script>
