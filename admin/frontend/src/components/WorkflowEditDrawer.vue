<template>
  <a-drawer
    v-model:open="visible"
    title="编辑工作流"
    width="800px"
    @close="handleClose"
  >
    <a-tabs v-model:activeKey="activeTab" type="card">
      <!-- 基本信息 -->
      <a-tab-pane key="basic" tab="基本信息">
        <WorkflowBasicInfo 
          v-model:name="editForm.name"
          v-model:description="editForm.description"
        />
      </a-tab-pane>

      <!-- 节点配置 -->
      <a-tab-pane key="nodes" tab="节点配置">
        <WorkflowNodeConfigs 
          :node-configs="editNodeConfigs"
          @update:node-configs="editNodeConfigs = $event"
        />
      </a-tab-pane>

      <!-- 高级配置 -->
      <a-tab-pane key="advanced" tab="高级配置">
        <WorkflowAdvancedConfig 
          v-model:json-string="editWorkflowJsonString"
          :original-json="editForm.workflow_json"
          @json-change="handleJsonChange"
        />
      </a-tab-pane>
    </a-tabs>

    <template #footer>
      <div style="text-align: right;">
        <a-button @click="handleClose" style="margin-right: 8px;">取消</a-button>
        <a-button type="primary" @click="handleSave" :loading="loading">
          保存工作流
        </a-button>
      </div>
    </template>
  </a-drawer>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'
import { updateWorkflow } from '@/api/workflow'
import WorkflowBasicInfo from './WorkflowBasicInfo.vue'
import WorkflowNodeConfigs from './WorkflowNodeConfigs.vue'
import WorkflowAdvancedConfig from './WorkflowAdvancedConfig.vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  workflowData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:open', 'saved'])

const visible = ref(false)
const activeTab = ref('basic')
const loading = ref(false)

// 编辑表单数据
const editForm = reactive({
  id: null,
  name: '',
  description: '',
  workflow_json: {}
})

const editWorkflowJsonString = ref('')
const editNodeConfigs = ref([])

// 监听props变化
watch(() => props.open, (newVal) => {
  visible.value = newVal
  if (newVal && props.workflowData) {
    initEditData()
  }
})

watch(visible, (newVal) => {
  emit('update:open', newVal)
})

// 初始化编辑数据
const initEditData = async () => {
  editForm.id = props.workflowData.id
  editForm.name = props.workflowData.name
  editForm.description = props.workflowData.description || ''
  editForm.workflow_json = props.workflowData.workflow_json || {}
  editWorkflowJsonString.value = JSON.stringify(props.workflowData.workflow_json, null, 2)
  
  // 生成节点配置
  await generateNodeConfigs(props.workflowData.workflow_json)
}

// 生成节点配置
const generateNodeConfigs = async (workflowJson) => {
  try {
    const response = await request.post('/admin/workflows/validate', {
      workflow_json: workflowJson
    })
    
    if (response.valid) {
      const configs = []
      const configItems = response.config_items
      
      // 核心配置
      if (configItems.core_config) {
        // 正面提示词
        if (configItems.core_config.positive_prompt) {
          configs.push({
            type: 'prompt',
            title: '正面提示词',
            label: '正面提示词',
            value: configItems.core_config.positive_prompt.current_value || '',
            placeholder: '输入正面提示词',
            node_id: configItems.core_config.positive_prompt.node_id
          })
        }
        
        // 负面提示词
        if (configItems.core_config.negative_prompt) {
          configs.push({
            type: 'prompt',
            title: '负面提示词',
            label: '负面提示词',
            value: configItems.core_config.negative_prompt.current_value || '',
            placeholder: '输入负面提示词',
            node_id: configItems.core_config.negative_prompt.node_id
          })
        }
        
        // 图像尺寸
        if (configItems.core_config.image_width || configItems.core_config.image_height) {
          configs.push({
            type: 'size',
            title: '图像尺寸',
            width: configItems.core_config.image_width?.current_value || 512,
            height: configItems.core_config.image_height?.current_value || 512,
            batch_size: configItems.core_config.batch_size?.current_value || 1,
            node_id: configItems.core_config.image_width?.node_id || configItems.core_config.image_height?.node_id
          })
        }
        
        // 基础模型
        if (configItems.core_config.base_model) {
          configs.push({
            type: 'model',
            title: '基础模型',
            label: '基础模型',
            value: configItems.core_config.base_model.current_value || '',
            options: [
              { value: 'qwen_image_fp8_e4m3fn.safetensors', label: 'Qwen图像生成模型' },
              { value: 'flux-dev', label: 'Flux开发版' },
              { value: 'flux1-standard', label: 'Flux1标准版' },
              { value: 'wan-video', label: 'WAN视频生成模型' }
            ],
            node_id: configItems.core_config.base_model.node_id
          })
        }
        
        // VAE模型
        if (configItems.core_config.vae_model) {
          configs.push({
            type: 'model',
            title: 'VAE模型',
            label: 'VAE模型',
            value: configItems.core_config.vae_model.current_value || '',
            options: [
              { value: 'qwen_image_vae.safetensors', label: 'Qwen VAE' },
              { value: 'vae-ft-mse-840000-ema-pruned.safetensors', label: 'SD VAE' }
            ],
            node_id: configItems.core_config.vae_model.node_id
          })
        }
        
        // CLIP模型
        if (configItems.core_config.clip_model) {
          configs.push({
            type: 'model',
            title: 'CLIP模型',
            label: 'CLIP模型',
            value: configItems.core_config.clip_model.current_value || '',
            options: [
              { value: 'qwen_2.5_vl_7b_fp8_scaled.safetensors', label: 'Qwen CLIP' },
              { value: 'clip_l.safetensors', label: 'CLIP Large' }
            ],
            node_id: configItems.core_config.clip_model.node_id
          })
        }
      }
      
      // 高级配置
      if (configItems.advanced_config) {
        // 采样参数
        if (configItems.advanced_config.sampling) {
          const sampling = configItems.advanced_config.sampling.parameters
          configs.push({
            type: 'sampling',
            title: '采样参数',
            steps: sampling.steps || 20,
            cfg: sampling.cfg || 2.5,
            seed: sampling.seed || -1,
            sampler_name: sampling.sampler_name || 'euler',
            node_id: configItems.advanced_config.sampling.node_id
          })
        }
        
        // LoRA配置
        if (configItems.advanced_config.loras) {
          const loras = configItems.advanced_config.loras.parameters
          configs.push({
            type: 'lora',
            title: 'LoRA配置',
            lora_name: loras.lora_name || '',
            strength_model: loras.strength_model || 1.0,
            strength_clip: loras.strength_clip || 1.0,
            node_id: configItems.advanced_config.loras.node_id
          })
        }
      }
      
      editNodeConfigs.value = configs
    }
  } catch (error) {
    console.error('生成节点配置失败:', error)
    editNodeConfigs.value = []
  }
}

