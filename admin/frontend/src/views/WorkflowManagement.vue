<template>
  <div>
    <div class="header-bar">
      <h1>工作流管理</h1>
      <div class="header-actions">
        <a-input-search
          v-model:value="searchQuery"
          placeholder="按名称搜索工作流"
          style="width: 250px;"
          @search="onSearch"
          allow-clear
        />
        <a-button type="primary" @click="showCreateModal" style="margin-left: 8px;">
          <plus-outlined /> 创建工作流
        </a-button>
      </div>
    </div>

    <a-table
      :columns="columns"
      :data-source="tableData"
      row-key="id"
      :pagination="false"
      :loading="loading"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'workflow_json'">
          <a-tag color="blue">
            {{ Object.keys(record.workflow_json || {}).length }} 个节点
          </a-tag>
        </template>
        <template v-else-if="column.key === 'created_at'">
          {{ formatDate(record.created_at) }}
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a @click="viewWorkflow(record)">查看</a>
            <a @click="editWorkflow(record)">编辑</a>
            <a @click="downloadWorkflow(record)">下载</a>
            <a-popconfirm
              title="确定删除这个工作流吗？"
              @confirm="deleteWorkflow(record.id)"
            >
              <a style="color: #ff4d4f;">删除</a>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-pagination
      v-model:current="pagination.current"
      :total="pagination.total"
      :page-size="pagination.pageSize"
      @change="handleTableChange"
      show-less-items
      style="margin-top: 16px; text-align: right;"
    />

    <!-- 创建工作流模态框 -->
    <a-modal
      v-model:open="createModalOpen"
      title="创建工作流"
      @ok="handleCreate"
      :confirm-loading="createModalLoading"
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
        <a-form :model="createForm" layout="vertical">
          <a-form-item label="工作流名称" required>
            <a-input v-model:value="createForm.name" placeholder="输入工作流名称" />
          </a-form-item>
          <a-form-item label="描述">
            <a-textarea v-model:value="createForm.description" :rows="3" placeholder="输入工作流描述" />
          </a-form-item>
          
          <!-- 创建方式选择 -->
          <a-form-item label="创建方式">
            <a-radio-group v-model:value="createMethod" @change="onCreateMethodChange">
              <a-radio value="upload">上传JSON文件</a-radio>
              <a-radio value="manual">手动输入JSON</a-radio>
            </a-radio-group>
          </a-form-item>
          
          <!-- 文件上传 -->
          <a-form-item v-if="createMethod === 'upload'" label="上传工作流文件" required>
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
          <a-form-item v-if="createMethod === 'manual'" label="工作流JSON" required>
            <a-textarea 
              v-model:value="workflowJsonString" 
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
      </div>

      <!-- 步骤2: 验证分析 -->
      <div v-if="currentStep === 1">
        <div v-if="validating" style="text-align: center; padding: 40px;">
          <a-spin size="large" />
          <div style="margin-top: 16px;">正在验证工作流...</div>
        </div>
        
        <div v-else-if="validationResult">
          <a-alert 
            :type="validationResult.valid ? 'success' : 'error'"
            :message="validationResult.valid ? '工作流验证成功' : '工作流验证失败'"
            :description="validationResult.valid ? `识别出 ${validationResult.node_analysis?.total_nodes || 0} 个节点` : validationResult.errors?.join(', ') || '验证失败'"
            style="margin-bottom: 16px;"
          />
          
          <div v-if="validationResult.valid">
            <a-descriptions title="工作流分析结果" :column="2" bordered>
              <a-descriptions-item label="节点总数">{{ validationResult.node_analysis?.total_nodes || 0 }}</a-descriptions-item>
              <a-descriptions-item label="工作流类型">{{ validationResult.node_analysis?.workflow_type || '未知' }}</a-descriptions-item>
              <a-descriptions-item label="复杂度">{{ validationResult.node_analysis?.complexity || '未知' }}</a-descriptions-item>
              <a-descriptions-item label="关键节点">{{ Object.keys(validationResult.node_analysis?.key_nodes || {}).length }}</a-descriptions-item>
            </a-descriptions>
            
            <div style="margin-top: 16px;">
              <h4>识别的配置项</h4>
              <a-tag v-for="(config, key) in validationResult.config_items?.core_config || {}" :key="key" color="blue" style="margin: 4px;">
                {{ key }}
              </a-tag>
              <a-tag v-for="(config, key) in validationResult.config_items?.advanced_config || {}" :key="key" color="green" style="margin: 4px;">
                {{ key }}
              </a-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤3: 配置参数 -->
      <div v-if="currentStep === 2">
        <div v-if="validationResult && validationResult.valid">
          <h4>核心配置</h4>
          <a-form :model="workflowConfig" layout="vertical" style="margin-bottom: 24px;">
            <a-form-item v-if="validationResult.config_items?.core_config?.positive_prompt" label="正面提示词">
              <a-textarea 
                v-model:value="workflowConfig.core_config.positive_prompt" 
                :rows="3" 
                placeholder="输入正面提示词"
              />
            </a-form-item>
            
            <a-form-item v-if="validationResult.config_items?.core_config?.base_model" label="基础模型">
              <a-select v-model:value="workflowConfig.core_config.base_model" style="width: 100%">
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
                      v-model:value="workflowConfig.advanced_config.sampling.steps" 
                      :min="1" 
                      :max="100" 
                      style="width: 100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="CFG值">
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
                  <a-form-item label="随机种子">
                    <a-input-number 
                      v-model:value="workflowConfig.advanced_config.sampling.seed" 
                      style="width: 100%"
                    />
                  </a-form-item>
                </a-col>
              </a-row>
            </div>
          </a-form>
        </div>
      </div>

      <!-- 步骤4: 完成创建 -->
      <div v-if="currentStep === 3">
        <a-result
          status="success"
          title="工作流配置完成"
          sub-title="点击确定保存工作流到系统"
        >
          <template #extra>
            <a-descriptions :column="1" bordered>
              <a-descriptions-item label="工作流名称">{{ createForm.name }}</a-descriptions-item>
              <a-descriptions-item label="描述">{{ createForm.description || '无' }}</a-descriptions-item>
              <a-descriptions-item label="节点数量">{{ validationResult?.node_analysis?.total_nodes || 0 }}</a-descriptions-item>
              <a-descriptions-item label="配置项数量">{{ Object.keys(validationResult?.config_items?.core_config || {}).length + Object.keys(validationResult?.config_items?.advanced_config || {}).length }}</a-descriptions-item>
            </a-descriptions>
          </template>
        </a-result>
      </div>

      <template #footer>
        <div style="text-align: right;">
          <a-button @click="createModalOpen = false" style="margin-right: 8px;">取消</a-button>
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
            :loading="createModalLoading"
          >
            创建工作流
          </a-button>
        </div>
      </template>
    </a-modal>

    <!-- 编辑工作流模态框 -->
    <a-modal
      v-model:open="editModalOpen"
      title="编辑工作流"
      @ok="handleEdit"
      :confirm-loading="editModalLoading"
      width="1000px"
    >
      <a-steps :current="editCurrentStep" style="margin-bottom: 24px;">
        <a-step title="基本信息" description="编辑名称和描述" />
        <a-step title="验证分析" description="验证格式并分析配置项" />
        <a-step title="配置参数" description="设置工作流参数" />
        <a-step title="完成编辑" description="保存修改" />
      </a-steps>

      <!-- 步骤1: 基本信息 -->
      <div v-if="editCurrentStep === 0">
        <a-form :model="editForm" layout="vertical">
          <a-form-item label="工作流名称" required>
            <a-input v-model:value="editForm.name" placeholder="输入工作流名称" />
          </a-form-item>
          <a-form-item label="描述">
            <a-textarea v-model:value="editForm.description" :rows="3" placeholder="输入工作流描述" />
          </a-form-item>
          
          <!-- 编辑方式选择 -->
          <a-form-item label="编辑方式">
            <a-radio-group v-model:value="editMethod" @change="onEditMethodChange">
              <a-radio value="smart">智能编辑（推荐）</a-radio>
              <a-radio value="manual">手动编辑JSON</a-radio>
            </a-radio-group>
          </a-form-item>
          
          <!-- 手动编辑JSON -->
          <a-form-item v-if="editMethod === 'manual'" label="工作流JSON" required>
            <a-textarea 
              v-model:value="editWorkflowJsonString" 
              :rows="10" 
              placeholder="输入工作流JSON内容"
              @change="handleEditJsonChange"
            />
            <div style="margin-top: 8px;">
              <a-button size="small" @click="formatEditJson">格式化JSON</a-button>
              <a-button size="small" @click="clearEditJson" style="margin-left: 8px;">清空</a-button>
            </div>
          </a-form-item>
        </a-form>
      </div>

      <!-- 步骤2: 验证分析 -->
      <div v-if="editCurrentStep === 1">
        <div v-if="editValidating" style="text-align: center; padding: 40px;">
          <a-spin size="large" />
          <div style="margin-top: 16px;">正在验证工作流...</div>
        </div>
        
        <div v-else-if="editValidationResult">
          <a-alert 
            :type="editValidationResult.valid ? 'success' : 'error'"
            :message="editValidationResult.valid ? '工作流验证成功' : '工作流验证失败'"
            :description="editValidationResult.valid ? `识别出 ${editValidationResult.node_analysis?.total_nodes || 0} 个节点` : editValidationResult.errors?.join(', ') || '验证失败'"
            style="margin-bottom: 16px;"
          />
          
          <div v-if="editValidationResult.valid">
            <a-descriptions title="工作流分析结果" :column="2" bordered>
              <a-descriptions-item label="节点总数">{{ editValidationResult.node_analysis?.total_nodes || 0 }}</a-descriptions-item>
              <a-descriptions-item label="工作流类型">{{ editValidationResult.node_analysis?.workflow_type || '未知' }}</a-descriptions-item>
              <a-descriptions-item label="复杂度">{{ editValidationResult.node_analysis?.complexity || '未知' }}</a-descriptions-item>
              <a-descriptions-item label="关键节点">{{ Object.keys(editValidationResult.node_analysis?.key_nodes || {}).length }}</a-descriptions-item>
            </a-descriptions>
            
            <div style="margin-top: 16px;">
              <h4>识别的配置项</h4>
              <a-tag v-for="(config, key) in editValidationResult.config_items?.core_config || {}" :key="key" color="blue" style="margin: 4px;">
                {{ key }}
              </a-tag>
              <a-tag v-for="(config, key) in editValidationResult.config_items?.advanced_config || {}" :key="key" color="green" style="margin: 4px;">
                {{ key }}
              </a-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 步骤3: 配置参数 -->
      <div v-if="editCurrentStep === 2">
        <div v-if="editValidationResult && editValidationResult.valid">
          <h4>核心配置</h4>
          <a-form :model="editWorkflowConfig" layout="vertical" style="margin-bottom: 24px;">
            <a-form-item v-if="editValidationResult.config_items?.core_config?.positive_prompt" label="正面提示词">
              <a-textarea 
                v-model:value="editWorkflowConfig.core_config.positive_prompt" 
                :rows="3" 
                placeholder="输入正面提示词"
              />
            </a-form-item>
            
            <a-form-item v-if="editValidationResult.config_items?.core_config?.base_model" label="基础模型">
              <a-select v-model:value="editWorkflowConfig.core_config.base_model" style="width: 100%">
                <a-select-option value="qwen-image">Qwen图像生成模型</a-select-option>
                <a-select-option value="flux-dev">Flux开发版</a-select-option>
                <a-select-option value="flux1-standard">Flux1标准版</a-select-option>
                <a-select-option value="wan-video">WAN视频生成模型</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
          
          <h4>高级配置</h4>
          <a-form :model="editWorkflowConfig" layout="vertical">
            <div v-if="editValidationResult.config_items?.advanced_config?.sampling">
              <a-row :gutter="16">
                <a-col :span="8">
                  <a-form-item label="采样步数">
                    <a-input-number 
                      v-model:value="editWorkflowConfig.advanced_config.sampling.steps" 
                      :min="1" 
                      :max="100" 
                      style="width: 100%"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="CFG值">
                    <a-input-number 
                      v-model:value="editWorkflowConfig.advanced_config.sampling.cfg" 
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
                      v-model:value="editWorkflowConfig.advanced_config.sampling.seed" 
                      style="width: 100%"
                    />
                  </a-form-item>
                </a-col>
              </a-row>
            </div>
          </a-form>
        </div>
      </div>

      <!-- 步骤4: 完成编辑 -->
      <div v-if="editCurrentStep === 3">
        <a-result
          status="success"
          title="工作流编辑完成"
          sub-title="点击确定保存修改到系统"
        >
          <template #extra>
            <a-descriptions :column="1" bordered>
              <a-descriptions-item label="工作流名称">{{ editForm.name }}</a-descriptions-item>
              <a-descriptions-item label="描述">{{ editForm.description || '无' }}</a-descriptions-item>
              <a-descriptions-item label="节点数量">{{ editValidationResult?.node_analysis?.total_nodes || 0 }}</a-descriptions-item>
              <a-descriptions-item label="配置项数量">{{ Object.keys(editValidationResult?.config_items?.core_config || {}).length + Object.keys(editValidationResult?.config_items?.advanced_config || {}).length }}</a-descriptions-item>
            </a-descriptions>
          </template>
        </a-result>
      </div>

      <template #footer>
        <div style="text-align: right;">
          <a-button @click="editModalOpen = false" style="margin-right: 8px;">取消</a-button>
          <a-button v-if="editCurrentStep > 0" @click="editPrevStep" style="margin-right: 8px;">上一步</a-button>
          <a-button 
            v-if="editCurrentStep < 3" 
            type="primary" 
            @click="editNextStep"
            :loading="editValidating"
            :disabled="!editCanProceedToNext"
          >
            {{ editCurrentStep === 1 ? '验证工作流' : '下一步' }}
          </a-button>
          <a-button 
            v-if="editCurrentStep === 3" 
            type="primary" 
            @click="handleEdit"
            :loading="editModalLoading"
          >
            保存修改
          </a-button>
        </div>
      </template>
    </a-modal>


    <!-- 查看工作流模态框 -->
    <a-modal
      v-model:open="viewModalOpen"
      title="查看工作流"
      :footer="null"
      width="800px"
    >
      <div v-if="viewWorkflowData">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="名称">{{ viewWorkflowData.name }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatDate(viewWorkflowData.created_at) }}</a-descriptions-item>
          <a-descriptions-item label="描述" :span="2">{{ viewWorkflowData.description || '无' }}</a-descriptions-item>
        </a-descriptions>
        <a-divider>工作流JSON</a-divider>
        <pre class="json-viewer">{{ JSON.stringify(viewWorkflowData.workflow_json, null, 2) }}</pre>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  getWorkflows, 
  createWorkflow, 
  updateWorkflow, 
  deleteWorkflow as deleteWorkflowAPI, 
  uploadWorkflowFile, 
  downloadWorkflow as downloadWorkflowAPI
} from '@/api/workflow'
import { message } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined } from '@ant-design/icons-vue'
import request from '@/utils/request'

