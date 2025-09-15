<template>
  <div v-if="nodeConfigs.length > 0">
          <a-tabs 
            v-model:activeKey="activeTab" 
            tab-position="left"
            class="node-config-tabs compact-tabs"
          >
      <a-tab-pane 
        v-for="(config, index) in nodeConfigs" 
        :key="index"
        :tab="config.title"
      >
        <div style="padding: 16px;">
          <!-- 提示词配置 -->
          <div v-if="config.type === 'prompt'">
            <a-form-item :label="config.label" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
              <a-textarea 
                :value="config.value" 
                @update:value="updateConfig(index, 'value', $event)"
                :rows="6" 
                :placeholder="config.placeholder"
              />
            </a-form-item>
          </div>
          
          <!-- 模型配置 -->
          <div v-else-if="config.type === 'model'">
            <a-form-item :label="config.label" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
              <a-select 
                :value="config.value" 
                @update:value="updateConfig(index, 'value', $event)"
                style="width: 100%"
              >
                <a-select-option v-for="option in config.options" :key="option.value" :value="option.value">
                  {{ option.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </div>
          
          <!-- 尺寸配置 -->
          <div v-else-if="config.type === 'size'">
            <!-- 尺寸配置选项 -->
            <a-form-item label="尺寸配置方式" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
              <a-radio-group 
                :value="config.sizeMode || 'custom'" 
                @update:value="updateConfig(index, 'sizeMode', $event)"
                @change="onSizeModeChange(index, $event)"
              >
                <a-radio value="default">使用生图配置默认尺寸</a-radio>
                <a-radio value="ratio">按比例设置</a-radio>
                <a-radio value="custom">自定义尺寸</a-radio>
              </a-radio-group>
            </a-form-item>

            <!-- 比例选择 -->
            <a-form-item v-if="config.sizeMode === 'ratio'" label="图片比例" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
              <a-select 
                :value="config.selectedRatio" 
                @update:value="updateConfig(index, 'selectedRatio', $event)"
                @change="onRatioChange(index, $event)"
                style="width: 100%"
                placeholder="选择图片比例"
              >
                <a-select-option 
                  v-for="ratio in imageGenSizeRatios" 
                  :key="ratio" 
                  :value="ratio"
                >
                  {{ ratio }}
                </a-select-option>
              </a-select>
            </a-form-item>

            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="宽度" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
                  <a-input-number 
                    :value="config.width" 
                    @update:value="updateConfig(index, 'width', $event)"
                    :min="64" 
                    :max="4096" 
                    :disabled="config.sizeMode === 'default'"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="高度" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
                  <a-input-number 
                    :value="config.height" 
                    @update:value="updateConfig(index, 'height', $event)"
                    :min="64" 
                    :max="4096" 
                    :disabled="config.sizeMode === 'default'"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="批次大小" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
                  <a-input-number 
                    :value="config.batch_size" 
                    @update:value="updateConfig(index, 'batch_size', $event)"
                    :min="1" 
                    :max="8" 
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>

            <!-- 显示当前配置信息 -->
            <div v-if="config.sizeMode === 'default'" style="margin-top: 8px; padding: 8px; background: #f0f0f0; border-radius: 4px; font-size: 12px; color: #666;">
              将使用生图配置中的默认尺寸: {{ imageGenDefaultSize.width }} × {{ imageGenDefaultSize.height }}
            </div>
          </div>
          
          <!-- 采样配置 -->
          <div v-else-if="config.type === 'sampling'">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="采样步数" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
                  <a-input-number 
                    :value="config.steps" 
                    @update:value="updateConfig(index, 'steps', $event)"
                    :min="1" 
                    :max="100" 
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="CFG值" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
                  <a-input-number 
                    :value="config.cfg" 
                    @update:value="updateConfig(index, 'cfg', $event)"
                    :min="1" 
                    :max="20" 
                    :step="0.1" 
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="随机种子" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
                  <a-input-number 
                    :value="config.seed" 
                    @update:value="updateConfig(index, 'seed', $event)"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="采样器" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
                  <a-select 
                    :value="config.sampler_name" 
                    @update:value="updateConfig(index, 'sampler_name', $event)"
                    style="width: 100%"
                  >
                    <a-select-option value="euler">Euler</a-select-option>
                    <a-select-option value="euler_ancestral">Euler Ancestral</a-select-option>
                    <a-select-option value="dpm_2">DPM++ 2M</a-select-option>
                    <a-select-option value="dpm_2_ancestral">DPM++ 2M Ancestral</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>
          </div>
          
          <!-- LoRA配置 -->
          <div v-else-if="config.type === 'lora'">
            <a-form-item label="LoRA模型" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
              <a-select 
                :value="config.lora_name" 
                @update:value="updateConfig(index, 'lora_name', $event)"
                placeholder="选择LoRA模型"
                style="width: 100%"
                show-search
                :filter-option="(input, option) => option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0"
              >
                <a-select-option v-for="option in loraOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="模型强度" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
                  <a-input-number 
                    :value="config.strength_model" 
                    @update:value="updateConfig(index, 'strength_model', $event)"
                    :min="0" 
                    :max="2" 
                    :step="0.1" 
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="CLIP强度" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
                  <a-input-number 
                    :value="config.strength_clip" 
                    @update:value="updateConfig(index, 'strength_clip', $event)"
                    :min="0" 
                    :max="2" 
                    :step="0.1" 
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </div>
          
          <!-- 其他配置 -->
          <div v-else>
            <a-form-item :label="config.label" :label-col="{ span: 24 }" :wrapper-col="{ span: 24 }">
              <a-input 
                :value="config.value" 
                @update:value="updateConfig(index, 'value', $event)"
                :placeholder="config.placeholder" 
              />
            </a-form-item>
          </div>
        </div>
      </a-tab-pane>
    </a-tabs>
  </div>
  <div v-else style="text-align: center; padding: 40px; color: #999;">
    暂无可配置的节点
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLoras } from '@/api/lora'
import { getImageGenConfig } from '@/api/imageGenConfig'

const props = defineProps({
  nodeConfigs: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:nodeConfigs'])

const activeTab = ref('0')
const loraOptions = ref([])

// 生图配置数据
const imageGenDefaultSize = ref({ width: 1024, height: 1024 })
const imageGenSizeRatios = ref(['1:1', '4:3', '3:4', '16:9', '9:16'])

// 获取LoRA列表
const fetchLoraOptions = async () => {
  try {
    const response = await getLoras(1, 1000) // 获取所有LoRA
    if (response && response.data && response.data.items && Array.isArray(response.data.items)) {
      loraOptions.value = response.data.items.map(lora => ({
        value: lora.name,
        label: `${lora.display_name || lora.name} (${lora.base_model || '未知模型'})`
      }))
    }
  } catch (error) {
    console.error('获取LoRA列表失败:', error)
    loraOptions.value = []
  }
}

// 加载生图配置
const loadImageGenConfig = async () => {
  try {
    const config = await getImageGenConfig()
    imageGenDefaultSize.value = config.default_size || { width: 1024, height: 1024 }
    imageGenSizeRatios.value = config.size_ratios || ['1:1', '4:3', '3:4', '16:9', '9:16']
  } catch (error) {
    console.error('加载生图配置失败:', error)
  }
}

// 更新配置
const updateConfig = (index, key, value) => {
  const newConfigs = [...props.nodeConfigs]
  newConfigs[index][key] = value
  emit('update:nodeConfigs', newConfigs)
}

// 尺寸配置方式改变
const onSizeModeChange = (index, event) => {
  const mode = event.target.value
  const newConfigs = [...props.nodeConfigs]
  const config = newConfigs[index]
  
  if (mode === 'default') {
    // 使用生图配置默认尺寸
    config.width = imageGenDefaultSize.value.width
    config.height = imageGenDefaultSize.value.height
  } else if (mode === 'ratio' && config.selectedRatio) {
    // 按比例设置
    const [widthRatio, heightRatio] = config.selectedRatio.split(':').map(Number)
    const baseSize = Math.min(imageGenDefaultSize.value.width, imageGenDefaultSize.value.height)
    config.width = Math.round(baseSize * widthRatio / Math.max(widthRatio, heightRatio))
    config.height = Math.round(baseSize * heightRatio / Math.max(widthRatio, heightRatio))
  }
  
  emit('update:nodeConfigs', newConfigs)
}

// 比例选择改变
const onRatioChange = (index, ratio) => {
  const newConfigs = [...props.nodeConfigs]
  const config = newConfigs[index]
  
  if (ratio) {
    const [widthRatio, heightRatio] = ratio.split(':').map(Number)
    const baseSize = Math.min(imageGenDefaultSize.value.width, imageGenDefaultSize.value.height)
    config.width = Math.round(baseSize * widthRatio / Math.max(widthRatio, heightRatio))
    config.height = Math.round(baseSize * heightRatio / Math.max(widthRatio, heightRatio))
  }
  
  emit('update:nodeConfigs', newConfigs)
}

// 组件挂载时获取LoRA列表和生图配置
onMounted(() => {
  fetchLoraOptions()
  loadImageGenConfig()
})
</script>

<style scoped>
/* 基础tabs样式 */
.node-config-tabs :deep(.ant-tabs-nav) {
  width: 100px;
  text-align: left;
}

/* 紧凑型tabs样式 - 使用更高优先级的选择器 */
.node-config-tabs.compact-tabs :deep(.ant-tabs-left > .ant-tabs-nav .ant-tabs-tab),
.node-config-tabs.compact-tabs :deep(.ant-tabs-right > .ant-tabs-nav .ant-tabs-tab),
.node-config-tabs.compact-tabs :deep(.ant-tabs-left > div > .ant-tabs-nav .ant-tabs-tab),
.node-config-tabs.compact-tabs :deep(.ant-tabs-right > div > .ant-tabs-nav .ant-tabs-tab) {
  padding: 6px 0px !important;
  text-align: left !important;
}

/* 更具体的选择器来确保覆盖 */
.node-config-tabs.compact-tabs :deep(.ant-tabs-tab) {
  padding: 4px 12px !important;
  text-align: left !important;
}
</style>