// 处理JSON变化
const handleJsonChange = (jsonString) => {
  editWorkflowJsonString.value = jsonString
  try {
    editForm.workflow_json = JSON.parse(jsonString)
  } catch (error) {
    // 忽略解析错误
  }
}

// 保存工作流
const handleSave = async () => {
  if (!editForm.name) {
    message.warning('请输入工作流名称')
    return
  }
  
  // 应用节点配置到工作流JSON
  let workflowJson = JSON.parse(JSON.stringify(editForm.workflow_json)) // 深拷贝
  
  // 应用节点配置
  editNodeConfigs.value.forEach(config => {
    if (config.node_id && workflowJson[config.node_id]) {
      const node = workflowJson[config.node_id]
      
      switch (config.type) {
        case 'prompt':
          if (node.inputs && 'text' in node.inputs) {
            node.inputs.text = config.value
          }
          break
        case 'model':
          if (node.inputs) {
            if (node.class_type === 'UNETLoader' && 'unet_name' in node.inputs) {
              node.inputs.unet_name = config.value
            } else if (node.class_type === 'VAELoader' && 'vae_name' in node.inputs) {
              node.inputs.vae_name = config.value
            } else if (node.class_type === 'CLIPLoader' && 'clip_name' in node.inputs) {
              node.inputs.clip_name = config.value
            }
          }
          break
        case 'size':
          if (node.inputs) {
            if ('width' in node.inputs) node.inputs.width = config.width
            if ('height' in node.inputs) node.inputs.height = config.height
            if ('batch_size' in node.inputs) node.inputs.batch_size = config.batch_size
          }
          break
        case 'sampling':
          if (node.inputs) {
            if ('steps' in node.inputs) node.inputs.steps = config.steps
            if ('cfg' in node.inputs) node.inputs.cfg = config.cfg
            if ('seed' in node.inputs) node.inputs.seed = config.seed
            if ('sampler_name' in node.inputs) node.inputs.sampler_name = config.sampler_name
          }
          break
        case 'lora':
          if (node.inputs) {
            if ('lora_name' in node.inputs) node.inputs.lora_name = config.lora_name
            if ('strength_model' in node.inputs) node.inputs.strength_model = config.strength_model
            if ('strength_clip' in node.inputs) node.inputs.strength_clip = config.strength_clip
          }
          break
      }
    }
  })
  
  // 验证工作流JSON
  try {
    const validationResponse = await request.post('/admin/workflows/validate', {
      workflow_json: workflowJson
    })
    
    if (!validationResponse.valid) {
      message.error('工作流验证失败: ' + validationResponse.errors.join(', '))
      return
    }
  } catch (error) {
    message.error('工作流验证失败: ' + error.message)
    return
  }

  loading.value = true
  try {
    await updateWorkflow(editForm.id, {
      name: editForm.name,
      description: editForm.description,
      workflow_json: workflowJson
    })
    message.success('工作流更新成功')
    emit('saved')
    handleClose()
  } catch (error) {
    console.error('Error updating workflow:', error)
    message.error('更新工作流失败')
  } finally {
    loading.value = false
  }
}

// 关闭抽屉
const handleClose = () => {
  visible.value = false
  activeTab.value = 'basic'
}
</script>
