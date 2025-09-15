<template>
  <div>
    <a-alert 
      message="高级用户功能" 
      description="直接编辑工作流JSON，适用于熟悉ComfyUI工作流结构的用户"
      type="info" 
      style="margin-bottom: 16px;"
    />
    
    <a-form-item label="工作流JSON">
      <a-textarea 
        :value="jsonString" 
        @update:value="$emit('update:jsonString', $event)"
        :rows="15" 
        placeholder="手动编辑工作流JSON内容"
        @change="handleJsonChange"
      />
      <div style="margin-top: 8px;">
        <a-button size="small" @click="formatJson">格式化JSON</a-button>
        <a-button size="small" @click="validateJson" style="margin-left: 8px;">验证JSON</a-button>
        <a-button size="small" @click="resetJson" style="margin-left: 8px;">重置</a-button>
      </div>
    </a-form-item>
  </div>
</template>

<script setup>
import { message } from 'ant-design-vue'
import request from '@/utils/request'

const props = defineProps({
  jsonString: {
    type: String,
    default: ''
  },
  originalJson: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:jsonString', 'jsonChange'])

// 处理JSON变化
const handleJsonChange = (e) => {
  emit('jsonChange', e.target.value)
}

// 格式化JSON
const formatJson = () => {
  try {
    const parsed = JSON.parse(props.jsonString)
    const formatted = JSON.stringify(parsed, null, 2)
    emit('update:jsonString', formatted)
    message.success('JSON格式化成功')
  } catch (error) {
    message.error('JSON格式错误，无法格式化')
  }
}

// 验证JSON
const validateJson = async () => {
  try {
    const workflowJson = JSON.parse(props.jsonString)
    const response = await request.post('/admin/workflows/validate', {
      workflow_json: workflowJson
    })
    
    if (response.valid) {
      message.success('JSON验证通过')
    } else {
      message.error('JSON验证失败: ' + response.errors.join(', '))
    }
  } catch (error) {
    message.error('JSON验证失败: ' + error.message)
  }
}

// 重置JSON
const resetJson = () => {
  const resetValue = JSON.stringify(props.originalJson, null, 2)
  emit('update:jsonString', resetValue)
  message.success('JSON已重置')
}
</script>
