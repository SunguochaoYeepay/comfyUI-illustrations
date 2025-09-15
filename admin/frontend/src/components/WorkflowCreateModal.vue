<template>
  <a-modal
    v-model:open="visible"
    title="创建工作流"
    @ok="handleCreate"
    :confirm-loading="loading"
    width="1000px"
    :ok-button-props="{ disabled: !validationResult || !validationResult.valid }"
  >
    <a-steps :current="currentStep" style="margin-bottom: 24px;">
      <a-step title="上传JSON" description="上传或输入工作流JSON" />
      <a-step title="验证分析" description="验证格式并分析配置项" />
      <a-step title="配置参数" description="设置工作流参数" />
      <a-step title="完成创建" description="保存工作流" />
    </a-steps>

    <!-- 步骤1: 上传JSON -->
    <div v-if="currentStep === 0">
      <WorkflowUploadStep 
        v-model:name="createForm.name"
        v-model:description="createForm.description"
        v-model:method="createMethod"
        v-model:file-list="fileList"
        v-model:workflow-json-string="workflowJsonString"
        v-model:uploaded-workflow-json="uploadedWorkflowJson"
        @method-change="onCreateMethodChange"
      />
    </div>

    <!-- 步骤2: 验证分析 -->
    <div v-if="currentStep === 1">
      <WorkflowValidationStep 
        :validating="validating"
        :validation-result="validationResult"
      />
    </div>

    <!-- 步骤3: 配置参数 -->
    <div v-if="currentStep === 2">
      <WorkflowConfigStep 
        v-if="validationResult && validationResult.valid"
        v-model:workflow-config="workflowConfig"
        :validation-result="validationResult"
      />
    </div>

    <!-- 步骤4: 完成创建 -->
    <div v-if="currentStep === 3">
      <WorkflowCompleteStep 
        :create-form="createForm"
        :validation-result="validationResult"
      />
    </div>

    <template #footer>
      <div style="text-align: right;">
        <a-button @click="handleClose" style="margin-right: 8px;">取消</a-button>
        <a-button v-if="currentStep > 0" @click="prevStep" style="margin-right: 8px;">上一步</a-button>
        <a-button 
          v-if="currentStep < 3" 
          type="primary" 
          @click="nextStep"
          :loading="validating"
          :disabled="!canProceedToNext"
        >
          {{ currentStep === 1 ? '验证工作流' : '下一步' }}
        </a-button>
        <a-button 
          v-if="currentStep === 3" 
          type="primary" 
          @click="handleCreate"
          :loading="loading"
        >
          创建工作流
        </a-button>
      </div>
    </template>
  </a-modal>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'
import { createWorkflow } from '@/api/workflow'
import WorkflowUploadStep from './WorkflowUploadStep.vue'
import WorkflowValidationStep from './WorkflowValidationStep.vue'
import WorkflowConfigStep from './WorkflowConfigStep.vue'
import WorkflowCompleteStep from './WorkflowCompleteStep.vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:open', 'created'])

const visible = ref(false)
const loading = ref(false)
const currentStep = ref(0)
const validating = ref(false)
const validationResult = ref(null)

// 创建表单数据
const createForm = reactive({
  name: '',
  description: '',
  workflow_json: {}
})

const workflowJsonString = ref('')
const createMethod = ref('upload')
const fileList = ref([])
const uploadedWorkflowJson = ref(null)
const workflowConfig = reactive({
  core_config: {},
  advanced_config: {}
})

// 计算属性
const canProceedToNext = computed(() => {
  if (currentStep.value === 0) {
    return createForm.name && (uploadedWorkflowJson.value || workflowJsonString.value)
  }
  if (currentStep.value === 1) {
    return validationResult.value && validationResult.value.valid
  }
  if (currentStep.value === 2) {
    return true
  }
  return false
})

// 监听props变化
watch(() => props.open, (newVal) => {
  visible.value = newVal
  if (newVal) {
    resetForm()
  }
})

watch(visible, (newVal) => {
  emit('update:open', newVal)
})

// 重置表单
const resetForm = () => {
  createForm.name = ''
  createForm.description = ''
  createForm.workflow_json = {}
  workflowJsonString.value = ''
  createMethod.value = 'upload'
  fileList.value = []
  uploadedWorkflowJson.value = null
  currentStep.value = 0
  validationResult.value = null
  workflowConfig.core_config = {}
  workflowConfig.advanced_config = {}
}