const router = useRouter()

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '名称', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '节点数', key: 'workflow_json', width: 100 },
  { title: '创建时间', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 200 },
]

const data = ref([])
const loading = ref(false)
const searchQuery = ref('')
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

// 计算属性确保数据始终是数组
const tableData = computed(() => {
  return Array.isArray(data.value) ? data.value : []
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
    return true // 配置步骤总是可以继续
  }
  return false
})

// 编辑计算属性
const editCanProceedToNext = computed(() => {
  if (editCurrentStep.value === 0) {
    return editForm.name && (editMethod.value === 'manual' ? editWorkflowJsonString.value : true)
  }
  if (editCurrentStep.value === 1) {
    return editValidationResult.value && editValidationResult.value.valid
  }
  if (editCurrentStep.value === 2) {
    return true // 配置步骤总是可以继续
  }
  return false
})

// 创建模态框状态
const createModalOpen = ref(false)
const createModalLoading = ref(false)
const createForm = reactive({
  name: '',
  description: '',
  workflow_json: {}
})
const workflowJsonString = ref('')
const createMethod = ref('upload') // 默认选择上传方式
const fileList = ref([])
const uploadedWorkflowJson = ref(null)

// 步骤控制
const currentStep = ref(0)
const validating = ref(false)
const validationResult = ref(null)
const workflowConfig = reactive({
  core_config: {},
  advanced_config: {}
})

