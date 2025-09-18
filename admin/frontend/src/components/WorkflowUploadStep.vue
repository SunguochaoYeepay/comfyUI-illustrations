<template>
  <a-form layout="vertical">
    <a-form-item label="工作流编码" required>
      <a-input 
        :value="code" 
        @update:value="$emit('update:code', $event)"
        placeholder="输入工作流编码（系统标识符，不可修改）" 
        :disabled="!!code"
      />
      <div style="margin-top: 4px; font-size: 12px; color: #666;">
        工作流编码是系统内部标识符，用于主服务匹配工作流，创建后不可修改
      </div>
    </a-form-item>
    <a-form-item label="工作流名称" required>
      <a-input 
        :value="name" 
        @update:value="$emit('update:name', $event)"
        placeholder="输入工作流名称（显示名称，可修改）" 
      />
      <div style="margin-top: 4px; font-size: 12px; color: #666;">
        工作流名称用于显示，可以随时修改
      </div>
    </a-form-item>
    <a-form-item label="描述">
      <a-textarea 
        :value="description" 
        @update:value="$emit('update:description', $event)"
        :rows="3" 
        placeholder="输入工作流描述" 
      />
    </a-form-item>
    
    <!-- 创建方式选择 -->
    <a-form-item label="创建方式">
      <a-radio-group 
        :value="method" 
        @update:value="$emit('update:method', $event)"
        @change="$emit('methodChange')"
      >
        <a-radio value="upload">上传JSON文件</a-radio>
        <a-radio value="manual">手动输入JSON</a-radio>
      </a-radio-group>
    </a-form-item>
    
    <!-- 文件上传 -->
    <a-form-item v-if="method === 'upload'" label="上传工作流文件" required>
      <a-upload
        :file-list="fileList"
        :before-upload="beforeUpload"
        @change="handleFileChange"
        accept=".json"
        :max-count="1"
      >
        <a-button>
          <upload-outlined /> 选择JSON文件
        </a-button>
      </a-upload>
      <div style="margin-top: 8px; color: #666;">
        支持上传ComfyUI工作流JSON文件，系统会自动验证和识别配置项
      </div>
    </a-form-item>
    
    <!-- 手动输入JSON -->
    <a-form-item v-if="method === 'manual'" label="工作流JSON" required>
      <a-textarea 
        :value="workflowJsonString" 
        @update:value="$emit('update:workflowJsonString', $event)"
        :rows="10" 
        placeholder="输入工作流JSON内容"
        @change="handleJsonChange"
      />
      <div style="margin-top: 8px;">
        <a-button size="small" @click="formatJson">格式化JSON</a-button>
        <a-button size="small" @click="clearJson" style="margin-left: 8px;">清空</a-button>
      </div>
    </a-form-item>
  </a-form>
</template>

<script setup>
import { message } from 'ant-design-vue'
import { UploadOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  code: {
    type: String,
    default: ''
  },
  name: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  method: {
    type: String,
    default: 'upload'
  },
  fileList: {
    type: Array,
    default: () => []
  },
  workflowJsonString: {
    type: String,
    default: ''
  },
  uploadedWorkflowJson: {
    type: Object,
    default: null
  }
})

const emit = defineEmits([
  'update:name',
  'update:description', 
  'update:method',
  'update:fileList',
  'update:workflowJsonString',
  'update:uploadedWorkflowJson',
  'methodChange'
])

// 文件上传相关方法
const beforeUpload = (file) => {
  const isJson = file.type === 'application/json' || file.name.endsWith('.json')
  if (!isJson) {
    message.error('只能上传JSON文件')
    return false
  }
  return false // 阻止自动上传
}

const handleFileChange = async (info) => {
  emit('update:fileList', info.fileList)
  if (info.fileList.length > 0) {
    const file = info.fileList[0].originFileObj
    try {
      const content = await file.text()
      const workflowJson = JSON.parse(content)
      emit('update:uploadedWorkflowJson', workflowJson)
      message.success('文件上传成功，已解析工作流JSON')
    } catch (error) {
      message.error('文件解析失败: ' + error.message)
      emit('update:fileList', [])
    }
  } else {
    emit('update:uploadedWorkflowJson', null)
  }
}

// JSON处理
const handleJsonChange = (e) => {
  emit('update:workflowJsonString', e.target.value)
}

const formatJson = () => {
  try {
    const parsed = JSON.parse(props.workflowJsonString)
    const formatted = JSON.stringify(parsed, null, 2)
    emit('update:workflowJsonString', formatted)
    message.success('JSON格式化成功')
  } catch (error) {
    message.error('JSON格式错误，无法格式化')
  }
}

const clearJson = () => {
  emit('update:workflowJsonString', '')
}
</script>