// 步骤控制
const nextStep = async () => {
  if (currentStep.value === 0) {
    await validateWorkflow()
  }
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

// 验证工作流
const validateWorkflow = async () => {
  if (currentStep.value !== 0) return
  
  validating.value = true
  try {
    let workflowJson = null
    
    if (createMethod.value === 'upload') {
      if (!uploadedWorkflowJson.value) {
        message.warning('请上传工作流JSON文件')
        return
      }
      workflowJson = uploadedWorkflowJson.value
    } else {
      if (!workflowJsonString.value) {
        message.warning('请输入工作流JSON内容')
        return
      }
      try {
        workflowJson = JSON.parse(workflowJsonString.value)
      } catch (error) {
        message.error('JSON格式错误，请检查输入内容')
        return
      }
    }
    
    const response = await request.post('/admin/workflows/validate', {
      workflow_json: workflowJson
    })
    
    validationResult.value = response
    
    if (response.valid) {
      initializeConfig(response.config_template)
      message.success('工作流验证成功')
    } else {
      message.error('工作流验证失败')
    }
  } catch (error) {
    console.error('验证工作流失败:', error)
    message.error('验证工作流失败: ' + error.message)
  } finally {
    validating.value = false
  }
}

// 初始化配置
const initializeConfig = (configTemplate) => {
  if (configTemplate?.core_config) {
    Object.keys(configTemplate.core_config).forEach(key => {
      workflowConfig.core_config[key] = configTemplate.core_config[key].default_value || ''
    })
  }
  if (configTemplate?.advanced_config) {
    Object.keys(configTemplate.advanced_config).forEach(key => {
      if (configTemplate.advanced_config[key].default_value) {
        workflowConfig.advanced_config[key] = { ...configTemplate.advanced_config[key].default_value }
      }
    })
  }
}

// 创建方式切换
const onCreateMethodChange = () => {
  if (createMethod.value === 'upload') {
    workflowJsonString.value = ''
  } else {
    fileList.value = []
    uploadedWorkflowJson.value = null
  }
}

// 创建工作流
const handleCreate = async () => {
  if (!validationResult.value || !validationResult.value.valid) {
    message.warning('请先完成工作流验证')
    return
  }
  
  let workflowJson = null
  if (createMethod.value === 'upload') {
    workflowJson = uploadedWorkflowJson.value
  } else {
    workflowJson = JSON.parse(workflowJsonString.value)
  }
  
  const configuredWorkflow = applyConfigToWorkflow(workflowJson, workflowConfig)
  
  loading.value = true
  try {
    const workflowData = {
      name: createForm.name,
      description: createForm.description,
      workflow_json: configuredWorkflow
    }
    
    await createWorkflow(workflowData)
    message.success('工作流创建成功')
    emit('created')
    handleClose()
  } catch (error) {
    console.error('Error creating workflow:', error)
    message.error('创建工作流失败')
  } finally {
    loading.value = false
  }
}

// 应用配置到工作流JSON
const applyConfigToWorkflow = (workflowJson, config) => {
  const result = JSON.parse(JSON.stringify(workflowJson))
  
  if (config.core_config?.positive_prompt) {
    Object.keys(result).forEach(nodeId => {
      const node = result[nodeId]
      if (node.class_type === 'CLIPTextEncode' && node.inputs?.text !== undefined) {
        node.inputs.text = config.core_config.positive_prompt
      }
    })
  }
  
  if (config.advanced_config?.sampling) {
    Object.keys(result).forEach(nodeId => {
      const node = result[nodeId]
      if (node.class_type === 'KSampler') {
        if (config.advanced_config.sampling.steps) {
          node.inputs.steps = config.advanced_config.sampling.steps
        }
        if (config.advanced_config.sampling.cfg) {
          node.inputs.cfg = config.advanced_config.sampling.cfg
        }
        if (config.advanced_config.sampling.seed) {
          node.inputs.seed = config.advanced_config.sampling.seed
        }
      }
    })
  }
  
  return result
}

// 关闭模态框
const handleClose = () => {
  visible.value = false
}
</script>