// 编辑模态框状态
const editModalOpen = ref(false)
const editModalLoading = ref(false)
const editForm = reactive({
  id: null,
  name: '',
  description: '',
  workflow_json: {}
})
const editWorkflowJsonString = ref('')

// 编辑步骤控制
const editCurrentStep = ref(0)
const editValidating = ref(false)
const editValidationResult = ref(null)
const editMethod = ref('smart') // 默认选择智能编辑
const editWorkflowConfig = reactive({
  core_config: {},
  advanced_config: {}
})


// 查看模态框状态
const viewModalOpen = ref(false)
const viewWorkflowData = ref(null)

// 获取工作流列表
const fetchWorkflows = async (page = 1, pageSize = 10, search = '') => {
  loading.value = true
  try {
    console.log('正在获取工作流列表...', { page, pageSize, search })
    const response = await getWorkflows({
      page,
      pageSize,
      search
    })
    
    console.log('API响应:', response)
    console.log('响应类型:', typeof response, '是否为数组:', Array.isArray(response))
    
    if (response && Array.isArray(response)) {
      data.value = response
      pagination.total = response.length
      pagination.current = page
      pagination.pageSize = pageSize
      console.log('设置数据成功，工作流数量:', response.length)
    } else {
      data.value = []
      console.error('响应格式错误:', response)
      message.error('获取工作流列表失败')
    }
  } catch (error) {
    console.error('Error fetching workflows:', error)
    data.value = []
    message.error('获取工作流列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索功能
const onSearch = (searchValue) => {
  pagination.current = 1
  fetchWorkflows(1, pagination.pageSize, searchValue)
}

// 分页处理
const handleTableChange = (page, pageSize) => {
  fetchWorkflows(page, pageSize, searchQuery.value)
}

// 创建工作流
const showCreateModal = () => {
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
  createModalOpen.value = true
}

// 步骤控制方法
const nextStep = async () => {
  if (currentStep.value === 0) {
    // 验证工作流
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
    
    // 调用验证API
    const response = await request.post('/admin/workflows/validate', {
      workflow_json: workflowJson
    })
    
    validationResult.value = response
    
    if (response.valid) {
      // 初始化配置
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

const handleCreate = async () => {
  if (!validationResult.value || !validationResult.value.valid) {
    message.warning('请先完成工作流验证')
    return
  }
  
  // 获取工作流JSON
  let workflowJson = null
  if (createMethod.value === 'upload') {
    workflowJson = uploadedWorkflowJson.value
  } else {
    workflowJson = JSON.parse(workflowJsonString.value)
  }
  
  // 应用配置到工作流JSON
  const configuredWorkflow = applyConfigToWorkflow(workflowJson, workflowConfig)
  
  createModalLoading.value = true
  try {
    const workflowData = {
      name: createForm.name,
      description: createForm.description,
      workflow_json: configuredWorkflow
    }
    
    await createWorkflow(workflowData)
    message.success('工作流创建成功')
    createModalOpen.value = false
    // 刷新列表
    await fetchWorkflows(pagination.current, pagination.pageSize, searchQuery.value)
  } catch (error) {
    console.error('Error creating workflow:', error)
    message.error('创建工作流失败')
  } finally {
    createModalLoading.value = false
  }
}

// 应用配置到工作流JSON
const applyConfigToWorkflow = (workflowJson, config) => {
  const result = JSON.parse(JSON.stringify(workflowJson)) // 深拷贝
  
  // 应用核心配置
  if (config.core_config?.positive_prompt) {
    // 找到正面提示词节点并更新
    Object.keys(result).forEach(nodeId => {
      const node = result[nodeId]
      if (node.class_type === 'CLIPTextEncode' && node.inputs?.text !== undefined) {
        node.inputs.text = config.core_config.positive_prompt
      }
    })
  }
  
  // 应用高级配置
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
  if (info.fileList.length > 0) {
    const file = info.fileList[0].originFileObj
    try {
      const content = await file.text()
      const workflowJson = JSON.parse(content)
      uploadedWorkflowJson.value = workflowJson
      message.success('文件上传成功，已解析工作流JSON')
    } catch (error) {
      message.error('文件解析失败: ' + error.message)
      fileList.value = []
    }
  } else {
    uploadedWorkflowJson.value = null
  }
}

const onCreateMethodChange = () => {
  // 切换创建方式时清空相关数据
  if (createMethod.value === 'upload') {
    workflowJsonString.value = ''
  } else {
    fileList.value = []
    uploadedWorkflowJson.value = null
  }
}

// 编辑工作流
const editWorkflow = (record) => {
  editForm.id = record.id
  editForm.name = record.name
  editForm.description = record.description || ''
  editForm.workflow_json = record.workflow_json || {}
  editWorkflowJsonString.value = JSON.stringify(record.workflow_json, null, 2)
  editCurrentStep.value = 0
  editMethod.value = 'smart'
  editValidationResult.value = null
  editWorkflowConfig.core_config = {}
  editWorkflowConfig.advanced_config = {}
  editModalOpen.value = true
}

// 编辑步骤控制方法
const editNextStep = async () => {
  if (editCurrentStep.value === 0) {
    // 验证工作流
    await editValidateWorkflow()
  }
  if (editCurrentStep.value < 3) {
    editCurrentStep.value++
  }
}

const editPrevStep = () => {
  if (editCurrentStep.value > 0) {
    editCurrentStep.value--
  }
}

// 编辑验证工作流
const editValidateWorkflow = async () => {
  if (editCurrentStep.value !== 0) return
  
  editValidating.value = true
  try {
    let workflowJson = null
    
    if (editMethod.value === 'smart') {
      // 智能编辑模式，使用现有的工作流JSON
      workflowJson = editForm.workflow_json
    } else {
      // 手动编辑模式，解析JSON字符串
      if (!editWorkflowJsonString.value) {
        message.warning('请输入工作流JSON内容')
        return
      }
      try {
        workflowJson = JSON.parse(editWorkflowJsonString.value)
      } catch (error) {
        message.error('JSON格式错误，请检查输入内容')
        return
      }
    }
    
    // 调用验证API
    const response = await request.post('/admin/workflows/validate', {
      workflow_json: workflowJson
    })
    
    editValidationResult.value = response
    
    if (response.valid) {
      // 初始化配置
      editInitializeConfig(response.config_template, workflowJson)
      message.success('工作流验证成功')
    } else {
      message.error('工作流验证失败')
    }
  } catch (error) {
    console.error('验证工作流失败:', error)
    message.error('验证工作流失败: ' + error.message)
  } finally {
    editValidating.value = false
  }
}

// 编辑初始化配置
const editInitializeConfig = (configTemplate, workflowJson) => {
  if (configTemplate?.core_config) {
    Object.keys(configTemplate.core_config).forEach(key => {
      // 从现有工作流中提取当前值
      let currentValue = configTemplate.core_config[key].default_value || ''
      
      if (key === 'positive_prompt') {
        // 查找正面提示词节点的当前值
        Object.keys(workflowJson).forEach(nodeId => {
          const node = workflowJson[nodeId]
          if (node.class_type === 'CLIPTextEncode' && node.inputs?.text !== undefined) {
            currentValue = node.inputs.text
          }
        })
      }
      
      editWorkflowConfig.core_config[key] = currentValue
    })
  }
  
  if (configTemplate?.advanced_config) {
    Object.keys(configTemplate.advanced_config).forEach(key => {
      if (configTemplate.advanced_config[key].default_value) {
        const defaultConfig = { ...configTemplate.advanced_config[key].default_value }
        
        if (key === 'sampling') {
          // 从现有工作流中提取采样参数
          Object.keys(workflowJson).forEach(nodeId => {
            const node = workflowJson[nodeId]
            if (node.class_type === 'KSampler') {
              if (node.inputs?.steps) defaultConfig.steps = node.inputs.steps
              if (node.inputs?.cfg) defaultConfig.cfg = node.inputs.cfg
              if (node.inputs?.seed) defaultConfig.seed = node.inputs.seed
            }
          })
        }
        
        editWorkflowConfig.advanced_config[key] = defaultConfig
      }
    })
  }
}

// 编辑方式切换
const onEditMethodChange = () => {
  if (editMethod.value === 'smart') {
    editWorkflowJsonString.value = ''
  }
}

const handleEdit = async () => {
  if (!editForm.name) {
    message.warning('请输入工作流名称')
    return
  }
  
  // 根据编辑方式处理工作流JSON
  let workflowJson = null
  
  if (editMethod.value === 'smart') {
    // 智能编辑模式，应用配置到工作流JSON
    if (!editValidationResult.value || !editValidationResult.value.valid) {
      message.warning('请先完成工作流验证')
      return
    }
    workflowJson = editApplyConfigToWorkflow(editForm.workflow_json, editWorkflowConfig)
  } else {
    // 手动编辑模式，解析JSON字符串
    if (!editWorkflowJsonString.value) {
      message.warning('请输入工作流JSON内容')
      return
    }
    try {
      workflowJson = JSON.parse(editWorkflowJsonString.value)
    } catch (error) {
      message.error('JSON格式错误，请检查输入内容')
      return
    }
  }

  editModalLoading.value = true
  try {
    await updateWorkflow(editForm.id, {
      name: editForm.name,
      description: editForm.description,
      workflow_json: workflowJson
    })
    message.success('工作流更新成功')
    editModalOpen.value = false
    fetchWorkflows(pagination.current, pagination.pageSize, searchQuery.value)
  } catch (error) {
    console.error('Error updating workflow:', error)
    message.error('更新工作流失败')
  } finally {
    editModalLoading.value = false
  }
}

// 编辑应用配置到工作流JSON
const editApplyConfigToWorkflow = (workflowJson, config) => {
  const result = JSON.parse(JSON.stringify(workflowJson)) // 深拷贝
  
  // 应用核心配置
  if (config.core_config?.positive_prompt) {
    // 找到正面提示词节点并更新
    Object.keys(result).forEach(nodeId => {
      const node = result[nodeId]
      if (node.class_type === 'CLIPTextEncode' && node.inputs?.text !== undefined) {
        node.inputs.text = config.core_config.positive_prompt
      }
    })
  }
  
  // 应用高级配置
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

// 删除工作流
const deleteWorkflow = async (id) => {
  try {
    await deleteWorkflowAPI(id)
    message.success('工作流删除成功')
    fetchWorkflows(pagination.current, pagination.pageSize, searchQuery.value)
  } catch (error) {
    console.error('Error deleting workflow:', error)
    message.error('删除工作流失败')
  }
}

// 查看工作流
const viewWorkflow = (record) => {
  viewWorkflowData.value = record
  viewModalOpen.value = true
}

// 下载工作流
const downloadWorkflow = async (record) => {
  try {
    const response = await downloadWorkflowAPI(record.id)
    const blob = new Blob([JSON.stringify(response.content, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = response.filename || `${record.name}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    message.success('工作流下载成功')
  } catch (error) {
    console.error('Error downloading workflow:', error)
    message.error('下载工作流失败')
  }
}

// 上传工作流文件



// JSON处理函数
const handleJsonChange = (e) => {
  try {
    createForm.workflow_json = JSON.parse(e.target.value)
  } catch (error) {
    // 忽略解析错误，让用户继续输入
  }
}

const handleEditJsonChange = (e) => {
  try {
    editForm.workflow_json = JSON.parse(e.target.value)
  } catch (error) {
    // 忽略解析错误，让用户继续输入
  }
}

const formatJson = () => {
  try {
    const parsed = JSON.parse(workflowJsonString.value)
    workflowJsonString.value = JSON.stringify(parsed, null, 2)
  } catch (error) {
    message.error('JSON格式错误，无法格式化')
  }
}

const formatEditJson = () => {
  try {
    const parsed = JSON.parse(editWorkflowJsonString.value)
    editWorkflowJsonString.value = JSON.stringify(parsed, null, 2)
  } catch (error) {
    message.error('JSON格式错误，无法格式化')
  }
}

const clearJson = () => {
  workflowJsonString.value = ''
  createForm.workflow_json = {}
}

const clearEditJson = () => {
  editWorkflowJsonString.value = ''
  editForm.workflow_json = {}
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchWorkflows()
})
</script>

<style scoped>
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-actions {
  display: flex;
  align-items: center;
}

.json-viewer {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
}
</style>
