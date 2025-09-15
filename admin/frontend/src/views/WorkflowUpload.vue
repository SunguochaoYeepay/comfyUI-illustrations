<template>
  <div class="workflow-upload">
    <a-page-header
      title="工作流上传"
      sub-title="上传并配置ComfyUI工作流"
      @back="() => $router.go(-1)"
    />
    
    <a-card class="upload-card" :bordered="false">
      <template #title>
        <span>上传工作流文件</span>
      </template>
      
      <!-- 文件上传 -->
      <a-upload
        :file-list="fileList"
        :before-upload="beforeUpload"
        @change="handleFileChange"
        accept=".json"
        :max-count="1"
        :show-upload-list="false"
      >
        <a-button type="primary" size="large" :loading="uploading">
          <upload-outlined />
          选择工作流JSON文件
        </a-button>
      </a-upload>
      
      <div v-if="fileList.length > 0" class="file-info">
        <a-alert
          :message="`已选择文件: ${fileList[0].name}`"
          type="info"
          show-icon
          style="margin-top: 16px;"
        />
      </div>
    </a-card>
    
    <!-- 验证结果 -->
    <a-card v-if="validationResult" class="validation-card" :bordered="false">
      <template #title>
        <span>验证结果</span>
        <a-tag :color="validationResult.valid ? 'green' : 'red'" style="margin-left: 8px;">
          {{ validationResult.valid ? '验证通过' : '验证失败' }}
        </a-tag>
      </template>
      
      <a-alert
        :type="validationResult.valid ? 'success' : 'error'"
        :message="validationResult.valid ? '工作流验证成功' : '工作流验证失败'"
        :description="validationResult.valid ? '已识别配置项，可以继续配置' : validationResult.errors.join(', ')"
        show-icon
        style="margin-bottom: 16px;"
      />
      
      <!-- 警告信息 -->
      <a-alert
        v-if="validationResult.warnings && validationResult.warnings.length > 0"
        type="warning"
        :message="`发现 ${validationResult.warnings.length} 个警告`"
        :description="validationResult.warnings.join(', ')"
        show-icon
        style="margin-bottom: 16px;"
      />
      
      <!-- 节点分析结果 -->
      <div v-if="validationResult.valid" class="node-analysis">
        <h4>节点分析结果</h4>
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="总节点数">
            {{ validationResult.node_analysis.total_nodes }}
          </a-descriptions-item>
          <a-descriptions-item label="节点类型">
            {{ Object.keys(validationResult.node_analysis.node_types).length }}
          </a-descriptions-item>
          <a-descriptions-item label="关键节点">
            {{ Object.keys(validationResult.node_analysis.key_nodes).length }}
          </a-descriptions-item>
          <a-descriptions-item label="可配置节点">
            {{ validationResult.node_analysis.configurable_nodes.length }}
          </a-descriptions-item>
          <a-descriptions-item label="工作流类型">
            {{ getWorkflowTypeName(validationResult.node_analysis.workflow_type) }}
          </a-descriptions-item>
          <a-descriptions-item label="复杂度">
            {{ getComplexityName(validationResult.node_analysis.complexity) }}
          </a-descriptions-item>
        </a-descriptions>
      </div>
      
      <!-- 配置项识别结果 -->
      <div v-if="validationResult.valid" class="config-items">
        <h4>识别的配置项</h4>
        
        <!-- 核心配置项 -->
        <div class="config-section">
          <h5>核心配置项</h5>
          <a-list :data-source="coreConfigItems" size="small" :grid="{ gutter: 16, column: 2 }">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-card size="small" :bordered="false">
                  <template #title>
                    <span>{{ getConfigItemName(item.key) }}</span>
                    <a-tag v-if="item.is_template" color="blue" style="margin-left: 8px;">
                      模板变量
                    </a-tag>
                  </template>
                  <p><strong>节点:</strong> {{ item.node_id }}</p>
                  <p><strong>参数:</strong> {{ item.parameter }}</p>
                  <p><strong>当前值:</strong> {{ formatValue(item.current_value) }}</p>
                </a-card>
              </a-list-item>
            </template>
          </a-list>
        </div>
        
        <!-- 高级配置项 -->
        <div class="config-section" v-if="advancedConfigItems.length > 0">
          <h5>高级配置项</h5>
          <a-list :data-source="advancedConfigItems" size="small" :grid="{ gutter: 16, column: 2 }">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-card size="small" :bordered="false">
                  <template #title>
                    <span>{{ getConfigItemName(item.key) }}</span>
                  </template>
                  <p><strong>节点:</strong> {{ item.node_id }}</p>
                  <p><strong>类型:</strong> {{ item.class_type }}</p>
                </a-card>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </div>
    </a-card>
    
    <!-- 配置表单 -->
    <a-card v-if="validationResult && validationResult.valid" class="config-form-card" :bordered="false">
      <template #title>
        <span>工作流配置</span>
      </template>
      
      <a-form :model="workflowConfig" layout="vertical" @finish="submitWorkflow">
        <!-- 基础信息 -->
        <a-form-item label="工作流名称" required>
          <a-input v-model:value="workflowConfig.name" placeholder="请输入工作流名称" />
        </a-form-item>
        
        <a-form-item label="工作流描述">
          <a-textarea v-model:value="workflowConfig.description" placeholder="请输入工作流描述" />
        </a-form-item>
        
        <!-- 核心配置 -->
        <div class="config-section">
          <h5>核心配置</h5>
          
          <!-- 提示词配置 -->
          <a-form-item 
            label="正面提示词" 
            v-if="coreConfigItems.find(item => item.key === 'positive_prompt')"
          >
            <a-textarea 
              v-model:value="workflowConfig.core_config.positive_prompt" 
              placeholder="请输入正面提示词"
              :rows="3"
            />
          </a-form-item>
          
          <!-- 图像尺寸配置 -->
          <a-row :gutter="16" v-if="coreConfigItems.find(item => item.key === 'image_width')">
            <a-col :span="12">
              <a-form-item label="图像宽度">
                <a-input-number 
                  v-model:value="workflowConfig.core_config.image_width" 
                  :min="64" 
                  :max="2048" 
                  :step="64"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="图像高度">
                <a-input-number 
                  v-model:value="workflowConfig.core_config.image_height" 
                  :min="64" 
                  :max="2048" 
                  :step="64"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>
          
          <!-- 基础模型配置 -->
          <a-form-item 
            label="基础模型" 
            v-if="coreConfigItems.find(item => item.key === 'base_model')"
          >
            <a-select v-model:value="workflowConfig.core_config.base_model" style="width: 100%">
              <a-select-option value="qwen-image">Qwen图像生成模型</a-select-option>
              <a-select-option value="flux-dev">Flux开发版</a-select-option>
              <a-select-option value="flux1-standard">Flux1标准版</a-select-option>
              <a-select-option value="wan-video">WAN视频生成模型</a-select-option>
            </a-select>
          </a-form-item>
        </div>
        
        <!-- 高级配置 -->
        <div class="config-section" v-if="advancedConfigItems.length > 0">
          <h5>高级配置</h5>
          
          <!-- LoRA配置 -->
          <div v-if="advancedConfigItems.find(item => item.key === 'loras')">
            <h6>LoRA配置</h6>
            <a-form-item label="LoRA文件">
              <a-select v-model:value="workflowConfig.advanced_config.loras.lora_name" style="width: 100%">
                <a-select-option value="Lightning-8steps">Lightning-8steps</a-select-option>
                <a-select-option value="Qwen-Style">Qwen-Style</a-select-option>
                <a-select-option value="Flux-Style">Flux-Style</a-select-option>
              </a-select>
            </a-form-item>
          </div>
          
          <!-- 采样参数配置 -->
          <div v-if="advancedConfigItems.find(item => item.key === 'sampling')">
            <h6>采样参数</h6>
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="步数">
                  <a-input-number 
                    v-model:value="workflowConfig.advanced_config.sampling.steps" 
                    :min="1" 
                    :max="100" 
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="CFG">
                  <a-input-number 
                    v-model:value="workflowConfig.advanced_config.sampling.cfg" 
                    :min="1" 
                    :max="20" 
                    :step="0.1" 
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="种子">
                  <a-input-number 
                    v-model:value="workflowConfig.advanced_config.sampling.seed" 
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </div>
        </div>
        
        <!-- 提交按钮 -->
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit" :loading="submitting">
              创建工作流
            </a-button>
            <a-button @click="resetForm">
              重置
            </a-button>
            <a-button @click="previewWorkflow">
              预览工作流
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
    
    <!-- 预览模态框 -->
    <a-modal
      v-model:open="previewVisible"
      title="工作流预览"
      width="80%"
      :footer="null"
    >
      <div class="workflow-preview">
        <pre>{{ JSON.stringify(workflowConfig, null, 2) }}</pre>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { UploadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import request from '@/utils/request'

export default {
  name: 'WorkflowUpload',
  components: {
    UploadOutlined
  },
  data() {
    return {
      fileList: [],
      validationResult: null,
      workflowConfig: {
        name: '',
        description: '',
        core_config: {},
        advanced_config: {}
      },
      submitting: false,
      uploading: false,
      previewVisible: false
    }
  },
  computed: {
    coreConfigItems() {
      if (!this.validationResult || !this.validationResult.config_items) return []
      return Object.entries(this.validationResult.config_items.core_config).map(([key, config]) => ({
        key,
        name: this.getConfigItemName(key),
        ...config
      }))
    },
    advancedConfigItems() {
      if (!this.validationResult || !this.validationResult.config_items) return []
      return Object.entries(this.validationResult.config_items.advanced_config).map(([key, config]) => ({
        key,
        name: this.getConfigItemName(key),
        ...config
      }))
    }
  },
  methods: {
    beforeUpload(file) {
      if (file.type !== 'application/json') {
        message.error('只能上传JSON文件')
        return false
      }
      return false // 阻止自动上传
    },
    
    async handleFileChange(info) {
      if (info.fileList.length > 0) {
        const file = info.fileList[0].originFileObj
        await this.validateWorkflow(file)
      }
    },
    
    async validateWorkflow(file) {
      this.uploading = true
      try {
        // 先读取文件内容保存原始JSON
        const content = await file.text()
        const workflowJson = JSON.parse(content)
        
        // 使用FormData上传文件
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await request.post('/admin/workflows/upload-and-validate', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        // 保存验证结果和原始JSON
        this.validationResult = {
          ...response,
          workflow_json: workflowJson
        }
        
        if (response.valid) {
          this.initializeConfig(response.config_template)
          message.success('工作流验证成功')
        } else {
          message.error('工作流验证失败')
        }
      } catch (error) {
        message.error('文件解析失败: ' + error.message)
      } finally {
        this.uploading = false
      }
    },
    
    initializeConfig(configTemplate) {
      // 根据配置模板初始化表单
      this.workflowConfig.core_config = {}
      this.workflowConfig.advanced_config = {}
      
      // 初始化核心配置
      if (configTemplate.core_config) {
        for (const [key, config] of Object.entries(configTemplate.core_config)) {
          this.workflowConfig.core_config[key] = config.default_value
        }
      }
      
      // 初始化高级配置
      if (configTemplate.advanced_config) {
        for (const [key, config] of Object.entries(configTemplate.advanced_config)) {
          this.workflowConfig.advanced_config[key] = config.default_value
        }
      }
    },
    
    async submitWorkflow() {
      this.submitting = true
      try {
        const response = await request.post('/admin/workflows/create-from-upload', {
          ...this.workflowConfig,
          workflow_json: this.validationResult.workflow_json
        })
        
        message.success('工作流创建成功')
        this.$router.push('/workflow-management')
      } catch (error) {
        message.error('工作流创建失败: ' + error.message)
      } finally {
        this.submitting = false
      }
    },
    
    resetForm() {
      this.workflowConfig = {
        name: '',
        description: '',
        core_config: {},
        advanced_config: {}
      }
      this.validationResult = null
      this.fileList = []
    },
    
    previewWorkflow() {
      this.previewVisible = true
    },
    
    getConfigItemName(key) {
      const names = {
        'positive_prompt': '正面提示词',
        'negative_prompt': '负面提示词',
        'image_width': '图像宽度',
        'image_height': '图像高度',
        'base_model': '基础模型',
        'loras': 'LoRA配置',
        'sampling': '采样参数',
        'reference_images': '参考图配置'
      }
      return names[key] || key
    },
    
    getWorkflowTypeName(type) {
      const names = {
        'image_generation': '图像生成',
        'image_generation_with_reference': '参考图生成',
        'image_processing': '图像处理',
        'unknown': '未知类型'
      }
      return names[type] || type
    },
    
    getComplexityName(complexity) {
      const names = {
        'simple': '简单',
        'medium': '中等',
        'complex': '复杂'
      }
      return names[complexity] || complexity
    },
    
    formatValue(value) {
      if (typeof value === 'string' && value.length > 50) {
        return value.substring(0, 50) + '...'
      }
      return value
    }
  }
}
</script>

<style scoped>
.workflow-upload {
  padding: 24px;
}

.upload-card,
.validation-card,
.config-form-card {
  margin-bottom: 24px;
}

.file-info {
  margin-top: 16px;
}

.node-analysis {
  margin-top: 16px;
}

.config-items {
  margin-top: 16px;
}

.config-section {
  margin-bottom: 24px;
}

.config-section h5 {
  margin-bottom: 16px;
  color: #1890ff;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 8px;
}

.config-section h6 {
  margin-bottom: 12px;
  color: #52c41a;
}

.workflow-preview {
  max-height: 500px;
  overflow-y: auto;
}

.workflow-preview pre {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
}
</style>
